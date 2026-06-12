import os
import logging
from datetime import datetime
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"
]

def calc_rsi(series, period=14):
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return (100 - (100 / (1 + rs))).iloc[-1]

def get_signal(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1d",
                         auto_adjust=True, progress=False)
        if df.empty or len(df) < 25:
            return {"error": "ডেটা পাওয়া যায়নি"}
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        close  = df["Close"]
        rsi    = calc_rsi(close)
        ema9   = close.ewm(span=9).mean()
        ema21  = close.ewm(span=21).mean()
        price  = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        change_pct = ((price - prev_close) / prev_close) * 100

        if rsi < 35 and ema9.iloc[-1] > ema21.iloc[-1] and ema9.iloc[-2] <= ema21.iloc[-2]:
            signal = "🟢 STRONG BUY"
            reason = f"RSI oversold ({rsi:.1f}) + EMA bullish crossover"
        elif rsi < 40 and price > ema21.iloc[-1]:
            signal = "🟡 BUY"
            reason = f"RSI low ({rsi:.1f}), price above EMA21"
        elif rsi > 70 and ema9.iloc[-1] < ema21.iloc[-1]:
            signal = "🔴 SELL"
            reason = f"RSI overbought ({rsi:.1f}) + bearish EMA"
        elif rsi > 65:
            signal = "🟠 CAUTION"
            reason = f"RSI high ({rsi:.1f}), possible reversal"
        else:
            signal = "⚪ HOLD"
            reason = f"RSI neutral ({rsi:.1f})"

        return {
            "symbol": symbol.replace(".NS", ""),
            "price": price,
            "change_pct": change_pct,
            "rsi": rsi,
            "ema9": float(ema9.iloc[-1]),
            "ema21": float(ema21.iloc[-1]),
            "signal": signal,
            "reason": reason,
        }
    except Exception as e:
        return {"error": str(e)}

def format_msg(data):
    if "error" in data:
        return f"❌ Error: {data['error']}"
    arrow = "📈" if data["change_pct"] >= 0 else "📉"
    return (
        f"*{data['symbol']}*\n"
        f"💰 Price  : ₹{data['price']:,.2f}  {arrow} {data['change_pct']:+.2f}%\n"
        f"📊 RSI    : {data['rsi']:.1f}\n"
        f"📉 EMA9   : ₹{data['ema9']:,.2f}\n"
        f"📈 EMA21  : ₹{data['ema21']:,.2f}\n"
        f"🎯 Signal : {data['signal']}\n"
        f"💡 Reason : {data['reason']}\n"
        f"🕐 Time   : {datetime.now().strftime('%d %b, %I:%M %p')}"
    )

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *NSE Trading Alert Bot*\n\n"
        "Commands:\n"
        "/price RELIANCE — live price\n"
        "/signal RELIANCE — buy/sell signal\n"
        "/watchlist — সব stocks\n"
        "/help — সাহায্য\n\n"
        "⚠️ _Educational purpose only_",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Help*\n\n"
        "`/price RELIANCE` — current price\n"
        "`/signal TCS` — RSI+EMA signal\n"
        "`/watchlist` — সব stocks-এর signal",
        parse_mode="Markdown"
    )

async def price_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /price RELIANCE")
        return
    symbol = ctx.args[0].upper() + ".NS"
    await update.message.reply_text(f"⏳ Price আনছি...")
    try:
        ticker = yf.Ticker(symbol)
        price  = ticker.fast_info.last_price
        await update.message.reply_text(
            f"💰 *{ctx.args[0].upper()}*\n"
            f"Price : ₹{price:,.2f}\n"
            f"🕐 {datetime.now().strftime('%d %b, %I:%M %p')}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def signal_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /signal RELIANCE")
        return
    symbol = ctx.args[0].upper() + ".NS"
    await update.message.reply_text("⏳ Signal বিশ্লেষণ হচ্ছে...")
    data = get_signal(symbol)
    await update.message.reply_text(format_msg(data), parse_mode="Markdown")

async def watchlist_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Watchlist analyze হচ্ছে...")
    results = []
    for sym in WATCHLIST:
        data = get_signal(sym)
        results.append(format_msg(data))
    header = f"📋 *Watchlist Report*\n🕐 {datetime.now().strftime('%d %b, %I:%M %p')}\n\n"
    full = header + "\n─────────────\n".join(results)
    for i in range(0, len(full), 4000):
        await update.message.reply_text(full[i:i+4000], parse_mode="Markdown")

async def auto_alert(ctx: ContextTypes.DEFAULT_TYPE):
    alerts = []
    for sym in WATCHLIST:
        data = get_signal(sym)
        if "error" not in data and ("BUY" in data["signal"] or "SELL" in data["signal"]):
            alerts.append(format_msg(data))
    if alerts and CHAT_ID:
        header = f"🔔 *Auto Alert*\n🕐 {datetime.now().strftime('%d %b, %I:%M %p')}\n\n"
        msg = header + "\n─────────────\n".join(alerts)
        await ctx.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",     start))
    app.add_handler(CommandHandler("help",      help_cmd))
    app.add_handler(CommandHandler("price",     price_cmd))
    app.add_handler(CommandHandler("signal",    signal_cmd))
    app.add_handler(CommandHandler("watchlist", watchlist_cmd))
    app.job_queue.run_repeating(auto_alert, interval=3600, first=60)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
