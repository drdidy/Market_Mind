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
# 🎨 NEUMORPHIC CSS STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* Import modern font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Root variables for neumorphic theming */
:root {
    --bg-color: #e0e0e0;
    --text-primary: #4a4a4a;
    --text-secondary: #6a6a6a;
    --text-muted: #8a8a8a;
    --shadow-light: #ffffff;
    --shadow-dark: #babebc;
    --border-radius: 20px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    /* Neumorphic shadows */
    --neu-convex: 9px 9px 16px var(--shadow-dark), -9px -9px 16px var(--shadow-light);
    --neu-concave: inset 9px 9px 16px var(--shadow-dark), inset -9px -9px 16px var(--shadow-light);
    --neu-flat: 4px 4px 8px var(--shadow-dark), -4px -4px 8px var(--shadow-light);
    --neu-pressed: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light);
}

/* Global styles */
html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 400;
    line-height: 1.6;
}

/* Neumorphic theme */
.stApp {
    background: var(--bg-color);
    color: var(--text-primary);
}

/* Hide Streamlit branding */
#MainMenu, footer, .stDeployButton { display: none !important; }

/* Enhanced neumorphic banner */
.main-banner {
    background: var(--bg-color);
    text-align: center;
    color: var(--text-primary);
    border-radius: var(--border-radius);
    padding: 3rem 2rem;
    margin-bottom: 2rem;
    box-shadow: var(--neu-convex);
    position: relative;
    overflow: hidden;
}

.main-banner h1 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    color: var(--text-primary);
    text-shadow: 1px 1px 2px var(--shadow-light);
}

.main-banner .subtitle {
    font-size: 1.1rem;
    font-weight: 400;
    color: var(--text-secondary);
    margin-top: 0.5rem;
}

/* Neumorphic cards container */
.cards-container {
    display: flex;
    gap: 2rem;
    margin: 2rem 0;
    overflow-x: auto;
    padding: 1rem 0;
}

.metric-card {
    flex: 1;
    min-width: 280px;
    padding: 2rem;
    border-radius: var(--border-radius);
    box-shadow: var(--neu-convex);
    transition: var(--transition);
    background: var(--bg-color);
    border: none;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 12px 12px 20px var(--shadow-dark), -12px -12px 20px var(--shadow-light);
}

.metric-card:active {
    box-shadow: var(--neu-pressed);
    transform: translateY(1px);
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
    color: var(--text-primary);
    flex-shrink: 0;
    background: var(--bg-color);
    box-shadow: var(--neu-flat);
}

.card-text {
    flex: 1;
}

.card-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.card-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    line-height: 1.1;
}

/* Neumorphic section headers */
.section-header {
    background: var(--bg-color);
    border-radius: var(--border-radius);
    padding: 1.5rem 2rem;
    margin: 2rem 0 1rem 0;
    box-shadow: var(--neu-concave);
}

.section-header h2 {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

/* Neumorphic tables */
.dataframe {
    border-radius: var(--border-radius) !important;
    overflow: hidden;
    box-shadow: var(--neu-convex);
    background: var(--bg-color);
    border: none !important;
}

.dataframe table {
    font-family: 'Inter', sans-serif !important;
    background: var(--bg-color) !important;
}

.dataframe th {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
    box-shadow: var(--neu-flat);
    border: none !important;
}

.dataframe td {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    border: none !important;
}

/* Neumorphic info boxes */
.info-box {
    background: var(--bg-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: var(--neu-concave);
    border: none;
}

.success-box {
    background: var(--bg-color);
    box-shadow: var(--neu-concave);
}

.warning-box {
    background: var(--bg-color);
    box-shadow: var(--neu-concave);
}

/* Neumorphic buttons */
.stButton > button {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--neu-convex) !important;
    transition: var(--transition) !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
}

.stButton > button:hover {
    box-shadow: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    box-shadow: var(--neu-pressed) !important;
    transform: translateY(1px) !important;
}

/* Neumorphic input fields */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div,
.stTimeInput > div > div > input {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--neu-concave) !important;
    padding: 0.75rem !important;
}

/* Neumorphic sliders */
.stSlider > div > div > div > div {
    background: var(--bg-color) !important;
    box-shadow: var(--neu-concave) !important;
    border-radius: var(--border-radius) !important;
}

/* Neumorphic sidebar */
.css-1d391kg {
    background: var(--bg-color) !important;
    border-right: none !important;
    box-shadow: var(--neu-flat) !important;
}

/* Neumorphic tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-color) !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--neu-concave) !important;
    padding: 0.5rem !important;
}

.stTabs [data-baseweb="tab"] {
    background: var(--bg-color) !important;
    color: var(--text-secondary) !important;
    border-radius: calc(var(--border-radius) - 5px) !important;
    border: none !important;
    transition: var(--transition) !important;
}

.stTabs [aria-selected="true"] {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    box-shadow: var(--neu-pressed) !important;
}

/* Neumorphic expanders */
.streamlit-expander {
    background: var(--bg-color) !important;
    border: none !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--neu-convex) !important;
    margin: 1rem 0 !important;
}

.streamlit-expander .streamlit-expanderHeader {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--border-radius) !important;
}

/* Responsive design */
@media (max-width: 768px) {
    .main-banner h1 { font-size: 2rem; }
    .main-banner { padding: 2rem 1rem; }
    .cards-container { flex-direction: column; gap: 1rem; }
    .metric-card { min-width: auto; padding: 1.5rem; }
    .card-icon { width: 3rem; height: 3rem; font-size: 1.5rem; }
    .card-value { font-size: 1.8rem; }
}

/* Custom scrollbar for neumorphic feel */
::-webkit-scrollbar {
    width: 12px;
    background: var(--bg-color);
}

::-webkit-scrollbar-track {
    background: var(--bg-color);
    border-radius: var(--border-radius);
    box-shadow: var(--neu-concave);
}

::-webkit-scrollbar-thumb {
    background: var(--bg-color);
    border-radius: var(--border-radius);
    box-shadow: var(--neu-convex);
}

::-webkit-scrollbar-thumb:hover {
    box-shadow: var(--neu-flat);
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_timezone():
    """Get user's selected timezone from session state"""
    if 'user_timezone' not in st.session_state:
        st.session_state.user_timezone = DEFAULT_TIMEZONE
    return st.session_state.user_timezone

def get_current_time_in_timezone(timezone_str):
    """Get current time in specified timezone"""
    try:
        tz = pytz.timezone(timezone_str)
        utc_now = datetime.now(pytz.UTC)
        local_time = utc_now.astimezone(tz)
        return local_time
    except:
        return datetime.now()

def format_time_with_timezone(dt, timezone_str):
    """Format datetime with timezone info"""
    try:
        tz = pytz.timezone(timezone_str)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
        
        tz_abbrev = dt.strftime('%Z')
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {tz_abbrev}"
    except:
        return dt.strftime('%Y-%m-%d %H:%M:%S')

def create_metric_card(card_type, icon, title, value):
    """Create a neumorphic metric card"""
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-content">
            <div class="card-icon">{icon}</div>
            <div class="card-text">
                <div class="card-title">{title}</div>
                <div class="card-value">{value:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_section_header(icon, title):
    """Create a neumorphic section header"""
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
        if current.hour != 16:
            blocks += 1
        current += timedelta(minutes=30)
    return blocks

def calculate_stock_blocks(anchor_time, target_time):
    """Calculate stock blocks (simple 30-minute intervals)"""
    return max(0, int((target_time - anchor_time).total_seconds() // 1800))

def create_forecast_table(price, slope, anchor, forecast_date, time_slots, is_spx=True, fan_mode=False, two_stage_exits=False):
    """Create forecast table with projections and optional two-stage exits"""
    rows = []
    
    for slot in time_slots:
        hour, minute = map(int, slot.split(":"))
        target_time = datetime.combine(forecast_date, time(hour, minute))
        
        if is_spx:
            blocks = calculate_spx_blocks(anchor, target_time)
        else:
            blocks = calculate_stock_blocks(anchor, target_time)
        
        if two_stage_exits:
            entry_price = round(price + slope * blocks, 2)
            first_exit = round(entry_price + 9, 2)
            fan_exit = round(price - slope * blocks, 2)
            
            rows.append({
                "Time": slot,
                "Entry": entry_price,
                "Exit 1 (+9)": first_exit,
                "Fan Exit": fan_exit,
                "Profit 1": "+9",
                "Fan Profit": round(abs(entry_price - fan_exit), 1)
            })
            
        elif fan_mode:
            entry_price = round(price + slope * blocks, 2)
            exit_price = round(price - slope * blocks, 2)
            rows.append({
                "Time": slot,
                "Entry": entry_price,
                "Exit": exit_price,
                "Spread": round(abs(entry_price - exit_price), 2)
            })
        else:
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
        "0.786": swing_high - (price_range * 0.786),
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

# Time slot definitions
SPX_SLOTS = make_time_slots(time(8, 30))
GENERAL_SLOTS = make_time_slots(time(7, 30))


