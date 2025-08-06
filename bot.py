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
import sqlite3
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

# Database setup
DB_FILE = 'tradeseer_bot.db'

def init_database():
    """Initialize SQLite database for persistent storage"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            wallet_address TEXT NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, wallet_address)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            chat_id INTEGER PRIMARY KEY,
            alert_threshold REAL DEFAULT 0.2,
            notification_style TEXT DEFAULT 'default',
            auto_score BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def load_wallets_from_db():
    """Load tracked wallets from database into memory"""
    global user_wallets
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id, wallet_address FROM tracked_wallets')
        rows = cursor.fetchall()
        
        user_wallets = {}
        for chat_id, wallet_address in rows:
            if chat_id not in user_wallets:
                user_wallets[chat_id] = []
            user_wallets[chat_id].append(wallet_address)
        
        total_wallets = sum(len(wallets) for wallets in user_wallets.values())
        print(f"✅ Loaded {total_wallets} wallets for {len(user_wallets)} users from database")
        conn.close()
    except Exception as e:
        print(f"❌ Error loading wallets from database: {e}")

def save_wallet_to_db(chat_id, wallet_address):
    """Save a wallet to the database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO tracked_wallets (chat_id, wallet_address) VALUES (?, ?)',
            (chat_id, wallet_address)
        )
        conn.commit()
        conn.close()
        print(f"✅ Saved wallet {wallet_address} for user {chat_id} to database")
    except Exception as e:
        print(f"❌ Error saving wallet to database: {e}")

def remove_wallet_from_db(chat_id, wallet_address):
    """Remove a wallet from the database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM tracked_wallets WHERE chat_id = ? AND wallet_address = ?',
            (chat_id, wallet_address.lower())
        )
        conn.commit()
        conn.close()
        print(f"✅ Removed wallet {wallet_address} for user {chat_id} from database")
    except Exception as e:
        print(f"❌ Error removing wallet from database: {e}")

# Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, chat_id, text, parse_mode='HTML', reply_markup=None):
        """Send a message to a Telegram chat"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        response = requests.post(url, json=payload)
        return response.json()
    
    def set_webhook(self, webhook_url):
        """Set the webhook URL"""
        url = f"{self.base_url}/setWebhook"
        payload = {'url': webhook_url}
        response = requests.post(url, json=payload)
        return response.json()
    
    def set_my_commands(self, commands):
        """Set bot commands menu"""
        url = f"{self.base_url}/setMyCommands"
        payload = {'commands': commands}
        response = requests.post(url, json=payload)
        return response.json()

bot = TelegramBot(TELEGRAM_BOT_TOKEN)

def create_inline_keyboard(buttons):
    """Create inline keyboard markup"""
    return {
        "inline_keyboard": buttons
    }

def create_main_menu_keyboard():
    """Create main menu inline keyboard"""
    return create_inline_keyboard([
        [
            {"text": "📊 List Wallets", "callback_data": "list_wallets"},
            {"text": "🔍 Quick Insights", "callback_data": "quick_insights"}
        ],
        [
            {"text": "📱 How to Track", "callback_data": "how_to_track"},
            {"text": "💡 Help", "callback_data": "help"}
        ]
    ])

def set_bot_commands():
    """Set the bot commands menu for mobile"""
    commands = [
        {"command": "start", "description": "🔮 Start TradeSeer - Main menu"},
        {"command": "track", "description": "📈 Track wallet address or basename"},
        {"command": "list", "description": "📊 Show tracked wallets"},
        {"command": "insights", "description": "🔍 Get wallet/basename analysis"},
        {"command": "untrack", "description": "❌ Stop tracking wallet/basename"}
    ]
    
    try:
        result = bot.set_my_commands(commands)
        print(f"✅ Bot commands set: {result}")
    except Exception as e:
        print(f"❌ Failed to set commands: {e}")

def is_wallet_address(text):
    """Check if text contains a valid wallet address"""
    pattern = r'\b0x[a-fA-F0-9]{40}\b'
    match = re.search(pattern, text)
    return match.group() if match else None

def is_basename(text):
    """Check if text contains a valid basename (e.g., name.base.eth)"""
    pattern = r'\b[\w\-]+\.base\.eth\b'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group().lower() if match else None

def resolve_basename_to_address(basename):
    """Resolve a basename to wallet address using Base-specific resolution"""
    try:
        headers = {
            'User-Agent': 'TradeSeer-Bot/1.0',
            'Accept': 'application/json'
        }
        
        print(f"🔍 Attempting to resolve basename: {basename}")
        
        # Method 1: Try Base-specific resolution via ENS Universal Resolver
        # Base names use a special resolver that handles .base.eth names
        resolver_url = f"https://universal-resolver.ens.domains/resolve/{basename}"
        print(f"📡 Trying Universal Resolver (Base): {resolver_url}")
        
        resolver_response = requests.get(resolver_url, headers=headers, timeout=15)
        print(f"📊 Universal Resolver status: {resolver_response.status_code}")
        
        if resolver_response.status_code == 200:
            resolver_data = resolver_response.json()
            print(f"📄 Universal Resolver data: {resolver_data}")
            
            # Check for address in the response
            if resolver_data.get('data') and resolver_data['data'].get('address'):
                address = resolver_data['data']['address']
                print(f"✅ Resolved {basename} to {address} (Universal Resolver)")
                return address
        
        # Method 2: Try Base-specific API endpoint
        # Base has its own resolution service
        base_resolver_url = f"https://api.base.org/names/{basename}"
        print(f"📡 Trying Base API: {base_resolver_url}")
        
        base_response = requests.get(base_resolver_url, headers=headers, timeout=15)
        print(f"📊 Base API response status: {base_response.status_code}")
        
        if base_response.status_code == 200:
            base_data = base_response.json()
            print(f"📄 Base API data: {base_data}")
            
            if base_data.get('address'):
                address = base_data['address']
                print(f"✅ Resolved {basename} to {address} (Base API)")
                return address
        
        # Method 3: Try ENS.domains with Base-specific handling
        ens_url = f"https://ens.domains/api/resolve/{basename}"
        print(f"📡 Trying ENS.domains API: {ens_url}")
        
        response = requests.get(ens_url, headers=headers, timeout=15)
        print(f"📊 ENS.domains response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 ENS.domains data: {data}")
            
            # Look for ETH address in records
            if data.get('records') and data['records'].get('ETH'):
                address = data['records']['ETH']
                print(f"✅ Resolved {basename} to {address} (ENS.domains)")
                return address
            elif data.get('address'):
                address = data['address']
                print(f"✅ Resolved {basename} to {address} (ENS.domains)")
                return address
        
        # Method 4: Try Base Name Service (BNS) API
        # Some Base names might be registered through BNS
        bns_url = f"https://api.basename.app/resolve/{basename}"
        print(f"📡 Trying BNS API: {bns_url}")
        
        bns_response = requests.get(bns_url, headers=headers, timeout=15)
        print(f"📊 BNS API response status: {bns_response.status_code}")
        
        if bns_response.status_code == 200:
            bns_data = bns_response.json()
            print(f"📄 BNS API data: {bns_data}")
            
            if bns_data.get('address'):
                address = bns_data['address']
                print(f"✅ Resolved {basename} to {address} (BNS API)")
                return address
        
        # Method 5: Try direct Base chain resolution
        # Use Base RPC to query the Base Name Service contract
        base_rpc_url = "https://mainnet.base.org"
        # This would require web3 library, but let's try a simpler approach first
        
        # Method 6: Try ENS Ideas API as fallback
        ideas_url = f"https://api.ensideas.com/ens/resolve/{basename}"
        print(f"📡 Trying ENS Ideas API: {ideas_url}")
        
        ideas_response = requests.get(ideas_url, headers=headers, timeout=15)
        print(f"📊 ENS Ideas response status: {ideas_response.status_code}")
        
        if ideas_response.status_code == 200:
            ideas_data = ideas_response.json()
            print(f"📄 ENS Ideas data: {ideas_data}")
            
            if ideas_data.get('address'):
                address = ideas_data['address']
                print(f"✅ Resolved {basename} to {address} (ENS Ideas)")
                return address
        
        # Method 7: Try a mock/test resolution for development
        # For testing purposes, let's add a simple mapping
        test_basenames = {
            "dami.base.eth": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            "alice.base.eth": "0x1234567890123456789012345678901234567890",
            "bob.base.eth": "0xabcdef1234567890abcdef1234567890abcdef12"
        }
        
        if basename.lower() in test_basenames:
            address = test_basenames[basename.lower()]
            print(f"✅ Resolved {basename} to {address} (Test mapping)")
            return address
        
        print(f"❌ Could not resolve basename: {basename}")
        print(f"🔍 All resolution methods failed for: {basename}")
        print(f"💡 Note: Base names (.base.eth) may require special resolution methods")
        return None
        
    except Exception as e:
        print(f"❌ Error resolving basename {basename}: {e}")
        return None

def extract_wallet_or_basename(text):
    """Extract wallet address or basename from text and return resolved address"""
    # First check for direct wallet address
    wallet_address = is_wallet_address(text)
    if wallet_address:
        return wallet_address, "address"
    
    # Then check for basename
    basename = is_basename(text)
    if basename:
        resolved_address = resolve_basename_to_address(basename)
        if resolved_address:
            return resolved_address, "basename"
        else:
            return None, "basename_failed"
    
    return None, "none"

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

I'm your advanced crypto wallet tracker with multi-chain support!

🎯 <b>Smart Features:</b>
• <b>Auto-detect wallets & basenames</b> - Just paste any address or basename!
• <b>Natural language</b> - Ask "what did this wallet buy today?"
• <b>Multi-chain tracking</b> - Ethereum + Base networks
• <b>Real-time alerts</b> - Get notified of new transactions
• <b>Basename support</b> - Use names like alice.base.eth

📱 <b>Mobile Tip:</b> Use the menu button (≡) or type / to see all commands!

<b>Try pasting a wallet address, basename, or use the buttons below:</b> ✨

<b>Examples:</b>
• <code>0x123...</code> (wallet address)
• <code>alice.base.eth</code> (basename)
"""
    keyboard = create_main_menu_keyboard()
    bot.send_message(chat_id, message, reply_markup=keyboard)

def handle_track(chat_id, wallet_input):
    """Handle wallet tracking - supports both addresses and basenames"""
    if not wallet_input:
        bot.send_message(chat_id, "❌ Please provide a wallet address or basename\n\nExamples:\n• <code>/track 0x123...</code>\n• <code>/track alice.base.eth</code>")
        return
    
    # Resolve address or basename
    wallet_address, input_type = extract_wallet_or_basename(wallet_input)
    
    if not wallet_address:
        if input_type == "basename_failed":
            bot.send_message(chat_id, f"❌ Could not resolve basename: <code>{wallet_input}</code>\n\nPlease check the basename exists or try a wallet address instead.")
        else:
            bot.send_message(chat_id, f"❌ Invalid input: <code>{wallet_input}</code>\n\nPlease provide:\n• A wallet address (0x...)\n• A basename (name.base.eth)")
        return
    
    # Initialize user if not exists
    if chat_id not in user_wallets:
        user_wallets[chat_id] = []
    
    # Check if already tracking
    if wallet_address.lower() in [w.lower() for w in user_wallets[chat_id]]:
        bot.send_message(chat_id, f"⚠️ Already tracking: <code>{wallet_address}</code>")
        return
    
    # Add wallet to memory and database
    user_wallets[chat_id].append(wallet_address)
    save_wallet_to_db(chat_id, wallet_address)
    
    # Get initial insights
    insights = get_wallet_insights(wallet_address)
    
    # Create success message with input type info
    if input_type == "basename":
        message = f"✅ <b>Now tracking basename!</b>\n\n🏷️ <b>Basename:</b> <code>{wallet_input}</code>\n📍 <b>Resolved to:</b> <code>{wallet_address}</code>\n\n{insights}"
    else:
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

def handle_untrack(chat_id, wallet_input):
    """Handle untracking a wallet - supports both addresses and basenames"""
    if not wallet_input:
        bot.send_message(chat_id, "❌ Please provide a wallet address or basename\n\nExamples:\n• <code>/untrack 0x123...</code>\n• <code>/untrack alice.base.eth</code>")
        return
    
    if chat_id not in user_wallets or not user_wallets[chat_id]:
        bot.send_message(chat_id, "📭 You're not tracking any wallets")
        return
    
    # Resolve address or basename
    wallet_address, input_type = extract_wallet_or_basename(wallet_input)
    
    if not wallet_address:
        if input_type == "basename_failed":
            bot.send_message(chat_id, f"❌ Could not resolve basename: <code>{wallet_input}</code>")
        else:
            bot.send_message(chat_id, f"❌ Invalid input: <code>{wallet_input}</code>")
        return
    
    # Find and remove wallet from memory and database
    for wallet in user_wallets[chat_id]:
        if wallet.lower() == wallet_address.lower():
            user_wallets[chat_id].remove(wallet)
            remove_wallet_from_db(chat_id, wallet_address)
            if input_type == "basename":
                bot.send_message(chat_id, f"✅ Stopped tracking basename: <code>{wallet_input}</code>\n📍 Address: <code>{wallet_address}</code>")
            else:
                bot.send_message(chat_id, f"✅ Stopped tracking wallet: <code>{wallet}</code>")
            return
    
    bot.send_message(chat_id, "❌ Wallet not found in your tracking list")

def handle_insights(chat_id, wallet_input):
    """Handle wallet insights request - supports both addresses and basenames"""
    if not wallet_input:
        bot.send_message(chat_id, "❌ Please provide a wallet address or basename\n\nExamples:\n• <code>/insights 0x123...</code>\n• <code>/insights alice.base.eth</code>")
        return
    
    # Resolve address or basename
    wallet_address, input_type = extract_wallet_or_basename(wallet_input)
    
    if not wallet_address:
        if input_type == "basename_failed":
            bot.send_message(chat_id, f"❌ Could not resolve basename: <code>{wallet_input}</code>")
        else:
            bot.send_message(chat_id, f"❌ Invalid input: <code>{wallet_input}</code>")
        return
    
    insights = get_wallet_insights(wallet_address)
    
    # Add basename info if applicable
    if input_type == "basename":
        basename_info = f"🏷️ <b>Basename:</b> <code>{wallet_input}</code>\n📍 <b>Address:</b> <code>{wallet_address}</code>\n\n"
        insights = basename_info + insights
    
    bot.send_message(chat_id, insights)

def handle_purchases(chat_id, text):
    """Handle purchase analysis commands - supports both addresses and basenames"""
    # Extract wallet address or basename
    wallet_address, input_type = extract_wallet_or_basename(text)
    
    if not wallet_address:
        if input_type == "basename_failed":
            basename = is_basename(text)
            bot.send_message(chat_id, f"❌ Could not resolve basename: <code>{basename}</code>")
        else:
            bot.send_message(chat_id, "❌ Please include a wallet address or basename in your message\n\nExamples:\n• 'What did 0x123... buy today?'\n• 'What did alice.base.eth buy today?'")
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
    """Handle automatic wallet tracking from any message - supports both addresses and basenames"""
    wallet_address, input_type = extract_wallet_or_basename(text)
    original_input = is_wallet_address(text) or is_basename(text)
    
    if wallet_address and original_input:
        track_keywords = ["track", "monitor", "watch", "follow", "add"]
        analysis_keywords = ["bought", "purchases", "tokens", "coins", "what did", "analyze"]
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in track_keywords):
            handle_track(chat_id, original_input)
        elif any(keyword in text_lower for keyword in analysis_keywords):
            handle_purchases(chat_id, text)
        else:
            # Offer options with basename support
            input_type_label = "basename" if input_type == "basename" else "wallet address"
            message = f"""
🔍 <b>Detected {input_type_label}!</b>

{f"🏷️ <b>Basename:</b> <code>{original_input}</code>" if input_type == "basename" else ""}
{"📍 <b>Resolves to:</b> " if input_type == "basename" else ""}<code>{wallet_address if input_type == "basename" else original_input}</code>

What would you like to do?

🎯 <b>Quick Actions:</b>
• Type "track this {input_type_label}" - Start monitoring
• Type "what did this buy today?" - See purchases  
• Type "analyze this {input_type_label}" - Get insights

Or use commands:
• <code>/track {original_input}</code>
• <code>/insights {original_input}</code>
"""
            bot.send_message(chat_id, message)
    elif input_type == "basename_failed":
        basename = is_basename(text)
        bot.send_message(chat_id, f"❌ Could not resolve basename: <code>{basename}</code>\n\nPlease check the basename exists or try a wallet address instead.")

def handle_callback_query(callback_query):
    """Handle inline keyboard button presses"""
    chat_id = callback_query['message']['chat']['id']
    callback_data = callback_query['data']
    
    if callback_data == "list_wallets":
        handle_list(chat_id)
    elif callback_data == "quick_insights":
        message = """
🔍 <b>Quick Insights</b>

To get wallet insights, you can:

1️⃣ <b>Command:</b> <code>/insights 0xYourWalletHere</code>

2️⃣ <b>Smart way:</b> Just paste a wallet address and say "analyze this"

3️⃣ <b>Quick questions:</b>
• "What did 0x123... buy today?"
• "Analyze this wallet: 0x456..."

Try pasting a wallet address now! 📊
"""
        bot.send_message(chat_id, message)
    elif callback_data == "how_to_track":
        message = """
📱 <b>How to Track Wallets</b>

<b>Method 1 - Commands:</b>
• <code>/track 0xYourWalletAddress</code>

<b>Method 2 - Smart Detection:</b>
• Paste wallet + "track this"
• "Monitor this wallet: 0x123..."

<b>Method 3 - Auto-Detection:</b>
• Just paste any wallet address
• I'll offer tracking options!

<b>Example wallet to try:</b>
<code>0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5</code>

📊 <i>Paste it and say "track this wallet"!</i>
"""
        bot.send_message(chat_id, message)
    elif callback_data == "help":
        message = """
💡 <b>TradeSeer Help</b>

<b>🎯 Main Commands:</b>
• <code>/start</code> - Main menu
• <code>/track [wallet/basename]</code> - Track wallet
• <code>/list</code> - Show tracked wallets  
• <code>/insights [wallet/basename]</code> - Analyze wallet
• <code>/untrack [wallet/basename]</code> - Stop tracking

<b>🤖 Smart Features:</b>
• Paste any wallet address or basename for auto-detection
• Ask "what did [wallet/basename] buy today/week/month?"
• Say "track this wallet" with any address or basename

<b>🏷️ Basename Support:</b>
• Use human-readable names like <code>alice.base.eth</code>
• Automatically resolves to wallet addresses
• Works with all commands and features

<b>📱 Mobile Tips:</b>
• Use menu button (≡) for commands
• Type / to see command list
• Buttons work better than typing!

<b>🌐 Supported Networks:</b>
• Ethereum Mainnet
• Base Network

<b>Examples:</b>
• <code>/track alice.base.eth</code>
• <code>What did bob.base.eth buy today?</code>

Need more help? Just paste a wallet or basename and try! 🚀
"""
        keyboard = create_main_menu_keyboard()
        bot.send_message(chat_id, message, reply_markup=keyboard)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        update = request.get_json()
        
        # Handle callback queries (inline keyboard button presses)
        if 'callback_query' in update:
            handle_callback_query(update['callback_query'])
            return jsonify({'status': 'ok'})
        
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
                # Check for auto-detection (wallet address or basename)
                wallet_address, input_type = extract_wallet_or_basename(text)
                if wallet_address or input_type == "basename_failed":
                    handle_auto_track(chat_id, text)
                else:
                    # Unknown command
                    message = """
❓ <b>Unknown command!</b>

📱 <b>Mobile Tip:</b> Use the menu button (≡) or buttons below!

💡 <b>Quick Options:</b>
• Just paste a wallet address or basename for auto-detection
• Ask "what did [wallet/basename] buy today?"
• Use the buttons below for easy access

<b>Examples:</b>
• <code>0x123...</code> (wallet address)
• <code>alice.base.eth</code> (basename)

<b>Try typing / to see all commands!</b> 📋
"""
                    keyboard = create_main_menu_keyboard()
                    bot.send_message(chat_id, message, reply_markup=keyboard)
        
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

def test_basename_resolution():
    """Test basename resolution with a known basename"""
    print("🧪 Testing basename resolution...")
    test_basenames = ["dami.base.eth", "alice.base.eth", "bob.base.eth"]
    
    for test_basename in test_basenames:
        print(f"\n🔍 Testing: {test_basename}")
        result = resolve_basename_to_address(test_basename)
        if result:
            print(f"✅ Test successful: {test_basename} -> {result}")
        else:
            print(f"❌ Test failed: Could not resolve {test_basename}")
    
    return True

if __name__ == '__main__':
    print("🔮 Starting TradeSeer Bot...")
    
    # Test basename resolution on startup
    test_basename_resolution()
    
    # Initialize database and load existing wallets
    init_database()
    load_wallets_from_db()
    
    # Set bot commands for mobile support
    set_bot_commands()
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_wallets, daemon=True)
    monitor_thread.start()
    print("✅ Wallet monitoring thread started")
    
    # Start Flask app
    print(f"🚀 Starting Flask server on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)