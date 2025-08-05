#!/usr/bin/env python3
"""
TradeSeer Bot - Webhook Version for Cloud Deployment
This version uses Flask webhooks instead of polling to avoid asyncio issues
"""

import os
import json
import requests
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')  # Will be set by Render
PORT = int(os.getenv('PORT', 5000))

# Validate environment variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
if not ETHERSCAN_API_KEY:
    raise ValueError("ETHERSCAN_API_KEY not found in environment variables")

# Global storage
user_wallets = {}
user_settings = {}
running = True

# Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Send a message to a Telegram chat"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def set_webhook(self, webhook_url):
        """Set the webhook URL"""
        url = f"{self.base_url}/setWebhook"
        data = {'url': webhook_url}
        response = requests.post(url, data=data)
        return response.json()
    
    def delete_webhook(self):
        """Delete the webhook"""
        url = f"{self.base_url}/deleteWebhook"
        response = requests.post(url)
        return response.json()

# Initialize bot
bot = TelegramBot(TELEGRAM_BOT_TOKEN)

def get_wallet_score(wallet_address):
    """Calculate a smart wallet score based on transaction patterns"""
    url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] != "1":
        return 0
    
    transactions = data["result"][:50]  # Last 50 transactions
    if not transactions:
        return 0
    
    score = 0
    total_volume = 0
    successful_trades = 0
    
    for tx in transactions:
        value = int(tx["value"]) / 10**18  # Convert from wei to ETH
        total_volume += value
        
        if tx["isError"] == "0":  # Successful transaction
            successful_trades += 1
            score += 10
        
        # Bonus for large transactions
        if value > 1:
            score += 20
        elif value > 0.1:
            score += 10
    
    # Calculate final score
    success_rate = successful_trades / len(transactions) if transactions else 0
    volume_bonus = min(total_volume * 5, 100)  # Cap at 100
    
    final_score = int(score * success_rate + volume_bonus)
    return min(final_score, 100)  # Cap at 100

def get_wallet_insights(wallet_address):
    """Get detailed insights about a wallet"""
    url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] != "1":
        return "❌ Unable to fetch wallet data"
    
    transactions = data["result"][:20]  # Last 20 transactions
    if not transactions:
        return "📭 No transactions found for this wallet"
    
    # Analyze patterns
    total_volume = sum(int(tx["value"]) / 10**18 for tx in transactions)
    successful_txs = sum(1 for tx in transactions if tx["isError"] == "0")
    failed_txs = len(transactions) - successful_txs
    
    # Get recent activity
    recent_tx = transactions[0]
    last_activity = datetime.fromtimestamp(int(recent_tx["timeStamp"]))
    days_ago = (datetime.now() - last_activity).days
    
    insights = f"""
🔍 <b>Wallet Insights</b>
📊 <b>Recent Activity:</b> {days_ago} days ago
💰 <b>Volume (Last 20 TXs):</b> {total_volume:.4f} ETH
✅ <b>Successful:</b> {successful_txs}
❌ <b>Failed:</b> {failed_txs}
📈 <b>Success Rate:</b> {(successful_txs/len(transactions)*100):.1f}%
🎯 <b>Smart Score:</b> {get_wallet_score(wallet_address)}/100
"""
    
    return insights

def check_wallet_activity(wallet_address):
    """Check if wallet has new transactions in the last 30 minutes"""
    url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] != "1":
        return False, None
    
    transactions = data["result"][:5]  # Check last 5 transactions
    cutoff_time = datetime.now() - timedelta(minutes=30)
    
    for tx in transactions:
        tx_time = datetime.fromtimestamp(int(tx["timeStamp"]))
        if tx_time > cutoff_time:
            value = int(tx["value"]) / 10**18
            if value > 0:  # Only notify for transactions with value
                return True, {
                    'hash': tx['hash'],
                    'value': value,
                    'from': tx['from'],
                    'to': tx['to'],
                    'timestamp': tx_time
                }
    
    return False, None

def monitor_wallets():
    """Background thread to monitor wallet activity"""
    print("🔮 Starting wallet monitoring...")
    
    while running:
        try:
            for user_id, wallets in user_wallets.items():
                for wallet in wallets:
                    has_activity, tx_data = check_wallet_activity(wallet)
                    
                    if has_activity and tx_data:
                        value = tx_data['value']
                        message = f"""
🚨 <b>Wallet Activity Detected!</b>

💰 <b>Amount:</b> {value:.4f} ETH
🏦 <b>Wallet:</b> <code>{wallet}</code>
🔗 <b>Hash:</b> <code>{tx_data['hash'][:20]}...</code>
⏰ <b>Time:</b> {tx_data['timestamp'].strftime('%H:%M:%S')}

🎯 <b>Smart Score:</b> {get_wallet_score(wallet)}/100
"""
                        
                        bot.send_message(user_id, message)
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"Error in monitoring: {e}")
            time.sleep(60)  # Wait longer on error

def handle_start(chat_id):
    """Handle /start command"""
    message = """
🔮 <b>Welcome to TradeSeer!</b>

🎯 Track smart wallets and get real-time notifications
📊 Analyze wallet performance with AI insights
⚡ Get alerts for high-value transactions

<b>Commands:</b>
/track [wallet] - Track a wallet
/list - Show tracked wallets  
/untrack [wallet] - Stop tracking
/score [wallet] - Get wallet score
/insights [wallet] - Detailed analysis

Ready to start tracking? 🚀
"""
    bot.send_message(chat_id, message)

def handle_track(chat_id, wallet_address):
    """Handle /track command"""
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address: /track 0x...")
        return
    
    # Validate wallet address
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        bot.send_message(chat_id, "❌ Invalid wallet address format")
        return
    
    # Initialize user wallets if not exists
    if chat_id not in user_wallets:
        user_wallets[chat_id] = []
    
    # Check if already tracking
    if wallet_address.lower() in [w.lower() for w in user_wallets[chat_id]]:
        bot.send_message(chat_id, "⚠️ Already tracking this wallet!")
        return
    
    # Add wallet
    user_wallets[chat_id].append(wallet_address)
    
    # Get initial score
    score = get_wallet_score(wallet_address)
    
    message = f"""
✅ <b>Wallet Added to Tracking!</b>

🏦 <b>Address:</b> <code>{wallet_address}</code>
🎯 <b>Smart Score:</b> {score}/100
📡 <b>Status:</b> Now monitoring for activity

You'll receive notifications for new transactions! 🔔
"""
    bot.send_message(chat_id, message)

def handle_list(chat_id):
    """Handle /list command"""
    if chat_id not in user_wallets or not user_wallets[chat_id]:
        bot.send_message(chat_id, "📭 You're not tracking any wallets yet.\n\nUse /track [wallet] to start!")
        return
    
    message = "📋 <b>Your Tracked Wallets:</b>\n\n"
    
    for i, wallet in enumerate(user_wallets[chat_id], 1):
        score = get_wallet_score(wallet)
        short_address = f"{wallet[:8]}...{wallet[-6:]}"
        message += f"{i}. <code>{short_address}</code> (Score: {score}/100)\n"
    
    message += f"\n💡 Total: {len(user_wallets[chat_id])} wallets"
    bot.send_message(chat_id, message)

def handle_untrack(chat_id, wallet_address):
    """Handle /untrack command"""
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address: /untrack 0x...")
        return
    
    if chat_id not in user_wallets:
        bot.send_message(chat_id, "📭 You're not tracking any wallets")
        return
    
    # Find and remove wallet
    for wallet in user_wallets[chat_id]:
        if wallet.lower() == wallet_address.lower():
            user_wallets[chat_id].remove(wallet)
            bot.send_message(chat_id, f"✅ Stopped tracking wallet: <code>{wallet}</code>")
            return
    
    bot.send_message(chat_id, "❌ Wallet not found in your tracking list")

def handle_score(chat_id, wallet_address):
    """Handle /score command"""
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address: /score 0x...")
        return
    
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        bot.send_message(chat_id, "❌ Invalid wallet address format")
        return
    
    score = get_wallet_score(wallet_address)
    
    # Score interpretation
    if score >= 80:
        rating = "🔥 Extremely Smart"
        emoji = "🚀"
    elif score >= 60:
        rating = "⭐ Very Smart"
        emoji = "📈"
    elif score >= 40:
        rating = "✅ Smart"
        emoji = "💎"
    elif score >= 20:
        rating = "⚠️ Average"
        emoji = "📊"
    else:
        rating = "❌ Low Activity"
        emoji = "💤"
    
    message = f"""
{emoji} <b>Wallet Score Analysis</b>

🏦 <b>Address:</b> <code>{wallet_address}</code>
🎯 <b>Smart Score:</b> {score}/100
📊 <b>Rating:</b> {rating}

💡 <i>Based on transaction patterns, success rate, and volume</i>
"""
    
    bot.send_message(chat_id, message)

def handle_insights(chat_id, wallet_address):
    """Handle /insights command"""
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address: /insights 0x...")
        return
    
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        bot.send_message(chat_id, "❌ Invalid wallet address format")
        return
    
    insights = get_wallet_insights(wallet_address)
    bot.send_message(chat_id, insights)

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        update = request.get_json()
        
        if 'message' not in update:
            return jsonify({'status': 'ok'})
        
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        print(f"Received message: {text} from {chat_id}")
        
        if text.startswith('/start'):
            handle_start(chat_id)
        
        elif text.startswith('/track'):
            parts = text.split(' ', 1)
            wallet = parts[1] if len(parts) > 1 else None
            handle_track(chat_id, wallet)
        
        elif text.startswith('/list'):
            handle_list(chat_id)
        
        elif text.startswith('/untrack'):
            parts = text.split(' ', 1)
            wallet = parts[1] if len(parts) > 1 else None
            handle_untrack(chat_id, wallet)
        
        elif text.startswith('/score'):
            parts = text.split(' ', 1)
            wallet = parts[1] if len(parts) > 1 else None
            handle_score(chat_id, wallet)
        
        elif text.startswith('/insights'):
            parts = text.split(' ', 1)
            wallet = parts[1] if len(parts) > 1 else None
            handle_insights(chat_id, wallet)
        
        else:
            bot.send_message(chat_id, "❌ Unknown command. Type /start for help.")
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'wallets_tracked': len(user_wallets)})

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set webhook URL"""
    webhook_url = f"{WEBHOOK_URL}/webhook"
    result = bot.set_webhook(webhook_url)
    return jsonify(result)

if __name__ == '__main__':
    print("🔮 TradeSeer Bot Starting...")
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_wallets, daemon=True)
    monitor_thread.start()
    print("📡 Monitoring thread started")
    
    # Set webhook if URL is provided
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        result = bot.set_webhook(webhook_url)
        print(f"Webhook set: {result}")
    
    # Start Flask app
    print(f"🚀 Starting server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)