from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import asyncio
import requests
from dotenv import load_dotenv

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
    await update.message.reply_text(
        "🔮 Welcome to *TradeSeer Bot*!\n\n"
        "Track smart wallets and get alerts *before they trade.*\n\n"
        "Commands:\n"
        "• /track <wallet>\n"
        "• /untrack <wallet>\n"
        "• /list",
        parse_mode="Markdown"
    )

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usage: /track <wallet_address>")
        return
    wallet = args[0].lower()
    user_wallets.setdefault(chat_id, set()).add(wallet)
    await update.message.reply_text(f"✅ Now tracking `{wallet}`", parse_mode="Markdown")

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    wallets = user_wallets.get(chat_id, set())
    if not wallets:
        await update.message.reply_text("📭 You're not tracking any wallets.")
    else:
        msg = "📋 Tracked wallets:\n" + "\n".join(f"• `{w}`" for w in wallets)
        await update.message.reply_text(msg, parse_mode="Markdown")

async def untrack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usage: /untrack <wallet_address>")
        return
    wallet = args[0].lower()
    if wallet in user_wallets.get(chat_id, set()):
        user_wallets[chat_id].remove(wallet)
        await update.message.reply_text(f"🗑 Stopped tracking `{wallet}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Wallet not found in your tracked list.")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("list", list_wallets))
    app.add_handler(CommandHandler("untrack", untrack))
    
    # Start the monitoring task properly
    app.job_queue.run_repeating(psychic_monitor_job, interval=30)
    
    await app.run_polling()

async def psychic_monitor_job(context):
    """Job to monitor wallets for ETH inflows"""
    for chat_id, wallets in user_wallets.items():
        for wallet in wallets:
            try:
                if check_eth_inflow(wallet):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"⚠️ *Psychic Ping*: `{wallet}` just received ETH!\n"
                            "🧠 Possible buy prep detected.\n"
                            "_Stay alert, anon._"
                        ),
                        parse_mode="Markdown"
                    )
            except Exception as e:
                print(f"Error checking {wallet}: {e}")

# To run:
if __name__ == "__main__":
    asyncio.run(main())
