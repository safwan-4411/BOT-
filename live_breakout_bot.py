# telegram_stock_bot.py
import os
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import mplfinance as mpf
import asyncio
import logging
from nsepython import nsefetch, index_url, stock_df
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# --- Config ---
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")  # Set this in Railway secrets
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")  # Set this in Railway secrets
STOCK_LIST = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]  # You can replace with your list

bot = Bot(token=TELEGRAM_TOKEN)
logging.basicConfig(level=logging.INFO)

# --- Functions ---
def calculate_fibonacci_targets(price: float, low: float) -> tuple:
    diff = price - low
    tp1 = price + 0.618 * diff
    tp2 = price + 1.0 * diff
    sl = low
    return round(tp1, 2), round(tp2, 2), round(sl, 2)

def fetch_data(symbol):
    df = stock_df(symbol)
    df = df.tail(50)  # Last 50 candles (days)
    df.columns = [col.lower() for col in df.columns]
    df.index.name = 'Date'
    return df

def detect_breakout(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    if latest['close'] > prev['high']:
        return True
    return False

def generate_chart(df, symbol):
    filename = f"/tmp/{symbol}.png"
    mpf.plot(df[-20:], type='candle', style='charles', title=symbol,
             volume=True, mav=(9, 21), savefig=dict(fname=filename, dpi=100))
    return filename

def scan_and_alert():
    for stock in STOCK_LIST:
        try:
            df = fetch_data(stock)
            if detect_breakout(df):
                latest = df.iloc[-1]
                price = latest['close']
                low = df['low'].iloc[-10:].min()
                tp1, tp2, sl = calculate_fibonacci_targets(price, low)

                message = f"\n🚀 *Breakout Alert*: {stock} \n\n💰 *CPM*: ₹{price}\n🎯 *TP1*: ₹{tp1}\n🎯 *TP2*: ₹{tp2}\n🛡️ *SL*: ₹{sl}"
                chart_path = generate_chart(df, stock)
                bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=open(chart_path, 'rb'), caption=message, parse_mode='Markdown')
        except Exception as e:
            logging.warning(f"Error processing {stock}: {e}")

# --- Bot Handlers ---
def reply_to_query(update: Update, context: CallbackContext):
    text = update.message.text.upper().strip()
    stock_name = text.replace("WHAT ABOUT", "").replace("?", "").strip()
    if stock_name in STOCK_LIST:
        df = fetch_data(stock_name)
        latest = df.iloc[-1]
        price = latest['close']
        low = df['low'].iloc[-10:].min()
        tp1, tp2, sl = calculate_fibonacci_targets(price, low)
        message = f"📊 {stock_name} Analysis:\n💰 Current Price: ₹{price}\n🎯 TP1: ₹{tp1}\n🎯 TP2: ₹{tp2}\n🛡️ SL: ₹{sl}"
        update.message.reply_text(message)
    else:
        update.message.reply_text("❌ Stock not in watchlist.")

def test_command(update: Update, context: CallbackContext):
    update.message.reply_text("🧪 Test Alert: Bot is working fine ✅")

# --- Main ---
def main():
    scan_and_alert()  # Run once when deployed

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("test", test_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_to_query))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
