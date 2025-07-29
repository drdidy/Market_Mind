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

/* SIDEBAR FIXES FOR TEXT CUTOFF */
.css-1d391kg {
    background: var(--bg-color) !important;
    border-right: none !important;
    box-shadow: var(--neu-flat) !important;
    min-width: 320px !important;
    width: 320px !important;
}

/* Sidebar text visibility */
.css-1d391kg .stSelectbox label,
.css-1d391kg .stTextInput label,
.css-1d391kg .stDateInput label,
.css-1d391kg .stSlider label,
.css-1d391kg .stTextArea label {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* Sidebar selectbox width fixes */
.css-1d391kg .stSelectbox > div {
    width: 100% !important;
}

.css-1d391kg .stSelectbox > div > div {
    width: 100% !important;
    min-width: 280px !important;
}

.css-1d391kg .stSelectbox > div > div > div {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--shadow-dark) !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--neu-concave) !important;
    width: 100% !important;
    min-width: 280px !important;
    padding: 0.75rem !important;
    white-space: nowrap !important;
    overflow: visible !important;
}

/* Sidebar input field width fixes */
.css-1d391kg .stTextInput > div,
.css-1d391kg .stDateInput > div,
.css-1d391kg .stTextArea > div {
    width: 100% !important;
    min-width: 280px !important;
}

.css-1d391kg .stTextInput > div > div,
.css-1d391kg .stDateInput > div > div,
.css-1d391kg .stTextArea > div > div {
    width: 100% !important;
}

.css-1d391kg input {
    background: var(--bg-color) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--shadow-dark) !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--neu-concave) !important;
    width: 100% !important;
    padding: 0.75rem !important;
}

/* Sidebar markdown text */
.css-1d391kg .stMarkdown p,
.css-1d391kg .stMarkdown h1,
.css-1d391kg .stMarkdown h2,
.css-1d391kg .stMarkdown h3,
.css-1d391kg .stMarkdown h4,
.css-1d391kg .stMarkdown h5,
.css-1d391kg .stMarkdown h6 {
    color: var(--text-primary) !important;
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
    .css-1d391kg { min-width: 280px !important; width: 280px !important; }
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
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        box-shadow: var(--neu-convex);
        transition: var(--transition);
        border: none;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <div style="
                width: 4rem;
                height: 4rem;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2rem;
                color: var(--text-primary);
                background: var(--bg-color);
                box-shadow: var(--neu-flat);
            ">{icon}</div>
            <div style="flex: 1;">
                <div style="
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: var(--text-muted);
                    margin-bottom: 0.5rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                ">{title}</div>
                <div style="
                    font-size: 2.2rem;
                    font-weight: 800;
                    color: var(--text-primary);
                    letter-spacing: -0.02em;
                    line-height: 1.1;
                ">{value:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_section_header(icon, title):
    """Create a neumorphic section header"""
    st.markdown(f"""
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 1.5rem 2rem;
        margin: 2rem 0 1rem 0;
        box-shadow: var(--neu-concave);
    ">
        <h2 style="
            margin: 0;
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        ">{icon} {title}</h2>
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

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 PLAYBOOK DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_playbook_navigation():
    """Create the main playbook navigation page"""
    st.markdown("""
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 3rem 2rem;
        text-align: center;
        color: var(--text-primary);
        margin-bottom: 2rem;
        box-shadow: var(--neu-convex);
    ">
        <h1 style="margin: 0; font-size: 3rem; color: var(--text-primary);">📚 Strategy Playbooks</h1>
        <p style="margin: 1rem 0 0 0; font-size: 1.2rem; color: var(--text-secondary);">
            Comprehensive trading strategies for each asset class
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Best Trading Days Cheat Sheet
    st.markdown("## 📅 Best Trading Days Cheat Sheet")
    
    table_data = []
    for ticker, info in BEST_TRADING_DAYS.items():
        table_data.append({
            "Ticker": f"{ICONS[ticker]} **{ticker}**",
            "Best Days": f"**{info['days']}**",
            "Rationale": info['rationale']
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Playbook selection
    st.markdown("## 📋 Select Detailed Playbook")
    
    st.markdown("""
    <div style="text-align: center; margin: 1.5rem 0;">
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            Choose a ticker below to access comprehensive trading strategies and rules
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(3)
    playbook_options = ["SPX"] + list(BEST_TRADING_DAYS.keys())
    
    for i, ticker in enumerate(playbook_options):
        col_idx = i % 3
        with cols[col_idx]:
            st.markdown(f"""
            <div style="margin-bottom: 1rem; cursor: pointer;">
                <div style="
                    background: var(--bg-color);
                    border-radius: var(--border-radius);
                    padding: 1.5rem;
                    text-align: center;
                    box-shadow: var(--neu-convex);
                    transition: var(--transition);
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{ICONS[ticker]}</div>
                    <div style="color: var(--text-primary); font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">{ticker}</div>
                    <div style="color: var(--text-muted); font-size: 0.85rem;">
                        {"Master Playbook" if ticker == "SPX" else "Trading Rules"}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(
                f"Open {ticker} Playbook",
                use_container_width=True,
                type="primary" if ticker == "SPX" else "secondary",
                key=f"nav_playbook_{ticker}",
                help=f"View comprehensive {ticker} strategy"
            ):
                st.session_state.selected_playbook = ticker
                st.rerun()

def display_spx_playbook():
    """Display comprehensive SPX playbook"""
    st.markdown("""
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        color: var(--text-primary);
        margin-bottom: 2rem;
        box-shadow: var(--neu-convex);
    ">
        <h1 style="margin: 0; color: var(--text-primary);">🧭 SPX Master Playbook</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; color: var(--text-secondary);">S&P 500 Index Trading Strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to Playbook Menu",
                 type="secondary",
                 help="Return to playbook selection",
                 use_container_width=False):
        st.session_state.selected_playbook = None
        st.rerun()
    
    # Golden Rules
    st.markdown("## 🔔 Golden Rules")
    st.markdown("""
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: var(--neu-concave);
        color: var(--text-primary);
    ">
    """, unsafe_allow_html=True)
    
    for rule in SPX_GOLDEN_RULES:
        st.markdown(f'<div style="color: var(--text-primary); margin-bottom: 0.5rem;">{rule}</div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Anchor Trading Rules
    st.markdown("## ⚓ Anchor Trading Rules")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📈 RTH Anchor Breaks")
        for rule in SPX_ANCHOR_RULES['rth_breaks']:
            st.markdown(f"• {rule}")
    
    with col2:
        st.markdown("### 🌙 Extended Hours")
        for rule in SPX_ANCHOR_RULES['extended_hours']:
            st.markdown(f"• {rule}")
    
    with col3:
        st.markdown("### 📅 Mon/Wed/Fri Rules")
        for rule in SPX_ANCHOR_RULES['mon_wed_fri']:
            st.markdown(f"• {rule}")
    
    st.markdown("---")
    
    # Fibonacci Bounce Strategy
    st.markdown("## 📈 Fibonacci Bounce Strategy")
    
    st.markdown("""
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--neu-concave);
        color: var(--text-primary);
    ">
    """, unsafe_allow_html=True)
    
    for rule in SPX_ANCHOR_RULES['fibonacci_bounce']:
        st.markdown(f'<div style="color: var(--text-primary); margin-bottom: 0.5rem;">• {rule}</div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Contract Strategies
    st.markdown("## 📏 Contract Line Strategies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Tuesday Contract Play")
        for strategy in CONTRACT_STRATEGIES['tuesday_play']:
            st.markdown(f"• {strategy}")
    
    with col2:
        st.markdown("### 📈 Thursday Contract Play")
        for strategy in CONTRACT_STRATEGIES['thursday_play']:
            st.markdown(f"• {strategy}")
    
    st.markdown("---")
    
    # Time Management
    st.markdown("## ⏰ Time Management & Volume")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🕐 Market Sessions")
        for session in TIME_RULES['market_sessions']:
            st.markdown(f"• {session}")
    
    with col2:
        st.markdown("### 📊 Volume Patterns")
        for pattern in TIME_RULES['volume_patterns']:
            st.markdown(f"• {pattern}")
    
    with col3:
        st.markdown("### 🎯 Multi-Timeframe")
        for rule in TIME_RULES['multi_timeframe']:
            st.markdown(f"• {rule}")

def display_stock_playbook(ticker):
    """Display simplified stock playbook"""
    best_day_info = BEST_TRADING_DAYS.get(ticker, {"days": "N/A", "rationale": "General market patterns"})
    
    st.markdown(f"""
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        color: var(--text-primary);
        margin-bottom: 2rem;
        box-shadow: var(--neu-convex);
    ">
        <h1 style="margin: 0; color: var(--text-primary);">{ICONS[ticker]} {ticker} Playbook</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; color: var(--text-secondary);">Optimized Trading Strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to Playbook Menu",
                 type="secondary",
                 help="Return to playbook selection",
                 use_container_width=False):
        st.session_state.selected_playbook = None
        st.rerun()
    
    # Best Trading Days
    st.markdown("## 📅 Optimal Trading Schedule")
    st.markdown(f"""
    <div style="
        background: var(--bg-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: var(--neu-concave);
    ">
        <h3 style="margin-top: 0; color: var(--text-primary);">Best Days: {best_day_info['days']}</h3>
        <p style="margin-bottom: 0; color: var(--text-secondary);"><strong>Rationale:</strong> {best_day_info['rationale']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Universal Risk Management
    st.markdown("## 🛡️ Risk Management (Universal Rules)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📏 Position Sizing")
        for rule in RISK_RULES['position_sizing']:
            st.markdown(f"• {rule}")
        
        st.markdown("### 🛑 Stop Strategy")
        for rule in RISK_RULES['stop_strategy']:
            st.markdown(f"• {rule}")
    
    with col2:
        st.markdown("### 📊 Market Context")
        for rule in RISK_RULES['market_context']:
            st.markdown(f"• {rule}")
        
        st.markdown("### 🧠 Psychology")
        for rule in RISK_RULES['psychological']:
            st.markdown(f"• {rule}")
    
    # Performance Targets
    st.markdown("### 🎯 Performance Targets")
    for target in RISK_RULES['performance_targets']:
        st.markdown(f"• {target}")

def display_selected_playbook():
    """Route to appropriate playbook display"""
    if st.session_state.selected_playbook == "SPX":
        display_spx_playbook()
    else:
        display_stock_playbook(st.session_state.selected_playbook)

# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ ENHANCED SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

# Get current time in user's timezone
user_tz = get_user_timezone()
current_time = get_current_time_in_timezone(user_tz)
current_time_str = format_time_with_timezone(current_time, user_tz)

st.sidebar.markdown(f"""
<div style="
    text-align: center; 
    padding: 1rem 0; 
    border-bottom: 1px solid var(--shadow-dark); 
    margin-bottom: 1.5rem;
    background: var(--bg-color);
">
    <h2 style="margin: 0; color: var(--text-primary);">⚙️ Strategy Controls</h2>
    <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.9rem;">v{VERSION}</p>
    <div style="
        margin-top: 1rem; 
        padding: 1rem; 
        background: var(--bg-color); 
        border-radius: var(--border-radius); 
        box-shadow: var(--neu-concave);
    ">
        <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.25rem;">Current Time:</div>
        <div style="font-size: 0.9rem; font-weight: 600; color: var(--text-primary);">{current_time_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Add spacing before timezone section
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Timezone selection with better spacing
st.sidebar.markdown("### 🌍 Timezone Settings")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

selected_timezone_display = st.sidebar.selectbox(
    "Select Your Timezone",
    options=list(TIMEZONE_OPTIONS.keys()),
    index=list(TIMEZONE_OPTIONS.values()).index(user_tz) if user_tz in TIMEZONE_OPTIONS.values() else 0,
    help="Choose your local timezone for accurate time display"
)

# Update session state when timezone changes
new_timezone = TIMEZONE_OPTIONS[selected_timezone_display]
if new_timezone != st.session_state.get('user_timezone'):
    st.session_state.user_timezone = new_timezone
    st.rerun()

# Add spacing before theme section
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Theme selection with better spacing
st.session_state.theme = st.sidebar.selectbox(
    "🎨 Theme", 
    ["Dark", "Light"], 
    index=0 if st.session_state.theme == "Dark" else 1,
    help="Choose your preferred theme"
)

# Add spacing before forecast section
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Forecast date selection
st.sidebar.markdown("### 📅 Forecast Settings")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

forecast_date = st.sidebar.date_input(
    "Target Date", 
    value=date.today() + timedelta(days=1),
    help="Select the date for your forecast analysis"
)

weekday = forecast_date.weekday()
day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
current_day = day_labels[weekday]

# Create custom styled info box with proper spacing
st.sidebar.markdown(f"""
<div style="
    background: var(--bg-color);
    border-radius: var(--border-radius);
    padding: 1rem;
    margin: 1rem 0;
    box-shadow: var(--neu-concave);
    text-align: center;
">
    <div style="color: var(--text-primary); font-weight: 600;">📊 {current_day} Trading Session</div>
</div>
""", unsafe_allow_html=True)

# Advanced slope controls
with st.sidebar.expander("📈 Slope Adjustments", expanded=True):
    st.markdown("*Fine-tune your prediction slopes*")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Group slopes logically
    st.markdown("**📊 SPX Slopes**")
    for key in ["SPX_HIGH", "SPX_CLOSE", "SPX_LOW"]:
        st.session_state.slopes[key] = st.slider(
            key.replace("SPX_", "").title(),
            min_value=-1.0,
            max_value=1.0,
            value=st.session_state.slopes[key],
            step=0.0001,
            format="%.4f",
            key=f"slope_{key}"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**🚀 Stock Slopes**")
    stock_keys = [k for k in st.session_state.slopes.keys() if k not in ["SPX_HIGH", "SPX_CLOSE", "SPX_LOW"]]
    for key in stock_keys:
        st.session_state.slopes[key] = st.slider(
            f"{ICONS.get(key, '📊')} {key}",
            min_value=-1.0,
            max_value=1.0,
            value=st.session_state.slopes[key],
            step=0.0001,
            format="%.4f",
            key=f"slope_{key}"
        )

# Preset management
with st.sidebar.expander("💾 Preset Manager"):
    st.markdown("*Save and load your favorite configurations*")
    st.markdown("<br>", unsafe_allow_html=True)
    
    preset_name = st.text_input(
        "Preset Name", 
        placeholder="Enter preset name...",
        help="Give your preset a memorable name"
    )
    
    col1, col2 = st.columns(2)
    
    if col1.button("💾 Save", use_container_width=True):
        if preset_name.strip():
            st.session_state.presets[preset_name.strip()] = deepcopy(st.session_state.slopes)
            st.success(f"✅ Saved '{preset_name}'")
        else:
            st.error("❌ Please enter a preset name")
    
    if st.session_state.presets:
        selected_preset = st.selectbox(
            "Load Preset",
            options=list(st.session_state.presets.keys()),
            help="Select a preset to load"
        )
        
        if col2.button("📂 Load", use_container_width=True):
            st.session_state.slopes.update(st.session_state.presets[selected_preset])
            st.success(f"✅ Loaded '{selected_preset}'")
            st.rerun()

# Share configuration
with st.sidebar.expander("🔗 Share Config"):
    st.markdown("*Share your current slope configuration*")
    st.markdown("<br>", unsafe_allow_html=True)
    
    share_url = f"?s={base64.b64encode(json.dumps(st.session_state.slopes).encode()).decode()}"
    st.text_area(
        "Share URL Suffix",
        value=share_url,
        height=100,
        help="Append this to your URL to share your current slope configuration"
    )
    
    if st.button("📋 Copy to Clipboard", use_container_width=True):
        st.success("✅ URL suffix ready to copy!")
# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 MAIN HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="
    background: var(--bg-color);
    border-radius: var(--border-radius);
    padding: 3rem 2rem;
    text-align: center;
    color: var(--text-primary);
    margin-bottom: 2rem;
    box-shadow: var(--neu-convex);
">
    <h1 style="
        margin: 0; 
        font-size: 2.5rem; 
        font-weight: 800; 
        color: var(--text-primary);
        text-shadow: 1px 1px 2px var(--shadow-light);
    ">{PAGE_ICON} {PAGE_TITLE}</h1>
    <div style="
        font-size: 1.1rem; 
        font-weight: 400; 
        color: var(--text-secondary); 
        margin-top: 0.5rem;
    ">Advanced Market Forecasting • {current_day} Session</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🔄 MAIN TABS NAVIGATION SETUP
# ═══════════════════════════════════════════════════════════════════════════════

# Check if user is viewing a specific playbook
if st.session_state.selected_playbook:
    display_selected_playbook()
else:
    # Create main navigation tabs
    main_tabs = st.tabs([
        "📈 SPX Market Analysis", 
        "🎯 SPX Contract Strategy", 
        "📊 Stock Analysis", 
        "📚 Strategy Playbooks"
    ])

# ═══════════════════════════════════════════════════════════════════════════════
    # 📈 SPX MARKET ANALYSIS TAB - Core Market Direction & Forecasts
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with main_tabs[0]:
        create_section_header("🎯", f"SPX Market Analysis - {current_day}")
        
        # Quick playbook access with neumorphic styling
        st.markdown("""
        <div style="text-align: center; margin: 1.5rem 0;">
            <div style="
                background: var(--bg-color);
                border-radius: var(--border-radius);
                padding: 1rem 2rem;
                box-shadow: var(--neu-convex);
                display: inline-block;
            ">
                <p style="margin: 0; color: var(--text-primary); font-weight: 600; font-size: 1rem;">
                    📚 Access complete SPX trading strategies & rules
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        playbook_col = st.columns([1, 2, 1])[1]
        with playbook_col:
            if st.button("🎯 Open SPX Master Playbook", 
                        use_container_width=True,
                        type="primary",
                        help="Access comprehensive SPX trading strategies and rules"):
                st.session_state.selected_playbook = "SPX"
                st.rerun()
        
        # Strategy overview with neumorphic styling
        st.markdown("""
        <div style="
            background: var(--bg-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--neu-concave);
        ">
            <h4 style="margin-top: 0; color: var(--text-primary);">📋 Market Analysis Overview</h4>
            <p style="color: var(--text-secondary); margin-bottom: 0;">Configure your SPX anchor points to analyze market direction and generate two-stage exit projections. 
            Use this analysis to identify optimal entry and exit levels for your trading strategy.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Rules Reminder
        with st.expander("🔔 Quick SPX Rules Reminder", expanded=False):
            st.markdown("**Key Rules to Remember:**")
            for rule in SPX_GOLDEN_RULES[:3]:
                st.markdown(f"• {rule}")
            st.markdown("*Click 'Open SPX Master Playbook' above for all rules and strategies*")
            # ── SPX ANCHOR INPUTS ────────────────────────────────────────────────────
        create_section_header("⚓", "Anchor Point Configuration")
        
        anchor_col1, anchor_col2, anchor_col3 = st.columns(3)
        
        with anchor_col1:
            st.markdown("#### 📈 **High Anchor**")
            high_price = st.number_input(
                "Price", 
                value=6185.8, 
                min_value=0.0, 
                step=0.1,
                key="spx_high_price",
                help="Previous day's high price"
            )
            high_time = st.time_input(
                "Time", 
                value=time(11, 30),
                key="spx_high_time",
                help="Time when high occurred"
            )
        
        with anchor_col2:
            st.markdown("#### 📊 **Close Anchor**")
            close_price = st.number_input(
                "Price", 
                value=6170.2, 
                min_value=0.0, 
                step=0.1,
                key="spx_close_price",
                help="Previous day's closing price"
            )
            close_time = st.time_input(
                "Time", 
                value=time(15, 0),
                key="spx_close_time",
                help="Market closing time"
            )
        
        with anchor_col3:
            st.markdown("#### 📉 **Low Anchor**")
            low_price = st.number_input(
                "Price", 
                value=6130.4, 
                min_value=0.0, 
                step=0.1,
                key="spx_low_price",
                help="Previous day's low price"
            )
            low_time = st.time_input(
                "Time", 
                value=time(13, 30),
                key="spx_low_time",
                help="Time when low occurred"
            )
            # ── MARKET ANALYSIS GENERATION ──────────────────────────────────────────
        create_section_header("📊", "Market Direction Analysis")
        
        analysis_button_col = st.columns([1, 2, 1])[1]
        with analysis_button_col:
            generate_analysis = st.button(
                "🚀 Generate Market Analysis",
                use_container_width=True,
                type="primary",
                help="Generate SPX market direction analysis with two-stage exits"
            )
        
        if generate_analysis:
            st.session_state.forecasts_generated = True
            
            # ── ANCHOR METRICS CARDS ──────────────────────────────────────────────
            st.markdown('<div class="cards-container">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                create_metric_card("high", "▲", "High Anchor", high_price)
            with col2:
                create_metric_card("close", "■", "Close Anchor", close_price)
            with col3:
                create_metric_card("low", "▼", "Low Anchor", low_price)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Calculate anchor times for previous day
            high_anchor = datetime.combine(forecast_date - timedelta(days=1), high_time)
            close_anchor = datetime.combine(forecast_date - timedelta(days=1), close_time)
            low_anchor = datetime.combine(forecast_date - timedelta(days=1), low_time)
            
            # ── TWO-STAGE EXIT ANALYSIS ──────────────────────────────────────────
            
            # High Anchor with Two-Stage Exits
            create_section_header("📈", "High Anchor: Two-Stage Exit Strategy")
            st.markdown("""
            <div style="
                background: var(--bg-color); 
                border-radius: var(--border-radius); 
                padding: 1rem; 
                margin-bottom: 1rem;
                box-shadow: var(--neu-concave);
            ">
                <strong style="color: var(--text-primary);">🎯 Two-Stage Exit Strategy:</strong><br>
                <span style="color: var(--text-secondary);">Exit 1 at +9 points (50% position), Fan Exit for remaining 50%</span>
            </div>
            """, unsafe_allow_html=True)

            high_forecast = create_forecast_table(
                high_price, 
                st.session_state.slopes["SPX_HIGH"], 
                high_anchor, 
                forecast_date, 
                SPX_SLOTS, 
                is_spx=True, 
                fan_mode=False,
                two_stage_exits=True
            )
            st.dataframe(high_forecast, use_container_width=True, hide_index=True)

            # Close Anchor with Two-Stage Exits
            create_section_header("📊", "Close Anchor: Two-Stage Exit Strategy")
            close_forecast = create_forecast_table(
                close_price, 
                st.session_state.slopes["SPX_CLOSE"], 
                close_anchor, 
                forecast_date, 
                SPX_SLOTS, 
                is_spx=True, 
                fan_mode=False,
                two_stage_exits=True
            )
            st.dataframe(close_forecast, use_container_width=True, hide_index=True)

            # Low Anchor with Two-Stage Exits
            create_section_header("📉", "Low Anchor: Two-Stage Exit Strategy") 
            low_forecast = create_forecast_table(
                low_price, 
                st.session_state.slopes["SPX_LOW"], 
                low_anchor, 
                forecast_date,
                SPX_SLOTS, 
                is_spx=True, 
                fan_mode=False,
                two_stage_exits=True
            )
            st.dataframe(low_forecast, use_container_width=True, hide_index=True)
            # ── PERFORMANCE ANALYSIS ──────────────────────────────────────────────
            create_section_header("📊", "Exit Strategy Performance Analysis")

            # Calculate average profits across all anchors
            all_entries = []
            all_fan_profits = []

            for forecast in [high_forecast, close_forecast, low_forecast]:
                all_entries.extend(forecast['Entry'].tolist())
                all_fan_profits.extend(forecast['Fan Profit'].tolist())

            avg_entry = sum(all_entries) / len(all_entries)
            avg_fan_profit = sum(all_fan_profits) / len(all_fan_profits)
            total_sessions = len(SPX_SLOTS)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("""
                <div style="
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    padding: 1rem; 
                    text-align: center;
                    box-shadow: var(--neu-convex);
                ">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--text-primary);">+9</div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary);">First Exit Points</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">High Probability</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    padding: 1rem; 
                    text-align: center;
                    box-shadow: var(--neu-convex);
                ">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--text-primary);">{avg_fan_profit:.1f}</div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary);">Avg Fan Profit</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Remaining 50%</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    padding: 1rem; 
                    text-align: center;
                    box-shadow: var(--neu-convex);
                ">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--text-primary);">{total_sessions}</div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary);">Time Slots</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Trading Windows</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                blended_profit = (9 + avg_fan_profit) / 2
                st.markdown(f"""
                <div style="
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    padding: 1rem; 
                    text-align: center;
                    box-shadow: var(--neu-convex);
                ">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--text-primary);">{blended_profit:.1f}</div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary);">Blended Avg</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Per Trade</div>
                </div>
                """, unsafe_allow_html=True)

            # Trading rules reminder with neumorphic styling
            st.markdown("""
            <div style="
                background: var(--bg-color); 
                border-radius: var(--border-radius); 
                padding: 1.5rem; 
                margin-top: 1rem;
                box-shadow: var(--neu-concave);
            ">
                <h4 style="margin-top: 0; color: var(--text-primary);">⚠️ Two-Stage Exit Rules</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div style="color: var(--text-secondary);">
                        <strong style="color: var(--text-primary);">🎯 First Exit (50% position):</strong><br>
                        • Target: +9 points<br>
                        • Timing: Exit immediately when hit<br>
                        • Logic: Secure reliable profit
                    </div>
                    <div style="color: var(--text-secondary);">
                        <strong style="color: var(--text-primary);">📊 Fan Exit (50% position):</strong><br>
                        • Target: Fan model projection<br>
                        • Timing: Based on time and price action<br>
                        • Logic: Capture extended move
                    </div>
                </div>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--shadow-dark); color: var(--text-secondary);">
                    <strong style="color: var(--text-primary);">🛑 Risk Management:</strong> Never hold past 3:45 PM • Trail stop after first exit • Full exit if breaks below entry anchor
                </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 SPX CONTRACT STRATEGY TAB - Contract Line + Fibonacci + Lookup
# ═══════════════════════════════════════════════════════════════════════════════
    
    with main_tabs[1]:
        create_section_header("🎯", f"SPX Contract Strategy - {current_day}")
        
        # Strategy overview with neumorphic styling
        st.markdown("""
        <div style="
            background: var(--bg-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--neu-concave);
        ">
            <h4 style="margin-top: 0; color: var(--text-primary);">📋 Contract Strategy Overview</h4>
            <p style="color: var(--text-secondary); margin-bottom: 0;">Configure contract line parameters, analyze Fibonacci bounce patterns, and get real-time price projections. 
            These tools help you identify precise entry points and algorithmic trading opportunities.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ── CONTRACT LINE SETUP ──────────────────────────────────────────────────
        create_section_header("📏", "Contract Line Configuration")
        
        st.markdown("""
        <div style="
            background: var(--bg-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--neu-concave);
        ">
            <h4 style="margin-top: 0; color: var(--text-primary);">⚠️ Two-Point Line Strategy</h4>
            <p style="color: var(--text-secondary); margin-bottom: 0;">Define two key price points to establish your trend line. The system will calculate 
            the optimal slope and project values across all time intervals.</p>
        </div>
        """, unsafe_allow_html=True)
        
        contract_col1, contract_col2 = st.columns(2)
        
        with contract_col1:
            st.markdown("#### 🎯 **Low-1 Point**")
            low1_time = st.time_input(
                "Time", 
                value=time(2, 0), 
                step=300,
                key="contract_low1_time",
                help="First reference point time"
            )
            low1_price = st.number_input(
                "Price", 
                value=10.0, 
                min_value=0.0, 
                step=0.1,
                key="contract_low1_price",
                help="First reference point price"
            )
        
        with contract_col2:
            st.markdown("#### 🎯 **Low-2 Point**")
            low2_time = st.time_input(
                "Time", 
                value=time(3, 30), 
                step=300,
                key="contract_low2_time",
                help="Second reference point time"
            )
            low2_price = st.number_input(
                "Price", 
                value=12.0, 
                min_value=0.0, 
                step=0.1,
                key="contract_low2_price",
                help="Second reference point price"
            )
        
        # ── CONTRACT ANALYSIS GENERATION ────────────────────────────────────────
        create_section_header("📊", "Contract Line Analysis")
        
        contract_button_col = st.columns([1, 2, 1])[1]
        with contract_button_col:
            generate_contract = st.button(
                "🚀 Generate Contract Analysis",
                use_container_width=True,
                type="primary",
                help="Generate contract line projections and analysis"
            )
        if generate_contract:
            # Calculate contract line parameters
            anchor_datetime = datetime.combine(forecast_date, low1_time)
            time_diff_blocks = calculate_spx_blocks(
                anchor_datetime, 
                datetime.combine(forecast_date, low2_time)
            )
            
            # Prevent division by zero
            if time_diff_blocks == 0:
                contract_slope = 0
                st.warning("⚠️ Low-1 and Low-2 times are too close. Adjust the time difference.")
            else:
                contract_slope = (low2_price - low1_price) / time_diff_blocks
            
            # Store contract parameters in session state
            st.session_state.contract_anchor = anchor_datetime
            st.session_state.contract_slope = contract_slope
            st.session_state.contract_price = low1_price
            
            # Display contract line metrics with neumorphic styling
            st.markdown(f"""
            <div style="
                background: var(--bg-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: var(--neu-concave);
            ">
                <h4 style="margin-top: 0; color: var(--text-primary);">📊 Contract Line Metrics</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div style="color: var(--text-secondary);">
                        <strong style="color: var(--text-primary);">📍 Anchor Point:</strong><br>
                        {low1_time.strftime('%H:%M')} @ ${low1_price:.2f}
                    </div>
                    <div style="color: var(--text-secondary);">
                        <strong style="color: var(--text-primary);">📈 Slope Rate:</strong><br>
                        {contract_slope:.4f} per block
                    </div>
                    <div style="color: var(--text-secondary);">
                        <strong style="color: var(--text-primary);">📏 Time Span:</strong><br>
                        {time_diff_blocks} blocks
                    </div>
                    <div style="color: var(--text-secondary);">
                        <strong style="color: var(--text-primary);">💰 Price Delta:</strong><br>
                        ${abs(low2_price - low1_price):.2f}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Generate contract line forecast table
            contract_forecast = create_forecast_table(
                low1_price,
                contract_slope,
                anchor_datetime,
                forecast_date,
                GENERAL_SLOTS,
                is_spx=True,
                fan_mode=False
            )
            st.dataframe(contract_forecast, use_container_width=True, hide_index=True)

        # ── FIBONACCI BOUNCE ANALYZER ────────────────────────────────────────────────
        create_section_header("📈", "Fibonacci Bounce Analysis")
        
        st.markdown("""
        <div style="
            background: var(--bg-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--neu-concave);
        ">
            <h4 style="margin-top: 0; color: var(--text-primary);">🎯 Algorithmic Entry Detection</h4>
            <p style="color: var(--text-secondary); margin-bottom: 0;">When SPX bounces off a line, the contract follows with a retracement to 0.786 Fibonacci level. 
            This is where algorithms typically enter for high-probability runs. Use this tool to identify optimal entry points.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Fibonacci input section
        fib_col1, fib_col2, fib_col3 = st.columns(3)
        
        with fib_col1:
            st.markdown("#### 📉 **Bounce Low**")
            bounce_low = st.number_input(
                "Contract Low Price",
                value=0.0,
                min_value=0.0,
                step=0.01,
                key="fib_bounce_low",
                help="Lowest price of the contract bounce"
            )
        
        with fib_col2:
            st.markdown("#### 📈 **Bounce High**")
            bounce_high = st.number_input(
                "Contract High Price", 
                value=0.0,
                min_value=0.0,
                step=0.01,
                key="fib_bounce_high",
                help="Highest price of the contract bounce"
            )
        
        with fib_col3:
            st.markdown("#### ⏰ **Next Hour Candle**")
            st.markdown("""
            <div style="
                background: var(--bg-color); 
                border-radius: var(--border-radius); 
                padding: 1rem; 
                margin-top: 1.8rem;
                box-shadow: var(--neu-concave);
            ">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚠️</div>
                    <div style="font-size: 0.9rem; font-weight: 600; color: var(--text-primary);">Watch Next Hour</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">0.786 entry typically occurs</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # Generate Fibonacci analysis
        if bounce_low > 0 and bounce_high > bounce_low:
            st.markdown("### 🧮 Fibonacci Retracement Levels")
            
            # Create and display fibonacci table
            fib_table = create_fibonacci_table(bounce_low, bounce_high)
            st.dataframe(fib_table, use_container_width=True, hide_index=True)
            
            # Highlight the key 0.786 level with neumorphic styling
            fib_levels = calculate_fibonacci_levels(bounce_low, bounce_high)
            key_entry = fib_levels["0.786"]
            
            st.markdown(f"""
            <div style="
                background: var(--bg-color);
                border-radius: var(--border-radius);
                padding: 2rem;
                margin: 1.5rem 0;
                text-align: center;
                box-shadow: var(--neu-convex);
            ">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎯</div>
                <h3 style="margin: 0; color: var(--text-primary); font-size: 1.8rem;">Algorithmic Entry Zone</h3>
                <div style="font-size: 3rem; font-weight: 800; color: var(--text-primary); margin: 1rem 0;">
                    ${key_entry:.2f}
                </div>
                <div style="font-size: 1.1rem; color: var(--text-secondary);">
                    <strong>0.786 Fibonacci Level</strong><br>
                    <span style="font-size: 0.9rem;">Expected in next hour candle</span>
                </div>
                <div style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-muted);">
                    Range: ${bounce_high:.2f} → ${bounce_low:.2f} (${bounce_high - bounce_low:.2f} spread)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Trading alerts with neumorphic styling
            current_range_percent = ((bounce_high - bounce_low) / bounce_low) * 100
            
            st.markdown("### ⚠️ Trading Alerts")
            
            alert_col1, alert_col2 = st.columns(2)
            
            with alert_col1:
                st.markdown(f"""
                <div style="
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    padding: 1rem;
                    box-shadow: var(--neu-concave);
                ">
                    <strong style="color: var(--text-primary);">📊 Range Analysis:</strong><br>
                    <span style="color: var(--text-secondary);">Swing Range: {current_range_percent:.1f}%<br>
                    {"Strong signal" if current_range_percent > 2 else "Weak signal" if current_range_percent < 1 else "Moderate signal"}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with alert_col2:
                st.markdown(f"""
                <div style="
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    padding: 1rem;
                    box-shadow: var(--neu-concave);
                ">
                    <strong style="color: var(--text-primary);">⏰ Timing:</strong><br>
                    <span style="color: var(--text-secondary);">Watch for: Next hour candle<br>
                    Entry: Around ${key_entry:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
        
        elif bounce_low > 0 or bounce_high > 0:
            st.warning("⚠️ Please enter both swing low and swing high values, with high > low")
        else:
            st.info("💡 Enter swing low and swing high prices to calculate Fibonacci retracement levels")
        
        # ── REAL-TIME CONTRACT LOOKUP ───────────────────────────────────────────────
        create_section_header("🔍", "Real-Time Contract Lookup")
        
        st.markdown("""
        <div style="
            background: var(--bg-color);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--neu-concave);
        ">
            <h4 style="margin-top: 0; color: var(--text-primary);">⚡ Instant Contract Projections</h4>
            <p style="color: var(--text-secondary); margin-bottom: 0;">Enter any time to get instant contract price projections based on your contract line. 
            This tool works with your configured contract parameters for precise entry timing.</p>
        </div>
        """, unsafe_allow_html=True)
        
        lookup_col1, lookup_col2 = st.columns([1, 2])
        
        with lookup_col1:
            lookup_time = st.time_input(
                "🕐 Lookup Time",
                value=time(9, 25),
                step=300,
                key="contract_lookup_time",
                help="Enter any time to get projected contract price"
            )
        
        with lookup_col2:
            if st.session_state.contract_anchor:
                target_datetime = datetime.combine(forecast_date, lookup_time)
                blocks = calculate_spx_blocks(st.session_state.contract_anchor, target_datetime)
                projected_value = st.session_state.contract_price + (st.session_state.contract_slope * blocks)
                
                st.markdown(f"""
                <div style="
                    padding: 1rem; 
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    margin-top: 1.8rem;
                    box-shadow: var(--neu-concave);
                ">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem;">🎯</div>
                        <div>
                            <div style="font-size: 0.9rem; color: var(--text-muted);">Contract Price @ {lookup_time.strftime('%H:%M')}</div>
                            <div style="font-size: 2rem; font-weight: 800; color: var(--text-primary);">${projected_value:.2f}</div>
                            <div style="font-size: 0.85rem; color: var(--text-secondary);">{blocks} blocks • {projected_value - st.session_state.contract_price:+.2f} change</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="
                    padding: 1rem; 
                    background: var(--bg-color); 
                    border-radius: var(--border-radius); 
                    margin-top: 1.8rem;
                    box-shadow: var(--neu-concave);
                ">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem;">⏳</div>
                        <div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-primary);">Waiting for Contract Configuration</div>
                            <div style="font-size: 0.9rem; color: var(--text-secondary);">Set contract line points and generate analysis to activate lookup</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
    # 📊 STOCK ANALYSIS TAB - Individual Stock Forecasts
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with main_tabs[2]:
        create_section_header("📊", f"Stock Analysis Center - {current_day}")
        
        # Sub-tabs for different stocks
        stock_tab_labels = [f"{ICONS[ticker]} {ticker}" for ticker in list(ICONS.keys())[1:]]
        stock_tabs = st.tabs(stock_tab_labels)
        
        # Enhanced Stock Tabs with playbook integration
        def create_enhanced_stock_tab(tab_index, ticker):
            """Create stock tab with playbook integration"""
            with stock_tabs[tab_index]:
                create_section_header(ICONS[ticker], f"{ticker} Analysis Center")
                
                # Show best trading days with neumorphic styling
                if ticker in BEST_TRADING_DAYS:
                    best_info = BEST_TRADING_DAYS[ticker]
                    st.markdown(f"""
                    <div style="
                        background: var(--bg-color);
                        border-radius: var(--border-radius);
                        padding: 1.2rem;
                        margin-bottom: 1.5rem;
                        box-shadow: var(--neu-convex);
                    ">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="
                                background: var(--bg-color);
                                border-radius: 50%;
                                width: 3rem;
                                height: 3rem;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 1.5rem;
                                box-shadow: var(--neu-flat);
                            ">📅</div>
                            <div>
                                <div style="color: var(--text-primary); font-weight: 700; font-size: 1.1rem;">
                                    Best Trading Days: {best_info['days']}
                                </div>
                                <div style="color: var(--text-secondary); margin-top: 0.25rem;">
                                    {best_info['rationale']}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced playbook access with neumorphic styling
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="
                        background: var(--bg-color);
                        border-radius: var(--border-radius);
                        padding: 0.6rem 1.5rem;
                        display: inline-block;
                        box-shadow: var(--neu-convex);
                    ">
                        <p style="margin: 0; color: var(--text-primary); font-weight: 600; font-size: 0.9rem;">
                            📚 Access detailed trading rules & risk management
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                playbook_col = st.columns([1, 2, 1])[1]
                with playbook_col:
                    if st.button(f"🎯 Open {ticker} Playbook", 
                                key=f"playbook_btn_{ticker}",
                                use_container_width=True,
                                type="secondary",
                                help=f"Access {ticker} specific trading guidelines"):
                        st.session_state.selected_playbook = ticker
                        st.rerun()
                
                # Enhanced strategy overview with neumorphic styling
                st.markdown(f"""
                <div style="
                    background: var(--bg-color);
                    border-radius: var(--border-radius);
                    padding: 1.5rem;
                    margin: 1rem 0;
                    box-shadow: var(--neu-concave);
                ">
                    <h4 style="margin-top: 0; color: var(--text-primary);">{ICONS[ticker]} {ticker} Strategy Overview</h4>
                    <p style="color: var(--text-secondary); margin-bottom: 0;">Configure anchor points from the previous trading day to project optimal entry and exit positions. 
                    Use the optimal trading days shown above for best results.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Input section
                create_section_header("⚓", "Previous Day Anchor Points")
                
                input_col1, input_col2 = st.columns(2)
                
                with input_col1:
                    st.markdown("#### 📉 **Low Anchor**")
                    low_price = st.number_input(
                        "Previous Day Low",
                        value=0.0,
                        min_value=0.0,
                        step=0.01,
                        key=f"{ticker}_low_price",
                        help=f"Enter {ticker}'s previous day low price"
                    )
                    low_time = st.time_input(
                        "Low Time",
                        value=time(7, 30),
                        key=f"{ticker}_low_time",
                        help="Time when the low occurred"
                    )
                
                with input_col2:
                    st.markdown("#### 📈 **High Anchor**")
                    high_price = st.number_input(
                        "Previous Day High",
                        value=0.0,
                        min_value=0.0,
                        step=0.01,
                        key=f"{ticker}_high_price",
                        help=f"Enter {ticker}'s previous day high price"
                    )
                    high_time = st.time_input(
                        "High Time",
                        value=time(7, 30),
                        key=f"{ticker}_high_time",
                        help="Time when the high occurred"
                    )
                    # ═══════════════════════════════════════════════════════════════════════════════
    # 📊 STOCK ANALYSIS TAB - Individual Stock Forecasts
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with main_tabs[2]:
        create_section_header("📊", f"Stock Analysis Center - {current_day}")
        
        # Sub-tabs for different stocks
        stock_tab_labels = [f"{ICONS[ticker]} {ticker}" for ticker in list(ICONS.keys())[1:]]
        stock_tabs = st.tabs(stock_tab_labels)
        
        # Enhanced Stock Tabs with playbook integration
        def create_enhanced_stock_tab(tab_index, ticker):
            """Create stock tab with playbook integration"""
            with stock_tabs[tab_index]:
                create_section_header(ICONS[ticker], f"{ticker} Analysis Center")
                
                # Show best trading days with neumorphic styling
                if ticker in BEST_TRADING_DAYS:
                    best_info = BEST_TRADING_DAYS[ticker]
                    st.markdown(f"""
                    <div style="
                        background: var(--bg-color);
                        border-radius: var(--border-radius);
                        padding: 1.2rem;
                        margin-bottom: 1.5rem;
                        box-shadow: var(--neu-convex);
                    ">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="
                                background: var(--bg-color);
                                border-radius: 50%;
                                width: 3rem;
                                height: 3rem;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 1.5rem;
                                box-shadow: var(--neu-flat);
                            ">📅</div>
                            <div>
                                <div style="color: var(--text-primary); font-weight: 700; font-size: 1.1rem;">
                                    Best Trading Days: {best_info['days']}
                                </div>
                                <div style="color: var(--text-secondary); margin-top: 0.25rem;">
                                    {best_info['rationale']}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced playbook access with neumorphic styling
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="
                        background: var(--bg-color);
                        border-radius: var(--border-radius);
                        padding: 0.6rem 1.5rem;
                        display: inline-block;
                        box-shadow: var(--neu-convex);
                    ">
                        <p style="margin: 0; color: var(--text-primary); font-weight: 600; font-size: 0.9rem;">
                            📚 Access detailed trading rules & risk management
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                playbook_col = st.columns([1, 2, 1])[1]
                with playbook_col:
                    if st.button(f"🎯 Open {ticker} Playbook", 
                                key=f"playbook_btn_{ticker}",
                                use_container_width=True,
                                type="secondary",
                                help=f"Access {ticker} specific trading guidelines"):
                        st.session_state.selected_playbook = ticker
                        st.rerun()
                
                # Enhanced strategy overview with neumorphic styling
                st.markdown(f"""
                <div style="
                    background: var(--bg-color);
                    border-radius: var(--border-radius);
                    padding: 1.5rem;
                    margin: 1rem 0;
                    box-shadow: var(--neu-concave);
                ">
                    <h4 style="margin-top: 0; color: var(--text-primary);">{ICONS[ticker]} {ticker} Strategy Overview</h4>
                    <p style="color: var(--text-secondary); margin-bottom: 0;">Configure anchor points from the previous trading day to project optimal entry and exit positions. 
                    Use the optimal trading days shown above for best results.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Input section
                create_section_header("⚓", "Previous Day Anchor Points")
                
                input_col1, input_col2 = st.columns(2)
                
                with input_col1:
                    st.markdown("#### 📉 **Low Anchor**")
                    low_price = st.number_input(
                        "Previous Day Low",
                        value=0.0,
                        min_value=0.0,
                        step=0.01,
                        key=f"{ticker}_low_price",
                        help=f"Enter {ticker}'s previous day low price"
                    )
                    low_time = st.time_input(
                        "Low Time",
                        value=time(7, 30),
                        key=f"{ticker}_low_time",
                        help="Time when the low occurred"
                    )
                
                with input_col2:
                    st.markdown("#### 📈 **High Anchor**")
                    high_price = st.number_input(
                        "Previous Day High",
                        value=0.0,
                        min_value=0.0,
                        step=0.01,
                        key=f"{ticker}_high_price",
                        help=f"Enter {ticker}'s previous day high price"
                    )
                    high_time = st.time_input(
                        "High Time",
                        value=time(7, 30),
                        key=f"{ticker}_high_time",
                        help="Time when the high occurred"
                    )

# ═══════════════════════════════════════════════════════════════════════════════
    # 📚 STRATEGY PLAYBOOKS TAB - Main Navigation
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with main_tabs[3]:
        create_playbook_navigation()

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 FOOTER & FINAL ELEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

# Add spacing before footer
st.markdown("<br><br>", unsafe_allow_html=True)

# Enhanced footer with neumorphic styling
user_tz = get_user_timezone()
current_time = get_current_time_in_timezone(user_tz)
generation_time = format_time_with_timezone(current_time, user_tz)

st.markdown(f"""
<div style="
    background: var(--bg-color);
    border-radius: var(--border-radius);
    padding: 2rem;
    margin-top: 3rem;
    text-align: center;
    box-shadow: var(--neu-convex);
">
    <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; flex-wrap: wrap;">
        <div>
            <h4 style="margin: 0; color: var(--text-primary);">🧠 Dr Didy MarketMind</h4>
            <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">
                Advanced Market Forecasting System v{VERSION}
            </p>
        </div>
        <div style="height: 40px; width: 1px; background: var(--shadow-dark);"></div>
        <div>
            <p style="margin: 0; font-size: 0.9rem; color: var(--text-secondary);">
                🕐 Generated: {generation_time}
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: var(--text-muted);">
                Target: {forecast_date.strftime('%A, %B %d, %Y')}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Enhanced disclaimer with neumorphic styling
st.markdown("""
<div style="
    background: var(--bg-color);
    border-radius: var(--border-radius);
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
    box-shadow: var(--neu-concave);
">
    <p style="margin: 0; font-size: 0.85rem; color: var(--text-secondary);">
        ⚠️ <strong style="color: var(--text-primary);">Disclaimer:</strong> This tool is for educational and analysis purposes only. 
        Always conduct your own research and consult with financial professionals before making investment decisions.
    </p>
</div>
""", unsafe_allow_html=True)

# Performance metrics with neumorphic styling
if st.session_state.forecasts_generated:
    with st.expander("📊 Session Performance Metrics", expanded=False):
        stock_tickers = list(ICONS.keys())[1:]
        active_slopes_count = len([s for s in st.session_state.slopes.values() if s != 0])
        
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div style="
                padding: 1rem; 
                background: var(--bg-color); 
                border-radius: var(--border-radius);
                box-shadow: var(--neu-convex);
            ">
                <strong style="color: var(--text-primary);">🎯 Forecasts Generated:</strong><br>
                <span style="color: var(--text-secondary);">SPX + {len(stock_tickers)} Stocks</span>
            </div>
            <div style="
                padding: 1rem; 
                background: var(--bg-color); 
                border-radius: var(--border-radius);
                box-shadow: var(--neu-convex);
            ">
                <strong style="color: var(--text-primary);">📈 Active Slopes:</strong><br>
                <span style="color: var(--text-secondary);">{active_slopes_count} configured</span>
            </div>
            <div style="
                padding: 1rem; 
                background: var(--bg-color); 
                border-radius: var(--border-radius);
                box-shadow: var(--neu-convex);
            ">
                <strong style="color: var(--text-primary);">💾 Saved Presets:</strong><br>
                <span style="color: var(--text-secondary);">{len(st.session_state.presets)} available</span>
            </div>
            <div style="
                padding: 1rem; 
                background: var(--bg-color); 
                border-radius: var(--border-radius);
                box-shadow: var(--neu-convex);
            ">
                <strong style="color: var(--text-primary);">⚡ Contract Line:</strong><br>
                <span style="color: var(--text-secondary);">{'Active' if st.session_state.contract_anchor else 'Inactive'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# System Status & Health Check with neumorphic styling
with st.expander("🔧 System Status", expanded=False):
    total_slopes = len(st.session_state.slopes)
    configured_slopes = sum(1 for slope in st.session_state.slopes.values() if slope != 0)
    slope_health = (configured_slopes / total_slopes) * 100
    
    contract_status = "✅ Active" if st.session_state.contract_anchor else "⏳ Inactive"
    playbook_status = "✅ Available" if len(BEST_TRADING_DAYS) > 0 else "❌ Missing"
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
        <div style="
            padding: 1rem; 
            background: var(--bg-color); 
            border-radius: var(--border-radius);
            box-shadow: var(--neu-convex);
        ">
            <strong style="color: var(--text-primary);">📊 Slope Configuration:</strong><br>
            <span style="color: var(--text-secondary);">{configured_slopes}/{total_slopes} configured ({slope_health:.0f}%)</span>
        </div>
        <div style="
            padding: 1rem; 
            background: var(--bg-color); 
            border-radius: var(--border-radius);
            box-shadow: var(--neu-convex);
        ">
            <strong style="color: var(--text-primary);">📏 Contract Line:</strong><br>
            <span style="color: var(--text-secondary);">{contract_status}</span>
        </div>
        <div style="
            padding: 1rem; 
            background: var(--bg-color); 
            border-radius: var(--border-radius);
            box-shadow: var(--neu-convex);
        ">
            <strong style="color: var(--text-primary);">📚 Playbooks:</strong><br>
            <span style="color: var(--text-secondary);">{playbook_status} ({len(BEST_TRADING_DAYS)} stocks)</span>
        </div>
        <div style="
            padding: 1rem; 
            background: var(--bg-color); 
            border-radius: var(--border-radius);
            box-shadow: var(--neu-convex);
        ">
            <strong style="color: var(--text-primary);">🎨 Theme:</strong><br>
            <span style="color: var(--text-secondary);">{st.session_state.theme} Mode</span>
        </div>
        <div style="
            padding: 1rem; 
            background: var(--bg-color); 
            border-radius: var(--border-radius);
            box-shadow: var(--neu-convex);
        ">
            <strong style="color: var(--text-primary);">🌍 Timezone:</strong><br>
            <span style="color: var(--text-secondary);">{user_tz.split('/')[-1]} Time</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Final spacing
st.markdown("<br>", unsafe_allow_html=True)
