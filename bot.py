from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import Conflict
import os
import asyncio
import requests
from dotenv import load_dotenv
import time
import threading
import json
from datetime import datetime, timedelta
import re

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using environment variables directly...")

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

# Validate environment variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
if not ETHERSCAN_API_KEY:
    raise ValueError("ETHERSCAN_API_KEY not found in environment variables")

user_wallets = {}
user_settings = {}  # Store user preferences
bot_instance = None
running = True

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
        value = float(tx["value"]) / 1e18
        total_volume += value
        
        # Score based on transaction frequency and volume
        if value > 1:  # High value transactions
            score += 10
        elif value > 0.1:  # Medium value
            score += 5
        
        # Check if transaction was successful (not reverted)
        if tx.get("isError") == "0":
            successful_trades += 1
    
    # Bonus for high volume and success rate
    if total_volume > 10:
        score += 20
    if successful_trades > len(transactions) * 0.8:  # 80% success rate
        score += 15
    
    return min(score, 100)  # Cap at 100

def get_wallet_insights(wallet_address):
    """Get detailed insights about a wallet"""
    url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data["status"] != "1":
        return None
    
    transactions = data["result"][:20]
    if not transactions:
        return None
    
    total_volume = sum(float(tx["value"]) / 1e18 for tx in transactions)
    avg_tx_value = total_volume / len(transactions)
    recent_activity = len([tx for tx in transactions if int(tx["timeStamp"]) > time.time() - 86400])  # Last 24h
    
    return {
        "total_volume": total_volume,
        "avg_tx_value": avg_tx_value,
        "recent_activity": recent_activity,
        "total_transactions": len(transactions)
    }

def check_eth_inflow(wallet_address):
    url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data["status"] == "1":
        for tx in data["result"][:5]:
            if tx["to"].lower() == wallet_address.lower() and float(tx["value"]) / 1e18 > 0.2:
                return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Track New Wallet", callback_data="track_wallet")],
        [InlineKeyboardButton("📋 My Tracked Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔮 Welcome to *TradeSeer Bot*!\n\n"
        "Track smart wallets and get alerts *before they trade.*\n\n"
        "✨ *Quick Start:*\n"
        "• Just paste any wallet address to track it!\n"
        "• Or say \"track this wallet: 0x...\"\n"
        "• Or use the menu buttons below\n\n"
        "✨ *Unique Features:*\n"
        "• 🎯 Smart Wallet Scoring\n"
        "• 📊 Transaction Insights\n"
        "• ⚡ Real-time Alerts\n"
        "• 🎨 Customizable Notifications\n\n"
        "Choose an option below or paste a wallet address:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔮 *TradeSeer Bot Help*\n\n"
        "📝 *How to Track Wallets:*\n"
        "• **Direct paste**: Just paste any wallet address\n"
        "• **Natural language**: \"Track this wallet: 0x...\"\n"
        "• **Commands**: \"I want to track 0x...\"\n"
        "• **Menu**: Use the buttons in /start\n\n"
        "📋 *Commands:*\n"
        "• `/start` - Main menu\n"
        "• `/help` - This help message\n"
        "• `/list` - Show tracked wallets\n"
        "• `/dashboard` - Portfolio overview\n\n"
        "🎯 *Smart Features:*\n"
        "• Automatic wallet scoring (0-100)\n"
        "• Transaction volume analysis\n"
        "• Real-time ETH inflow alerts\n"
        "• Customizable notification styles",
        parse_mode="Markdown"
    )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command version of list wallets"""
    chat_id = update.effective_chat.id
    wallets = user_wallets.get(chat_id, set())
    
    if not wallets:
        await update.message.reply_text(
            "📭 *No tracked wallets*\n\n"
            "You haven't tracked any wallets yet. Just paste a wallet address to get started!",
            parse_mode="Markdown"
        )
        return
    
    message = "📋 *Your Tracked Wallets:*\n\n"
    
    for i, wallet in enumerate(wallets, 1):
        score = get_wallet_score(wallet)
        insights = get_wallet_insights(wallet)
        
        message += f"{i}. `{wallet[:10]}...`\n"
        message += f"   🎯 Score: {score}/100\n"
        if insights:
            message += f"   📊 Volume: {insights['total_volume']:.2f} ETH\n"
        message += "\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command version of dashboard"""
    chat_id = update.effective_chat.id
    wallets = user_wallets.get(chat_id, set())
    
    if not wallets:
        await update.message.reply_text(
            "📊 *Dashboard*\n\n"
            "No data to display yet. Track some wallets to see your dashboard!",
            parse_mode="Markdown"
        )
        return
    
    total_score = 0
    total_volume = 0
    active_wallets = 0
    
    for wallet in wallets:
        score = get_wallet_score(wallet)
        insights = get_wallet_insights(wallet)
        
        total_score += score
        if insights:
            total_volume += insights['total_volume']
        if score > 50:
            active_wallets += 1
    
    avg_score = total_score / len(wallets) if wallets else 0
    
    message = "📊 *Your Dashboard*\n\n"
    message += f"📈 Total Tracked: {len(wallets)} wallets\n"
    message += f"🎯 Average Score: {avg_score:.1f}/100\n"
    message += f"💰 Total Volume: {total_volume:.2f} ETH\n"
    message += f"🚀 Active Wallets: {active_wallets}\n\n"
    
    if avg_score > 70:
        message += "🌟 *Excellent portfolio!* You're tracking high-value wallets.\n"
    elif avg_score > 50:
        message += "📈 *Good selection!* Your wallets show promising activity.\n"
    else:
        message += "💡 *Consider adding more active wallets* to improve your tracking.\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "track_wallet":
        await query.edit_message_text(
            "📝 *Track New Wallet*\n\n"
            "Simply copy and paste a wallet address below:\n"
            "Example: `0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6`\n\n"
            "I'll automatically analyze it and start tracking!",
            parse_mode="Markdown"
        )
        context.user_data['awaiting_wallet'] = True
    
    elif query.data == "list_wallets":
        await list_wallets_callback(query)
    
    elif query.data == "settings":
        await settings_menu(query)
    
    elif query.data == "dashboard":
        await dashboard(query)
    
    elif query.data.startswith("track_"):
        wallet = query.data.replace("track_", "")
        await track_wallet_from_callback(query, wallet)
    
    elif query.data.startswith("untrack_"):
        wallet = query.data.replace("untrack_", "")
        await untrack_wallet_from_callback(query, wallet)
    
    elif query.data == "back_to_menu":
        await start(update, context)

async def track_wallet_from_callback(query, wallet_address):
    chat_id = query.message.chat.id
    wallet = wallet_address.lower()
    
    # Get wallet insights
    insights = get_wallet_insights(wallet)
    score = get_wallet_score(wallet)
    
    user_wallets.setdefault(chat_id, set()).add(wallet)
    
    message = f"✅ *Wallet Tracked Successfully!*\n\n"
    message += f"📍 Address: `{wallet}`\n"
    message += f"🎯 Smart Score: {score}/100\n"
    
    if insights:
        message += f"📊 *Insights:*\n"
        message += f"• Total Volume: {insights['total_volume']:.2f} ETH\n"
        message += f"• Avg TX Value: {insights['avg_tx_value']:.2f} ETH\n"
        message += f"• Recent Activity: {insights['recent_activity']} TXs (24h)\n"
        message += f"• Total TXs: {insights['total_transactions']}\n\n"
    
    if score > 70:
        message += "🚀 *High-value wallet detected!* This wallet shows strong trading patterns.\n"
    elif score > 40:
        message += "📈 *Promising wallet!* Moderate activity detected.\n"
    else:
        message += "⚠️ *Low activity wallet.* Monitor for potential changes.\n"
    
    keyboard = [[InlineKeyboardButton("🗑 Stop Tracking", callback_data=f"untrack_{wallet}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def untrack_wallet_from_callback(query, wallet_address):
    chat_id = query.message.chat.id
    wallet = wallet_address.lower()
    
    if wallet in user_wallets.get(chat_id, set()):
        user_wallets[chat_id].remove(wallet)
        await query.edit_message_text(
            f"🗑 *Stopped tracking* `{wallet}`\n\n"
            "The wallet has been removed from your tracking list.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Wallet not found in your tracked list.",
            parse_mode="Markdown"
        )

async def list_wallets_callback(query):
    chat_id = query.message.chat.id
    wallets = user_wallets.get(chat_id, set())
    
    if not wallets:
        await query.edit_message_text(
            "📭 *No tracked wallets*\n\n"
            "You haven't tracked any wallets yet. Use the 'Track New Wallet' option to get started!",
            parse_mode="Markdown"
        )
        return
    
    message = "📋 *Your Tracked Wallets:*\n\n"
    keyboard = []
    
    for wallet in wallets:
        score = get_wallet_score(wallet)
        insights = get_wallet_insights(wallet)
        
        message += f"📍 `{wallet[:10]}...`\n"
        message += f"🎯 Score: {score}/100\n"
        if insights:
            message += f"📊 Volume: {insights['total_volume']:.2f} ETH\n"
        message += "─" * 20 + "\n"
        
        keyboard.append([InlineKeyboardButton(f"🗑 Stop tracking {wallet[:10]}...", callback_data=f"untrack_{wallet}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def settings_menu(query):
    chat_id = query.message.chat.id
    settings = user_settings.get(chat_id, {
        "alert_threshold": 0.2,
        "notification_style": "psychic",
        "auto_score": True
    })
    
    message = "⚙️ *Settings*\n\n"
    message += f"🔔 Alert Threshold: {settings['alert_threshold']} ETH\n"
    message += f"🎨 Notification Style: {settings['notification_style'].title()}\n"
    message += f"🎯 Auto Score: {'Enabled' if settings['auto_score'] else 'Disabled'}\n\n"
    message += "Customize your tracking experience!"
    
    keyboard = [
        [InlineKeyboardButton("🔔 Change Alert Threshold", callback_data="change_threshold")],
        [InlineKeyboardButton("🎨 Change Style", callback_data="change_style")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def dashboard(query):
    chat_id = query.message.chat.id
    wallets = user_wallets.get(chat_id, set())
    
    if not wallets:
        await query.edit_message_text(
            "📊 *Dashboard*\n\n"
            "No data to display yet. Track some wallets to see your dashboard!",
            parse_mode="Markdown"
        )
        return
    
    total_score = 0
    total_volume = 0
    active_wallets = 0
    
    for wallet in wallets:
        score = get_wallet_score(wallet)
        insights = get_wallet_insights(wallet)
        
        total_score += score
        if insights:
            total_volume += insights['total_volume']
        if score > 50:
            active_wallets += 1
    
    avg_score = total_score / len(wallets) if wallets else 0
    
    message = "📊 *Your Dashboard*\n\n"
    message += f"📈 Total Tracked: {len(wallets)} wallets\n"
    message += f"🎯 Average Score: {avg_score:.1f}/100\n"
    message += f"💰 Total Volume: {total_volume:.2f} ETH\n"
    message += f"🚀 Active Wallets: {active_wallets}\n\n"
    
    if avg_score > 70:
        message += "🌟 *Excellent portfolio!* You're tracking high-value wallets.\n"
    elif avg_score > 50:
        message += "📈 *Good selection!* Your wallets show promising activity.\n"
    else:
        message += "💡 *Consider adding more active wallets* to improve your tracking.\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_wallet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_wallet'):
        # Handle explicit wallet input from menu
        await handle_explicit_wallet_input(update, context)
        return
    
    # Handle natural language wallet tracking
    text = update.message.text.strip().lower()
    
    # Check for natural language tracking requests
    tracking_keywords = [
        "track", "tracking", "monitor", "watch", "follow", "add", "start tracking",
        "i want to track", "can you track", "please track", "track this", "track wallet"
    ]
    
    # Check if message contains tracking keywords
    is_tracking_request = any(keyword in text for keyword in tracking_keywords)
    
    # Check if it looks like a wallet address (0x followed by 40 hex chars)
    looks_like_wallet = text.startswith('0x') and len(text) == 42 and all(c in '0123456789abcdef' for c in text[2:])
    
    if is_tracking_request or looks_like_wallet:
        # Extract wallet address from the message
        wallet_address = extract_wallet_address(text)
        
        if wallet_address:
            await track_wallet_directly(update, context, wallet_address)
        else:
            await update.message.reply_text(
                "❌ *No valid wallet address found*\n\n"
                "Please provide a valid Ethereum wallet address.\n"
                "Example: `0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6`",
                parse_mode="Markdown"
            )
    else:
        # Not a tracking request, ignore
        return

def extract_wallet_address(text):
    """Extract wallet address from text"""
    
    # Look for 0x followed by 40 hex characters
    pattern = r'0x[a-fA-F0-9]{40}'
    matches = re.findall(pattern, text)
    
    if matches:
        return matches[0].lower()
    
    return None

async def handle_explicit_wallet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet input when explicitly waiting for it"""
    wallet_address = update.message.text.strip()
    
    # Basic wallet address validation
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        await update.message.reply_text(
            "❌ *Invalid wallet address*\n\n"
            "Please provide a valid Ethereum wallet address (0x followed by 40 characters).",
            parse_mode="Markdown"
        )
        return
    
    await track_wallet_directly(update, context, wallet_address)
    
    # Clear the awaiting state
    context.user_data['awaiting_wallet'] = False

async def track_wallet_directly(update: Update, context: ContextTypes.DEFAULT_TYPE, wallet_address):
    """Track a wallet directly with full analysis"""
    chat_id = update.effective_chat.id
    
    # Get wallet insights and score
    insights = get_wallet_insights(wallet_address)
    score = get_wallet_score(wallet_address)
    
    user_wallets.setdefault(chat_id, set()).add(wallet_address.lower())
    
    message = f"✅ *Wallet Tracked Successfully!*\n\n"
    message += f"📍 Address: `{wallet_address}`\n"
    message += f"🎯 Smart Score: {score}/100\n"
    
    if insights:
        message += f"📊 *Insights:*\n"
        message += f"• Total Volume: {insights['total_volume']:.2f} ETH\n"
        message += f"• Avg TX Value: {insights['avg_tx_value']:.2f} ETH\n"
        message += f"• Recent Activity: {insights['recent_activity']} TXs (24h)\n"
        message += f"• Total TXs: {insights['total_transactions']}\n\n"
    
    if score > 70:
        message += "🚀 *High-value wallet detected!* This wallet shows strong trading patterns.\n"
    elif score > 40:
        message += "📈 *Promising wallet!* Moderate activity detected.\n"
    else:
        message += "⚠️ *Low activity wallet.* Monitor for potential changes.\n"
    
    keyboard = [[InlineKeyboardButton("🗑 Stop Tracking", callback_data=f"untrack_{wallet_address}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

def test_notification_system():
    """Test the notification system"""
    print("🧪 Testing notification system...")
    # --- SET YOUR ACTUAL CHAT ID BELOW ---
    test_chat_id = 5079471554  # Replace with your actual chat ID (remove quotes)
    test_message = "🧪 *Test Notification*\n\nThis is a test message to verify the notification system is working properly.\n\n✅ If you received this, the notification system is working!"
    
    try:
        send_telegram_message(test_chat_id, test_message)
        print("✅ Test notification sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Test notification failed: {e}")
        return False

def send_telegram_message(chat_id, message):
    """Send message using direct HTTP API to avoid event loop issues"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ Alert sent to {chat_id}")
            return True
        else:
            print(f"❌ Failed to send alert: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def monitor_wallets():
    """Background thread to monitor wallets"""
    print("🔮 Starting wallet monitoring...")
    print("📡 Monitoring wallets for ETH inflows every 30 seconds...")
    
    while running:
        try:
            total_wallets = sum(len(wallets) for wallets in user_wallets.values())
            if total_wallets > 0:
                print(f"🔍 Checking {total_wallets} wallets for ETH inflows...")
            
            for chat_id, wallets in user_wallets.items():
                for wallet in wallets:
                    try:
                        if check_eth_inflow(wallet):
                            print(f"⚠️ ETH inflow detected for {wallet[:10]}...")
                            
                            settings = user_settings.get(chat_id, {"notification_style": "psychic"})
                            style = settings.get("notification_style", "psychic")
                            
                            if style == "psychic":
                                message = (
                                    f"⚠️ *Psychic Ping*: `{wallet}` just received ETH!\n"
                                    "🧠 Possible buy prep detected.\n"
                                    "_Stay alert, anon._"
                                )
                            elif style == "professional":
                                message = (
                                    f"📊 *Alert*: `{wallet}` received significant ETH inflow\n"
                                    "💼 Potential trading activity detected.\n"
                                    "_Monitor for follow-up transactions._"
                                )
                            else:  # minimal
                                message = f"🔔 `{wallet}` received ETH"
                            
                            success = send_telegram_message(chat_id, message)
                            if success:
                                print(f"✅ Alert sent successfully to user {chat_id}")
                            else:
                                print(f"❌ Failed to send alert to user {chat_id}")
                        else:
                            print(f"✅ No ETH inflow detected for {wallet[:10]}...")
                    except Exception as e:
                        print(f"❌ Error checking {wallet}: {e}")
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"❌ Error in monitor thread: {e}")
            time.sleep(30)

async def main():
    global bot_instance, running
    
    print("🔮 TradeSeer Bot is starting...")
    print("📡 Setting up wallet monitoring...")
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_wallets, daemon=True)
    monitor_thread.start()
    
    # Create and run the bot
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot_instance = app.bot
    
    # Add error handler for conflicts
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        if isinstance(context.error, Conflict):
            print(f"⚠️ Bot conflict detected: {context.error}")
            print("💡 This usually means another bot instance is running")
        else:
            print(f"❌ Error: {context.error}")
    
    app.add_error_handler(error_handler)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("dashboard", dashboard_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_input))
    
    print("✅ Bot is ready! Monitoring wallets for ETH inflows...")
    print("📱 Send /start to your bot to begin!")
    
    try:
        await app.initialize()
        await app.start()
        await app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down TradeSeer Bot...")
        running = False
    except Conflict as e:
        print(f"⚠️ Bot conflict detected: {e}")
        print("💡 Bot will exit and Render will restart it automatically")
        running = False
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        print("💡 Bot will exit and Render will restart it automatically")
        running = False
    finally:
        await app.stop()
        await app.shutdown()

# To run:
if __name__ == "__main__":
    asyncio.run(main())
