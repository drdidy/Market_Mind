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

# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

if "theme" not in st.session_state:
    st.session_state.update(
        theme="Dark",
        slopes=deepcopy(BASE_SLOPES),
        presets={},
        contract_anchor=None,
        contract_slope=None,
        contract_price=None,
        forecasts_generated=False,
        selected_playbook=None
    )

# Load slopes from URL parameters if available
if st.query_params.get("s"):
    try:
        st.session_state.slopes.update(
            json.loads(base64.b64decode(st.query_params["s"][0]).decode())
        )
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ENHANCED CSS STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* Import modern font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Root variables for theming */
:root {
    --border-radius: 16px;
    --shadow-light: 0 4px 20px rgba(0, 0, 0, 0.08);
    --shadow-medium: 0 8px 32px rgba(0, 0, 0, 0.12);
    --shadow-heavy: 0 16px 48px rgba(0, 0, 0, 0.16);
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-success: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    --gradient-warning: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    --gradient-info: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

/* Global styles */
html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 400;
    line-height: 1.6;
}

/* Dark theme */
.stApp {
    background: linear-gradient(135deg, #0c1426 0%, #1a1f36 50%, #0f1419 100%);
    color: #e2e8f0;
}

/* Hide Streamlit branding */
#MainMenu, footer, .stDeployButton { display: none !important; }

/* Enhanced banner */
.main-banner {
    background: var(--gradient-primary);
    text-align: center;
    color: white;
    border-radius: var(--border-radius);
    padding: 2rem 1.5rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-heavy);
    position: relative;
    overflow: hidden;
}

.main-banner::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%);
    z-index: 1;
}

.main-banner h1 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    position: relative;
    z-index: 2;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.main-banner .subtitle {
    font-size: 1.1rem;
    font-weight: 400;
    opacity: 0.9;
    position: relative;
    z-index: 2;
    margin-top: 0.5rem;
}

/* Enhanced cards container */
.cards-container {
    display: flex;
    gap: 1.5rem;
    margin: 2rem 0;
    overflow-x: auto;
    padding: 0.5rem 0;
}

.metric-card {
    flex: 1;
    min-width: 280px;
    padding: 2rem;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-medium);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    z-index: 1;
}

.metric-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: var(--shadow-heavy);
}

.metric-card.high {
    background: rgba(34, 197, 94, 0.1);
}
.metric-card.high::before {
    background: var(--gradient-success);
}

.metric-card.close {
    background: rgba(59, 130, 246, 0.1);
}
.metric-card.close::before {
    background: var(--gradient-info);
}

.metric-card.low {
    background: rgba(239, 68, 68, 0.1);
}
.metric-card.low::before {
    background: var(--gradient-warning);
}

.card-content {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.card-icon {
    width: 4rem;
    height: 4rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    color: white;
    flex-shrink: 0;
}

.card-icon.high { background: var(--gradient-success); }
.card-icon.close { background: var(--gradient-info); }
.card-icon.low { background: var(--gradient-warning); }

.card-text {
    flex: 1;
}

.card-title {
    font-size: 0.95rem;
    font-weight: 500;
    opacity: 0.8;
    margin-bottom: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.card-value {
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.1;
}

/* Section headers */
.section-header {
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--border-radius);
    padding: 1.5rem 2rem;
    margin: 2rem 0 1rem 0;
    border-left: 4px solid var(--gradient-primary);
    backdrop-filter: blur(10px);
}

.section-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

/* Enhanced tables */
.dataframe {
    border-radius: var(--border-radius) !important;
    overflow: hidden;
    box-shadow: var(--shadow-medium);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.dataframe table {
    font-family: 'Inter', sans-serif !important;
}

.dataframe th {
    background: rgba(255, 255, 255, 0.1) !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
}

/* Info boxes */
.info-box {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    margin: 1rem 0;
    backdrop-filter: blur(10px);
}

.success-box {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
}

.warning-box {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.2);
}

/* Responsive design */
@media (max-width: 768px) {
    .main-banner h1 { font-size: 2rem; }
    .main-banner { padding: 1.5rem 1rem; }
    .cards-container { flex-direction: column; }
    .metric-card { min-width: auto; padding: 1.5rem; }
    .card-icon { width: 3rem; height: 3rem; font-size: 1.5rem; }
    .card-value { font-size: 1.8rem; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_metric_card(card_type, icon, title, value):
    """Create a beautiful metric card with enhanced styling"""
    st.markdown(f"""
    <div class="metric-card {card_type}">
        <div class="card-content">
            <div class="card-icon {card_type}">{icon}</div>
            <div class="card-text">
                <div class="card-title">{title}</div>
                <div class="card-value">{value:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_section_header(icon, title):
    """Create a styled section header"""
    st.markdown(f"""
    <div class="section-header">
        <h2>{icon} {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def make_time_slots(start_time=time(7, 30)):
    """Generate time slots for trading sessions"""
    base = datetime(2025, 1, 1, start_time.hour, start_time.minute)
    slot_count = 15 - (2 if start_time.hour == 8 and start_time.minute == 30 else 0)
    return [(base + timedelta(minutes=30 * i)).strftime("%H:%M") for i in range(slot_count)]

def calculate_spx_blocks(anchor_time, target_time):
    """Calculate SPX blocks with market hours consideration"""
    blocks = 0
    current = anchor_time
    while current < target_time:
        if current.hour != 16:  # Skip 4 PM hour
            blocks += 1
        current += timedelta(minutes=30)
    return blocks

def calculate_stock_blocks(anchor_time, target_time):
    """Calculate stock blocks (simple 30-minute intervals)"""
    return max(0, int((target_time - anchor_time).total_seconds() // 1800))

def create_forecast_table(price, slope, anchor, forecast_date, time_slots, is_spx=True, fan_mode=False, two_stage_exits=False):
    """Create enhanced forecast table with projections and optional two-stage exits"""
    rows = []
    
    for slot in time_slots:
        hour, minute = map(int, slot.split(":"))
        target_time = datetime.combine(forecast_date, time(hour, minute))
        
        if is_spx:
            blocks = calculate_spx_blocks(anchor, target_time)
        else:
            blocks = calculate_stock_blocks(anchor, target_time)
        
        if two_stage_exits:
            # SPX Two-Stage Exit System with 8.5 point target
            entry_price = round(price + slope * blocks, 2)
            first_exit = round(entry_price + 8.5, 2)  # 8.5 point target
            fan_exit = round(price - slope * blocks, 2)  # Fan model exit
            
            rows.append({
                "Time": slot,
                "Entry": entry_price,
                "Exit 1 (+8.5)": first_exit,
                "Fan Exit": fan_exit,
                "Profit 1": "+8.5",
                "Fan Profit": round(abs(entry_price - fan_exit), 1)
            })
            
        elif fan_mode:
            # Regular fan mode (for stocks)
            entry_price = round(price + slope * blocks, 2)
            exit_price = round(price - slope * blocks, 2)
            rows.append({
                "Time": slot,
                "Entry": entry_price,
                "Exit": exit_price,
                "Spread": round(abs(entry_price - exit_price), 2)
            })
        else:
            # Regular projection mode
            projected = round(price + slope * blocks, 2)
            rows.append({
                "Time": slot,
                "Projected": projected,
                "Change": round(slope * blocks, 2)
            })
    
    return pd.DataFrame(rows)

def calculate_fibonacci_levels(swing_low, swing_high):
    """Calculate key Fibonacci retracement levels for bounce analysis"""
    price_range = swing_high - swing_low
    
    fib_levels = {
        "0.236": swing_high - (price_range * 0.236),
        "0.382": swing_high - (price_range * 0.382),
        "0.500": swing_high - (price_range * 0.500),
        "0.618": swing_high - (price_range * 0.618),
        "0.786": swing_high - (price_range * 0.786),  # 🎯 KEY ALGO ENTRY LEVEL
        "1.000": swing_low
    }
    
    return fib_levels

def create_fibonacci_table(swing_low, swing_high):
    """Create a formatted table showing Fibonacci levels"""
    fib_levels = calculate_fibonacci_levels(swing_low, swing_high)
    
    fib_data = []
    for level, price in fib_levels.items():
        emphasis = "🎯 **ALGO ENTRY**" if level == "0.786" else ""
        fib_data.append({
            "Fibonacci Level": level,
            "Price": f"${price:.2f}",
            "Note": emphasis
        })
    
    return pd.DataFrame(fib_data)

# Define time slots
SPX_SLOTS = make_time_slots(time(8, 30))
GENERAL_SLOTS = make_time_slots(time(7, 30))