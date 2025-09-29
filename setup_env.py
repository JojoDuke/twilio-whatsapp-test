#!/usr/bin/env python3
"""
Setup script to help users create their .env file
"""
import os

def create_env_file():
    """Create a .env file with user input"""
    env_path = os.path.join("ai_chatbot", ".env")
    
    print("🚀 WhatsApp AI Chatbot Environment Setup")
    print("=" * 50)
    print("This script will help you create your .env file with the necessary configuration.")
    print()
    
    # Get OpenAI API Key
    openai_key = input("Enter your OpenAI API Key: ").strip()
    if not openai_key:
        print("❌ OpenAI API Key is required!")
        return False
    
    # Get Database URL
    print("\n📊 Database Configuration")
    print("You can use Neon (https://neon.tech/) for free PostgreSQL hosting")
    database_url = input("Enter your PostgreSQL Database URL: ").strip()
    if not database_url:
        print("❌ Database URL is required!")
        return False
    
    # Optional Twilio configuration
    print("\n📱 Twilio Configuration (Optional - press Enter to skip)")
    twilio_sid = input("Enter your Twilio Account SID (optional): ").strip()
    twilio_token = input("Enter your Twilio Auth Token (optional): ").strip()
    
    # Server configuration
    print("\n🌐 Server Configuration")
    port = input("Enter server port (default: 8000): ").strip() or "8000"
    host = input("Enter server host (default: 0.0.0.0): ").strip() or "0.0.0.0"
    
    # Create .env content
    env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={openai_key}

# Database Configuration (PostgreSQL/Neon)
DATABASE_URL={database_url}
"""
    
    if twilio_sid and twilio_token:
        env_content += f"""
# Twilio Configuration
TWILIO_ACCOUNT_SID={twilio_sid}
TWILIO_AUTH_TOKEN={twilio_token}
"""
    
    env_content += f"""
# Server Configuration
PORT={port}
HOST={host}
"""
    
    # Write .env file
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"\n✅ Environment file created successfully at: {env_path}")
        print("\n🔒 IMPORTANT: Never commit your .env file to version control!")
        print("The .env file contains sensitive information and is already ignored by git.")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    """Main setup function"""
    if not os.path.exists("ai_chatbot"):
        print("❌ ai_chatbot directory not found. Please run this script from the project root.")
        return
    
    env_path = os.path.join("ai_chatbot", ".env")
    if os.path.exists(env_path):
        overwrite = input(f"⚠️  .env file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    if create_env_file():
        print("\n🎉 Setup complete! You can now:")
        print("1. cd ai_chatbot")
        print("2. python -m venv venv")
        print("3. Activate your virtual environment")
        print("4. pip install -r requirements.txt")
        print("5. python init_db.py")
        print("6. uvicorn main:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    main()
