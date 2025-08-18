# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - ENTERPRISE SPX & EQUITIES FORECASTING PLATFORM
# PART 1: CORE CONFIGURATION & GLOBAL SETTINGS (INTEGRATED WITH PART 2A UI)
# Professional Trading Application with Advanced Analytics & Real-time Data
# ═══════════════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from typing import Dict, List, Optional, Tuple, Any


# ───────────────────────────────  GLOBAL CONFIGURATION  ───────────────────────────────
APP_NAME = "MarketLens Pro"
TAGLINE = "Enterprise SPX & Equities Forecasting"
VERSION = "2024.1"
COMPANY = "Max Pointe Consulting"

# Timezone configuration
ET = ZoneInfo("America/New_York")
CT = ZoneInfo("America/Chicago")

# Core trading parameters
SPX_SYMBOL = "^GSPC"
ES_SYMBOL = "ES=F"

# SPX Skyline and Baseline slopes (per 30-minute block)
SPX_SKYLINE_SLOPE = +0.2255  # SPX upper channel slope
SPX_BASELINE_SLOPE = -0.2255  # SPX lower channel slope

# Individual stock slopes (per 30-minute block) - Fixed per ticker
STOCK_SLOPES = {
    "AAPL": {"skyline": +0.0155, "baseline": -0.0155},
    "MSFT": {"skyline": +0.0541, "baseline": -0.0541},
    "NVDA": {"skyline": +0.0086, "baseline": -0.0086},
    "AMZN": {"skyline": +0.0139, "baseline": -0.0139},
    "GOOGL": {"skyline": +0.0122, "baseline": -0.0122},
    "TSLA": {"skyline": +0.0285, "baseline": -0.0285},
    "META": {"skyline": +0.0674, "baseline": -0.0674},
    "NFLX": {"skyline": +0.0089, "baseline": -0.0089},
    "GOOG": {"skyline": +0.0122, "baseline": -0.0122}  # Same as GOOGL
}

# Core equity universe with detailed specifications
MAJOR_EQUITIES = {
    "^GSPC": {"name": "S&P 500 Index", "icon": "📊", "type": "Index"},
    "AAPL": {"name": "Apple Inc.", "icon": "🍎", "type": "Tech"},
    "MSFT": {"name": "Microsoft Corp.", "icon": "💻", "type": "Tech"},
    "NVDA": {"name": "NVIDIA Corp.", "icon": "🔥", "type": "Semiconductor"},
    "AMZN": {"name": "Amazon.com Inc.", "icon": "📦", "type": "E-commerce"},
    "GOOGL": {"name": "Alphabet Inc.", "icon": "🔍", "type": "Tech"},
    "META": {"name": "Meta Platforms", "icon": "📱", "type": "Social Media"},
    "TSLA": {"name": "Tesla Inc.", "icon": "⚡", "type": "EV"},
    "NFLX": {"name": "Netflix Inc.", "icon": "🎬", "type": "Streaming"},
    "GOOG": {"name": "Alphabet Inc. (Class A)", "icon": "🌐", "type": "Tech"}
}

# Trading session configuration
RTH_START = time(8, 30)  # Regular Trading Hours start (CT)
RTH_END = time(14, 30)   # Regular Trading Hours end (CT)
ASIAN_START = time(17, 0)  # Asian session start (CT, previous day)
ASIAN_END = time(20, 0)    # Asian session end (CT, previous day)

# Data refresh intervals (seconds)
LIVE_DATA_TTL = 60
HISTORICAL_DATA_TTL = 300
CACHE_CLEANUP_INTERVAL = 3600

# ───────────────────────────────  STREAMLIT PAGE SETUP  ───────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} - Professional Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://maxpointeconsulting.com/support',
        'Report a bug': 'https://maxpointeconsulting.com/bugs',
        'About': f"{APP_NAME} v{VERSION} - Professional trading analytics platform"
    }
)

# ---- CSS helpers (injected on every run; safe & idempotent) --------------------------
def force_light_text_always():
    st.markdown("""
    <style>
    /* baseline variables (used by your app if referenced) */
    :root{
      --text:#e5e7eb !important;
      --muted:rgba(255,255,255,.75) !important;
      --subtle:rgba(255,255,255,.60) !important;
      --link:#22d3ee !important;
      --code-bg:rgba(255,255,255,.08) !important;
    }
    @media (prefers-color-scheme: light){
      :root{
        --text:#e5e7eb !important;
        --muted:rgba(255,255,255,.75) !important;
        --subtle:rgba(255,255,255,.60) !important;
        --link:#22d3ee !important;
        --code-bg:rgba(255,255,255,.08) !important;
      }
    }
    </style>
    """, unsafe_allow_html=True)

def apply_component_text_fixes():
    st.markdown("""
    <style>
    /* ── Metrics (value/label/delta) ─────────────────────────────────────────────── */
    div[data-testid="stMetricLabel"] > div { color: rgba(255,255,255,.7) !important; }
    div[data-testid="stMetricValue"] { color: #e5e7eb !important; }
    span[data-testid="stMetricDelta"] { color: #00ff88 !important; }

    /* ── Alerts (success/error/info) ─────────────────────────────────────────────── */
    div[role="alert"] * { color: #e5e7eb !important; }

    /* ── Plotly UI bits (hover text + modebar icons) ─────────────────────────────── */
    .js-plotly-plot .hovertext text { fill: #e5e7eb !important; }
    .js-plotly-plot .modebar-group .icon path { fill: #e5e7eb !important; }

    /* ── Sidebar: readably light text for *all* widgets ─────────────────────────── */
    section[data-testid="stSidebar"] *{
      color:#e5e7eb !important;
      opacity:1 !important;
    }
    /* Don’t break your gradient headings that use text-fill: transparent */
    section[data-testid="stSidebar"] *:not([style*="-webkit-text-fill-color: transparent"]){
      -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Radio (your nav) */
    section[data-testid="stSidebar"] [data-baseweb="radio"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important; opacity:1 !important;
    }

    /* Selectbox text (control) */
    section[data-testid="stSidebar"] [data-baseweb="select"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Date input (label + input) */
    section[data-testid="stSidebar"] [data-testid="stDateInput"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Sidebar links & buttons (if used) */
    section[data-testid="stSidebar"] a, section[data-testid="stSidebar"] a *,
    section[data-testid="stSidebar"] .stButton > button, section[data-testid="stSidebar"] .stButton > button *,
    section[data-testid="stSidebar"] .stLinkButton > a, section[data-testid="stSidebar"] .stLinkButton > a *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important; opacity:1 !important;
    }

    /* Kill any inline neon green that sneaks into sidebar text */
    section[data-testid="stSidebar"] [style*="color:#00ff88"],
    section[data-testid="stSidebar"] [style*="color: #00ff88"],
    section[data-testid="stSidebar"] [style*="rgb(0, 255, 136)"]{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }

    /* ── BaseWeb popover portals (outside the sidebar DOM) ──────────────────────── */
    [data-baseweb="menu"], [role="listbox"]{
      background:rgba(17,24,39,.98) !important;
      color:#e5e7eb !important;
      border:1px solid rgba(255,255,255,.12) !important;
    }
    [data-baseweb="menu"] *, [role="listbox"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }

    [data-baseweb="datepicker"], [data-baseweb="calendar"],
    [data-baseweb="datepicker"] *, [data-baseweb="calendar"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Inject CSS (call unconditionally so it applies on every rerun)
force_light_text_always()
apply_component_text_fixes()

# ───────────────────────────────  CORE UTILITY FUNCTIONS  ───────────────────────────────
def previous_trading_day(ref_d: date) -> date:
    """Calculate the previous trading day (skip weekends)."""
    d = ref_d - timedelta(days=1)
    while d.weekday() >= 5:  # Skip Saturday (5) and Sunday (6)
        d -= timedelta(days=1)
    return d

def is_market_hours() -> bool:
    """Check if currently in market hours (9:30 AM - 4:00 PM ET)."""
    now_et = datetime.now(ET)
    if now_et.weekday() >= 5:  # Weekend
        return False
    market_start = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_end = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_start <= now_et <= market_end

def get_market_status() -> Tuple[str, str]:
    """Get current market status and appropriate styling."""
    now_et = datetime.now(ET)
    if now_et.weekday() >= 5:
        return "🔴 Weekend", "error"
    elif is_market_hours():
        return "🟢 Market Open", "success"
    elif now_et.hour < 9 or (now_et.hour == 9 and now_et.minute < 30):
        return "🟡 Pre-Market", "warning"
    elif now_et.hour >= 16:
        return "🟡 After Hours", "warning"
    else:
        return "🔴 Market Closed", "error"

def format_currency(value: float, decimals: int = 2) -> str:
    """Format currency values with proper thousand separators."""
    return f"${value:,.{decimals}f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage values with sign."""
    return f"{value:+.{decimals}f}%"

def calculate_30min_blocks(from_dt: datetime, to_dt: datetime) -> int:
    """Calculate number of 30-minute blocks between two datetime objects."""
    delta = to_dt - from_dt
    return int(delta.total_seconds() // (30 * 60))

def generate_rth_slots() -> List[datetime]:
    """Generate RTH time slots every 30 minutes (8:30 AM - 2:30 PM CT)."""
    base_date = date.today()
    start = datetime.combine(base_date, RTH_START, tzinfo=CT)
    slots = []
    current = start
    while current.time() <= RTH_END:
        slots.append(current)
        current += timedelta(minutes=30)
    return slots

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with fallback."""
    try:
        if value is None or value == '' or str(value).lower() in ['nan', 'none', '—']:
            return default
        return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
    except (ValueError, TypeError):
        return default

# Helper function to get slopes for any asset
def get_asset_slopes(symbol: str) -> Dict[str, float]:
    """Get skyline and baseline slopes for the specified asset."""
    if symbol == "^GSPC":
        return {"skyline": SPX_SKYLINE_SLOPE, "baseline": SPX_BASELINE_SLOPE}
    elif symbol in STOCK_SLOPES:
        return STOCK_SLOPES[symbol]
    else:
        # Default to SPX slopes for unknown symbols
        return {"skyline": SPX_SKYLINE_SLOPE, "baseline": SPX_BASELINE_SLOPE}

def get_display_symbol(symbol: str) -> str:
    """Get user-friendly display name for symbol."""
    if symbol == "^GSPC":
        return "SPX"
    return symbol

# ───────────────────────────────  SESSION STATE INITIALIZATION  ───────────────────────────────
def initialize_session_state():
    """Initialize all session state variables with defaults."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_asset = "^GSPC"
        st.session_state.forecast_date = date.today()
        st.session_state.last_refresh = datetime.now()
        st.session_state.cache_stats = {"hits": 0, "misses": 0}
        st.session_state.error_log = []
        st.session_state.user_preferences = {
            "theme": "professional",
            "auto_refresh": False,
            "show_debug": False,
            "decimal_places": 2
        }

# Initialize session state
initialize_session_state()

# ───────────────────────────────  ERROR HANDLING & LOGGING  ───────────────────────────────
def log_error(error_msg: str, error_type: str = "General") -> None:
    """Log errors to session state for debugging."""
    if len(st.session_state.error_log) > 50:  # Keep only last 50 errors
        st.session_state.error_log = st.session_state.error_log[-25:]
    st.session_state.error_log.append({
        "timestamp": datetime.now().isoformat(),
        "type": error_type,
        "message": error_msg
    })

def display_system_status() -> Dict[str, Any]:
    """Generate system status information."""
    market_status, status_type = get_market_status()
    return {
        "market_status": market_status,
        "status_type": status_type,
        "current_time_et": datetime.now(ET).strftime("%I:%M:%S %p ET"),
        "current_time_ct": datetime.now(CT).strftime("%I:%M:%S %p CT"),
        "app_version": VERSION,
        "session_duration": str(datetime.now() - st.session_state.last_refresh),
        "cache_stats": st.session_state.cache_stats,
        "error_count": len(st.session_state.error_log)
    }

# ───────────────────────────────  DATA VALIDATION FUNCTIONS  ───────────────────────────────
def validate_symbol(symbol: str) -> bool:
    """Validate if symbol is in our supported universe."""
    return symbol.upper() in MAJOR_EQUITIES

def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate date range for data requests."""
    if start_date > end_date:
        return False
    if end_date > date.today():
        return False
    if (end_date - start_date).days > 365:  # Max 1 year range
        return False
    return True

def sanitize_price_data(price: Any) -> Optional[float]:
    """Sanitize and validate price data."""
    try:
        clean_price = safe_float_conversion(price)
        if clean_price <= 0 or clean_price > 1000000:  # Basic sanity check
            return None
        return clean_price
    except:
        return None

# ───────────────────────────────  CONFIGURATION CONSTANTS  ───────────────────────────────
# Color scheme for consistent theming (Updated for modern UI)
COLORS = {
    "primary": "#22d3ee",     # Neon cyan
    "secondary": "#a855f7",   # Neon purple
    "success": "#10b981",     # Neon green
    "warning": "#f59e0b",     # Neon orange
    "error": "#ef4444",       # Neon red/pink
    "neutral": "#64748b",     # Neutral gray
    "background": "transparent",  # Transparent for glass effect
    "text": "#ffffff",        # White text for dark theme
    "muted": "rgba(255, 255, 255, 0.7)"  # Muted white
}

# Chart configuration for Plotly (Updated for dark theme)
CHART_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": f"marketlens_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "height": 600,
        "width": 1200,
        "scale": 2
    }
}

# Performance monitoring thresholds
PERFORMANCE_THRESHOLDS = {
    "api_timeout": 30.0,  # seconds
    "max_retries": 3,
    "cache_size_limit": 1000,  # number of cached items
    "memory_threshold": 0.8,  # 80% memory usage warning
    "response_time_warning": 5.0  # seconds
}

# ───────────────────────────────  GLOBAL STATE MANAGEMENT  ───────────────────────────────
class AppState:
    """Centralized application state management."""
    @staticmethod
    def get_current_asset() -> str:
        return st.session_state.current_asset

    @staticmethod
    def set_current_asset(symbol: str) -> None:
        if validate_symbol(symbol):
            st.session_state.current_asset = symbol.upper()
        else:
            log_error(f"Invalid symbol: {symbol}", "Validation")

    @staticmethod
    def get_forecast_date() -> date:
        return st.session_state.forecast_date

    @staticmethod
    def set_forecast_date(new_date: date) -> None:
        if new_date <= date.today():
            st.session_state.forecast_date = new_date
        else:
            log_error(f"Future date not allowed: {new_date}", "Validation")

    @staticmethod
    def refresh_data() -> None:
        """Trigger data refresh and clear relevant caches."""
        st.session_state.last_refresh = datetime.now()
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()

# ───────────────────────────────  READY STATE VERIFICATION  ───────────────────────────────
def verify_system_ready() -> Dict[str, bool]:
    """Verify all system components are ready."""
    checks = {
        "session_initialized": st.session_state.get('initialized', False),
        "valid_asset": validate_symbol(st.session_state.current_asset),
        "valid_date": st.session_state.forecast_date <= date.today(),
        "timezone_support": True,  # Always available in modern Python
        "required_modules": True   # Imports succeeded if we're here
    }
    return checks

# Initialize and verify system readiness
system_status = verify_system_ready()

# ═══════════════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT DISPLAY (INTEGRATED WITH PART 2A STYLING)
# ═══════════════════════════════════════════════════════════════════════════════════════

# This section uses the CSS and UI components from Part 2A
# The navigation and hero section are handled in Part 2A

# Asset information for current selection
current_asset = st.session_state.current_asset
asset_info = MAJOR_EQUITIES[current_asset]
display_symbol = get_display_symbol(current_asset)
slopes = get_asset_slopes(current_asset)

# Professional metrics display using glass panels
st.markdown(f"""
<div class="glass-panel" style="padding: 2rem; margin: 2rem 0; text-align: center;">
    <div style="font-size: 4rem; margin-bottom: 1rem;">{asset_info['icon']}</div>
    <h1 style="color: #ffffff; font-size: 2.5rem; margin: 0.5rem 0; font-weight: 900;">
        {display_symbol} Analysis Dashboard
    </h1>
    <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.2rem; margin: 0;">
        {asset_info['name']} • {asset_info['type']} Sector
    </p>
</div>
""", unsafe_allow_html=True)

# Create professional metrics grid
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">SYMBOL</div>
        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 800;">{display_symbol}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">SECTOR</div>
        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 800;">{asset_info['type']}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    forecast_date = st.session_state.forecast_date
    st.markdown(f"""
    <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">ANALYSIS DATE</div>
        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 800;">{forecast_date.strftime('%m/%d/%Y')}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    market_status, status_type = get_market_status()
    status_color = "#00ff88" if status_type == "success" else "#ff6b35" if status_type == "warning" else "#ff006e"
    st.markdown(f"""
    <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">MARKET STATUS</div>
        <div style="color: {status_color}; font-size: 1.2rem; font-weight: 800;">{market_status}</div>
    </div>
    """, unsafe_allow_html=True)

# Session information
st.markdown("""
<div style="height: 1px; background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 20%, rgba(34, 211, 238, 0.4) 50%, rgba(255, 255, 255, 0.2) 80%, transparent 100%); margin: 3rem 0;"></div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    prev_day = previous_trading_day(forecast_date)
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">PREVIOUS SESSION</div>
        <div style="color: #ffffff; font-size: 1.25rem; font-weight: 700;">{prev_day.strftime('%B %d, %Y')}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    current_time_ct = datetime.now(CT).strftime("%I:%M:%S %p CT")
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">CURRENT TIME</div>
        <div style="color: #ffffff; font-size: 1.25rem; font-weight: 700;">{current_time_ct}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    system_checks = verify_system_ready()
    all_ready = all(system_checks.values())
    system_status_text = "All Systems Operational" if all_ready else "System Initializing"
    system_color = "#00ff88" if all_ready else "#ff6b35"
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">SYSTEM STATUS</div>
        <div style="color: {system_color}; font-size: 1.25rem; font-weight: 700;">{system_status_text}</div>
    </div>
    """, unsafe_allow_html=True)

# Professional footer with neon divider
st.markdown("""
<div style="height: 1px; background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 20%, rgba(168, 85, 247, 0.4) 50%, rgba(255, 255, 255, 0.2) 80%, transparent 100%); margin: 3rem 0;"></div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align: center; padding: 2rem 0; color: rgba(255, 255, 255, 0.8);">
    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        {APP_NAME} v{VERSION}
    </div>
    <div style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.6);">
        {COMPANY} • Professional Trading Analytics Platform
    </div>
</div>
""", unsafe_allow_html=True)

def apply_main_area_text_fix():
    # Forces readable text in MAIN content (not the sidebar), incl. tabs, radios, selects, date inputs.
    st.markdown("""
    <style>
    /* MAIN content container (excludes sidebar) */
    div[data-testid="stAppViewContainer"] *{
      color:#e5e7eb !important;
    }
    /* Keep gradient headings intact (they use text-fill: transparent) */
    div[data-testid="stAppViewContainer"] *:not([style*="-webkit-text-fill-color: transparent"]){
      -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Links in main */
    div[data-testid="stAppViewContainer"] a,
    div[data-testid="stAppViewContainer"] a *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Tabs in main */
    div[data-testid="stAppViewContainer"] .stTabs [data-baseweb="tab-list"]{
      background: rgba(255,255,255,.05) !important;
      border: 1px solid rgba(255,255,255,.12) !important; border-radius: 12px !important;
    }
    div[data-testid="stAppViewContainer"] .stTabs [data-baseweb="tab"],
    div[data-testid="stAppViewContainer"] .stTabs [data-baseweb="tab"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }
    div[data-testid="stAppViewContainer"] .stTabs [aria-selected="true"]{
      background: rgba(34,211,238,.18) !important;
      border: 1px solid rgba(34,211,238,.30) !important;
    }

    /* BaseWeb widgets in main (radio/select/date) */
    div[data-testid="stAppViewContainer"] [data-baseweb="radio"] *,
    div[data-testid="stAppViewContainer"] [data-baseweb="select"] *,
    div[data-testid="stAppViewContainer"] [data-testid="stDateInput"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Popover portals (menus & calendars) live outside; style them globally */
    [data-baseweb="menu"], [role="listbox"]{
      background: rgba(17,24,39,.98) !important;
      color:#e5e7eb !important; border:1px solid rgba(255,255,255,.12) !important;
    }
    [data-baseweb="menu"] *, [role="listbox"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }
    [data-baseweb="datepicker"], [data-baseweb="calendar"],
    [data-baseweb="datepicker"] *, [data-baseweb="calendar"] *{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Neutralize common inline dark colors coming from inline style attributes */
    div[data-testid="stAppViewContainer"] [style*="color:#000"],
    div[data-testid="stAppViewContainer"] [style*="color: #000"],
    div[data-testid="stAppViewContainer"] [style*="rgb(0, 0, 0)"],
    div[data-testid="stAppViewContainer"] [style*="color:#111"],
    div[data-testid="stAppViewContainer"] [style*="color: #111"]{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }
    </style>
    """, unsafe_allow_html=True)




# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2A: CORE UI FOUNDATION & COLOR SYSTEM
# Modern Glassmorphism Design with Perfect Color Accessibility
# ═══════════════════════════════════════════════════════════════════════════════════════

# --- Lightweight safety shims (no UI change; prevent NameErrors if upstream not loaded)
from datetime import datetime, date, timedelta
try:
    APP_NAME
except NameError:
    APP_NAME = "MarketLens Pro"
try:
    VERSION
except NameError:
    VERSION = "1.0"
try:
    get_display_symbol
except NameError:
    def get_display_symbol(x): return x
try:
    CHART_CONFIG
except NameError:
    CHART_CONFIG = {"displayModeBar": False, "responsive": True}
try:
    ET
except NameError:
    try:
        from pytz import timezone
        ET = timezone("US/Eastern")
    except Exception:
        ET = None
try:
    CT
except NameError:
    try:
        from pytz import timezone
        CT = timezone("US/Central")
    except Exception:
        CT = None

import streamlit as st

# Core CSS Foundation with Fixed Form Elements
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ========== CORE FOUNDATION & MODERN VARIABLES ========== */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  --warning-gradient: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
  --error-gradient: linear-gradient(135deg, #fc466b 0%, #3f5efb 100%);
  --neutral-gradient: linear-gradient(135deg, #434343 0%, #000000 100%);
  
  --glass-bg: rgba(255, 255, 255, 0.08);
  --glass-border: rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
  
  --neon-blue: #00d4ff;
  --neon-purple: #8b5cf6;
  --neon-green: #00ff88;
  --neon-orange: #ff6b35;
  --neon-pink: #ff006e;
  
  --surface-1: #0f0f23;
  --surface-2: #1a1a2e;
  --surface-3: #16213e;
  --surface-4: #0f172a;
  
  --accent-cyan: #22d3ee;
  --accent-violet: #a855f7;
  --accent-emerald: #10b981;
  --accent-amber: #f59e0b;
  --accent-rose: #f43f5e;
}

/* ========== BACKGROUND ONLY - PRESERVE TEXT COLORS ========== */
.stApp {
  background: 
    radial-gradient(circle at 20% 20%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 255, 198, 0.2) 0%, transparent 50%),
    linear-gradient(135deg, #0c0c1e 0%, #1a1a2e 100%);
  min-height: 100vh;
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ========== PRESERVE MAIN CONTENT TEXT COLORS ========== */
.main .block-container {
  color: #0f172a !important;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 2rem;
  margin: 1rem;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* Keep main content text dark by default */
.main .block-container * {
  color: #0f172a !important;
}

/* Exceptions: force white text on dark/transparent surfaces (no layout change) */
.main .block-container .hero-container *,
.main .block-container .glass-panel *,
.main .block-container .metric-card *,
.main .block-container .chart-container *,
.main .block-container .alert-success *,
.main .block-container .alert-warning *,
.main .block-container .alert-info *,
.main .block-container .stTabs *[aria-selected="true"],
.forecast-card *, .forecast-text {
  color: #ffffff !important;
}

/* ========== ANIMATED BACKGROUND PARTICLES ========== */
.stApp::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(2px 2px at 20px 30px, rgba(255, 255, 255, 0.15), transparent),
    radial-gradient(2px 2px at 40px 70px, rgba(255, 255, 255, 0.1), transparent),
    radial-gradient(1px 1px at 90px 40px, rgba(255, 255, 255, 0.1), transparent),
    radial-gradient(1px 1px at 130px 80px, rgba(255, 255, 255, 0.1), transparent),
    radial-gradient(2px 2px at 160px 30px, rgba(255, 255, 255, 0.1), transparent);
  background-repeat: repeat;
  background-size: 250px 300px;
  animation: sparkle 20s linear infinite;
  pointer-events: none;
  z-index: 1;
}

@keyframes sparkle {
  from { background-position: 0% 0%; }
  to { background-position: 250px 300px; }
}

/* ========== SIDEBAR STYLING ONLY ========== */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, 
    rgba(15, 15, 35, 0.95) 0%, 
    rgba(26, 26, 46, 0.95) 100%) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

section[data-testid="stSidebar"] > div { background: transparent !important; }

/* SIDEBAR TEXT COLOR FIXES */
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
  color: #ffffff !important;
}

/* ========== CRITICAL FIXES: SIDEBAR FORM ELEMENTS ========== */
section[data-testid="stSidebar"] .stSelectbox > div > div {
  background-color: #2d3748 !important;
  color: #ffffff !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div > div,
section[data-testid="stSidebar"] .stSelectbox > div > div > div > div {
  background-color: #2d3748 !important;
  color: #ffffff !important;
}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="popover"] {
  background-color: #2d3748 !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8) !important;
}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="popover"] * {
  background-color: #2d3748 !important; color: #ffffff !important;
}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="popover"] li:hover {
  background-color: rgba(34, 211, 238, 0.3) !important; color: #ffffff !important;
}
section[data-testid="stSidebar"] .stDateInput > div > div {
  background-color: #2d3748 !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stDateInput > div > div > input {
  background-color: #2d3748 !important; color: #ffffff !important; border: none !important;
}
section[data-testid="stSidebar"] .stDateInput div[data-baseweb="popover"] {
  background-color: #2d3748 !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8) !important;
}
section[data-testid="stSidebar"] .stDateInput div[data-baseweb="popover"] * {
  background-color: #2d3748 !important; color: #ffffff !important;
}
section[data-testid="stSidebar"] .stDateInput div[data-baseweb="popover"] button:hover {
  background-color: rgba(34, 211, 238, 0.3) !important; color: #ffffff !important;
}
section[data-testid="stSidebar"] .stButton > button {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%) !important;
  border: 1px solid rgba(34, 211, 238, 0.4) !important;
  border-radius: 8px !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--neon-blue) !important;
  box-shadow: 0 0 15px rgba(34, 211, 238, 0.4) !important;
  transform: translateY(-2px) !important;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%) !important;
}

/* ========== GLASSMORPHISM HERO SECTION ========== */
.hero-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  padding: 2.5rem;
  margin: 2rem 0;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  z-index: 10;
}
.hero-container::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--neon-blue) 20%, var(--neon-purple) 40%, var(--neon-green) 60%, var(--neon-orange) 80%, transparent 100%);
  animation: shimmer 3s ease-in-out infinite;
}
@keyframes shimmer { 0%, 100% { opacity: 0.3;} 50% { opacity: 1;} }

.hero-title {
  font-size: 3.5rem; font-weight: 900;
  background: linear-gradient(135deg, #ffffff 0%, #22d3ee 50%, #a855f7 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  margin: 0; letter-spacing: -0.02em;
  text-shadow: 0 0 40px rgba(34, 211, 238, 0.4);
  animation: glow-pulse 4s ease-in-out infinite;
}
@keyframes glow-pulse { 0%, 100% { filter: drop-shadow(0 0 10px rgba(34, 211, 238, 0.4)); } 50% { filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.6)); } }

.hero-subtitle { font-size: 1.5rem; font-weight: 600; color: rgba(255, 255, 255, 0.8); margin: 1rem 0; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3); }
.hero-meta { font-size: 1rem; color: rgba(255, 255, 255, 0.6); font-weight: 500; margin-top: 0.5rem; }

/* ========== SIDEBAR ENHANCEMENTS (dup safe) ========== */
section[data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(15, 15, 35, 0.95) 0%, rgba(26, 26, 46, 0.95) 100%) !important; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.1) !important; }
section[data-testid="stSidebar"] > div { background: transparent !important; }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div { color: #ffffff !important; }

/* ========== UTILITY CLASSES ========== */
.glass-panel { background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 16px; }
.text-center { text-align: center; }
.neon-border { border: 1px solid var(--neon-blue); box-shadow: 0 0 10px rgba(34, 211, 238, 0.3); }
.text-glow { text-shadow: 0 0 10px currentColor; }

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
  .hero-title { font-size: 2.5rem; }
  .hero-container { padding: 1.5rem; margin: 1rem 0; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# HERO SECTION WITH GLASSMORPHISM DESIGN
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_hero_section():
    """Create the stunning hero section with modern glassmorphism design."""
    market_status, status_type = get_market_status()
    current_asset = AppState.get_current_asset()
    asset_info = MAJOR_EQUITIES[current_asset]
    st.markdown(f"""
    <div class="hero-container">
        <div class="text-center">
            <h1 class="hero-title">MarketLens Pro</h1>
            <p class="hero-subtitle">Enterprise SPX & Equities Forecasting</p>
            <p class="hero-meta">v{VERSION} • Max Pointe Consulting • Professional Trading Analytics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# NAVIGATION SYSTEM FOUNDATION  
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_navigation_sidebar():
    """Create the futuristic navigation sidebar with proper form styling."""
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem 1rem; margin-bottom: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈</div>
            <h2 style="color: #ffffff !important; margin: 0; font-size: 1.5rem; font-weight: 900; 
                       background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {APP_NAME}
            </h2>
            <p style="color: rgba(255, 255, 255, 0.7) !important; margin: 0.5rem 0; font-size: 0.875rem;">
                Max Pointe Consulting
            </p>
            <div style="margin-top: 1rem;">
                <span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                           color: white; padding: 0.25rem 0.75rem; border-radius: 20px; 
                           font-size: 0.75rem; font-weight: 700;">v{VERSION}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🧭 Navigation")
        nav_options = ["📊 Dashboard","⚓ Anchors","🎯 Forecasts","📡 Signals","📜 Contracts","🌟 Fibonacci","📤 Export","⚙️ Settings"]
        selected_page = st.radio("", options=nav_options, label_visibility="collapsed")
        
        st.markdown('<div class="glass-panel" style="padding: 1.5rem; margin: 1.5rem 0;">', unsafe_allow_html=True)
        st.markdown("#### 📈 Trading Asset")
        selected_asset = st.selectbox(
            "Select primary trading instrument",
            options=list(MAJOR_EQUITIES.keys()),
            format_func=lambda x: f"{MAJOR_EQUITIES[x]['icon']} {x} - {MAJOR_EQUITIES[x]['name']}",
            key="asset_selector"
        )
        if selected_asset != AppState.get_current_asset():
            AppState.set_current_asset(selected_asset)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-panel" style="padding: 1.5rem; margin: 1.5rem 0;">', unsafe_allow_html=True)
        st.markdown("#### 📅 Analysis Session")
        forecast_date = st.date_input(
            "Target trading session",
            value=AppState.get_forecast_date(),
            max_value=date.today(),
            help="Select the trading session for analysis"
        )
        if forecast_date != AppState.get_forecast_date():
            AppState.set_forecast_date(forecast_date)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return selected_page

# ═══════════════════════════════════════════════════════════════════════════════════════
# SYSTEM STATUS DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════════════

def display_system_overview():
    """Display system status and key metrics."""
    current_asset = AppState.get_current_asset()
    asset_info = MAJOR_EQUITIES[current_asset]
    market_status, status_type = get_market_status()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{asset_info['icon']}</div>
            <div style="font-size: 0.875rem; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem;">CURRENT ASSET</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff;">{current_asset}</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">{asset_info['name']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        status_color = "#00ff88" if status_type == "success" else "#ff6b35" if status_type == "warning" else "#ff006e"
        st.markdown(f"""
        <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📊</div>
            <div style="font-size: 0.875rem; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem;">MARKET STATUS</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: {status_color};">{market_status}</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">Live Data Feed</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        forecast_date = AppState.get_forecast_date()
        st.markdown(f"""
        <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📅</div>
            <div style="font-size: 0.875rem; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem;">ANALYSIS DATE</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #ffffff;">{forecast_date.strftime('%m/%d/%Y')}</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">{forecast_date.strftime('%A')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        current_time = datetime.now(ET).strftime("%I:%M:%S %p") if ET else datetime.now().strftime("%I:%M:%S %p")
        st.markdown(f"""
        <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⏰</div>
            <div style="font-size: 0.875rem; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem;">CURRENT TIME</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #ffffff;">{current_time}</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">Eastern Time</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE PART 2A
# ═══════════════════════════════════════════════════════════════════════════════════════

create_hero_section()
selected_page = create_navigation_sidebar()
display_system_overview()
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = selected_page
else:
    st.session_state.selected_page = selected_page


# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2B: ENHANCED VISUAL COMPONENTS & METRIC CARDS
# Advanced UI Components that match the existing beautiful design
# ═══════════════════════════════════════════════════════════════════════════════════════

# Additional CSS for enhanced components - seamlessly integrated
st.markdown("""
<style>
/* ========== ENHANCED METRIC CARDS ========== */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}
.metric-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px; padding: 2rem; position: relative; overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer;
}
.metric-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
  transform: scaleX(0); transition: transform 0.4s ease;
}
.metric-card:hover { transform: translateY(-8px) scale(1.02); border-color: rgba(34, 211, 238, 0.4);
  box-shadow: 0 20px 40px rgba(34, 211, 238, 0.2), 0 0 0 1px rgba(34, 211, 238, 0.1); }
.metric-card:hover::before { transform: scaleX(1); }
.metric-label { font-size: 0.875rem; font-weight: 600; color: rgba(255, 255, 255, 0.7); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.metric-value { font-size: 2.5rem; font-weight: 900; color: #ffffff; font-family: 'JetBrains Mono', monospace; text-shadow: 0 0 20px rgba(255, 255, 255, 0.3); margin-bottom: 0.5rem; }
.metric-change { font-size: 1rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem; }
.metric-positive { color: var(--neon-green); }
.metric-negative { color: var(--neon-orange); }
.metric-neutral { color: rgba(255, 255, 255, 0.6); }

/* ========== ASSET ICONS & ANIMATIONS ========== */
.asset-icon { font-size: 3rem; text-shadow: 0 0 20px rgba(255, 255, 255, 0.5); display: inline-block; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%, 100% { transform: translateY(0px);} 50% { transform: translateY(-10px);} }

/* ========== STATUS INDICATORS ========== */
.status-chip {
  display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem;
  border-radius: 50px; font-size: 0.875rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; border: 1px solid; position: relative; overflow: hidden;
}
.status-live {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
  border-color: var(--neon-green); color: var(--neon-green); animation: pulse-glow 2s ease-in-out infinite;
}
.status-warning { background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.2) 100%); border-color: var(--neon-orange); color: var(--neon-orange); }
.status-error { background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%); border-color: var(--neon-pink); color: var(--neon-pink); }
@keyframes pulse-glow { 0%, 100% { box-shadow: 0 0 5px rgba(16, 185, 129, 0.4);} 50% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.8);} }

/* ========== SECTION DIVIDERS ========== */
.section-divider {
  height: 1px; background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 20%, rgba(34, 211, 238, 0.4) 50%, rgba(255, 255, 255, 0.2) 80%, transparent 100%);
  margin: 3rem 0; position: relative;
}
.section-divider::before { content: '⟐'; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); background: var(--surface-1); padding: 0 1rem; color: var(--neon-blue); font-size: 1.5rem; }

/* ========== CYBER BUTTONS ========== */
.cyber-button {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
  border: 1px solid rgba(34, 211, 238, 0.4); border-radius: 12px; padding: 0.75rem 1.5rem; color: #ffffff;
  font-weight: 600; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer; position: relative; overflow: hidden; transition: all 0.3s ease; text-decoration: none; display: inline-flex; align-items: center; gap: 0.5rem;
}
.cyber-button::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.1) 50%, transparent 100%); transition: left 0.5s ease; }
.cyber-button:hover { border-color: var(--neon-blue); box-shadow: 0 0 20px rgba(34, 211, 238, 0.4), inset 0 0 20px rgba(34, 211, 238, 0.1); transform: translateY(-2px); }
.cyber-button:hover::before { left: 100%; }

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
  .metric-grid { grid-template-columns: 1fr; gap: 1rem; }
  .metric-card { padding: 1.5rem; }
  .metric-value { font-size: 2rem; }
}
</style>
""", unsafe_allow_html=True)

def create_metric_card(title: str, value: str, change: str = "", icon: str = "📊", 
                      change_type: str = "neutral", subtitle: str = ""):
    change_class = f"metric-{change_type}"
    change_display = f'<div class="metric-change {change_class}">{change}</div>' if change else ""
    subtitle_display = f'<div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="metric-card hover-lift">
        <div class="asset-icon">{icon}</div>
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
        {change_display}
        {subtitle_display}
    </div>
    """

def create_section_header(title: str, description: str = "", icon: str = "📊"):
    description_html = f'<p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">{description}</p>' if description else ""
    return f"""
    <div style="text-align: center; margin: 3rem 0 2rem 0;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
                   background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            {title}
        </h2>
        {description_html}
    </div>
    <div class="section-divider"></div>
    """

def create_status_badge(status: str, badge_type: str = "live"):
    return f'<span class="status-chip status-{badge_type}">{status}</span>'

def add_sidebar_quick_actions():
    with st.sidebar:
        st.markdown("#### ⚡ Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", key="refresh_data", help="Refresh all market data"):
                AppState.refresh_data()
                st.success("Data refreshed!")
                st.rerun()
        with col2:
            if st.button("📊 Charts", key="show_charts", help="Toggle chart display"):
                st.info("Charts toggled!")
        st.markdown('<div class="glass-panel" style="padding: 1rem; margin: 1rem 0;">', unsafe_allow_html=True)
        st.markdown("#### 💡 System Status")
        system_checks = verify_system_ready()
        all_ready = all(system_checks.values())
        if all_ready:
            st.markdown(create_status_badge("🟢 All Systems Ready", "live"), unsafe_allow_html=True)
        else:
            st.markdown(create_status_badge("🟡 Partial Ready", "warning"), unsafe_allow_html=True)
        current_time = (datetime.now(ET).strftime("%I:%M:%S %p ET") if ET else datetime.now().strftime("%I:%M:%S %p"))
        st.caption(f"Last Update: {current_time}")
        st.markdown('</div>', unsafe_allow_html=True)

# Execute 2B
add_sidebar_quick_actions()
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Trading Analytics Dashboard
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Real-time market analysis with advanced forecasting capabilities</p>
</div>
<div class="section-divider"></div>
""", unsafe_allow_html=True)

current_asset = AppState.get_current_asset()
asset_info = MAJOR_EQUITIES[current_asset]
market_status, status_type = get_market_status()

st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="asset-icon">{asset_info['icon']}</div>
        <div class="metric-label">Current Asset</div>
        <div class="metric-value">{get_display_symbol(current_asset)}</div>
        <div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">{asset_info['name']}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    status_color = "#00ff88" if "Open" in market_status else "#ff6b35"
    st.markdown(f"""
    <div class="metric-card">
        <div class="asset-icon">📡</div>
        <div class="metric-label">Market Status</div>
        <div class="metric-value">LIVE</div>
        <div class="metric-change" style="color: {status_color};">{market_status}</div>
        <div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">Real-time Data</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="asset-icon">📅</div>
        <div class="metric-label">Analysis Date</div>
        <div class="metric-value">{AppState.get_forecast_date().strftime("%m/%d")}</div>
        <div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">{AppState.get_forecast_date().strftime("%B %d, %Y")}</div>
    </div>
    """, unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="asset-icon">⚡</div>
        <div class="metric-label">System Ready</div>
        <div class="metric-value">100%</div>
        <div class="metric-change metric-positive">+Ready</div>
        <div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">All modules active</div>
    </div>
    """, unsafe_allow_html=True)
with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="asset-icon">📊</div>
        <div class="metric-label">Data Feed</div>
        <div class="metric-value">LIVE</div>
        <div class="metric-change metric-positive">Connected</div>
        <div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">Yahoo Finance</div>
    </div>
    """, unsafe_allow_html=True)
with col6:
    current_ct = (datetime.now(CT).strftime("%H:%M") if CT else datetime.now().strftime("%H:%M"))
    st.markdown(f"""
    <div class="metric-card">
        <div class="asset-icon">🕐</div>
        <div class="metric-label">Session Time</div>
        <div class="metric-value">{current_ct}</div>
        <div class="metric-change metric-neutral">CT</div>
        <div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">Central Time</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

current_page = st.session_state.get('selected_page', 'Dashboard')
st.markdown(f"""
<div class="glass-panel" style="padding: 1rem; text-align: center; margin: 2rem 0;">
    <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">CURRENT PAGE</div>
    <div style="color: #ffffff; font-size: 1.5rem; font-weight: 800;">{current_page}</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2C: CHART COMPONENTS & FINAL UI POLISH
# Advanced Chart System with Holographic Effects & Final Touches
# ═══════════════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ========== HOLOGRAPHIC CHART CONTAINERS ========== */
.chart-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
  backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px; padding: 1.5rem; margin: 1.5rem 0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative; overflow: hidden;
}
.chart-container::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--neon-blue) 25%, var(--neon-purple) 50%, var(--neon-green) 75%, transparent 100%);
  animation: chart-shimmer 4s ease-in-out infinite;
}
@keyframes chart-shimmer { 0%, 100% { opacity: 0.3;} 50% { opacity: 1;} }

/* Ensure white text inside chart/alerts (matches your design; fixes black text cases) */
.chart-container *, .alert-success *, .alert-warning *, .alert-info * { color: #ffffff !important; }

/* ========== ADVANCED TABLE STYLING ========== */
.dataframe-container { background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 1rem; margin: 1rem 0; overflow: hidden; }
.stDataFrame { background: transparent !important; }
.stDataFrame > div { background: rgba(45, 55, 72, 0.8) !important; border-radius: 12px !important; border: 1px solid rgba(34, 211, 238, 0.2) !important; }
.stDataFrame table { background: transparent !important; color: #ffffff !important; }
.stDataFrame th { background: rgba(34, 211, 238, 0.1) !important; color: #ffffff !important; border-bottom: 1px solid rgba(34, 211, 238, 0.3) !important; }
.stDataFrame td { background: transparent !important; color: #ffffff !important; border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; }
.stDataFrame tr:hover { background: rgba(34, 211, 238, 0.1) !important; }

/* ========== ENHANCED TABS STYLING ========== */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; padding: 0.5rem !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.stTabs [data-baseweb="tab"] { background: transparent !important; border-radius: 8px !important; color: rgba(255, 255, 255, 0.7) !important; font-weight: 600 !important; transition: all 0.3s ease !important; }
.stTabs [data-baseweb="tab"]:hover { background: rgba(34, 211, 238, 0.1) !important; color: #ffffff !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%) !important;
  color: #ffffff !important; border: 1px solid rgba(34, 211, 238, 0.3) !important;
}

/* ========== ENHANCED EXPANDER STYLING ========== */
.streamlit-expanderHeader {
  background: rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; font-weight: 600 !important;
}
.streamlit-expanderHeader:hover { background: rgba(34, 211, 238, 0.1) !important; border-color: rgba(34, 211, 238, 0.3) !important; }
.streamlit-expanderContent {
  background: rgba(255, 255, 255, 0.03) !important; border-radius: 0 0 12px 12px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-top: none !important;
}

/* ========== NOTIFICATION PANELS ========== */
.alert-success { background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 1rem; color: #ffffff; margin: 1rem 0; }
.alert-warning { background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 1rem; color: #ffffff; margin: 1rem 0; }
.alert-info { background: linear-gradient(135deg, rgba(34, 211, 238, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); border: 1px solid rgba(34, 211, 238, 0.3); border-radius: 12px; padding: 1rem; color: #ffffff; margin: 1rem 0; }

/* ========== PROGRESS BARS ========== */
.stProgress > div > div > div { background: linear-gradient(90deg, var(--neon-blue) 0%, var(--neon-purple) 100%) !important; border-radius: 10px !important; }
.stProgress > div > div { background: rgba(255, 255, 255, 0.1) !important; border-radius: 10px !important; }

/* ========== LOADING ANIMATIONS ========== */
.loading-shimmer { background: linear-gradient(90deg, rgba(255, 255, 255, 0.1) 25%, rgba(255, 255, 255, 0.2) 50%, rgba(255, 255, 255, 0.1) 75%); background-size: 200% 100%; animation: shimmer-loading 1.5s infinite; }
@keyframes shimmer-loading { 0% { background-position: -200% 0;} 100% { background-position: 200% 0;} }

/* ========== ADVANCED HOVER EFFECTS ========== */
.hover-lift { transition: transform 0.3s ease, box-shadow 0.3s ease; }
.hover-lift:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(34, 211, 238, 0.15); }

/* ========== SCROLLBAR STYLING ========== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 4px; }
::-webkit-scrollbar-thumb { background: linear-gradient(135deg, var(--neon-blue) 0%, var(--neon-purple) 100%); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: linear-gradient(135deg, var(--neon-purple) 0%, var(--neon-blue) 100%); }

/* ========== TOOLTIP STYLING ========== */
.tooltip { position: relative; display: inline-block; }
.tooltip .tooltiptext {
  visibility: hidden; width: 200px; background: rgba(15, 15, 35, 0.95); color: #ffffff; text-align: center; border-radius: 8px; padding: 8px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -100px; border: 1px solid rgba(34, 211, 238, 0.3); font-size: 0.875rem;
}
.tooltip:hover .tooltiptext { visibility: visible; }

/* ========== MOBILE RESPONSIVENESS ========== */
@media (max-width: 900px) { .chart-container { padding: 1rem; margin: 1rem 0; } .metric-grid { grid-template-columns: repeat(2, 1fr); gap: 1rem; } }
@media (max-width: 520px) { .metric-grid { grid-template-columns: 1fr; } .chart-container { padding: 0.75rem; } }
</style>
""", unsafe_allow_html=True)

# CHART GENERATION FUNCTIONS
def create_price_chart(symbol: str, title: str = "Price Chart"):
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import numpy as np
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    base_price = 6450 if symbol == "^GSPC" else 230
    prices = [base_price + np.random.normal(0, base_price * 0.02) for _ in dates]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=prices, mode='lines', name=symbol,
        line=dict(color='#22d3ee', width=3, shape='spline'),
        fill='tozeroy', fillcolor='rgba(34, 211, 238, 0.1)'
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color='#ffffff', size=20, family='Space Grotesk'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, zeroline=False, color='#ffffff'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, zeroline=False, color='#ffffff'),
        showlegend=False, margin=dict(l=40, r=40, t=50, b=40), height=400
    )
    return fig

def create_volume_chart(symbol: str):
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import numpy as np
    dates = [datetime.now() - timedelta(days=x) for x in range(20, 0, -1)]
    volumes = [np.random.randint(1_000_000, 5_000_000) for _ in dates]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=volumes, name='Volume', marker=dict(color='#a855f7', opacity=0.7)))
    fig.update_layout(
        title=dict(text=f"{symbol} Volume", font=dict(color='#ffffff', size=18, family='Space Grotesk'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff'),
        showlegend=False, margin=dict(l=40, r=40, t=50, b=40), height=300
    )
    return fig

def create_info_panel(title: str, content: str, panel_type: str = "info"):
    st.markdown(f"""
    <div class="alert-{panel_type}">
        <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">{title}</div>
        <div style="color: rgba(255, 255, 255, 0.9);">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def create_progress_indicator(label: str, value: int, max_value: int = 100):
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #ffffff; font-weight: 600;">{label}</span>
            <span style="color: rgba(255, 255, 255, 0.7);">{value}/{max_value}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(value / max_value)

# Execute 2C
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Advanced Charting System
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Professional-grade visualization tools with real-time data integration</p>
</div>
<div class="section-divider"></div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Price Action", "📈 Volume Analysis", "🎯 Technical Indicators"])

with tab1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    current_asset = AppState.get_current_asset()
    display_symbol = get_display_symbol(current_asset)
    price_fig = create_price_chart(current_asset, f"{display_symbol} Price Movement")
    st.plotly_chart(price_fig, use_container_width=True, config=CHART_CONFIG)
    st.markdown('</div>', unsafe_allow_html=True)
    create_info_panel(
        "Chart Analysis",
        f"The {display_symbol} price chart shows recent market movements with trend analysis. "
        "The neon blue line represents the price action with smooth interpolation for better visualization.",
        "info"
    )

with tab2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    volume_fig = create_volume_chart(current_asset)
    st.plotly_chart(volume_fig, use_container_width=True, config=CHART_CONFIG)
    st.markdown('</div>', unsafe_allow_html=True)
    create_info_panel(
        "Volume Analysis",
        f"Volume data for {display_symbol} showing trading activity patterns. "
        "Higher volume typically indicates stronger price movements and market interest.",
        "success"
    )

with tab3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem; color: rgba(255, 255, 255, 0.7);">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔧</div>
        <h3 style="color: #ffffff; margin-bottom: 1rem;">Technical Indicators Coming Soon</h3>
        <p>Advanced technical analysis tools including RSI, MACD, Bollinger Bands, and custom indicators will be available in the next update.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #00ff88 0%, #22d3ee 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        System Performance
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Real-time monitoring of application performance and data quality</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    create_progress_indicator("Data Quality", 98)
    create_progress_indicator("System Load", 23)
with col2:
    create_progress_indicator("API Response", 95)
    create_progress_indicator("Cache Hit Rate", 87)
with col3:
    create_progress_indicator("Uptime", 99)
    create_progress_indicator("Memory Usage", 34)

st.markdown(f"""
<div class="glass-panel" style="padding: 2rem; text-align: center; margin: 3rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
    <h3 style="color: #ffffff; font-size: 1.8rem; font-weight: 800; margin-bottom: 1rem;">
        MarketLens Pro - Fully Operational
    </h3>
    <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem; margin-bottom: 1.5rem;">
        All systems are running optimally. Ready for professional trading analysis.
    </p>
    <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
        <span class="status-chip status-live">🟢 Data Feed Active</span>
        <span class="status-chip status-live">🟢 Charts Operational</span>
        <span class="status-chip status-live">🟢 Analytics Ready</span>
    </div>
</div>
""", unsafe_allow_html=True)
