# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - ENTERPRISE SPX & EQUITIES FORECASTING PLATFORM  
# PART 1: CORE CONFIGURATION & GLOBAL SETTINGS (FULLY FIXED)
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

# ───────────────────────────────  USER INTERFACE  ───────────────────────────────
# Simple title without complex styling
st.title(f"📈 {APP_NAME}")
st.subheader(f"{TAGLINE} - v{VERSION}")

# Basic metrics without complex HTML
col1, col2, col3 = st.columns(3)

with col1:
    market_status, _ = get_market_status()
    st.metric("Market Status", market_status)

with col2:
    current_time = datetime.now(CT).strftime("%I:%M:%S %p CT")
    st.metric("Current Time", current_time)

with col3:
    st.metric("Company", COMPANY)

# Sidebar controls with proper contrast
with st.sidebar:
    st.title("🎛️ Controls")
    
    # Asset selector with proper visibility
    st.subheader("Select Asset:")
    selected_asset = st.selectbox(
        "Choose trading instrument",
        options=list(MAJOR_EQUITIES.keys()),
        format_func=lambda x: f"{MAJOR_EQUITIES[x]['icon']} {get_display_symbol(x)} - {MAJOR_EQUITIES[x]['name']}",
        label_visibility="collapsed"
    )

    # Date selector with proper visibility
    st.subheader("Forecast Date:")
    forecast_date = st.date_input(
        "Analysis date", 
        value=date.today(),
        max_value=date.today(),
        label_visibility="collapsed"
    )

# Update session state
AppState.set_current_asset(selected_asset)
AppState.set_forecast_date(forecast_date)

# Get slope information for the selected asset (INTERNAL ONLY - NOT DISPLAYED)
slopes = get_asset_slopes(selected_asset)
display_symbol = get_display_symbol(selected_asset)

# Asset information display (PROFESSIONAL - NO SLOPES SHOWN)
asset_info = MAJOR_EQUITIES[selected_asset]

st.subheader(f"{asset_info['icon']} {display_symbol} Analysis")

# Professional grid layout
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Asset Symbol", display_symbol)

with col2:
    st.metric("Asset Name", asset_info['name'])

with col3:
    st.metric("Sector", asset_info['type'])

with col4:
    st.metric("Analysis Date", forecast_date.strftime('%b %d, %Y'))

# Second row - Professional trading information
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Previous Session", previous_trading_day(forecast_date).strftime('%b %d, %Y'))

with col2:
    st.metric("Market Session", "Regular Trading Hours")

with col3:
    st.metric("Time Zone", "Central Time (CT)")

# System status display
system_checks = verify_system_ready()
all_ready = all(system_checks.values())

if all_ready:
    st.success("🟢 System Operational")
else:
    st.warning("🟡 System Initializing")

# Professional footer
st.markdown("---")
st.markdown(f"**{APP_NAME}** v{VERSION} | {COMPANY} | Professional Trading Analytics Platform")








# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2A: FOUNDATION CSS & CORE STYLING (CONSUMER READY)
# Professional Trading Interface - Visual Foundation
# ═══════════════════════════════════════════════════════════════════════════════════════

# Professional UI styling foundation
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ========== PROFESSIONAL DESIGN SYSTEM ========== */
:root {
  /* Professional Color Palette */
  --primary-blue: #0ea5e9;
  --primary-purple: #8b5cf6;
  --success-green: #10b981;
  --warning-orange: #f59e0b;
  --error-red: #ef4444;
  --neutral-gray: #64748b;
  
  /* Glass Effect System */
  --glass-light: rgba(255, 255, 255, 0.1);
  --glass-border: rgba(255, 255, 255, 0.2);
  --glass-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
  
  /* Professional Surfaces */
  --surface-dark: #0f172a;
  --surface-medium: #1e293b;
  --surface-light: #334155;
  
  /* Typography */
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.8);
  --text-muted: rgba(255, 255, 255, 0.6);
}

/* ========== GLOBAL STYLING ========== */
html, body, .stApp {
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  background-attachment: fixed;
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.stApp {
  background: 
    radial-gradient(circle at 20% 20%, rgba(14, 165, 233, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
    linear-gradient(135deg, var(--surface-dark) 0%, var(--surface-medium) 100%);
  min-height: 100vh;
}

/* ========== PROFESSIONAL BACKGROUND EFFECTS ========== */
.stApp::before {
  content: '';
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: 
    radial-gradient(1px 1px at 25px 35px, rgba(255, 255, 255, 0.1), transparent),
    radial-gradient(1px 1px at 75px 85px, rgba(255, 255, 255, 0.08), transparent),
    radial-gradient(1px 1px at 125px 45px, rgba(255, 255, 255, 0.06), transparent);
  background-repeat: repeat;
  background-size: 200px 250px;
  animation: professional-float 30s linear infinite;
  pointer-events: none;
  z-index: 1;
  opacity: 0.6;
}

@keyframes professional-float {
  from { background-position: 0% 0%; }
  to { background-position: 200px 250px; }
}

/* ========== TEXT VISIBILITY SYSTEM ========== */
/* Ensure all text is properly visible */
.stApp, .stApp *, .main *, .block-container *,
h1, h2, h3, h4, h5, h6, p, span, div, label,
.stMarkdown, .stMarkdown * {
  color: var(--text-primary) !important;
}

/* Headers with professional styling */
h1 {
  font-size: 2.5rem !important;
  font-weight: 800 !important;
  color: var(--text-primary) !important;
  margin-bottom: 1rem !important;
}

h2 {
  font-size: 1.875rem !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  margin-bottom: 0.75rem !important;
}

h3 {
  font-size: 1.5rem !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
  margin-bottom: 0.5rem !important;
}

/* ========== PROFESSIONAL FORM ELEMENTS ========== */
/* Sidebar form elements with perfect visibility */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, 
    rgba(15, 23, 42, 0.95) 0%, 
    rgba(30, 41, 59, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-right: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
}

/* PERFECT FORM VISIBILITY - Consumer Ready */
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stSelectbox input,
section[data-testid="stSidebar"] .stDateInput input,
section[data-testid="stSidebar"] .stDateInput > div > div,
.stSelectbox > div > div,
.stSelectbox input,
.stDateInput input,
.stDateInput > div > div {
  background: #ffffff !important;
  color: #000000 !important;
  border: 1px solid #cccccc !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
}

/* Dropdown options visibility */
.stSelectbox [role="listbox"],
.stSelectbox [role="option"],
.stSelectbox ul,
.stSelectbox li {
  background: #ffffff !important;
  color: #000000 !important;
}

.stSelectbox [role="option"]:hover {
  background: #f0f9ff !important;
  color: #000000 !important;
}

/* Calendar popup visibility */
.stDateInput .stCalendar,
.stDateInput .stCalendar * {
  background: #ffffff !important;
  color: #000000 !important;
}

/* ========== PROFESSIONAL METRICS ========== */
[data-testid="metric-container"] {
  background: var(--glass-light);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: var(--glass-shadow);
  transition: all 0.3s ease;
}

[data-testid="metric-container"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

[data-testid="metric-container"] > div {
  color: var(--text-primary) !important;
}

/* ========== PROFESSIONAL BUTTONS ========== */
.stButton > button {
  background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-purple) 100%);
  border: none;
  border-radius: 10px;
  color: #ffffff !important;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.875rem;
}

.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(14, 165, 233, 0.4);
}

/* ========== PROFESSIONAL ALERTS ========== */
.stSuccess {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border-left: 4px solid var(--success-green);
  border-radius: 8px;
  color: var(--text-primary) !important;
}

.stWarning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%);
  border-left: 4px solid var(--warning-orange);
  border-radius: 8px;
  color: var(--text-primary) !important;
}

.stError {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%);
  border-left: 4px solid var(--error-red);
  border-radius: 8px;
  color: var(--text-primary) !important;
}

.stInfo {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
  border-left: 4px solid var(--primary-blue);
  border-radius: 8px;
  color: var(--text-primary) !important;
}

/* ========== PROFESSIONAL SIDEBAR ========== */
section[data-testid="stSidebar"] > div {
  padding-top: 1rem;
  background: transparent;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
  color: var(--text-primary) !important;
}

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
  h1 { font-size: 2rem !important; }
  h2 { font-size: 1.5rem !important; }
  h3 { font-size: 1.25rem !important; }
  
  [data-testid="metric-container"] {
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  h1 { font-size: 1.75rem !important; }
  h2 { font-size: 1.25rem !important; }
  
  .stButton > button {
    padding: 0.5rem 1rem;
    font-size: 0.75rem;
  }
}

/* ========== PROFESSIONAL POLISH ========== */
.stMarkdown > div {
  color: var(--text-primary) !important;
}

/* Clean scrollbars */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--surface-dark);
}

::-webkit-scrollbar-thumb {
  background: var(--surface-light);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--glass-border);
}

/* ========== ACCESSIBILITY ========== */
.stApp *:focus {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
}

/* ========== PROFESSIONAL SPACING ========== */
.block-container {
  padding-top: 2rem;
  padding-bottom: 2rem;
  max-width: 1200px;
}

/* ========== FINAL POLISH ========== */
.stApp .main .block-container {
  background: transparent;
}
</style>
""", unsafe_allow_html=True)

# Professional visual confirmation
st.markdown("""
<div style="
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  margin: 2rem 0;
  backdrop-filter: blur(10px);
">
  <h3 style="color: #0ea5e9 !important; margin: 0 0 0.5rem 0;">Professional Interface Active</h3>
  <p style="color: rgba(255, 255, 255, 0.8) !important; margin: 0;">
    Visual foundation loaded with professional styling and optimal form visibility.
  </p>
</div>
""", unsafe_allow_html=True)
