# Deploying to Railway

This guide will help you deploy your WhatsApp bot to Railway, eliminating the need for ngrok.

## Prerequisites

- A [Railway account](https://railway.app/) (free tier: $5 credit/month)
- Your environment variables ready:
  - `OPENAI_API_KEY`
  - `NEON_DB_URL`

## Deployment Steps

### 1. Create Railway Project

1. **Go to [Railway](https://railway.app/)**

2. **Sign in with GitHub**

3. **Click "New Project"**

4. **Select "Deploy from GitHub repo"**

5. **Choose your `twilio-wa-bot` repository**

### 2. Configure Environment Variables

1. **In your Railway project**, click on your service

2. **Go to the "Variables" tab**

3. **Add the following variables**:
   - `OPENAI_API_KEY` = your OpenAI API key
   - `NEON_DB_URL` = your Neon PostgreSQL connection string
   
   Example format for `NEON_DB_URL`:
   ```
   postgresql://user:password@host.neon.tech/dbname?sslmode=require
   ```

### 3. Deploy

Railway will automatically:
- Detect your `Procfile`
- Install dependencies from `requirements.txt`
- Run the start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Wait for the deployment to complete (usually 2-3 minutes).

### 4. Get Your Railway URL

1. Go to **Settings** tab in your Railway service
2. Scroll to **Networking** section
3. Click **Generate Domain**
4. You'll get a URL like: `https://your-project.up.railway.app`

### 5. Update Twilio Webhook

1. Go to your [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** > **Try it out** > **Send a WhatsApp message** (or your WhatsApp Business setup)
3. In the **Sandbox Settings** or **WhatsApp Senders**, find the webhook configuration
4. Update the webhook URL to:
   ```
   https://your-project.up.railway.app/whatsapp
   ```
5. Make sure the HTTP method is set to `POST`
6. Save the configuration

### 6. Test Your Bot

Send a WhatsApp message to your Twilio number and verify:
- You receive a response from the bot
- The conversation is saved to your database

## Monitoring and Logs

- View logs in Railway Dashboard > Your Service > Deployments > View Logs
- Monitor resource usage and costs
- Check for any deployment or runtime errors

## Troubleshooting

### Issue: "Module not found" errors
- Check that all dependencies are in `requirements.txt`
- Verify the deployment logs for the exact missing module
- Add any missing dependencies and redeploy

### Issue: Database connection fails
- Check that `NEON_DB_URL` is correctly set in Railway environment variables
- Ensure the connection string includes `?sslmode=require`
- Verify your Neon database is active and not paused

### Issue: OpenAI API errors
- Verify `OPENAI_API_KEY` is correctly set
- Check your OpenAI account has available credits

### Issue: Webhook not responding
- Verify the webhook URL in Twilio is correct
- Check Railway deployment logs for errors
- Test the health check endpoint: `https://your-project.up.railway.app/`

### Issue: Port errors
- Railway automatically provides the `$PORT` variable
- Make sure your Procfile uses `$PORT` (not a hardcoded port)

## Project Structure

```
twilio-wa-bot/
├── ai_chatbot/
│   ├── db.py            # Database configuration
│   ├── main.py          # FastAPI application
│   ├── init_db.py       # Database initialization
│   └── requirements.txt # Local dev dependencies
├── Procfile             # Railway start command
├── requirements.txt     # Production dependencies
└── .gitignore          # Git ignore rules
```

## Cost Considerations

- **Railway Free Tier**: $5 credit per month
  - Usually sufficient for small to medium traffic bots
  - Approximately 500 hours of uptime per month
- **Neon Free Tier**: 3GB storage, 100 hours of compute per month
- **OpenAI**: Pay per token usage

For a typical chatbot with moderate usage, the free tiers should be sufficient.

## Updating Your Deployment

Railway automatically redeploys when you push to your GitHub repository:

```bash
git add .
git commit -m "Your update message"
git push origin master
```

Railway will detect the push and redeploy automatically.

## Manual Redeployment

If needed, you can manually trigger a redeploy:
1. Go to Railway Dashboard > Your Service
2. Click on the latest deployment
3. Click "Redeploy"

## Rollback

If something goes wrong, you can rollback:
1. Go to Railway Dashboard > Your Service > Deployments
2. Find a previous successful deployment
3. Click the three dots menu > "Redeploy"

## Pausing/Resuming

To save credits when not in use:
1. Railway Dashboard > Your Service > Settings
2. Scroll to **Danger Zone**
3. Click **Pause Service** (or Resume)

---

## Why Railway?

✅ **Better for FastAPI** - Runs actual servers, not serverless functions  
✅ **No cold starts** - Your app stays warm  
✅ **Automatic HTTPS** - Secure by default  
✅ **Easy deployments** - Push to GitHub and it deploys  
✅ **Great logs** - Easy debugging  
✅ **Fair pricing** - $5/month free credit  

**Need Help?** 
- [Railway Documentation](https://docs.railway.app/)
- [Twilio WhatsApp Documentation](https://www.twilio.com/docs/whatsapp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
