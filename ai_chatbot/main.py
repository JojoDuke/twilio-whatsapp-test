from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from db import SessionLocal, Conversation
from datetime import datetime
from openai import OpenAI
import logging
import os

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

    # Call OpenAI for a chatbot reply
    logger.info("🤖 Calling OpenAI API...")
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": Body}]
    )
    bot_reply = completion.choices[0].message.content
    logger.info(f"✅ OpenAI Response: {bot_reply}")

    # Add reply to Twilio response
    twilio_resp.message(bot_reply)

    # Save conversation to Neon DB
    logger.info("💾 Saving to database...")
    db = SessionLocal()
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
