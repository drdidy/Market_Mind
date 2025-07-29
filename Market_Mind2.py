# ═══════════════════════════════════════════════════════════════════════════════
# 📈 DR DIDY SPX FORECAST - ENHANCED VERSION v1.6.1
# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 Complete Market Forecasting System with Playbooks & Two-Stage Exits
# 🔧 Clean, Well-Organized Code for Easy Maintenance and Collaboration

import json
import base64
import streamlit as st
from datetime import datetime, date, time, timedelta
from copy import deepcopy
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PAGE_TITLE = "Dr Didy SPX Forecast"
PAGE_ICON = "📈"
VERSION = "1.6.1"

BASE_SLOPES = {
    "SPX_HIGH": -0.2792, "SPX_CLOSE": -0.2792, "SPX_LOW": -0.2792,
    "TSLA": -0.1508, "NVDA": -0.0485, "AAPL": -0.0750,
    "MSFT": -0.17,   "AMZN": -0.03,   "GOOGL": -0.07,
    "META": -0.035,  "NFLX": -0.23,
}

ICONS = {
    "SPX": "🧭", "TSLA": "🚗", "NVDA": "🧠", "AAPL": "🍎",
    "MSFT": "🪟", "AMZN": "📦", "GOOGL": "🔍",
    "META": "📘", "NFLX": "📺"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 PLAYBOOK DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

BEST_TRADING_DAYS = {
    "NVDA": {"days": "Tue / Thu", "rationale": "Highest volatility and option-flow mid-week"},
    "META": {"days": "Tue / Thu", "rationale": "News-feed reprice, AI headlines often drop Tue/Thu"},
    "TSLA": {"days": "Mon / Wed", "rationale": "Post-weekend gamma squeeze & mid-week momentum"},
    "AAPL": {"days": "Mon / Wed", "rationale": "Earnings drift & supply-chain headlines"},
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
        "📈 **Scale into positions**: 1/3 initial, 1/3 confirmation, 1/3 momentum",
        "📅 **Reduce size on Fridays**: Weekend risk isn't worth it"
    ],
    "stop_strategy": [
        "🛑 **Hard stops at -15% for options**: No exceptions",
        "📈 **Trailing stops after +25%**: Protect profits aggressively",
        "🕞 **Time stops at 3:45 PM**: Avoid close volatility"
    ],
    "market_context": [
        "📊 **VIX above 25**: Reduce position sizes by 50%",
        "📈 **Major earnings week**: Avoid unrelated tickers",
        "📢 **FOMC/CPI days**: Trade post-announcement only (10:30+ AM)"
    ],
    "psychological": [
        "🛑 **3 losses in a row**: Step away for 1 hour minimum",
        "🎉 **Big win euphoria**: Reduce next position size by 50%",
        "😡 **Revenge trading**: Automatic day-end (no exceptions)"
    ],
    "performance_targets": [
        "🎯 **Win rate target: 55%+**: More important than individual trade size",
        "💰 **Risk/reward minimum: 1:1.5**: Risk $100 to make $150+",
        "📊 **Weekly P&L cap**: Stop after +20% or -10% weekly moves"
    ]
}

SPX_ANCHOR_RULES = {
    "rth_breaks": [
        "📉 **30-min close below RTH entry anchor**: Price may retrace above anchor line but will fall below again shortly after",
        "🚫 **Don't chase the bounce**: Prepare for the inevitable breakdown",
        "⏱️ **Wait for confirmation**: Let the market give you the entry"
    ],
    "extended_hours": [
        "🌙 **Extended session weakness + recovery**: Use recovered anchor as buy signal in RTH",
        "📈 **Extended session anchors carry forward momentum** into regular trading hours",
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
        "🎯 **Identify two overnight option low points** that rise $400-$500",
        "📐 **Use them to set Tuesday contract slope** (handled in SPX tab)",
        "⚡ **Tuesday contract setups often provide best mid-week momentum**"
    ],
    "thursday_play": [
        "💰 **If Wednesday's low premium was cheap**: Thursday low ≈ Wed low (buy-day)",
        "📉 **If Wednesday stayed pricey**: Thursday likely a put-day (avoid longs)",
        "🔄 **Wednesday pricing telegraphs Thursday direction**"
    ]
}

TIME_RULES = {
    "market_sessions": [
        "🕘 **9:30-10:00 AM**: Initial range, avoid FOMO entries",
        "🕙 **10:30-11:30 AM**: Institutional flow window, best entries",
        "🕐 **2:00-3:00 PM**: Final push time, momentum plays",
        "🕞 **3:30+ PM**: Scalps only, avoid new positions"
    ],
    "volume_patterns": [
        "📊 **Entry volume > 20-day average**: Strong conviction signal",
        "📉 **Declining volume on bounces**: Fade the move",
        "⚡ **Volume spike + anchor break**: High probability setup"
    ],
    "multi_timeframe": [
        "🎯 **5-min + 15-min + 1-hour** all pointing same direction = high conviction",
        "❓ **Conflicting timeframes** = wait for resolution",
        "📊 **Daily anchor + intraday setup** = strongest edge"
    ]
}

