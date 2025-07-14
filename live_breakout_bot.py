import time
import schedule
from datetime import datetime
import logging
from telegram import Bot
from nsepython import *
import pandas as pd

# ========== CONFIG ==========
TEST_MODE = True  # Set to False to run during live market
BOT_TOKEN = "8167208295:AAGBUjMy05_tUv8qIpdh6h5mQGK2PJavRbU"
CHAT_ID = "1436652020"
NSE_STOCKS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]  # Add more stocks here
SCAN_TIME = "09:20"  # Scheduled scan time
# ============================

bot = Bot(token=BOT_TOKEN)

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(message)s")

def send_telegram(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        logging.info(f"✅ Sent to Telegram: {message}")
    except Exception as e:
        logging.error(f"❌ Telegram error: {e}")

def check_breakout(stock):
    try:
        df = nse_eq(stock)
        df = pd.DataFrame(df)
        df["lastPrice"] = pd.to_numeric(df["lastPrice"], errors="coerce")
        price = df["lastPrice"].iloc[0]

        # Simple breakout logic (replace with your real logic)
        if price > 500:  # Placeholder logic
            message = f"🚨 *Breakout Detected!*\nStock: `{stock}`\nPrice: ₹{price}"
            send_telegram(message)
            return True
    except Exception as e:
        logging.error(f"Error checking {stock}: {e}")
    return False

def run_scanner():
    logging.info("🔍 Running NSE breakout scan...")
    found = False
    for stock in NSE_STOCKS:
        if check_breakout(stock):
            found = True

    if not found:
        send_telegram("😴 No breakout today. Please rest.")
        logging.info("📭 No breakout detected.")

if __name__ == "__main__":
    if TEST_MODE:
        logging.info("🚧 Running in TEST MODE...")
        send_telegram("🧪 Test Alert: Bot is working fine ✅")
    else:
        schedule.every().day.at(SCAN_TIME).do(run_scanner)
        logging.info(f"⏳ Scheduled scan at {SCAN_TIME} every day.")

        while True:
            schedule.run_pending()
            time.sleep(1)
