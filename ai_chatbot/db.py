from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config
from datetime import datetime

# Use the single Neon connection string
DATABASE_URL = config("NEON_DB_URL")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Base class for models
Base = declarative_base()

# Define Conversations table
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_number = Column(String, index=True)     # WhatsApp user phone number
    user_message = Column(Text)                  # Incoming message
    bot_reply = Column(Text)                     # Chatbot’s reply
    timestamp = Column(DateTime, default=datetime.utcnow)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize DB
def init_db():
    Base.metadata.create_all(bind=engine)
