# Deploying to Vercel

This guide will help you deploy your WhatsApp bot to Vercel, eliminating the need for ngrok.

## Prerequisites

- A [Vercel account](https://vercel.com/signup) (free tier works fine)
- Your environment variables ready:
  - `OPENAI_API_KEY`
  - `NEON_DB_URL`

## Deployment Steps

### 1. Install Vercel CLI (Optional but recommended)

```bash
npm install -g vercel
```

### 2. Deploy via Vercel Dashboard (Easiest Method)

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add Vercel deployment configuration"
   git push origin master
   ```

2. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**

3. **Click "Add New Project"**

4. **Import your GitHub repository**

5. **Configure your project**:
   - Framework Preset: `Other`
   - Root Directory: `./` (leave as default)
   - Build Command: (leave empty)
   - Output Directory: (leave empty)

6. **Add Environment Variables**:
   Click on "Environment Variables" and add:
   - `OPENAI_API_KEY` = your OpenAI API key
   - `NEON_DB_URL` = your Neon PostgreSQL connection string
   
   Example format for `NEON_DB_URL`:
   ```
   postgresql://user:password@host.neon.tech/dbname?sslmode=require
   ```

7. **Click "Deploy"**

8. **Wait for deployment** (usually takes 1-2 minutes)

### 3. Deploy via Vercel CLI (Alternative Method)

If you prefer using the command line:

```bash
# Login to Vercel
vercel login

# Deploy (from project root)
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No
# - What's your project's name? (enter a name)
# - In which directory is your code located? ./

# Add environment variables
vercel env add OPENAI_API_KEY
# (paste your key when prompted)

vercel env add NEON_DB_URL
# (paste your database URL when prompted)

# Deploy to production
vercel --prod
```

## After Deployment

### 1. Get Your Vercel URL

After deployment, you'll receive a URL like:
```
https://your-project-name.vercel.app
```

### 2. Update Twilio Webhook

1. Go to your [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** > **Try it out** > **Send a WhatsApp message** (or your WhatsApp Business setup)
3. In the **Sandbox Settings** or **WhatsApp Senders**, find the webhook configuration
4. Update the webhook URL to:
   ```
   https://your-project-name.vercel.app/whatsapp
   ```
5. Make sure the HTTP method is set to `POST`
6. Save the configuration

### 3. Test Your Bot

Send a WhatsApp message to your Twilio number and verify:
- You receive a response from the bot
- The conversation is saved to your database

## Monitoring and Logs

- View logs in [Vercel Dashboard](https://vercel.com/dashboard) > Your Project > Logs
- Monitor function executions and errors
- Check for any environment variable issues

## Troubleshooting

### Issue: "Module not found" errors
- Make sure `requirements.txt` is in the root directory
- Verify all dependencies are listed

### Issue: Database connection fails
- Check that `NEON_DB_URL` is correctly set in Vercel environment variables
- Ensure the connection string includes `?sslmode=require`
- Verify your Neon database is active

### Issue: OpenAI API errors
- Verify `OPENAI_API_KEY` is correctly set
- Check your OpenAI account has available credits

### Issue: Webhook not responding
- Verify the webhook URL in Twilio is correct
- Check Vercel deployment logs for errors
- Test the health check endpoint: `https://your-project-name.vercel.app/`

## Project Structure

```
twilio-wa-bot/
├── api/
│   └── index.py          # Vercel serverless function entry point
├── ai_chatbot/
│   ├── db.py            # Database configuration
│   ├── main.py          # Original local development file
│   └── requirements.txt # Dependencies (kept for reference)
├── requirements.txt      # Root dependencies for Vercel
├── vercel.json          # Vercel configuration
└── .vercelignore        # Files to exclude from deployment
```

## Cost Considerations

- **Vercel Free Tier**: Includes 100GB bandwidth and 100 hours of serverless function execution per month
- **Neon Free Tier**: Includes 3GB storage and 100 hours of compute per month
- **OpenAI**: Pay per token usage

For a typical chatbot with moderate usage, the free tiers should be sufficient.

## Updating Your Deployment

Whenever you push changes to your GitHub repository:
- Vercel will automatically redeploy (if you connected via GitHub)
- You can also manually redeploy from the Vercel dashboard

Or via CLI:
```bash
vercel --prod
```

## Rollback

If something goes wrong, you can rollback to a previous deployment:
1. Go to Vercel Dashboard > Your Project > Deployments
2. Find a previous successful deployment
3. Click the three dots menu > "Promote to Production"

---

**Need Help?** 
- [Vercel Documentation](https://vercel.com/docs)
- [Twilio WhatsApp Documentation](https://www.twilio.com/docs/whatsapp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

