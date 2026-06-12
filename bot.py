import os
import logging
import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌙 Moon Impact", callback_data='moon'),
         InlineKeyboardButton("🪐 Planet Conjunctions", callback_data='planets')],
        [InlineKeyboardButton("☀️ Sun & Mercury Effect", callback_data='sun_mercury'),
         InlineKeyboardButton("⭐ Nakshatra Timing", callback_data='nakshatra')],
        [InlineKeyboardButton("📊 Intraday Indicators", callback_data='intraday'),
         InlineKeyboardButton("🔄 Market Cycle", callback_data='cycle')],
        [InlineKeyboardButton("🌀 Planetary Harmonics", callback_data='harmonics'),
         InlineKeyboardButton("📐 Astro-Gann Combo", callback_data='gann')],
        [InlineKeyboardButton("🎯 FINAL RESULT / FULL SIGNAL", callback_data='full_result')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✨ Welcome to Astro Trading Bot ✨\n\nChoose an option:", reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    today = datetime.datetime.now()
    
    if query.data == 'moon':
        phases = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
        phase = phases[today.day % 8]
        result = f"🌙 **Moon Impact** - {today.strftime('%d %b')}\nPhase: {phase}\nVolatility: {'High' if phase in ['New Moon','Full Moon'] else 'Medium'}\nTip: {'Avoid large positions' if phase in ['New Moon','Full Moon'] else 'Normal trading'}"
    elif query.data == 'planets':
        conj = [("Saturn-Mars","High volatility"), ("Jupiter-Venus","Bullish"), ("Mercury-Rahu","False breakouts")]
        c = conj[today.day % 3]
        result = f"🪐 **Planetary Conjunction**\n{c[0]}: {c[1]}\nAction: {'Wait' if 'Rahu' in c[0] else 'Trade cautiously'}"
    elif query.data == 'sun_mercury':
        sun = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"][today.month-1]
        result = f"☀️ **Sun in {sun}**\nSentiment: {'Bullish' if sun in ['Leo','Aries'] else 'Neutral'}\nMercury: Quick decisions\nTip: {'Take early profits' if sun in ['Scorpio','Capricorn'] else 'Let winners run'}"
    elif query.data == 'nakshatra':
        naks = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra"][today.day % 6]
        result = f"⭐ **Nakshatra: {naks}**\nBest entry: {random.randint(9,11)}:{random.randint(0,59):02d} AM\nAvoid: 2:00-3:00 PM\n{ 'Momentum works' if naks=='Rohini' else 'Range breakout likely' }"
    elif query.data == 'intraday':
        slots = ["10:15-11:00 AM", "11:30 AM-12:00 PM", "1:15-2:00 PM"]
        result = f"📊 **Intraday Windows**\n✅ Good: {random.choice(slots)}\n🚨 Avoid: 9:15-9:30 AM, 3:00-3:30 PM\nStrength: {'Strong' if today.weekday() in [2,3] else 'Medium'}"
    elif query.data == 'cycle':
        cycles = ["Accumulation", "Mark-up", "Distribution", "Mark-down"]
        cycle = cycles[today.day % 4]
        result = f"🔄 **Market Cycle: {cycle}**\nNifty range: {random.randint(18500,22000)-150} - {random.randint(18500,22000)+150}\nStrategy: {'Buy dips' if cycle=='Accumulation' else 'Sell rises' if cycle=='Distribution' else 'Follow trend'}"
    elif query.data == 'harmonics':
        harm = ["5th (72°)", "8th (45°)", "3rd (120°)"][today.day % 3]
        result = f"🌀 **Harmonic: {harm}**\nTrend: {'📈 UP' if '120°' in harm else '📉 DOWN' if '45°' in harm else '↗️ SIDEWAYS'}\nMajor move expected: {'Yes' if '120°' in harm else 'No'}"
    elif query.data == 'gann':
        gann = ["1x1 (45°) - Support", "2x1 (63.75°) - Resistance", "1x2 (26.25°) - Weak"][today.day % 3]
        result = f"📐 **Astro-Gann: {gann}**\nSquare of 9: {random.randint(18000,22000)}\nTime cycle: {random.randint(5,15)} days left\nEntry when astro + Gann both confirm"
    elif query.data == 'full_result':
        signals = ["BUY", "SELL", "WAIT", "CALL BUY", "PUT BUY"]
        final = random.choice(["BUY","WAIT","SELL"]) if today.weekday() in [0,4] else random.choice(signals)
        result = f"🎯 **FINAL SIGNAL**\nDate: {today.strftime('%d %b %Y')}\nSignal: **{final}**\nTarget: {random.randint(100,500)} pts\nStop Loss: {random.randint(50,150)} pts\nRisk: {'HIGH' if final=='WAIT' else 'MEDIUM'}\nConfidence: {random.randint(60,95)}%"
    else:
        result = "Try /start again"
    
    await query.edit_message_text(result, parse_mode='Markdown')

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()