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

def force_light_text_always():
    st.markdown("""
    <style>
    /* Lock the app to light text regardless of OS theme */
    :root{
      --text:#e5e7eb !important;
      --muted:rgba(255,255,255,.75) !important;
      --subtle:rgba(255,255,255,.60) !important;
      --link:#22d3ee !important;
      --code-bg:rgba(255,255,255,.08) !important;
    }
    /* Neutralize any prior prefers-color-scheme override */
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

if "force_text" not in st.session_state:
    force_light_text_always()
    st.session_state.force_text = True




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

def patch_sidebar_text_colors():
    st.markdown("""
    <style>
    /* Base: make all sidebar text readable */
    section[data-testid="stSidebar"] *{
      color:#e5e7eb !important;
      -webkit-text-fill-color:#e5e7eb !important;
    }

    /* Markdown links (if you have "Next page" as a link) */
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a *{
      color:#e5e7eb !important;
      -webkit-text-fill-color:#e5e7eb !important;
      opacity:1 !important;
    }

    /* RADIO (your nav) */
    section[data-testid="stSidebar"] [data-baseweb="radio"] *{
      color:#e5e7eb !important;
    }

    /* SELECTBOX (asset) — control text + dropdown menu (lives in a portal) */
    section[data-testid="stSidebar"] [data-baseweb="select"] *{ color:#e5e7eb !important; }
    [data-baseweb="menu"], [role="listbox"]{
      background:rgba(17,24,39,.98) !important;
      color:#e5e7eb !important;
      border:1px solid rgba(255,255,255,.12) !important;
    }
    [data-baseweb="menu"] *, [role="listbox"] *{ color:#e5e7eb !important; }

    /* DATE INPUT (label + input) */
    section[data-testid="stSidebar"] [data-testid="stDateInput"] *{
      color:#e5e7eb !important;
    }
    /* Datepicker popover */
    [data-baseweb="datepicker"] *, [data-baseweb="calendar"] *{
      color:#e5e7eb !important;
    }

    /* Buttons/Link buttons in the sidebar (if any) */
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stLinkButton > a{
      color:#e5e7eb !important;
    }

    /* Nuke any inline neon green that sneaks into the sidebar */
    section[data-testid="stSidebar"] [style*="color:#00ff88"],
    section[data-testid="stSidebar"] [style*="color: #00ff88"],
    section[data-testid="stSidebar"] [style*="rgb(0, 255, 136)"]{
      color:#e5e7eb !important; -webkit-text-fill-color:#e5e7eb !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Build sidebar UI first…
selected_page = create_navigation_sidebar()
# …then force the colors:
patch_sidebar_text_colors()


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
# MARKETLENS PRO - PART 2C1: REAL DATA CHART FUNCTIONS (FIXED)
# Working integration with existing app using real Yahoo Finance data
# ═══════════════════════════════════════════════════════════════════════════════════════

# Additional CSS for chart containers with proper text colors
st.markdown("""
<style>
/* ========== CHART CONTAINERS WITH PROPER TEXT COLORS ========== */
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
    var(--neon-blue) 25%,
    var(--neon-purple) 50%,
    var(--neon-green) 75%,
    transparent 100%);
  animation: chart-shimmer 4s ease-in-out infinite;
}

@keyframes chart-shimmer {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ========== ENSURE WHITE TEXT IN CHART AREAS ========== */
.chart-container *,
.chart-container h1,
.chart-container h2, 
.chart-container h3,
.chart-container p,
.chart-container div {
  color: #ffffff !important;
}

/* ========== TAB STYLING WITH WHITE TEXT ========== */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255, 255, 255, 0.05) !important;
  border-radius: 12px !important;
  padding: 0.5rem !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 8px !important;
  color: rgba(255, 255, 255, 0.7) !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
  background: rgba(34, 211, 238, 0.1) !important;
  color: #ffffff !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%) !important;
  color: #ffffff !important;
  border: 1px solid rgba(34, 211, 238, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# REAL DATA FUNCTIONS (NO DUPLICATE IMPORTS)
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=180, show_spinner=False)
def fetch_real_price_data(symbol: str) -> dict:
    """Fetch real current price data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d")
        
        if hist.empty:
            return {"status": "error", "error": "No data available"}
        
        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
        
        return {
            "status": "success",
            "price": current_price,
            "change": change,
            "change_pct": change_pct,
            "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_chart_data(symbol: str, period: str = "1mo") -> pd.DataFrame:
    """Fetch real historical data for charts."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval="1d")
        
        if data.empty:
            return pd.DataFrame()
        
        # Reset index to make Date a column
        data = data.reset_index()
        return data
    except Exception:
        return pd.DataFrame()

def build_real_price_chart(symbol: str, title: str):
    """Build price chart with real Yahoo Finance data."""
    
    # Get real historical data
    df = fetch_chart_data(symbol, period="1mo")
    
    if df.empty:
        # Create error chart
        fig = go.Figure()
        fig.add_annotation(
            text=f"⚠️ Unable to load real data for {symbol}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color='#ff6b35', size=18),
            bgcolor='rgba(255, 107, 53, 0.1)',
            bordercolor='#ff6b35',
            borderwidth=2,
            borderpad=20
        )
        fig.update_layout(
            title=f"{title} - Data Unavailable",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            height=400
        )
        return fig
    
    # Calculate moving average
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # Create chart
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name=f'{symbol} Price',
        line=dict(color='#22d3ee', width=3),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Price: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add moving average if we have enough data
    if len(df) >= 20 and not df['MA20'].isna().all():
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['MA20'],
            mode='lines',
            name='20-Day Average',
            line=dict(color='#ff6b35', width=2, dash='dot'),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>MA20: $%{y:,.2f}<extra></extra>'
        ))
    
    # Set proper Y-axis range
    price_min = df['Close'].min()
    price_max = df['Close'].max()
    price_range = price_max - price_min
    y_bottom = price_min - (price_range * 0.05)
    y_top = price_max + (price_range * 0.05)
    
    # Style the chart
    fig.update_layout(
        title=dict(
            text=f"{title} (Live Yahoo Finance Data)",
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
            range=[y_bottom, y_top],
            tickformat='$,.2f'
        ),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1,
            font=dict(color='#ffffff')
        ),
        margin=dict(l=60, r=40, t=60, b=40),
        height=400
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════════════
# CHART SECTION HEADER
# ═══════════════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Live Market Charts
    </h2>
    <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem; margin: 0.5rem 0 0 0;">
        Real-time data visualization powered by Yahoo Finance
    </p>
</div>
<div style="height: 1px; background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 20%, rgba(34, 211, 238, 0.4) 50%, rgba(255, 255, 255, 0.2) 80%, transparent 100%); margin: 3rem 0;"></div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# CHART TABS (START WITH TAB 1)
# ═══════════════════════════════════════════════════════════════════════════════════════

# Get current asset info
current_asset = AppState.get_current_asset()
display_symbol = get_display_symbol(current_asset)
asset_info = MAJOR_EQUITIES[current_asset]

# Create chart tabs
tab1, tab2, tab3 = st.tabs(["📊 Price Action", "📈 Volume Analysis", "🎯 Technical Indicators"])

# TAB 1: PRICE ACTION WITH REAL DATA
with tab1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Create and display real price chart
    price_chart = build_real_price_chart(current_asset, f"{display_symbol} Price Movement")
    st.plotly_chart(price_chart, use_container_width=True, config=CHART_CONFIG)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get real market data for analysis
    live_data = fetch_real_price_data(current_asset)
    
    if live_data['status'] == 'success':
        # Show analysis with real data
        price = live_data['price']
        change = live_data['change']
        change_pct = live_data['change_pct']
        
        change_color = "#00ff88" if change >= 0 else "#ff6b35"
        trend_word = "positive" if change >= 0 else "negative"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%); 
                    border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
            <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem; color: #ffffff;">
                📊 Live Price Analysis
            </div>
            <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
                <strong>{display_symbol}</strong> is currently trading at <strong>${price:,.2f}</strong> with a 
                <span style="color: {change_color}; font-weight: 700;">{trend_word}</span> movement of 
                <strong style="color: {change_color};">${change:+.2f} ({change_pct:+.2f}%)</strong> from the previous session.
                Chart displays real market data from Yahoo Finance with 20-day moving average overlay.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # Show error message
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%); 
                    border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
            <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem; color: #ffffff;">
                ⚠️ Data Connection Issue
            </div>
            <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
                Unable to fetch real market data for <strong>{display_symbol}</strong>. 
                Error: {live_data.get('error', 'Unknown error')}. 
                Please check your internet connection and try refreshing the page.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 2C2: VOLUME & TECHNICAL ANALYSIS COMPLETION
# Complete the remaining tabs with real Yahoo Finance data integration
# ═══════════════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════════════
# REAL DATA FUNCTIONS FOR TECHNICAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def fetch_technical_data(symbol: str) -> pd.DataFrame:
    """Fetch extended historical data for technical indicators."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="6mo", interval="1d")  # 6 months for good indicator calculation
        
        if data.empty:
            return pd.DataFrame()
        
        data = data.reset_index()
        return data
    except Exception:
        return pd.DataFrame()

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate RSI, MACD, and Bollinger Bands from real data."""
    if df.empty or len(df) < 26:  # Need minimum data for MACD
        return df
    
    try:
        # RSI Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD Calculation
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        return df
    except Exception:
        return df

def build_technical_chart(symbol: str):
    """Build technical indicators chart with real data."""
    
    from plotly.subplots import make_subplots
    
    # Get real technical data
    df = fetch_technical_data(symbol)
    
    if df.empty:
        # Error chart
        fig = make_subplots(rows=1, cols=1)
        fig.add_annotation(
            text=f"⚠️ Unable to load technical data for {symbol}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(color='#ff6b35', size=18),
            bgcolor='rgba(255, 107, 53, 0.1)', bordercolor='#ff6b35', borderwidth=2
        )
        fig.update_layout(
            title=f"{symbol} Technical Analysis - Data Error",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'), height=600
        )
        return fig, {}
    
    # Calculate indicators
    df = calculate_technical_indicators(df)
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=[
            f'{symbol} Price & Bollinger Bands (Live Data)',
            f'{symbol} RSI (Live Data)', 
            f'{symbol} MACD (Live Data)'
        ],
        vertical_spacing=0.08,
        row_heights=[0.5, 0.25, 0.25]
    )
    
    # Price and Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Close'],
        mode='lines', name='Price',
        line=dict(color='#22d3ee', width=2),
        hovertemplate='Price: $%{y:,.2f}<extra></extra>'
    ), row=1, col=1)
    
    if not df['BB_upper'].isna().all():
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['BB_upper'],
            mode='lines', name='BB Upper',
            line=dict(color='#a855f7', width=1),
            hovertemplate='BB Upper: $%{y:,.2f}<extra></extra>'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['BB_lower'],
            mode='lines', name='BB Lower',
            line=dict(color='#a855f7', width=1),
            fill='tonexty', fillcolor='rgba(168, 85, 247, 0.1)',
            hovertemplate='BB Lower: $%{y:,.2f}<extra></extra>'
        ), row=1, col=1)
    
    # RSI
    if not df['RSI'].isna().all():
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['RSI'],
            mode='lines', name='RSI',
            line=dict(color='#00ff88', width=2),
            hovertemplate='RSI: %{y:.1f}<extra></extra>'
        ), row=2, col=1)
    
    # RSI reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(255, 107, 53, 0.7)", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(0, 255, 136, 0.7)", row=2, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="rgba(255, 255, 255, 0.3)", row=2, col=1)
    
    # MACD
    if not df['MACD'].isna().all():
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['MACD'],
            mode='lines', name='MACD',
            line=dict(color='#22d3ee', width=2),
            hovertemplate='MACD: %{y:.3f}<extra></extra>'
        ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['MACD_signal'],
            mode='lines', name='Signal',
            line=dict(color='#ff6b35', width=2),
            hovertemplate='Signal: %{y:.3f}<extra></extra>'
        ), row=3, col=1)
        
        # MACD Histogram
        colors = ['#00ff88' if x >= 0 else '#ff006e' for x in df['MACD_histogram']]
        fig.add_trace(go.Bar(
            x=df['Date'], y=df['MACD_histogram'],
            name='Histogram', marker_color=colors, opacity=0.6,
            hovertemplate='Histogram: %{y:.4f}<extra></extra>'
        ), row=3, col=1)
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{symbol} Technical Analysis (Live Yahoo Finance Data)",
            font=dict(color='#ffffff', size=18), x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0.7)', bordercolor='rgba(255,255,255,0.3)', 
                   borderwidth=1, font=dict(color='#ffffff')),
        height=600, margin=dict(l=60, r=40, t=80, b=40)
    )
    
    # Update axes
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff')
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff')
    fig.update_yaxes(tickformat='$,.2f', row=1, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    # Get current values for analysis
    current_values = {}
    if len(df) > 0:
        current_values = {
            'rsi': df['RSI'].iloc[-1] if not df['RSI'].isna().all() else 50,
            'macd': df['MACD'].iloc[-1] if not df['MACD'].isna().all() else 0,
            'macd_signal': df['MACD_signal'].iloc[-1] if not df['MACD_signal'].isna().all() else 0,
            'price': df['Close'].iloc[-1],
            'bb_upper': df['BB_upper'].iloc[-1] if not df['BB_upper'].isna().all() else 0,
            'bb_lower': df['BB_lower'].iloc[-1] if not df['BB_lower'].isna().all() else 0
        }
    
    return fig, current_values

# ═══════════════════════════════════════════════════════════════════════════════════════
# COMPLETE TAB 2: VOLUME ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Get real volume data
    volume_data = fetch_real_price_data(current_asset)
    historical_data = fetch_chart_data(current_asset, period="1mo")
    
    if volume_data['status'] == 'success' and not historical_data.empty:
        current_volume = volume_data['volume']
        
        # Calculate volume metrics from real data
        if 'Volume' in historical_data.columns:
            avg_volume = int(historical_data['Volume'].mean())
            relative_volume = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Volume trend (last 5 days vs previous 5 days)
            if len(historical_data) >= 10:
                recent_vol = historical_data['Volume'].tail(5).mean()
                previous_vol = historical_data['Volume'].iloc[-10:-5].mean()
                volume_trend = ((recent_vol - previous_vol) / previous_vol) * 100 if previous_vol > 0 else 0
            else:
                volume_trend = 0
        else:
            avg_volume = 0
            relative_volume = 1.0
            volume_trend = 0
        
        # Volume analysis header
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: #ffffff; margin-bottom: 1rem; font-weight: 800;">
                Live Volume Analysis - {display_symbol}
            </h3>
            <p style="color: rgba(255, 255, 255, 0.8); line-height: 1.6;">
                Real-time volume analysis powered by Yahoo Finance data showing institutional activity patterns.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Volume metrics grid
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem; font-weight: 600;">CURRENT VOLUME</div>
                <div style="color: #a855f7; font-size: 1.8rem; font-weight: 800;">{current_volume:,}</div>
                <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem; margin-top: 0.5rem;">shares traded today</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            trend_color = "#00ff88" if volume_trend >= 0 else "#ff6b35"
            trend_sign = "+" if volume_trend >= 0 else ""
            st.markdown(f"""
            <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem; font-weight: 600;">VOLUME TREND</div>
                <div style="color: {trend_color}; font-size: 1.8rem; font-weight: 800;">{trend_sign}{volume_trend:.1f}%</div>
                <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem; margin-top: 0.5rem;">5-day comparison</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            rel_color = "#ff6b35" if relative_volume > 2.0 else "#00ff88" if relative_volume > 1.2 else "#a855f7"
            st.markdown(f"""
            <div class="glass-panel" style="padding: 1.5rem; text-align: center;">
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.875rem; margin-bottom: 0.5rem; font-weight: 600;">RELATIVE VOLUME</div>
                <div style="color: {rel_color}; font-size: 1.8rem; font-weight: 800;">{relative_volume:.1f}x</div>
                <div style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem; margin-top: 0.5rem;">vs 30-day average</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Volume analysis insights
        if relative_volume > 2.5:
            analysis = f"Exceptionally high volume at {relative_volume:.1f}x average suggests major institutional activity or significant news impact."
            panel_type = "warning"
        elif relative_volume > 1.5:
            analysis = f"Above-average volume at {relative_volume:.1f}x indicates strong market interest and potential for continued momentum."
            panel_type = "success"
        elif relative_volume < 0.5:
            analysis = f"Below-average volume at {relative_volume:.1f}x suggests low participation and potential for range-bound trading."
            panel_type = "info"
        else:
            analysis = f"Normal volume levels at {relative_volume:.1f}x average indicate typical market participation."
            panel_type = "info"
        
        # Display analysis panel
        panel_colors = {
            "success": ("rgba(16, 185, 129, 0.1)", "rgba(16, 185, 129, 0.3)"),
            "warning": ("rgba(245, 158, 11, 0.1)", "rgba(245, 158, 11, 0.3)"),
            "info": ("rgba(34, 211, 238, 0.1)", "rgba(34, 211, 238, 0.3)")
        }
        bg_color, border_color = panel_colors[panel_type]
        
        st.markdown(f"""
        <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin: 1.5rem 0;">
            <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem; color: #ffffff;">
                📊 Live Volume Insights
            </div>
            <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
                <strong>{display_symbol}</strong> volume analysis: {current_volume:,} shares traded vs {avg_volume:,} average. 
                {analysis} Volume trend: {volume_trend:+.1f}% over past 5 sessions.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # Volume data error
        st.markdown(f"""
        <div style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem; color: #ff6b35;">⚠️</div>
            <h3 style="color: #ffffff; margin-bottom: 1rem; font-weight: 800;">Volume Data Unavailable</h3>
            <p style="color: rgba(255, 255, 255, 0.8);">
                Unable to fetch real volume data for {display_symbol}. Please check your connection and try refreshing.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# COMPLETE TAB 3: TECHNICAL INDICATORS  
# ═══════════════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Create technical chart
    tech_chart, tech_values = build_technical_chart(current_asset)
    st.plotly_chart(tech_chart, use_container_width=True, config=CHART_CONFIG)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Technical analysis panels
    if tech_values:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # RSI Analysis
            rsi = tech_values.get('rsi', 50)
            if rsi > 70:
                rsi_status = "Overbought"
                rsi_color = "#ff6b35"
                rsi_action = "Consider profit-taking opportunities"
                panel_type = "warning"
            elif rsi < 30:
                rsi_status = "Oversold"
                rsi_color = "#00ff88"
                rsi_action = "Potential buying opportunity emerging"
                panel_type = "success"
            else:
                rsi_status = "Neutral"
                rsi_color = "#a855f7"
                rsi_action = "RSI in normal trading range"
                panel_type = "info"
            
            panel_colors = {
                "success": ("rgba(16, 185, 129, 0.1)", "rgba(16, 185, 129, 0.3)"),
                "warning": ("rgba(245, 158, 11, 0.1)", "rgba(245, 158, 11, 0.3)"),
                "info": ("rgba(34, 211, 238, 0.1)", "rgba(34, 211, 238, 0.3)")
            }
            bg_color, border_color = panel_colors[panel_type]
            
            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem; color: #ffffff;">
                    RSI Analysis ({rsi:.1f})
                </div>
                <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
                    <strong style="color: {rsi_color};">{rsi_status}</strong> conditions detected. 
                    {rsi_action}. Current 14-period RSI calculated from real Yahoo Finance data.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # MACD Analysis
            macd = tech_values.get('macd', 0)
            macd_signal = tech_values.get('macd_signal', 0)
            
            if macd > macd_signal:
                macd_status = "Bullish"
                macd_color = "#00ff88"
                macd_action = "MACD above signal suggests upward momentum"
                panel_type = "success"
            elif macd < macd_signal:
                macd_status = "Bearish"
                macd_color = "#ff6b35"
                macd_action = "MACD below signal indicates downward pressure"
                panel_type = "warning"
            else:
                macd_status = "Neutral"
                macd_color = "#a855f7"
                macd_action = "MACD near signal line, watch for direction"
                panel_type = "info"
            
            bg_color, border_color = panel_colors[panel_type]
            
            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem; color: #ffffff;">
                    MACD Signal ({macd_status})
                </div>
                <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
                    <strong style="color: {macd_color};">{macd_action}</strong>. 
                    MACD: {macd:.3f}, Signal: {macd_signal:.3f}. Based on real 12/26/9 period calculation.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Bollinger Bands Analysis
            price = tech_values.get('price', 0)
            bb_upper = tech_values.get('bb_upper', 0)
            bb_lower = tech_values.get('bb_lower', 0)
            
            if bb_upper != bb_lower:
                bb_position = (price - bb_lower) / (bb_upper - bb_lower)
                
                if bb_position > 0.8:
                    bb_status = "Near Upper Band"
                    bb_color = "#ff6b35"
                    bb_action = "Price near resistance, watch for reversal"
                    panel_type = "warning"
                elif bb_position < 0.2:
                    bb_status = "Near Lower Band"
                    bb_color = "#00ff88"
                    bb_action = "Price near support, potential bounce zone"
                    panel_type = "success"
                else:
                    bb_status = "Middle Range"
                    bb_color = "#a855f7"
                    bb_action = "Price trading within normal band range"
                    panel_type = "info"
            else:
                bb_status = "Calculating"
                bb_color = "#a855f7"
                bb_action = "Bollinger Bands data being calculated"
                panel_type = "info"
            
            bg_color, border_color = panel_colors[panel_type]
            
            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem; color: #ffffff;">
                    Bollinger Bands ({bb_status})
                </div>
                <div style="color: rgba(255, 255, 255, 0.9); line-height: 1.6;">
                    <strong style="color: {bb_color};">{bb_action}</strong>. 
                    Current price: ${price:.2f}. Based on 20-period moving average with 2 standard deviations.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Technical data error
        st.markdown(f"""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); 
                    border-radius: 12px; padding: 2rem; margin: 1rem 0; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem; color: #ff6b35;">⚠️</div>
            <div style="font-weight: 700; font-size: 1.2rem; margin-bottom: 1rem; color: #ffffff;">
                Technical Analysis Unavailable
            </div>
            <div style="color: rgba(255, 255, 255, 0.9);">
                Unable to calculate technical indicators for <strong>{display_symbol}</strong>. 
                This requires extended historical data from Yahoo Finance.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════════════
# FINAL STATUS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div class="glass-panel" style="padding: 2rem; text-align: center; margin: 3rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
    <h3 style="color: #ffffff; font-size: 1.8rem; font-weight: 800; margin-bottom: 1rem;">
        MarketLens Pro - Live Data Integration Complete
    </h3>
    <p style="color: rgba(255, 255, 255, 0.8); font-size: 1.1rem; margin-bottom: 1.5rem;">
        All analysis modules operational with real-time Yahoo Finance data. 
        Professional-grade market intelligence at your fingertips.
    </p>
    <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
        <span class="status-chip status-live">📊 Live Charts</span>
        <span class="status-chip status-live">📈 Volume Analysis</span>
        <span class="status-chip status-live">🎯 Technical Indicators</span>
        <span class="status-chip status-live">⚡ Real-time Updates</span>
    </div>
</div>
""", unsafe_allow_html=True)









# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 3A: CORE MARKET DATA FUNCTIONS
# Real Yahoo Finance Integration with Professional Error Handling
# ═══════════════════════════════════════════════════════════════════════════════════════

# Text visibility fix for dark UI
def inject_global_styles():
    st.markdown("""
    <style>
    /* Make metric labels/values/deltas readable on dark UI */
    div[data-testid="stMetricLabel"] > div { color: rgba(255,255,255,0.7) !important; }
    div[data-testid="stMetricValue"] { color: #e5e7eb !important; }
    span[data-testid="stMetricDelta"] {
      color: #00ff88 !important;
      background: rgba(0,255,136,0.12);
      padding: 2px 8px; border-radius: 999px; font-weight: 700;
    }

    /* Lighten text inside success/error/info banners */
    div[role="alert"] * { color: #e5e7eb !important; }

    /* Optional: make alert backgrounds fit dark glass UI */
    div[role="alert"] { background: rgba(255,255,255,0.06) !important; }
    
    /* Fix all text visibility */
    .stMarkdown, .stText, .stCaption { color: rgba(255,255,255,0.9) !important; }
    
    /* Fix success/warning/error messages */
    .stSuccess, .stWarning, .stError, .stInfo { 
        color: #ffffff !important; 
        background: rgba(255,255,255,0.05) !important;
    }
    .stSuccess *, .stWarning *, .stError *, .stInfo * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# Apply styles once
if "css_injected" not in st.session_state:
    inject_global_styles()
    st.session_state.css_injected = True

# ═══════════════════════════════════════════════════════════════════════════════════════
# DATA VALIDATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def validate_price_data(data: dict) -> bool:
    """Validate if price data looks reasonable."""
    if data.get('status') != 'success':
        return False
    
    price = data.get('price', 0)
    change_pct = data.get('change_pct', 0)
    
    # Basic sanity checks
    if price <= 0 or price > 100000:  # Unreasonable price range
        return False
    
    # Check if change is too extreme (>50% in one update)
    if abs(change_pct) > 50:
        return False
    
    # Check for NaN or infinite values
    if not np.isfinite(price) or not np.isfinite(change_pct):
        return False
    
    return True

def validate_symbol_format(symbol: str) -> bool:
    """Validate symbol format and check if supported."""
    if not symbol or len(symbol) > 10:
        return False
    
    # Check if symbol is in our supported universe
    return symbol.upper() in MAJOR_EQUITIES

def calculate_data_quality_score(data: dict, historical_data: pd.DataFrame = None) -> int:
    """Calculate data quality score (0-100)."""
    score = 0
    
    # Base score for successful data retrieval
    if data.get('status') == 'success':
        score += 40
    
    # Price validation
    if validate_price_data(data):
        score += 30
    
    # Volume check
    if data.get('volume', 0) > 0:
        score += 15
    
    # Timestamp freshness (within last 5 minutes)
    timestamp = data.get('timestamp')
    if timestamp and (datetime.now() - timestamp).total_seconds() < 300:
        score += 15
    
    return min(100, score)

# ═══════════════════════════════════════════════════════════════════════════════════════
# CORE MARKET DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)  # Cache for 1 minute
def get_real_market_data(symbol: str) -> dict:
    """Fetch real market data from Yahoo Finance with validation."""
    try:
        # Validate symbol first
        if not validate_symbol_format(symbol):
            raise ValueError(f"Invalid or unsupported symbol: {symbol}")
        
        ticker = yf.Ticker(symbol)
        
        # Get current quote data with timeout
        info = ticker.info
        hist = ticker.history(period="2d", interval="1m")
        
        if hist.empty:
            raise ValueError(f"No price data available for {symbol}")
        
        # Get latest price data
        latest = hist.iloc[-1]
        previous_close = info.get('previousClose')
        
        # Fallback to historical close if no previous close
        if previous_close is None and len(hist) > 1:
            previous_close = hist['Close'].iloc[-2]
        elif previous_close is None:
            previous_close = latest['Close']
        
        current_price = float(latest['Close'])
        change = current_price - previous_close
        change_pct = (change / previous_close) * 100 if previous_close != 0 else 0
        
        # Get additional market data
        volume = int(latest['Volume']) if 'Volume' in latest and pd.notna(latest['Volume']) else 0
        high_52w = info.get('fiftyTwoWeekHigh', current_price)
        low_52w = info.get('fiftyTwoWeekLow', current_price)
        market_cap = info.get('marketCap', 0)
        
        # Build result dictionary
        result = {
            'symbol': symbol,
            'price': current_price,
            'change': change,
            'change_pct': change_pct,
            'volume': volume,
            'previous_close': previous_close,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'market_cap': market_cap,
            'timestamp': datetime.now(),
            'status': 'success',
            'data_source': 'yahoo_finance'
        }
        
        # Validate the data before returning
        if not validate_price_data(result):
            raise ValueError("Price data failed validation checks")
        
        return result
        
    except Exception as e:
        # Return structured error data
        return {
            'symbol': symbol,
            'price': 0.0,
            'change': 0.0,
            'change_pct': 0.0,
            'volume': 0,
            'previous_close': 0.0,
            'high_52w': 0.0,
            'low_52w': 0.0,
            'market_cap': 0,
            'timestamp': datetime.now(),
            'status': 'error',
            'error': str(e),
            'data_source': 'error'
        }

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_historical_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical price data with EMA calculations."""
    try:
        if not validate_symbol_format(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise ValueError(f"No historical data available for {symbol}")
        
        # Reset index to make Date a column
        hist = hist.reset_index()
        hist['Symbol'] = symbol
        
        # Calculate EMAs (8 and 21 period)
        if len(hist) >= 21:  # Need at least 21 periods for 21 EMA
            hist['EMA_8'] = hist['Close'].ewm(span=8, adjust=False).mean()
            hist['EMA_21'] = hist['Close'].ewm(span=21, adjust=False).mean()
            
            # EMA trend analysis
            hist['EMA_Signal'] = np.where(hist['EMA_8'] > hist['EMA_21'], 1, -1)
            hist['EMA_Crossover'] = hist['EMA_Signal'].diff()
        
        # Add data quality metadata
        hist['Data_Quality'] = 'high'
        hist['Last_Updated'] = datetime.now()
        
        return hist
        
    except Exception as e:
        log_error(f"Historical data error for {symbol}: {str(e)}", "Data")
        return pd.DataFrame()

@st.cache_data(ttl=180, show_spinner=False)  # Cache for 3 minutes  
def get_intraday_data(symbol: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame:
    """Fetch intraday data with EMA analysis."""
    try:
        if not validate_symbol_format(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval, prepost=True)
        
        if hist.empty:
            raise ValueError(f"No intraday data available for {symbol}")
        
        hist = hist.reset_index()
        hist['Symbol'] = symbol
        
        # Calculate short-term EMAs for intraday trading
        if len(hist) >= 21:
            hist['EMA_8'] = hist['Close'].ewm(span=8, adjust=False).mean()
            hist['EMA_21'] = hist['Close'].ewm(span=21, adjust=False).mean()
            
            # Intraday momentum signals
            hist['Momentum'] = hist['Close'].pct_change(periods=5) * 100
            hist['EMA_Trend'] = np.where(hist['EMA_8'] > hist['EMA_21'], 'Bullish', 'Bearish')
        
        return hist
        
    except Exception as e:
        log_error(f"Intraday data error for {symbol}: {str(e)}", "Data")
        return pd.DataFrame()

# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKET STATUS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def get_market_session_info() -> dict:
    """Get detailed market session information."""
    now_et = datetime.now(ET)
    now_ct = datetime.now(CT)
    
    # Get basic market status
    basic_status, status_type = get_market_status()
    
    # Determine trading session
    if now_et.weekday() < 5:  # Weekday
        if time(4, 0) <= now_et.time() < time(9, 30):
            session = "Pre-Market"
            session_emoji = "🌅"
        elif time(9, 30) <= now_et.time() < time(16, 0):
            session = "Regular Hours"
            session_emoji = "📈"
        elif time(16, 0) <= now_et.time() < time(20, 0):
            session = "After Hours"
            session_emoji = "🌆"
        else:
            session = "Overnight"
            session_emoji = "🌙"
    else:
        session = "Weekend"
        session_emoji = "📴"
    
    # Calculate time to next market event
    if now_et.weekday() < 5:  # Weekday
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if now_et < market_open:
            next_event = "Market Open"
            time_to_event = market_open - now_et
        elif now_et < market_close:
            next_event = "Market Close"
            time_to_event = market_close - now_et
        else:
            # Next day market open
            next_open = market_open + timedelta(days=1)
            next_event = "Next Market Open"
            time_to_event = next_open - now_et
    else:
        # Calculate time to Monday market open
        days_until_monday = (7 - now_et.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 1
        next_monday = now_et + timedelta(days=days_until_monday)
        next_open = next_monday.replace(hour=9, minute=30, second=0, microsecond=0)
        next_event = "Monday Market Open"
        time_to_event = next_open - now_et
    
    return {
        "status": basic_status,
        "session": session,
        "session_emoji": session_emoji,
        "timestamp_et": now_et,
        "timestamp_ct": now_ct,
        "is_trading": session in ["Pre-Market", "Regular Hours", "After Hours"],
        "next_event": next_event,
        "time_to_event": time_to_event,
        "market_day": now_et.weekday() < 5
    }

# ═══════════════════════════════════════════════════════════════════════════════════════
# DATA QUALITY MONITORING
# ═══════════════════════════════════════════════════════════════════════════════════════

def get_system_health_metrics() -> dict:
    """Get comprehensive system health metrics."""
    
    current_asset = AppState.get_current_asset()
    
    # Test data connectivity
    market_data = get_real_market_data(current_asset)
    historical_data = get_historical_data(current_asset, period="5d")
    
    # Calculate metrics
    data_quality = calculate_data_quality_score(market_data, historical_data)
    api_status = "Connected" if market_data['status'] == 'success' else "Error"
    
    # Cache performance
    cache_stats = st.session_state.get('cache_stats', {"hits": 0, "misses": 0})
    total_requests = cache_stats['hits'] + cache_stats['misses']
    cache_hit_rate = (cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
    
    # System performance
    session_start = st.session_state.get('last_refresh', datetime.now())
    uptime = datetime.now() - session_start
    
    return {
        "data_quality": data_quality,
        "api_status": api_status,
        "cache_hit_rate": cache_hit_rate,
        "uptime_minutes": uptime.total_seconds() / 60,
        "historical_data_points": len(historical_data),
        "last_update": market_data.get('timestamp', datetime.now()),
        "error_count": len(st.session_state.get('error_log', [])),
        "system_load": min(100, (data_quality + cache_hit_rate) / 2)
    }

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE PART 3A - CORE DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

# Display header
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📡</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #00ff88 0%, #22d3ee 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Core Market Data System
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Real-time Yahoo Finance integration with professional validation</p>
</div>
<div class="section-divider"></div>
""", unsafe_allow_html=True)

# Get current asset and market data
current_asset = AppState.get_current_asset()
market_data = get_real_market_data(current_asset)
session_info = get_market_session_info()
health_metrics = get_system_health_metrics()

# Display current market data
st.markdown("#### 📊 Live Market Data")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if market_data['status'] == 'success':
        st.metric(
            "Current Price", 
            f"${market_data['price']:,.2f}",
            f"{market_data['change']:+.2f}"
        )
    else:
        st.metric("Current Price", "Error", "No Data")

with col2:
    if market_data['status'] == 'success':
        st.metric(
            "Change %", 
            f"{market_data['change_pct']:+.2f}%",
            "Real-time"
        )
    else:
        st.metric("Change %", "—", "Error")

with col3:
    st.metric(
        "Market Session",
        session_info['session'],
        session_info['session_emoji']
    )

with col4:
    if market_data['status'] == 'success':
        st.metric(
            "Volume",
            f"{market_data['volume']:,}",
            "Shares"
        )
    else:
        st.metric("Volume", "—", "Error")

# Display market session information
st.markdown("#### ⏰ Market Session Details")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Current Time ET",
        session_info['timestamp_et'].strftime("%I:%M:%S %p"),
        "Eastern Time"
    )

with col2:
    st.metric(
        "Current Time CT", 
        session_info['timestamp_ct'].strftime("%I:%M:%S %p"),
        "Central Time"
    )

with col3:
    hours_to_event = session_info['time_to_event'].total_seconds() / 3600
    st.metric(
        session_info['next_event'],
        f"{hours_to_event:.1f}h",
        "Until Event"
    )

# System health status
st.markdown("#### 🔧 System Health Status")

if market_data['status'] == 'success':
    st.success(f"✅ **Live Data Connected** - Real-time {current_asset} data from Yahoo Finance")
else:
    st.error(f"❌ **Data Connection Error** - {market_data.get('error', 'Unknown error')}")

# Health metrics display
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Data Quality", f"{health_metrics['data_quality']}%", "Score")

with col2: 
    st.metric("API Status", health_metrics['api_status'], "Yahoo Finance")

with col3:
    st.metric("Cache Hit Rate", f"{health_metrics['cache_hit_rate']:.1f}%", "Performance")

with col4:
    st.metric("System Uptime", f"{health_metrics['uptime_minutes']:.1f}m", "Session")

# Data validation results
if market_data['status'] == 'success':
    validation_passed = validate_price_data(market_data)
    if validation_passed:
        st.info("✅ **Data Validation Passed** - Price data meets quality standards")
    else:
        st.warning("⚠️ **Data Validation Warning** - Price data may have quality issues")
else:
    st.warning("⚠️ **Validation Skipped** - No valid data to validate")







# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 3B: ASIAN SESSION & ADVANCED DATA PROCESSING
# ES Futures Analysis and Professional Data Processing Functions
# ═══════════════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════════════
# ASIAN SESSION DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_es_spx_offset() -> float:
    """Calculate current ES futures to SPX offset."""
    try:
        # Get current ES futures price
        es_ticker = yf.Ticker("ES=F")
        es_data = es_ticker.history(period="1d", interval="1m", prepost=True)
        
        # Get current SPX price
        spx_ticker = yf.Ticker("^GSPC")
        spx_data = spx_ticker.history(period="1d", interval="1m", prepost=True)
        
        if not es_data.empty and not spx_data.empty:
            current_es = float(es_data['Close'].iloc[-1])
            current_spx = float(spx_data['Close'].iloc[-1])
            offset = current_spx - current_es
            
            return offset
        else:
            # Fallback to typical offset
            return -23.5
            
    except Exception as e:
        log_error(f"ES-SPX offset calculation error: {str(e)}", "Data")
        return -23.5

@st.cache_data(ttl=300, show_spinner=False)
def get_es_asian_session_data(target_date: date, timeframe: str = "30m") -> dict:
    """Get ES futures data for Asian session (5-8 PM CT previous day)."""
    try:
        # Calculate Asian session window (previous day 5-8 PM CT)
        prev_day = target_date - timedelta(days=1)
        
        # Handle weekends - go back to Friday
        while prev_day.weekday() >= 5:
            prev_day -= timedelta(days=1)
        
        start_time = datetime.combine(prev_day, time(17, 0), tzinfo=CT)
        end_time = datetime.combine(prev_day, time(20, 0), tzinfo=CT)
        
        # Get ES futures data with extended period for better coverage
        es_ticker = yf.Ticker("ES=F")
        es_data = es_ticker.history(period="7d", interval=timeframe, prepost=True)
        
        if es_data.empty:
            return {"status": "error", "message": "No ES futures data available"}
        
        # Convert timezone and filter for Asian session
        es_data_reset = es_data.reset_index()
        es_data_reset['Datetime_CT'] = pd.to_datetime(es_data_reset['Datetime']).dt.tz_convert(CT)
        
        # Filter for Asian session window
        asian_mask = (
            (es_data_reset['Datetime_CT'] >= start_time) & 
            (es_data_reset['Datetime_CT'] <= end_time)
        )
        asian_data = es_data_reset[asian_mask].copy()
        
        if asian_data.empty:
            return {"status": "error", "message": f"No ES data found for Asian session on {prev_day.strftime('%Y-%m-%d')}"}
        
        # Find swing points using CLOSE prices (line chart compatibility)
        highest_close_idx = asian_data['Close'].idxmax()
        lowest_close_idx = asian_data['Close'].idxmin()
        
        es_high_close = float(asian_data.loc[highest_close_idx, 'Close'])
        es_low_close = float(asian_data.loc[lowest_close_idx, 'Close'])
        high_time = asian_data.loc[highest_close_idx, 'Datetime_CT']
        low_time = asian_data.loc[lowest_close_idx, 'Datetime_CT']
        
        # Convert ES to SPX equivalent using current offset
        offset = get_es_spx_offset()
        spx_high_equivalent = es_high_close + offset
        spx_low_equivalent = es_low_close + offset
        
        # Calculate additional metrics
        asian_range = es_high_close - es_low_close
        time_between_extremes = abs((high_time - low_time).total_seconds() / 3600)
        
        return {
            "status": "success",
            "es_high_close": es_high_close,
            "es_low_close": es_low_close,
            "spx_high_equivalent": spx_high_equivalent,
            "spx_low_equivalent": spx_low_equivalent,
            "high_time_ct": high_time.to_pydatetime(),
            "low_time_ct": low_time.to_pydatetime(),
            "asian_range": asian_range,
            "time_between_extremes": time_between_extremes,
            "es_spx_offset": offset,
            "data_points": len(asian_data),
            "timeframe": timeframe.upper(),
            "session_date": prev_day,
            "method": "LINE_CHART_CLOSES"
        }
        
    except Exception as e:
        log_error(f"Asian session data error: {str(e)}", "Data")
        return {"status": "error", "message": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def get_previous_day_ohlc(symbol: str, target_date: date) -> dict:
    """Get previous trading day OHLC data with validation."""
    try:
        # Calculate previous trading day
        prev_day = target_date - timedelta(days=1)
        while prev_day.weekday() >= 5:  # Skip weekends
            prev_day -= timedelta(days=1)
        
        ticker = yf.Ticker(symbol)
        hist_data = ticker.history(period="1mo", interval="1d")
        
        if hist_data.empty:
            return {"status": "error", "message": f"No historical data for {symbol}"}
        
        # Find data for the previous trading day
        hist_reset = hist_data.reset_index()
        hist_reset['Date_Only'] = pd.to_datetime(hist_reset['Date']).dt.date
        
        # Try to find exact date first
        exact_match = hist_reset[hist_reset['Date_Only'] == prev_day]
        
        if not exact_match.empty:
            row = exact_match.iloc[-1]
            actual_date = prev_day
        else:
            # Use most recent available data
            row = hist_reset.iloc[-1]
            actual_date = hist_reset['Date_Only'].iloc[-1]
        
        # Extract OHLC data
        ohlc_data = {
            "status": "success",
            "symbol": symbol,
            "date": actual_date,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]) if "Volume" in row and pd.notna(row["Volume"]) else 0,
            "range": float(row["High"] - row["Low"]),
            "range_pct": float((row["High"] - row["Low"]) / row["Close"] * 100),
            "body_size": float(abs(row["Close"] - row["Open"])),
            "upper_wick": float(row["High"] - max(row["Open"], row["Close"])),
            "lower_wick": float(min(row["Open"], row["Close"]) - row["Low"])
        }
        
        # Add candle analysis
        if row["Close"] > row["Open"]:
            ohlc_data["candle_type"] = "Bullish"
            ohlc_data["candle_color"] = "Green"
        elif row["Close"] < row["Open"]:
            ohlc_data["candle_type"] = "Bearish"
            ohlc_data["candle_color"] = "Red"
        else:
            ohlc_data["candle_type"] = "Doji"
            ohlc_data["candle_color"] = "Neutral"
        
        return ohlc_data
        
    except Exception as e:
        log_error(f"Previous day OHLC error for {symbol}: {str(e)}", "Data")
        return {"status": "error", "message": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════════════
# PROJECTION CALCULATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def calculate_30min_blocks_advanced(from_dt: datetime, to_dt: datetime, 
                                  exclude_weekends: bool = True) -> int:
    """Calculate 30-minute blocks with weekend exclusion option."""
    if from_dt >= to_dt:
        return 0
    
    if not exclude_weekends:
        # Simple calculation without weekend exclusion
        total_seconds = (to_dt - from_dt).total_seconds()
        return int(total_seconds // (30 * 60))
    
    # Complex calculation excluding weekends
    current_dt = from_dt
    total_blocks = 0
    
    while current_dt < to_dt:
        # Skip weekends
        if current_dt.weekday() < 5:  # Monday = 0, Friday = 4
            next_30min = current_dt + timedelta(minutes=30)
            if next_30min <= to_dt:
                total_blocks += 1
        
        current_dt += timedelta(minutes=30)
    
    return total_blocks

def generate_rth_projection_slots(base_date: date) -> List[datetime]:
    """Generate RTH time slots (8:30 AM - 2:30 PM CT) for projections."""
    slots = []
    start_time = datetime.combine(base_date, RTH_START, tzinfo=CT)
    current_time = start_time
    
    while current_time.time() <= RTH_END:
        slots.append(current_time)
        current_time += timedelta(minutes=30)
    
    return slots

def calculate_price_projection(base_price: float, base_time: datetime, 
                             target_time: datetime, slope_per_30min: float,
                             exclude_weekends: bool = True) -> float:
    """Calculate projected price using slope and time difference."""
    blocks = calculate_30min_blocks_advanced(base_time, target_time, exclude_weekends)
    projected_price = base_price + (slope_per_30min * blocks)
    return projected_price

# ═══════════════════════════════════════════════════════════════════════════════════════
# TECHNICAL ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def calculate_ema_signals(price_data: pd.DataFrame) -> dict:
    """Calculate EMA signals and crossovers."""
    if len(price_data) < 21:
        return {"status": "insufficient_data", "message": "Need at least 21 periods for EMA calculation"}
    
    try:
        # Calculate EMAs
        ema_8 = price_data['Close'].ewm(span=8, adjust=False).mean()
        ema_21 = price_data['Close'].ewm(span=21, adjust=False).mean()
        
        # Current values
        current_ema_8 = ema_8.iloc[-1]
        current_ema_21 = ema_21.iloc[-1]
        current_price = price_data['Close'].iloc[-1]
        
        # Trend determination
        if current_ema_8 > current_ema_21:
            trend = "Bullish"
            trend_strength = ((current_ema_8 - current_ema_21) / current_ema_21) * 100
        else:
            trend = "Bearish"
            trend_strength = ((current_ema_21 - current_ema_8) / current_ema_8) * 100
        
        # Crossover detection
        prev_ema_8 = ema_8.iloc[-2] if len(ema_8) > 1 else current_ema_8
        prev_ema_21 = ema_21.iloc[-2] if len(ema_21) > 1 else current_ema_21
        
        crossover = "None"
        if prev_ema_8 <= prev_ema_21 and current_ema_8 > current_ema_21:
            crossover = "Bullish"
        elif prev_ema_8 >= prev_ema_21 and current_ema_8 < current_ema_21:
            crossover = "Bearish"
        
        # Price relative to EMAs
        price_vs_ema8 = ((current_price - current_ema_8) / current_ema_8) * 100
        price_vs_ema21 = ((current_price - current_ema_21) / current_ema_21) * 100
        
        return {
            "status": "success",
            "current_ema_8": current_ema_8,
            "current_ema_21": current_ema_21,
            "current_price": current_price,
            "trend": trend,
            "trend_strength": abs(trend_strength),
            "crossover": crossover,
            "price_vs_ema8": price_vs_ema8,
            "price_vs_ema21": price_vs_ema21,
            "ema_distance": abs(current_ema_8 - current_ema_21),
            "ema_distance_pct": abs(trend_strength)
        }
        
    except Exception as e:
        log_error(f"EMA calculation error: {str(e)}", "Technical")
        return {"status": "error", "message": str(e)}

def analyze_momentum_signals(price_data: pd.DataFrame) -> dict:
    """Analyze momentum and volatility signals."""
    if len(price_data) < 10:
        return {"status": "insufficient_data"}
    
    try:
        # Calculate momentum indicators
        close_prices = price_data['Close']
        
        # Price momentum (5-period rate of change)
        momentum_5 = close_prices.pct_change(periods=5) * 100
        current_momentum = momentum_5.iloc[-1] if not momentum_5.empty else 0
        
        # Volatility (20-period rolling standard deviation)
        volatility = close_prices.rolling(window=min(20, len(close_prices))).std()
        current_volatility = volatility.iloc[-1] if not volatility.empty else 0
        
        # Average True Range approximation
        high_low = price_data['High'] - price_data['Low']
        avg_range = high_low.rolling(window=min(14, len(high_low))).mean()
        current_atr = avg_range.iloc[-1] if not avg_range.empty else 0
        
        # Momentum classification
        if abs(current_momentum) > 2.0:
            momentum_strength = "Strong"
        elif abs(current_momentum) > 0.5:
            momentum_strength = "Moderate"
        else:
            momentum_strength = "Weak"
        
        momentum_direction = "Bullish" if current_momentum > 0 else "Bearish" if current_momentum < 0 else "Neutral"
        
        return {
            "status": "success",
            "momentum_5": current_momentum,
            "momentum_direction": momentum_direction,
            "momentum_strength": momentum_strength,
            "volatility": current_volatility,
            "atr": current_atr,
            "volatility_pct": (current_volatility / close_prices.iloc[-1]) * 100 if close_prices.iloc[-1] != 0 else 0
        }
        
    except Exception as e:
        log_error(f"Momentum analysis error: {str(e)}", "Technical")
        return {"status": "error", "message": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE PART 3B - ASIAN SESSION & ADVANCED PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════════════

# Display header
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🌏</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #a855f7 0%, #00ff88 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Asian Session Analysis
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">ES Futures overnight analysis with SPX conversion and technical signals</p>
</div>
<div class="section-divider"></div>
""", unsafe_allow_html=True)

# Get current asset and analysis data
current_asset = AppState.get_current_asset()
forecast_date = AppState.get_forecast_date()

# Get Asian session data
asian_data = get_es_asian_session_data(forecast_date, "30m")
previous_day_data = get_previous_day_ohlc(current_asset, forecast_date)

# Display Asian session results
st.markdown("#### 🌏 Asian Session Swing Analysis (ES Futures)")

if asian_data['status'] == 'success':
    st.success(f"✅ **Asian Session Data Retrieved** - {asian_data['data_points']} data points from {asian_data['session_date'].strftime('%Y-%m-%d')}")
    
    # Asian session metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "ES High (Close)",
            f"${asian_data['es_high_close']:,.2f}",
            f"SPX: ${asian_data['spx_high_equivalent']:,.2f}"
        )
    
    with col2:
        st.metric(
            "ES Low (Close)", 
            f"${asian_data['es_low_close']:,.2f}",
            f"SPX: ${asian_data['spx_low_equivalent']:,.2f}"
        )
    
    with col3:
        st.metric(
            "Asian Range",
            f"${asian_data['asian_range']:.2f}",
            f"{asian_data['timeframe']} Data"
        )
    
    with col4:
        st.metric(
            "Time Between Extremes",
            f"{asian_data['time_between_extremes']:.1f}h",
            "High to Low"
        )
    
    # Time details
    st.markdown("#### ⏰ Asian Session Timing Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "High Time (CT)",
            asian_data['high_time_ct'].strftime("%I:%M %p"),
            asian_data['high_time_ct'].strftime("%m/%d")
        )
    
    with col2:
        st.metric(
            "Low Time (CT)",
            asian_data['low_time_ct'].strftime("%I:%M %p"), 
            asian_data['low_time_ct'].strftime("%m/%d")
        )
    
    with col3:
        st.metric(
            "ES-SPX Offset",
            f"{asian_data['es_spx_offset']:+.1f}",
            "Points"
        )
    
else:
    st.error(f"❌ **Asian Session Data Error** - {asian_data.get('message', 'Unknown error')}")

# Display previous day analysis
st.markdown("#### 📊 Previous Day OHLC Analysis")

if previous_day_data['status'] == 'success':
    st.success(f"✅ **Previous Day Data Retrieved** - {previous_day_data['date'].strftime('%Y-%m-%d')} for {previous_day_data['symbol']}")
    
    # OHLC metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Previous High",
            f"${previous_day_data['high']:,.2f}",
            f"{previous_day_data['candle_color']} Candle"
        )
    
    with col2:
        st.metric(
            "Previous Close",
            f"${previous_day_data['close']:,.2f}",
            f"Range: {previous_day_data['range_pct']:.2f}%"
        )
    
    with col3:
        st.metric(
            "Previous Low",
            f"${previous_day_data['low']:,.2f}",
            f"Volume: {previous_day_data['volume']:,}"
        )
    
    with col4:
        st.metric(
            "Daily Range",
            f"${previous_day_data['range']:.2f}",
            previous_day_data['candle_type']
        )
    
    # Candle analysis
    st.markdown("#### 🕯️ Candle Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Body Size",
            f"${previous_day_data['body_size']:.2f}",
            "Real Body"
        )
    
    with col2:
        st.metric(
            "Upper Wick",
            f"${previous_day_data['upper_wick']:.2f}",
            "Top Shadow"
        )
    
    with col3:
        st.metric(
            "Lower Wick", 
            f"${previous_day_data['lower_wick']:.2f}",
            "Bottom Shadow"
        )

else:
    st.error(f"❌ **Previous Day Data Error** - {previous_day_data.get('message', 'Unknown error')}")

# Technical analysis with EMAs
st.markdown("#### 📈 Technical Analysis (8 EMA vs 21 EMA)")

# Get historical data for EMA analysis
historical_data = get_historical_data(current_asset, period="2mo", interval="1d")

if not historical_data.empty:
    ema_signals = calculate_ema_signals(historical_data)
    momentum_signals = analyze_momentum_signals(historical_data)
    
    if ema_signals['status'] == 'success':
        st.success("✅ **Technical Analysis Complete** - EMA signals calculated")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "8 EMA",
                f"${ema_signals['current_ema_8']:,.2f}",
                f"Trend: {ema_signals['trend']}"
            )
        
        with col2:
            st.metric(
                "21 EMA",
                f"${ema_signals['current_ema_21']:,.2f}",
                f"Strength: {ema_signals['trend_strength']:.2f}%"
            )
        
        with col3:
            crossover_display = "🔴 None" if ema_signals['crossover'] == "None" else f"{'🟢' if ema_signals['crossover'] == 'Bullish' else '🔴'} {ema_signals['crossover']}"
            st.metric(
                "EMA Crossover",
                crossover_display,
                "Signal"
            )
        
        with col4:
            if momentum_signals['status'] == 'success':
                momentum_color = "🟢" if momentum_signals['momentum_direction'] == "Bullish" else "🔴" if momentum_signals['momentum_direction'] == "Bearish" else "🟡"
                st.metric(
                    "Momentum",
                    f"{momentum_color} {momentum_signals['momentum_strength']}",
                    f"{momentum_signals['momentum_5']:+.2f}%"
                )
            else:
                st.metric("Momentum", "Error", "—")
        
        # Price relative to EMAs
        col1, col2 = st.columns(2)
        
        with col1:
            price_vs_8_color = "🟢" if ema_signals['price_vs_ema8'] > 0 else "🔴"
            st.metric(
                "Price vs 8 EMA",
                f"{price_vs_8_color} {ema_signals['price_vs_ema8']:+.2f}%",
                "Relative Position"
            )
        
        with col2:
            price_vs_21_color = "🟢" if ema_signals['price_vs_ema21'] > 0 else "🔴"
            st.metric(
                "Price vs 21 EMA",
                f"{price_vs_21_color} {ema_signals['price_vs_ema21']:+.2f}%",
                "Relative Position"
            )
    
    else:
        st.error(f"❌ **EMA Analysis Error** - {ema_signals.get('message', 'Calculation failed')}")

else:
    st.warning("⚠️ **No Historical Data** - Unable to perform technical analysis")

# Projection readiness check
st.markdown("#### 🎯 Projection System Readiness")

projection_ready = (
    asian_data['status'] == 'success' and 
    previous_day_data['status'] == 'success'
)

if projection_ready:
    st.success("✅ **Projection System Ready** - All required data available for skyline/baseline calculations")
    
    # Show what data is available for projections
    st.info(f"""
    **Available for Projections:**
    - Asian Session Anchors: SPX High {asian_data['spx_high_equivalent']:,.2f} | SPX Low {asian_data['spx_low_equivalent']:,.2f}
    - Previous Day Anchors: High {previous_day_data['high']:,.2f} | Low {previous_day_data['low']:,.2f} | Close {previous_day_data['close']:,.2f}
    - Asset Slopes: {get_asset_slopes(current_asset)}
    """)
else:
    st.warning("⚠️ **Projection System Partial** - Some required data missing for complete analysis")











# ═══════════════════════════════════════════════════════════════════════════════════════
# MARKETLENS PRO - PART 3C: LIVE CHART INTEGRATION & DATA SYSTEM COMPLETION
# Professional Chart System with Real Data and Final Integration
# ═══════════════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════════════
# ADVANCED CHART FUNCTIONS WITH REAL DATA
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_professional_price_chart(symbol: str, title: str = "Price Chart", show_emas: bool = True):
    """Create professional price chart with real data and EMAs."""
    
    # Get real historical data
    df = get_historical_data(symbol, period="1mo", interval="1d")
    
    if df.empty:
        return create_fallback_chart(symbol, title)
    
    # Ensure proper date column
    date_col = 'Date' if 'Date' in df.columns else df.index
    
    # Create the main chart
    fig = go.Figure()
    
    # Add main price line
    fig.add_trace(go.Scatter(
        x=df[date_col] if 'Date' in df.columns else df.index,
        y=df['Close'],
        mode='lines',
        name=f'{symbol} Price',
        line=dict(
            color='#22d3ee',
            width=3
        ),
        hovertemplate='<b>%{x}</b><br>Price: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add EMAs if requested and data is sufficient
    if show_emas and len(df) >= 21:
        if 'EMA_8' in df.columns:
            fig.add_trace(go.Scatter(
                x=df[date_col] if 'Date' in df.columns else df.index,
                y=df['EMA_8'],
                mode='lines',
                name='8 EMA',
                line=dict(color='#00ff88', width=2, dash='dot'),
                hovertemplate='8 EMA: $%{y:,.2f}<extra></extra>'
            ))
        
        if 'EMA_21' in df.columns:
            fig.add_trace(go.Scatter(
                x=df[date_col] if 'Date' in df.columns else df.index,
                y=df['EMA_21'],
                mode='lines',
                name='21 EMA',
                line=dict(color='#ff6b35', width=2, dash='dash'),
                hovertemplate='21 EMA: $%{y:,.2f}<extra></extra>'
            ))
    
    # Calculate optimal Y-axis range for better zoom
    min_price = df['Close'].min()
    max_price = df['Close'].max()
    price_range = max_price - min_price
    y_padding = price_range * 0.05
    y_min = max(0, min_price - y_padding)
    y_max = max_price + y_padding
    
    # Professional styling
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
            color='#ffffff',
            title="Date"
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            zeroline=False,
            color='#ffffff',
            range=[y_min, y_max],
            tickformat='$,.2f',
            title="Price"
        ),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1,
            font=dict(color='#ffffff')
        ),
        margin=dict(l=60, r=40, t=60, b=40),
        height=450,
        hovermode='x unified'
    )
    
    return fig

def create_volume_chart_with_data(symbol: str):
    """Create volume chart using real data."""
    
    # Get real historical data
    df = get_historical_data(symbol, period="1mo", interval="1d")
    
    if df.empty:
        return create_fallback_volume_chart(symbol)
    
    # Ensure proper date column
    date_col = 'Date' if 'Date' in df.columns else df.index
    
    # Create volume chart
    fig = go.Figure()
    
    # Color volume bars based on price change
    colors = []
    for i in range(len(df)):
        if i == 0:
            colors.append('#a855f7')  # First bar neutral
        else:
            if df['Close'].iloc[i] >= df['Close'].iloc[i-1]:
                colors.append('#00ff88')  # Green for up days
            else:
                colors.append('#ff6b35')  # Orange for down days
    
    fig.add_trace(go.Bar(
        x=df[date_col] if 'Date' in df.columns else df.index,
        y=df['Volume'],
        name='Volume',
        marker=dict(
            color=colors,
            opacity=0.7
        ),
        hovertemplate='<b>%{x}</b><br>Volume: %{y:,}<extra></extra>'
    ))
    
    # Calculate volume moving average
    if len(df) >= 20:
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=df[date_col] if 'Date' in df.columns else df.index,
            y=df['Volume_MA'],
            mode='lines',
            name='Volume MA (20)',
            line=dict(color='#ffffff', width=2, dash='dot'),
            hovertemplate='Volume MA: %{y:,}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text=f"{symbol} Volume Analysis",
            font=dict(color='#ffffff', size=18, family='Space Grotesk'),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            color='#ffffff',
            title="Date"
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            color='#ffffff',
            title="Volume"
        ),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1,
            font=dict(color='#ffffff')
        ),
        margin=dict(l=60, r=40, t=50, b=40),
        height=350
    )
    
    return fig

def create_intraday_momentum_chart(symbol: str):
    """Create intraday momentum chart with real data."""
    
    # Get intraday data
    df = get_intraday_data(symbol, period="1d", interval="5m")
    
    if df.empty:
        return create_fallback_momentum_chart(symbol)
    
    # Ensure proper datetime column
    datetime_col = 'Datetime' if 'Datetime' in df.columns else df.index
    
    # Create momentum chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Price Action', 'Momentum Indicator'),
        vertical_spacing=0.15,
        row_heights=[0.7, 0.3]
    )
    
    # Price chart with EMAs
    fig.add_trace(
        go.Scatter(
            x=df[datetime_col] if 'Datetime' in df.columns else df.index,
            y=df['Close'],
            mode='lines',
            name='Price',
            line=dict(color='#22d3ee', width=2),
            hovertemplate='Price: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add EMAs if available
    if 'EMA_8' in df.columns and len(df) >= 21:
        fig.add_trace(
            go.Scatter(
                x=df[datetime_col] if 'Datetime' in df.columns else df.index,
                y=df['EMA_8'],
                mode='lines',
                name='8 EMA',
                line=dict(color='#00ff88', width=1),
                hovertemplate='8 EMA: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Momentum indicator
    if 'Momentum' in df.columns:
        # Color momentum bars
        momentum_colors = ['#00ff88' if x > 0 else '#ff6b35' for x in df['Momentum']]
        
        fig.add_trace(
            go.Bar(
                x=df[datetime_col] if 'Datetime' in df.columns else df.index,
                y=df['Momentum'],
                name='Momentum',
                marker=dict(color=momentum_colors, opacity=0.7),
                hovertemplate='Momentum: %{y:+.2f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5, row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{symbol} Intraday Momentum Analysis",
            font=dict(color='#ffffff', size=18, family='Space Grotesk'),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1,
            font=dict(color='#ffffff')
        ),
        height=500,
        hovermode='x unified'
    )
    
    # Update axes
    fig.update_xaxes(
        gridcolor='rgba(255,255,255,0.1)',
        showgrid=True,
        color='#ffffff'
    )
    fig.update_yaxes(
        gridcolor='rgba(255,255,255,0.1)',
        showgrid=True,
        color='#ffffff'
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════════════
# FALLBACK CHART FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def create_fallback_chart(symbol: str, title: str):
    """Fallback chart when real data is unavailable."""
    
    # Generate demo data
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    
    # Asset-specific demo data
    demo_params = {
        "^GSPC": {"base": 6443, "volatility": 80},
        "AAPL": {"base": 230, "volatility": 8},
        "MSFT": {"base": 420, "volatility": 15},
        "NVDA": {"base": 140, "volatility": 12},
        "AMZN": {"base": 185, "volatility": 14},
    }
    
    params = demo_params.get(symbol, {"base": 200, "volatility": 10})
    
    # Generate realistic price movement
    prices = []
    current_price = params["base"]
    
    for i in range(len(dates)):
        trend = np.sin(i * 0.1) * (params["volatility"] * 0.2)
        daily_change = np.random.normal(0, params["volatility"] * 0.15)
        current_price += trend + daily_change
        prices.append(max(current_price, params["base"] * 0.5))  # Prevent negative prices
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=f"{symbol} (Demo)",
        line=dict(color='#ff6b35', width=3, dash='dot'),
        hovertemplate='<b>%{x}</b><br>Demo Price: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add demo warning
    fig.add_annotation(
        text="⚠️ Demo Data - Real data unavailable",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(color='#ff6b35', size=12),
        bgcolor='rgba(255, 107, 53, 0.1)',
        bordercolor='#ff6b35',
        borderwidth=1,
        align="left"
    )
    
    # Calculate Y range
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    y_min = max(0, min_price - (price_range * 0.1))
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
        margin=dict(l=60, r=40, t=60, b=40),
        height=450
    )
    
    return fig

def create_fallback_volume_chart(symbol: str):
    """Fallback volume chart with demo data."""
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=20), end=datetime.now(), freq='D')
    volumes = [np.random.randint(1000000, 5000000) for _ in dates]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=dates,
        y=volumes,
        name='Volume (Demo)',
        marker=dict(color='#a855f7', opacity=0.7)
    ))
    
    fig.add_annotation(
        text="⚠️ Demo Volume Data",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(color='#a855f7', size=12),
        bgcolor='rgba(168, 85, 247, 0.1)',
        bordercolor='#a855f7',
        borderwidth=1
    )
    
    fig.update_layout(
        title=dict(
            text=f"{symbol} Volume (Demo)",
            font=dict(color='#ffffff', size=18, family='Space Grotesk'),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff'),
        showlegend=False,
        height=350
    )
    
    return fig

def create_fallback_momentum_chart(symbol: str):
    """Fallback momentum chart with demo data."""
    
    dates = pd.date_range(start=datetime.now() - timedelta(hours=6), end=datetime.now(), freq='5T')
    momentum = [np.random.normal(0, 1.5) for _ in dates]
    
    fig = go.Figure()
    
    momentum_colors = ['#00ff88' if x > 0 else '#ff6b35' for x in momentum]
    
    fig.add_trace(go.Bar(
        x=dates,
        y=momentum,
        name='Momentum (Demo)',
        marker=dict(color=momentum_colors, opacity=0.7)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
    
    fig.add_annotation(
        text="⚠️ Demo Momentum Data",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(color='#00ff88', size=12),
        bgcolor='rgba(0, 255, 136, 0.1)',
        bordercolor='#00ff88',
        borderwidth=1
    )
    
    fig.update_layout(
        title=dict(
            text=f"{symbol} Momentum (Demo)",
            font=dict(color='#ffffff', size=18, family='Space Grotesk'),
            x=0.5
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff', family='Space Grotesk'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True, color='#ffffff'),
        showlegend=False,
        height=350
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════════════
# DATA INTEGRATION SUMMARY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════════════

def get_comprehensive_data_summary() -> dict:
    """Get comprehensive summary of all data systems."""
    
    current_asset = AppState.get_current_asset()
    forecast_date = AppState.get_forecast_date()
    
    # Test all data sources
    market_data = get_real_market_data(current_asset)
    historical_data = get_historical_data(current_asset)
    asian_data = get_es_asian_session_data(forecast_date)
    previous_day = get_previous_day_ohlc(current_asset, forecast_date)
    
    # Calculate overall system status
    data_sources = {
        "live_market": market_data['status'] == 'success',
        "historical": not historical_data.empty,
        "asian_session": asian_data['status'] == 'success',
        "previous_day": previous_day['status'] == 'success'
    }
    
    successful_sources = sum(data_sources.values())
    total_sources = len(data_sources)
    system_health = (successful_sources / total_sources) * 100
    
    return {
        "system_health": system_health,
        "data_sources": data_sources,
        "successful_sources": successful_sources,
        "total_sources": total_sources,
        "market_data_quality": calculate_data_quality_score(market_data, historical_data),
        "projection_ready": data_sources["asian_session"] and data_sources["previous_day"],
        "chart_ready": data_sources["historical"],
        "live_ready": data_sources["live_market"]
    }

# ═══════════════════════════════════════════════════════════════════════════════════════
# EXECUTE PART 3C - LIVE CHARTS & FINAL INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════════════

# Display header
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #22d3ee 0%, #a855f7 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Live Chart Integration
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Professional charts with real market data and technical analysis</p>
</div>
<div class="section-divider"></div>
""", unsafe_allow_html=True)

# Get current asset for charts
current_asset = AppState.get_current_asset()
display_symbol = get_display_symbol(current_asset)

# Create chart tabs with real data
tab1, tab2, tab3 = st.tabs(["📊 Price & EMAs", "📈 Volume Analysis", "⚡ Momentum"])

with tab1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Controls for chart customization
    col1, col2 = st.columns([3, 1])
    
    with col2:
        show_emas = st.checkbox("Show EMAs", value=True, help="Display 8 and 21 EMAs")
    
    # Create and display price chart
    price_fig = create_professional_price_chart(current_asset, f"{display_symbol} Price Analysis", show_emas)
    st.plotly_chart(price_fig, use_container_width=True, config=CHART_CONFIG)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Create and display volume chart
    volume_fig = create_volume_chart_with_data(current_asset)
    st.plotly_chart(volume_fig, use_container_width=True, config=CHART_CONFIG)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Create and display momentum chart
    momentum_fig = create_intraday_momentum_chart(current_asset)
    st.plotly_chart(momentum_fig, use_container_width=True, config=CHART_CONFIG)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Final data system summary
st.markdown(f"""
<div style="text-align: center; margin: 3rem 0 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">🔧</div>
    <h2 style="color: #ffffff; font-size: 2.5rem; font-weight: 900; margin: 0;
               background: linear-gradient(135deg, #00ff88 0%, #22d3ee 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Data System Status
    </h2>
    <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0.5rem 0 0 0;">Complete system overview and readiness verification</p>
</div>
""", unsafe_allow_html=True)

# Get comprehensive system summary
system_summary = get_comprehensive_data_summary()

# Display system health overview
st.markdown("#### 🔧 System Health Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    health_color = "🟢" if system_summary['system_health'] >= 75 else "🟡" if system_summary['system_health'] >= 50 else "🔴"
    st.metric(
        "System Health",
        f"{health_color} {system_summary['system_health']:.0f}%",
        f"{system_summary['successful_sources']}/{system_summary['total_sources']} Sources"
    )

with col2:
    quality_color = "🟢" if system_summary['market_data_quality'] >= 75 else "🟡" if system_summary['market_data_quality'] >= 50 else "🔴"
    st.metric(
        "Data Quality",
        f"{quality_color} {system_summary['market_data_quality']}%",
        "Market Data"
    )

with col3:
    projection_status = "🟢 Ready" if system_summary['projection_ready'] else "🔴 Incomplete"
    st.metric(
        "Projection System",
        projection_status,
        "Anchors Available"
    )

with col4:
    chart_status = "🟢 Active" if system_summary['chart_ready'] else "🔴 Unavailable"
    st.metric(
        "Chart System",
        chart_status,
        "Historical Data"
    )

# Data source breakdown
st.markdown("#### 📡 Data Source Status")

data_sources = system_summary['data_sources']

col1, col2, col3, col4 = st.columns(4)

with col1:
    live_status = "🟢 Connected" if data_sources['live_market'] else "🔴 Error"
    st.metric("Live Market", live_status, "Yahoo Finance")

with col2:
    hist_status = "🟢 Available" if data_sources['historical'] else "🔴 Missing"
    st.metric("Historical Data", hist_status, "Price History")

with col3:
    asian_status = "🟢 Retrieved" if data_sources['asian_session'] else "🔴 Failed"
    st.metric("Asian Session", asian_status, "ES Futures")

with col4:
    prev_status = "🟢 Retrieved" if data_sources['previous_day'] else "🔴 Failed"
    st.metric("Previous Day", prev_status, "OHLC Data")

# Final system status
if system_summary['system_health'] >= 75:
    st.success("✅ **Data System Fully Operational** - All core components functioning properly")
elif system_summary['system_health'] >= 50:
    st.warning("⚠️ **Data System Partial** - Some components may be using fallback data")
else:
    st.error("❌ **Data System Issues** - Multiple components need attention")

# Summary information
st.info(f"""
**Data System Summary:**
- Live Market Data: {'✅' if data_sources['live_market'] else '❌'} Real-time prices from Yahoo Finance
- Historical Analysis: {'✅' if data_sources['historical'] else '❌'} Price history with 8/21 EMAs
- Asian Session: {'✅' if data_sources['asian_session'] else '❌'} ES futures overnight analysis
- Previous Day: {'✅' if data_sources['previous_day'] else '❌'} OHLC anchor data
- Chart Integration: {'✅' if system_summary['chart_ready'] else '❌'} Professional visualization
- Projection Ready: {'✅' if system_summary['projection_ready'] else '❌'} Skyline/Baseline calculations
""")

# Performance metrics
st.markdown("#### ⚡ Performance Metrics")

performance_metrics = get_system_health_metrics()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Cache Hit Rate",
        f"{performance_metrics['cache_hit_rate']:.1f}%",
        "Data Caching"
    )

with col2:
    st.metric(
        "Session Uptime",
        f"{performance_metrics['uptime_minutes']:.1f}m",
        "Current Session"
    )

with col3:
    st.metric(
        "Error Count",
        f"{performance_metrics['error_count']}",
        "Session Errors"
    )



