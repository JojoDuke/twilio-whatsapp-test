from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
from openai import OpenAI
from mangum import Mangum
import os
import sys

# Add parent directory to path to import from ai_chatbot
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_chatbot'))

from db import SessionLocal, Conversation

# Init FastAPI
app = FastAPI()

# Initialize OpenAI client - use os.environ for Vercel
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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

# Health check endpoint
@app.get("/")
@app.get("/api")
async def health_check():
    return {"status": "ok", "message": "WhatsApp Bot API is running on Vercel"}

# Wrap the FastAPI app with Mangum for Vercel serverless
handler = Mangum(app)

