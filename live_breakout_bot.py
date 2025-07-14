import pandas as pd
import numpy as np
import schedule
import time
from datetime import datetime
from nsepython import *
from telegram import Bot

# Hardcoded Telegram Bot Config
TELEGRAM_BOT_TOKEN = "8167208295:AAGBUjMy05_tUv8qIpdh6h5mQGK2PJavRbU"
TELEGRAM_CHAT_ID = "1436652020"
TEST_MODE = False

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_alert(strategy, stock, cpm, tp1, tp2, sl, confidence):
    message = f"""
🚨 [{strategy}] Signal for: {stock}
🕐 Time: {datetime.now().strftime("%Y-%m-%d %H:%M")}
📊 Strategy: {strategy}
CPM: ₹{cpm}
TP1: ₹{tp1} | TP2: ₹{tp2}
SL: ₹{sl}
Confidence: {confidence}
#NSE #{stock} #{strategy.replace(" ", "")}
"""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def calculate_confidence(**kwargs):
    score = sum(kwargs.values())
    if score >= 3:
        return "🔥🔥🔥"
    elif score == 2:
        return "🔥🔥"
    elif score == 1:
        return "🔥"
    else:
        return "⚠️"

def fetch_data(stock, interval="15m"):
    try:
        data = convert_csv_to_df(stock, interval=interval)
        return data
    except:
        return None

def check_short_term(stock):
    df = fetch_data(stock, "15m")
    if df is None or len(df) < 50:
        return
    df["EMA9"] = df["close"].ewm(span=9).mean()
    df["EMA21"] = df["close"].ewm(span=21).mean()
    df["EMA200"] = df["close"].ewm(span=200).mean()
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    if prev["EMA9"] < prev["EMA21"] and latest["EMA9"] > latest["EMA21"]:
        if latest["close"] > latest["EMA200"]:
            confidence = calculate_confidence(
                ema_cross=True, above_200=True, strong_candle=True
            )
            send_telegram_alert("Short-Term Crossover", stock, round(latest["close"], 2),
                                round(latest["close"] * 1.015, 2),
                                round(latest["close"] * 1.03, 2),
                                round(latest["close"] * 0.985, 2),
                                confidence)

def check_btst(stock):
    df = fetch_data(stock, "1d")
    if df is None or len(df) < 3:
        return
    today = df.iloc[-1]
    prev = df.iloc[-2]
    if today["close"] > prev["high"]:
        confidence = calculate_confidence(breakout=True, volume=True, ema=True)
        send_telegram_alert("BTST", stock, round(today["close"], 2),
                            round(today["close"] * 1.02, 2),
                            round(today["close"] * 1.04, 2),
                            round(today["close"] * 0.98, 2),
                            confidence)

def check_intraday(stock):
    df = fetch_data(stock, "15m")
    if df is None or len(df) < 20:
        return
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    if latest["close"] > prev["high"]:
        confidence = calculate_confidence(breakout=True, volume=True)
        send_telegram_alert("Intraday Breakout", stock, round(latest["close"], 2),
                            round(latest["close"] * 1.01, 2),
                            round(latest["close"] * 1.02, 2),
                            round(latest["close"] * 0.99, 2),
                            confidence)

def check_ipo_base(stock):
    df = fetch_data(stock, "1d")
    if df is None or len(df) < 60:
        return
    high = df["high"].max()
    latest = df.iloc[-1]
    if latest["close"] > high * 0.99 and latest["close"] > latest["open"]:
        confidence = calculate_confidence(breakout=True, ema=True, price_action=True)
        send_telegram_alert("IPO Base Breakout", stock, round(latest["close"], 2),
                            round(latest["close"] * 1.03, 2),
                            round(latest["close"] * 1.05, 2),
                            round(latest["close"] * 0.97, 2),
                            confidence)

def get_nse_stocks():
    return ["INFY", "RELIANCE", "TCS", "HDFCBANK", "LT", "SBIN"]

def run_intraday_and_short_term():
    for stock in get_nse_stocks():
        check_intraday(stock)
        check_short_term(stock)

def run_ipo_base():
    for stock in get_nse_stocks():
        check_ipo_base(stock)

def run_btst():
    for stock in get_nse_stocks():
        check_btst(stock)

if TEST_MODE:
    send_telegram_alert("TEST - Short-Term", "INFY", 1500, 1530, 1560, 1470, "🔥🔥🔥")
    send_telegram_alert("TEST - BTST", "RELIANCE", 2800, 2850, 2900, 2750, "🔥🔥")
else:
    schedule.every(15).minutes.do(run_intraday_and_short_term)
    schedule.every(15).minutes.do(run_ipo_base)
    schedule.every().day.at("15:20").do(run_btst)

    while True:
        schedule.run_pending()
        time.sleep(60)
