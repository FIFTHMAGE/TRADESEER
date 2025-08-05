# 🚀 Deploy TradeSeer Bot to Cloud

## Option 1: Railway (Recommended - Free)

### Step 1: Prepare Your Code
1. Create a GitHub repository
2. Upload your TradeSeer folder to GitHub
3. Make sure you have these files:
   - `bot.py`
   - `requirements.txt`
   - `Procfile`
   - `runtime.txt`
   - `.gitignore`

### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your TradeSeer repository
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `ETHERSCAN_API_KEY` = your Etherscan API key
6. Deploy!

### Step 3: Test
1. Send `/start` to your bot on Telegram
2. Add some wallets to track
3. Wait for notifications!

## Option 2: Render (Alternative Free Option)

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Create "New Web Service"
4. Connect your GitHub repository
5. Add environment variables (same as Railway)
6. Deploy!

## Environment Variables Needed

Make sure to set these in your cloud platform:
- `TELEGRAM_BOT_TOKEN` = Your Telegram bot token
- `ETHERSCAN_API_KEY` = Your Etherscan API key

## Benefits of Cloud Deployment

✅ **24/7 Operation** - Works even when your computer is off
✅ **Mobile Access** - Receive notifications on your phone
✅ **No Manual Start** - Automatically runs
✅ **Reliable** - Professional hosting infrastructure
✅ **Scalable** - Can handle multiple users

## Troubleshooting

- **Bot not responding**: Check environment variables are set correctly
- **No notifications**: Verify wallet addresses are valid and have activity
- **Deployment fails**: Check logs in your cloud platform dashboard 