from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from db import SessionLocal, Conversation
from datetime import datetime
from openai import OpenAI
import logging
import os
from typing import List, Dict
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # type: ignore

from reservio import (
    get_business_info,
    get_booking_slots,
    summarize_slots,
    get_services,
    summarize_services,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Init FastAPI
app = FastAPI()

# Initialize OpenAI client - try environment variable first (Railway), then .env file (local)
openai_key = os.environ.get("OPENAI_API_KEY")
if not openai_key:
    try:
        from decouple import config
        openai_key = config("OPENAI_API_KEY")
    except Exception:
        raise ValueError("OPENAI_API_KEY not found in environment variables or .env file")
        
client = OpenAI(api_key=openai_key)

# Reservio env-driven defaults
RESERVIO_SERVICE_ID = os.environ.get("RESERVIO_SERVICE_ID")  # optional
RESERVIO_RESOURCE_ID = os.environ.get("RESERVIO_RESOURCE_ID")  # optional
RESERVIO_BUSINESS_ID = os.environ.get("RESERVIO_BUSINESS_ID")  # optional

BOOKING_SYSTEM_PROMPT = (
    "You are a WhatsApp assistant for a barbershop. "
    "Your ONLY job is to help the user schedule a haircut appointment. "
    "Follow these steps:\n"
    "1) Greet briefly using the business name.\n"
    "2) First, present the list of available services with numbers.\n"
    "3) When the user picks a service (by number or name), offer 3-5 nearest available times (display in AM/PM), respecting business hours 8:00–4:00 (Europe/Prague).\n"
    "4) If the user wants more options, tell them they can reply 'more' to see additional times.\n"
    "5) If user wants later, suggest future dates within the next 7 days.\n"
    "6) Collect full name and phone if missing.\n"
    "7) Confirm summary (service, date, time, barber/resource if applicable).\n"
    "8) Do not discuss anything outside booking a haircut.\n"
    "Keep messages short, clear, and actionable."
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("🚀 WhatsApp Bot Server Starting Up!")
    logger.info("=" * 50)
    logger.info(f"✅ Server is running")
    logger.info(f"✅ OpenAI client initialized")
    logger.info(f"✅ Database connection ready")
    logger.info("=" * 50)

# Health check endpoint (for Railway)
@app.get("/")
async def health_check():
    logger.info("🏥 Health check endpoint hit")
    return {"status": "ok", "message": "WhatsApp Bot is running on Railway"}

# Twilio Webhook Route
@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),   # WhatsApp user number
    Body: str = Form(...)    # Incoming message text
):
    logger.info("=" * 50)
    logger.info("📱 NEW WHATSAPP MESSAGE RECEIVED")
    logger.info(f"From: {From}")
    logger.info(f"Message: {Body}")
    logger.info("=" * 50)
    
    # Create Twilio response
    twilio_resp = MessagingResponse()

    # Retrieve brief history (last 5 exchanges) for context
    db = SessionLocal()
    recent_messages: List[Conversation] = (
        db.query(Conversation)
        .filter(Conversation.user_number == From)
        .order_by(Conversation.timestamp.desc())
        .limit(5)
        .all()
    )

    # Optional: fetch business info (name, timezone) to ground the assistant
    business_info = await get_business_info(RESERVIO_BUSINESS_ID)
    business_name = (business_info or {}).get("name") or "our barbershop"
    timezone = (business_info or {}).get("settings", {}).get("timezone") or "Europe/Prague"

    # Fetch services list (Czech names are preserved from API)
    services = await get_services(RESERVIO_BUSINESS_ID)
    services_summary = summarize_services(services)

    # Try to detect selected service by user input (number or name substring)
    selected_service_id = None
    selected_service_name = None
    selected_service_duration_min = None
    body_norm = (Body or "").strip()
    if body_norm:
        # number choice (1..N)
        if body_norm.isdigit():
            idx = int(body_norm)
            if 1 <= idx <= len(services):
                svc = services[idx - 1]
                selected_service_id = svc.get("id")
                attrs = (svc.get("attributes") or {})
                selected_service_name = attrs.get("name")
                dur = attrs.get("duration")
                if isinstance(dur, (int, float)):
                    selected_service_duration_min = int(dur // 60)
        # name/substring choice
        if not selected_service_id and len(body_norm) >= 2:
            lower_body = body_norm.casefold()
            for svc in services:
                attrs = (svc.get("attributes") or {})
                name = attrs.get("name") or ""
                if name and name.casefold() in lower_body or lower_body in name.casefold():
                    selected_service_id = svc.get("id")
                    selected_service_name = name
                    dur = attrs.get("duration")
                    if isinstance(dur, (int, float)):
                        selected_service_duration_min = int(dur // 60)
                    break

    # Parse explicit day requests (today, tomorrow, or YYYY-MM-DD) in Europe/Prague
    requested_day_start = None
    requested_day_end = None
    lower_body = body_norm.lower()
    # Resolve Prague timezone with fallback to fixed offset if tzdata missing
    if ZoneInfo is not None:
        try:
            prague_tz = ZoneInfo("Europe/Prague")
            utc_tz = ZoneInfo("UTC")
        except Exception:
            prague_tz = None
            utc_tz = None
    else:
        prague_tz = None
        utc_tz = None

    if prague_tz is None:
        # Fallback: fixed GMT+1 offset (does not handle DST)
        from datetime import timezone, timedelta
        prague_tz = timezone(timedelta(hours=1))
        utc_tz = timezone.utc

    now_prague = datetime.utcnow().replace(tzinfo=utc_tz).astimezone(prague_tz)
    now_utc = now_prague.astimezone(utc_tz)
    try:
        from datetime import timedelta, datetime as dt_mod
        if "tomorrow" in lower_body or "zítra" in lower_body:
            day = (now_prague + timedelta(days=1)).date()
            requested_day_start = dt_mod.combine(day, dt_mod.min.time()).replace(tzinfo=prague_tz).astimezone(utc_tz)
            requested_day_end = dt_mod.combine(day, dt_mod.max.time()).replace(tzinfo=prague_tz).astimezone(utc_tz)
        elif "today" in lower_body or "dnes" in lower_body:
            day = now_prague.date()
            requested_day_start = dt_mod.combine(day, dt_mod.min.time()).replace(tzinfo=prague_tz).astimezone(utc_tz)
            requested_day_end = dt_mod.combine(day, dt_mod.max.time()).replace(tzinfo=prague_tz).astimezone(utc_tz)
        else:
            # Simple YYYY-MM-DD parse
            import re
            m = re.search(r"(20\d{2}-\d{2}-\d{2})", lower_body)
            if m:
                ymd = m.group(1)
                year, month, day = map(int, ymd.split("-"))
                day_date = dt_mod(year, month, day).date()
                requested_day_start = dt_mod.combine(day_date, dt_mod.min.time()).replace(tzinfo=prague_tz).astimezone(utc_tz)
                requested_day_end = dt_mod.combine(day_date, dt_mod.max.time()).replace(tzinfo=prague_tz).astimezone(utc_tz)
    except Exception:
        requested_day_start = None
        requested_day_end = None

    # Try to fetch availability for the next 7 days or the requested day (use selected service if provided)
    availability_note = ""
    try:
        from datetime import timedelta
        # Define query window and an effective lower bound that never allows past times
        if requested_day_start and requested_day_end:
            query_start = requested_day_start
            query_end = requested_day_end
            # Do not allow past times even when a specific day (e.g., today) is requested
            effective_not_before = requested_day_start if requested_day_start > now_utc else now_utc
        else:
            query_start = now_utc
            query_end = now_utc + timedelta(days=7)
            effective_not_before = now_utc
        effective_service_id = selected_service_id or RESERVIO_SERVICE_ID
        if effective_service_id:
            slots = await get_booking_slots(
                business_id=RESERVIO_BUSINESS_ID,
                start_utc=query_start,
                end_utc=query_end,
                service_id=effective_service_id,
                resource_id=RESERVIO_RESOURCE_ID,
            )
            # If user asked for "more", increase limit
            more_requested = (" more" in lower_body) or (lower_body.strip() == "more") or ("více" in lower_body)
            availability_note = summarize_slots(
                slots,
                limit=50 if (requested_day_start or more_requested) else 5,
                timezone="Europe/Prague",
                min_duration_minutes=selected_service_duration_min,
                # Ensure no past times are suggested
                not_before_utc=effective_not_before,
                open_hour_local=8,
                close_hour_local=16,
                annotate_last_start=bool(requested_day_start),
            )
    except Exception as e:
        logger.warning(f"Availability fetch failed: {e}")

    # Build chat messages with strict system prompt
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": BOOKING_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Business: {business_name}. Timezone: {timezone}. Use only haircut-related booking guidance.",
        },
        {
            "role": "system",
            "content": f"Current UTC datetime: {datetime.utcnow().isoformat()}Z",
        },
    ]

    # Include a short recap of last user/bot exchange to keep context tight
    for conv in reversed(recent_messages):
        messages.append({"role": "user", "content": conv.user_message or ""})
        if conv.bot_reply:
            messages.append({"role": "assistant", "content": conv.bot_reply})

    # Provide service list first to drive proactive selection
    if services_summary:
        messages.append({"role": "system", "content": services_summary})

    # If a service was selected, provide that context and show availability
    if selected_service_id:
        messages.append({
            "role": "system",
            "content": f"Selected service id: {selected_service_id} name: {selected_service_name}",
        })
        if availability_note:
            messages.append({"role": "system", "content": availability_note})

    # Current user message last
    # Ensure a first-time greeting with business name if no history
    if not recent_messages:
        greet = f"Welcome to {business_name}! How can I help you book a haircut today?"
        messages.append({"role": "assistant", "content": greet})

    messages.append({"role": "user", "content": Body})

    # On first contact or greeting, send a deterministic greeting with services and return
    greetings = {"hi", "hello", "hey", "ahoj", "čau", "cau", "dobry den", "dobrý den"}
    is_greeting = (body_norm.lower() in greetings) or (len(body_norm.split()) <= 3 and any(g in body_norm.lower() for g in greetings))
    if not recent_messages or is_greeting:
        first_reply_parts: List[str] = []
        first_reply_parts.append(f"Welcome to {business_name}! How can I help you book a haircut today?")
        if services_summary:
            first_reply_parts.append(services_summary)
        first_reply_parts.append("Please reply with the number of the service to continue.")
        first_message_text = "\n".join(first_reply_parts)

        twilio_resp.message(first_message_text)

        new_message = Conversation(
            user_number=From,
            user_message=Body,
            bot_reply=first_message_text,
            timestamp=datetime.utcnow()
        )
        db.add(new_message)
        db.commit()
        db.close()

        return PlainTextResponse(str(twilio_resp), media_type="application/xml")

    # Call OpenAI for a constrained booking reply
    logger.info("🤖 Calling OpenAI API for barber booking...")
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.3,
    )
    bot_reply = completion.choices[0].message.content
    logger.info(f"✅ OpenAI Response: {bot_reply}")

    # Add reply to Twilio response
    twilio_resp.message(bot_reply)

    # Save conversation to Neon DB
    logger.info("💾 Saving to database...")
    new_message = Conversation(
        user_number=From,
        user_message=Body,
        bot_reply=bot_reply,
        timestamp=datetime.utcnow()
    )
    db.add(new_message)
    db.commit()
    db.close()
    logger.info("✅ Conversation saved to database")
    logger.info("📤 Sending response back to WhatsApp")
    logger.info("=" * 50)

    # Send back Twilio-compatible XML
    return PlainTextResponse(str(twilio_resp), media_type="application/xml")
