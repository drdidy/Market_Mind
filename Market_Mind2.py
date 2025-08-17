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



# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2A: FOUNDATION CSS & CORE STYLING (FIXED FOR STREAMLIT)
# Next-Generation Trading Interface - Foundation Layer
# ═══════════════════════════════════════════════════════════════════════════════════════

# Foundation CSS styling that works with Streamlit
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ========== CORE FOUNDATION & MODERN VARIABLES ========== */
:root {
  /* Glassmorphism System */
  --glass-bg: rgba(255, 255, 255, 0.08);
  --glass-border: rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
  --glass-hover: rgba(255, 255, 255, 0.12);
  
  /* Neon Color Palette */
  --neon-blue: #00d4ff;
  --neon-purple: #8b5cf6;
  --neon-green: #00ff88;
  --neon-orange: #ff6b35;
  --neon-pink: #ff006e;
  --neon-cyan: #22d3ee;
  --neon-violet: #a855f7;
  
  /* Surface Colors */
  --surface-1: #0f0f23;
  --surface-2: #1a1a2e;
  --surface-3: #16213e;
  --surface-4: #0f172a;
  --surface-5: #1e1b4b;
  
  /* Accent Colors */
  --accent-cyan: #22d3ee;
  --accent-violet: #a855f7;
  --accent-emerald: #10b981;
  --accent-amber: #f59e0b;
  --accent-rose: #f43f5e;
  
  /* Animation Timing */
  --transition-fast: 0.15s;
  --transition-normal: 0.3s;
  --transition-slow: 0.5s;
  --ease-out: cubic-bezier(0.4, 0, 0.2, 1);
}

/* ========== GLOBAL RESET & BASE STYLES ========== */
html, body, .stApp {
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, var(--surface-1) 0%, var(--surface-2) 25%, var(--surface-3) 50%, var(--surface-4) 75%, var(--surface-5) 100%);
  background-attachment: fixed;
  color: #ffffff;
  overflow-x: hidden;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.stApp {
  background: 
    radial-gradient(circle at 20% 20%, rgba(34, 211, 238, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(16, 185, 129, 0.1) 0%, transparent 50%),
    linear-gradient(135deg, var(--surface-1) 0%, var(--surface-2) 100%);
  min-height: 100vh;
  position: relative;
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
    radial-gradient(1px 1px at 130px 80px, rgba(255, 255, 255, 0.08), transparent),
    radial-gradient(2px 2px at 160px 30px, rgba(255, 255, 255, 0.12), transparent);
  background-repeat: repeat;
  background-size: 300px 400px;
  animation: sparkle 25s linear infinite;
  pointer-events: none;
  z-index: 1;
  opacity: 0.8;
}

@keyframes sparkle {
  from { background-position: 0% 0%; }
  to { background-position: 300px 400px; }
}

/* ========== TEXT VISIBILITY FIXES FOR STREAMLIT ========== */
/* Force white text for ALL Streamlit components */
.stApp, .stApp *, .main *, .block-container *, 
.stMarkdown, .stMarkdown *, .css-1d391kg *, 
.css-12oz5g7 *, .css-1ekf893 *, .css-16idsys *,
h1, h2, h3, h4, h5, h6, p, span, div, label {
  color: #ffffff !important;
}

/* Specific Streamlit component fixes */
.stSelectbox label, 
.stDateInput label,
.stButton > button,
.stRadio label,
.stMetric label,
.stMetric div,
.stText,
.stCaption,
[data-testid="metric-container"],
[data-testid="metric-container"] > div,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
  color: #ffffff !important;
}

/* Sidebar text fixes */
section[data-testid="stSidebar"] *, 
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
  color: #ffffff !important;
}

/* Form element base styling */
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 12px !important;
  color: #ffffff !important;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* Alert styling */
.stAlert, .stInfo, .stSuccess, .stWarning, .stError {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 12px !important;
  color: #ffffff !important;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.stSuccess {
  border-left: 4px solid var(--neon-green) !important;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.08) 100%) !important;
}

.stWarning {
  border-left: 4px solid var(--neon-orange) !important;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.08) 100%) !important;
}

.stError {
  border-left: 4px solid var(--neon-pink) !important;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.08) 100%) !important;
}

.stInfo {
  border-left: 4px solid var(--neon-cyan) !important;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.15) 0%, rgba(59, 130, 246, 0.08) 100%) !important;
}

/* ========== SIDEBAR FOUNDATION ========== */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, 
    rgba(15, 15, 35, 0.98) 0%, 
    rgba(26, 26, 46, 0.95) 50%,
    rgba(15, 23, 42, 0.98) 100%);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border-right: 2px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 80px rgba(0, 0, 0, 0.6);
}

section[data-testid="stSidebar"] > div {
  background: transparent;
  padding-top: 1rem;
}

/* ========== BUTTON FOUNDATION ========== */
.stButton > button {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.25) 0%, rgba(168, 85, 247, 0.25) 100%);
  border: 2px solid rgba(34, 211, 238, 0.5);
  border-radius: 12px;
  color: #ffffff !important;
  font-weight: 700;
  padding: 0.75rem 1.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.stButton > button:hover {
  border-color: var(--neon-cyan);
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.35) 0%, rgba(168, 85, 247, 0.35) 100%);
  box-shadow: 0 0 30px rgba(34, 211, 238, 0.5);
  transform: translateY(-2px);
}

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
  .stApp {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .stApp {
    font-size: 13px;
  }
}

/* ========== UTILITIES ========== */
.glass-panel {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
}

.text-center { text-align: center; }
.text-white { color: #ffffff !important; }

/* ========== FIX FOR STREAMLIT MARKDOWN ========== */
.stMarkdown > div {
  color: #ffffff !important;
}

/* Fix for expander content */
.streamlit-expanderContent,
.streamlit-expanderContent *,
details[data-testid="stExpander"] *,
div[data-testid="stExpander"] * {
  color: #ffffff !important;
}

/* Fix for tabs */
.stTabs [data-baseweb="tab-list"] *,
.stTabs [data-baseweb="tab-panel"] * {
  color: #ffffff !important;
}

/* Fix for columns */
.css-12oz5g7 *, .css-1d391kg *, .css-16idsys * {
  color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# Test that the CSS is working
st.markdown('<div style="color: #ffffff !important; text-align: center; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 12px; margin: 1rem 0;"><h3 style="color: #22d3ee !important;">✅ Part 2A Foundation CSS Loaded Successfully</h3><p style="color: rgba(255,255,255,0.8) !important;">The foundation styling is now active. You should see this text in white with a glass background.</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2B: INTERACTIVE COMPONENTS & ADVANCED UI ELEMENTS
# Professional Interface Components with Modern Design Elements (Fixed for Streamlit)
# ═══════════════════════════════════════════════════════════════════════════════════════

# Advanced UI components and interactive elements (builds on Part 2A)
st.markdown("""
<style>
/* ========== METRIC CARDS & DASHBOARD COMPONENTS ========== */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
  padding: 0;
}

.metric-card {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.06) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 1.5rem;
  padding: 2rem;
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  text-align: center;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, 
    var(--neon-cyan) 0%, 
    var(--neon-violet) 33%,
    var(--neon-green) 66%,
    var(--neon-orange) 100%);
  transform: scaleX(0);
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 1.5rem 1.5rem 0 0;
}

.metric-card:hover {
  transform: translateY(-12px) scale(1.03);
  border-color: rgba(34, 211, 238, 0.4);
  box-shadow: 
    0 25px 50px rgba(34, 211, 238, 0.25),
    0 0 0 1px rgba(34, 211, 238, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.metric-card:hover::before {
  transform: scaleX(1);
}

.metric-label {
  font-size: 0.875rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.75) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.75rem;
}

.metric-value {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 900;
  color: #ffffff !important;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  text-shadow: 0 0 30px rgba(255, 255, 255, 0.4);
  margin-bottom: 0.75rem;
  line-height: 1;
}

.metric-change {
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.metric-positive { 
  color: var(--neon-green) !important;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
}

.metric-negative { 
  color: var(--neon-orange) !important;
  text-shadow: 0 0 10px rgba(255, 107, 53, 0.5);
}

.metric-neutral { 
  color: rgba(255, 255, 255, 0.7) !important;
}

/* ========== ENHANCED NAVIGATION SIDEBAR ========== */
section[data-testid="stSidebar"]::before {
  content: '';
  position: absolute;
  top: 0; right: 0; width: 1px; height: 100%;
  background: linear-gradient(180deg,
    transparent 0%,
    var(--neon-cyan) 25%,
    var(--neon-violet) 50%,
    var(--neon-green) 75%,
    transparent 100%);
  animation: sidebar-glow 4s ease-in-out infinite;
}

@keyframes sidebar-glow {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

/* Enhanced Radio Button Styling */
section[data-testid="stSidebar"] .stRadio label {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.03) 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 1rem !important;
  padding: 1rem !important;
  margin: 0.25rem 0 !important;
  color: rgba(255, 255, 255, 0.8) !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  cursor: pointer !important;
  position: relative !important;
  overflow: hidden !important;
}

section[data-testid="stSidebar"] .stRadio label:hover {
  background: linear-gradient(135deg, 
    rgba(34, 211, 238, 0.15) 0%, 
    rgba(168, 85, 247, 0.15) 100%) !important;
  border-color: rgba(34, 211, 238, 0.4) !important;
  color: #ffffff !important;
  transform: translateX(6px) !important;
  box-shadow: 
    0 4px 12px rgba(34, 211, 238, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

/* Enhanced Select Box Styling */
section[data-testid="stSidebar"] .stSelectbox > div > div {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    rgba(255, 255, 255, 0.05) 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  border-radius: 1rem !important;
  color: #ffffff !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

section[data-testid="stSidebar"] .stSelectbox > div > div:hover {
  border-color: rgba(34, 211, 238, 0.5) !important;
  box-shadow: 
    0 0 20px rgba(34, 211, 238, 0.3),
    0 4px 12px rgba(0, 0, 0, 0.2) !important;
  transform: translateY(-1px) !important;
}

/* ========== STATUS INDICATORS & CHIPS ========== */
.status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border: 2px solid;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  white-space: nowrap;
}

.status-live {
  background: linear-gradient(135deg, 
    rgba(16, 185, 129, 0.25) 0%, 
    rgba(5, 150, 105, 0.25) 100%);
  border-color: var(--neon-green);
  color: var(--neon-green) !important;
  animation: pulse-glow-green 3s ease-in-out infinite;
  box-shadow: 
    0 0 20px rgba(16, 185, 129, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.status-warning {
  background: linear-gradient(135deg, 
    rgba(245, 158, 11, 0.25) 0%, 
    rgba(217, 119, 6, 0.25) 100%);
  border-color: var(--neon-orange);
  color: var(--neon-orange) !important;
  box-shadow: 
    0 0 15px rgba(245, 158, 11, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.status-error {
  background: linear-gradient(135deg, 
    rgba(239, 68, 68, 0.25) 0%, 
    rgba(220, 38, 38, 0.25) 100%);
  border-color: var(--neon-pink);
  color: var(--neon-pink) !important;
  box-shadow: 
    0 0 15px rgba(239, 68, 68, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.status-success {
  background: linear-gradient(135deg, 
    rgba(16, 185, 129, 0.25) 0%, 
    rgba(5, 150, 105, 0.25) 100%);
  border-color: var(--neon-green);
  color: var(--neon-green) !important;
  box-shadow: 
    0 0 20px rgba(16, 185, 129, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

@keyframes pulse-glow-green {
  0%, 100% { 
    box-shadow: 
      0 0 15px rgba(16, 185, 129, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }
  50% { 
    box-shadow: 
      0 0 30px rgba(16, 185, 129, 0.6),
      0 0 60px rgba(16, 185, 129, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
}

/* ========== ENHANCED BUTTON STYLING ========== */
.stButton > button {
  background: linear-gradient(135deg, 
    rgba(34, 211, 238, 0.25) 0%, 
    rgba(168, 85, 247, 0.25) 100%) !important;
  border: 2px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 1rem !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  font-size: 0.875rem !important;
  padding: 1rem 1.5rem !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  position: relative !important;
  overflow: hidden !important;
  cursor: pointer !important;
  box-shadow: 
    0 4px 12px rgba(34, 211, 238, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

.stButton > button:hover {
  border-color: var(--neon-cyan) !important;
  background: linear-gradient(135deg, 
    rgba(34, 211, 238, 0.35) 0%, 
    rgba(168, 85, 247, 0.35) 100%) !important;
  box-shadow: 
    0 0 30px rgba(34, 211, 238, 0.5),
    0 8px 24px rgba(34, 211, 238, 0.3),
    inset 0 0 30px rgba(34, 211, 238, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  transform: translateY(-3px) scale(1.02) !important;
}

/* ========== ASSET ICONS & ANIMATIONS ========== */
.asset-icon {
  font-size: clamp(2.5rem, 6vw, 3.5rem);
  text-shadow: 
    0 0 20px rgba(255, 255, 255, 0.6),
    0 0 40px rgba(34, 211, 238, 0.3);
  display: inline-block;
  animation: float-smooth 4s ease-in-out infinite;
  margin-bottom: 1rem;
  filter: brightness(1.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes float-smooth {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  25% { transform: translateY(-8px) rotate(1deg); }
  50% { transform: translateY(-12px) rotate(0deg); }
  75% { transform: translateY(-6px) rotate(-1deg); }
}

.asset-icon-large {
  font-size: clamp(3rem, 8vw, 5rem);
  text-shadow: 
    0 0 30px rgba(255, 255, 255, 0.8),
    0 0 60px rgba(168, 85, 247, 0.4);
  display: inline-block;
  animation: float-large-complex 6s ease-in-out infinite;
  margin-bottom: 1.5rem;
  filter: brightness(1.2);
}

@keyframes float-large-complex {
  0%, 100% { transform: translateY(0px) rotate(0deg) scale(1); }
  16% { transform: translateY(-15px) rotate(2deg) scale(1.05); }
  33% { transform: translateY(-20px) rotate(0deg) scale(1.08); }
  50% { transform: translateY(-10px) rotate(-1deg) scale(1.03); }
  66% { transform: translateY(-18px) rotate(1deg) scale(1.06); }
  83% { transform: translateY(-8px) rotate(-2deg) scale(1.02); }
}

/* ========== HOVER UTILITIES ========== */
.hover-lift {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-lift:hover {
  transform: translateY(-6px) scale(1.02);
  filter: brightness(1.1);
}

.hover-glow {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-glow:hover {
  box-shadow: 
    0 0 20px rgba(34, 211, 238, 0.4),
    0 0 40px rgba(34, 211, 238, 0.2);
  border-color: rgba(34, 211, 238, 0.6);
}
</style>
""", unsafe_allow_html=True)

# Test that Part 2B interactive components are working
st.markdown('<div style="color: #ffffff !important; text-align: center; padding: 1rem; background: linear-gradient(135deg, rgba(34, 211, 238, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%); border: 1px solid rgba(34, 211, 238, 0.3); border-radius: 16px; margin: 1rem 0;"><h3 style="color: #22d3ee !important;">✅ Part 2B Interactive Components Loaded Successfully</h3><p style="color: rgba(255,255,255,0.8) !important;">Advanced interactive elements, animations, and hover effects are now active.</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2C: UI FUNCTIONS & COMPONENT SYSTEM
# Interactive Components and Advanced UI Functions (Fixed for Streamlit)
# ═══════════════════════════════════════════════════════════════════════════════════════

# Final UI components and functions (builds on Parts 2A and 2B)
st.markdown("""
<style>
/* ========== HERO SECTION STYLING ========== */
.hero-container {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.06) 100%);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 2rem;
  padding: 3rem;
  margin: 2rem 0;
  box-shadow: 
    0 20px 40px rgba(31, 38, 135, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  z-index: 10;
}

.hero-container::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--neon-cyan) 15%, 
    var(--neon-violet) 30%,
    var(--neon-green) 45%,
    var(--neon-orange) 60%,
    var(--neon-pink) 75%,
    transparent 100%);
  animation: shimmer-rainbow 4s ease-in-out infinite;
}

@keyframes shimmer-rainbow {
  0%, 100% { 
    opacity: 0.4; 
    transform: translateX(-100%);
  }
  50% { 
    opacity: 1; 
    transform: translateX(100%);
  }
}

.hero-title {
  font-size: clamp(2.5rem, 8vw, 4rem);
  font-weight: 900;
  background: linear-gradient(135deg, 
    #ffffff 0%, 
    var(--neon-cyan) 25%, 
    var(--neon-violet) 50%,
    var(--neon-green) 75%,
    #ffffff 100%);
  background-size: 300% 300%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: -0.03em;
  text-shadow: 0 0 60px rgba(34, 211, 238, 0.4);
  animation: glow-pulse 6s ease-in-out infinite, gradient-shift 8s ease-in-out infinite;
  text-align: center;
  line-height: 1.1;
}

@keyframes glow-pulse {
  0%, 100% { 
    filter: drop-shadow(0 0 10px rgba(34, 211, 238, 0.4));
    transform: scale(1);
  }
  33% { 
    filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.6));
    transform: scale(1.02);
  }
  66% { 
    filter: drop-shadow(0 0 15px rgba(16, 185, 129, 0.5));
    transform: scale(1.01);
  }
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  25% { background-position: 100% 50%; }
  50% { background-position: 50% 100%; }
  75% { background-position: 0% 100%; }
}

.hero-subtitle {
  font-size: clamp(1.125rem, 4vw, 1.75rem);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85) !important;
  margin: 1.5rem 0;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  text-align: center;
  letter-spacing: -0.01em;
}

.hero-meta {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.65) !important;
  font-weight: 500;
  margin-top: 1rem;
  text-align: center;
  letter-spacing: 0.01em;
}

/* ========== SECTION HEADERS ========== */
.section-header {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.03) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 1rem;
  padding: 2rem;
  margin: 2rem 0;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #ffffff 0%, var(--neon-cyan) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 1rem 0;
}

.section-subtitle {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.7) !important;
  font-weight: 500;
  margin: 0;
}

/* ========== DATA TABLES & CHARTS ========== */
.dataframe-container {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.05) 0%, 
    rgba(255, 255, 255, 0.02) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 1rem;
  margin: 1rem 0;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.chart-container {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.03) 100%);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 1.25rem;
  padding: 1.5rem;
  margin: 1.5rem 0;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.chart-container::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--neon-cyan) 50%, 
    transparent 100%);
  animation: chart-glow 3s ease-in-out infinite;
}

@keyframes chart-glow {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ========== ENHANCED DATAFRAME STYLING ========== */
.stDataFrame {
  background: transparent !important;
}

.stDataFrame table {
  background: transparent !important;
  color: #ffffff !important;
  border-radius: 0.75rem !important;
  overflow: hidden !important;
}

.stDataFrame th {
  background: linear-gradient(135deg, 
    rgba(34, 211, 238, 0.15) 0%, 
    rgba(168, 85, 247, 0.15) 100%) !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  border: none !important;
  padding: 1rem !important;
  font-size: 0.875rem !important;
}

.stDataFrame td {
  background: rgba(255, 255, 255, 0.03) !important;
  color: rgba(255, 255, 255, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
  padding: 0.75rem !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.875rem !important;
}

.stDataFrame tr:hover td {
  background: rgba(34, 211, 238, 0.1) !important;
  color: #ffffff !important;
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
  background: var(--surface-1);
  padding: 0 1rem;
  color: var(--neon-cyan);
  font-size: 1.5rem;
}

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
  .hero-container {
    padding: 2rem;
    margin: 1rem 0;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.25rem;
  }
  
  .metric-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .metric-card {
    padding: 1.5rem;
    min-height: 160px;
  }
  
  .asset-icon {
    font-size: 2.5rem;
  }
  
  .section-title {
    font-size: 2rem;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    font-size: 1rem;
  }
  
  .hero-container {
    padding: 1.5rem;
  }
  
  .metric-card {
    padding: 1rem;
    min-height: 140px;
  }
  
  .metric-value {
    font-size: 1.5rem;
  }
}

/* ========== LOADING STATES ========== */
.loading-shimmer {
  background: linear-gradient(90deg,
    rgba(255, 255, 255, 0.08) 25%,
    rgba(255, 255, 255, 0.18) 50%,
    rgba(255, 255, 255, 0.08) 75%);
  background-size: 200% 100%;
  animation: shimmer-loading 2s infinite cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes shimmer-loading {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.pulse-animation {
  animation: pulse-subtle 3s ease-in-out infinite;
}

@keyframes pulse-subtle {
  0%, 100% { 
    opacity: 0.8;
    transform: scale(1);
  }
  50% { 
    opacity: 1;
    transform: scale(1.02);
  }
}

/* ========== UTILITY CLASSES ========== */
.text-center { text-align: center !important; }
.text-left { text-align: left !important; }
.text-right { text-align: right !important; }

.font-light { font-weight: 300 !important; }
.font-normal { font-weight: 400 !important; }
.font-medium { font-weight: 500 !important; }
.font-semibold { font-weight: 600 !important; }
.font-bold { font-weight: 700 !important; }
.font-black { font-weight: 900 !important; }

.text-xs { font-size: 0.75rem !important; }
.text-sm { font-size: 0.875rem !important; }
.text-base { font-size: 1rem !important; }
.text-lg { font-size: 1.125rem !important; }
.text-xl { font-size: 1.25rem !important; }
.text-2xl { font-size: 1.5rem !important; }
.text-3xl { font-size: 1.875rem !important; }
.text-4xl { font-size: 2.25rem !important; }

.m-0 { margin: 0 !important; }
.m-1 { margin: 0.25rem !important; }
.m-2 { margin: 0.5rem !important; }
.m-4 { margin: 1rem !important; }

.p-0 { padding: 0 !important; }
.p-1 { padding: 0.25rem !important; }
.p-2 { padding: 0.5rem !important; }
.p-4 { padding: 1rem !important; }

/* ========== ACCESSIBILITY ========== */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.focus-visible:focus {
  outline: 2px solid var(--neon-cyan);
  outline-offset: 2px;
}

/* ========== FINAL ENHANCEMENT ANIMATIONS ========== */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fade-in-up 0.6s ease-out;
}

@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.scale-in {
  animation: scale-in 0.4s ease-out;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# UI COMPONENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_hero_section():
    """Create the stunning hero section with modern glassmorphism design."""
    
    # Get current market data for dynamic display
    market_status, status_type = get_market_status()
    current_asset = AppState.get_current_asset()
    asset_info = MAJOR_EQUITIES[current_asset]
    display_symbol = get_display_symbol(current_asset)
    
    st.markdown(f"""
    <div class="hero-container">
        <div class="text-center">
            <h1 class="hero-title">MarketLens Pro</h1>
            <p class="hero-subtitle">Enterprise SPX & Equities Forecasting</p>
            <p class="hero-meta">v{VERSION} • Max Pointe Consulting • Professional Trading Analytics</p>
        </div>
        
        <div class="metric-grid" style="margin-top: 2rem;">
            <div class="metric-card hover-lift">
                <div class="asset-icon">{asset_info['icon']}</div>
                <div class="metric-label">Current Asset</div>
                <div class="metric-value">{display_symbol}</div>
                <div class="metric-change metric-neutral">{asset_info['name']}</div>
            </div>
            
            <div class="metric-card hover-lift">
                <div class="asset-icon">📊</div>
                <div class="metric-label">Market Status</div>
                <div class="metric-value">LIVE</div>
                <div class="metric-change">
                    <span class="status-chip status-{status_type}">{market_status}</span>
                </div>
            </div>
            
            <div class="metric-card hover-lift">
                <div class="asset-icon">⚡</div>
                <div class="metric-label">Analysis Date</div>
                <div class="metric-value">{AppState.get_forecast_date().strftime('%m/%d')}</div>
                <div class="metric-change metric-neutral">{AppState.get_forecast_date().strftime('%B %d, %Y')}</div>
            </div>
            
            <div class="metric-card hover-lift">
                <div class="asset-icon">🎯</div>
                <div class="metric-label">System Status</div>
                <div class="metric-value">READY</div>
                <div class="metric-change metric-positive">
                    <span class="status-chip status-live">🟢 All Systems Go</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_navigation_sidebar():
    """Create the futuristic navigation sidebar."""
    
    with st.sidebar:
        # Company branding with neon effect
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem 1rem; margin-bottom: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈</div>
            <h2 style="color: #ffffff; margin: 0; font-size: 1.5rem; font-weight: 900; 
                       background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {APP_NAME}
            </h2>
            <p style="color: rgba(255, 255, 255, 0.7); margin: 0.5rem 0; font-size: 0.875rem;">
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
            ("📊", "Dashboard", "Real-time overview"),
            ("⚓", "Anchors", "Price anchors"),
            ("🎯", "Forecasts", "Projection tables"),
            ("📡", "Signals", "Live alerts"),
            ("📜", "Contracts", "Options analysis"),
            ("🌟", "Fibonacci", "Technical levels"),
            ("📤", "Export", "Data export"),
            ("⚙️", "Settings", "Configuration")
        ]
        
        selected_page = st.radio(
            "",
            options=[f"{icon} {name}" for icon, name, _ in nav_options],
            label_visibility="collapsed"
        )
        
        # Asset selector
        st.markdown('<div class="glass-panel" style="padding: 1.5rem; margin: 1.5rem 0;">', unsafe_allow_html=True)
        st.markdown("#### 📈 Trading Asset")
        
        selected_asset = st.selectbox(
            "Select primary trading instrument",
            options=list(MAJOR_EQUITIES.keys()),
            format_func=lambda x: f"{MAJOR_EQUITIES[x]['icon']} {get_display_symbol(x)} - {MAJOR_EQUITIES[x]['name']}",
            key="asset_selector"
        )
        
        # Update asset if changed
        if selected_asset != AppState.get_current_asset():
            AppState.set_current_asset(selected_asset)
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Date selector
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
        
        # Quick actions
        st.markdown("#### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", key="refresh_btn", help="Refresh all data"):
                AppState.refresh_data()
                st.rerun()
        
        with col2:
            if st.button("📋 Export", key="export_btn", help="Quick export"):
                st.success("Export ready!")
        
        # System status
        st.markdown('<div class="glass-panel" style="padding: 1rem; margin: 1.5rem 0;">', unsafe_allow_html=True)
        st.markdown("#### ⚡ System Status")
        
        system_checks = verify_system_ready()
        all_good = all(system_checks.values())
        
        status_color = "success" if all_good else "warning"
        status_text = "All Systems Operational" if all_good else "Partial Ready"
        status_icon = "🟢" if all_good else "🟡"
        
        st.markdown(f"""
        <div class="status-chip status-{status_color}" style="width: 100%; justify-content: center;">
            {status_icon} {status_text}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return selected_page

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

def create_section_header(title: str, description: str = "", icon: str = "🎯"):
    """Create a beautiful section header with modern styling."""
    
    desc_html = f'<p class="section-subtitle">{description}</p>' if description else ""
    
    return f"""
    <div class="section-header">
        <div class="asset-icon-large">{icon}</div>
        <h2 class="section-title">{title}</h2>
        {desc_html}
    </div>
    """

def create_status_badge(text: str, status_type: str = "neutral"):
    """Create a status badge with appropriate styling."""
    return f'<span class="status-chip status-{status_type}">{text}</span>'

def create_chart_container(title: str = ""):
    """Create a chart container with beautiful styling."""
    title_html = f'<h3 style="color: #ffffff; margin: 0 0 1rem 0; text-align: center;">{title}</h3>' if title else ""
    
    st.markdown(f"""
    <div class="chart-container">
        {title_html}
    </div>
    """, unsafe_allow_html=True)

def create_enhanced_dataframe(df, title: str = ""):
    """Create an enhanced dataframe display with beautiful styling."""
    title_html = f'<h3 style="color: #ffffff; margin: 0 0 1rem 0;">{title}</h3>' if title else ""
    
    st.markdown(f"""
    <div class="dataframe-container">
        {title_html}
    </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# MAIN UI INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════════════

# Create the hero section
create_hero_section()

# Create navigation and get selected page
selected_page = create_navigation_sidebar()

# Add section divider
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# Test that Part 2C functions are working
st.markdown('<div style="color: #ffffff !important; text-align: center; padding: 1rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; margin: 1rem 0;"><h3 style="color: #10b981 !important;">✅ Part 2C UI Functions Loaded Successfully</h3><p style="color: rgba(255,255,255,0.8) !important;">Complete UI system with hero section, navigation, and utility functions is now active.</p></div>', unsafe_allow_html=True)
