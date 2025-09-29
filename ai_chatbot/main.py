from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from db import SessionLocal, Conversation
from datetime import datetime
from openai import OpenAI
from decouple import config

# Init FastAPI
app = FastAPI()

# Initialize OpenAI client
client = OpenAI(api_key=config("OPENAI_API_KEY"))

# Twilio Webhook Route
@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),   # WhatsApp user number
    Body: str = Form(...)    # Incoming message text
):
    # Create Twilio response
    twilio_resp = MessagingResponse()

    # Call OpenAI for a chatbot reply
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": Body}]
    )
    bot_reply = completion.choices[0].message.content

    # Add reply to Twilio response
    twilio_resp.message(bot_reply)

    # Save conversation to Neon DB
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

    # Send back Twilio-compatible XML
    return PlainTextResponse(str(twilio_resp), media_type="application/xml")
