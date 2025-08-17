# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - ENTERPRISE SPX & EQUITIES FORECASTING PLATFORM  
# PART 1: CORE CONFIGURATION & GLOBAL SETTINGS (ERROR-FREE VERSION)
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
        'Get Help': 'https://quantumtradingsystems.com/support',
        'Report a bug': 'https://quantumtradingsystems.com/bugs', 
        'About': f"{APP_NAME} v{VERSION} - Professional trading analytics platform"
    }
)

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

# ───────────────────────────────  TEXT VISIBILITY FIX FOR MODERN UI  ───────────────────────────────
# Force all Streamlit components to use white text for dark theme compatibility
st.markdown("""
<style>
/* Force white text for all Streamlit components */
.stApp, .stApp * {
    color: #ffffff !important;
}

/* Specific fixes for form elements */
.stSelectbox label, 
.stDateInput label,
.stButton > button,
.stRadio label,
.stMetric label,
.stMetric div {
    color: #ffffff !important;
}

/* Fix metric values */
[data-testid="metric-container"] {
    color: #ffffff !important;
}

[data-testid="metric-container"] > div {
    color: #ffffff !important;
}

/* Fix sidebar text */
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Fix main content area */
.main .block-container * {
    color: #ffffff !important;
}

/* Fix dataframes */
.stDataFrame {
    color: #ffffff !important;
}

/* Fix alerts and info boxes */
.stAlert, .stInfo, .stSuccess, .stWarning, .stError {
    color: #ffffff !important;
}

/* Fix markdown content */
.stMarkdown {
    color: #ffffff !important;
}

/* Fix headers */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

/* Fix paragraphs and text */
p, span, div {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────  DEMONSTRATION SECTION (UPDATED FOR UI)  ───────────────────────────────
# Create a simple demonstration that works with the new UI
st.markdown(f"""
<div style="color: #ffffff; padding: 1rem; margin: 1rem 0;">
    <h1 style="color: #ffffff !important;">📈 {APP_NAME}</h1>
    <h2 style="color: rgba(255, 255, 255, 0.8) !important;">{TAGLINE} - v{VERSION}</h2>
    <p style="color: rgba(255, 255, 255, 0.7) !important;">Professional Trading Analytics Platform by {COMPANY}</p>
</div>
""", unsafe_allow_html=True)

# Create columns for demonstration metrics
col1, col2, col3 = st.columns(3)

with col1:
    market_status, _ = get_market_status()
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.1); padding: 1rem; border-radius: 12px; text-align: center;">
        <h3 style="color: #ffffff !important; margin: 0;">Market Status</h3>
        <p style="color: #22d3ee !important; font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">{market_status}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    current_time = datetime.now(CT).strftime("%I:%M:%S %p CT")
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.1); padding: 1rem; border-radius: 12px; text-align: center;">
        <h3 style="color: #ffffff !important; margin: 0;">Current Time</h3>
        <p style="color: #a855f7 !important; font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">{current_time}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.1); padding: 1rem; border-radius: 12px; text-align: center;">
        <h3 style="color: #ffffff !important; margin: 0;">Company</h3>
        <p style="color: #10b981 !important; font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">{COMPANY}</p>
    </div>
    """, unsafe_allow_html=True)

# Create sidebar demonstration
with st.sidebar:
    st.markdown(f"""
    <div style="color: #ffffff; text-align: center; padding: 1rem;">
        <h2 style="color: #ffffff !important;">🎛️ Controls</h2>
        <p style="color: rgba(255, 255, 255, 0.8) !important;">Application ready for Part 3</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Asset selector
    st.markdown('<p style="color: #ffffff !important; font-weight: bold;">Select Asset:</p>', unsafe_allow_html=True)
    selected_asset = st.selectbox(
        "Choose trading instrument",
        options=list(MAJOR_EQUITIES.keys()),
        format_func=lambda x: f"{MAJOR_EQUITIES[x]['icon']} {get_display_symbol(x)}",
        label_visibility="collapsed"
    )

    # Date selector
    st.markdown('<p style="color: #ffffff !important; font-weight: bold;">Forecast Date:</p>', unsafe_allow_html=True)
    forecast_date = st.date_input(
        "Analysis date", 
        value=date.today(),
        max_value=date.today(),
        label_visibility="collapsed"
    )

# Update session state
AppState.set_current_asset(selected_asset)
AppState.set_forecast_date(forecast_date)

# Get slope information for the selected asset
slopes = get_asset_slopes(selected_asset)
display_symbol = get_display_symbol(selected_asset)

if selected_asset == "^GSPC":
    slope_info = f"SPX Slopes: Skyline +{slopes['skyline']:.4f}, Baseline {slopes['baseline']:.4f}"
else:
    slope_info = f"{display_symbol} Slopes: Skyline +{slopes['skyline']:.4f}, Baseline {slopes['baseline']:.4f}"

# Asset information display
asset_info = MAJOR_EQUITIES[selected_asset]
st.markdown(f"""
<div style="background: rgba(255, 255, 255, 0.08); padding: 2rem; border-radius: 16px; margin: 2rem 0; text-align: center;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">{asset_info['icon']}</div>
    <h2 style="color: #ffffff !important;">{display_symbol} Analysis</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
        <div>
            <h4 style="color: rgba(255, 255, 255, 0.7) !important; margin: 0;">Asset Symbol</h4>
            <p style="color: #ffffff !important; font-weight: bold; margin: 0;">{display_symbol}</p>
        </div>
        <div>
            <h4 style="color: rgba(255, 255, 255, 0.7) !important; margin: 0;">Asset Name</h4>
            <p style="color: #ffffff !important; font-weight: bold; margin: 0;">{asset_info['name']}</p>
        </div>
        <div>
            <h4 style="color: rgba(255, 255, 255, 0.7) !important; margin: 0;">Sector</h4>
            <p style="color: #ffffff !important; font-weight: bold; margin: 0;">{asset_info['type']}</p>
        </div>
        <div>
            <h4 style="color: rgba(255, 255, 255, 0.7) !important; margin: 0;">Analysis Date</h4>
            <p style="color: #ffffff !important; font-weight: bold; margin: 0;">{forecast_date.strftime('%B %d, %Y')}</p>
        </div>
        <div>
            <h4 style="color: rgba(255, 255, 255, 0.7) !important; margin: 0;">Previous Day</h4>
            <p style="color: #ffffff !important; font-weight: bold; margin: 0;">{previous_trading_day(forecast_date).strftime('%B %d, %Y')}</p>
        </div>
        <div>
            <h4 style="color: rgba(255, 255, 255, 0.7) !important; margin: 0;">Slopes Configuration</h4>
            <p style="color: #ffffff !important; font-weight: bold; margin: 0;">{slope_info}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# System status display
system_checks = verify_system_ready()
all_ready = all(system_checks.values())

st.markdown(f"""
<div style="background: rgba(255, 255, 255, 0.08); padding: 1.5rem; border-radius: 16px; margin: 2rem 0; text-align: center;">
    <h3 style="color: #ffffff !important;">System Status</h3>
    <p style="color: {'#10b981' if all_ready else '#f59e0b'} !important; font-size: 1.25rem; font-weight: bold;">
        {'🟢 All Systems Ready' if all_ready else '🟡 Partial Ready'}
    </p>
    <p style="color: rgba(255, 255, 255, 0.7) !important; margin: 0;">Ready for Part 3 - Data Integration</p>
</div>
""", unsafe_allow_html=True)
