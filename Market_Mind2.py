# ═══════════════════════════════════════════════════════════════════════════════
# 📈 DR DIDY MARKETMIND - VERSION v1.6.1
# ═══════════════════════════════════════════════════════════════════════════════

import json
import base64
import streamlit as st
from datetime import datetime, date, time, timedelta
from copy import deepcopy
import pandas as pd
import pytz

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PAGE_TITLE = "Dr Didy MarketMind"
PAGE_ICON = "🧠"
VERSION = "1.6.1"
DEFAULT_TIMEZONE = "America/Chicago"

BASE_SLOPES = {
    "SPX_HIGH": -0.2792, "SPX_CLOSE": -0.2792, "SPX_LOW": -0.2792,
    "TSLA": -0.1508, "NVDA": -0.0485, "AAPL": -0.0750,
    "MSFT": -0.17, "AMZN": -0.03, "GOOGL": -0.07,
    "META": -0.035, "NFLX": -0.23,
}

ICONS = {
    "SPX": "🧭", "TSLA": "🚗", "NVDA": "🧠", "AAPL": "🍎",
    "MSFT": "🪟", "AMZN": "📦", "GOOGL": "🔍",
    "META": "📘", "NFLX": "📺"
}

TIMEZONE_OPTIONS = {
    "🇺🇸 Chicago (CT)": "America/Chicago",
    "🇺🇸 New York (ET)": "America/New_York", 
    "🇺🇸 Los Angeles (PT)": "America/Los_Angeles",
    "🇺🇸 Denver (MT)": "America/Denver",
    "🇬🇧 London (GMT)": "Europe/London",
    "🇯🇵 Tokyo (JST)": "Asia/Tokyo",
    "🇦🇺 Sydney (AEST)": "Australia/Sydney",
    "🇩🇪 Frankfurt (CET)": "Europe/Berlin",
    "🇸🇬 Singapore (SGT)": "Asia/Singapore",
    "🌍 UTC": "UTC"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 PLAYBOOK DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

BEST_TRADING_DAYS = {
    "NVDA": {"days": "Tue / Thu", "rationale": "Highest volatility and option-flow mid-week"},
    "META": {"days": "Tue / Thu", "rationale": "News-feed reprice, AI headlines often drop Tue/Thu"},
    "TSLA": {"days": "Mon / Wed", "rationale": "Post-weekend gamma squeeze & mid-week momentum"},
    "AAPL": {"days": "Mon / Wed", "rationale": "Earnings drift & supply-chain headlines"},
    "MSFT": {"days": "Tue / Thu", "rationale": "Enterprise announcements and cloud updates"},
    "AMZN": {"days": "Wed / Thu", "rationale": "Mid-week marketplace volume & OPEX flow"},
    "GOOGL": {"days": "Thu / Fri", "rationale": "Search-ad spend updates tilt end-week"},
    "NFLX": {"days": "Tue / Fri", "rationale": "Subscriber metrics chatter on Tue, positioning unwind on Fri"}
}

SPX_GOLDEN_RULES = [
    "🚪 **Exit levels are exits - never entries**",
    "🧲 **Anchors are magnets, not timing signals - let price come to you**",
    "🎁 **The market will give you your entry - don't force it**",
    "🔄 **Consistency in process trumps perfection in prediction**",
    "❓ **When in doubt, stay out - there's always another trade**",
    "🏗️ **SPX ignores the full 16:00-17:00 maintenance block**"
]

RISK_RULES = {
    "position_sizing": [
        "🎯 **Never risk more than 2% per trade**: Consistency beats home runs",
        "📈 **Scale into positions**: 1/3 at anchor touch, 1/3 on volume confirmation, 1/3 on trend continuation",
        "⏰ **Scaling Timing**: Wait minimum 15 minutes between entries to avoid overcommitting",
        "📅 **Reduce size on Fridays**: Weekend risk and 0DTE isn't worth it"
    ],
    "stop_strategy": [
        "🛑 **Hard stops at -20% for options**: No exceptions",
        "📈 **Trailing stops after +40%**: Protect profits aggressively",
        "🕞 **Time stops at 1:45 PM**: Avoid close volatility"
    ],
    "market_context": [
        "📊 **VIX above 25**: Reduce position sizes by 50%",
        "📈 **Major earnings week**: Avoid unrelated tickers",
        "📢 **FOMC/CPI days**: Trade post-announcement only (10:30+ AM and 1:00+ PM)"
    ],
    "psychological": [
        "🛑 **2 daily losses in a row**: Step away for 2 DAYS minimum",
        "🎉 **Big win euphoria**: Reduce next day's position size by 25%",
        "😡 **Revenge trading**: Automatic day-end (no exceptions)"
    ],
    "performance_targets": [
        "🎯 **Win rate target: 80%+**: More important than individual trade size",
        "💰 **Risk/reward minimum: 1:1.5**: Risk $1000 to make $1500+",
        "📊 **Weekly portfolio P&L cap**: Stop after +25% or -10% weekly moves"
    ]
}

SPX_ANCHOR_RULES = {
    "rth_breaks": [
        "📉 **30-min close below RTH entry anchor**: RTH entry anchor = 8:30 AM price level for HIGH and CLOSE",
        "🚫 **Don't chase the bounce**: If price breaks anchor sharply, Price may retrace above level but will fall below again",
        "⏱️ **If looking for a put, Wait for confirmation**: Let market give you entry after the retrace fails",
        "📊 **Key Level**: 8:30 AM anchor price level becomes critical support/resistance for the session"
    ],
    "extended_hours": [
        "🌙 **Extended session weakness + recovery**: Use recovered anchor as buy signal in RTH",
        "📈 **Extended session anchors carry forward momentum** into regular trading hours on Tuesdays and Thursdays",
        "🎯 **Overnight anchor recovery**: Strong setup for next day strength"
    ],
    "mon_wed_fri": [
        "📅 **No touch of high, close, or low anchors** on Mon/Wed/Fri = Potential sell day later",
        "⏳ **Don't trade TO the anchor**: Let the market give you the entry",
        "✅ **Wait for price action confirmation** rather than anticipating touches"
    ],
    "fibonacci_bounce": [
        "📈 **SPX Line Touch + Bounce**: When SPX price touches line and bounces, contract follows the same pattern",
        "🎯 **0.786 Fibonacci Entry**: Contract retraces to 0.786 fib level (low to high of bounce) = major algo entry point",
        "⏰ **Next Hour Candle**: The 0.786 retracement typically occurs in the NEXT hour candle, not the same one",
        "💰 **High Probability**: Algos consistently enter at 0.786 level for profitable runs",
        "📊 **Setup Requirements**: Clear bounce off SPX line + identifiable low-to-high swing for fib calculation"
    ]
}

CONTRACT_STRATEGIES = {
    "tuesday_play": [
        "🎯 **Identify two overnight option low points**: Look for contract lows between 8:00 PM - 7:30 AM that rise $400-$500",
        "📐 **Use them to set Tuesday contract slope**: Plot line between these two points in Contracts tab",
        "⏰ **Timing Window**: Focus on 8:00 PM - 7:00 AM overnight session for clearest signals",
        "⚡ **Tuesday contract setups often provide best mid-week momentum**"
    ],
    "thursday_play": [
        "💰 **If Wednesday's low premium was cheap**: Under $5 = Thursday low ≈ Wed low (buy-day)",
        "📉 **If Wednesday stayed pricey**: Above $15 = Thursday likely a put-day (avoid longs)",
        "🔄 **Wednesday 2:00-3:00 PM pricing**: Final hour premium levels predict Thursday direction",
        "📊 **Price Threshold**: $5-$15 = neutral zone, wait for Thursday open confirmation"
    ]
}

TIME_RULES = {
    "market_sessions": [
        "🕘 **8:30-9:00 AM**: Initial range, avoid FOMO entries",
        "🕙 **9:30-10:30 AM**: Institutional flow window - algos finish overnight rebalancing, clearest directional moves",
        "📊 **Institutional Signals**: Look for sustained volume + clean price action during this hour",
        "🕐 **1:00-2:00 PM**: Final push time, momentum plays",
        "🕞 **2:30+ PM**: Avoid new positions"
    ],
    "volume_patterns": [
        "📊 **Entry volume > 20-day average**: Strong conviction signal",
        "📉 **Declining volume on bounces**: Fade the move",
        "⚡ **Volume spike + anchor break**: High probability breakout - trade the direction",
        "🛡️ **Volume spike at anchor (no break)**: Anchor holding strong - trade the bounce",
        "🔄 **Volume confirms institutional participation**: Big money validates the move",
        "❌ **Low volume breakouts**: Often fail - wait for volume confirmation",
        "📈 **Volume expansion on trend continuation**: Momentum building - stay with move",
        "⚠️ **Volume divergence**: Price up but volume down = potential reversal warning"
    ],
    "multi_timeframe": [
        "🎯 **5-min + 15-min + 1-hour** all pointing same direction = high conviction",
        "❓ **Conflicting timeframes** = wait for resolution",
        "📊 **Daily anchor + intraday setup** = strongest edge"
    ]
}
