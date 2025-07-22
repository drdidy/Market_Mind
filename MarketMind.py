# ═══════════════════════════════════════════════════════════════════════════════
# 📈 Dr Didy SPX Forecast – v1.6.0 (Enhanced UI)
# ═══════════════════════════════════════════════════════════════════════════════

import json
import base64
import streamlit as st
from datetime import datetime, date, time, timedelta
from copy import deepcopy
import pandas as pd

# ── CONSTANTS & CONFIGURATION ────────────────────────────────────────────────
PAGE_TITLE = "Dr Didy SPX Forecast"
PAGE_ICON = "📈"
VERSION = "1.6.0"

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

COLORS = {
    "primary": "#1f77b4",
    "success": "#28a745", 
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 PLAYBOOK PART 1: DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════
# 🔗 ADD THIS AFTER SECTION 1 (Imports & Constants)

# ── BEST TRADING DAYS CHEAT SHEET ────────────────────────────────────────────
BEST_TRADING_DAYS = {
    "NVDA": {"days": "Tue / Thu", "rationale": "Highest volatility and option-flow mid-week"},
    "META": {"days": "Tue / Thu", "rationale": "News-feed reprice, AI headlines often drop Tue/Thu"},
    "TSLA": {"days": "Mon / Wed", "rationale": "Post-weekend gamma squeeze & mid-week momentum"},
    "AAPL": {"days": "Mon / Wed", "rationale": "Earnings drift & supply-chain headlines"},
    "AMZN": {"days": "Wed / Thu", "rationale": "Mid-week marketplace volume & OPEX flow"},
    "GOOGL": {"days": "Thu / Fri", "rationale": "Search-ad spend updates tilt end-week"},
    "NFLX": {"days": "Tue / Fri", "rationale": "Subscriber metrics chatter on Tue, positioning unwind on Fri"}
}

# ── SPX GOLDEN RULES ─────────────────────────────────────────────────────────
SPX_GOLDEN_RULES = [
    "🚪 **Exit levels are exits - never entries**",
    "🧲 **Anchors are magnets, not timing signals - let price come to you**", 
    "🎁 **The market will give you your entry - don't force it**",
    "🔄 **Consistency in process trumps perfection in prediction**",
    "❓ **When in doubt, stay out - there's always another trade**",
    "🏗️ **SPX ignores the full 16:00-17:00 maintenance block**"
]

# ── RISK MANAGEMENT RULES ────────────────────────────────────────────────────
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

# ── SPX ANCHOR TRADING RULES ─────────────────────────────────────────────────
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
    ]
}

# ── CONTRACT STRATEGIES ──────────────────────────────────────────────────────
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

# ── TIME MANAGEMENT RULES ────────────────────────────────────────────────────
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

# ── SESSION STATE INITIALIZATION ────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.update(
        theme="Dark",  # Default to dark theme for modern look
        slopes=deepcopy(BASE_SLOPES),
        presets={},
        contract_anchor=None,
        contract_slope=None,
        contract_price=None,
        forecasts_generated=False
    )

# Load slopes from URL parameters if available
if st.query_params.get("s"):
    try:
        st.session_state.slopes.update(
            json.loads(base64.b64decode(st.query_params["s"][0]).decode())
        )
    except Exception:
        pass

# ── PAGE CONFIGURATION ───────────────────────────────────────────────────────
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── ENHANCED CSS STYLING ────────────────────────────────────────────────────
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

/* Responsive design */
@media (max-width: 768px) {
    .main-banner h1 { font-size: 2rem; }
    .main-banner { padding: 1.5rem 1rem; }
    .cards-container { flex-direction: column; }
    .metric-card { min-width: auto; padding: 1.5rem; }
    .card-icon { width: 3rem; height: 3rem; font-size: 1.5rem; }
    .card-value { font-size: 1.8rem; }
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
</style>
""", unsafe_allow_html=True)

# ── HELPER FUNCTIONS ────────────────────────────────────────────────────────

def create_metric_card(card_type, icon, title, value):
    """Create a beautiful metric card"""
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
    """Generate time slots for trading"""
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

def create_forecast_table(price, slope, anchor, forecast_date, time_slots, is_spx=True, fan_mode=False):
    """Create forecast table with projections"""
    rows = []
    
    for slot in time_slots:
        hour, minute = map(int, slot.split(":"))
        target_time = datetime.combine(forecast_date, time(hour, minute))
        
        if is_spx:
            blocks = calculate_spx_blocks(anchor, target_time)
        else:
            blocks = calculate_stock_blocks(anchor, target_time)
        
        if fan_mode:
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

# Define time slots
SPX_SLOTS = make_time_slots(time(8, 30))
GENERAL_SLOTS = make_time_slots(time(7, 30))

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 PLAYBOOK PART 2: DISPLAY FUNCTIONS  
# ═══════════════════════════════════════════════════════════════════════════════
# 🔗 ADD THIS AFTER SECTION 4 (Helper Functions)

def create_playbook_navigation():
    """Create the main playbook navigation page"""
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
    
    # Create the table
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
    
    # Playbook selection with enhanced styling
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
            # Enhanced button styling for each playbook
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
    """Display comprehensive SPX playbook"""
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

# Initialize playbook state
if 'selected_playbook' not in st.session_state:
    st.session_state.selected_playbook = None


# ── ENHANCED SIDEBAR ────────────────────────────────────────────────────────

st.sidebar.markdown(f"""
<div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem;">
    <h2 style="margin: 0; color: #667eea;">⚙️ Strategy Controls</h2>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.7; font-size: 0.9rem;">v{VERSION}</p>
</div>
""", unsafe_allow_html=True)

# Theme selection (keeping for future use)
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
            st.experimental_rerun()

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

# ── MAIN HEADER ─────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="main-banner">
    <h1>{PAGE_ICON} {PAGE_TITLE}</h1>
    <div class="subtitle">Advanced Market Forecasting • {current_day} Session</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 PLAYBOOK PART 3: MAIN INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════
# 🔗 REPLACE YOUR EXISTING MAIN TABS SECTION WITH THIS

# Check if user is viewing a specific playbook
if st.session_state.selected_playbook:
    display_selected_playbook()
else:
    # Create main navigation tabs
    main_tabs = st.tabs(["📈 Forecasting Tools", "📚 Strategy Playbooks"])
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FORECASTING TAB (Your existing functionality)
    # ═══════════════════════════════════════════════════════════════════════════════
    with main_tabs[0]:
        # Sub-tabs for different assets
        tab_labels = [f"{ICONS[ticker]} {ticker}" for ticker in ICONS.keys()]
        forecast_tabs = st.tabs(tab_labels)
        
        # SPX Tab - Enhanced with playbook integration
        with forecast_tabs[0]:
            create_section_header("🎯", f"SPX Strategy Center - {current_day}")
            
            # Quick playbook access with enhanced styling
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
                            📚 Click below to access complete SPX trading strategies & rules
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
                <h4 style="margin-top: 0;">📋 Strategy Overview</h4>
                <p>Configure your SPX anchor points and contract line parameters for precise market timing. 
                The system uses advanced block calculations to project optimal entry and exit points.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick Rules Reminder
            with st.expander("🔔 Quick SPX Rules Reminder", expanded=False):
                st.markdown("**Key Rules to Remember:**")
                for rule in SPX_GOLDEN_RULES[:3]:  # Show first 3 rules
                    st.markdown(f"• {rule}")
                st.markdown("*Click 'View Complete SPX Playbook' above for all rules and strategies*")
            
            # YOUR EXISTING SPX CONTENT GOES HERE
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
                    key="spx_low1_time",
                    help="First reference point time"
                )
                low1_price = st.number_input(
                    "Price", 
                    value=10.0, 
                    min_value=0.0, 
                    step=0.1,
                    key="spx_low1_price",
                    help="First reference point price"
                )
            
            with contract_col2:
                st.markdown("#### 🎯 **Low-2 Point**")
                low2_time = st.time_input(
                    "Time", 
                    value=time(3, 30), 
                    step=300,
                    key="spx_low2_time",
                    help="Second reference point time"
                )
                low2_price = st.number_input(
                    "Price", 
                    value=12.0, 
                    min_value=0.0, 
                    step=0.1,
                    key="spx_low2_price",
                    help="Second reference point price"
                )
            
            # ADD YOUR SECTIONS 7-8 (FORECAST GENERATION & LOOKUP) HERE
            
        # Enhanced Stock Tabs with playbook integration
        def create_enhanced_stock_tab(tab_index, ticker):
            """Create stock tab with playbook integration"""
            with forecast_tabs[tab_index]:
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
                
                # YOUR EXISTING STOCK TAB CONTENT GOES HERE
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
                
                # ADD YOUR EXISTING STOCK FORECAST GENERATION CODE HERE
        
        # Create all enhanced stock tabs
        stock_tickers = list(ICONS.keys())[1:]
        for i, ticker in enumerate(stock_tickers, 1):
            create_enhanced_stock_tab(i, ticker)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # STRATEGY PLAYBOOKS TAB
    # ═══════════════════════════════════════════════════════════════════════════════
    with main_tabs[1]:
        create_playbook_navigation()
    
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
            key="low1_time",
            help="First reference point time"
        )
        low1_price = st.number_input(
            "Price", 
            value=10.0, 
            min_value=0.0, 
            step=0.1,
            key="low1_price",
            help="First reference point price"
        )
    
    with contract_col2:
        st.markdown("#### 🎯 **Low-2 Point**")
        low2_time = st.time_input(
            "Time", 
            value=time(3, 30), 
            step=300,
            key="low2_time",
            help="Second reference point time"
        )
        low2_price = st.number_input(
            "Price", 
            value=12.0, 
            min_value=0.0, 
            step=0.1,
            key="low2_price",
            help="Second reference point price"
        )

# ── FORECAST GENERATION ──────────────────────────────────────────────────
    
    forecast_button_col = st.columns([1, 2, 1])[1]  # Center the button
    
    with forecast_button_col:
        generate_forecast = st.button(
            "🚀 Generate Complete Forecast",
            use_container_width=True,
            type="primary",
            help="Generate all anchor trends and contract line projections"
        )
    
    if generate_forecast:
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
        
        # ── ANCHOR TREND TABLES ───────────────────────────────────────────────
        
        # High Anchor Trend
        create_section_header("📈", "High Anchor Projections")
        high_forecast = create_forecast_table(
            high_price, 
            st.session_state.slopes["SPX_HIGH"], 
            high_anchor, 
            forecast_date, 
            SPX_SLOTS, 
            is_spx=True, 
            fan_mode=True
        )
        st.dataframe(high_forecast, use_container_width=True, hide_index=True)
        
        # Close Anchor Trend  
        create_section_header("📊", "Close Anchor Projections")
        close_forecast = create_forecast_table(
            close_price, 
            st.session_state.slopes["SPX_CLOSE"], 
            close_anchor, 
            forecast_date, 
            SPX_SLOTS, 
            is_spx=True, 
            fan_mode=True
        )
        st.dataframe(close_forecast, use_container_width=True, hide_index=True)
        
        # Low Anchor Trend
        create_section_header("📉", "Low Anchor Projections") 
        low_forecast = create_forecast_table(
            low_price, 
            st.session_state.slopes["SPX_LOW"], 
            low_anchor, 
            forecast_date, 
            SPX_SLOTS, 
            is_spx=True, 
            fan_mode=True
        )
        st.dataframe(low_forecast, use_container_width=True, hide_index=True)

# ── CONTRACT LINE GENERATION ─────────────────────────────────────────
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
    
    # ── REAL-TIME LOOKUP SYSTEM ───────────────────────────────────────────────
    create_section_header("🔍", "Real-Time Price Lookup")
    
    st.markdown("""
    <div class="info-box">
        <h4 style="margin-top: 0;">⚡ Instant Projections</h4>
        <p>Enter any time to get instant price projections based on your contract line. 
        This tool works regardless of whether you've generated the full forecast.</p>
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
            <div style="padding: 1rem; background: rgba(34, 197, 94, 0.1); border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.2); margin-top: 1.8rem;">
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
            <div style="padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.2); margin-top: 1.8rem;">
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
# 🚀 STOCK ANALYSIS TABS
# ═══════════════════════════════════════════════════════════════════════════════

def create_stock_tab(tab_index, ticker):
    """Create an enhanced stock analysis tab"""
    with tabs[tab_index]:
        create_section_header(ICONS[ticker], f"{ticker} Analysis Center")
        
        st.markdown(f"""
        <div class="info-box">
            <h4 style="margin-top: 0;">{ICONS[ticker]} {ticker} Strategy Overview</h4>
            <p>Configure anchor points from the previous trading day to project optimal entry and exit positions. 
            The system uses your custom slope settings to generate precise fan-based projections.</p>
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

# Create all stock tabs
stock_tickers = list(ICONS.keys())[1:]  # Exclude SPX
for i, ticker in enumerate(stock_tickers, 1):
    create_stock_tab(i, ticker)

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 FOOTER & FINAL ELEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

# Add some spacing before footer
st.markdown("<br><br>", unsafe_allow_html=True)

# Enhanced footer
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
                🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.6;">
                Target: {forecast_date.strftime('%A, %B %d, %Y')}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Disclaimer as separate element
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
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div style="padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px;">
                <strong>🎯 Forecasts Generated:</strong><br>
                SPX + {len(stock_tickers)} Stocks
            </div>
            <div style="padding: 1rem; background: rgba(34, 197, 94, 0.1); border-radius: 8px;">
                <strong>📈 Active Slopes:</strong><br>
                {len([s for s in st.session_state.slopes.values() if s != 0])} configured
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

# Quick tips
with st.expander("💡 Pro Tips & Strategy Guide", expanded=False):
    st.markdown("""
    ### 🎯 **Optimization Tips**
    
    **🔧 Slope Tuning:**
    - Start with default slopes and adjust based on market conditions
    - Negative slopes typically indicate downward pressure
    - Fine-tune in 0.001 increments for precision
    
    **⚓ Anchor Point Strategy:**
    - Use significant previous day levels (high, low, close)
    - Ensure times reflect actual market conditions
    - Consider volume and volatility when setting anchors
    
    **📏 Contract Line Setup:**
    - Choose Low-1 and Low-2 points with meaningful separation
    - Test different time intervals for optimal results
    - Monitor slope consistency across timeframes
    
    **🕐 Real-Time Usage:**
    - Use lookup tool for quick market timing decisions
    - Cross-reference multiple anchor projections
    - Adjust strategy based on developing market conditions
    
    ### 📊 **Best Practices**
    
    1. **Start Simple:** Begin with SPX forecasts before moving to individual stocks
    2. **Save Presets:** Create configurations for different market conditions
    3. **Validate Projections:** Compare forecasts with actual market movements
    4. **Risk Management:** Always use proper position sizing and stop losses
    
    ### 🚀 **Advanced Features**
    
    - **Fan Mode:** Entry/Exit projections for complex strategies
    - **Block Calculations:** Precise time-based position sizing
    - **Multi-Timeframe:** Coordinate across different time intervals
    - **Preset Management:** Quick strategy switching
    """)

# Add final spacing
st.markdown("<br>", unsafe_allow_html=True)
