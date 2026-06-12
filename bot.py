#!/usr/bin/env python3
"""
Astro Trading Engine + Technical + Fundamental Analysis
Full hybrid market signal generator.
"""

import numpy as np
import math
from datetime import datetime, timedelta, date
from skyfield.api import load, Topos
from skyfield import almanac
import yfinance as yf
import pandas_ta as ta

# ------------------------------------------------------------
# 0. Configuration
# ------------------------------------------------------------
LOCATION = Topos('19.0760 N', '72.8777 E')   # Mumbai
TYPICAL_PRICE = 22500   # placeholder NIFTY price

# ------------------------------------------------------------
# 1. Nakshatra setup
# ------------------------------------------------------------
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]
NAKSHATRA_START = np.linspace(0, 360, 28)[:-1]

def get_nakshatra(moon_long):
    idx = int(moon_long // (360/27))
    return NAKSHATRAS[idx]

def nakshatra_timing_factor(moon_long):
    name = get_nakshatra(moon_long)
    impact = {
        "Ashwini": 0.2, "Bharani": -0.1, "Krittika": 0.3, "Rohini": 0.1,
        "Mrigashira": -0.2, "Ardra": 0.5, "Punarvasu": 0.0, "Pushya": 0.6,
        "Ashlesha": -0.5, "Magha": -0.2, "Purva Phalguni": 0.1, "Uttara Phalguni": 0.2,
        "Hasta": 0.1, "Chitra": 0.2, "Swati": -0.1, "Vishakha": 0.3,
        "Anuradha": -0.1, "Jyeshtha": -0.4, "Mula": -0.3, "Purva Ashadha": 0.2,
        "Uttara Ashadha": 0.1, "Shravana": 0.0, "Dhanishtha": 0.2,
        "Shatabhisha": -0.2, "Purva Bhadrapada": -0.1, "Uttara Bhadrapada": 0.2,
        "Revati": -0.2
    }.get(name, 0.0)
    return impact, name

# ------------------------------------------------------------
# 2. Moon cycle
# ------------------------------------------------------------
def moon_phase_and_volatility(eph, observer, dt):
    ts = load.timescale()
    t = ts.utc(dt.year, dt.month, dt.day)
    angle = almanac.moon_phase(eph, observer, t).degrees
    # FIX: phase angle 0° = New Moon, 180° = Full Moon
    # So illuminated fraction = (1 - cos(angle)) / 2
    illum = (1 - math.cos(math.radians(angle))) / 2.0
    if illum < 0.03: phase = "New Moon"
    elif illum < 0.25: phase = "Waxing Crescent"
    elif illum < 0.45: phase = "First Quarter"
    elif illum < 0.55: phase = "Waxing Gibbous"
    elif illum < 0.75: phase = "Full Moon"
    elif illum < 0.97: phase = "Waning Gibbous"
    else: phase = "Waning Crescent"
    volatility = 2 * abs(illum - 0.5)
    return phase, illum, volatility

# ------------------------------------------------------------
# 3. Planetary longitudes, conjunctions, aspects
# ------------------------------------------------------------
PLANETS = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn']
CONJ_THRESH = 5.0
ASPECTS = {0: "conjunction", 60: "sextile", 90: "square", 120: "trine", 180: "opposition"}
ASPECT_ORB = 5

def get_longitudes(eph, ts, dt):
    t = ts.utc(dt.year, dt.month, dt.day, 12, 0, 0)
    longs = {}
    for name in PLANETS:
        body = eph[name]
        astro = eph['earth'].at(t).observe(body).apparent()
        lon, lat, dist = astro.ecliptic_latlon()
        longs[name] = lon.degrees
    return longs

def find_conjunctions(longs):
    conj = []
    names = list(longs.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            sep = abs(longs[names[i]] - longs[names[j]])
            sep = min(sep, 360-sep)
            if sep < CONJ_THRESH:
                conj.append((names[i], names[j], sep))
    return conj

def get_aspects(longs):
    scores = {k:0.0 for k in ASPECTS.values()}
    names = list(longs.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            diff = abs(longs[names[i]] - longs[names[j]])
            diff = min(diff, 360-diff)
            for angle, aname in ASPECTS.items():
                if abs(diff - angle) <= ASPECT_ORB:
                    strength = 1.0 - abs(diff - angle)/ASPECT_ORB
                    scores[aname] += strength
    return scores

def harmonic_score(aspect_scores):
    pos = aspect_scores["trine"] + aspect_scores["sextile"]*0.8
    neg = aspect_scores["square"] + aspect_scores["opposition"]*1.2
    return pos - neg

# ------------------------------------------------------------
# 4. Gann
# ------------------------------------------------------------
def gann_level_from_jupiter(jupiter_lon, price):
    gann_price = (jupiter_lon / 360.0) * 10000
    diff = (price - gann_price) / gann_price * 100
    return gann_price, diff

# ------------------------------------------------------------
# 5. Numerology
# ------------------------------------------------------------
def numerological_digit(n):
    n = int(n)
    if n == 0: return 0
    while n > 9 and n not in (11,22,33):
        n = sum(int(d) for d in str(n))
    return n

def numerology_bias(price, dt):
    price_digit = numerological_digit(price)
    date_digit = numerological_digit(dt.day + dt.month + dt.year)
    bias = "bullish" if (price_digit % 2) == (date_digit % 2) else "bearish"
    return price_digit, date_digit, bias

# ------------------------------------------------------------
# 6. Intraday planetary hours
# ------------------------------------------------------------
def planetary_hours(eph, observer, dt):
    ts = load.timescale()
    t0 = ts.utc(dt.year, dt.month, dt.day, 0,0,0)
    t1 = ts.utc(dt.year, dt.month, dt.day, 23,59,59)
    f = almanac.sunrise_sunset(eph, observer)
    times, events = almanac.find_discrete(t0, t1, f)
    sunrise = sunset = None
    for ti, ev in zip(times, events):
        if ev == 1: sunrise = ti.utc_datetime()
        elif ev == 2: sunset = ti.utc_datetime()
    if not sunrise or not sunset:
        return []
    day_len = (sunset - sunrise).total_seconds() / 3600.0
    hour_len = day_len / 12.0
    planet_order = ['sun','venus','mercury','moon','saturn','jupiter','mars']
    windows = []
    for i in range(12):
        start = sunrise + timedelta(hours=i*hour_len)
        end = sunrise + timedelta(hours=(i+1)*hour_len)
        ruler = planet_order[i % 7]
        if ruler in ('jupiter','venus'):
            windows.append((start.strftime("%H:%M"), end.strftime("%H:%M"), ruler))
    return windows

# ------------------------------------------------------------
# 7. Technical Signal (RSI, MACD, EMA)
# ------------------------------------------------------------
def get_technical_signal(symbol="NIFTY50.NS", period="1mo"):
    df = yf.download(symbol, period=period, interval="1d", progress=False)
    if df.empty:
        return 0
    rsi = ta.rsi(df['Close'], length=14).iloc[-1]
    macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    macd_hist = macd['MACDh_12_26_9'].iloc[-1]
    ema20 = ta.ema(df['Close'], length=20).iloc[-1]
    ema50 = ta.ema(df['Close'], length=50).iloc[-1]
    
    score = 0.0
    if rsi < 30: score += 1
    elif rsi > 70: score -= 1
    if macd_hist > 0: score += 0.5
    else: score -= 0.5
    if ema20 > ema50: score += 0.5
    else: score -= 0.5
    
    if score > 0.5: return 1
    elif score < -0.5: return -1
    else: return 0

# ------------------------------------------------------------
# 8. Fundamental Signal (P/E ratio)
# ------------------------------------------------------------
def get_fundamental_signal(symbol="^NSEI"):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    pe = info.get('trailingPE', None)
    if pe is None:
        return 0
    if pe < 18: return 1
    elif pe > 25: return -1
    else: return 0

# ------------------------------------------------------------
# 9. Main Astro Analysis (return dict)
# ------------------------------------------------------------
def full_astro_analysis(date_obj, current_price=TYPICAL_PRICE):
    eph = load('de421.bsp')
    ts = load.timescale()
    observer = LOCATION
    dt = datetime(date_obj.year, date_obj.month, date_obj.day, 12,0,0)
    
    # Planetary longs
    longs = get_longitudes(eph, ts, dt)
    # Moon
    moon_lon = longs['moon']
    nakshatra_impact, nakshatra_name = nakshatra_timing_factor(moon_lon)
    phase, illum, moon_vol = moon_phase_and_volatility(eph, observer, dt)
    conjunctions = find_conjunctions(longs)
    aspects = get_aspects(longs)
    harm_score = harmonic_score(aspects)
    # Gann
    gann_price, gann_diff = gann_level_from_jupiter(longs['jupiter'], current_price)
    # Numerology
    price_digit, date_digit, num_bias = numerology_bias(current_price, dt)
    # Intraday windows
    windows = planetary_hours(eph, observer, dt)
    # Vedic lord
    lord_map = {
        "Ashwini":"Ketu","Bharani":"Venus","Krittika":"Sun","Rohini":"Moon",
        "Mrigashira":"Mars","Ardra":"Rahu","Punarvasu":"Jupiter","Pushya":"Saturn",
        "Ashlesha":"Mercury","Magha":"Ketu","Purva Phalguni":"Venus","Uttara Phalguni":"Sun",
        "Hasta":"Moon","Chitra":"Mars","Swati":"Rahu","Vishakha":"Jupiter","Anuradha":"Saturn",
        "Jyeshtha":"Mercury","Mula":"Ketu","Purva Ashadha":"Venus","Uttara Ashadha":"Sun",
        "Shravana":"Moon","Dhanishtha":"Mars","Shatabhisha":"Rahu","Purva Bhadrapada":"Jupiter",
        "Uttara Bhadrapada":"Saturn","Revati":"Mercury"
    }
    lord = lord_map.get(nakshatra_name, "Unknown")
    vedic_bias = 0.2 if lord in ("Jupiter","Venus") else (-0.1 if lord in ("Saturn","Rahu","Ketu") else 0.0)
    
    # Aggregate astro score
    total_astro = (nakshatra_impact * 0.3 +
                   moon_vol * 0.2 +
                   (harm_score / 5) * 0.3 +
                   (1 if num_bias == "bullish" else -1) * 0.1 +
                   vedic_bias * 0.1)
    if conjunctions:
        total_astro += 0.2 * len(conjunctions)
    
    if total_astro > 0.4: sent = "Strongly Bullish"
    elif total_astro > 0.1: sent = "Bullish"
    elif total_astro > -0.1: sent = "Neutral"
    elif total_astro > -0.4: sent = "Bearish"
    else: sent = "Strongly Bearish"
    
    return {
        "score": total_astro,
        "sentiment": sent,
        "moon_phase": phase,
        "nakshatra": nakshatra_name,
        "nakshatra_lord": lord,
        "moon_volatility": moon_vol,
        "conjunctions": conjunctions,
        "harmonic_score": harm_score,
        "num_bias": num_bias,
        "good_windows": windows
    }

# ------------------------------------------------------------
# 10. Full Hybrid (Astro + Tech + Funda)
# ------------------------------------------------------------
def full_hybrid_analysis(date_obj, current_price, symbol="NIFTY50.NS"):
    astro = full_astro_analysis(date_obj, current_price)
    tech = get_technical_signal(symbol)
    fund = get_fundamental_signal("^NSEI")
    
    final_score = astro['score'] + (tech * 0.3) + (fund * 0.2)
    confidence = min(100, max(0, (final_score + 1) * 50))
    
    if final_score > 0.4: sentiment = "Strongly Bullish"
    elif final_score > 0.1: sentiment = "Bullish"
    elif final_score > -0.1: sentiment = "Neutral"
    elif final_score > -0.4: sentiment = "Bearish"
    else: sentiment = "Strongly Bearish"
    
    print("\n" + "="*70)
    print(f"FULL HYBRID ANALYSIS – {date_obj}")
    print("="*70)
    print(f"Current Price: {current_price}")
    print(f"\n--- ASTRO COMPONENT ---")
    print(f"Nakshatra: {astro['nakshatra']} (Lord {astro['nakshatra_lord']})")
    print(f"Moon Phase: {astro['moon_phase']} | Volatility: {astro['moon_volatility']:.2f}")
    print(f"Astro Score: {astro['score']:.2f} -> {astro['sentiment']}")
    print(f"Planetary conjunctions: {len(astro['conjunctions'])}")
    print(f"Numerology Bias: {astro['num_bias']}")
    if astro['good_windows']:
        print("Intraday windows:", ", ".join([f"{w[0]}-{w[1]}({w[2]})" for w in astro['good_windows']]))
    print(f"\n--- TECHNICAL SIGNAL (RSI+MACD+EMA) ---")
    print(f"Tech Score: {tech}  (-1=Bear,0=Neutral,1=Bull)")
    print(f"\n--- FUNDAMENTAL SIGNAL (P/E) ---")
    print(f"Fund Score: {fund}  (-1=Overvalued,0=Neutral,1=Undervalued)")
    print(f"\n--- COMBINED ---")
    print(f"Final Score: {final_score:.2f}")
    print(f"Market Sentiment: {sentiment}")
    print(f"Confidence: {confidence:.0f}%")
    print("="*70)
    return {
        "date": date_obj,
        "price": current_price,
        "sentiment": sentiment,
        "final_score": final_score,
        "confidence": confidence
    }

# ------------------------------------------------------------
# 11. Run for today
# ------------------------------------------------------------
if __name__ == "__main__":
    today = date.today()
    # Replace with live NIFTY price if needed
    result = full_hybrid_analysis(today, current_price=22500, symbol="NIFTY50.NS")
