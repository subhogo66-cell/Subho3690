import os
from telegram.ext import Updater, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")

def start(update, context):
    update.message.reply_text("✨ Welcome to Astro Trading Bot ✨\n\nCommands:\n/moon - Moon impact on Nifty\n/planet - Planetary conjunctions\n/full - Final trading signal")

def moon(update, context):
    update.message.reply_text("🌙 Moon Impact:\n\nToday's volatility is MEDIUM.\nNormal trading conditions.\nAvoid large positions after 2 PM.")

def planet(update, context):
    update.message.reply_text("🪐 Planetary Conjunction:\n\nNo major conjunction today.\nMarket should be stable.")

def full(update, context):
    update.message.reply_text("🎯 FINAL SIGNAL:\n\nAction: WAIT\nReason: Mixed astro signals\nBest time: 10:30 AM - 11:30 AM")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("moon", moon))
    dp.add_handler(CommandHandler("planet", planet))
    dp.add_handler(CommandHandler("full", full))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
