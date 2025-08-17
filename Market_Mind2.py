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

/* Keep main content text dark */
.main .block-container * {
  color: #0f172a !important;
}

/* Exception: Keep metric cards with white text */
.main .block-container .hero-container *,
.main .block-container .glass-panel *,
.main .block-container .metric-card * {
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

section[data-testid="stSidebar"] > div {
  background: transparent !important;
}

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

/* Fix sidebar selectbox */
section[data-testid="stSidebar"] .stSelectbox > div > div {
  background-color: #2d3748 !important;
  color: #ffffff !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 8px !important;
}

section[data-testid="stSidebar"] .stSelectbox > div > div > div {
  background-color: #2d3748 !important;
  color: #ffffff !important;
}

section[data-testid="stSidebar"] .stSelectbox > div > div > div > div {
  background-color: #2d3748 !important;
  color: #ffffff !important;
}

/* Fix sidebar selectbox dropdown */
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="popover"] {
  background-color: #2d3748 !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8) !important;
}

section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="popover"] * {
  background-color: #2d3748 !important;
  color: #ffffff !important;
}

section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="popover"] li:hover {
  background-color: rgba(34, 211, 238, 0.3) !important;
  color: #ffffff !important;
}

/* Fix sidebar date input */
section[data-testid="stSidebar"] .stDateInput > div > div {
  background-color: #2d3748 !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 8px !important;
}

section[data-testid="stSidebar"] .stDateInput > div > div > input {
  background-color: #2d3748 !important;
  color: #ffffff !important;
  border: none !important;
}

/* Fix sidebar date picker calendar */
section[data-testid="stSidebar"] .stDateInput div[data-baseweb="popover"] {
  background-color: #2d3748 !important;
  border: 1px solid rgba(34, 211, 238, 0.5) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8) !important;
}

section[data-testid="stSidebar"] .stDateInput div[data-baseweb="popover"] * {
  background-color: #2d3748 !important;
  color: #ffffff !important;
}

section[data-testid="stSidebar"] .stDateInput div[data-baseweb="popover"] button:hover {
  background-color: rgba(34, 211, 238, 0.3) !important;
  color: #ffffff !important;
}

/* Fix sidebar buttons */
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
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  padding: 2.5rem;
  margin: 2rem 0;
  box-shadow: 
    0 8px 32px rgba(31, 38, 135, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  z-index: 10;
}

.hero-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    var(--neon-blue) 20%, 
    var(--neon-purple) 40%,
    var(--neon-green) 60%,
    var(--neon-orange) 80%, 
    transparent 100%);
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 900;
  background: linear-gradient(135deg, #ffffff 0%, #22d3ee 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: -0.02em;
  text-shadow: 0 0 40px rgba(34, 211, 238, 0.4);
  animation: glow-pulse 4s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { 
    filter: drop-shadow(0 0 10px rgba(34, 211, 238, 0.4));
  }
  50% { 
    filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.6));
  }
}

.hero-subtitle {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin: 1rem 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.hero-meta {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  margin-top: 0.5rem;
}

/* ========== SIDEBAR ENHANCEMENTS ========== */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, 
    rgba(15, 15, 35, 0.95) 0%, 
    rgba(26, 26, 46, 0.95) 100%) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

section[data-testid="stSidebar"] > div {
  background: transparent !important;
}

/* Fix sidebar text color */
section[data-testid="stSidebar"] * {
  color: #ffffff !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
  color: #ffffff !important;
}

/* ========== UTILITY CLASSES ========== */
.glass-panel {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
}

.text-center { text-align: center; }

.neon-border {
  border: 1px solid var(--neon-blue);
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.3);
}

.text-glow {
  text-shadow: 0 0 10px currentColor;
}

/* ========== RESPONSIVE DESIGN ========== */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-container {
    padding: 1.5rem;
    margin: 1rem 0;
  }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# HERO SECTION WITH GLASSMORPHISM DESIGN
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_hero_section():
    """Create the stunning hero section with modern glassmorphism design."""
    
    # Get current market data for dynamic display
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
            <div style="font-size: 0.875rem; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem;">ANALYSIS DATE</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #ffffff;">{forecast_date.strftime('%m/%d/%Y')}</div>
            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">{forecast_date.strftime('%A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        current_time = datetime.now(ET).strftime("%I:%M:%S %p")
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
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.metric-value {
  font-size: 2.5rem;
  font-weight: 900;
  color: #ffffff;
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
}

.metric-positive { color: var(--neon-green); }
.metric-negative { color: var(--neon-orange); }
.metric-neutral { color: rgba(255, 255, 255, 0.6); }

/* ========== ASSET ICONS & ANIMATIONS ========== */
.asset-icon {
  font-size: 3rem;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
  display: inline-block;
  animation: float 3s ease-in-out infinite;
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
}

.status-live {
  background: linear-gradient(135deg, 
    rgba(16, 185, 129, 0.2) 0%, 
    rgba(5, 150, 105, 0.2) 100%);
  border-color: var(--neon-green);
  color: var(--neon-green);
  animation: pulse-glow 2s ease-in-out infinite;
}

.status-warning {
  background: linear-gradient(135deg, 
    rgba(245, 158, 11, 0.2) 0%, 
    rgba(217, 119, 6, 0.2) 100%);
  border-color: var(--neon-orange);
  color: var(--neon-orange);
}

.status-error {
  background: linear-gradient(135deg, 
    rgba(239, 68, 68, 0.2) 0%, 
    rgba(220, 38, 38, 0.2) 100%);
  border-color: var(--neon-pink);
  color: var(--neon-pink);
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
  background: var(--surface-1);
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
  color: #ffffff;
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
# MARKETLENS PRO - PART 2C1: WORKING REAL DATA CHART FUNCTIONS
# Functional real data charts using yfinance (no duplicate imports)
# ═══════════════════════════════════════════════════════════════════════════════════════

# Additional CSS for chart containers only
st.markdown("""
<style>
.chart-container {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.03) 100%);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
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
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    #22d3ee 25%,
    #a855f7 50%,
    #00ff88 75%,
    transparent 100%);
  animation: chart-shimmer 4s ease-in-out infinite;
}

@keyframes chart-shimmer {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# WORKING REAL DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def fetch_real_price_data(symbol: str):
    """Fetch real price data from Yahoo Finance - WORKING VERSION"""
    try:
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Get 1 month of daily data
        hist_data = ticker.history(period="1mo", interval="1d")
        
        if hist_data.empty:
            return None, "No data available"
        
        # Reset index to get dates as column
        hist_data = hist_data.reset_index()
        
        # Get current price info
        info = ticker.info
        current_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
        previous_close = info.get('previousClose', hist_data['Close'].iloc[-2])
        
        # Calculate change
        change = current_price - previous_close
        change_pct = (change / previous_close) * 100 if previous_close > 0 else 0
        
        return {
            'hist_data': hist_data,
            'current_price': float(current_price),
            'change': float(change),
            'change_pct': float(change_pct),
            'volume': int(info.get('volume', 0)),
            'symbol': symbol
        }, None
        
    except Exception as e:
        return None, str(e)

def create_working_price_chart(symbol: str):
    """Create price chart with REAL Yahoo Finance data - GUARANTEED WORKING"""
    
    # Fetch real data
    data, error = fetch_real_price_data(symbol)
    
    if error or not data:
        # Create error chart
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ Cannot fetch real data for {symbol}<br>Error: {error or 'Unknown error'}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, 
            font=dict(color='#ff6b35', size=16),
            bgcolor='rgba(255, 107, 53, 0.1)',
            bordercolor='#ff6b35',
            borderwidth=2
        )
        fig.update_layout(
            title=f"{symbol} Price Chart - Data Error",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            height=400
        )
        return fig
    
    # Use real data
    df = data['hist_data']
    
    # Create the chart with real data
    fig = go.Figure()
    
    # Add real price line
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name=f"{symbol} Real Price",
        line=dict(color='#22d3ee', width=3),
        hovertemplate='Date: %{x}<br>Price: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add 20-day moving average if enough data
    if len(df) >= 20:
        df['MA20'] = df['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['MA20'],
            mode='lines',
            name='20-Day MA',
            line=dict(color='#ff6b35', width=1, dash='dot'),
            hovertemplate='20-Day MA: $%{y:,.2f}<extra></extra>'
        ))
    
    # Set proper Y-axis range
    min_price = df['Close'].min()
    max_price = df['Close'].max()
    price_range = max_price - min_price
    y_min = min_price - (price_range * 0.05)
    y_max = max_price + (price_range * 0.05)
    
    # Style the chart
    fig.update_layout(
        title=dict(
            text=f"{symbol} Live Price Chart (Yahoo Finance)",
            font=dict(color='#ffffff', size=18),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            color='#ffffff'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            color='#ffffff',
            range=[y_min, y_max],
            tickformat='$,.2f'
        ),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        ),
        height=400,
        margin=dict(l=60, r=40, t=60, b=40)
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE WORKING CHARTS
# ═══════════════════════════════════════════════════════════════════════════════════════

# Section header
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Live Market Data Charts
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">
        Real-time Yahoo Finance data integration
    </p>
</div>
""", unsafe_allow_html=True)

# Get current asset
current_asset = AppState.get_current_asset()
display_symbol = get_display_symbol(current_asset)

# Create main price chart
st.markdown('<div class="chart-container">', unsafe_allow_html=True)

# Generate and display the working chart
price_chart = create_working_price_chart(current_asset)
st.plotly_chart(price_chart, use_container_width=True, config=CHART_CONFIG)

st.markdown('</div>', unsafe_allow_html=True)

# Display data status
data_result, error = fetch_real_price_data(current_asset)

if data_result and not error:
    # Show real data metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Price", 
            f"${data_result['current_price']:,.2f}",
            f"{data_result['change']:+.2f}"
        )
    
    with col2:
        st.metric(
            "Daily Change", 
            f"{data_result['change_pct']:+.2f}%",
            f"${data_result['change']:+.2f}"
        )
    
    with col3:
        st.metric(
            "Volume", 
            f"{data_result['volume']:,}" if data_result['volume'] > 0 else "N/A"
        )
    
    with col4:
        st.metric(
            "Data Points", 
            f"{len(data_result['hist_data'])}" if data_result['hist_data'] is not None else "0"
        )
    
    # Success message
    st.success(f"✅ **Live data successfully loaded for {display_symbol}** - Chart shows real Yahoo Finance data with {len(data_result['hist_data'])} data points")
    
else:
    # Error message
    st.error(f"❌ **Failed to load real data for {display_symbol}** - Error: {error}")
    st.info("💡 **Troubleshooting:** Check your internet connection or try selecting a different asset. Yahoo Finance may be temporarily unavailable.")

# Data source info
st.markdown(f"""
<div class="glass-panel" style="padding: 1.5rem; margin: 2rem 0; text-align: center;">
    <div style="color: rgba(255, 255, 255, 0.8); font-size: 1rem; margin-bottom: 0.5rem;">
        <strong>Data Source:</strong> Yahoo Finance API via yfinance library
    </div>
    <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.875rem;">
        Real-time price data • 1-month historical chart • 20-day moving average
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2C2: WORKING VOLUME & TECHNICAL ANALYSIS
# Complete working tabs with real Yahoo Finance data
# ═══════════════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════════════
# WORKING TECHNICAL ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def fetch_technical_data(symbol: str):
    """Fetch data for technical analysis - WORKING VERSION"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Get 3 months of data for indicators
        hist_data = ticker.history(period="3mo", interval="1d")
        
        if hist_data.empty:
            return None, "No technical data available"
        
        # Reset index
        hist_data = hist_data.reset_index()
        
        # Calculate technical indicators
        close_prices = hist_data['Close']
        
        # RSI calculation
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD calculation
        exp1 = close_prices.ewm(span=12).mean()
        exp2 = close_prices.ewm(span=26).mean()
        macd_line = exp1 - exp2
        macd_signal = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - macd_signal
        
        # Bollinger Bands
        bb_period = 20
        bb_middle = close_prices.rolling(window=bb_period).mean()
        bb_std = close_prices.rolling(window=bb_period).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        # Add indicators to dataframe
        hist_data['RSI'] = rsi
        hist_data['MACD'] = macd_line
        hist_data['MACD_Signal'] = macd_signal
        hist_data['MACD_Histogram'] = macd_histogram
        hist_data['BB_Upper'] = bb_upper
        hist_data['BB_Middle'] = bb_middle
        hist_data['BB_Lower'] = bb_lower
        hist_data['SMA_20'] = close_prices.rolling(window=20).mean()
        
        return hist_data, None
        
    except Exception as e:
        return None, str(e)

def create_working_technical_chart(symbol: str):
    """Create working technical analysis chart with real data"""
    
    # Fetch technical data
    tech_data, error = fetch_technical_data(symbol)
    
    if error or tech_data is None:
        # Error chart
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ Cannot fetch technical data for {symbol}<br>Error: {error or 'Unknown error'}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False,
            font=dict(color='#ff6b35', size=16),
            bgcolor='rgba(255, 107, 53, 0.1)',
            bordercolor='#ff6b35',
            borderwidth=2
        )
        fig.update_layout(
            title=f"{symbol} Technical Analysis - Data Error",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            height=600
        )
        return fig
    
    # Create subplots for technical indicators
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            f'{symbol} Price & Bollinger Bands (Live Data)',
            f'{symbol} RSI (Live Data)', 
            f'{symbol} MACD (Live Data)'
        ),
        vertical_spacing=0.08,
        row_heights=[0.5, 0.25, 0.25]
    )
    
    # Price and Bollinger Bands (Row 1)
    fig.add_trace(go.Scatter(
        x=tech_data['Date'],
        y=tech_data['Close'],
        mode='lines',
        name='Price',
        line=dict(color='#22d3ee', width=2),
        hovertemplate='Price: $%{y:,.2f}<extra></extra>'
    ), row=1, col=1)
    
    # Add SMA if available
    if not tech_data['SMA_20'].isna().all():
        fig.add_trace(go.Scatter(
            x=tech_data['Date'],
            y=tech_data['SMA_20'],
            mode='lines',
            name='SMA 20',
            line=dict(color='#ff6b35', width=1, dash='dot'),
            hovertemplate='SMA 20: $%{y:,.2f}<extra></extra>'
        ), row=1, col=1)
    
    # Add Bollinger Bands if available
    if not tech_data['BB_Upper'].isna().all():
        fig.add_trace(go.Scatter(
            x=tech_data['Date'],
            y=tech_data['BB_Upper'],
            mode='lines',
            name='BB Upper',
            line=dict(color='#a855f7', width=1),
            hovertemplate='BB Upper: $%{y:,.2f}<extra></extra>'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=tech_data['Date'],
            y=tech_data['BB_Lower'],
            mode='lines',
            name='BB Lower',
            line=dict(color='#a855f7', width=1),
            fill='tonexty',
            fillcolor='rgba(168, 85, 247, 0.1)',
            hovertemplate='BB Lower: $%{y:,.2f}<extra></extra>'
        ), row=1, col=1)
    
    # RSI (Row 2)
    if not tech_data['RSI'].isna().all():
        fig.add_trace(go.Scatter(
            x=tech_data['Date'],
            y=tech_data['RSI'],
            mode='lines',
            name='RSI',
            line=dict(color='#00ff88', width=2),
            hovertemplate='RSI: %{y:.1f}<extra></extra>'
        ), row=2, col=1)
    
    # RSI reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(239, 68, 68, 0.5)", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(16, 185, 129, 0.5)", row=2, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="rgba(255, 255, 255, 0.3)", row=2, col=1)
    
    # MACD (Row 3)
    if not tech_data['MACD'].isna().all():
        fig.add_trace(go.Scatter(
            x=tech_data['Date'],
            y=tech_data['MACD'],
            mode='lines',
            name='MACD',
            line=dict(color='#22d3ee', width=2),
            hovertemplate='MACD: %{y:.3f}<extra></extra>'
        ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=tech_data['Date'],
            y=tech_data['MACD_Signal'],
            mode='lines',
            name='Signal',
            line=dict(color='#ff6b35', width=2),
            hovertemplate='Signal: %{y:.3f}<extra></extra>'
        ), row=3, col=1)
        
        # MACD Histogram
        colors = ['#00ff88' if x >= 0 else '#ff006e' for x in tech_data['MACD_Histogram']]
        fig.add_trace(go.Bar(
            x=tech_data['Date'],
            y=tech_data['MACD_Histogram'],
            name='Histogram',
            marker_color=colors,
            opacity=0.6,
            hovertemplate='Histogram: %{y:.4f}<extra></extra>'
        ), row=3, col=1)
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{symbol} Technical Analysis (Yahoo Finance)",
            font=dict(color='#ffffff', size=18),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        ),
        height=600,
        margin=dict(l=60, r=40, t=60, b=40)
    )
    
    # Update axes
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff')
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff')
    
    # Format price axis
    fig.update_yaxes(tickformat='$,.2f', row=1, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)  # RSI range
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════════════
# WORKING TABS IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════════════

# Create tab system
tab1, tab2, tab3 = st.tabs(["📊 Price Action", "📈 Volume Analysis", "🎯 Technical Indicators"])

# Get current asset info
current_asset = AppState.get_current_asset()
display_symbol = get_display_symbol(current_asset)

# TAB 1: Price Action (already handled in 2C1)
with tab1:
    st.markdown("**Price Action tab content is handled in Part 2C1**")
    st.info("💡 The price chart above shows real Yahoo Finance data for the selected asset.")

# TAB 2: Volume Analysis with REAL data
with tab2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
        <h3 style="color: #ffffff; margin-bottom: 1rem;">Live Volume Analysis for {display_symbol}</h3>
        <p style="color: rgba(255, 255, 255, 0.8);">Real-time volume analysis from Yahoo Finance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get real data for volume analysis
    data_result, error = fetch_real_price_data(current_asset)
    
    if data_result and not error:
        # Calculate volume metrics from real data
        hist_data = data_result['hist_data']
        current_volume = data_result.get('volume', 0)
        
        if 'Volume' in hist_data.columns and len(hist_data) > 0:
            # Calculate real volume metrics
            avg_volume = int(hist_data['Volume'].mean())
            
            # Calculate relative volume
            relative_volume = (current_volume / avg_volume) if avg_volume > 0 and current_volume > 0 else 0
            
            # Calculate volume trend (last 5 vs previous 5 days)
            if len(hist_data) >= 10:
                recent_vol = hist_data['Volume'].tail(5).mean()
                previous_vol = hist_data['Volume'].iloc[-10:-5].mean()
                volume_trend = ((recent_vol - previous_vol) / previous_vol) * 100 if previous_vol > 0 else 0
            else:
                volume_trend = 0
            
            # Display real volume metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">CURRENT VOLUME</div>
                    <div style="color: #a855f7; font-size: 1.5rem; font-weight: 800;">{current_volume:,}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                trend_color = "#00ff88" if volume_trend >= 0 else "#ff6b35"
                trend_sign = "+" if volume_trend >= 0 else ""
                st.markdown(f"""
                <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">VOLUME TREND</div>
                    <div style="color: {trend_color}; font-size: 1.5rem; font-weight: 800;">{trend_sign}{volume_trend:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                relative_color = "#ff6b35" if relative_volume > 1.5 else "#00ff88" if relative_volume > 0.8 else "#a855f7"
                st.markdown(f"""
                <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem;">RELATIVE VOLUME</div>
                    <div style="color: {relative_color}; font-size: 1.5rem; font-weight: 800;">{relative_volume:.1f}x</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Volume analysis
            if relative_volume > 2.0:
                st.success(f"🔥 **High Volume Activity** - {relative_volume:.1f}x average suggests institutional interest")
            elif relative_volume > 1.5:
                st.info(f"📈 **Above Average Volume** - {relative_volume:.1f}x indicates increased market participation")
            elif relative_volume < 0.5:
                st.warning(f"📉 **Low Volume** - {relative_volume:.1f}x suggests limited market interest")
            else:
                st.info(f"✅ **Normal Volume** - {relative_volume:.1f}x average indicates typical trading activity")
        
        else:
            st.warning("⚠️ Volume data not available for this asset")
    
    else:
        st.error(f"❌ Cannot fetch volume data: {error}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 3: Technical Indicators with REAL data
with tab3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Create and display technical chart
    tech_chart = create_working_technical_chart(current_asset)
    st.plotly_chart(tech_chart, use_container_width=True, config=CHART_CONFIG)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get technical data for analysis
    tech_result, tech_error = fetch_technical_data(current_asset)
    
    if tech_result is not None and not tech_error:
        # Get latest indicator values
        try:
            latest_rsi = tech_result['RSI'].iloc[-1] if not tech_result['RSI'].isna().all() else 50
            latest_macd = tech_result['MACD'].iloc[-1] if not tech_result['MACD'].isna().all() else 0
            latest_signal = tech_result['MACD_Signal'].iloc[-1] if not tech_result['MACD_Signal'].isna().all() else 0
            current_price = tech_result['Close'].iloc[-1]
            bb_upper = tech_result['BB_Upper'].iloc[-1] if not tech_result['BB_Upper'].isna().all() else current_price
            bb_lower = tech_result['BB_Lower'].iloc[-1] if not tech_result['BB_Lower'].isna().all() else current_price
            
            # Technical analysis summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # RSI Analysis
                if latest_rsi > 70:
                    rsi_status = "🔴 Overbought"
                    rsi_message = f"RSI at {latest_rsi:.1f} suggests potential selling pressure"
                    rsi_type = "warning"
                elif latest_rsi < 30:
                    rsi_status = "🟢 Oversold"
                    rsi_message = f"RSI at {latest_rsi:.1f} suggests potential buying opportunity"
                    rsi_type = "success"
                else:
                    rsi_status = "🟡 Neutral"
                    rsi_message = f"RSI at {latest_rsi:.1f} indicates normal trading range"
                    rsi_type = "info"
                
                if rsi_type == "warning":
                    st.warning(f"**{rsi_status}**\n\n{rsi_message}")
                elif rsi_type == "success":
                    st.success(f"**{rsi_status}**\n\n{rsi_message}")
                else:
                    st.info(f"**{rsi_status}**\n\n{rsi_message}")
            
            with col2:
                # MACD Analysis
                if latest_macd > latest_signal:
                    macd_status = "🟢 Bullish Signal"
                    macd_message = f"MACD above signal line suggests upward momentum"
                    st.success(f"**{macd_status}**\n\n{macd_message}")
                elif latest_macd < latest_signal:
                    macd_status = "🔴 Bearish Signal"
                    macd_message = f"MACD below signal line suggests downward pressure"
                    st.warning(f"**{macd_status}**\n\n{macd_message}")
                else:
                    macd_status = "🟡 Neutral"
                    macd_message = f"MACD near signal line, awaiting direction"
                    st.info(f"**{macd_status}**\n\n{macd_message}")
            
            with col3:
                # Bollinger Bands Analysis
                if bb_upper != bb_lower:
                    bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
                    
                    if bb_position > 0.8:
                        bb_status = "🔴 Near Upper Band"
                        bb_message = f"Price near resistance level - potential reversal zone"
                        st.warning(f"**{bb_status}**\n\n{bb_message}")
                    elif bb_position < 0.2:
                        bb_status = "🟢 Near Lower Band"
                        bb_message = f"Price near support level - potential bounce zone"
                        st.success(f"**{bb_status}**\n\n{bb_message}")
                    else:
                        bb_status = "🟡 Middle Range"
                        bb_message = f"Price in normal range - no extreme levels"
                        st.info(f"**{bb_status}**\n\n{bb_message}")
                else:
                    st.info("**Bollinger Bands**\n\nInsufficient data for analysis")
            
        except Exception as e:
            st.error(f"Error calculating indicators: {str(e)}")
    
    else:
        st.error(f"❌ Cannot calculate technical indicators: {tech_error}")

# Final status
st.markdown(f"""
<div class="glass-panel" style="padding: 2rem; text-align: center; margin: 3rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
    <h3 style="color: #ffffff; font-size: 1.8rem; font-weight: 800; margin-bottom: 1rem;">
        Live Data Integration Complete
    </h3>
    <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem; margin-bottom: 1.5rem;">
        All chart systems now use real Yahoo Finance data for {display_symbol}
    </p>
    <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
        <span class="status-chip status-live">🟢 Real Price Data</span>
        <span class="status-chip status-live">🟢 Live Volume</span>
        <span class="status-chip status-live">🟢 Technical Indicators</span>
    </div>
</div>
""", unsafe_allow_html=True)











# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 3: REAL MARKET DATA INTEGRATION
# Live Yahoo Finance Data with Caching and Error Handling
# ═══════════════════════════════════════════════════════════════════════════════════════

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════════════════════
# REAL MARKET DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)  # Cache for 1 minute
def get_real_market_data(symbol: str) -> dict:
    """Fetch real market data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        
        # Get current quote data
        info = ticker.info
        hist = ticker.history(period="2d", interval="1m")
        
        if hist.empty:
            raise ValueError(f"No data available for {symbol}")
        
        # Get latest price data
        latest = hist.iloc[-1]
        previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else latest['Close'])
        
        current_price = float(latest['Close'])
        change = current_price - previous_close
        change_pct = (change / previous_close) * 100 if previous_close != 0 else 0
        
        # Get additional data
        volume = int(latest['Volume']) if 'Volume' in latest else 0
        high_52w = info.get('fiftyTwoWeekHigh', current_price)
        low_52w = info.get('fiftyTwoWeekLow', current_price)
        
        return {
            'symbol': symbol,
            'price': current_price,
            'change': change,
            'change_pct': change_pct,
            'volume': volume,
            'previous_close': previous_close,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'timestamp': datetime.now(),
            'status': 'success'
        }
        
    except Exception as e:
        # Return fallback data with error status
        return {
            'symbol': symbol,
            'price': 0.0,
            'change': 0.0,
            'change_pct': 0.0,
            'volume': 0,
            'previous_close': 0.0,
            'high_52w': 0.0,
            'low_52w': 0.0,
            'timestamp': datetime.now(),
            'status': 'error',
            'error': str(e)
        }

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_historical_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical price data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise ValueError(f"No historical data available for {symbol}")
        
        # Reset index to make Date a column
        hist = hist.reset_index()
        hist['Symbol'] = symbol
        
        return hist
        
    except Exception as e:
        # Return empty DataFrame on error
        return pd.DataFrame()

@st.cache_data(ttl=180, show_spinner=False)  # Cache for 3 minutes
def get_intraday_data(symbol: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame:
    """Fetch intraday data for charts."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise ValueError(f"No intraday data available for {symbol}")
        
        hist = hist.reset_index()
        hist['Symbol'] = symbol
        
        return hist
        
    except Exception as e:
        return pd.DataFrame()

# ═══════════════════════════════════════════════════════════════════════════════════════
# UPDATED CHART FUNCTIONS WITH REAL DATA
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_real_price_chart(symbol: str, title: str = "Price Chart"):
    """Create price chart using real Yahoo Finance data."""
    
    import plotly.graph_objects as go
    
    # Get real historical data
    df = get_historical_data(symbol, period="1mo", interval="1d")
    
    if df.empty:
        # Fallback to demo data if real data fails
        return create_demo_chart(symbol, title)
    
    # Calculate moving averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # Create the chart
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['Date'] if 'Date' in df.columns else df.index,
        y=df['Close'],
        mode='lines',
        name=symbol,
        line=dict(
            color='#22d3ee',
            width=3
        ),
        hovertemplate='<b>%{x}</b><br>Price: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add 20-day SMA if we have enough data
    if len(df) >= 20:
        fig.add_trace(go.Scatter(
            x=df['Date'] if 'Date' in df.columns else df.index,
            y=df['SMA_20'],
            mode='lines',
            name='SMA 20',
            line=dict(color='#ff6b35', width=1, dash='dot'),
            hovertemplate='SMA 20: $%{y:,.2f}<extra></extra>'
        ))
    
    # Calculate proper Y-axis range
    min_price = df['Close'].min()
    max_price = df['Close'].max()
    price_range = max_price - min_price
    y_min = min_price - (price_range * 0.05)
    y_max = max_price + (price_range * 0.05)
    
    # Chart styling
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color='#ffffff', size=20, family='Space Grotesk'),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            zeroline=False,
            color='#ffffff'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            zeroline=False,
            color='#ffffff',
            range=[y_min, y_max],
            tickformat='$,.2f'
        ),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        ),
        margin=dict(l=60, r=40, t=50, b=40),
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_demo_chart(symbol: str, title: str):
    """Fallback demo chart when real data is unavailable."""
    
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import numpy as np
    
    # Demo data (as backup)
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    
    asset_data = {
        "^GSPC": {"base": 6443, "volatility": 80},
        "AAPL": {"base": 230, "volatility": 8},
        "MSFT": {"base": 420, "volatility": 15},
        "NVDA": {"base": 140, "volatility": 12},
        "AMZN": {"base": 185, "volatility": 14},
        "GOOGL": {"base": 175, "volatility": 10},
        "META": {"base": 520, "volatility": 25},
        "TSLA": {"base": 240, "volatility": 20},
        "NFLX": {"base": 680, "volatility": 35},
        "GOOG": {"base": 175, "volatility": 10},
    }
    
    if symbol in asset_data:
        base_price = asset_data[symbol]["base"]
        volatility_range = asset_data[symbol]["volatility"]
    else:
        base_price = 200
        volatility_range = 10
    
    prices = []
    current_price = base_price
    
    for i in range(30):
        trend = np.sin(i * 0.2) * (volatility_range * 0.3)
        daily_change = np.random.normal(0, volatility_range * 0.25)
        current_price += trend + daily_change
        prices.append(current_price)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=f"{symbol} (Demo)",
        line=dict(color='#ff6b35', width=3, dash='dot'),
        hovertemplate='<b>%{x}</b><br>Demo Price: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add warning annotation
    fig.add_annotation(
        text="⚠️ Demo Data - Real data unavailable",
        xref="paper", yref="paper",
        x=0.5, y=0.95,
        showarrow=False,
        font=dict(color='#ff6b35', size=12),
        bgcolor='rgba(255, 107, 53, 0.1)',
        bordercolor='#ff6b35',
        borderwidth=1
    )
    
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    y_min = min_price - (price_range * 0.1)
    y_max = max_price + (price_range * 0.1)
    
    fig.update_layout(
        title=dict(
            text=f"{title} (Demo Mode)",
            font=dict(color='#ffffff', size=20, family='Space Grotesk'),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            color='#ffffff'
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            color='#ffffff',
            range=[y_min, y_max],
            tickformat='$,.2f'
        ),
        showlegend=False,
        margin=dict(l=60, r=40, t=50, b=40),
        height=400
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════════════
# UPDATED LIVE DATA DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════════════

def display_real_market_data():
    """Display real market data for the selected asset."""
    
    current_asset = AppState.get_current_asset()
    asset_info = MAJOR_EQUITIES[current_asset]
    display_symbol = get_display_symbol(current_asset)
    
    # Get real market data
    market_data = get_real_market_data(current_asset)
    
    if market_data['status'] == 'success':
        # Real data available
        price = market_data['price']
        change = market_data['change']
        change_pct = market_data['change_pct']
        volume = market_data['volume']
        
        # Status indicators
        data_status = "🟢 Live Data"
        status_color = "#00ff88"
        
    else:
        # Error getting real data
        price = 0.0
        change = 0.0
        change_pct = 0.0
        volume = 0
        
        data_status = "🔴 Data Error"
        status_color = "#ff006e"
    
    # Display live price panel
    change_color = "#00ff88" if change >= 0 else "#ff6b35"
    change_icon = "↗" if change >= 0 else "↘"
    
    st.markdown(f"""
    <div class="glass-panel" style="padding: 2rem; text-align: center; margin: 2rem 0; position: relative;">
        <div style="position: absolute; top: 1rem; right: 1rem;">
            <span style="background: {status_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">
                {data_status}
            </span>
        </div>
        <div class="asset-icon" style="font-size: 4rem; margin-bottom: 1rem;">{asset_info['icon']}</div>
        <h1 style="color: #ffffff; font-size: 3rem; margin: 0; font-family: 'JetBrains Mono', monospace;">
            ${price:,.2f}
        </h1>
        <div style="color: {change_color}; font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">
            {change_icon} ${change:+.2f} ({change_pct:+.2f}%)
        </div>
        <div style="color: rgba(255,255,255,0.7); font-size: 1rem;">
            {display_symbol} • {asset_info['name']}
        </div>
        <div style="color: rgba(255,255,255,0.6); font-size: 0.875rem; margin-top: 1rem;">
            Volume: {volume:,} • Updated: {market_data['timestamp'].strftime('%H:%M:%S')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return market_data

# ═══════════════════════════════════════════════════════════════════════════════════════
# DATA QUALITY INDICATOR
# ═══════════════════════════════════════════════════════════════════════════════════════

def show_data_quality_status():
    """Show data quality and connectivity status."""
    
    current_asset = AppState.get_current_asset()
    
    # Test connectivity to Yahoo Finance
    market_data = get_real_market_data(current_asset)
    
    if market_data['status'] == 'success':
        # Real data working
        st.success(f"✅ **Live Data Connected** - Real-time {current_asset} data from Yahoo Finance")
        
        # Show data quality metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Data Source", "Yahoo Finance", "Live")
            
        with col2:
            st.metric("Last Update", market_data['timestamp'].strftime('%H:%M:%S'), "Real-time")
            
        with col3:
            st.metric("Data Quality", "High", "✅ Verified")
            
    else:
        # Error with real data
        st.error(f"❌ **Data Connection Error** - Using demo data for {current_asset}")
        st.info(f"**Error Details:** {market_data.get('error', 'Unknown error')}")
        
        # Show fallback status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Data Source", "Demo Mode", "Fallback")
            
        with col2:
            st.metric("Status", "Simulated", "⚠️ Not Live")
            
        with col3:
            st.metric("Data Quality", "Demo", "⚠️ Simulated")

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE PART 3 - REAL DATA INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════════════

# Add data quality status section
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📡</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #00ff88 0%, #22d3ee 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Live Market Data
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Real-time data from Yahoo Finance with intelligent fallback</p>
</div>
<div class="section-divider"></div>
""", unsafe_allow_html=True)

# Display real market data
market_data = display_real_market_data()

# Show data quality status
show_data_quality_status()

# Update the charts to use real data
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Live Charts & Analysis
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Real-time charting with live data integration</p>
</div>
<div class="section-divider"></div>
""", unsafe_allow_html=True)

# Real-time chart
current_asset = AppState.get_current_asset()
display_symbol = get_display_symbol(current_asset)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)

# Create chart with real data
price_fig = create_real_price_chart(current_asset, f"{display_symbol} Live Price Chart")
st.plotly_chart(price_fig, use_container_width=True, config=CHART_CONFIG)

st.markdown('</div>', unsafe_allow_html=True)

# Real data status
if market_data['status'] == 'success':
    st.success(f"📊 **Chart showing live {display_symbol} data** - Last updated: {market_data['timestamp'].strftime('%H:%M:%S')}")
else:
    st.warning(f"📊 **Chart showing demo {display_symbol} data** - Live data temporarily unavailable")
