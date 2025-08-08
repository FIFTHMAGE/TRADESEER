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
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging

# Import all required packages with proper error handling
WEB3_AVAILABLE = False
WALLET_AVAILABLE = False
CRYPTO_AVAILABLE = False
ACCOUNT_AVAILABLE = False

# Try to import Web3 first
try:
    from web3 import Web3
    from eth_utils import to_checksum_address
    WEB3_AVAILABLE = True
    print("✅ Web3 available for full blockchain functionality")
except ImportError as e:
    print(f"⚠️ Web3 not available - some features may be limited: {e}")

# Try to import Account
try:
    from eth_account import Account
    ACCOUNT_AVAILABLE = True
    print("✅ Account creation available")
except ImportError as e:
    print(f"❌ Account features not available: {e}")

# Try to import cryptography
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
    print("✅ Cryptography features available")
except ImportError as e:
    print(f"❌ Cryptography features not available: {e}")

# Set wallet availability based on required components
if ACCOUNT_AVAILABLE and CRYPTO_AVAILABLE:
    WALLET_AVAILABLE = True
    print("✅ Wallet features available")
else:
    print("❌ Wallet features not available - missing required dependencies")

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

# Global state for pending swaps and token info requests
PENDING_SWAPS = {}  # chat_id -> swap_info
TOKEN_INFO_REQUESTS = {}  # chat_id -> token_info_request

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
    
    # New table for connected wallets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connected_wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            wallet_address TEXT NOT NULL,
            wallet_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            date_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, wallet_address)
        )
    ''')
    
    # New table for wallet private keys (encrypted)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            wallet_address TEXT NOT NULL,
            encrypted_private_key TEXT NOT NULL,
            salt TEXT NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, wallet_address)
        )
    ''')
    
    # New table for transaction history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            wallet_address TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            token_address TEXT,
            token_symbol TEXT,
            amount REAL,
            tx_hash TEXT,
            chain TEXT DEFAULT 'base',
            status TEXT DEFAULT 'pending',
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with wallet connection support")

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
            {"text": "📈 Dashboard", "callback_data": "dashboard"},
            {"text": "⚙️ Settings", "callback_data": "settings"}
        ],
        [
            {"text": "💼 My Wallets", "callback_data": "my_wallets"},
            {"text": "🔐 Create Wallet", "callback_data": "create_wallet"}
        ],
        [
            {"text": "📊 Transaction History", "callback_data": "transaction_history"},
            {"text": "💱 Quick Swap", "callback_data": "quick_swap"}
        ],
        [
            {"text": "📱 How to Track", "callback_data": "how_to_track"},
            {"text": "💡 Help", "callback_data": "help"}
        ]
    ])

def create_settings_keyboard():
    """Create settings menu keyboard"""
    return create_inline_keyboard([
        [
            {"text": "🔮 Psychic Style", "callback_data": "style_psychic"},
            {"text": "💼 Professional", "callback_data": "style_professional"}
        ],
        [
            {"text": "🔔 Minimal", "callback_data": "style_minimal"},
            {"text": "💰 Alert Threshold", "callback_data": "alert_threshold"}
        ],
        [
            {"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}
        ]
    ])

def get_user_settings(chat_id):
    """Get user settings from database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT alert_threshold, notification_style, auto_score FROM user_settings WHERE chat_id = ?', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'alert_threshold': row[0],
                'notification_style': row[1],
                'auto_score': bool(row[2])
            }
        else:
            # Return defaults if no settings found
            return {
                'alert_threshold': 0.2,
                'notification_style': 'default',
                'auto_score': True
            }
    except Exception as e:
        print(f"Error getting user settings: {e}")
        return {
            'alert_threshold': 0.2,
            'notification_style': 'default',
            'auto_score': True
        }

def save_user_settings(chat_id, settings):
    """Save user settings to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_settings 
            (chat_id, alert_threshold, notification_style, auto_score) 
            VALUES (?, ?, ?, ?)
        ''', (chat_id, settings['alert_threshold'], settings['notification_style'], settings['auto_score']))
        conn.commit()
        conn.close()
        print(f"✅ Saved settings for user {chat_id}")
    except Exception as e:
        print(f"❌ Error saving user settings: {e}")

def get_dashboard_analytics(chat_id):
    """Get comprehensive dashboard analytics for a user"""
    if chat_id not in user_wallets or not user_wallets[chat_id]:
        return None
    
    wallets = user_wallets[chat_id]
    total_wallets = len(wallets)
    
    # Calculate scores and metrics
    scores = []
    total_volume = 0
    active_wallets = 0
    
    for wallet in wallets:
        score = get_wallet_score(wallet)
        scores.append(score)
        
        # Get recent transactions for volume calculation
        eth_transactions = get_transactions_from_chain(wallet, "ethereum")[:10]
        base_transactions = get_transactions_from_chain(wallet, "base")[:10]
        
        wallet_volume = 0
        for tx in eth_transactions + base_transactions:
            try:
                value_eth = float(tx["value"]) / 1e18
                wallet_volume += value_eth
            except (ValueError, KeyError):
                continue
        
        total_volume += wallet_volume
        
        # Count active wallets (score > 40)
        if score > 40:
            active_wallets += 1
    
    # Calculate averages
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Get top performing wallets
    wallet_scores = list(zip(wallets, scores))
    wallet_scores.sort(key=lambda x: x[1], reverse=True)
    top_wallets = wallet_scores[:3]
    
    return {
        'total_wallets': total_wallets,
        'avg_score': avg_score,
        'total_volume': total_volume,
        'active_wallets': active_wallets,
        'top_wallets': top_wallets,
        'score_distribution': {
            'high': len([s for s in scores if s >= 70]),
            'medium': len([s for s in scores if 40 <= s < 70]),
            'low': len([s for s in scores if s < 40])
        }
    }

def format_notification(message, style, wallet_address, tx_data):
    """Format notification based on user's preferred style"""
    value = float(tx_data['value']) / 1e18
    chain = tx_data.get('chain', 'unknown').title()
    chain_emoji = "🔷" if chain.lower() == "base" else "⚡"
    
    if style == "psychic":
        return f"""
🔮 <b>Psychic Ping!</b> {chain_emoji}

The cosmic forces have detected movement in your tracked wallet!

💼 <b>Wallet:</b> <code>{wallet_address}</code>
🔗 <b>Chain:</b> {chain}
💰 <b>Value:</b> {value:.6f} ETH
🔍 <b>Hash:</b> <code>{tx_data['hash']}</code>

The stars align for potential trading activity! 🌟
"""
    elif style == "professional":
        return f"""
📊 <b>Wallet Activity Alert</b> {chain_emoji}

A tracked wallet has received a new transaction.

💼 <b>Wallet:</b> <code>{wallet_address}</code>
🔗 <b>Network:</b> {chain}
💰 <b>Amount:</b> {value:.6f} ETH
🔍 <b>Transaction:</b> <code>{tx_data['hash']}</code>

Monitor for potential trading activity.
"""
    elif style == "minimal":
        return f"""
🚨 {chain_emoji} <code>{wallet_address}</code>
💰 {value:.6f} ETH | {chain}
🔗 <code>{tx_data['hash']}</code>
"""
    else:  # default
        return f"""
🚨 <b>Wallet Activity Alert!</b> {chain_emoji}

💼 <b>Wallet:</b> <code>{wallet_address}</code>
🔗 <b>Chain:</b> {chain}
💰 <b>Value:</b> {value:.6f} ETH
🔍 <b>Hash:</b> <code>{tx_data['hash']}</code>

📊 <b>From:</b> <code>{tx_data['from']}</code>
📨 <b>To:</b> <code>{tx_data['to']}</code>
"""

def handle_dashboard(chat_id):
    """Handle dashboard request"""
    analytics = get_dashboard_analytics(chat_id)
    
    if not analytics:
        bot.send_message(chat_id, "📭 You're not tracking any wallets yet!\n\nTry: <code>/track 0x123...</code>")
        return
    
    message = f"""
📊 <b>TradeSeer Dashboard</b>

📈 <b>Portfolio Overview:</b>
• Total Tracked Wallets: {analytics['total_wallets']}
• Average Score: {analytics['avg_score']:.1f}/100
• Total Volume: {analytics['total_volume']:.4f} ETH
• Active Wallets: {analytics['active_wallets']}

📊 <b>Score Distribution:</b>
• 🚀 High (70-100): {analytics['score_distribution']['high']} wallets
• 📈 Medium (40-69): {analytics['score_distribution']['medium']} wallets  
• ⚠️ Low (0-39): {analytics['score_distribution']['low']} wallets

🏆 <b>Top Performing Wallets:</b>
"""
    
    for i, (wallet, score) in enumerate(analytics['top_wallets'], 1):
        short_wallet = wallet[:10] + "..." + wallet[-6:]
        message += f"{i}. <code>{short_wallet}</code> - {score}/100\n"
    
    message += "\n💡 <i>Tip: Higher scores indicate more active and successful wallets</i>"
    
    bot.send_message(chat_id, message)

def handle_settings(chat_id):
    """Handle settings menu"""
    settings = get_user_settings(chat_id)
    
    style_names = {
        'default': 'Default',
        'psychic': '🔮 Psychic',
        'professional': '💼 Professional', 
        'minimal': '🔔 Minimal'
    }
    
    current_style = style_names.get(settings['notification_style'], 'Default')
    
    message = f"""
⚙️ <b>TradeSeer Settings</b>

🔔 <b>Notification Style:</b> {current_style}
💰 <b>Alert Threshold:</b> {settings['alert_threshold']} ETH
📊 <b>Auto Score:</b> {'✅ On' if settings['auto_score'] else '❌ Off'}

Choose an option below to customize:
"""
    
    keyboard = create_settings_keyboard()
    bot.send_message(chat_id, message, reply_markup=keyboard)

def handle_alert_threshold(chat_id):
    """Handle alert threshold setting"""
    settings = get_user_settings(chat_id)
    current_threshold = settings['alert_threshold']
    
    message = f"""
💰 <b>Alert Threshold Setting</b>

Set the minimum ETH amount that triggers alerts.

<b>Current Options:</b>
• 0.1 ETH - Very sensitive (many alerts)
• 0.2 ETH - Balanced (recommended)
• 0.5 ETH - Less sensitive
• 1.0 ETH - Only large transactions

<b>To change:</b>
Send a message like "set threshold 0.5" or "threshold 1.0"

<b>Your current threshold:</b> {current_threshold} ETH
"""
    bot.send_message(chat_id, message)

# Wallet Management Functions
def generate_encryption_key(password, salt):
    """Generate encryption key from password and salt"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_private_key(private_key, password):
    """Encrypt private key with password"""
    salt = os.urandom(16)
    key = generate_encryption_key(password, salt)
    f = Fernet(key)
    encrypted_key = f.encrypt(private_key.encode())
    return encrypted_key, salt

def decrypt_private_key(encrypted_key, salt, password):
    """Decrypt private key with password"""
    try:
        key = generate_encryption_key(password, salt)
        f = Fernet(key)
        decrypted_key = f.decrypt(encrypted_key)
        return decrypted_key.decode()
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None

def create_new_wallet(chat_id, wallet_name, password):
    """Create a new wallet for the user"""
    if not ACCOUNT_AVAILABLE:
        return None, "Account creation not available - missing eth_account dependency"
    
    if not CRYPTO_AVAILABLE:
        return None, "Encryption not available - missing cryptography dependency"
    
    try:
        # Generate new account
        account = Account.create()
        private_key = account.key.hex()
        wallet_address = account.address
        
        # Encrypt private key
        encrypted_key, salt = encrypt_private_key(private_key, password)
        
        # Save to database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Save connected wallet
        cursor.execute('''
            INSERT OR REPLACE INTO connected_wallets 
            (chat_id, wallet_address, wallet_name, is_active) 
            VALUES (?, ?, ?, ?)
        ''', (chat_id, wallet_address, wallet_name, True))
        
        # Save encrypted private key
        cursor.execute('''
            INSERT OR REPLACE INTO wallet_keys 
            (chat_id, wallet_address, encrypted_private_key, salt) 
            VALUES (?, ?, ?, ?)
        ''', (chat_id, wallet_address, encrypted_key, salt))
        
        conn.commit()
        conn.close()
        
        return wallet_address, None
    except Exception as e:
        return None, f"Error creating wallet: {e}"

def get_user_wallets(chat_id):
    """Get all connected wallets for a user"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT wallet_address, wallet_name, is_active 
            FROM connected_wallets 
            WHERE chat_id = ? AND is_active = 1
        ''', (chat_id,))
        wallets = cursor.fetchall()
        conn.close()
        return wallets
    except Exception as e:
        print(f"Error getting user wallets: {e}")
        return []

def get_wallet_balance(wallet_address, chain="base"):
    """Get wallet balance on specified chain"""
    if not WEB3_AVAILABLE:
        return None
    
    try:
        if chain == "base":
            w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        elif chain == "ethereum":
            w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
        else:
            return None
        
        balance_wei = w3.eth.get_balance(wallet_address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return float(balance_eth)
    except Exception as e:
        print(f"Error getting balance: {e}")
        return None

def get_token_info(token_address, chain="base"):
    """Get token information"""
    try:
        if chain == "base":
            url = f"https://api.basescan.org/api?module=token&action=tokeninfo&contractaddress={token_address}&apikey={ETHERSCAN_API_KEY}"
        else:
            url = f"https://api.etherscan.io/api?module=token&action=tokeninfo&contractaddress={token_address}&apikey={ETHERSCAN_API_KEY}"
        
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "1" and data["result"]:
            return data["result"][0]
        return None
    except Exception as e:
        print(f"Error getting token info: {e}")
        return None

def execute_token_swap(chat_id, wallet_address, token_address, amount_eth, password):
    """Execute a token swap on Base network using Uniswap V3"""
    if not WALLET_AVAILABLE:
        return None, "Wallet features not available"
    
    try:
        # Get encrypted private key
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT encrypted_private_key, salt 
            FROM wallet_keys 
            WHERE chat_id = ? AND wallet_address = ?
        ''', (chat_id, wallet_address))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None, "Wallet not found"
        
        encrypted_key, salt = row
        
        # Decrypt private key
        private_key = decrypt_private_key(encrypted_key, salt, password)
        if not private_key:
            return None, "Invalid password"
        
        # Create account
        account = Account.from_key(private_key)
        
        # Connect to Base network
        if WEB3_AVAILABLE:
            w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        else:
            # Fallback: simulate the transaction
            tx_hash = f"0x{secrets.token_hex(32)}"
            
            # Save transaction to database
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bot_transactions 
                (chat_id, wallet_address, transaction_type, token_address, amount, tx_hash, chain, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (chat_id, wallet_address, "swap", token_address, amount_eth, tx_hash, "base", "simulated"))
            conn.commit()
            conn.close()
            
            return tx_hash, None
        
        # Uniswap V3 Router contract (Base)
        router_address = "0x2626664c2603336E57B271c5C0b26F421741e481"  # BaseSwap router
        
        # Uniswap V3 Router ABI (simplified for swapExactETHForTokens)
        router_abi = [
            {
                "inputs": [
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactETHForTokens",
                "outputs": [{"name": "amounts", "type": "uint256[]"}],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        
        # Create router contract instance
        router_contract = w3.eth.contract(address=router_address, abi=router_abi)
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        
        # Calculate deadline (10 minutes from now)
        deadline = w3.eth.get_block('latest')['timestamp'] + 600
        
        # Build swap path (ETH -> Token)
        path = [
            "0x4200000000000000000000000000000000000006",  # WETH on Base
            token_address
        ]
        
        # Estimate gas for the transaction
        try:
            gas_estimate = router_contract.functions.swapExactETHForTokens(
                0,  # amountOutMin (no slippage protection for now)
                path,
                wallet_address,
                deadline
            ).estimate_gas({
                'from': wallet_address,
                'value': w3.to_wei(amount_eth, 'ether')
            })
        except Exception as e:
            print(f"Gas estimation failed: {e}")
            gas_estimate = 200000  # Default gas limit
        
        # Build transaction
        transaction = router_contract.functions.swapExactETHForTokens(
            0,  # amountOutMin
            path,
            wallet_address,
            deadline
        ).build_transaction({
            'from': wallet_address,
            'value': w3.to_wei(amount_eth, 'ether'),
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(wallet_address)
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Save transaction to database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bot_transactions 
            (chat_id, wallet_address, transaction_type, token_address, amount, tx_hash, chain, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, wallet_address, "swap", token_address, amount_eth, tx_hash.hex(), "base", "pending"))
        conn.commit()
        conn.close()
        
        return tx_hash.hex(), None
        
    except Exception as e:
        return None, f"Error executing swap: {e}"

def get_gas_estimate(wallet_address, token_address, amount_eth):
    """Estimate gas for a token swap"""
    if not WEB3_AVAILABLE:
        return None, "Web3 not available"
    
    try:
        w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        
        # Uniswap V3 Router contract
        router_address = "0x2626664c2603336E57B271c5C0b26F421741e481"
        router_abi = [
            {
                "inputs": [
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactETHForTokens",
                "outputs": [{"name": "amounts", "type": "uint256[]"}],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        
        router_contract = w3.eth.contract(address=router_address, abi=router_abi)
        
        deadline = w3.eth.get_block('latest')['timestamp'] + 600
        path = [
            "0x4200000000000000000000000000000000000006",  # WETH on Base
            token_address
        ]
        
        gas_estimate = router_contract.functions.swapExactETHForTokens(
            0,
            path,
            wallet_address,
            deadline
        ).estimate_gas({
            'from': wallet_address,
            'value': w3.to_wei(amount_eth, 'ether')
        })
        
        gas_price = w3.eth.gas_price
        gas_cost_wei = gas_estimate * gas_price
        gas_cost_eth = w3.from_wei(gas_cost_wei, 'ether')
        
        return {
            'gas_estimate': gas_estimate,
            'gas_price': gas_price,
            'gas_cost_eth': float(gas_cost_eth)
        }, None
        
    except Exception as e:
        return None, f"Error estimating gas: {e}"

def get_token_price(token_address, chain="base"):
    """Get token price in ETH"""
    try:
        # Use 1inch API for price data
        url = f"https://api.1inch.dev/swap/v5.2/1/quote"
        headers = {
            'Authorization': 'Bearer YOUR_1INCH_API_KEY',  # You'll need to get this
            'Accept': 'application/json'
        }
        
        params = {
            'src': '0x4200000000000000000000000000000000000006',  # WETH
            'dst': token_address,
            'amount': '1000000000000000000'  # 1 ETH in wei
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if 'toTokenAmount' in data:
            return float(data['toTokenAmount']) / 1e18
        return None
        
    except Exception as e:
        print(f"Error getting token price: {e}")
        return None

def calculate_slippage(amount_eth, slippage_percent=0.5):
    """Calculate minimum output amount based on slippage"""
    slippage_multiplier = 1 - (slippage_percent / 100)
    return amount_eth * slippage_multiplier

def handle_wallet_connection(chat_id, text):
    """Handle wallet connection commands"""
    text_lower = text.lower()
    
    if "create wallet" in text_lower or "new wallet" in text_lower:
        # Extract wallet name and password
        import re
        name_match = re.search(r'name[:\s]+([^\s]+)', text, re.IGNORECASE)
        password_match = re.search(r'password[:\s]+([^\s]+)', text, re.IGNORECASE)
        
        if not name_match or not password_match:
            bot.send_message(chat_id, """
🔐 <b>Create New Wallet</b>

To create a new wallet, use this format:
<code>create wallet name:MyWallet password:MyPassword123</code>

<b>Requirements:</b>
• Name: Any name for your wallet
• Password: Strong password (min 8 characters)

<b>Example:</b>
<code>create wallet name:TradingWallet password:SecurePass123!</code>

⚠️ <b>Important:</b> Save your password securely!
""")
            return
        
        wallet_name = name_match.group(1)
        password = password_match.group(1)
        
        if len(password) < 8:
            bot.send_message(chat_id, "❌ Password must be at least 8 characters long")
            return
        
        # Create wallet
        wallet_address, error = create_new_wallet(chat_id, wallet_name, password)
        
        if error:
            bot.send_message(chat_id, f"❌ {error}")
        else:
            message = f"""
✅ <b>Wallet Created Successfully!</b>

🏷️ <b>Name:</b> {wallet_name}
📍 <b>Address:</b> <code>{wallet_address}</code>
🔗 <b>Network:</b> Base Network

💰 <b>Next Steps:</b>
• Send ETH to this address to start trading
• Use "connect wallet" to import existing wallet
• Use "my wallets" to see all your wallets

⚠️ <b>Security:</b> Keep your password safe!
"""
            bot.send_message(chat_id, message)
    
    elif "my wallets" in text_lower or "list wallets" in text_lower:
        wallets = get_user_wallets(chat_id)
        
        if not wallets:
            bot.send_message(chat_id, """
📭 <b>No Connected Wallets</b>

You haven't connected any wallets yet.

<b>Options:</b>
• Create new wallet: "create wallet name:MyWallet password:MyPass123"
• Import existing wallet: "connect wallet [private_key]"

💡 <b>Tip:</b> Start with creating a new wallet!
""")
            return
        
        message = "💼 <b>Your Connected Wallets:</b>\n\n"
        
        for wallet_address, wallet_name, is_active in wallets:
            balance = get_wallet_balance(wallet_address)
            balance_str = f"{balance:.6f} ETH" if balance is not None else "Unknown"
            
            message += f"""
🏷️ <b>{wallet_name}</b>
📍 <code>{wallet_address}</code>
💰 Balance: {balance_str}
{'✅ Active' if is_active else '❌ Inactive'}
"""
        
        message += "\n💡 <b>Commands:</b>\n• 'swap [token] [amount]' - Buy tokens (CA or ticker)\n• 'balance [wallet]' - Check balance"
        bot.send_message(chat_id, message)
    
    elif "swap" in text_lower or "buy" in text_lower:
        # Extract token and amount - support both CA and ticker
        import re
        
        # First try to extract a contract address
        token_match = re.search(r'([0-9a-fA-F]{42})', text)
        
        if token_match:
            # Found a contract address
            token_input = token_match.group(1)
        else:
            # Try to extract a ticker symbol (word before amount)
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ['swap', 'buy'] and i + 2 < len(words):
                    # Next word should be token, word after that should be amount
                    token_input = words[i + 1]
                    break
            else:
                # Fallback: try to find any word that could be a ticker
                for word in words:
                    if word.lower() not in ['swap', 'buy', 'token', 'tokens'] and not re.match(r'\d+\.?\d*', word):
                        token_input = word
                        break
                else:
                    token_input = None
        
        # Extract amount
        amount_match = re.search(r'(\d+\.?\d*)', text)
        
        if not token_input or not amount_match:
            bot.send_message(chat_id, """
💱 <b>Token Swap</b>

To buy tokens, use this format:
<code>swap [token] [amount_in_eth]</code>

<b>Examples:</b>
• <code>swap USDC 0.1</code> - Buy USDC using ticker
• <code>swap 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 0.1</code> - Buy using contract address
• <code>swap pepe 0.05</code> - Buy meme tokens

<b>Supported:</b>
• Contract addresses (0x...)
• Popular token tickers (USDC, USDT, WETH, LINK, etc.)
• Meme tokens (PEPE, DOGE, SHIB, etc.)

💡 <b>Tip:</b> Use "my wallets" to see your available wallets first!
""")
            return
        
        amount = float(amount_match.group(1))
        
        # Resolve token input to contract address
        contract_address, token_symbol, source = resolve_token_input(token_input)
        
        if not contract_address:
            bot.send_message(chat_id, f"""
❌ <b>Token Not Found</b>

Could not find token: <code>{token_input}</code>

<b>Try:</b>
• Check the token name/spelling
• Use a contract address instead
• Try popular tokens like USDC, USDT, WETH

💡 <b>Popular tokens:</b> USDC, USDT, WETH, LINK, UNI, AAVE, COMP, MKR
""")
            return
        
        # Get user's wallets
        wallets = get_user_wallets(chat_id)
        if not wallets:
            bot.send_message(chat_id, "❌ No wallets connected. Create a wallet first!")
            return
        
        # For now, use the first wallet
        wallet_address, wallet_name, _ = wallets[0]
        
        # Check balance
        balance = get_wallet_balance(wallet_address)
        if balance is None or balance < amount:
            bot.send_message(chat_id, f"❌ Insufficient balance. You have {balance:.6f} ETH, need {amount} ETH")
            return
        
        # Get token info (use resolved symbol if available)
        token_info = get_token_info(contract_address)
        if token_info and token_info.get('tokenSymbol'):
            token_symbol = token_info.get('tokenSymbol')
        
        # Show source information
        source_info = ""
        if source == "popular_tokens":
            source_info = "✅ Found in popular tokens database"
        elif source == "coingecko":
            source_info = "🌐 Found via CoinGecko API"
        elif source == "contract_address":
            source_info = "📋 Using provided contract address"
        
        # Get gas estimate
        gas_info, gas_error = get_gas_estimate(wallet_address, contract_address, amount)
        
        if gas_error:
            gas_message = "⚠️ Gas estimation failed - using default values"
            gas_cost = 0.001  # Default gas cost
        else:
            gas_message = f"⛽ Gas cost: ~{gas_info['gas_cost_eth']:.6f} ETH"
            gas_cost = gas_info['gas_cost_eth']
        
        # Calculate total cost
        total_cost = amount + gas_cost
        
        # Check if user has enough for total cost
        if balance < total_cost:
            bot.send_message(chat_id, f"❌ Insufficient balance for swap + gas. You have {balance:.6f} ETH, need {total_cost:.6f} ETH")
            return
        
        message = f"""
💱 <b>Swap Confirmation</b>

🏷️ <b>Token:</b> {token_symbol} ({contract_address[:10]}...)
💰 <b>Swap Amount:</b> {amount} ETH
⛽ <b>Gas Cost:</b> ~{gas_cost:.6f} ETH
💸 <b>Total Cost:</b> {total_cost:.6f} ETH
💼 <b>Wallet:</b> {wallet_name}
📍 <b>Address:</b> <code>{wallet_address}</code>

{source_info}
{gas_message}

🔐 <b>To execute:</b>
Send your wallet password to confirm the swap.

⚠️ <b>Security:</b> Your password is only used to decrypt your private key and is not stored.
"""
        bot.send_message(chat_id, message)
        
        # Store pending swap info for password confirmation
        PENDING_SWAPS[chat_id] = {
            'wallet_address': wallet_address,
            'contract_address': contract_address,
            'token_symbol': token_symbol,
            'amount': amount,
            'gas_cost': gas_cost,
            'total_cost': total_cost,
            'timestamp': time.time()
        }
        
        bot.send_message(chat_id, "💡 <b>Next:</b> Send your wallet password to execute the swap")

def set_bot_commands():
    """Set the bot commands menu for mobile"""
    commands = [
        {"command": "start", "description": "🔮 Start TradeSeer - Main menu"},
        {"command": "track", "description": "📈 Track wallet address or basename"},
        {"command": "list", "description": "📊 Show tracked wallets"},
        {"command": "dashboard", "description": "📈 Portfolio dashboard & analytics"},
        {"command": "settings", "description": "⚙️ Customize notifications & alerts"},
        {"command": "wallets", "description": "💼 Manage connected wallets"},
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
    """Resolve a basename to wallet address using proper Base name resolution"""
    try:
        headers = {
            'User-Agent': 'TradeSeer-Bot/1.0',
            'Accept': 'application/json'
        }
        
        print(f"🔍 Attempting to resolve basename: {basename}")
        
        # Method 1: Try ENS Universal Resolver (Primary method for Base names)
        # According to OnchainKit docs, this is the correct way to resolve .base.eth names
        resolver_url = f"https://universal-resolver.ens.domains/resolve/{basename}"
        print(f"📡 Trying ENS Universal Resolver: {resolver_url}")
        
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
        
        # Method 2: Try ENS.domains API with proper Base handling
        # Base names are ENS names, so they should work with ENS.domains
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
        
        # Method 3: Try ENS API v1
        ens_api_url = f"https://api.ens.domains/v1/name/{basename}"
        print(f"📡 Trying ENS API v1: {ens_api_url}")
        
        ens_response = requests.get(ens_api_url, headers=headers, timeout=15)
        print(f"📊 ENS API v1 response status: {ens_response.status_code}")
        
        if ens_response.status_code == 200:
            ens_data = ens_response.json()
            print(f"📄 ENS API v1 data: {ens_data}")
            
            if ens_data.get('records', {}).get('ETH'):
                address = ens_data['records']['ETH']
                print(f"✅ Resolved {basename} to {address} (ENS API v1)")
                return address
        
        # Method 4: Try Base-specific resolution via CCIP-Read
        # Base names use CCIP-Read for cross-chain resolution
        ccip_url = f"https://universal-resolver.ens.domains/resolve/{basename}?coinType=60"
        print(f"📡 Trying CCIP-Read resolution: {ccip_url}")
        
        ccip_response = requests.get(ccip_url, headers=headers, timeout=15)
        print(f"📊 CCIP-Read response status: {ccip_response.status_code}")
        
        if ccip_response.status_code == 200:
            ccip_data = ccip_response.json()
            print(f"📄 CCIP-Read data: {ccip_data}")
            
            if ccip_data.get('data') and ccip_data['data'].get('address'):
                address = ccip_data['data']['address']
                print(f"✅ Resolved {basename} to {address} (CCIP-Read)")
                return address
        
        # Method 5: Try Web3-based ENS resolution (most reliable)
        if WEB3_AVAILABLE:
            try:
                print(f"📡 Trying Web3 ENS resolution for: {basename}")
                address = resolve_ens_with_web3(basename)
                if address:
                    print(f"✅ Resolved {basename} to {address} (Web3)")
                    return address
            except Exception as e:
                print(f"❌ Web3 resolution failed: {e}")
        
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
        print(f"💡 Note: Base names (.base.eth) use ENS protocol with CCIP-Read for cross-chain resolution")
        return None
        
    except Exception as e:
        print(f"❌ Error resolving basename {basename}: {e}")
        return None

def resolve_ens_with_web3(ens_name):
    """Resolve ENS name using Web3 library (most reliable method)"""
    if not WEB3_AVAILABLE:
        return None
    
    try:
        # Connect to Ethereum mainnet (ENS resolution always starts from L1)
        w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
        
        # ENS Registry contract address
        ens_registry = '0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e'
        
        # ENS Registry ABI (minimal for resolution)
        ens_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "node", "type": "bytes32"}
                ],
                "name": "resolver",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            }
        ]
        
        # Resolver ABI (minimal for addr function)
        resolver_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "node", "type": "bytes32"}
                ],
                "name": "addr",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            }
        ]
        
        # Create contract instances
        registry = w3.eth.contract(address=ens_registry, abi=ens_abi)
        
        # Get the namehash of the ENS name
        namehash = w3.ens.namehash(ens_name)
        
        # Get the resolver address
        resolver_address = registry.functions.resolver(namehash).call()
        
        if resolver_address == '0x0000000000000000000000000000000000000000':
            print(f"❌ No resolver found for {ens_name}")
            return None
        
        # Create resolver contract instance
        resolver = w3.eth.contract(address=resolver_address, abi=resolver_abi)
        
        # Get the address
        address = resolver.functions.addr(namehash).call()
        
        if address == '0x0000000000000000000000000000000000000000':
            print(f"❌ No address set for {ens_name}")
            return None
        
        # Convert to checksum address
        checksum_address = to_checksum_address(address)
        return checksum_address
        
    except Exception as e:
        print(f"❌ Web3 ENS resolution error: {e}")
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
                # Get user settings
                user_settings = get_user_settings(user_id)
                alert_threshold = user_settings['alert_threshold']
                notification_style = user_settings['notification_style']
                
                for wallet in wallets:
                    has_activity, tx_data = check_wallet_activity(wallet)
                    
                    if has_activity and tx_data:
                        # Check if transaction value meets user's threshold
                        value_eth = float(tx_data['value']) / 1e18
                        if value_eth >= alert_threshold:
                            # Format message based on user's preferred style
                            message = format_notification("", notification_style, wallet, tx_data)
                            bot.send_message(user_id, message)
                            print(f"Alert sent for wallet {wallet} to user {user_id} (threshold: {alert_threshold} ETH)")
                    
                    # Small delay between wallet checks
                    time.sleep(2)
            
            # Monitor pending transactions
            monitor_pending_transactions()
            
            # Wait 5 minutes before next full check
            time.sleep(300)
        except Exception as e:
            print(f"Error in monitoring: {e}")
            time.sleep(60)

def monitor_pending_transactions():
    """Monitor pending bot transactions for confirmation"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT chat_id, wallet_address, transaction_type, token_address, amount, tx_hash, chain, status
            FROM bot_transactions 
            WHERE status = 'pending'
        ''')
        pending_txs = cursor.fetchall()
        conn.close()
        
        for tx in pending_txs:
            chat_id, wallet_address, tx_type, token_address, amount, tx_hash, chain, status = tx
            
            if WEB3_AVAILABLE:
                # Check transaction status on blockchain
                try:
                    if chain == "base":
                        w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
                    else:
                        w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
                    
                    tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
                    
                    if tx_receipt and tx_receipt['status'] == 1:
                        # Transaction confirmed
                        update_transaction_status(tx_hash, 'confirmed')
                        
                        # Get token info for notification
                        token_info = get_token_info(token_address, chain)
                        token_symbol = token_info.get('tokenSymbol', 'Unknown') if token_info else 'Unknown'
                        
                        message = f"""
✅ <b>Swap Confirmed!</b>

🏷️ <b>Token:</b> {token_symbol}
💰 <b>Amount:</b> {amount} ETH
🔗 <b>Transaction:</b> <code>{tx_hash}</code>
🌐 <b>Network:</b> {chain.title()}

🎉 <b>Your tokens have been received!</b>
"""
                        bot.send_message(chat_id, message)
                        
                    elif tx_receipt and tx_receipt['status'] == 0:
                        # Transaction failed
                        update_transaction_status(tx_hash, 'failed')
                        
                        message = f"""
❌ <b>Swap Failed</b>

🔗 <b>Transaction:</b> <code>{tx_hash}</code>
🌐 <b>Network:</b> {chain.title()}

💡 <b>Possible reasons:</b>
• Insufficient gas
• Slippage too high
• Token not found
• Network congestion

Try again with a higher gas limit or different amount.
"""
                        bot.send_message(chat_id, message)
                        
                except Exception as e:
                    print(f"Error checking transaction {tx_hash}: {e}")
                    # Transaction might still be pending
                    continue
                    
    except Exception as e:
        print(f"Error monitoring pending transactions: {e}")

def update_transaction_status(tx_hash, status):
    """Update transaction status in database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bot_transactions 
            SET status = ? 
            WHERE tx_hash = ?
        ''', (status, tx_hash))
        conn.commit()
        conn.close()
        print(f"✅ Updated transaction {tx_hash} status to {status}")
    except Exception as e:
        print(f"Error updating transaction status: {e}")

def get_transaction_history(chat_id):
    """Get user's transaction history"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT transaction_type, token_address, amount, tx_hash, chain, status, date_created
            FROM bot_transactions 
            WHERE chat_id = ?
            ORDER BY date_created DESC
            LIMIT 10
        ''', (chat_id,))
        transactions = cursor.fetchall()
        conn.close()
        
        if not transactions:
            return "📭 No transaction history found."
        
        message = "📊 <b>Recent Transactions:</b>\n\n"
        
        for tx in transactions:
            tx_type, token_address, amount, tx_hash, chain, status, date_created = tx
            
            # Get token info
            token_info = get_token_info(token_address, chain)
            token_symbol = token_info.get('tokenSymbol', 'Unknown') if token_info else 'Unknown'
            
            # Format date
            date_str = datetime.fromisoformat(date_created.replace('Z', '+00:00')).strftime('%m/%d %H:%M')
            
            # Status emoji
            status_emoji = {
                'pending': '⏳',
                'confirmed': '✅',
                'failed': '❌',
                'simulated': '🧪'
            }.get(status, '❓')
            
            message += f"""
{status_emoji} <b>{tx_type.title()}</b> - {token_symbol}
💰 {amount} ETH • {chain.title()}
🔗 <code>{tx_hash[:10]}...</code>
📅 {date_str}
"""
        
        return message
        
    except Exception as e:
        print(f"Error getting transaction history: {e}")
        return "❌ Error loading transaction history."

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
• <b>Portfolio dashboard</b> - Track your wallet collection performance
• <b>Customizable alerts</b> - Choose notification style & thresholds
• <b>Wallet connection</b> - Create wallets and buy tokens directly!

📱 <b>Mobile Tip:</b> Use the menu button (≡) or type / to see all commands!

<b>Try pasting a wallet address, basename, or use the buttons below:</b> ✨

<b>Examples:</b>
• <code>0x123...</code> (wallet address)
• <code>alice.base.eth</code> (basename)
• <code>create wallet name:MyWallet password:MyPass123</code>
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
• <code>/dashboard</code> - Portfolio overview & analytics
• <code>/settings</code> - Customize notifications & alerts
• <code>/wallets</code> - Manage connected wallets
• <code>/insights [wallet/basename]</code> - Analyze wallet
• <code>/untrack [wallet/basename]</code> - Stop tracking

<b>🤖 Smart Features:</b>
• Paste any wallet address or basename for auto-detection
• Ask "what did [wallet/basename] buy today/week/month?"
• Say "track this wallet" with any address or basename
• Set alert thresholds: "set threshold 0.5"

<b>💼 Wallet Features:</b>
• Create new wallets: "create wallet name:MyWallet password:MyPass123"
• View connected wallets: "my wallets"
• Buy tokens: "swap [token] [amount]" (CA or ticker)
• Check balances automatically

<b>🏷️ Basename Support:</b>
• Use human-readable names like <code>alice.base.eth</code>
• Automatically resolves to wallet addresses
• Works with all commands and features

<b>📊 Dashboard Features:</b>
• Portfolio overview with total wallets & average score
• Score distribution analysis
• Top performing wallets
• Total volume tracking

<b>⚙️ Customization:</b>
• Notification styles: Psychic, Professional, Minimal
• Customizable alert thresholds
• Personalized settings per user

<b>🔐 Security:</b>
• Private keys encrypted with your password
• Secure wallet creation and management
• Transaction history tracking

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
• <code>set threshold 0.5</code>
• <code>create wallet name:TradingWallet password:SecurePass123!</code>
• <code>swap 0x1234567890123456789012345678901234567890 0.1</code>

Need more help? Just paste a wallet or basename and try! 🚀
"""
        keyboard = create_main_menu_keyboard()
        bot.send_message(chat_id, message, reply_markup=keyboard)
    elif callback_data == "dashboard":
        handle_dashboard(chat_id)
    elif callback_data == "settings":
        handle_settings(chat_id)
    elif callback_data == "style_psychic":
        settings = get_user_settings(chat_id)
        settings['notification_style'] = 'psychic'
        save_user_settings(chat_id, settings)
        bot.send_message(chat_id, "✅ Notification style set to 🔮 Psychic")
        handle_settings(chat_id)
    elif callback_data == "style_professional":
        settings = get_user_settings(chat_id)
        settings['notification_style'] = 'professional'
        save_user_settings(chat_id, settings)
        bot.send_message(chat_id, "✅ Notification style set to 💼 Professional")
        handle_settings(chat_id)
    elif callback_data == "style_minimal":
        settings = get_user_settings(chat_id)
        settings['notification_style'] = 'minimal'
        save_user_settings(chat_id, settings)
        bot.send_message(chat_id, "✅ Notification style set to 🔔 Minimal")
        handle_settings(chat_id)
    elif callback_data == "alert_threshold":
        handle_alert_threshold(chat_id)
    elif callback_data == "my_wallets":
        handle_wallet_connection(chat_id, "my wallets")
    elif callback_data == "create_wallet":
        bot.send_message(chat_id, """
🔐 <b>Create New Wallet</b>

To create a new wallet, send a message with this format:

<code>create wallet name:MyWallet password:MyPassword123</code>

<b>Requirements:</b>
• Name: Any name for your wallet
• Password: Strong password (min 8 characters)

<b>Example:</b>
<code>create wallet name:TradingWallet password:SecurePass123!</code>

⚠️ <b>Important:</b> Save your password securely!

💡 <b>After creating:</b>
• Send ETH to the wallet address
• Use "my wallets" to see your wallets
• Use "swap [token] [amount]" to buy tokens (CA or ticker)
""")
    elif callback_data == "transaction_history":
        history = get_transaction_history(chat_id)
        bot.send_message(chat_id, history)
    elif callback_data == "quick_swap":
        bot.send_message(chat_id, """
💱 <b>Quick Swap</b>

To quickly swap tokens, use this format:

<code>swap [token] [amount_in_eth]</code>

<b>Example:</b>
<code>swap 0x1234567890123456789012345678901234567890 0.1</code>

<b>Features:</b>
• Gas estimation
• Balance checking
• Transaction monitoring
• Automatic confirmations

💡 <b>Tip:</b> Make sure you have a wallet connected first!
""")
    elif callback_data == "back_to_menu":
        handle_start(chat_id)

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
            elif text.startswith('/dashboard'):
                handle_dashboard(chat_id)
            elif text.startswith('/settings'):
                handle_settings(chat_id)
            elif text.startswith('/wallet') or text.startswith('/wallets'):
                handle_wallet_connection(chat_id, text)
            else:
                # Check for pending swap password confirmation first
                if chat_id in PENDING_SWAPS:
                    # User is confirming a swap with password
                    swap_info = PENDING_SWAPS[chat_id]
                    
                    # Check if swap is still valid (within 5 minutes)
                    if time.time() - swap_info['timestamp'] > 300:  # 5 minutes
                        del PENDING_SWAPS[chat_id]
                        bot.send_message(chat_id, "❌ Swap confirmation expired. Please try again.")
                        return jsonify({'status': 'ok'})
                    
                    # Execute the swap
                    tx_hash, error = execute_token_swap(
                        chat_id,
                        swap_info['wallet_address'],
                        swap_info['contract_address'],
                        swap_info['payment_amount'],
                        text  # password
                    )
                    
                    # Clear pending swap
                    del PENDING_SWAPS[chat_id]
                    
                    if error:
                        bot.send_message(chat_id, f"❌ Swap failed: {error}")
                    else:
                        bot.send_message(chat_id, f"""
✅ <b>Swap Executed Successfully!</b>

🏷️ <b>Token:</b> {swap_info['token_symbol']}
💰 <b>Payment:</b> {swap_info['payment_amount']} {swap_info.get('payment_token', 'ETH')}
📊 <b>Estimated tokens:</b> {swap_info.get('estimated_tokens', 0):.2f} {swap_info['token_symbol']}
🔗 <b>Transaction:</b> <code>{tx_hash}</code>

📊 <b>Track your transaction:</b>
• Use "my wallets" to see updated balances
• Check transaction status on BaseScan

🎉 <b>Happy trading!</b>
""")
                    
                    return jsonify({'status': 'ok'})
                
                # Check for buy requests after token info
                if chat_id in TOKEN_INFO_REQUESTS and 'buy with' in text.lower():
                    handle_buy_request(chat_id, text)
                    return jsonify({'status': 'ok'})
                
                # Check for token drops (CA or ticker)
                import re
                # Check if it's a contract address
                if re.match(r'^0x[a-fA-F0-9]{40}$', text.strip()):
                    handle_token_info_request(chat_id, text.strip())
                    return jsonify({'status': 'ok'})
                
                # Check if it's a ticker symbol (3-10 characters, all caps or all lowercase)
                if re.match(r'^[A-Za-z]{3,10}$', text.strip()):
                    handle_token_info_request(chat_id, text.strip())
                    return jsonify({'status': 'ok'})
                
                # Check for wallet commands
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in ['create wallet', 'new wallet', 'my wallets', 'list wallets', 'swap', 'buy']):
                    handle_wallet_connection(chat_id, text)
                # Check for threshold setting commands
                elif any(keyword in text_lower for keyword in ['threshold', 'alert']) and any(char.isdigit() for char in text):
                    # Extract number from text
                    import re
                    numbers = re.findall(r'\d+\.?\d*', text)
                    if numbers:
                        try:
                            threshold = float(numbers[0])
                            if 0.01 <= threshold <= 10.0:  # Reasonable range
                                settings = get_user_settings(chat_id)
                                settings['alert_threshold'] = threshold
                                save_user_settings(chat_id, settings)
                                bot.send_message(chat_id, f"✅ Alert threshold set to {threshold} ETH\n\n💡 You'll now only get alerts for transactions ≥ {threshold} ETH")
                            else:
                                bot.send_message(chat_id, "❌ Please set threshold between 0.01 and 10.0 ETH")
                        except ValueError:
                            bot.send_message(chat_id, "❌ Invalid threshold value. Please use a number like 0.5")
                    else:
                        bot.send_message(chat_id, "❌ Please specify a threshold value (e.g., 'set threshold 0.5')")
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

# Token database for popular tokens on Base network
POPULAR_TOKENS = {
    # Popular tokens on Base
    "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "usdt": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    "weth": "0x4200000000000000000000000000000000000006",
    "dai": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    "link": "0x4a2F0dF2c40D03e8272425Edf011E0369D8f7545",
    "uni": "0x6fd9d7AD17242c41f7131d257212c54A0e816691",
    "aave": "0x65a2508C429a6078a7BC2f7dF81aB6BD5d3E5b0a",
    "comp": "0x9e1028F5F1D5eDE59748FFceE5532509976840E0",
    "mkr": "0x3F56e0c36d275367b8C502090EDF38289b3dEa0d",
    "sushi": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "crv": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "yfi": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "bal": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "snx": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "1inch": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "ens": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "matic": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "avax": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "dot": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "atom": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "sol": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "ada": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "xrp": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "ltc": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "bch": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "etc": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "xlm": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "vet": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "icp": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "fil": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "apt": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "near": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "algo": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "flow": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "hbar": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "sand": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "mana": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "enj": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "grt": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "bat": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "zrx": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "knc": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "ren": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "oxt": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "storj": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "nano": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "omg": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "zil": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "waves": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "hot": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "theta": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "iota": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "neo": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "qtum": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "dash": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "xmr": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "eos": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "trx": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "btt": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "leo": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    "cake": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
    # Note: DOGE and SHIB are found via DexScreener API
    # Note: PEPE, DOGE, SHIB and other meme tokens are found via DexScreener API
    # Removing placeholder addresses to allow external API discovery
    "oganesson": "0x7D49a065D17d6d4a55dc0814997B7c4C8C8C8C8C8",
}

def resolve_token_input(token_input):
    """
    Resolve token input (ticker or contract address) to contract address and symbol.
    Enhanced to use DexScreener and Pump.fun for broader token discovery.
    
    Args:
        token_input (str): Token ticker symbol or contract address
        
    Returns:
        tuple: (contract_address, token_symbol, source)
    """
    if not token_input:
        return None, None, "error"
    
    token_input = token_input.strip()
    
    # Check if it's a contract address
    if token_input.startswith('0x') and len(token_input) == 42:
        # First check our popular tokens database for known symbols
        for ticker, address in POPULAR_TOKENS.items():
            if address.lower() == token_input.lower():
                return token_input, ticker.upper(), "contract_address"
        
        # If not in our database, try to get info from DexScreener
        dex_info = get_token_info_from_dexscreener(token_input)
        if dex_info:
            return token_input, dex_info.get('symbol', 'Unknown').upper(), "contract_address"
        
        # Fallback: return the address with "Unknown" symbol
        return token_input, "Unknown", "contract_address"
    
    # Check our popular tokens database first
    if token_input.lower() in POPULAR_TOKENS:
        return POPULAR_TOKENS[token_input.lower()], token_input.upper(), "popular_tokens"
    
    # Try DexScreener for broader token discovery
    dex_info = search_token_on_dexscreener(token_input)
    if dex_info:
        return dex_info.get('address'), dex_info.get('symbol', token_input.upper()).upper(), "dexscreener"
    
    # Try Pump.fun for additional token discovery
    pump_info = search_token_on_pumpfun(token_input)
    if pump_info:
        return pump_info.get('address'), pump_info.get('symbol', token_input.upper()).upper(), "pumpfun"
    
    # Try CoinGecko as final fallback
    coingecko_info = search_token_on_coingecko(token_input)
    if coingecko_info:
        return coingecko_info.get('address'), coingecko_info.get('symbol', token_input.upper()).upper(), "coingecko"
    
    return None, None, "not_found"

def get_token_info_from_dexscreener(contract_address):
    """
    Get token information from DexScreener by contract address
    
    Args:
        contract_address (str): Token contract address
        
    Returns:
        dict: Token information or None
    """
    try:
        # DexScreener API endpoint for Base network
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'pairs' in data and data['pairs']:
                # Get the first pair (usually the most liquid)
                pair = data['pairs'][0]
                
                return {
                    'address': contract_address,
                    'symbol': pair.get('baseToken', {}).get('symbol', 'Unknown'),
                    'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                    'price': pair.get('priceUsd', 0),
                    'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                    'volume_24h': pair.get('volume', {}).get('h24', 0),
                    'liquidity': pair.get('liquidity', {}).get('usd', 0),
                    'dex': pair.get('dexId', 'Unknown'),
                    'pair_address': pair.get('pairAddress', 'Unknown')
                }
        
        return None
        
    except Exception as e:
        print(f"Error getting token info from DexScreener: {e}")
        return None

def search_token_on_dexscreener(token_symbol):
    """
    Search for token on DexScreener by symbol
    
    Args:
        token_symbol (str): Token symbol to search for
        
    Returns:
        dict: Token information or None
    """
    try:
        # DexScreener search endpoint
        url = f"https://api.dexscreener.com/latest/dex/search?q={token_symbol}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'pairs' in data and data['pairs']:
                # Filter for Base network pairs
                base_pairs = [pair for pair in data['pairs'] if pair.get('chainId') == 'base']
                
                if base_pairs:
                    # Get the most liquid pair
                    best_pair = max(base_pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0))
                    
                    return {
                        'address': best_pair.get('baseToken', {}).get('address', 'Unknown'),
                        'symbol': best_pair.get('baseToken', {}).get('symbol', token_symbol.upper()),
                        'name': best_pair.get('baseToken', {}).get('name', 'Unknown'),
                        'price': best_pair.get('priceUsd', 0),
                        'price_change_24h': best_pair.get('priceChange', {}).get('h24', 0),
                        'volume_24h': best_pair.get('volume', {}).get('h24', 0),
                        'liquidity': best_pair.get('liquidity', {}).get('usd', 0),
                        'dex': best_pair.get('dexId', 'Unknown'),
                        'pair_address': best_pair.get('pairAddress', 'Unknown')
                    }
        
        return None
        
    except Exception as e:
        print(f"Error searching token on DexScreener: {e}")
        return None

def search_token_on_pumpfun(token_symbol):
    """
    Search for token on Pump.fun by symbol
    
    Args:
        token_symbol (str): Token symbol to search for
        
    Returns:
        dict: Token information or None
    """
    try:
        # Pump.fun API endpoint (Base network)
        url = f"https://api.pump.fun/v1/tokens/search?q={token_symbol}&chain=base"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data']:
                # Get the first result
                token = data['data'][0]
                
                return {
                    'address': token.get('address', 'Unknown'),
                    'symbol': token.get('symbol', token_symbol.upper()),
                    'name': token.get('name', 'Unknown'),
                    'price': token.get('price', 0),
                    'market_cap': token.get('marketCap', 0),
                    'volume_24h': token.get('volume24h', 0),
                    'holders': token.get('holders', 0),
                    'created_at': token.get('createdAt', 'Unknown')
                }
        
        return None
        
    except Exception as e:
        print(f"Error searching token on Pump.fun: {e}")
        return None

def search_token_on_coingecko(token_symbol):
    """
    Search for token on CoinGecko by symbol (fallback)
    
    Args:
        token_symbol (str): Token symbol to search for
        
    Returns:
        dict: Token information or None
    """
    try:
        # CoinGecko search endpoint
        url = f"https://api.coingecko.com/api/v3/search?query={token_symbol}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'coins' in data and data['coins']:
                # Look for Base network tokens
                for coin in data['coins']:
                    # Check if it has Base network info
                    coin_id = coin.get('id', '')
                    
                    # Get detailed coin info
                    detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                    detail_response = requests.get(detail_url, timeout=10)
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        
                        # Check for Base network contract
                        if 'platforms' in detail_data:
                            base_contract = detail_data['platforms'].get('base', '')
                            if base_contract:
                                return {
                                    'address': base_contract,
                                    'symbol': coin.get('symbol', token_symbol.upper()).upper(),
                                    'name': coin.get('name', 'Unknown'),
                                    'price': detail_data.get('market_data', {}).get('current_price', {}).get('usd', 0),
                                    'market_cap': detail_data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                                    'volume_24h': detail_data.get('market_data', {}).get('total_volume', {}).get('usd', 0)
                                }
        
        return None
        
    except Exception as e:
        print(f"Error searching token on CoinGecko: {e}")
        return None

def get_comprehensive_token_info(token_input):
    """
    Get comprehensive token information including price, market cap, volume, etc.
    Enhanced to use DexScreener, Pump.fun, and other sources for better data.
    
    Args:
        token_input (str): Token address or ticker symbol
        
    Returns:
        dict: Comprehensive token information
    """
    # First resolve the token input
    contract_address, token_symbol, source = resolve_token_input(token_input)
    
    if not contract_address:
        return None, f"Token not found: {token_input}"
    
    try:
        # Get enhanced data based on source
        if source == "dexscreener":
            # Get data from DexScreener
            dex_info = get_token_info_from_dexscreener(contract_address)
            if dex_info:
                comprehensive_info = {
                    'contract_address': contract_address,
                    'symbol': token_symbol,
                    'source': source,
                    'name': dex_info.get('name', 'Unknown'),
                    'decimals': 18,  # Default for most tokens
                    'price_usd': dex_info.get('price', 0),
                    'price_change_24h': dex_info.get('price_change_24h', 0),
                    'market_cap': 0,  # DexScreener doesn't provide this directly
                    'volume_24h': dex_info.get('volume_24h', 0),
                    'liquidity': dex_info.get('liquidity', 0),
                    'dex': dex_info.get('dex', 'Unknown'),
                    'circulating_supply': 0,
                    'total_supply': 0,
                    'ath': 0,
                    'ath_change_percentage': 0,
                    'last_updated': 'Now'
                }
                return comprehensive_info, None
        
        elif source == "pumpfun":
            # Get data from Pump.fun
            pump_info = search_token_on_pumpfun(token_symbol)
            if pump_info:
                comprehensive_info = {
                    'contract_address': contract_address,
                    'symbol': token_symbol,
                    'source': source,
                    'name': pump_info.get('name', 'Unknown'),
                    'decimals': 18,
                    'price_usd': pump_info.get('price', 0),
                    'price_change_24h': 0,  # Pump.fun doesn't provide this
                    'market_cap': pump_info.get('market_cap', 0),
                    'volume_24h': pump_info.get('volume_24h', 0),
                    'holders': pump_info.get('holders', 0),
                    'created_at': pump_info.get('created_at', 'Unknown'),
                    'circulating_supply': 0,
                    'total_supply': 0,
                    'ath': 0,
                    'ath_change_percentage': 0,
                    'last_updated': 'Now'
                }
                return comprehensive_info, None
        
        elif source == "coingecko":
            # Get data from CoinGecko
            coingecko_info = search_token_on_coingecko(token_symbol)
            if coingecko_info:
                comprehensive_info = {
                    'contract_address': contract_address,
                    'symbol': token_symbol,
                    'source': source,
                    'name': coingecko_info.get('name', 'Unknown'),
                    'decimals': 18,
                    'price_usd': coingecko_info.get('price', 0),
                    'price_change_24h': 0,  # Would need additional API call
                    'market_cap': coingecko_info.get('market_cap', 0),
                    'volume_24h': coingecko_info.get('volume_24h', 0),
                    'circulating_supply': 0,
                    'total_supply': 0,
                    'ath': 0,
                    'ath_change_percentage': 0,
                    'last_updated': 'Now'
                }
                return comprehensive_info, None
        
        # Fallback to original method for popular tokens and contract addresses
        # Get basic token info from Etherscan
        token_info = get_token_info(contract_address)
        
        # Get price and market data from CoinGecko
        price_data = get_token_price_data(contract_address, token_symbol)
        
        # Combine the information
        comprehensive_info = {
            'contract_address': contract_address,
            'symbol': token_symbol,
            'source': source,
            'name': token_info.get('tokenName', 'Unknown') if token_info else 'Unknown',
            'decimals': token_info.get('tokenDecimal', 18) if token_info else 18,
            'price_usd': price_data.get('price_usd', 0),
            'price_change_24h': price_data.get('price_change_24h', 0),
            'market_cap': price_data.get('market_cap', 0),
            'volume_24h': price_data.get('volume_24h', 0),
            'circulating_supply': price_data.get('circulating_supply', 0),
            'total_supply': price_data.get('total_supply', 0),
            'ath': price_data.get('ath', 0),
            'ath_change_percentage': price_data.get('ath_change_percentage', 0),
            'last_updated': price_data.get('last_updated', 'Unknown')
        }
        
        return comprehensive_info, None
        
    except Exception as e:
        print(f"Error getting comprehensive token info: {e}")
        return None, f"Error retrieving token information: {e}"

def get_token_price_data(contract_address, token_symbol):
    """
    Get token price and market data from CoinGecko API
    
    Args:
        contract_address (str): Token contract address
        token_symbol (str): Token symbol
        
    Returns:
        dict: Price and market data
    """
    try:
        # Try to get data by contract address first
        url = f"https://api.coingecko.com/api/v3/simple/token_price/base?contract_addresses={contract_address}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true&include_last_updated_at=true"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if contract_address.lower() in data:
                token_data = data[contract_address.lower()]
                return {
                    'price_usd': token_data.get('usd', 0),
                    'price_change_24h': token_data.get('usd_24h_change', 0),
                    'market_cap': token_data.get('usd_market_cap', 0),
                    'volume_24h': token_data.get('usd_24h_vol', 0),
                    'last_updated': token_data.get('last_updated_at', 'Unknown')
                }
        
        # If contract address lookup fails, try by symbol
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_symbol.lower()}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true&include_last_updated_at=true"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if token_symbol.lower() in data:
                token_data = data[token_symbol.lower()]
                return {
                    'price_usd': token_data.get('usd', 0),
                    'price_change_24h': token_data.get('usd_24h_change', 0),
                    'market_cap': token_data.get('usd_market_cap', 0),
                    'volume_24h': token_data.get('usd_24h_vol', 0),
                    'last_updated': token_data.get('last_updated_at', 'Unknown')
                }
        
        # Fallback: return basic structure
        return {
            'price_usd': 0,
            'price_change_24h': 0,
            'market_cap': 0,
            'volume_24h': 0,
            'circulating_supply': 0,
            'total_supply': 0,
            'ath': 0,
            'ath_change_percentage': 0,
            'last_updated': 'Unknown'
        }
        
    except Exception as e:
        print(f"Error getting price data: {e}")
        return {
            'price_usd': 0,
            'price_change_24h': 0,
            'market_cap': 0,
            'volume_24h': 0,
            'circulating_supply': 0,
            'total_supply': 0,
            'ath': 0,
            'ath_change_percentage': 0,
            'last_updated': 'Unknown'
        }

def format_token_info_message(token_info):
    """
    Format token information into a readable message
    
    Args:
        token_info (dict): Comprehensive token information
        
    Returns:
        str: Formatted message
    """
    price = token_info.get('price_usd', 0)
    price_change = token_info.get('price_change_24h', 0)
    market_cap = token_info.get('market_cap', 0)
    volume = token_info.get('volume_24h', 0)
    liquidity = token_info.get('liquidity', 0)
    holders = token_info.get('holders', 0)
    dex = token_info.get('dex', '')
    source = token_info.get('source', 'Unknown')
    
    # Format price change
    try:
        price_change = float(price_change)
        price_change_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
        price_change_str = f"{price_change:+.2f}%" if price_change != 0 else "0.00%"
    except (ValueError, TypeError):
        price_change_emoji = "➡️"
        price_change_str = "0.00%"
    
    # Format large numbers
    def format_number(num):
        try:
            num = float(num)
            if num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.2f}M"
            elif num >= 1e3:
                return f"${num/1e3:.2f}K"
            else:
                return f"${num:.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    # Format source with emoji
    source_emoji = {
        'popular_tokens': '🏆',
        'dexscreener': '📊',
        'pumpfun': '🚀',
        'coingecko': '🦎',
        'contract_address': '📍'
    }.get(source, '💡')
    
    # Format price safely
    try:
        price = float(price)
        price_str = f"${price:.6f}"
    except (ValueError, TypeError):
        price_str = "$0.000000"
    
    message = f"""
🪙 <b>Token Information</b>

🏷️ <b>Name:</b> {token_info.get('name', 'Unknown')} ({token_info.get('symbol', 'Unknown')})
📍 <b>Contract:</b> <code>{token_info.get('contract_address', 'Unknown')}</code>
💰 <b>Price:</b> {price_str} {price_change_emoji} {price_change_str}
📊 <b>Market Cap:</b> {format_number(market_cap)}
📈 <b>24h Volume:</b> {format_number(volume)}"""

    # Add source-specific information
    if source == "dexscreener" and liquidity > 0:
        message += f"\n💧 <b>Liquidity:</b> {format_number(liquidity)}"
        if dex:
            message += f"\n🏪 <b>DEX:</b> {dex}"
    
    elif source == "pumpfun" and holders > 0:
        message += f"\n👥 <b>Holders:</b> {holders:,}"
        created_at = token_info.get('created_at', '')
        if created_at and created_at != 'Unknown':
            message += f"\n📅 <b>Created:</b> {created_at}"
    
    message += f"""
🔗 <b>Network:</b> Base

{source_emoji} <b>Source:</b> {source.replace('_', ' ').title()}
🕒 <b>Updated:</b> {token_info.get('last_updated', 'Unknown')}
"""
    
    return message

def handle_token_info_request(chat_id, token_input):
    """
    Handle token information request and initiate buying flow
    
    Args:
        chat_id (int): Telegram chat ID
        token_input (str): Token address or ticker symbol
    """
    # Get comprehensive token information
    token_info, error = get_comprehensive_token_info(token_input)
    
    if error:
        bot.send_message(chat_id, f"""
❌ <b>Token Not Found</b>

Could not find token: <code>{token_input}</code>

<b>Try:</b>
• Check the token name/spelling
• Use a contract address instead
• Try popular tokens like USDC, USDT, WETH

💡 <b>Popular tokens:</b> USDC, USDT, WETH, LINK, UNI, AAVE, COMP, MKR
""")
        return
    
    # Format and send token information
    info_message = format_token_info_message(token_info)
    
    # Add buying options
    buy_message = f"""
{info_message}

💱 <b>Want to buy this token?</b>

<b>Payment Options:</b>
• ETH (native)
• USDC (stablecoin)
• USDT (stablecoin)

<b>To buy:</b>
Reply with your payment choice and amount:
• <code>buy with ETH 0.1</code>
• <code>buy with USDC 100</code>
• <code>buy with USDT 100</code>

💡 <b>Note:</b> You need a connected wallet to buy tokens.
Use "my wallets" to see your available wallets.
"""
    
    # Store token info for buying flow
    TOKEN_INFO_REQUESTS[chat_id] = {
        'token_info': token_info,
        'timestamp': time.time()
    }
    
    bot.send_message(chat_id, buy_message)

def handle_buy_request(chat_id, text):
    """
    Handle buy request after token info
    
    Args:
        chat_id (int): Telegram chat ID
        text (str): Buy command text
    """
    if chat_id not in TOKEN_INFO_REQUESTS:
        bot.send_message(chat_id, "❌ No token selected. Please search for a token first.")
        return
    
    # Check if request is still valid (within 10 minutes)
    if time.time() - TOKEN_INFO_REQUESTS[chat_id]['timestamp'] > 600:  # 10 minutes
        del TOKEN_INFO_REQUESTS[chat_id]
        bot.send_message(chat_id, "❌ Token selection expired. Please search for a token again.")
        return
    
    token_info = TOKEN_INFO_REQUESTS[chat_id]['token_info']
    
    # Parse buy command
    import re
    buy_match = re.search(r'buy with (\w+) (\d+\.?\d*)', text.lower())
    
    if not buy_match:
        bot.send_message(chat_id, """
❌ <b>Invalid Buy Command</b>

<b>Correct format:</b>
• <code>buy with ETH 0.1</code>
• <code>buy with USDC 100</code>
• <code>buy with USDT 100</code>

<b>Example:</b>
<code>buy with ETH 0.05</code> - Buy with 0.05 ETH
""")
        return
    
    payment_token = buy_match.group(1).upper()
    amount = float(buy_match.group(2))
    
    # Validate payment token
    valid_payment_tokens = ['ETH', 'USDC', 'USDT']
    if payment_token not in valid_payment_tokens:
        bot.send_message(chat_id, f"""
❌ <b>Invalid Payment Token</b>

<b>Supported payment tokens:</b>
• ETH
• USDC
• USDT

<b>Example:</b>
<code>buy with ETH 0.1</code>
""")
        return
    
    # Get user's wallets
    wallets = get_user_wallets(chat_id)
    if not wallets:
        bot.send_message(chat_id, """
❌ <b>No Wallets Connected</b>

You need to connect a wallet to buy tokens.

<b>Options:</b>
• Create new wallet: "create wallet name:MyWallet password:MyPass123"
• Import existing wallet: "connect wallet [private_key]"

💡 <b>Tip:</b> Start with creating a new wallet!
""")
        return
    
    # For now, use the first wallet
    wallet_address, wallet_name, _ = wallets[0]
    
    # Check balance for payment token
    if payment_token == 'ETH':
        balance = get_wallet_balance(wallet_address)
        balance_str = f"{balance:.6f} ETH" if balance is not None else "Unknown"
    else:
        # For USDC/USDT, we'd need to check token balance
        balance = 0  # Placeholder - would need to implement token balance checking
        balance_str = f"{balance} {payment_token}"
    
    if balance is None or balance < amount:
        bot.send_message(chat_id, f"""
❌ <b>Insufficient Balance</b>

You have: {balance_str}
Need: {amount} {payment_token}

💡 <b>Tip:</b> Send more {payment_token} to your wallet first.
""")
        return
    
    # Calculate estimated tokens to receive
    target_token_price = token_info.get('price_usd', 0)
    payment_amount_usd = amount * (1 if payment_token == 'USDC' or payment_token == 'USDT' else 0)  # Placeholder for ETH price
    
    if target_token_price > 0:
        estimated_tokens = payment_amount_usd / target_token_price
    else:
        estimated_tokens = 0
    
    # Show confirmation
    confirmation_message = f"""
💱 <b>Buy Confirmation</b>

🪙 <b>Buying:</b> {token_info.get('symbol', 'Unknown')} ({token_info.get('name', 'Unknown')})
💰 <b>Payment:</b> {amount} {payment_token}
📊 <b>Estimated tokens:</b> {estimated_tokens:.2f} {token_info.get('symbol', 'Unknown')}
💼 <b>Wallet:</b> {wallet_name}
📍 <b>Address:</b> <code>{wallet_address}</code>

⛽ <b>Gas fee:</b> ~0.001-0.005 ETH (estimated)

🔐 <b>To execute:</b>
Send your wallet password to confirm the purchase.

⚠️ <b>Security:</b> Your password is only used to decrypt your private key and is not stored.
"""
    
    # Store pending buy info
    PENDING_SWAPS[chat_id] = {
        'wallet_address': wallet_address,
        'contract_address': token_info.get('contract_address'),
        'token_symbol': token_info.get('symbol'),
        'payment_token': payment_token,
        'payment_amount': amount,
        'estimated_tokens': estimated_tokens,
        'timestamp': time.time()
    }
    
    # Clear token info request
    del TOKEN_INFO_REQUESTS[chat_id]
    
    bot.send_message(chat_id, confirmation_message)

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