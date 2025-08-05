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
import re
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
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=payload)
        return response.json()
    
    def set_webhook(self, webhook_url):
        """Set the webhook URL"""
        url = f"{self.base_url}/setWebhook"
        payload = {'url': webhook_url}
        response = requests.post(url, json=payload)
        return response.json()

bot = TelegramBot(TELEGRAM_BOT_TOKEN)

def is_wallet_address(text):
    """Check if text contains a valid wallet address"""
    pattern = r'\b0x[a-fA-F0-9]{40}\b'
    match = re.search(pattern, text)
    return match.group() if match else None

def get_token_transfers(wallet_address, chain, days=1):
    """Get token transfers for a wallet in the last X days"""
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    cutoff_timestamp = int(cutoff_time.timestamp())
    
    if chain == "ethereum":
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    elif chain == "base":
        url = f"https://api.basescan.org/api?module=account&action=tokentx&address={wallet_address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    else:
        return []
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "1" and "result" in data:
            transfers = data["result"]
            # Filter for recent transfers
            recent_transfers = []
            for transfer in transfers:
                if int(transfer["timeStamp"]) > cutoff_timestamp:
                    transfer["chain"] = chain
                    recent_transfers.append(transfer)
            return recent_transfers
        return []
    except Exception as e:
        print(f"Error fetching {chain} token transfers: {e}")
        return []

def analyze_token_purchases(wallet_address, days=1):
    """Analyze what tokens a wallet bought in the last X days"""
    # Get transfers from both chains
    eth_transfers = get_token_transfers(wallet_address, "ethereum", days)
    base_transfers = get_token_transfers(wallet_address, "base", days)
    
    # Combine and sort by timestamp
    all_transfers = eth_transfers + base_transfers
    all_transfers.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    # Filter for incoming transfers only (purchases)
    purchases = []
    wallet_lower = wallet_address.lower()
    
    for transfer in all_transfers:
        if transfer["to"].lower() == wallet_lower:
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
    
    # Combine and sort by timestamp
    all_transactions = eth_transactions + base_transactions
    all_transactions.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    # Use most recent 50 transactions for scoring
    transactions = all_transactions[:50]
    
    if not transactions:
        return 0
    
    score = 0
    total_value = 0
    unique_contracts = set()
    gas_efficiency = []
    
    for tx in transactions:
        try:
            # Transaction frequency (more recent = higher score)
            tx_age_days = (datetime.utcnow() - datetime.utcfromtimestamp(int(tx["timeStamp"]))).days
            if tx_age_days < 7:
                score += 15
            elif tx_age_days < 30:
                score += 10
            elif tx_age_days < 90:
                score += 5
            
            # Transaction value
            value_eth = float(tx["value"]) / 1e18
            total_value += value_eth
            if value_eth > 1:
                score += 10
            elif value_eth > 0.1:
                score += 5
            
            # Contract interactions
            if tx["to"] and tx["to"] not in unique_contracts:
                unique_contracts.add(tx["to"])
                score += 3
            
            # Gas efficiency
            gas_used = int(tx["gasUsed"])
            gas_price = int(tx["gasPrice"])
            efficiency = gas_used * gas_price
            gas_efficiency.append(efficiency)
            
        except (ValueError, KeyError):
            continue
    
    # Diversity bonus
    if len(unique_contracts) > 10:
        score += 20
    elif len(unique_contracts) > 5:
        score += 10
    
    # Volume bonus
    if total_value > 10:
        score += 25
    elif total_value > 1:
        score += 15
    elif total_value > 0.1:
        score += 5
    
    return min(score, 100)

def get_wallet_insights(wallet_address):
    """Get detailed insights about a wallet across Ethereum and Base"""
    # Get transactions from both chains
    eth_transactions = get_transactions_from_chain(wallet_address, "ethereum")
    base_transactions = get_transactions_from_chain(wallet_address, "base")
    
    # Combine and sort by timestamp
    all_transactions = eth_transactions + base_transactions
    all_transactions.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    # Use most recent 20 transactions for insights
    transactions = all_transactions[:20]
    
    if not transactions:
        return "❌ Unable to fetch wallet data. Please check the wallet address."
    
    total_value = 0
    gas_spent = 0
    unique_addresses = set()
    chain_distribution = {"ethereum": 0, "base": 0}
    
    for tx in transactions:
        try:
            value_eth = float(tx["value"]) / 1e18
            total_value += value_eth
            
            gas_used = int(tx["gasUsed"])
            gas_price = int(tx["gasPrice"])
            gas_spent += (gas_used * gas_price) / 1e18
            
            if tx["to"]:
                unique_addresses.add(tx["to"])
            
            chain = tx.get("chain", "unknown")
            if chain in chain_distribution:
                chain_distribution[chain] += 1
                
        except (ValueError, KeyError):
            continue
    
    # Calculate activity metrics
    if transactions:
        latest_tx = transactions[0]
        latest_timestamp = int(latest_tx["timeStamp"])
        days_since_last = (datetime.utcnow() - datetime.utcfromtimestamp(latest_timestamp)).days
        last_activity_str = f"{days_since_last} days ago"
        last_chain = latest_tx.get("chain", "unknown").title()
    else:
        days_since_last = "Unknown"
        last_activity_str = "Unknown"
        last_chain = "Unknown"
    
    score = get_wallet_score(wallet_address)
    
    # Generate insights message
    insights = f"""
🔍 <b>Wallet Analysis</b>
📊 <b>Smart Score:</b> {score}/100

💰 <b>Activity Summary:</b>
• Total Volume: {total_value:.4f} ETH
• Gas Spent: {gas_spent:.6f} ETH  
• Unique Interactions: {len(unique_addresses)}
• Last Activity: {last_activity_str} ({last_chain})

🌐 <b>Chain Distribution:</b>
• Ethereum: {chain_distribution['ethereum']} transactions
• Base: {chain_distribution['base']} transactions

📈 <b>Assessment:</b>
"""
    
    if score >= 80:
        insights += "🔥 Highly active whale - Premium trader"
    elif score >= 60:
        insights += "⚡ Active trader - Good volume"
    elif score >= 40:
        insights += "📊 Moderate activity - Regular user"
    elif score >= 20:
        insights += "🌱 Light activity - Casual user"
    else:
        insights += "😴 Low activity - Inactive wallet"
    
    return insights

def check_wallet_activity(wallet_address):
    """Check if wallet has new transactions in the last 30 minutes on both chains"""
    # Get recent transactions from both chains
    eth_transactions = get_transactions_from_chain(wallet_address, "ethereum")[:5]
    base_transactions = get_transactions_from_chain(wallet_address, "base")[:5]
    
    # Combine and sort by timestamp
    all_transactions = eth_transactions + base_transactions
    all_transactions.sort(key=lambda x: int(x["timeStamp"]), reverse=True)
    
    # Check only the 5 most recent transactions
    transactions = all_transactions[:5]
    
    cutoff_time = datetime.utcnow() - timedelta(minutes=30)
    
    for tx in transactions:
        try:
            tx_time = datetime.utcfromtimestamp(int(tx["timeStamp"]))
            if tx_time > cutoff_time:
                # Return transaction data with chain info
                tx_data = {
                    'hash': tx['hash'],
                    'value': tx['value'],
                    'from': tx['from'],
                    'to': tx['to'],
                    'chain': tx.get('chain', 'unknown')
                }
                return True, tx_data
        except (ValueError, KeyError):
            continue
    
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
🚨 <b>Wallet Activity Alert!</b> {chain_emoji}

💼 <b>Wallet:</b> <code>{wallet}</code>
🔗 <b>Chain:</b> {chain}
💰 <b>Value:</b> {float(value)/1e18:.6f} ETH
🔍 <b>Hash:</b> <code>{tx_data['hash']}</code>

📊 <b>From:</b> <code>{tx_data['from']}</code>
📨 <b>To:</b> <code>{tx_data['to']}</code>
"""
                        bot.send_message(user_id, message)
                        print(f"Alert sent for wallet {wallet} to user {user_id}")
                    
                    # Small delay between wallet checks
                    time.sleep(2)
            
            # Wait 5 minutes before next full check
            time.sleep(300)
        except Exception as e:
            print(f"Error in monitoring: {e}")
            time.sleep(60)

def handle_start(chat_id):
    """Handle /start command"""
    message = """
🔮 <b>Welcome to TradeSeer!</b>

I'm your advanced crypto wallet tracker with multi-chain support! Here's what I can do:

🎯 <b>Smart Features:</b>
• <b>Auto-detect wallets</b> - Just paste any wallet address!
• <b>Natural language</b> - Ask "what did this wallet buy today?"
• <b>Multi-chain tracking</b> - Ethereum + Base networks
• <b>Real-time alerts</b> - Get notified of new transactions

📱 <b>Easy Commands:</b>
• <code>/track [wallet]</code> - Track a wallet
• <code>/insights [wallet]</code> - Get wallet analysis  
• <code>/list</code> - Show tracked wallets
• <code>/untrack [wallet]</code> - Stop tracking

🚀 <b>Smart Usage:</b>
• Paste wallet + "track this" = Auto-track
• Paste wallet + "what bought" = Purchase analysis
• Ask "what tokens did [wallet] buy this week?"

<b>Just try pasting a wallet address - I'll detect it automatically!</b> ✨
"""
    bot.send_message(chat_id, message)

def handle_track(chat_id, wallet_address):
    """Handle wallet tracking"""
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address\n\nExample: <code>/track 0x123...</code>")
        return
    
    # Initialize user if not exists
    if chat_id not in user_wallets:
        user_wallets[chat_id] = []
    
    # Check if already tracking
    if wallet_address.lower() in [w.lower() for w in user_wallets[chat_id]]:
        bot.send_message(chat_id, f"⚠️ Already tracking: <code>{wallet_address}</code>")
        return
    
    # Add wallet
    user_wallets[chat_id].append(wallet_address)
    
    # Get initial insights
    insights = get_wallet_insights(wallet_address)
    
    message = f"✅ <b>Now tracking wallet!</b>\n\n{insights}"
    bot.send_message(chat_id, message)

def handle_list(chat_id):
    """Handle listing tracked wallets"""
    if chat_id not in user_wallets or not user_wallets[chat_id]:
        bot.send_message(chat_id, "📭 You're not tracking any wallets yet!\n\nTry: <code>/track 0x123...</code>")
        return
    
    message = "📊 <b>Your Tracked Wallets:</b>\n\n"
    for i, wallet in enumerate(user_wallets[chat_id], 1):
        score = get_wallet_score(wallet)
        message += f"{i}. <code>{wallet}</code>\n   📊 Score: {score}/100\n\n"
    
    bot.send_message(chat_id, message)

def handle_untrack(chat_id, wallet_address):
    """Handle untracking a wallet"""
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address\n\nExample: <code>/untrack 0x123...</code>")
        return
    
    if chat_id not in user_wallets or not user_wallets[chat_id]:
        bot.send_message(chat_id, "📭 You're not tracking any wallets")
        return
    
    # Find and remove wallet
    for wallet in user_wallets[chat_id]:
        if wallet.lower() == wallet_address.lower():
            user_wallets[chat_id].remove(wallet)
            bot.send_message(chat_id, f"✅ Stopped tracking wallet: <code>{wallet}</code>")
            return
    
    bot.send_message(chat_id, "❌ Wallet not found in your tracking list")

def handle_insights(chat_id, wallet_address):
    """Handle wallet insights request"""
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please provide a wallet address\n\nExample: <code>/insights 0x123...</code>")
        return
    
    insights = get_wallet_insights(wallet_address)
    bot.send_message(chat_id, insights)

def handle_purchases(chat_id, text):
    """Handle purchase analysis commands"""
    # Extract wallet address
    wallet_address = is_wallet_address(text)
    if not wallet_address:
        bot.send_message(chat_id, "❌ Please include a wallet address in your message\n\nExample: 'What did 0x123... buy today?'")
        return
    
    # Determine time period
    text_lower = text.lower()
    if "today" in text_lower:
        days = 1
        period = "today"
    elif "week" in text_lower or "7 days" in text_lower:
        days = 7
        period = "this week"
    elif "month" in text_lower or "30 days" in text_lower:
        days = 30
        period = "this month"
    else:
        days = 1  # Default to today
        period = "today"
    
    # Get purchase data
    purchases = analyze_token_purchases(wallet_address, days)
    
    if not purchases:
        bot.send_message(chat_id, f"📭 No token purchases found for this wallet {period}")
        return
    
    # Aggregate by token
    token_summary = {}
    for purchase in purchases:
        token_name = purchase.get("tokenName", "Unknown")
        token_symbol = purchase.get("tokenSymbol", "???")
        chain = purchase.get("chain", "unknown")
        
        key = f"{token_name} ({token_symbol})"
        if key not in token_summary:
            token_summary[key] = {
                "count": 0,
                "chains": set(),
                "latest_time": 0
            }
        
        token_summary[key]["count"] += 1
        token_summary[key]["chains"].add(chain.title())
        token_summary[key]["latest_time"] = max(token_summary[key]["latest_time"], int(purchase["timeStamp"]))
    
    # Create response
    message = f"💰 <b>Token Purchases {period.title()}</b>\n\n"
    message += f"📊 <b>Wallet:</b> <code>{wallet_address}</code>\n"
    message += f"🔄 <b>Total Purchases:</b> {len(purchases)}\n\n"
    
    # Sort by count and show top tokens
    sorted_tokens = sorted(token_summary.items(), key=lambda x: x[1]["count"], reverse=True)
    
    for token, data in sorted_tokens[:10]:  # Show top 10
        chains_str = ", ".join(data["chains"])
        latest_date = datetime.utcfromtimestamp(data["latest_time"]).strftime("%m/%d")
        message += f"• <b>{token}</b>\n"
        message += f"  📊 {data['count']} purchases • 🌐 {chains_str} • 📅 {latest_date}\n\n"
    
    if len(sorted_tokens) > 10:
        message += f"... and {len(sorted_tokens) - 10} more tokens\n\n"
    
    message += "💡 <i>Tip: Ask about specific time periods like 'this week' or 'this month'</i>"
    
    bot.send_message(chat_id, message)

def handle_auto_track(chat_id, text):
    """Handle automatic wallet tracking from any message"""
    wallet_address = is_wallet_address(text)
    if wallet_address:
        track_keywords = ["track", "monitor", "watch", "follow", "add"]
        analysis_keywords = ["bought", "purchases", "tokens", "coins", "what did", "analyze"]
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in track_keywords):
            handle_track(chat_id, wallet_address)
        elif any(keyword in text_lower for keyword in analysis_keywords):
            handle_purchases(chat_id, text)
        else:
            # Offer options
            message = f"""
🔍 <b>Detected wallet address!</b>

<code>{wallet_address}</code>

What would you like to do?

🎯 <b>Quick Actions:</b>
• Type "track this wallet" - Start monitoring
• Type "what did this buy today?" - See purchases  
• Type "analyze this wallet" - Get insights

Or use commands:
• <code>/track {wallet_address}</code>
• <code>/insights {wallet_address}</code>
"""
            bot.send_message(chat_id, message)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        update = request.get_json()
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
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
            elif text.startswith('/insights'):
                parts = text.split(' ', 1)
                wallet = parts[1] if len(parts) > 1 else None
                handle_insights(chat_id, wallet)
            elif text.startswith('/purchases') or text.startswith('/bought') or text.startswith('/tokens'):
                handle_purchases(chat_id, text)
            else:
                # Check for auto-detection
                wallet_address = is_wallet_address(text)
                if wallet_address:
                    handle_auto_track(chat_id, text)
                else:
                    # Unknown command
                    message = """
❓ <b>Unknown command!</b>

🎯 <b>Available commands:</b>
• <code>/start</code> - Show welcome message
• <code>/track [wallet]</code> - Track a wallet
• <code>/insights [wallet]</code> - Analyze wallet
• <code>/list</code> - Show tracked wallets
• <code>/untrack [wallet]</code> - Stop tracking

💡 <b>Smart features:</b>
• Just paste a wallet address!
• Ask "what did 0x123... buy today?"
• Say "track this wallet: 0x456..."

Try: <code>/start</code> for full instructions!
"""
                    bot.send_message(chat_id, message)
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set the webhook URL"""
    try:
        webhook_url = WEBHOOK_URL + '/webhook' if WEBHOOK_URL else request.url_root + 'webhook'
        result = bot.set_webhook(webhook_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'wallets_tracked': len(user_wallets)})

@app.route('/', methods=['GET'])
def home():
    """Home page"""
    return """
    <h1>🔮 TradeSeer Bot</h1>
    <p>Telegram bot for tracking crypto wallets with multi-chain support!</p>
    <p><a href="/health">Health Check</a> | <a href="/set_webhook">Set Webhook</a></p>
    """

if __name__ == '__main__':
    print("🔮 Starting TradeSeer Bot...")
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_wallets, daemon=True)
    monitor_thread.start()
    print("✅ Wallet monitoring thread started")
    
    # Start Flask app
    print(f"🚀 Starting Flask server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)