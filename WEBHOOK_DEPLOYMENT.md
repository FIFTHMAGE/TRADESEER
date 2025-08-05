# 🚀 TradeSeer Bot - Webhook Deployment Guide

## New Approach: Webhook-Based Bot

This version uses **webhooks instead of polling** to avoid all asyncio/event loop issues that were causing deployment problems.

## Render Deployment (Recommended)

### Step 1: Setup Repository
1. Commit the new webhook files:
   - `webhook_bot.py` (new main bot file)
   - `requirements.txt` (updated dependencies)
   - `Procfile` (updated to use web service)

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Create "New Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python webhook_bot.py`

### Step 3: Set Environment Variables
Add these in Render dashboard:
- `TELEGRAM_BOT_TOKEN` = Your bot token from BotFather
- `ETHERSCAN_API_KEY` = Your Etherscan API key  
- `WEBHOOK_URL` = `https://your-app-name.onrender.com` (get this after deployment)

### Step 4: Activate Webhook
1. Wait for deployment to complete
2. Get your app URL from Render (e.g., `https://tradeseer-bot-xyz.onrender.com`)
3. Visit: `https://your-app-url.onrender.com/set_webhook`
4. You should see a success message

### Step 5: Test Your Bot
1. Start a chat with your bot on Telegram
2. Send `/start` - you should get a welcome message immediately
3. Try tracking a wallet: `/track 0x...`

## Why This Approach Works Better

### ✅ Advantages:
- **No asyncio issues** - Uses simple Flask web server
- **Instant responses** - Webhooks are faster than polling
- **More reliable** - No event loop conflicts
- **Resource efficient** - Only processes when needed
- **Cloud-friendly** - Web services are easier to deploy

### 🔄 How It Works:
1. Telegram sends messages to your webhook URL
2. Flask receives and processes them instantly
3. Background thread monitors wallets every 30 seconds
4. Notifications sent via Telegram API

## Health Check

Visit `https://your-app-url/health` to verify your bot is running.

## Troubleshooting

**Bot not responding?**
- Check webhook is set: visit `/set_webhook`
- Verify `WEBHOOK_URL` environment variable
- Check Render logs for errors

**No wallet notifications?**
- Verify Etherscan API key is valid
- Check tracked wallets have recent activity
- Monitor logs for API errors

**Deployment fails?**
- Check requirements.txt syntax
- Verify Python version compatibility
- Review Render build logs

## Commands Available

- `/start` - Welcome message and help
- `/track [wallet]` - Track a wallet address
- `/list` - Show all tracked wallets
- `/untrack [wallet]` - Stop tracking a wallet
- `/score [wallet]` - Get wallet smart score
- `/insights [wallet]` - Detailed wallet analysis

## Ready to Deploy!

This webhook approach should eliminate all the asyncio issues we've been fighting. It's a much cleaner, more reliable solution for cloud deployment.