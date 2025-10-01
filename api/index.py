from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database setup - use environment variable
DATABASE_URL = os.environ.get("NEON_DB_URL")
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()

# Define Conversations table
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_number = Column(String, index=True)
    user_message = Column(Text)
    bot_reply = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    return {"status": "ok", "message": "WhatsApp Bot API is running on Railway"}

