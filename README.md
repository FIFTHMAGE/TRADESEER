# TradeSeer Bot 🔮

A revolutionary Telegram bot that tracks smart wallets and provides intelligent alerts before they trade on Base network.

## ✨ Unique Features

### 🎯 Smart Wallet Scoring
- **AI-powered scoring system** that analyzes transaction patterns
- **0-100 score** based on volume, frequency, and success rate
- **Automatic insights** for each tracked wallet

### 📊 Transaction Insights
- **Real-time analytics** for each wallet
- **Volume tracking** and transaction history
- **Activity patterns** and trading behavior analysis

### 🎨 Customizable Experience
- **Multiple notification styles**: Psychic, Professional, Minimal
- **Adjustable alert thresholds**
- **Personalized dashboard** with portfolio overview

### ⚡ Enhanced User Experience
- **One-click wallet tracking** - just paste the address!
- **Interactive buttons** instead of typing commands
- **Smart validation** and error handling
- **Visual dashboard** with portfolio metrics

## 🚀 How It Works

1. **Start the bot** with `/start`
2. **Click "Track New Wallet"**
3. **Paste any wallet address** - no commands needed!
4. **Get instant insights** and smart scoring
5. **Receive real-time alerts** when wallets receive ETH

## 📱 User Interface

### Main Menu
- 🔍 **Track New Wallet** - Paste any address to start tracking
- 📋 **My Tracked Wallets** - View all tracked wallets with scores
- ⚙️ **Settings** - Customize alerts and preferences
- 📊 **Dashboard** - Portfolio overview and analytics

### Smart Features
- **Automatic wallet analysis** when you add a new address
- **Instant scoring** (0-100) based on transaction patterns
- **Volume insights** and activity metrics
- **Success rate analysis** for each wallet

## 🎯 Smart Scoring System

The bot analyzes each wallet and provides a **0-100 score** based on:

- **Transaction Volume** - Higher volume = higher score
- **Activity Frequency** - More active wallets score better
- **Success Rate** - Successful transactions boost score
- **Recent Activity** - Recent transactions weighted more heavily

### Score Categories:
- **70-100**: 🚀 High-value wallets with strong patterns
- **40-69**: 📈 Promising wallets with moderate activity
- **0-39**: ⚠️ Low activity wallets (monitor for changes)

## 📊 Dashboard Analytics

Get a complete overview of your tracking portfolio:

- **Total Tracked Wallets** - How many you're monitoring
- **Average Score** - Overall quality of your selections
- **Total Volume** - Combined ETH volume across all wallets
- **Active Wallets** - Number of high-scoring wallets

## 🎨 Customization Options

### Notification Styles
- **🔮 Psychic**: "Psychic Ping" with mysterious vibes
- **💼 Professional**: Clean, business-like alerts
- **🔔 Minimal**: Simple, direct notifications

### Alert Thresholds
- **Customizable ETH amounts** for triggering alerts
- **Default: 0.2 ETH** (easily adjustable)

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/FIFTHMAGE/TRADESEER.git
   cd TradeSeer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ETHERSCAN_API_KEY=your_etherscan_api_key
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from @BotFather
- `ETHERSCAN_API_KEY`: Your Etherscan API key for Base network

## 🔮 How It Works

The bot continuously monitors tracked wallet addresses by:
1. **Analyzing transaction patterns** for each wallet
2. **Calculating smart scores** based on volume and activity
3. **Detecting incoming ETH transfers** (>0.2 ETH by default)
4. **Sending personalized alerts** with customizable styles
5. **Providing real-time insights** and portfolio analytics

## 🛡️ Security

- Sensitive credentials are stored in `.env` file (not committed to git)
- API keys and tokens are validated on startup
- Error handling for network issues and API failures
- Secure HTTP API calls for notifications

## Requirements

- Python 3.7+
- python-telegram-bot[job-queue]
- requests
- python-dotenv

## 🚀 What Makes It Unique

1. **🎯 Smart Scoring** - No other bot analyzes wallet patterns like this
2. **📊 Real Analytics** - Actual transaction insights, not just alerts
3. **🎨 Customizable** - Multiple notification styles and preferences
4. **⚡ One-Click Tracking** - Just paste addresses, no commands needed
5. **📱 Beautiful UI** - Interactive buttons and visual feedback
6. **🔮 Predictive Alerts** - AI-powered pattern recognition

## License

MIT License
