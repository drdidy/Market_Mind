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

/* ========== APP BACKGROUND ONLY (do not force text colors) ========== */
.stApp {
  background: 
    radial-gradient(circle at 20% 20%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 255, 198, 0.2) 0%, transparent 50%),
    linear-gradient(135deg, #0c0c1e 0%, #1a1a2e 100%);
  min-height: 100vh;
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ===================== MAIN CONTENT CONTAINER ===================== */
/* Keep your glass card look but DO NOT force dark text here */
.main .block-container {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 2rem;
  margin: 1rem;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* Allow text color to inherit from your global fixes (no dark forcing) */
.main .block-container * {
  color: inherit !important;
  -webkit-text-fill-color: inherit !important;
}

/* Keep these components white as you intended */
.main .block-container .hero-container *,
.main .block-container .glass-panel *,
.main .block-container .metric-card * {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

/* Make common widgets readable in MAIN when sitting on dark areas */
div[data-testid="stAppViewContainer"] [data-baseweb="radio"] *,
div[data-testid="stAppViewContainer"] [data-baseweb="select"] *,
div[data-testid="stAppViewContainer"] [data-testid="stDateInput"] *{
  color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
}

/* Popover portals (menus/calendars) are outside main; style globally */
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

/* ========== ANIMATED BACKGROUND PARTICLES ========== */
.stApp::before {
  content: '';
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
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
@keyframes sparkle { from { background-position: 0% 0%; } to { background-position: 250px 300px; } }

/* ========== SIDEBAR STYLING ONLY ========== */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(15, 15, 35, 0.95) 0%, rgba(26, 26, 46, 0.95) 100%) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}
section[data-testid="stSidebar"] > div { background: transparent !important; }

/* Sidebar text readable (keep gradient headings intact) */
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] *:not([style*="-webkit-text-fill-color: transparent"]) {
  -webkit-text-fill-color:#ffffff !important;
}

/* Sidebar controls */
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

/* Date input in sidebar */
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

/* Sidebar buttons */
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
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px; padding: 2.5rem; margin: 2rem 0;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative; overflow: hidden; z-index: 10;
}
.hero-container::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--neon-blue) 20%, var(--neon-purple) 40%, var(--neon-green) 60%, var(--neon-orange) 80%, transparent 100%);
  animation: shimmer 3s ease-in-out infinite;
}
@keyframes shimmer { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
.hero-title {
  font-size: 3.5rem; font-weight: 900;
  background: linear-gradient(135deg, #ffffff 0%, #22d3ee 50%, #a855f7 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  margin: 0; letter-spacing: -0.02em; text-shadow: 0 0 40px rgba(34, 211, 238, 0.4);
  animation: glow-pulse 4s ease-in-out infinite;
}
@keyframes glow-pulse { 0%, 100% { filter: drop-shadow(0 0 10px rgba(34, 211, 238, 0.4)); } 50% { filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.6)); } }
.hero-subtitle { font-size: 1.5rem; font-weight: 600; color: rgba(255, 255, 255, 0.8); margin: 1rem 0; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3); }
.hero-meta { font-size: 1rem; color: rgba(255, 255, 255, 0.6); font-weight: 500; margin-top: 0.5rem; }

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
        # Company branding with neon effect
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

        # Navigation menu
        st.markdown("### 🧭 Navigation")

        nav_options = [
            "📊 Dashboard",
            "⚓ Anchors",
            "🎯 Forecasts",
            "📡 Signals",
            "📜 Contracts",
            "🌟 Fibonacci",
            "📤 Export",
            "⚙️ Settings"
        ]

        selected_page = st.radio(
            "",
            options=nav_options,
            label_visibility="collapsed"
        )

        # Asset selector with enhanced styling
        st.markdown('<div class="glass-panel" style="padding: 1.5rem; margin: 1.5rem 0;">', unsafe_allow_html=True)
        st.markdown("#### 📈 Trading Asset")

        selected_asset = st.selectbox(
            "Select primary trading instrument",
            options=list(MAJOR_EQUITIES.keys()),
            format_func=lambda x: f"{MAJOR_EQUITIES[x]['icon']} {x} - {MAJOR_EQUITIES[x]['name']}",
            key="asset_selector"
        )

        # Update asset if changed
        if selected_asset != AppState.get_current_asset():
            AppState.set_current_asset(selected_asset)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Date selector with proper styling
        st.markdown('<div class="glass-panel" style="padding: 1.5rem; margin: 1.5rem 0;">', unsafe_allow_html=True)
        st.markdown("#### 📅 Analysis Session")

        forecast_date = st.date_input(
            "Target trading session",
            value=AppState.get_forecast_date(),
            max_value=date.today(),
            help="Select the trading session for analysis"
        )

        # Update date if changed
        if forecast_date != AppState.get_forecast_date():
            AppState.set_forecast_date(forecast_date)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # 🔽 SIDEBAR-ONLY TEXT COLOR PATCH (runs last so it wins)
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] * { color:#e5e7eb !important; }
        section[data-testid="stSidebar"] *:not([style*="-webkit-text-fill-color: transparent"]) {
          -webkit-text-fill-color:#e5e7eb !important;
        }
        section[data-testid="stSidebar"] [data-baseweb="radio"] *{
          color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important; opacity:1 !important;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] *{
          color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
        }
        [data-baseweb="menu"], [role="listbox"]{
          background:rgba(17,24,39,.98) !important;
          color:#e5e7eb !important;
          border:1px solid rgba(255,255,255,.12) !important;
        }
        [data-baseweb="menu"] *, [role="listbox"] *{ color:#e5e7eb !important; }
        section[data-testid="stSidebar"] [data-testid="stDateInput"] *{
          color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
        }
        [data-baseweb="datepicker"], [data-baseweb="calendar"],
        [data-baseweb="datepicker"] *, [data-baseweb="calendar"] *{
          color:#e5e7eb !important;
        }
        section[data-testid="stSidebar"] a, section[data-testid="stSidebar"] a *,
        section[data-testid="stSidebar"] .stButton > button, section[data-testid="stSidebar"] .stButton > button *,
        section[data-testid="stSidebar"] .stLinkButton > a, section[data-testid="stSidebar"] .stLinkButton > a *{
          color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important; opacity:1 !important;
        }
        section[data-testid="stSidebar"] [style*="color:#00ff88"],
        section[data-testid="stSidebar"] [style*="color: #00ff88"],
        section[data-testid="stSidebar"] [style*="rgb(0, 255, 136)"]{
          color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
        }
        </style>
        """, unsafe_allow_html=True)

        return selected_page

# ═══════════════════════════════════════════════════════════════════════════════════════
# SYSTEM STATUS DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════════════

def display_system_overview():
    """Display system status and key metrics."""
    current_asset = AppState.get_current_asset()
    asset_info = MAJOR_EQUITIES[current_asset]
    market_status, status_type = get_market_status()
    
    # Create key metrics display
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
            <div style="font-size: 0.875rem; color: rgba(255, 255, 255, 0.7); margin-bottom: 0.5rem;">ANALYSIS DATE</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #ffffff;">{forecast_date.strftime('%m/%d/%Y')}</div>
            <div style="font-size: 0.75rem; color: rgba(255, 255, 255, 0.6); margin-top: 0.5rem;">{forecast_date.strftime('%A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        current_time = datetime.now(ET).strftime("%I:%M:%S %p")
        st.markdown(f"""
        <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⏰</div>
            <div style="font-size: 0.875rem; color: rgba(255, 255, 255, 0.7); margin-bottom: 0.5rem;">CURRENT TIME</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #ffffff;">{current_time}</div>
            <div style="font-size: 0.75rem; color: rgba(255, 255, 255, 0.6); margin-top: 0.5rem;">Eastern Time</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE PART 2A
# ═══════════════════════════════════════════════════════════════════════════════════════

# Create the hero section
create_hero_section()

# Create navigation and get selected page
selected_page = create_navigation_sidebar()

# Display system overview
display_system_overview()

# Store selected page for next parts
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
/* ===== 2B SCOPED TEXT SAFETY PATCH (keeps text readable on all pages) ===== */
/* Ensure anything inside metric cards / glass panels is light text by default,
   without touching the rest of your app. Only kicks in when child elements
   don't already declare a color inline. */
.main .block-container .metric-card,
.main .block-container .glass-panel{
  color:#e5e7eb !important;
}
.main .block-container .metric-card *:not([style*="color"]),
.main .block-container .glass-panel *:not([style*="color"]){
  color:#e5e7eb !important;
  -webkit-text-fill-color:#e5e7eb !important;
}

/* ========== ENHANCED METRIC CARDS ========== */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.metric-card {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 2rem;
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
  transform: scaleX(0);
  transition: transform 0.4s ease;
}

.metric-card:hover {
  transform: translateY(-8px) scale(1.02);
  border-color: rgba(34, 211, 238, 0.4);
  box-shadow: 
    0 20px 40px rgba(34, 211, 238, 0.2),
    0 0 0 1px rgba(34, 211, 238, 0.1);
}

.metric-card:hover::before {
  transform: scaleX(1);
}

.metric-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7) !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.metric-value {
  font-size: 2.5rem;
  font-weight: 900;
  color: #ffffff !important;
  font-family: 'JetBrains Mono', monospace;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
  margin-bottom: 0.5rem;
}

.metric-change {
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  /* Note: color comes from modifier classes or inline styles you set. */
}

.metric-positive { color: var(--neon-green) !important; }
.metric-negative { color: var(--neon-orange) !important; }
.metric-neutral  { color: rgba(255, 255, 255, 0.75) !important; }

/* ========== ASSET ICONS & ANIMATIONS ========== */
.asset-icon {
  font-size: 3rem;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
  display: inline-block;
  animation: float 3s ease-in-out infinite;
  color:#ffffff !important; /* keep emoji text visible if it falls back to glyph */
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

/* ========== STATUS INDICATORS ========== */
.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border: 1px solid;
  position: relative;
  overflow: hidden;
  color:#e5e7eb !important; /* default safety */
}

.status-live {
  background: linear-gradient(135deg, 
    rgba(16, 185, 129, 0.2) 0%, 
    rgba(5, 150, 105, 0.2) 100%);
  border-color: var(--neon-green);
  color: var(--neon-green) !important;
  animation: pulse-glow 2s ease-in-out infinite;
}

.status-warning {
  background: linear-gradient(135deg, 
    rgba(245, 158, 11, 0.2) 0%, 
    rgba(217, 119, 6, 0.2) 100%);
  border-color: var(--neon-orange);
  color: var(--neon-orange) !important;
}

.status-error {
  background: linear-gradient(135deg, 
    rgba(239, 68, 68, 0.2) 0%, 
    rgba(220, 38, 38, 0.2) 100%);
  border-color: var(--neon-pink);
  color: var(--neon-pink) !important;
}

@keyframes pulse-glow {
  0%, 100% { 
    box-shadow: 0 0 5px rgba(16, 185, 129, 0.4);
  }
  50% { 
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.8);
  }
}

/* ========== SECTION DIVIDERS ========== */
.section-divider {
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.2) 20%, 
    rgba(34, 211, 238, 0.4) 50%,
    rgba(255, 255, 255, 0.2) 80%, 
    transparent 100%);
  margin: 3rem 0;
  position: relative;
}

.section-divider::before {
  content: '⟐';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  /* fallback if --surface-1 isn't defined on this page */
  background: var(--surface-1, rgba(15,15,35,0.95));
  padding: 0 1rem;
  color: var(--neon-blue);
  font-size: 1.5rem;
}

/* ========== CYBER BUTTONS ========== */
.cyber-button {
  background: linear-gradient(135deg, 
    rgba(34, 211, 238, 0.2) 0%, 
    rgba(168, 85, 247, 0.2) 100%);
  border: 1px solid rgba(34, 211, 238, 0.4);
  border-radius: 12px;
  padding: 0.75rem 1.5rem;
  color: #ffffff !important;
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.cyber-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.1) 50%, 
    transparent 100%);
  transition: left 0.5s ease;
}

.cyber-button:hover {
  border-color: var(--neon-blue);
  box-shadow: 
    0 0 20px rgba(34, 211, 238, 0.4),
    inset 0 0 20px rgba(34, 211, 238, 0.1);
  transform: translateY(-2px);
}

.cyber-button:hover::before {
  left: 100%;
}

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
  .metric-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .metric-card {
    padding: 1.5rem;
  }
  
  .metric-value {
    font-size: 2rem;
  }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# ENHANCED METRIC CARD FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_metric_card(title: str, value: str, change: str = "", icon: str = "📊", 
                      change_type: str = "neutral", subtitle: str = ""):
    """Create a beautiful metric card with glassmorphism design."""
    
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
    """Create a beautiful section header with neon styling."""
    
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
    """Create a status badge with neon styling."""
    
    return f'<span class="status-chip status-{badge_type}">{status}</span>'

# ═══════════════════════════════════════════════════════════════════════════════════════
# ENHANCED DATA VISUALIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_live_price_display(symbol: str, price: float, change: float, change_pct: float):
    """Create a live price display with animated elements."""
    
    change_color = "#00ff88" if change >= 0 else "#ff6b35"
    change_icon = "↗" if change >= 0 else "↘"
    
    asset_info = MAJOR_EQUITIES.get(symbol, {"icon": "📊", "name": symbol})
    
    return f"""
    <div class="glass-panel" style="padding: 2rem; text-align: center; margin: 1rem 0;">
        <div class="asset-icon" style="font-size: 4rem; margin-bottom: 1rem;">{asset_info['icon']}</div>
        <h1 style="color: #ffffff; font-size: 3rem; margin: 0; font-family: 'JetBrains Mono', monospace;">
            ${price:,.2f}
        </h1>
        <div style="color: {change_color}; font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">
            {change_icon} ${change:+.2f} ({change_pct:+.2f}%)
        </div>
        <div style="color: rgba(255,255,255,0.7); font-size: 1rem;">
            {symbol} • {asset_info['name']}
        </div>
    </div>
    """

def create_quick_stats_grid(stats_data: list):
    """Create a grid of quick statistics with neon styling."""
    
    html = '<div class="metric-grid">'
    
    for stat in stats_data:
        html += create_metric_card(
            title=stat.get('title', 'Metric'),
            value=stat.get('value', '—'),
            change=stat.get('change', ''),
            icon=stat.get('icon', '📊'),
            change_type=stat.get('change_type', 'neutral'),
            subtitle=stat.get('subtitle', '')
        )
    
    html += '</div>'
    
    return html

# ═══════════════════════════════════════════════════════════════════════════════════════
# SIDEBAR ENHANCEMENTS
# ═══════════════════════════════════════════════════════════════════════════════════════

def add_sidebar_quick_actions():
    """Add quick action buttons to sidebar."""
    
    with st.sidebar:
        # Quick actions section
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
        
        # System status
        st.markdown('<div class="glass-panel" style="padding: 1rem; margin: 1rem 0;">', unsafe_allow_html=True)
        st.markdown("#### 💡 System Status")
        
        # Check system readiness
        system_checks = verify_system_ready()
        all_ready = all(system_checks.values())
        
        if all_ready:
            st.markdown(create_status_badge("🟢 All Systems Ready", "live"), unsafe_allow_html=True)
        else:
            st.markdown(create_status_badge("🟡 Partial Ready", "warning"), unsafe_allow_html=True)
        
        # Show current time
        current_time = datetime.now(ET).strftime("%I:%M:%S %p ET")
        st.caption(f"Last Update: {current_time}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE PART 2B COMPONENTS - USING DIRECT STREAMLIT RENDERING
# ═══════════════════════════════════════════════════════════════════════════════════════

# Add quick actions to sidebar
add_sidebar_quick_actions()

# Display section header for main content
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

# Create enhanced stats using existing data - DIRECT RENDERING
current_asset = AppState.get_current_asset()
asset_info = MAJOR_EQUITIES[current_asset]
market_status, status_type = get_market_status()

# Enhanced stats grid with direct Streamlit components
st.markdown('<div class="metric-grid">', unsafe_allow_html=True)

# Create individual metric cards using columns
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

# Second row
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
    st.markdown(f"""
    <div class="metric-card">
        <div class="asset-icon">🕐</div>
        <div class="metric-label">Session Time</div>
        <div class="metric-value">{datetime.now(CT).strftime("%H:%M")}</div>
        <div class="metric-change metric-neutral">CT</div>
        <div style="font-size: 0.875rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">Central Time</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Add a section for displaying selected page navigation
current_page = st.session_state.get('selected_page', 'Dashboard')

# Page indicator with proper HTML rendering
st.markdown(f"""
<div class="glass-panel" style="padding: 1rem; text-align: center; margin: 2rem 0;">
    <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">CURRENT PAGE</div>
    <div style="color: #ffffff; font-size: 1.5rem; font-weight: 800;">{current_page}</div>
</div>
""", unsafe_allow_html=True)







# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2C (MERGED 2C1 + 2C2): REAL DATA CHARTS, VOLUME & TECHNICALS
# Yahoo Finance integration (incl. ES=F) + Asian Session swing high/low (CT 17:00–20:00)
# ═══════════════════════════════════════════════════════════════════════════════════════

# ---------- CSS for chart containers ----------
st.markdown("""
<style>
.chart-container {
  background: linear-gradient(135deg, rgba(255,255,255,.08) 0%, rgba(255,255,255,.03) 100%);
  backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255,255,255,.12); border-radius: 20px;
  padding: 1.5rem; margin: 1.5rem 0; box-shadow: 0 8px 32px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.1);
  position: relative; overflow: hidden;
}
.chart-container::before{
  content:''; position:absolute; top:0; left:0; right:0; height:1px;
  background:linear-gradient(90deg, transparent 0%, var(--neon-blue) 25%, var(--neon-purple) 50%, var(--neon-green) 75%, transparent 100%);
  animation: chart-shimmer 4s ease-in-out infinite;
}
@keyframes chart-shimmer { 0%,100%{opacity:.3;} 50%{opacity:1;} }

.chart-container *, .chart-container h1, .chart-container h2, .chart-container h3, 
.chart-container p, .chart-container div { color:#ffffff !important; }

/* tab styling */
.stTabs [data-baseweb="tab-list"]{ background:rgba(255,255,255,.05)!important; border-radius:12px!important; padding:.5rem!important; border:1px solid rgba(255,255,255,.1)!important; }
.stTabs [data-baseweb="tab"]{ background:transparent!important; border-radius:8px!important; color:rgba(255,255,255,.7)!important; font-weight:600!important; transition:all .3s ease!important; }
.stTabs [data-baseweb="tab"]:hover{ background:rgba(34,211,238,.1)!important; color:#fff!important; }
.stTabs [data-baseweb="tab"][aria-selected="true"]{ background:linear-gradient(135deg, rgba(34,211,238,.2) 0%, rgba(168,85,247,.2) 100%)!important; color:#fff!important; border:1px solid rgba(34,211,238,.3)!important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# REAL DATA HELPERS (HARDENED)
# ═══════════════════════════════════════════════════════════════════════════════════════

def _ensure_1d_series_from_col(frame: pd.DataFrame, key_hint: str = "Close") -> pd.Series:
    """
    Return a 1-D numeric Series for a given price column even if Yahoo returns MultiIndex
    or duplicates. Falls back to the first numeric column if needed.
    """
    if key_hint in frame.columns:
        col = frame[key_hint]
        if isinstance(col, pd.DataFrame):
            # choose the first subcolumn
            col = col.iloc[:, 0]
        return pd.to_numeric(col, errors="coerce")
    # MultiIndex case like ('Close', 'SYMBOL')
    if isinstance(frame.columns, pd.MultiIndex):
        # If first level contains key_hint, take that block's first column
        lvl0 = frame.columns.get_level_values(0)
        if key_hint in set(lvl0):
            sub = frame[key_hint]
            if isinstance(sub, pd.DataFrame):
                sub = sub.iloc[:, 0]
            return pd.to_numeric(sub, errors="coerce")
    # Fallback: look for a column whose name contains 'close'
    for c in frame.columns:
        if isinstance(c, str) and "close" in c.lower():
            col = frame[c]
            if isinstance(col, pd.DataFrame):
                col = col.iloc[:, 0]
            return pd.to_numeric(col, errors="coerce")
    # Last fallback: first numeric-looking column
    for c in frame.columns:
        s = pd.to_numeric(frame[c], errors="coerce")
        if isinstance(s, pd.Series) and s.notna().any():
            return s
    return pd.Series(dtype="float64")

@st.cache_data(ttl=180, show_spinner=False)
def fetch_real_price_data(symbol: str) -> dict:
    """Daily snapshot: last close vs prior close; works for ES=F too."""
    try:
        df = yf.download(symbol, period="5d", interval="1d",
                         progress=False, auto_adjust=False, threads=False, group_by="column")
        if df is None or df.empty:
            return {"status": "error", "error": "No daily data available"}
        df = df.dropna(how="any")

        close = _ensure_1d_series_from_col(df, "Close").dropna()
        if close.empty:
            return {"status": "error", "error": "Close series empty"}

        current_price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(close) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0.0

        vol = df.get("Volume", pd.Series(dtype="float64"))
        if isinstance(vol, pd.DataFrame):
            vol = vol.iloc[:, 0]
        vol = pd.to_numeric(vol, errors="coerce")
        volume = int(vol.iloc[-1]) if not vol.empty and pd.notna(vol.iloc[-1]) else 0

        return {"status": "success", "price": current_price, "change": change,
                "change_pct": change_pct, "volume": volume}
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_chart_data(symbol: str, period: str = "1mo") -> pd.DataFrame:
    """Daily history for charts and metrics (normalized)."""
    try:
        df = yf.download(symbol, period=period, interval="1d",
                         progress=False, auto_adjust=False, threads=False, group_by="column")
        if df is None or df.empty:
            return pd.DataFrame()
        # If MultiIndex columns, collapse to first series per OHLCV key
        if isinstance(df.columns, pd.MultiIndex):
            new_df = pd.DataFrame(index=df.index)
            for top in df.columns.get_level_values(0).unique():
                try:
                    sub = df[top]
                    if isinstance(sub, pd.DataFrame):
                        new_df[top] = pd.to_numeric(sub.iloc[:, 0], errors="coerce")
                    else:
                        new_df[top] = pd.to_numeric(sub, errors="coerce")
                except Exception:
                    pass
            df = new_df
        df = df.dropna(how="any").reset_index()  # has 'Date'
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_intraday_ct(symbol: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    """Intraday bars (converted to CT). Good for ES Asian session slicing."""
    try:
        df = yf.download(symbol, period=period, interval=interval,
                         progress=False, auto_adjust=False, threads=False, group_by="column")
        if df is None or df.empty:
            return pd.DataFrame()
        idx = df.index
        if getattr(idx, "tz", None) is None:
            idx = idx.tz_localize("UTC")
        idx = idx.tz_convert(str(CT))
        df.index = idx
        return df.dropna(how="any")
    except Exception:
        return pd.DataFrame()

# ═══════════════════════════════════════════════════════════════════════════════════════
# PRICE CHART (DAILY)
# ═══════════════════════════════════════════════════════════════════════════════════════

def build_real_price_chart(symbol: str, title: str):
    df = fetch_chart_data(symbol, period="1mo")
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"⚠️ Unable to load real data for {symbol}",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#ff6b35", size=18))
        fig.update_layout(title=f"{title} - Data Unavailable",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#ffffff"), height=400)
        return fig

    close = _ensure_1d_series_from_col(df, "Close")
    ma20 = close.rolling(20, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=close, mode="lines", name=f"{symbol} Price",
                             line=dict(color="#22d3ee", width=3),
                             hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Price: $%{y:,.2f}<extra></extra>"))
    if ma20.notna().sum() > 0:
        fig.add_trace(go.Scatter(x=df["Date"], y=ma20,
                                 mode="lines", name="20-Day Average",
                                 line=dict(color="#ff6b35", width=2, dash="dot"),
                                 hovertemplate="<b>%{x|%Y-%m-%d}</b><br>MA20: $%{y:,.2f}<extra></extra>"))

    valid = close.dropna()
    pmin = float(valid.min()) if len(valid) else 0.0
    pmax = float(valid.max()) if len(valid) else 1.0
    pad = (pmax - pmin) * 0.05
    if not np.isfinite(pad) or pad <= 0:
        pad = max(pmax * 0.005, 1.0)

    fig.update_layout(
        title=dict(text=f"{title} (Live Yahoo Finance Data)", font=dict(color="#ffffff", size=18), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)", showgrid=True, color="#ffffff"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)", showgrid=True, color="#ffffff",
                   range=[pmin - pad, pmax + pad], tickformat="$,.2f"),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0.7)", bordercolor="rgba(255,255,255,0.3)", borderwidth=1, font=dict(color="#ffffff")),
        margin=dict(l=60, r=40, t=60, b=40),
        height=400,
    )
    return fig

# ═══════════════════════════════════════════════════════════════════════════════════════
# TECHNICALS (RSI, MACD, BB) — Robust against MultiIndex/short history
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def fetch_technical_data(symbol: str) -> pd.DataFrame:
    try:
        df = yf.download(symbol, period="6mo", interval="1d",
                         progress=False, auto_adjust=False, threads=False, group_by="column")
        if df is None or df.empty:
            return pd.DataFrame()
        # Collapse MultiIndex to first subcolumn per OHLCV
        if isinstance(df.columns, pd.MultiIndex):
            new_df = pd.DataFrame(index=df.index)
            for top in df.columns.get_level_values(0).unique():
                try:
                    sub = df[top]
                    if isinstance(sub, pd.DataFrame):
                        new_df[top] = pd.to_numeric(sub.iloc[:, 0], errors="coerce")
                    else:
                        new_df[top] = pd.to_numeric(sub, errors="coerce")
                except Exception:
                    pass
            df = new_df
        return df.dropna(how="any").reset_index()
    except Exception:
        return pd.DataFrame()

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()

    # SAFELY get close as 1-D Series
    close = _ensure_1d_series_from_col(out, "Close")
    # keep a canonical Close column for downstream charts
    out["Close"] = close

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).rolling(14, min_periods=14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    out["MACD"] = exp1 - exp2
    out["MACD_signal"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["MACD_histogram"] = out["MACD"] - out["MACD_signal"]

    # Bollinger
    mid = close.rolling(20, min_periods=20).mean()
    sd = close.rolling(20, min_periods=20).std()
    out["BB_middle"] = mid
    out["BB_upper"] = mid + 2 * sd
    out["BB_lower"] = mid - 2 * sd

    return out

def build_technical_chart(symbol: str):
    from plotly.subplots import make_subplots
    df = fetch_technical_data(symbol)
    if df.empty:
        fig = make_subplots(rows=1, cols=1)
        fig.add_annotation(text=f"⚠️ Unable to load technical data for {symbol}",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#ff6b35", size=18))
        fig.update_layout(title=f"{symbol} Technical Analysis - Data Error",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#ffffff"), height=600)
        return fig, {}

    df = calculate_technical_indicators(df)
    close_series = _ensure_1d_series_from_col(df, "Close")

    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.08,
                        row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=[f"{symbol} Price & Bollinger Bands",
                                        f"{symbol} RSI", f"{symbol} MACD"])

    # Price + BB
    fig.add_trace(go.Scatter(x=df["Date"], y=close_series, mode="lines", name="Price",
                             line=dict(color="#22d3ee", width=2),
                             hovertemplate="Price: $%{y:,.2f}<extra></extra>"), row=1, col=1)
    if "BB_upper" in df and df["BB_upper"].notna().any():
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_upper"], mode="lines", name="BB Upper",
                                 line=dict(color="#a855f7", width=1),
                                 hovertemplate="BB Upper: $%{y:,.2f}<extra></extra>"), row=1, col=1)
    if "BB_lower" in df and df["BB_lower"].notna().any():
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_lower"], mode="lines", name="BB Lower",
                                 line=dict(color="#a855f7", width=1), fill="tonexty",
                                 fillcolor="rgba(168,85,247,.1)",
                                 hovertemplate="BB Lower: $%{y:,.2f}<extra></extra>"), row=1, col=1)

    # RSI
    if "RSI" in df and df["RSI"].notna().any():
        fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], mode="lines", name="RSI",
                                 line=dict(color="#00ff88", width=2),
                                 hovertemplate="RSI: %{y:.1f}<extra></extra>"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(255,107,53,.7)", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="rgba(0,255,136,.7)", row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="rgba(255,255,255,.3)", row=2, col=1)

    # MACD
    if "MACD" in df and df["MACD"].notna().any():
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], mode="lines", name="MACD",
                                 line=dict(color="#22d3ee", width=2),
                                 hovertemplate="MACD: %{y:.3f}<extra></extra>"), row=3, col=1)
    if "MACD_signal" in df and df["MACD_signal"].notna().any():
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD_signal"], mode="lines", name="Signal",
                                 line=dict(color="#ff6b35", width=2),
                                 hovertemplate="Signal: %{y:.3f}<extra></extra>"), row=3, col=1)
    if "MACD_histogram" in df and df["MACD_histogram"].notna().any():
        colors = ["#00ff88" if x >= 0 else "#ff006e" for x in df["MACD_histogram"].fillna(0)]
        fig.add_trace(go.Bar(x=df["Date"], y=df["MACD_histogram"], name="Histogram",
                             marker_color=colors, opacity=0.6,
                             hovertemplate="Histogram: %{y:.4f}<extra></extra>"), row=3, col=1)

    fig.update_layout(
        title=dict(text=f"{symbol} Technical Analysis (Live Yahoo Finance Data)",
                   font=dict(color="#ffffff", size=18), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0.7)", bordercolor="rgba(255,255,255,.3)", borderwidth=1,
                    font=dict(color="#ffffff")),
        height=600, margin=dict(l=60, r=40, t=80, b=40)
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,.1)", showgrid=True, color="#ffffff")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.1)", showgrid=True, color="#ffffff")
    fig.update_yaxes(tickformat="$,.2f", row=1, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    current_values = {}
    if len(df) > 0:
        # use safe getters everywhere
        rsi_val = float(df["RSI"].iloc[-1]) if "RSI" in df and pd.notna(df["RSI"].iloc[-1]) else 50.0
        macd_val = float(df["MACD"].iloc[-1]) if "MACD" in df and pd.notna(df["MACD"].iloc[-1]) else 0.0
        macd_sig = float(df["MACD_signal"].iloc[-1]) if "MACD_signal" in df and pd.notna(df["MACD_signal"].iloc[-1]) else 0.0
        price_val = float(close_series.iloc[-1]) if len(close_series) else 0.0
        bb_u = float(df["BB_upper"].iloc[-1]) if "BB_upper" in df and pd.notna(df["BB_upper"].iloc[-1]) else 0.0
        bb_l = float(df["BB_lower"].iloc[-1]) if "BB_lower" in df and pd.notna(df["BB_lower"].iloc[-1]) else 0.0
        current_values = {"rsi": rsi_val, "macd": macd_val, "macd_signal": macd_sig,
                          "price": price_val, "bb_upper": bb_u, "bb_lower": bb_l}
    return fig, current_values

# ═══════════════════════════════════════════════════════════════════════════════════════
# ES ASIAN SESSION SWING HIGH/LOW (CT 17:00–20:00 previous day)
# ═══════════════════════════════════════════════════════════════════════════════════════

def _asian_window_datetimes(ref_session_date: date) -> Tuple[datetime, datetime]:
    prior = ref_session_date - timedelta(days=1)
    start_dt = datetime.combine(prior, ASIAN_START, tzinfo=CT)   # 17:00 CT prev day
    end_dt   = datetime.combine(prior, ASIAN_END, tzinfo=CT)     # 20:00 CT prev day
    return start_dt, end_dt

def compute_asian_high_low_for_es(ref_session_date: date) -> Tuple[Optional[float], Optional[float], pd.DataFrame]:
    df = fetch_intraday_ct(ES_SYMBOL, period="5d", interval="5m")
    if df.empty:
        return None, None, pd.DataFrame()

    start_dt, end_dt = _asian_window_datetimes(ref_session_date)
    slice_df = df.loc[(df.index >= start_dt) & (df.index <= end_dt)]
    if slice_df.empty:
        start_dt2, end_dt2 = _asian_window_datetimes(ref_session_date - timedelta(days=1))
        slice_df = df.loc[(df.index >= start_dt2) & (df.index <= end_dt2)]

    if slice_df.empty:
        return None, None, pd.DataFrame()

    high_series = slice_df.get("High", slice_df.get("Close"))
    low_series  = slice_df.get("Low",  slice_df.get("Close"))
    if isinstance(high_series, pd.DataFrame): high_series = high_series.iloc[:, 0]
    if isinstance(low_series, pd.DataFrame):  low_series  = low_series.iloc[:, 0]
    high = pd.to_numeric(high_series, errors="coerce").dropna()
    low  = pd.to_numeric(low_series,  errors="coerce").dropna()

    if high.empty or low.empty:
        return None, None, slice_df

    return float(high.max()), float(low.min()), slice_df

def build_es_intraday_with_asian_levels(symbol_for_title: str, ref_session_date: date):
    swing_high, swing_low, asian_df = compute_asian_high_low_for_es(ref_session_date)
    intra = fetch_intraday_ct(ES_SYMBOL, period="3d", interval="5m")
    fig = go.Figure()

    if intra.empty:
        fig.add_annotation(text="⚠️ ES intraday data unavailable", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(color="#ff6b35", size=18))
    else:
        price = intra.get("Close", None)
        if isinstance(price, pd.DataFrame):
            price = price.iloc[:, 0]
        fig.add_trace(go.Scatter(x=intra.index, y=price, mode="lines", name="ES=F (Close)",
                                 line=dict(color="#22d3ee", width=2),
                                 hovertemplate="%{x|%Y-%m-%d %H:%M CT}<br>Price: $%{y:,.2f}<extra></extra>"))

    if asian_df is not None and not asian_df.empty and swing_high is not None and swing_low is not None:
        fig.add_vrect(x0=asian_df.index.min(), x1=asian_df.index.max(),
                      fillcolor="rgba(168,85,247,.08)", line_width=0, layer="below")
        fig.add_hline(y=swing_high, line_color="#a855f7", line_dash="dash",
                      annotation_text="Asian High", annotation_position="top left")
        fig.add_hline(y=swing_low, line_color="#a855f7", line_dash="dash",
                      annotation_text="Asian Low", annotation_position="bottom left")

    fig.update_layout(
        title=dict(text=f"ES Asian Session Swing Levels (Proxy for {symbol_for_title})",
                   font=dict(color="#ffffff", size=18), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"),
        xaxis=dict(gridcolor="rgba(255,255,255,.1)", showgrid=True, color="#ffffff"),
        yaxis=dict(gridcolor="rgba(255,255,255,.1)", showgrid=True, color="#ffffff", tickformat="$,.2f"),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,.7)", bordercolor="rgba(255,255,255,.3)", borderwidth=1, font=dict(color="#ffffff")),
        margin=dict(l=60, r=40, t=60, b=40),
        height=420,
    )
    return fig, swing_high, swing_low

# ═══════════════════════════════════════════════════════════════════════════════════════
# SECTION HEADER
# ═══════════════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="text-align:center; margin:3rem 0 2rem 0;">
  <div style="font-size:3rem; margin-bottom:1rem;">📈</div>
  <h2 style="color:#fff; font-size:2.5rem; font-weight:900; margin:0;
             background:linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
    Live Market Charts
  </h2>
  <p style="color:rgba(255,255,255,.8); font-size:1.1rem; margin:.5rem 0 0;">
    Real-time data visualization powered by Yahoo Finance
  </p>
</div>
<div style="height:1px; background:linear-gradient(90deg, transparent 0%, rgba(255,255,255,.2) 20%, rgba(34,211,238,.4) 50%, rgba(255,255,255,.2) 80%, transparent 100%); margin:3rem 0;"></div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════════════

current_asset = AppState.get_current_asset()
display_symbol = get_display_symbol(current_asset)

tab1, tab2, tab3 = st.tabs(["📊 Price Action", "📈 Volume Analysis", "🎯 Technical & Asian Session"])

# ── TAB 1: PRICE ACTION
with tab1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    price_chart = build_real_price_chart(current_asset, f"{display_symbol} Price Movement")
    st.plotly_chart(price_chart, use_container_width=True, config=CHART_CONFIG)
    st.markdown('</div>', unsafe_allow_html=True)

    live = fetch_real_price_data(current_asset)
    if live["status"] == "success":
        price = live["price"]; ch = live["change"]; chp = live["change_pct"]
        c = "#00ff88" if ch >= 0 else "#ff6b35"
        word = "positive" if ch >= 0 else "negative"
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, rgba(16,185,129,.1) 0%, rgba(5,150,105,.1) 100%);
                    border:1px solid rgba(16,185,129,.3); border-radius:12px; padding:1.5rem; margin:1rem 0;">
          <div style="font-weight:700; font-size:1.1rem; margin-bottom:.5rem; color:#fff;">📊 Live Price Analysis</div>
          <div style="color:rgba(255,255,255,.9); line-height:1.6;">
            <strong>{display_symbol}</strong> is currently <strong>${price:,.2f}</strong> with a
            <span style="color:{c}; font-weight:700;">{word}</span> move of
            <strong style="color:{c};">{ch:+.2f} ({chp:+.2f}%)</strong> vs prior close.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, rgba(245,158,11,.1) 0%, rgba(217,119,6,.1) 100%);
                    border:1px solid rgba(245,158,11,.3); border-radius:12px; padding:1.5rem; margin:1rem 0;">
          <div style="font-weight:700; font-size:1.1rem; margin-bottom:.5rem; color:#fff;">⚠️ Data Connection Issue</div>
          <div style="color:rgba(255,255,255,.9);">Unable to fetch data for <strong>{display_symbol}</strong>. Error: {live.get('error','Unknown')}.</div>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 2: VOLUME ANALYSIS (robust math: all floats/ints, no ambiguous truth)
with tab2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    hist = fetch_chart_data(current_asset, period="1mo")
    live = fetch_real_price_data(current_asset)

    if not hist.empty and "Volume" in hist.columns and live["status"] == "success":
        vol = hist["Volume"]
        if isinstance(vol, pd.DataFrame): vol = vol.iloc[:, 0]
        vol = pd.to_numeric(vol, errors="coerce").dropna()

        current_volume = int(live.get("volume", 0) or 0)
        avg_volume = int(vol.mean()) if not vol.empty else 0

        if len(vol) >= 10:
            recent_mean = float(vol.tail(5).mean())
            previous_mean = float(vol.iloc[-10:-5].mean())
            volume_trend = float(((recent_mean - previous_mean) / previous_mean) * 100) if previous_mean > 0 else 0.0
        else:
            volume_trend = 0.0

        relative_volume = (current_volume / avg_volume) if avg_volume > 0 else None

        def fmt_int(x): 
            try: return f"{int(x):,}"
            except: return "—"
        def fmt_pct(x):
            try: return f"{float(x):+.1f}%"
            except: return "—"

        st.markdown(f"""
        <div style="text-align:center; padding:1rem 0 1.5rem 0;">
          <div style="font-size:2.25rem; margin-bottom:.25rem;">📊</div>
          <h3 style="color:#fff; margin:0; font-weight:800;">Live Volume Analysis - {display_symbol}</h3>
          <p style="color:rgba(255,255,255,.8); margin:.5rem 0 0;">Real-time participation metrics</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="glass-panel" style="padding:1.25rem; text-align:center;">
              <div style="color:rgba(255,255,255,.7); font-size:.875rem; margin-bottom:.5rem; font-weight:600;">CURRENT VOLUME</div>
              <div style="color:#a855f7; font-size:1.8rem; font-weight:800;">{fmt_int(current_volume)}</div>
              <div style="color:rgba(255,255,255,.6); font-size:.75rem; margin-top:.5rem;">shares traded today</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            tcolor = "#00ff88" if volume_trend >= 0 else "#ff6b35"
            st.markdown(f"""
            <div class="glass-panel" style="padding:1.25rem; text-align:center;">
              <div style="color:rgba(255,255,255,.7); font-size:.875rem; margin-bottom:.5rem; font-weight:600;">VOLUME TREND</div>
              <div style="color:{tcolor}; font-size:1.8rem; font-weight:800;">{fmt_pct(volume_trend)}</div>
              <div style="color:rgba(255,255,255,.6); font-size:.75rem; margin-top:.5rem;">5-day vs prior 5-day</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            if relative_volume is None:
                rel_val = "—"; rel_color = "#a855f7"
            else:
                rel_val = f"{relative_volume:.1f}x"
                rel_color = "#ff6b35" if relative_volume > 2.0 else ("#00ff88" if relative_volume > 1.2 else "#a855f7")
            st.markdown(f"""
            <div class="glass-panel" style="padding:1.25rem; text-align:center;">
              <div style="color:rgba(255,255,255,.7); font-size:.875rem; margin-bottom:.5rem; font-weight:600;">RELATIVE VOLUME</div>
              <div style="color:{rel_color}; font-size:1.8rem; font-weight:800;">{rel_val}</div>
              <div style="color:rgba(255,255,255,.6); font-size:.75rem; margin-top:.5rem;">vs 30-day average</div>
            </div>
            """, unsafe_allow_html=True)

        if relative_volume is None:
            analysis = "Insufficient recent volume history to compute relative participation."
            panel_type = "info"
        elif relative_volume > 2.5:
            analysis = f"Exceptionally high volume at {relative_volume:.1f}x suggests major institutional activity."
            panel_type = "warning"
        elif relative_volume > 1.5:
            analysis = f"Above-average volume at {relative_volume:.1f}x indicates strong market interest."
            panel_type = "success"
        elif relative_volume < 0.5:
            analysis = f"Below-average volume at {relative_volume:.1f}x suggests low participation."
            panel_type = "info"
        else:
            analysis = f"Normal volume levels at {relative_volume:.1f}x indicate typical participation."
            panel_type = "info"

        panel_colors = {
            "success": ("rgba(16,185,129,.1)", "rgba(16,185,129,.3)"),
            "warning": ("rgba(245,158,11,.1)", "rgba(245,158,11,.3)"),
            "info":    ("rgba(34,211,238,.1)", "rgba(34,211,238,.3)"),
        }
        bgc, brc = panel_colors[panel_type]
        st.markdown(f"""
        <div style="background:{bgc}; border:1px solid {brc}; border-radius:12px; padding:1.25rem; margin:1.25rem 0;">
          <div style="font-weight:700; font-size:1.05rem; margin-bottom:.5rem; color:#fff;">📊 Live Volume Insights</div>
          <div style="color:rgba(255,255,255,.9); line-height:1.6;">
            <strong>{display_symbol}</strong> volume: {fmt_int(current_volume)} today vs {fmt_int(avg_volume)} 30-day avg.
            {analysis} Trend last 5 sessions: {fmt_pct(volume_trend)}.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center; padding:3rem;">
          <div style="font-size:4rem; margin-bottom:1rem; color:#ff6b35;">⚠️</div>
          <h3 style="color:#fff; margin-bottom:1rem; font-weight:800;">Volume Data Unavailable</h3>
          <p style="color:rgba(255,255,255,.8);">Unable to fetch real volume data for {display_symbol}.</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 3: TECHNICALS + ES ASIAN SESSION SWING LEVELS
with tab3:
    # --- ES Asian Session for SPX proxy or ES itself ---
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    ref_date = AppState.get_forecast_date()
    title_sym = display_symbol if display_symbol else "SPX"
    es_fig, asian_high, asian_low = build_es_intraday_with_asian_levels(title_sym, ref_date)
    st.plotly_chart(es_fig, use_container_width=True, config=CHART_CONFIG)

    if asian_high is not None and asian_low is not None:
        st.markdown(f"""
        <div style="text-align:center; margin-top:.75rem;">
          <span class="status-chip status-live">Asian High: ${asian_high:,.2f}</span>
          <span class="status-chip status-live" style="margin-left:.5rem;">Asian Low: ${asian_low:,.2f}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; color:rgba(255,255,255,.8); margin-top:.5rem;">
          Could not determine Asian session levels (insufficient intraday data).
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Technical Indicators for the current asset (daily) ---
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    tech_fig, tech_vals = build_technical_chart(current_asset)
    st.plotly_chart(tech_fig, use_container_width=True, config=CHART_CONFIG)
    st.markdown('</div>', unsafe_allow_html=True)

    # Insights panels from tech_vals
    if tech_vals:
        col1, col2, col3 = st.columns(3)

        # Panel color map
        pc = {"success":("rgba(16,185,129,.1)","rgba(16,185,129,.3)"),
              "warning":("rgba(245,158,11,.1)","rgba(245,158,11,.3)"),
              "info":   ("rgba(34,211,238,.1)","rgba(34,211,238,.3)")}

        # RSI
        with col1:
            rsi = float(tech_vals.get("rsi", 50.0))
            if rsi > 70:      status, color, action, ptype = "Overbought", "#ff6b35", "Consider profit-taking", "warning"
            elif rsi < 30:    status, color, action, ptype = "Oversold",   "#00ff88", "Potential buying zone", "success"
            else:             status, color, action, ptype = "Neutral",    "#a855f7", "Normal trading range", "info"
            bg, br = pc[ptype]
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {br}; border-radius:12px; padding:1.5rem; margin:1rem 0;">
              <div style="font-weight:700; font-size:1.1rem; margin-bottom:.5rem; color:#fff;">RSI Analysis ({rsi:.1f})</div>
              <div style="color:rgba(255,255,255,.9); line-height:1.6;">
                <strong style="color:{color};">{status}</strong>. {action}.
              </div>
            </div>
            """, unsafe_allow_html=True)

        # MACD
        with col2:
            macd = float(tech_vals.get("macd", 0.0))
            signal = float(tech_vals.get("macd_signal", 0.0))
            if macd > signal:  status, color, action, ptype = "Bullish", "#00ff88", "MACD above signal (upward momentum)", "success"
            elif macd < signal:status, color, action, ptype = "Bearish", "#ff6b35", "MACD below signal (downward pressure)", "warning"
            else:               status, color, action, ptype = "Neutral", "#a855f7", "MACD near signal; watch direction", "info"
            bg, br = pc[ptype]
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {br}; border-radius:12px; padding:1.5rem; margin:1rem 0;">
              <div style="font-weight:700; font-size:1.1rem; margin-bottom:.5rem; color:#fff;">MACD Signal ({status})</div>
              <div style="color:rgba(255,255,255,.9); line-height:1.6;">
                <strong style="color:{color};">{action}</strong>.
                MACD: {macd:.3f}, Signal: {signal:.3f}.
              </div>
            </div>
            """, unsafe_allow_html=True)

        # BB context
        with col3:
            price = float(tech_vals.get("price", 0.0))
            ub = float(tech_vals.get("bb_upper", 0.0))
            lb = float(tech_vals.get("bb_lower", 0.0))
            if ub != lb and ub > 0 and lb > 0:
                pos = (price - lb) / (ub - lb)
                if pos > 0.8:   status, color, action, ptype = "Near Upper Band", "#ff6b35", "Possible resistance / fade", "warning"
                elif pos < 0.2: status, color, action, ptype = "Near Lower Band", "#00ff88", "Potential bounce / support", "success"
                else:           status, color, action, ptype = "Mid-Range", "#a855f7", "Within normal band range", "info"
            else:
                status, color, action, ptype = "Calculating", "#a855f7", "Bands require more history", "info"
            bg, br = pc[ptype]
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {br}; border-radius:12px; padding:1.5rem; margin:1rem 0;">
              <div style="font-weight:700; font-size:1.1rem; margin-bottom:.5rem; color:#fff;">Bollinger Bands ({status})</div>
              <div style="color:rgba(255,255,255,.9); line-height:1.6;">
                <strong style="color:{color};">{action}</strong>.
                Current price: ${price:,.2f}.
              </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# FINAL STATUS SUMMARY (optional)
# ═══════════════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div class="glass-panel" style="padding: 2rem; text-align: center; margin: 3rem 0;">
  <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
  <h3 style="color:#fff; font-size:1.8rem; font-weight:800; margin-bottom:1rem;">
    MarketLens Pro – Live Data & ES Asian Session Levels Active
  </h3>
  <p style="color:rgba(255,255,255,.8); font-size:1.05rem; margin-bottom:1.25rem;">
    Charts, volume analytics, technicals, and ES Asian swing levels are now fully integrated.
  </p>
  <div style="display:flex; justify-content:center; gap:1rem; flex-wrap:wrap;">
    <span class="status-chip status-live">📊 Live Charts</span>
    <span class="status-chip status-live">📈 Volume Analysis</span>
    <span class="status-chip status-live">🗾 Asian Session Levels</span>
    <span class="status-chip status-live">🎯 Technical Indicators</span>
  </div>
</div>
""", unsafe_allow_html=True)




# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 3A (LIGHT MODE + ROBUST DATA)
# Core market data with validation and clean integration to Part 2 styling
# ═══════════════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf

# ---- Timezones (safe if already defined) ----
try:
    ET  # type: ignore
except NameError:
    ET = ZoneInfo("America/New_York")
try:
    CT  # type: ignore
except NameError:
    CT = ZoneInfo("America/Chicago")

# ---- Light-mode micro fix (do NOT flip whole app to dark) ----
def _light_mode_touchups():
    st.markdown("""
    <style>
    /* Keep metrics/readouts readable on the light theme */
    div[data-testid="stMetricLabel"] > div { color: #64748b !important; font-weight: 700; }
    div[data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 900; }
    span[data-testid="stMetricDelta"] { font-weight: 700; border-radius: 999px; padding: 2px 8px; }
    /* Streamlit alert chips stay readable on white cards */
    div[role="alert"] * { color: #0f172a !important; }
    </style>
    """, unsafe_allow_html=True)

if "mlp_light_fixes" not in st.session_state:
    _light_mode_touchups()
    st.session_state["mlp_light_fixes"] = True

# ---- Helpers and validation ----
def _fallback_asset():
    # Try AppState if present, else ^GSPC
    try:
        return AppState.get_current_asset()  # type: ignore
    except Exception:
        return st.session_state.get("asset", "^GSPC")

def _fallback_date():
    try:
        return AppState.get_forecast_date()  # type: ignore
    except Exception:
        return st.session_state.get("forecast_date", date.today())

def validate_symbol_format(symbol: str) -> bool:
    """Permissive validation (supports ^, =, -, ., /) to avoid blocking valid tickers like ^GSPC, ES=F."""
    return isinstance(symbol, str) and 0 < len(symbol) <= 15

def validate_price_data(data: dict) -> bool:
    if data.get("status") != "success":
        return False
    price = float(data.get("price", 0) or 0)
    change_pct = float(data.get("change_pct", 0) or 0)
    if price <= 0 or price > 1_000_000:
        return False
    if not np.isfinite(price) or not np.isfinite(change_pct):
        return False
    if abs(change_pct) > 50:
        return False
    return True

def calculate_data_quality_score(data: dict, hist: pd.DataFrame | None = None) -> int:
    score = 0
    if data.get("status") == "success": score += 40
    if validate_price_data(data): score += 30
    if float(data.get("volume", 0) or 0) >= 0: score += 15  # volume may be 0 for indices
    ts = data.get("timestamp")
    if isinstance(ts, datetime) and (datetime.now(ET) - ts).total_seconds() < 300: score += 15
    return min(100, score)

@st.cache_data(ttl=60, show_spinner=False)
def get_real_market_data(symbol: str) -> dict:
    """Live-ish quote via yfinance with robust fallbacks (1m→1d)."""
    try:
        if not validate_symbol_format(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")

        tkr = yf.Ticker(symbol)

        # Primary: 1m intraday (prepost too)
        try:
            intraday = tkr.history(period="1d", interval="1m", prepost=True)
            if isinstance(intraday, pd.DataFrame) and not intraday.empty and "Close" in intraday.columns:
                last = intraday.iloc[-1]
                px = float(last["Close"])
                ts_idx = intraday.index[-1]
                ts = pd.Timestamp(ts_idx)
                if ts.tz is None: ts = ts.tz_localize("UTC")
                ts = ts.tz_convert(ET)
                prev_close = float(intraday.iloc[-2]["Close"]) if len(intraday) > 1 else px
                change = px - prev_close
                change_pct = (change / prev_close) * 100 if prev_close else 0
                vol = int(last["Volume"]) if "Volume" in intraday.columns and pd.notna(last["Volume"]) else 0
                out = {
                    "symbol": symbol,
                    "price": px,
                    "change": change,
                    "change_pct": change_pct,
                    "volume": vol,
                    "previous_close": prev_close,
                    "timestamp": ts.to_pydatetime(),
                    "status": "success",
                    "data_source": "yfinance:1m"
                }
                if validate_price_data(out):
                    return out
        except Exception:
            pass

        # Fallback: daily
        daily = tkr.history(period="5d", interval="1d")
        if isinstance(daily, pd.DataFrame) and not daily.empty and "Close" in daily.columns:
            last = daily.iloc[-1]
            px = float(last["Close"])
            ts_idx = daily.index[-1]
            ts = pd.Timestamp(ts_idx)
            if ts.tz is None: ts = ts.tz_localize("UTC")
            ts = ts.tz_convert(ET)
            prev_close = float(daily.iloc[-2]["Close"]) if len(daily) > 1 else px
            change = px - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0
            vol = int(last["Volume"]) if "Volume" in daily.columns and pd.notna(last["Volume"]) else 0
            return {
                "symbol": symbol,
                "price": px,
                "change": change,
                "change_pct": change_pct,
                "volume": vol,
                "previous_close": prev_close,
                "timestamp": ts.to_pydatetime(),
                "status": "success",
                "data_source": "yfinance:1d"
            }

        raise RuntimeError("No data available")

    except Exception as e:
        return {
            "symbol": symbol,
            "price": 0.0, "change": 0.0, "change_pct": 0.0, "volume": 0,
            "previous_close": 0.0, "timestamp": datetime.now(ET),
            "status": "error", "error": str(e), "data_source": "error"
        }

@st.cache_data(ttl=300, show_spinner=False)
def get_historical_data(symbol: str, period: str = "2mo", interval: str = "1d") -> pd.DataFrame:
    """Historical with built-in EMA(8/21) + safe column handling."""
    try:
        tkr = yf.Ticker(symbol)
        df = tkr.history(period=period, interval=interval)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        # Normalize datetime column name
        for c in ["Date", "Datetime"]:
            if c in df.columns:
                df.rename(columns={c: "Dt"}, inplace=True)
                break
        if "Dt" not in df.columns:
            df["Dt"] = pd.to_datetime(df.index)

        # EMAs when enough points
        if "Close" in df.columns and len(df) >= 21:
            df["EMA_8"]  = df["Close"].ewm(span=8, adjust=False).mean()
            df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=180, show_spinner=False)
def get_intraday_data(symbol: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame:
    """Intraday with 8/21 EMAs + 5-bar Momentum (%)."""
    try:
        tkr = yf.Ticker(symbol)
        df = tkr.history(period=period, interval=interval, prepost=True)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        # Normalize time column
        for c in ["Datetime", "Date"]:
            if c in df.columns:
                df.rename(columns={c: "Dt"}, inplace=True)
                break
        if "Dt" not in df.columns:
            df["Dt"] = pd.to_datetime(df.index)

        if "Close" in df.columns and len(df) >= 21:
            df["EMA_8"] = df["Close"].ewm(span=8, adjust=False).mean()
            df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()
            df["Momentum"] = df["Close"].pct_change(periods=5) * 100
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def get_market_session_info() -> dict:
    now_et = datetime.now(ET)
    now_ct = datetime.now(CT)

    # Session
    if now_et.weekday() < 5:
        if time(4,0) <= now_et.time() < time(9,30): sess, emoji = "Pre-Market", "🌅"
        elif time(9,30) <= now_et.time() < time(16,0): sess, emoji = "Regular Hours", "📈"
        elif time(16,0) <= now_et.time() < time(20,0): sess, emoji = "After Hours", "🌆"
        else: sess, emoji = "Overnight", "🌙"
    else:
        sess, emoji = "Weekend", "📴"

    # Next event
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    if now_et.weekday() < 5:
        if now_et < market_open:
            next_event, delta = "Market Open", (market_open - now_et)
        elif now_et < market_close:
            next_event, delta = "Market Close", (market_close - now_et)
        else:
            next_event, delta = "Next Market Open", ((market_open + timedelta(days=1)) - now_et)
    else:
        # to Monday 9:30 ET
        days = (7 - now_et.weekday()) % 7 or 1
        next_open = (now_et + timedelta(days=days)).replace(hour=9, minute=30, second=0, microsecond=0)
        next_event, delta = "Monday Market Open", (next_open - now_et)

    return {
        "session": sess,
        "session_emoji": emoji,
        "timestamp_et": now_et,
        "timestamp_ct": now_ct,
        "next_event": next_event,
        "time_to_event": delta,
        "is_trading": sess in ["Pre-Market", "Regular Hours", "After Hours"],
        "market_day": now_et.weekday() < 5
    }

def get_system_health_metrics() -> dict:
    asset = _fallback_asset()
    md = get_real_market_data(asset)
    hd = get_historical_data(asset, period="5d", interval="1d")
    dq = calculate_data_quality_score(md, hd)
    uptime = (datetime.now(ET) - st.session_state.get("session_start_et", datetime.now(ET))).total_seconds()/60
    return {
        "data_quality": dq,
        "api_status": "Connected" if md.get("status") == "success" else "Error",
        "cache_hit_rate": 0.0,   # (Left simple; wire to your cache stats if you track them)
        "uptime_minutes": uptime,
        "historical_data_points": len(hd),
        "last_update": md.get("timestamp", datetime.now(ET)),
        "error_count": 0,
        "system_load": dq
    }

# ---- UI: Live Market Data (light-friendly) ----
st.markdown("## 📡 Core Market Data System")
asset = _fallback_asset()
md = get_real_market_data(asset)
sess = get_market_session_info()
health = get_system_health_metrics()

col1, col2, col3, col4 = st.columns(4)
with col1:
    if md["status"] == "success":
        st.metric("Current Price", f"${md['price']:,.2f}", f"{md['change']:+.2f}")
    else:
        st.metric("Current Price", "—", "Error")
with col2:
    if md["status"] == "success":
        st.metric("Change %", f"{md['change_pct']:+.2f}%", "Latest")
    else:
        st.metric("Change %", "—", "Error")
with col3:
    st.metric("Market Session", sess["session"], sess["session_emoji"])
with col4:
    st.metric("Last Update (ET)", md.get("timestamp", datetime.now(ET)).strftime("%I:%M:%S %p"), "Time")

st.markdown("### ⏰ Session Details")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Current Time ET", sess["timestamp_et"].strftime("%I:%M:%S %p"), "Eastern")
with c2:
    st.metric("Current Time CT", sess["timestamp_ct"].strftime("%I:%M:%S %p"), "Central")
with c3:
    st.metric(sess["next_event"], f"{sess['time_to_event'].total_seconds()/3600:.1f}h", "Until")

st.markdown("### 🔧 System Health")
h1, h2, h3, h4 = st.columns(4)
with h1: st.metric("Data Quality", f"{health['data_quality']}%", "Score")
with h2: st.metric("API Status", health["api_status"], "yfinance")
with h3: st.metric("Hist Points", str(health["historical_data_points"]), "Count")
with h4: st.metric("Uptime", f"{health['uptime_minutes']:.1f}m", "Session")

if md["status"] == "success":
    st.info("✅ Data validation OK" if validate_price_data(md) else "⚠️ Price data looks odd")
else:
    st.warning(f"⚠️ Data error: {md.get('error','unknown')}")





# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 3B (ASIAN SESSION LIKE WORKING APP)
# ES futures overnight anchors (5–8 PM CT) with ES→SPX conversion via live offset
# ═══════════════════════════════════════════════════════════════════════════════════════

ES_SYMBOL = "ES=F"

def previous_trading_day(ref_d: date) -> date:
    d = ref_d - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d

@st.cache_data(ttl=60, show_spinner=False)
def get_current_es_spx_offset() -> float:
    """SPX - ES offset. Falls back to typical if missing."""
    try:
        es = yf.Ticker("ES=F").history(period="1d", interval="1m", prepost=True)
        sp = yf.Ticker("^GSPC").history(period="1d", interval="1m", prepost=True)
        if not es.empty and not sp.empty:
            return float(sp["Close"].iloc[-1]) - float(es["Close"].iloc[-1])
    except Exception:
        pass
    return -23.5

def asian_window_ct(forecast_d: date) -> tuple[datetime, datetime]:
    prior = forecast_d - timedelta(days=1)
    return (
        datetime.combine(prior, time(17, 0), tzinfo=CT),
        datetime.combine(prior, time(20, 0), tzinfo=CT),
    )

@st.cache_data(ttl=300, show_spinner=False)
def es_fetch_asian_data(start_ct: datetime, end_ct: datetime, interval: str = "30m") -> pd.DataFrame:
    """Robust pull (tries 7d→1mo), normalizes datetime, filters to window, returns Open/High/Low/Close."""
    try:
        tkr = yf.Ticker(ES_SYMBOL)
        raw = pd.DataFrame()
        for period in ["7d", "1mo"]:
            try:
                raw = tkr.history(period=period, interval=interval, prepost=True)
                if raw is not None and not raw.empty:
                    break
            except Exception:
                continue
        if raw is None or raw.empty:
            return pd.DataFrame(columns=["Dt","Open","High","Low","Close"])

        df = raw.reset_index()
        # Find datetime column
        dtcol = None
        for c in ["Datetime", "Date", "index"]:
            if c in df.columns:
                dtcol = c
                break
        if dtcol is None:
            return pd.DataFrame(columns=["Dt","Open","High","Low","Close"])

        df.rename(columns={dtcol: "Dt"}, inplace=True)
        df["Dt"] = pd.to_datetime(df["Dt"])
        if df["Dt"].dt.tz is None:
            df["Dt"] = df["Dt"].dt.tz_localize("UTC")
        df["Dt"] = df["Dt"].dt.tz_convert(CT)

        df = df[["Dt","Open","High","Low","Close"]].dropna()
        mask = (df["Dt"] >= start_ct) & (df["Dt"] <= end_ct)
        return df.loc[mask].sort_values("Dt").reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["Dt","Open","High","Low","Close"])

@st.cache_data(ttl=300, show_spinner=False)
def es_asian_anchors_as_spx(forecast_d: date, timeframe: str = "30m") -> dict | None:
    """
    Use CLOSE-only swing detection for perfect line-chart matching.
    Returns SPX-equivalent close highs/lows + times.
    """
    try:
        start_ct, end_ct = asian_window_ct(forecast_d)
        es = es_fetch_asian_data(start_ct - timedelta(minutes=60), end_ct + timedelta(minutes=60), interval=timeframe)
        if es.empty:
            return None

        hi_idx = es["Close"].idxmax()
        lo_idx = es["Close"].idxmin()
        es_hi = float(es.loc[hi_idx, "Close"])
        es_lo = float(es.loc[lo_idx, "Close"])
        off = get_current_es_spx_offset()

        return {
            "high_px": es_hi + off,
            "high_time_ct": es.loc[hi_idx, "Dt"].to_pydatetime(),
            "low_px": es_lo + off,
            "low_time_ct": es.loc[lo_idx, "Dt"].to_pydatetime(),
            "es_high_close_raw": es_hi,
            "es_low_close_raw": es_lo,
            "conversion_offset": off,
            "timeframe": timeframe.upper(),
            "data_points": len(es),
            "method": "LINE_CHART_CLOSES",
        }
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def get_previous_day_ohlc(symbol: str, forecast_d: date) -> dict | None:
    """Prev trading day OHLC with weekend skip and safe fallback."""
    try:
        prev_d = previous_trading_day(forecast_d)
        df = yf.Ticker(symbol).history(period="1mo", interval="1d")
        if df is None or df.empty: return None
        df = df.reset_index()
        df["_d"] = pd.to_datetime(df["Date"]).dt.date if "Date" in df.columns else pd.to_datetime(df["Datetime"]).dt.date
        rows = df[df["_d"] == prev_d]
        if rows.empty:
            row = df.iloc[-1]
            use_d = df["_d"].iloc[-1]
        else:
            row = rows.iloc[-1]
            use_d = prev_d
        return {
            "symbol": symbol,
            "date": use_d,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]) if "Volume" in row else 0,
        }
    except Exception:
        return None

# ---- UI: Asian Session + Prior Day ----
st.markdown("## 🌏 Asian Session Analysis (ES → SPX)")
asset = _fallback_asset()
fdate = _fallback_date()
asian = es_asian_anchors_as_spx(fdate, "30m")
prevd = get_previous_day_ohlc(asset, fdate)

st.markdown("### ES Overnight Anchors (5–8 PM CT)")
if asian:
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("ES High (Close)", f"${asian['es_high_close_raw']:,.2f}", "Raw ES")
    with c2: st.metric("ES Low (Close)", f"${asian['es_low_close_raw']:,.2f}", "Raw ES")
    with c3: st.metric("SPX High Eq.", f"${asian['high_px']:,.2f}", asian['timeframe'])
    with c4: st.metric("SPX Low Eq.", f"${asian['low_px']:,.2f}", f"Offset {asian['conversion_offset']:+.1f}")
    st.caption(f"High @ {asian['high_time_ct'].strftime('%-I:%M %p CT')} • Low @ {asian['low_time_ct'].strftime('%-I:%M %p CT')} • Points: {asian['data_points']}")
else:
    st.warning("Could not retrieve ES overnight window. (Symbol ES=F via yfinance)")

st.markdown("### Previous Day OHLC")
if prevd:
    d1,d2,d3,d4 = st.columns(4)
    with d1: st.metric("Prev High", f"${prevd['high']:,.2f}")
    with d2: st.metric("Prev Close", f"${prevd['close']:,.2f}")
    with d3: st.metric("Prev Low", f"${prevd['low']:,.2f}")
    with d4:
        rng = prevd["high"] - prevd["low"]
        pct = (rng / prevd["close"])*100 if prevd["close"] else 0
        st.metric("Daily Range", f"${rng:,.2f}", f"{pct:.2f}%")
else:
    st.warning("Previous-day OHLC unavailable for selected asset/date.")

# ---- EMA snapshot (daily) ----
st.markdown("### 📈 Technical Snapshot (8/21 EMA, Daily)")
hist = get_historical_data(asset, period="2mo", interval="1d")
if not hist.empty and "EMA_8" in hist and "EMA_21" in hist:
    last = hist.iloc[-1]
    e1,e2,e3 = st.columns(3)
    with e1: st.metric("8 EMA", f"${last['EMA_8']:,.2f}")
    with e2: st.metric("21 EMA", f"${last['EMA_21']:,.2f}")
    with e3:
        bias = "Bullish" if last["EMA_8"] > last["EMA_21"] else "Bearish"
        st.metric("Trend", bias)
else:
    st.info("Not enough data for EMAs yet.")





# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 3C (PLOTLY WHITE THEME)
# Professional charts with live data (light-mode friendly)
# ═══════════════════════════════════════════════════════════════════════════════════════

import plotly.graph_objs as go
from plotly.subplots import make_subplots

def create_price_chart(symbol: str, title: str = "Price & EMAs", show_emas: bool = True):
    df = get_historical_data(symbol, period="1mo", interval="1d")
    if df.empty or "Close" not in df.columns:
        return go.Figure(layout=dict(template="plotly_white", title=f"{symbol} (No Data)"))
    x = df["Dt"] if "Dt" in df.columns else df.index
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df["Close"], mode="lines", name="Close"))
    if show_emas and "EMA_8" in df and "EMA_21" in df:
        fig.add_trace(go.Scatter(x=x, y=df["EMA_8"], mode="lines", name="EMA 8"))
        fig.add_trace(go.Scatter(x=x, y=df["EMA_21"], mode="lines", name="EMA 21"))
    fig.update_layout(
        template="plotly_white",
        title=title, height=420,
        margin=dict(l=40,r=20,t=60,b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_volume_chart(symbol: str):
    df = get_historical_data(symbol, period="1mo", interval="1d")
    if df.empty or "Volume" not in df.columns:
        return go.Figure(layout=dict(template="plotly_white", title=f"{symbol} Volume (No Data)"))
    x = df["Dt"] if "Dt" in df.columns else df.index
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=df["Volume"], name="Volume", opacity=0.8))
    if len(df) >= 20:
        df["VolMA20"] = df["Volume"].rolling(20).mean()
        fig.add_trace(go.Scatter(x=x, y=df["VolMA20"], name="Vol MA(20)", mode="lines"))
    fig.update_layout(template="plotly_white", title=f"{symbol} Volume", height=340, margin=dict(l=40,r=20,t=50,b=40))
    return fig

def create_intraday_momentum(symbol: str):
    df = get_intraday_data(symbol, period="1d", interval="5m")
    if df.empty or "Close" not in df.columns:
        return go.Figure(layout=dict(template="plotly_white", title=f"{symbol} Intraday (No Data)"))
    x = df["Dt"] if "Dt" in df.columns else df.index
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("Price (5m)", "Momentum (5-bar ROC %)"),
                        row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=x, y=df["Close"], name="Close", mode="lines"), row=1, col=1)
    if "EMA_8" in df and "EMA_21" in df:
        fig.add_trace(go.Scatter(x=x, y=df["EMA_8"], name="EMA 8", mode="lines"), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=df["EMA_21"], name="EMA 21", mode="lines"), row=1, col=1)
    if "Momentum" in df:
        fig.add_trace(go.Bar(x=x, y=df["Momentum"], name="Momentum", opacity=0.8), row=2, col=1)
    fig.update_layout(template="plotly_white", height=520, margin=dict(l=40,r=20,t=60,b=40), hovermode="x unified")
    return fig

# ---- UI: Tabs ----
st.markdown("## 📈 Live Chart Integration")
cur = _fallback_asset()
tab1, tab2, tab3 = st.tabs(["📊 Price & EMAs", "📈 Volume", "⚡ Intraday Momentum"])

with tab1:
    show_emas = st.checkbox("Show EMAs", value=True)
    st.plotly_chart(create_price_chart(cur, f"{cur} — Price & EMAs", show_emas), use_container_width=True)

with tab2:
    st.plotly_chart(create_volume_chart(cur), use_container_width=True)

with tab3:
    st.plotly_chart(create_intraday_momentum(cur), use_container_width=True)

# ---- System overview (simple) ----
st.markdown("### 🔎 Data System Status")
md = get_real_market_data(cur)
hist_ok = not get_historical_data(cur).empty
asian_ok = es_asian_anchors_as_spx(_fallback_date()) is not None
prev_ok = get_previous_day_ohlc(cur, _fallback_date()) is not None

c1,c2,c3,c4 = st.columns(4)
with c1: st.metric("Live Market", "🟢" if md.get("status")=="success" else "🔴", md.get("data_source",""))
with c2: st.metric("Historical", "🟢" if hist_ok else "🔴", "Price/EMAs")
with c3: st.metric("Asian Session", "🟢" if asian_ok else "🔴", "ES 5–8 PM CT")
with c4: st.metric("Prev Day", "🟢" if prev_ok else "🔴", "OHLC")



