# TradeSeer Bot 🔮

A Telegram bot that tracks smart wallets and provides alerts before they trade on Base network.

## Features

- **Smart Wallet Tracking**: Monitor specific wallet addresses for incoming ETH
- **Real-time Alerts**: Get notified when tracked wallets receive significant ETH inflows
- **Psychic Monitoring**: Continuous background monitoring with 30-second intervals
- **Easy Management**: Simple commands to track/untrack wallets

## Commands

- `/start` - Welcome message and command overview
- `/track <wallet_address>` - Start tracking a wallet address
- `/untrack <wallet_address>` - Stop tracking a wallet address
- `/list` - Show all currently tracked wallets

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

## How it Works

The bot continuously monitors tracked wallet addresses by:
1. Checking recent transactions on Base network
2. Detecting incoming ETH transfers (>0.2 ETH)
3. Sending alerts to users when significant inflows are detected

## Security

- Sensitive credentials are stored in `.env` file (not committed to git)
- API keys and tokens are validated on startup
- Error handling for network issues and API failures

## Requirements

- Python 3.7+
- python-telegram-bot
- requests
- python-dotenv

## License

MIT License
