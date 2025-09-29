# WhatsApp AI Chatbot with Twilio

A simple WhatsApp chatbot powered by OpenAI's GPT-3.5-turbo, built with FastAPI and integrated with Twilio for WhatsApp messaging. The bot stores conversation history in a PostgreSQL database.

## Features

- 🤖 AI-powered responses using OpenAI GPT-3.5-turbo
- 📱 WhatsApp integration via Twilio
- 💾 Conversation history stored in PostgreSQL database
- 🚀 Fast and lightweight FastAPI backend
- 🔒 Secure environment variable management

## Prerequisites

- Python 3.8 or higher
- OpenAI API account and API key
- Twilio account with WhatsApp sandbox or approved WhatsApp Business account
- PostgreSQL database (we recommend [Neon](https://neon.tech/) for free hosting)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd twilio-wa-bot
   ```

2. **Create and activate virtual environment**
   ```bash
   cd ai_chatbot
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the `ai_chatbot` directory with the following variables:
   ```env
   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Database Configuration (PostgreSQL/Neon)
   DATABASE_URL=postgresql://username:password@host:port/database_name
   
   # Optional: Twilio Configuration (for additional features)
   TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
   TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
   ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```

## Configuration

### OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file

### Database Setup (Neon - Recommended)
1. Go to [Neon](https://neon.tech/) and create a free account
2. Create a new project
3. Copy the connection string from your dashboard
4. Add it to your `.env` file as `DATABASE_URL`

### Twilio WhatsApp Setup
1. Create a [Twilio account](https://www.twilio.com/)
2. Set up WhatsApp sandbox or get WhatsApp Business API approved
3. Configure your webhook URL to point to `https://your-domain.com/whatsapp`
4. For local development, you can use ngrok to expose your local server

## Running the Application

1. **Start the FastAPI server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **For local development with ngrok** (optional)
   ```bash
   # In a separate terminal
   ngrok http 8000
   ```
   Then use the ngrok URL as your Twilio webhook URL.

## API Endpoints

- `POST /whatsapp` - Webhook endpoint for Twilio WhatsApp messages

## Project Structure

```
ai_chatbot/
├── main.py          # FastAPI application and webhook handler
├── db.py            # Database models and configuration
├── init_db.py       # Database initialization script
├── requirements.txt # Python dependencies
├── .env            # Environment variables (create this)
├── .gitignore      # Git ignore rules
└── venv/           # Virtual environment (excluded from git)
```

## Database Schema

The application uses a simple `conversations` table with the following structure:
- `id`: Primary key
- `user_number`: WhatsApp user's phone number
- `user_message`: Message sent by the user
- `bot_reply`: AI-generated response
- `timestamp`: When the conversation occurred

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security Notes

- Never commit your `.env` file to version control
- Keep your OpenAI API key secure
- Use environment variables for all sensitive configuration
- Consider implementing rate limiting for production use

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Note**: This is a basic implementation. For production use, consider adding:
- Error handling and logging
- Rate limiting
- User authentication
- Message validation
- Webhook signature verification
- Database connection pooling
- Health check endpoints

