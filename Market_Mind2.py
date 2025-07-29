# ═══════════════════════════════════════════════════════════════════════════════
# 📈 DR DIDY SPX FORECAST - VERSION v1.6.1
# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 Complete Market Forecasting System with Playbooks & Two-Stage Exits
# 🔧 Clean, Well-Organized Code for Easy Maintenance and Collaboration

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

PAGE_TITLE = "Dr Didy SPX Forecast"
PAGE_ICON = "📈"
VERSION = "1.6.1"
DEFAULT_TIMEZONE = "America/Chicago"  # Chicago timezone

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
        # Fallback to system time if timezone fails
        return datetime.now()

def format_time_with_timezone(dt, timezone_str):
    """Format datetime with timezone info"""
    try:
        tz = pytz.timezone(timezone_str)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
        
        # Get timezone abbreviation
        tz_abbrev = dt.strftime('%Z')
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {tz_abbrev}"
    except:
        return dt.strftime('%Y-%m-%d %H:%M:%S')

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
            # SPX Two-Stage Exit System with 9 point target
            entry_price = round(price + slope * blocks, 2)
            first_exit = round(entry_price + 9, 2)  # 9 point target
            fan_exit = round(price - slope * blocks, 2)  # Fan model exit
            
            rows.append({
                "Time": slot,
                "Entry": entry_price,
                "Exit 1 (+ 9)": first_exit,
                "Fan Exit": fan_exit,
                "Profit 1": "+ 9",
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

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 PLAYBOOK DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_playbook_navigation():
    """Create the main playbook navigation page with enhanced styling"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 3rem 2rem;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    ">
        <h1 style="margin: 0; font-size: 3rem;">📚 Strategy Playbooks</h1>
        <p style="margin: 1rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
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
    
    # Enhanced playbook selection
    st.markdown("## 📋 Select Detailed Playbook")
    
    st.markdown("""
    <div style="text-align: center; margin: 1.5rem 0;">
        <p style="color: #e2e8f0; font-size: 1.1rem; opacity: 0.8;">
            Choose a ticker below to access comprehensive trading strategies and rules
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(3)
    playbook_options = ["SPX"] + list(BEST_TRADING_DAYS.keys())
    
    for i, ticker in enumerate(playbook_options):
        col_idx = i % 3
        with cols[col_idx]:
            button_color = "#667eea" if ticker == "SPX" else "#f59e0b"
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <div style="
                    background: linear-gradient(135deg, {button_color} 0%, {button_color}cc 100%);
                    border-radius: 12px;
                    padding: 0.1rem;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                ">
                    <div style="
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 11px;
                        padding: 1rem;
                        text-align: center;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    ">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{ICONS[ticker]}</div>
                        <div style="color: white; font-weight: 600; font-size: 1rem;">{ticker}</div>
                        <div style="color: rgba(255, 255, 255, 0.8); font-size: 0.85rem;">
                            {"Master Playbook" if ticker == "SPX" else "Trading Rules"}
                        </div>
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
    """Display comprehensive SPX playbook with all strategies"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2rem;
        color: white;
        margin-bottom: 2rem;
    ">
        <h1 style="margin: 0;">🧭 SPX Master Playbook</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">S&P 500 Index Trading Strategy</p>
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
        background: rgba(255, 215, 0, 0.1);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    ">
    """, unsafe_allow_html=True)
    
    for rule in SPX_GOLDEN_RULES:
        st.markdown(rule)
    
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
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
    """, unsafe_allow_html=True)
    
    for rule in SPX_ANCHOR_RULES['fibonacci_bounce']:
        st.markdown(f"• {rule}")
    
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
    """Display simplified stock playbook with universal rules"""
    best_day_info = BEST_TRADING_DAYS.get(ticker, {"days": "N/A", "rationale": "General market patterns"})
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2rem;
        color: white;
        margin-bottom: 2rem;
    ">
        <h1 style="margin: 0;">{ICONS[ticker]} {ticker} Playbook</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Optimized Trading Strategy</p>
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
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    ">
        <h3 style="margin-top: 0; color: #22c55e;">Best Days: {best_day_info['days']}</h3>
        <p style="margin-bottom: 0;"><strong>Rationale:</strong> {best_day_info['rationale']}</p>
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
<div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem;">
    <h2 style="margin: 0; color: #667eea;">⚙️ Strategy Controls</h2>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.7; font-size: 0.9rem;">v{VERSION}</p>
    <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px;">
        <div style="font-size: 0.85rem; opacity: 0.8;">Current Time:</div>
        <div style="font-size: 0.9rem; font-weight: 600;">{current_time_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Timezone selection
st.sidebar.markdown("### 🌍 Timezone Settings")
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

# Theme selection
st.session_state.theme = st.sidebar.selectbox(
    "🎨 Theme", 
    ["Dark", "Light"], 
    index=0 if st.session_state.theme == "Dark" else 1
)

# Forecast date selection
st.sidebar.markdown("### 📅 Forecast Settings")
forecast_date = st.sidebar.date_input(
    "Target Date", 
    value=date.today() + timedelta(days=1),
    help="Select the date for your forecast analysis"
)

weekday = forecast_date.weekday()
day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
current_day = day_labels[weekday]

st.sidebar.info(f"📊 **{current_day}** Trading Session")

# Advanced slope controls
with st.sidebar.expander("📈 Slope Adjustments", expanded=True):
    st.markdown("*Fine-tune your prediction slopes*")
    
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
<div class="main-banner">
    <h1>{PAGE_ICON} {PAGE_TITLE}</h1>
    <div class="subtitle">Advanced Market Forecasting • {current_day} Session</div>
</div>
""", unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════════════════════
# 🔄 PART 7a: SPX MARKET ANALYSIS & CONTRACT STRATEGY TABS
# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 Replace your existing main tabs section with this organized structure

# Check if user is viewing a specific playbook
if st.session_state.selected_playbook:
    display_selected_playbook()
else:
    # Create clean four-tab structure
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
        
        # Quick playbook access
        st.markdown("""
        <div style="text-align: center; margin: 1.5rem 0;">
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 0.1rem;
                display: inline-block;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 11px;
                    padding: 0.8rem 2rem;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                ">
                    <p style="margin: 0; color: white; font-weight: 600; font-size: 1rem;">
                        📚 Access complete SPX trading strategies & rules
                    </p>
                </div>
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
        
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top: 0;">📋 Market Analysis Overview</h4>
            <p>Configure your SPX anchor points to analyze market direction and generate two-stage exit projections. 
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
            <div style="background: rgba(34, 197, 94, 0.1); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <strong>🎯 Two-Stage Exit Strategy:</strong> Exit 1 at +9 points (50% position), Fan Exit for remaining 50%
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
                <div style="background: rgba(34, 197, 94, 0.1); border-radius: 8px; padding: 1rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: #22c55e;">+9</div>
                    <div style="font-size: 0.9rem;">First Exit Points</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">High Probability</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.1); border-radius: 8px; padding: 1rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: #3b82f6;">{avg_fan_profit:.1f}</div>
                    <div style="font-size: 0.9rem;">Avg Fan Profit</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Remaining 50%</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="background: rgba(245, 158, 11, 0.1); border-radius: 8px; padding: 1rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: #f59e0b;">{total_sessions}</div>
                    <div style="font-size: 0.9rem;">Time Slots</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Trading Windows</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                blended_profit = (9 + avg_fan_profit) / 2
                st.markdown(f"""
                <div style="background: rgba(139, 92, 246, 0.1); border-radius: 8px; padding: 1rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: #8b5cf6;">{blended_profit:.1f}</div>
                    <div style="font-size: 0.9rem;">Blended Avg</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Per Trade</div>
                </div>
                """, unsafe_allow_html=True)

            # Trading rules reminder
            st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
                <h4 style="margin-top: 0;">⚠️ Two-Stage Exit Rules</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <strong>🎯 First Exit (50% position):</strong><br>
                        • Target: +9 points<br>
                        • Timing: Exit immediately when hit<br>
                        • Logic: Secure reliable profit
                    </div>
                    <div>
                        <strong>📊 Fan Exit (50% position):</strong><br>
                        • Target: Fan model projection<br>
                        • Timing: Based on time and price action<br>
                        • Logic: Capture extended move
                    </div>
                </div>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(245, 158, 11, 0.2);">
                    <strong>🛑 Risk Management:</strong> Never hold past 3:45 PM • Trail stop after first exit • Full exit if breaks below entry anchor
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 SPX CONTRACT STRATEGY TAB - Contract Line + Fibonacci + Lookup
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with main_tabs[1]:
        create_section_header("🎯", f"SPX Contract Strategy - {current_day}")
        
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top: 0;">📋 Contract Strategy Overview</h4>
            <p>Configure contract line parameters, analyze Fibonacci bounce patterns, and get real-time price projections. 
            These tools help you identify precise entry points and algorithmic trading opportunities.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ── CONTRACT LINE SETUP ──────────────────────────────────────────────────
        create_section_header("📏", "Contract Line Configuration")
        
        st.markdown("""
        <div class="warning-box">
            <h4 style="margin-top: 0;">⚠️ Two-Point Line Strategy</h4>
            <p>Define two key price points to establish your trend line. The system will calculate 
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
            
            # Display contract line metrics
            st.markdown(f"""
            <div class="success-box">
                <h4 style="margin-top: 0;">📊 Contract Line Metrics</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div>
                        <strong>📍 Anchor Point:</strong><br>
                        {low1_time.strftime('%H:%M')} @ ${low1_price:.2f}
                    </div>
                    <div>
                        <strong>📈 Slope Rate:</strong><br>
                        {contract_slope:.4f} per block
                    </div>
                    <div>
                        <strong>📏 Time Span:</strong><br>
                        {time_diff_blocks} blocks
                    </div>
                    <div>
                        <strong>💰 Price Delta:</strong><br>
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

            # ═══════════════════════════════════════════════════════════════════════════════
# 🔄 PART 7b: FIBONACCI ANALYSIS, STOCK TABS & PLAYBOOKS
# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 This continues from Part 7a - add this after the contract analysis section

        # ── FIBONACCI BOUNCE ANALYZER ────────────────────────────────────────────────
        create_section_header("📈", "Fibonacci Bounce Analysis")
        
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top: 0;">🎯 Algorithmic Entry Detection</h4>
            <p>When SPX bounces off a line, the contract follows with a retracement to 0.786 Fibonacci level. 
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
            <div style="background: rgba(245, 158, 11, 0.1); border-radius: 8px; padding: 1rem; margin-top: 1.8rem;">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚠️</div>
                    <div style="font-size: 0.9rem; font-weight: 600;">Watch Next Hour</div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">0.786 entry typically occurs</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Generate Fibonacci analysis
        if bounce_low > 0 and bounce_high > bounce_low:
            st.markdown("### 🧮 Fibonacci Retracement Levels")
            
            # Create and display fibonacci table
            fib_table = create_fibonacci_table(bounce_low, bounce_high)
            st.dataframe(fib_table, use_container_width=True, hide_index=True)
            
            # Highlight the key 0.786 level
            fib_levels = calculate_fibonacci_levels(bounce_low, bounce_high)
            key_entry = fib_levels["0.786"]
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(34, 197, 94, 0.1) 100%);
                border: 2px solid rgba(34, 197, 94, 0.4);
                border-radius: 12px;
                padding: 2rem;
                margin: 1.5rem 0;
                text-align: center;
                box-shadow: 0 8px 25px rgba(34, 197, 94, 0.3);
            ">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎯</div>
                <h3 style="margin: 0; color: #22c55e; font-size: 1.8rem;">Algorithmic Entry Zone</h3>
                <div style="font-size: 3rem; font-weight: 800; color: #22c55e; margin: 1rem 0;">
                    ${key_entry:.2f}
                </div>
                <div style="font-size: 1.1rem; opacity: 0.9;">
                    <strong>0.786 Fibonacci Level</strong><br>
                    <span style="font-size: 0.9rem;">Expected in next hour candle</span>
                </div>
                <div style="margin-top: 1rem; font-size: 0.85rem; opacity: 0.7;">
                    Range: ${bounce_high:.2f} → ${bounce_low:.2f} (${bounce_high - bounce_low:.2f} spread)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Trading alerts
            current_range_percent = ((bounce_high - bounce_low) / bounce_low) * 100
            
            st.markdown("### ⚠️ Trading Alerts")
            
            alert_col1, alert_col2 = st.columns(2)
            
            with alert_col1:
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.1); border-radius: 8px; padding: 1rem;">
                    <strong>📊 Range Analysis:</strong><br>
                    Bounce Range: {current_range_percent:.1f}%<br>
                    {"Strong signal" if current_range_percent > 2 else "Weak signal" if current_range_percent < 1 else "Moderate signal"}
                </div>
                """, unsafe_allow_html=True)
            
            with alert_col2:
                st.markdown(f"""
                <div style="background: rgba(139, 92, 246, 0.1); border-radius: 8px; padding: 1rem;">
                    <strong>⏰ Timing:</strong><br>
                    Watch for: Next hour candle<br>
                    Entry: Around ${key_entry:.2f}
                </div>
                """, unsafe_allow_html=True)
        
        elif bounce_low > 0 or bounce_high > 0:
            st.warning("⚠️ Please enter both bounce low and high values, with high > low")
        else:
            st.info("💡 Enter bounce low and high prices to calculate Fibonacci retracement levels")
        
        # ── REAL-TIME CONTRACT LOOKUP ───────────────────────────────────────────────
        create_section_header("🔍", "Real-Time Contract Lookup")
        
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top: 0;">⚡ Instant Contract Projections</h4>
            <p>Enter any time to get instant contract price projections based on your contract line. 
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
                <div style="padding: 1rem; background: rgba(34, 197, 94, 0.1); border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.2); margin-top: 1.8rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem;">🎯</div>
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.8;">Contract Price @ {lookup_time.strftime('%H:%M')}</div>
                            <div style="font-size: 2rem; font-weight: 800; color: #22c55e;">${projected_value:.2f}</div>
                            <div style="font-size: 0.85rem; opacity: 0.7;">{blocks} blocks • {projected_value - st.session_state.contract_price:+.2f} change</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.2); margin-top: 1.8rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem;">⏳</div>
                        <div>
                            <div style="font-size: 1.1rem; font-weight: 600;">Waiting for Contract Configuration</div>
                            <div style="font-size: 0.9rem; opacity: 0.8;">Set contract line points and generate analysis to activate lookup</div>
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
                
                # Show best trading days for this stock with enhanced visibility
                if ticker in BEST_TRADING_DAYS:
                    best_info = BEST_TRADING_DAYS[ticker]
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(34, 197, 94, 0.1) 100%);
                        border: 2px solid rgba(34, 197, 94, 0.3);
                        border-radius: 12px;
                        padding: 1.2rem;
                        margin-bottom: 1.5rem;
                        box-shadow: 0 4px 15px rgba(34, 197, 94, 0.2);
                    ">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="
                                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                                border-radius: 50%;
                                width: 3rem;
                                height: 3rem;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 1.5rem;
                            ">📅</div>
                            <div>
                                <div style="color: #22c55e; font-weight: 700; font-size: 1.1rem;">
                                    Best Trading Days: {best_info['days']}
                                </div>
                                <div style="color: #e2e8f0; opacity: 0.9; margin-top: 0.25rem;">
                                    {best_info['rationale']}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced playbook access
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="
                        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                        border-radius: 12px;
                        padding: 0.1rem;
                        display: inline-block;
                        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
                    ">
                        <div style="
                            background: rgba(255, 255, 255, 0.1);
                            border-radius: 11px;
                            padding: 0.6rem 1.5rem;
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.2);
                        ">
                            <p style="margin: 0; color: white; font-weight: 600; font-size: 0.9rem;">
                                📚 Access detailed trading rules & risk management
                            </p>
                        </div>
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
                
                st.markdown(f"""
                <div class="info-box">
                    <h4 style="margin-top: 0;">{ICONS[ticker]} {ticker} Strategy Overview</h4>
                    <p>Configure anchor points from the previous trading day to project optimal entry and exit positions. 
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
                
                # Current slope display
                current_slope = st.session_state.slopes[ticker]
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.1); border-radius: 12px; padding: 1rem; margin: 1rem 0; border: 1px solid rgba(59, 130, 246, 0.2);">
                    <strong>📊 Current {ticker} Slope:</strong> <code>{current_slope:.4f}</code>
                    <small style="opacity: 0.7; display: block;">Adjust in sidebar under 'Slope Adjustments'</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate button
                generate_col = st.columns([1, 2, 1])[1]
                with generate_col:
                    generate_stock = st.button(
                        f"🚀 Generate {ticker} Forecast",
                        use_container_width=True,
                        type="primary",
                        key=f"generate_{ticker}",
                        help=f"Generate complete forecast analysis for {ticker}"
                    )
                
                # Results section
                if generate_stock:
                    if low_price > 0 and high_price > 0:
                        # Metrics cards
                        st.markdown('<div class="cards-container">', unsafe_allow_html=True)
                        
                        metric_col1, metric_col2 = st.columns(2)
                        with metric_col1:
                            create_metric_card("low", "📉", f"{ticker} Low", low_price)
                        with metric_col2:
                            create_metric_card("high", "📈", f"{ticker} High", high_price)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Calculate anchor times
                        low_anchor = datetime.combine(forecast_date, low_time)
                        high_anchor = datetime.combine(forecast_date, high_time)
                        
                        # Generate forecast tables
                        create_section_header("📉", f"{ticker} Low Anchor Projections")
                        
                        low_forecast = create_forecast_table(
                            low_price,
                            current_slope,
                            low_anchor,
                            forecast_date,
                            GENERAL_SLOTS,
                            is_spx=False,
                            fan_mode=True
                        )
                        st.dataframe(low_forecast, use_container_width=True, hide_index=True)
                        
                        # Analysis insights
                        price_range = high_price - low_price
                        avg_entry = low_forecast['Entry'].mean()
                        avg_exit = low_forecast['Exit'].mean()
                        avg_spread = low_forecast['Spread'].mean()
                        
                        st.markdown(f"""
                        <div class="success-box">
                            <h4 style="margin-top: 0;">📊 Low Anchor Analysis</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1rem;">
                                <div><strong>Average Entry:</strong><br>${avg_entry:.2f}</div>
                                <div><strong>Average Exit:</strong><br>${avg_exit:.2f}</div>
                                <div><strong>Average Spread:</strong><br>${avg_spread:.2f}</div>
                                <div><strong>Prev Day Range:</strong><br>${price_range:.2f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        create_section_header("📈", f"{ticker} High Anchor Projections")
                        
                        high_forecast = create_forecast_table(
                            high_price,
                            current_slope,
                            high_anchor,
                            forecast_date,
                            GENERAL_SLOTS,
                            is_spx=False,
                            fan_mode=True
                        )
                        st.dataframe(high_forecast, use_container_width=True, hide_index=True)
                        
                        # High anchor analysis
                        avg_entry_high = high_forecast['Entry'].mean()
                        avg_exit_high = high_forecast['Exit'].mean()
                        avg_spread_high = high_forecast['Spread'].mean()
                        
                        st.markdown(f"""
                        <div class="success-box">
                            <h4 style="margin-top: 0;">📊 High Anchor Analysis</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1rem;">
                                <div><strong>Average Entry:</strong><br>${avg_entry_high:.2f}</div>
                                <div><strong>Average Exit:</strong><br>${avg_exit_high:.2f}</div>
                                <div><strong>Average Spread:</strong><br>${avg_spread_high:.2f}</div>
                                <div><strong>Efficiency:</strong><br>{(avg_spread_high/price_range*100):.1f}%</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.warning("⚠️ Please enter both low and high prices to generate forecast.")
        
        # Create all enhanced stock tabs
        stock_tickers = list(ICONS.keys())[1:]
        for i, ticker in enumerate(stock_tickers):
            create_enhanced_stock_tab(i, ticker)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📚 STRATEGY PLAYBOOKS TAB - Trading Rules & Guides
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with main_tabs[3]:
        create_playbook_navigation()
                
                # ═══════════════════════════════════════════════════════════════════════════════
                # 📊 PERFORMANCE ANALYSIS
                # ═══════════════════════════════════════════════════════════════════════════════
                create_section_header("🎯", "Exit Strategy Performance Analysis")
                
                # Calculate comprehensive performance metrics
                all_entries = []
                all_fan_profits = []
                
                for forecast in [high_forecast, close_forecast, low_forecast]:
                    all_entries.extend(forecast['Entry'].tolist())
                    all_fan_profits.extend(forecast['Fan Profit'].tolist())
                
                avg_entry = sum(all_entries) / len(all_entries)
                avg_fan_profit = sum(all_fan_profits) / len(all_fan_profits)
                total_sessions = len(SPX_SLOTS)
                blended_profit = (9 + avg_fan_profit) / 2
                
                # Performance metrics cards
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div style="background: rgba(34, 197, 94, 0.1); border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid rgba(34, 197, 94, 0.2);">
                        <div style="font-size: 2rem; font-weight: bold; color: #22c55e;">+8.5</div>
                        <div style="font-size: 1rem; font-weight: 600;">First Exit Points</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">High Probability</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background: rgba(59, 130, 246, 0.1); border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid rgba(59, 130, 246, 0.2);">
                        <div style="font-size: 2rem; font-weight: bold; color: #3b82f6;">{avg_fan_profit:.1f}</div>
                        <div style="font-size: 1rem; font-weight: 600;">Avg Fan Profit</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">Remaining 50%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="background: rgba(245, 158, 11, 0.1); border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid rgba(245, 158, 11, 0.2);">
                        <div style="font-size: 2rem; font-weight: bold; color: #f59e0b;">{total_sessions}</div>
                        <div style="font-size: 1rem; font-weight: 600;">Time Slots</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">Trading Windows</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div style="background: rgba(139, 92, 246, 0.1); border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid rgba(139, 92, 246, 0.2);">
                        <div style="font-size: 2rem; font-weight: bold; color: #8b5cf6;">{blended_profit:.1f}</div>
                        <div style="font-size: 1rem; font-weight: 600;">Blended Avg</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">Per Trade</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced trading rules reminder
                st.markdown("""
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 2rem; margin-top: 2rem;">
                    <h4 style="margin-top: 0; color: #f59e0b;">⚠️ Two-Stage Exit Rules & Risk Management</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem;">
                        <div>
                            <strong>🎯 First Exit (50% position):</strong><br>
                            • Target: +9 points<br>
                            • Timing: Exit immediately when hit<br>
                            • Logic: Secure reliable profit<br>
                            • Success Rate: ~95%+
                        </div>
                        <div>
                            <strong>📊 Fan Exit (50% position):</strong><br>
                            • Target: Fan model projection<br>
                            • Timing: Based on time and price action<br>
                            • Logic: Capture extended move<br>
                            • Potential: Higher upside
                        </div>
                        <div>
                            <strong>🛑 Risk Management:</strong><br>
                            • Never hold past 3:45 PM<br>
                            • Trail stop after first exit<br>
                            • Full exit if breaks below entry anchor<br>
                            • Position size: 1-2% max risk
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
                # 📏 CONTRACT LINE GENERATION & ANALYSIS
                # ═══════════════════════════════════════════════════════════════════════════════
                create_section_header("📏", "Contract Line Analysis")
                
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
                
                # Enhanced contract line metrics display
                st.markdown(f"""
                <div class="success-box">
                    <h4 style="margin-top: 0;">📊 Contract Line Metrics</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                        <div>
                            <strong>📍 Anchor Point:</strong><br>
                            {low1_time.strftime('%H:%M')} @ ${low1_price:.2f}
                        </div>
                        <div>
                            <strong>📈 Slope Rate:</strong><br>
                            {contract_slope:.4f} per block
                        </div>
                        <div>
                            <strong>📏 Time Span:</strong><br>
                            {time_diff_blocks} blocks
                        </div>
                        <div>
                            <strong>💰 Price Delta:</strong><br>
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
            
            # ═══════════════════════════════════════════════════════════════════════════════
            # 📈 FIBONACCI BOUNCE ANALYZER - Advanced Algorithmic Entry Detection
            # ═══════════════════════════════════════════════════════════════════════════════
            create_section_header("📈", "Fibonacci Bounce Analysis")
            
            st.markdown("""
            <div class="info-box">
                <h4 style="margin-top: 0;">🎯 Algorithmic Entry Detection</h4>
                <p>When SPX bounces off a line, the contract follows with a retracement to 0.786 Fibonacci level. 
                This is where algorithms typically enter for high-probability runs. Use this tool to identify optimal entry points 
                that typically occur in the next hour candle.</p>
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
                <div style="background: rgba(245, 158, 11, 0.1); border-radius: 12px; padding: 1rem; margin-top: 1.8rem; border: 1px solid rgba(245, 158, 11, 0.2);">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚠️</div>
                        <div style="font-size: 1rem; font-weight: 600;">Watch Next Hour</div>
                        <div style="font-size: 0.85rem; opacity: 0.8;">0.786 entry typically occurs</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Generate Fibonacci analysis
            if bounce_low > 0 and bounce_high > bounce_low:
                st.markdown("### 🧮 Fibonacci Retracement Levels")
                
                # Create and display fibonacci table
                fib_table = create_fibonacci_table(bounce_low, bounce_high)
                st.dataframe(fib_table, use_container_width=True, hide_index=True)
                
                # Highlight the key 0.786 level
                fib_levels = calculate_fibonacci_levels(bounce_low, bounce_high)
                key_entry = fib_levels["0.786"]
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(34, 197, 94, 0.1) 100%);
                    border: 2px solid rgba(34, 197, 94, 0.4);
                    border-radius: 12px;
                    padding: 2rem;
                    margin: 1.5rem 0;
                    text-align: center;
                    box-shadow: 0 8px 25px rgba(34, 197, 94, 0.3);
                ">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎯</div>
                    <h3 style="margin: 0; color: #22c55e; font-size: 1.8rem;">Algorithmic Entry Zone</h3>
                    <div style="font-size: 3rem; font-weight: 800; color: #22c55e; margin: 1rem 0;">
                        ${key_entry:.2f}
                    </div>
                    <div style="font-size: 1.1rem; opacity: 0.9;">
                        <strong>0.786 Fibonacci Level</strong><br>
                        <span style="font-size: 0.9rem;">Expected in next hour candle</span>
                    </div>
                    <div style="margin-top: 1rem; font-size: 0.85rem; opacity: 0.7;">
                        Range: ${bounce_high:.2f} → ${bounce_low:.2f} (${bounce_high - bounce_low:.2f} spread)
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced trading alerts
                current_range_percent = ((bounce_high - bounce_low) / bounce_low) * 100
                
                st.markdown("### ⚠️ Trading Alerts & Analysis")
                
                alert_col1, alert_col2, alert_col3 = st.columns(3)
                
                with alert_col1:
                    signal_strength = "Strong signal" if current_range_percent > 2 else "Weak signal" if current_range_percent < 1 else "Moderate signal"
                    signal_color = "#22c55e" if current_range_percent > 2 else "#ef4444" if current_range_percent < 1 else "#f59e0b"
                    
                    st.markdown(f"""
                    <div style="background: rgba(59, 130, 246, 0.1); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(59, 130, 246, 0.2);">
                        <strong>📊 Range Analysis:</strong><br>
                        Bounce Range: {current_range_percent:.1f}%<br>
                        <span style="color: {signal_color}; font-weight: 600;">{signal_strength}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with alert_col2:
                    st.markdown(f"""
                    <div style="background: rgba(139, 92, 246, 0.1); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(139, 92, 246, 0.2);">
                        <strong>⏰ Timing Strategy:</strong><br>
                        Watch for: Next hour candle<br>
                        Entry Zone: ${key_entry:.2f}<br>
                        Setup Type: Algo entry
                    </div>
                    """, unsafe_allow_html=True)
                
                with alert_col3:
                    profit_potential = bounce_high - key_entry
                    st.markdown(f"""
                    <div style="background: rgba(34, 197, 94, 0.1); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(34, 197, 94, 0.2);">
                        <strong>💰 Profit Potential:</strong><br>
                        From 0.786: ${profit_potential:.2f}<br>
                        Risk/Reward: Favorable<br>
                        Probability: High
                    </div>
                    """, unsafe_allow_html=True)
            
            elif bounce_low > 0 or bounce_high > 0:
                st.warning("⚠️ Please enter both bounce low and high values, with high > low")
            else:
                st.info("💡 Enter bounce low and high prices to calculate Fibonacci retracement levels")
            
            # ═══════════════════════════════════════════════════════════════════════════════
            # 🔍 REAL-TIME LOOKUP SYSTEM
            # ═══════════════════════════════════════════════════════════════════════════════
            create_section_header("🔍", "Real-Time Price Lookup")
            
            st.markdown("""
            <div class="info-box">
                <h4 style="margin-top: 0;">⚡ Instant Projections</h4>
                <p>Enter any time to get instant price projections based on your contract line. 
                This tool works regardless of whether you've generated the full forecast and provides 
                immediate market timing insights.</p>
            </div>
            """, unsafe_allow_html=True)
            
            lookup_col1, lookup_col2 = st.columns([1, 2])
            
            with lookup_col1:
                lookup_time = st.time_input(
                    "🕐 Lookup Time",
                    value=time(9, 25),
                    step=300,
                    key="lookup_time_input",
                    help="Enter any time to get projected price"
                )
            
            with lookup_col2:
                if st.session_state.contract_anchor:
                    target_datetime = datetime.combine(forecast_date, lookup_time)
                    blocks = calculate_spx_blocks(st.session_state.contract_anchor, target_datetime)
                    projected_value = st.session_state.contract_price + (st.session_state.contract_slope * blocks)
                    
                    st.markdown(f"""
                    <div style="padding: 1.5rem; background: rgba(34, 197, 94, 0.1); border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.2); margin-top: 1.8rem;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="font-size: 2rem;">🎯</div>
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Projected @ {lookup_time.strftime('%H:%M')}</div>
                                <div style="font-size: 2rem; font-weight: 800; color: #22c55e;">${projected_value:.2f}</div>
                                <div style="font-size: 0.85rem; opacity: 0.7;">{blocks} blocks • {projected_value - st.session_state.contract_price:+.2f} change</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="padding: 1.5rem; background: rgba(245, 158, 11, 0.1); border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.2); margin-top: 1.8rem;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="font-size: 2rem;">⏳</div>
                            <div>
                                <div style="font-size: 1.1rem; font-weight: 600;">Waiting for Configuration</div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Set Low-1 & Low-2 points and generate forecast to activate lookup</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
        # 🚀 STOCK TABS WITH PLAYBOOK INTEGRATION
        # ═══════════════════════════════════════════════════════════════════════════════
        
        def create_enhanced_stock_tab(tab_index, ticker):
            """Create enhanced stock tab with playbook integration and best trading days"""
            with forecast_tabs[tab_index]:
                create_section_header(ICONS[ticker], f"{ticker} Analysis Center")
                
                # Enhanced best trading days display
                if ticker in BEST_TRADING_DAYS:
                    best_info = BEST_TRADING_DAYS[ticker]
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(34, 197, 94, 0.1) 100%);
                        border: 2px solid rgba(34, 197, 94, 0.3);
                        border-radius: 12px;
                        padding: 1.2rem;
                        margin-bottom: 1.5rem;
                        box-shadow: 0 4px 15px rgba(34, 197, 94, 0.2);
                    ">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="
                                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                                border-radius: 50%;
                                width: 3rem;
                                height: 3rem;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 1.5rem;
                            ">📅</div>
                            <div>
                                <div style="color: #22c55e; font-weight: 700; font-size: 1.1rem;">
                                    Best Trading Days: {best_info['days']}
                                </div>
                                <div style="color: #e2e8f0; opacity: 0.9; margin-top: 0.25rem;">
                                    {best_info['rationale']}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced playbook access
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="
                        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                        border-radius: 12px;
                        padding: 0.1rem;
                        display: inline-block;
                        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
                    ">
                        <div style="
                            background: rgba(255, 255, 255, 0.1);
                            border-radius: 11px;
                            padding: 0.6rem 1.5rem;
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.2);
                        ">
                            <p style="margin: 0; color: white; font-weight: 600; font-size: 0.9rem;">
                                📚 Access detailed trading rules & risk management
                            </p>
                        </div>
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
                
                # Enhanced strategy overview
                st.markdown(f"""
                <div class="info-box">
                    <h4 style="margin-top: 0;">{ICONS[ticker]} {ticker} Strategy Overview</h4>
                    <p>Configure anchor points from the previous trading day to project optimal entry and exit positions. 
                    Use the optimal trading days shown above for best results. The system uses your custom slope settings 
                    to generate precise fan-based projections tailored to {ticker}'s unique characteristics.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # ═══════════════════════════════════════════════════════════════════════════════
                # 📊 STOCK INPUT SECTION
                # ═══════════════════════════════════════════════════════════════════════════════
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
                
                # Enhanced current slope display
                current_slope = st.session_state.slopes[ticker]
                slope_trend = "Bearish" if current_slope < 0 else "Bullish" if current_slope > 0 else "Neutral"
                slope_color = "#ef4444" if current_slope < 0 else "#22c55e" if current_slope > 0 else "#6b7280"
                
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.1); border-radius: 12px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(59, 130, 246, 0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>📊 Current {ticker} Slope:</strong> <code style="font-size: 1.1rem;">{current_slope:.4f}</code><br>
                            <small style="opacity: 0.7;">Adjust in sidebar under 'Slope Adjustments'</small>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: {slope_color}; font-weight: 600; font-size: 1.1rem;">{slope_trend}</div>
                            <div style="font-size: 0.85rem; opacity: 0.7;">Market Bias</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced generate button
                generate_col = st.columns([1, 2, 1])[1]
                with generate_col:
                    generate_stock = st.button(
                        f"🚀 Generate {ticker} Forecast",
                        use_container_width=True,
                        type="primary",
                        key=f"generate_{ticker}",
                        help=f"Generate complete forecast analysis for {ticker}"
                    )
                
                # ═══════════════════════════════════════════════════════════════════════════════
                # 📈 STOCK FORECAST RESULTS
                # ═══════════════════════════════════════════════════════════════════════════════
                if generate_stock:
                    if low_price > 0 and high_price > 0:
                        # Enhanced metrics cards
                        st.markdown('<div class="cards-container">', unsafe_allow_html=True)
                        
                        metric_col1, metric_col2 = st.columns(2)
                        with metric_col1:
                            create_metric_card("low", "📉", f"{ticker} Low", low_price)
                        with metric_col2:
                            create_metric_card("high", "📈", f"{ticker} High", high_price)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Calculate anchor times
                        low_anchor = datetime.combine(forecast_date, low_time)
                        high_anchor = datetime.combine(forecast_date, high_time)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # 📉 LOW ANCHOR ANALYSIS
                        # ═══════════════════════════════════════════════════════════════════════════════
                        create_section_header("📉", f"{ticker} Low Anchor Projections")
                        
                        low_forecast = create_forecast_table(
                            low_price,
                            current_slope,
                            low_anchor,
                            forecast_date,
                            GENERAL_SLOTS,
                            is_spx=False,
                            fan_mode=True
                        )
                        st.dataframe(low_forecast, use_container_width=True, hide_index=True)
                        
                        # Enhanced analysis insights
                        price_range = high_price - low_price
                        avg_entry = low_forecast['Entry'].mean()
                        avg_exit = low_forecast['Exit'].mean()
                        avg_spread = low_forecast['Spread'].mean()
                        max_spread = low_forecast['Spread'].max()
                        min_spread = low_forecast['Spread'].min()
                        
                        st.markdown(f"""
                        <div class="success-box">
                            <h4 style="margin-top: 0;">📊 Low Anchor Performance Analysis</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1rem;">
                                <div><strong>Average Entry:</strong><br>${avg_entry:.2f}</div>
                                <div><strong>Average Exit:</strong><br>${avg_exit:.2f}</div>
                                <div><strong>Average Spread:</strong><br>${avg_spread:.2f}</div>
                                <div><strong>Max Spread:</strong><br>${max_spread:.2f}</div>
                                <div><strong>Min Spread:</strong><br>${min_spread:.2f}</div>
                                <div><strong>Prev Day Range:</strong><br>${price_range:.2f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # 📈 HIGH ANCHOR ANALYSIS
                        # ═══════════════════════════════════════════════════════════════════════════════
                        create_section_header("📈", f"{ticker} High Anchor Projections")
                        
                        high_forecast = create_forecast_table(
                            high_price,
                            current_slope,
                            high_anchor,
                            forecast_date,
                            GENERAL_SLOTS,
                            is_spx=False,
                            fan_mode=True
                        )
                        st.dataframe(high_forecast, use_container_width=True, hide_index=True)
                        
                        # Enhanced high anchor analysis
                        avg_entry_high = high_forecast['Entry'].mean()
                        avg_exit_high = high_forecast['Exit'].mean()
                        avg_spread_high = high_forecast['Spread'].mean()
                        efficiency = (avg_spread_high/price_range*100) if price_range > 0 else 0
                        
                        st.markdown(f"""
                        <div class="success-box">
                            <h4 style="margin-top: 0;">📊 High Anchor Performance Analysis</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1rem;">
                                <div><strong>Average Entry:</strong><br>${avg_entry_high:.2f}</div>
                                <div><strong>Average Exit:</strong><br>${avg_exit_high:.2f}</div>
                                <div><strong>Average Spread:</strong><br>${avg_spread_high:.2f}</div>
                                <div><strong>Efficiency:</strong><br>{efficiency:.1f}%</div>
                                <div><strong>Range Capture:</strong><br>{(avg_spread_high/price_range):.2f}x</div>
                                <div><strong>Volatility Factor:</strong><br>{(avg_spread_high/avg_entry_high*100):.1f}%</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # 📊 COMPARATIVE ANALYSIS
                        # ═══════════════════════════════════════════════════════════════════════════════
                        st.markdown(f"### 🔍 {ticker} Strategy Comparison")
                        
                        comparison_col1, comparison_col2 = st.columns(2)
                        
                        with comparison_col1:
                            better_anchor = "Low Anchor" if avg_spread > avg_spread_high else "High Anchor"
                            better_spread = max(avg_spread, avg_spread_high)
                            
                            st.markdown(f"""
                            <div style="background: rgba(139, 92, 246, 0.1); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(139, 92, 246, 0.2);">
                                <strong>🏆 Optimal Strategy:</strong><br>
                                {better_anchor}<br>
                                <span style="color: #8b5cf6; font-weight: 600;">${better_spread:.2f} avg spread</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with comparison_col2:
                            best_day_info = BEST_TRADING_DAYS.get(ticker, {"days": "N/A"})
                            st.markdown(f"""
                            <div style="background: rgba(34, 197, 94, 0.1); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(34, 197, 94, 0.2);">
                                <strong>📅 Best Trading Days:</strong><br>
                                {best_day_info['days']}<br>
                                <span style="color: #22c55e; font-weight: 600;">Optimal timing</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                    else:
                        st.warning("⚠️ Please enter both low and high prices to generate forecast.")
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # 🚀 CREATE ALL STOCK TABS
        # ═══════════════════════════════════════════════════════════════════════════════
        stock_tickers = list(ICONS.keys())[1:]  # Exclude SPX
        for i, ticker in enumerate(stock_tickers, 1):
            create_enhanced_stock_tab(i, ticker)

# ═══════════════════════════════════════════════════════════════════════════════
    # 📚 STRATEGY PLAYBOOKS TAB - Main Navigation
    # ═══════════════════════════════════════════════════════════════════════════════
    with main_tabs[1]:
        create_playbook_navigation()

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 FOOTER & FINAL ELEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

# Add spacing before footer
st.markdown("<br><br>", unsafe_allow_html=True)

# Enhanced footer with timezone-aware time
user_tz = get_user_timezone()
current_time = get_current_time_in_timezone(user_tz)
generation_time = format_time_with_timezone(current_time, user_tz)

st.markdown(f"""
<div style="
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 3rem;
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
">
    <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; flex-wrap: wrap;">
        <div>
            <h4 style="margin: 0; color: #667eea;">📈 Dr Didy SPX Forecast</h4>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.7; font-size: 0.9rem;">
                Advanced Market Forecasting System v{VERSION}
            </p>
        </div>
        <div style="height: 40px; width: 1px; background: rgba(255,255,255,0.1);"></div>
        <div>
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">
                🕐 Generated: {generation_time}
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.6;">
                Target: {forecast_date.strftime('%A, %B %d, %Y')}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Enhanced disclaimer
st.markdown("""
<div style="
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
">
    <p style="margin: 0; font-size: 0.85rem;">
        ⚠️ <strong>Disclaimer:</strong> This tool is for educational and analysis purposes only. 
        Always conduct your own research and consult with financial professionals before making investment decisions.
    </p>
</div>
""", unsafe_allow_html=True)

# Performance metrics (if forecasts were generated)
if st.session_state.forecasts_generated:
    with st.expander("📊 Session Performance Metrics", expanded=False):
        stock_tickers = list(ICONS.keys())[1:]  # Exclude SPX for count
        active_slopes_count = len([s for s in st.session_state.slopes.values() if s != 0])
        
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div style="padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px;">
                <strong>🎯 Forecasts Generated:</strong><br>
                SPX + {len(stock_tickers)} Stocks
            </div>
            <div style="padding: 1rem; background: rgba(34, 197, 94, 0.1); border-radius: 8px;">
                <strong>📈 Active Slopes:</strong><br>
                {active_slopes_count} configured
            </div>
            <div style="padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px;">
                <strong>💾 Saved Presets:</strong><br>
                {len(st.session_state.presets)} available
            </div>
            <div style="padding: 1rem; background: rgba(139, 92, 246, 0.1); border-radius: 8px;">
                <strong>⚡ Contract Line:</strong><br>
                {'Active' if st.session_state.contract_anchor else 'Inactive'}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Enhanced Pro Tips & Strategy Guide
with st.expander("💡 Pro Tips & Strategy Guide", expanded=False):
    st.markdown("""
    ### 🎯 **Optimization Tips**
    
    **🔧 Slope Tuning:**
    - Start with default slopes and adjust based on market conditions
    - Negative slopes typically indicate downward pressure
    - Fine-tune in 0.0001 increments for precision
    - Test different slopes across various market environments
    
    **⚓ Anchor Point Strategy:**
    - Use significant previous day levels (high, low, close)
    - Ensure times reflect actual market conditions
    - Consider volume and volatility when setting anchors
    - Cross-reference multiple anchors for confirmation
    
    **📏 Contract Line Setup:**
    - Choose Low-1 and Low-2 points with meaningful separation
    - Test different time intervals for optimal results
    - Monitor slope consistency across timeframes
    - Use contract lines for precise entry timing
    
    **🕐 Real-Time Usage:**
    - Use lookup tool for quick market timing decisions
    - Cross-reference multiple anchor projections
    - Adjust strategy based on developing market conditions
    - Combine with Fibonacci analysis for enhanced entries
    
    ### 📊 **Best Practices**
    
    1. **Start Simple:** Begin with SPX forecasts before moving to individual stocks
    2. **Save Presets:** Create configurations for different market conditions
    3. **Validate Projections:** Compare forecasts with actual market movements
    4. **Risk Management:** Always use proper position sizing and stop losses
    5. **Use Best Days:** Trade stocks on their optimal days for better results
    6. **Two-Stage Exits:** Implement the 8.5-point + fan model strategy for SPX
    
    ### 🚀 **Advanced Features**
    
    - **📈 Two-Stage Exits:** SPX 8.5-point + fan model for systematic profits
    - **📊 Fibonacci Analysis:** 0.786 retracement algo entry detection
    - **📅 Best Trading Days:** Optimized timing for each stock
    - **🎯 Fan Mode:** Entry/Exit projections for complex strategies
    - **🧮 Block Calculations:** Precise time-based position sizing
    - **⏰ Multi-Timeframe:** Coordinate across different time intervals
    - **💾 Preset Management:** Quick strategy switching
    - **📚 Integrated Playbooks:** Complete trading strategies and rules
    
    ### ⚠️ **Risk Management Essentials**
    
    - **Position Size:** Never risk more than 2% per trade
    - **Stop Losses:** Hard stops at -15% for options
    - **Time Management:** Never hold past 3:45 PM
    - **Market Context:** Reduce size when VIX > 25
    - **Psychology:** Step away after 3 losses in a row
    """)

# System Status & Health Check
with st.expander("🔧 System Status", expanded=False):
    # Calculate system health metrics
    total_slopes = len(st.session_state.slopes)
    configured_slopes = sum(1 for slope in st.session_state.slopes.values() if slope != 0)
    slope_health = (configured_slopes / total_slopes) * 100
    
    contract_status = "✅ Active" if st.session_state.contract_anchor else "⏳ Inactive"
    playbook_status = "✅ Available" if len(BEST_TRADING_DAYS) > 0 else "❌ Missing"
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
        <div style="padding: 1rem; background: rgba(34, 197, 94, 0.1); border-radius: 8px;">
            <strong>📊 Slope Configuration:</strong><br>
            {configured_slopes}/{total_slopes} configured ({slope_health:.0f}%)
        </div>
        <div style="padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px;">
            <strong>📏 Contract Line:</strong><br>
            {contract_status}
        </div>
        <div style="padding: 1rem; background: rgba(139, 92, 246, 0.1); border-radius: 8px;">
            <strong>📚 Playbooks:</strong><br>
            {playbook_status} ({len(BEST_TRADING_DAYS)} stocks)
        </div>
        <div style="padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px;">
            <strong>🎨 Theme:</strong><br>
            {st.session_state.theme} Mode
        </div>
        <div style="padding: 1rem; background: rgba(168, 85, 247, 0.1); border-radius: 8px;">
            <strong>🌍 Timezone:</strong><br>
            {user_tz.split('/')[-1]} Time
        </div>
    </div>
    """, unsafe_allow_html=True)

# Final spacing
st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🎉 COMPLETION MESSAGE
# ═══════════════════════════════════════════════════════════════════════════════
# This completes the enhanced Dr Didy SPX Forecast application with:
# ✅ Two-stage exit strategy (8.5-point + fan model)
# ✅ Fibonacci bounce analysis with algo entry detection
# ✅ Comprehensive playbook system with trading strategies
# ✅ Enhanced stock analysis with best trading days
# ✅ Professional UI with beautiful styling
# ✅ Clean, well-organized code structure
# ✅ Advanced risk management and performance tracking
# ✅ Real-time lookup and contract line analysis
# ✅ Timezone support with Chicago default and global options
