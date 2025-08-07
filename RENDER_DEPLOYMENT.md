# 🚀 Render Deployment Guide for TradeSeer Bot

This guide will help you deploy the TradeSeer Bot to Render with full wallet creation functionality.

## 📋 Prerequisites

1. **GitHub Repository** - Your code should be pushed to GitHub
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
4. **Etherscan API Key** - Get from [etherscan.io](https://etherscan.io/apis)

## 🔧 Step-by-Step Deployment

### 1. Connect GitHub Repository

1. Go to [render.com](https://render.com) and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your `TRADESEER` repository
5. Click **"Connect"**

### 2. Configure the Web Service

Use these settings:

- **Name**: `tradeseer-bot` (or any name you prefer)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`
- **Plan**: `Free` (or upgrade for better performance)

### 3. Set Environment Variables

Add these environment variables in Render:

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather | ✅ Yes |
| `ETHERSCAN_API_KEY` | Your Etherscan API key | ✅ Yes |
| `WEBHOOK_URL` | Will be set automatically by Render | ✅ Yes |
| `PORT` | Port number (default: 5000) | ❌ No |

### 4. Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete (usually 2-5 minutes)
3. Your bot will be available at: `https://your-app-name.onrender.com`

## 🔐 Wallet Creation Features

The deployed bot includes full wallet creation functionality:

### ✅ **Features Available:**
- 🔐 **Create new Ethereum wallets**
- 🔒 **Secure private key encryption**
- 💼 **Wallet management**
- 💱 **Token swapping on Base network**
- 📊 **Transaction history**
- 🔍 **Wallet analytics**

### 📱 **Usage Commands:**
```
create wallet name:MyWallet password:MyPassword123!
my wallets
swap [token_address] [amount]
```

## 🧪 Testing Your Deployment

### 1. Health Check
Visit your bot URL to see the health page:
```
https://your-app-name.onrender.com/health
```

### 2. Set Webhook
Visit this URL to set the Telegram webhook:
```
https://your-app-name.onrender.com/set_webhook
```

### 3. Test Bot Commands
Send these commands to your bot:
- `/start` - Main menu
- `create wallet name:TestWallet password:TestPass123!` - Create wallet
- `/help` - Get help

## 🔧 Troubleshooting

### Common Issues:

#### 1. Build Failures
**Problem**: Build fails during dependency installation
**Solution**: 
- Check that `requirements.txt` is in the root directory
- Ensure all dependencies are listed correctly
- Check Render logs for specific error messages

#### 2. Webhook Not Working
**Problem**: Bot doesn't respond to messages
**Solution**:
- Visit `/set_webhook` endpoint
- Check that `WEBHOOK_URL` is set correctly
- Verify `TELEGRAM_BOT_TOKEN` is valid

#### 3. Wallet Creation Not Working
**Problem**: "Create wallet" command fails
**Solution**:
- Check that all dependencies are installed (web3, eth-account, cryptography)
- Verify database permissions
- Check Render logs for error messages

### Check Logs:
1. Go to your Render dashboard
2. Click on your web service
3. Go to **"Logs"** tab
4. Look for error messages

## 📊 Monitoring

### Render Dashboard Features:
- **Real-time logs** - Monitor bot activity
- **Metrics** - CPU, memory usage
- **Deployments** - Track deployment history
- **Environment variables** - Manage configuration

### Bot Health Indicators:
Look for these messages in logs:
```
✅ Web3 available for full blockchain functionality
✅ Account creation available
✅ Cryptography features available
✅ Wallet features available
✅ Database initialized with wallet connection support
```

## 🔄 Auto-Deploy

Render automatically deploys when you push to your main branch:

1. Make changes to your code
2. Push to GitHub: `git push origin main`
3. Render automatically detects changes
4. New deployment starts automatically

## 💰 Cost Optimization

### Free Tier Limits:
- **750 hours/month** (enough for 24/7 operation)
- **512 MB RAM**
- **Shared CPU**
- **Sleep after 15 minutes of inactivity**

### Upgrade Options:
- **Starter Plan** ($7/month) - Always on, more resources
- **Standard Plan** ($25/month) - Better performance

## 🔒 Security Best Practices

1. **Environment Variables**: Never commit tokens to git
2. **Database**: SQLite database is stored securely on Render
3. **Private Keys**: Encrypted with user passwords
4. **HTTPS**: All communications are encrypted

## 📞 Support

If you encounter issues:

1. **Check Render logs** for error messages
2. **Verify environment variables** are set correctly
3. **Test locally** first to isolate issues
4. **Check the troubleshooting guide** in `WALLET_TROUBLESHOOTING.md`

## 🎉 Success!

Once deployed, your bot will have:
- ✅ Full wallet creation functionality
- ✅ Multi-chain support (Ethereum + Base)
- ✅ Real-time transaction monitoring
- ✅ Secure private key management
- ✅ Token swapping capabilities

Your bot URL will be: `https://your-app-name.onrender.com`

---

**Need help?** Check the logs in your Render dashboard or refer to the troubleshooting guides. 