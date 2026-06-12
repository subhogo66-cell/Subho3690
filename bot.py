import os
import telegram
from telegram.ext import Updater, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")

def start(update, context):
    update.message.reply_text("Welcome to Astro Trading Bot!\n\nSend /moon for moon impact")

def moon(update, context):
    update.message.reply_text("🌙 Moon Impact: Today is normal volatility. Trade with caution.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("moon", moon))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
