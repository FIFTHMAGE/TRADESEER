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

def is_wallet_address(text):
    """Check if text contains a valid wallet address"""
    import re
    # Ethereum address pattern: 0x followed by 40 hex characters
    pattern = r'\b0x[a-fA-F0-9]{40}\b'
    match = re.search(pattern, text)
    return match.group() if match else None

def get_token_transfers(wallet_address, chain, days=1):
    """Get token transfers for a wallet in the last X days"""
    from datetime import datetime, timedelta
    
    if chain == "ethereum":
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    elif chain == "base":
        url = f"https://api.basescan.org/api?module=account&action=tokentx&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    else:
        return []
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "1" and "result" in data:
            transfers = data["result"]
            
            # Filter by time period
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            recent_transfers = []
            
            for transfer in transfers:
                tx_time = datetime.utcfromtimestamp(int(transfer["timeStamp"]))
                if tx_time > cutoff_time:
                    transfer["chain"] = chain
                    recent_transfers.append(transfer)
            
            return recent_transfers
        return []
    except Exception as e:
        print(f"Error fetching {chain} token transfers: {e}")
        return []

def analyze_token_purchases(wallet_address, days=1):
    """Analyze what tokens a wallet bought in the last X days"""
    # Get token transfers from both chains
    eth_transfers = get_token_transfers(wallet_address, "ethereum", days)
    base_transfers = get_token_transfers(wallet_address, "base", days)
    
    all_transfers = eth_transfers + base_transfers
    all_transfers.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    # Filter for incoming transfers (purchases)
    purchases = []
    for transfer in all_transfers:
        if transfer["to"].lower() == wallet_address.lower():
            purchases.append(transfer)
    
    return purchases

def get_transactions_from_chain(wallet_address, chain):
    """Get transactions from a specific chain"""
    if chain == "ethereum":
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    elif chain == "base":
        url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    else:
        return []
    
    try:
        response = requests.get(url)
        data = response.json()
    
        if data["status"] == "1" and "result" in data:
            transactions = data["result"]
            # Add chain info to each transaction
            for tx in transactions:
                tx["chain"] = chain
            return transactions
        return []
    except Exception as e:
        print(f"Error fetching {chain} transactions: {e}")
        return []

def get_wallet_score(wallet_address):
    """Calculate a smart wallet score based on transaction patterns across Ethereum and Base"""
    # Get transactions from both Ethereum and Base
    eth_transactions = get_transactions_from_chain(wallet_address, "ethereum")
    base_transactions = get_transactions_from_chain(wallet_address, "base")
    
    # Combine and sort by timestamp (most recent first)
    all_transactions = eth_transactions + base_transactions
    all_transactions.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    transactions = all_transactions[:50]  # Last 50 transactions across both chains
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
    """Get detailed insights about a wallet across Ethereum and Base"""
    # Get transactions from both chains
    eth_transactions = get_transactions_from_chain(wallet_address, "ethereum")
    base_transactions = get_transactions_from_chain(wallet_address, "base")
    
    # Combine and sort by timestamp (most recent first)
    all_transactions = eth_transactions + base_transactions
    all_transactions.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    transactions = all_transactions[:20]  # Last 20 transactions across both chains
    if not transactions:
        return "📭 No transactions found for this wallet on Ethereum or Base"
    
    # Analyze patterns
    total_volume = sum(int(tx["value"]) / 10**18 for tx in transactions)
    successful_txs = sum(1 for tx in transactions if tx["isError"] == "0")
    failed_txs = len(transactions) - successful_txs
    
    # Chain distribution
    eth_txs = sum(1 for tx in transactions if tx.get("chain") == "ethereum")
    base_txs = sum(1 for tx in transactions if tx.get("chain") == "base")
    
    # Get recent activity
    recent_tx = transactions[0]
    last_activity = datetime.utcfromtimestamp(int(recent_tx["timeStamp"]))
    days_ago = (datetime.utcnow() - last_activity).days
    
    # Format the timestamp for better readability
    last_activity_str = last_activity.strftime('%Y-%m-%d %H:%M UTC')
    last_chain = recent_tx.get("chain", "unknown").title()
    
    insights = f"""
🔍 <b>Wallet Insights (Multi-Chain)</b>
📊 <b>Last Activity:</b> {days_ago} days ago ({last_activity_str}) on {last_chain}
💰 <b>Volume (Last 20 TXs):</b> {total_volume:.4f} ETH
🔗 <b>Chain Distribution:</b> ETH: {eth_txs} | Base: {base_txs}
✅ <b>Successful:</b> {successful_txs}
❌ <b>Failed:</b> {failed_txs}
📈 <b>Success Rate:</b> {(successful_txs/len(transactions)*100):.1f}%
🎯 <b>Smart Score:</b> {get_wallet_score(wallet_address)}/100
"""
    
    return insights

def check_wallet_activity(wallet_address):
    """Check if wallet has new transactions in the last 30 minutes on both chains"""
    # Get recent transactions from both chains
    eth_transactions = get_transactions_from_chain(wallet_address, "ethereum")[:5]
    base_transactions = get_transactions_from_chain(wallet_address, "base")[:5]
    
    # Combine and sort by timestamp (most recent first)
    all_transactions = eth_transactions + base_transactions
    all_transactions.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    transactions = all_transactions[:5]  # Check last 5 transactions across both chains
    cutoff_time = datetime.utcnow() - timedelta(minutes=30)
    
    for tx in transactions:
        tx_time = datetime.utcfromtimestamp(int(tx["timeStamp"]))
        if tx_time > cutoff_time:
            value = int(tx["value"]) / 10**18
            if value > 0:  # Only notify for transactions with value
                chain = tx.get("chain", "unknown")
                return True, {
                    'hash': tx['hash'],
                    'value': value,
                    'from': tx['from'],
                    'to': tx['to'],
                    'timestamp': tx_time,
                    'chain': chain
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
                        chain = tx_data.get('chain', 'unknown').title()
                        chain_emoji = "🔷" if chain.lower() == "base" else "⚡"
                        message = f"""
🚨 <b>Wallet Activity Detected!</b>

💰 <b>Amount:</b> {value:.4f} ETH
{chain_emoji} <b>Chain:</b> {chain}
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

🎯 Track smart wallets across Ethereum & Base
📊 Analyze wallet performance with AI insights
💰 See what tokens wallets are buying
⚡ Get real-time transaction alerts

<b>Quick Start:</b>
Just paste any wallet address and I'll help you!

<b>Commands:</b>
/track [wallet] - Track a wallet for notifications
/list - Show all tracked wallets  
/untrack [wallet] - Stop tracking a wallet
/score [wallet] - Get smart wallet score (0-100)
/insights [wallet] - Detailed wallet analysis
/purchases [wallet] [today/week/month] - Token purchases

<b>Natural Language:</b>
🔹 "Track this wallet: 0x123..."
🔹 "What did 0x123... buy today?"
🔹 "0x123... purchases this week"

Ready to track some smart money? 🚀
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

def handle_purchases(chat_id, text):
    """Handle purchase analysis commands"""
    # Extract wallet address and time period
    wallet_address = is_wallet_address(text)
    
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address: /purchases 0x... [today/week/month]")
        return
    
    # Determine time period
    days = 1  # default to today
    if "week" in text.lower():
        days = 7
    elif "month" in text.lower():
        days = 30
    elif "today" in text.lower():
        days = 1
    
    # Get token purchases
    purchases = analyze_token_purchases(wallet_address, days)
    
    if not purchases:
        period = "today" if days == 1 else "this week" if days == 7 else "this month"
        bot.send_message(chat_id, f"📭 No token purchases found for this wallet {period}")
        return

    # Format response
    period = "Today" if days == 1 else "This Week" if days == 7 else "This Month"
    response = f"💰 <b>Token Purchases - {period}</b>\n\n"
    
    # Group by token
    token_summary = {}
    for purchase in purchases:
        token_name = purchase.get('tokenName', 'Unknown Token')
        token_symbol = purchase.get('tokenSymbol', '???')
        chain = purchase.get('chain', 'unknown')
        
        if token_symbol not in token_summary:
            token_summary[token_symbol] = {
                'name': token_name,
                'count': 0,
                'chains': set(),
                'latest_time': 0
            }
        
        token_summary[token_symbol]['count'] += 1
        token_summary[token_symbol]['chains'].add(chain)
        token_summary[token_symbol]['latest_time'] = max(
            token_summary[token_symbol]['latest_time'], 
            int(purchase['timeStamp'])
        )
    
    # Sort by latest purchase
    sorted_tokens = sorted(
        token_summary.items(), 
        key=lambda x: x[1]['latest_time'], 
        reverse=True
    )
    
    for token_symbol, data in sorted_tokens[:10]:  # Top 10 tokens
        chains_str = ", ".join(data['chains']).title()
        latest_time = datetime.utcfromtimestamp(data['latest_time'])
        time_str = latest_time.strftime('%m/%d %H:%M')
        
        response += f"🪙 <b>{token_symbol}</b> ({data['name']})\n"
        response += f"   📊 {data['count']} purchase(s) | 🔗 {chains_str} | ⏰ {time_str}\n\n"
    
    response += f"💡 <i>Total: {len(purchases)} token purchases analyzed</i>"
    
    # Limit message length
    if len(response) > 4000:
        response = response[:3900] + "\n\n... (truncated)"
    
    bot.send_message(chat_id, response)

def handle_auto_track(chat_id, text):
    """Handle automatic wallet tracking from any message"""
    wallet_address = is_wallet_address(text)
        
        if wallet_address:
        # Check if user wants to track or just analyze
        track_keywords = ["track", "monitor", "watch", "follow", "add"]
        analysis_keywords = ["bought", "purchases", "tokens", "coins", "what did", "analyze"]
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in track_keywords):
            # User wants to track the wallet
            handle_track(chat_id, wallet_address)
        elif any(keyword in text_lower for keyword in analysis_keywords):
            # User wants to analyze purchases
            handle_purchases(chat_id, text)
    else:
            # Default: offer options
            short_address = f"{wallet_address[:8]}...{wallet_address[-6:]}"
            response = f"""
🔍 <b>Wallet Detected!</b>

📋 <b>Address:</b> <code>{short_address}</code>

What would you like to do?

🔹 <b>Track wallet:</b> Get real-time notifications
🔹 <b>Get insights:</b> Analyze wallet performance  
🔹 <b>Check purchases:</b> See recent token buys

<i>Type: "track this wallet" or "what did this wallet buy today"</i>
"""
            bot.send_message(chat_id, response)

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
        
        elif text.startswith('/purchases') or text.startswith('/bought') or text.startswith('/tokens'):
            handle_purchases(chat_id, text)
        
                            else:
            # Try to auto-detect wallet addresses or provide help
            wallet_address = is_wallet_address(text)
            if wallet_address:
                handle_auto_track(chat_id, text)
                        else:
                bot.send_message(chat_id, """
❌ <b>Unknown command</b>

<b>Available commands:</b>
/start - Get started
/track [wallet] - Track a wallet
/list - Show tracked wallets
/untrack [wallet] - Stop tracking
/score [wallet] - Get wallet score
/insights [wallet] - Detailed analysis
/purchases [wallet] [today/week/month] - See token buys

<b>Or just paste a wallet address!</b> 
<i>Example: "0x123... track this wallet"</i>
""")
        
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