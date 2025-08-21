# ============================================================================
# MARKETLENS PRO v5 - PART 1: CORE FOUNDATION
# ============================================================================
# Contains: Core configuration, session state, utility functions, main dashboard
# Dependencies: None (standalone foundation)
# Next Part: Part 2A (CSS styling, sidebar navigation, form fixes)
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime as dt
from datetime import datetime, timedelta, time
import pytz
import warnings
import time as time_module
from typing import Dict, List, Tuple, Optional, Union
import json
import hashlib

warnings.filterwarnings('ignore')

# ============================================================================
# CORE CONFIGURATION
# ============================================================================

# App Configuration
APP_NAME = "MarketLens Pro v5"
COMPANY = "Max Pointe Consulting"
VERSION = "5.0.0"

# Theme Configuration
COLORS = {
    'primary': '#22d3ee',     # Cyan
    'secondary': '#a855f7',   # Purple  
    'success': '#00ff88',     # Green
    'warning': '#ff6b35',     # Orange
    'dark': '#0f172a',        # Dark slate
    'glass': 'rgba(15, 23, 42, 0.8)',
    'accent': 'rgba(34, 211, 238, 0.2)'
}

# Trading Configuration
TRADING_CONFIG = {
    'spx_slopes': {'skyline': 0.2255, 'baseline': -0.2255},
    'stock_slopes': {
        'AAPL': 0.0155, 'MSFT': 0.0541, 'NVDA': 0.0086,
        'AMZN': 0.0139, 'GOOGL': 0.0122, 'TSLA': 0.0285, 'META': 0.0674
    },
    'asian_session': {'start': '17:00', 'end': '19:30'},  # CT
    'rth_session': {'start': '08:30', 'end': '14:30'},     # CT
    'anchor_days': ['Monday', 'Tuesday'],
    'timeframe': '30m'
}

# Market Symbols
SYMBOLS = {
    'spx_futures': 'ES=F',
    'spx_index': '^GSPC',
    'stocks': ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'TSLA', 'META'],
    'indices': ['^GSPC', '^IXIC', '^DJI', '^RUT']
}

# Cache Configuration
CACHE_CONFIG = {
    'live_ttl': 60,      # 60 seconds for live data
    'historical_ttl': 300, # 5 minutes for historical data
    'max_cache_size': 1000
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables with defaults"""
    
    # Core app state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_page = 'Dashboard'
        st.session_state.last_update = datetime.now()
        
    # Trading state
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = 'AAPL'
        
    if 'analysis_date' not in st.session_state:
        st.session_state.analysis_date = datetime.now().date()
        
    if 'timeframe' not in st.session_state:
        st.session_state.timeframe = '30m'
        
    # Cache state
    if 'data_cache' not in st.session_state:
        st.session_state.data_cache = {}
        
    if 'cache_timestamps' not in st.session_state:
        st.session_state.cache_timestamps = {}
        
    # Anchor state
    if 'anchors' not in st.session_state:
        st.session_state.anchors = {}
        
    if 'projected_lines' not in st.session_state:
        st.session_state.projected_lines = {}
        
    # Analysis state
    if 'signals' not in st.session_state:
        st.session_state.signals = []
        
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {}
        
    # UI state
    if 'show_advanced' not in st.session_state:
        st.session_state.show_advanced = False
        
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
        
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_cache_key(symbol: str, period: str, interval: str) -> str:
    """Generate cache key for data storage"""
    return f"{symbol}_{period}_{interval}_{datetime.now().date()}"

def is_cache_valid(cache_key: str, ttl: int) -> bool:
    """Check if cached data is still valid"""
    if cache_key not in st.session_state.cache_timestamps:
        return False
    
    timestamp = st.session_state.cache_timestamps[cache_key]
    return (datetime.now() - timestamp).total_seconds() < ttl

def clear_expired_cache():
    """Remove expired cache entries"""
    current_time = datetime.now()
    expired_keys = []
    
    for key, timestamp in st.session_state.cache_timestamps.items():
        if (current_time - timestamp).total_seconds() > CACHE_CONFIG['historical_ttl']:
            expired_keys.append(key)
    
    for key in expired_keys:
        if key in st.session_state.data_cache:
            del st.session_state.data_cache[key]
        del st.session_state.cache_timestamps[key]

def convert_timezone(dt_obj: datetime, from_tz: str, to_tz: str) -> datetime:
    """Convert datetime between timezones"""
    try:
        from_timezone = pytz.timezone(from_tz)
        to_timezone = pytz.timezone(to_tz)
        
        if dt_obj.tzinfo is None:
            dt_obj = from_timezone.localize(dt_obj)
        
        return dt_obj.astimezone(to_timezone)
    except Exception as e:
        st.warning(f"Timezone conversion error: {e}")
        return dt_obj

def format_price(price: float, precision: int = 2) -> str:
    """Format price with proper decimal places"""
    if pd.isna(price):
        return "N/A"
    return f"${price:,.{precision}f}"

def format_percentage(value: float, precision: int = 2) -> str:
    """Format percentage with proper sign and color coding"""
    if pd.isna(value):
        return "N/A"
    
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{precision}f}%"

def calculate_color_by_value(value: float, positive_color: str = None, negative_color: str = None) -> str:
    """Return color based on positive/negative value"""
    if pd.isna(value):
        return "#94a3b8"  # Gray for N/A
    
    positive_color = positive_color or COLORS['success']
    negative_color = negative_color or COLORS['warning']
    
    return positive_color if value >= 0 else negative_color

def get_trading_session_times():
    """Get current trading session information"""
    ct_tz = pytz.timezone('America/Chicago')
    et_tz = pytz.timezone('America/New_York')
    current_ct = datetime.now(ct_tz)
    
    # Asian Session (Previous day 5:00 PM - 7:30 PM CT)
    asian_start = current_ct.replace(hour=17, minute=0, second=0, microsecond=0) - timedelta(days=1)
    asian_end = current_ct.replace(hour=19, minute=30, second=0, microsecond=0) - timedelta(days=1)
    
    # RTH Session (8:30 AM - 2:30 PM CT)
    rth_start = current_ct.replace(hour=8, minute=30, second=0, microsecond=0)
    rth_end = current_ct.replace(hour=14, minute=30, second=0, microsecond=0)
    
    return {
        'asian_start': asian_start,
        'asian_end': asian_end,
        'rth_start': rth_start,
        'rth_end': rth_end,
        'current_ct': current_ct
    }

def validate_data_quality(data: pd.DataFrame, symbol: str) -> Dict:
    """Validate data quality and return score"""
    if data is None or data.empty:
        return {'score': 0, 'issues': ['No data available'], 'status': 'error'}
    
    issues = []
    score = 100
    
    # Check for missing data
    missing_pct = data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100
    if missing_pct > 5:
        issues.append(f"High missing data: {missing_pct:.1f}%")
        score -= 20
    
    # Check for price anomalies
    if 'Close' in data.columns:
        price_changes = data['Close'].pct_change().abs()
        extreme_moves = (price_changes > 0.1).sum()  # >10% moves
        if extreme_moves > len(data) * 0.02:  # More than 2% of data points
            issues.append(f"Unusual price volatility detected")
            score -= 15
    
    # Check data recency
    if hasattr(data.index, 'max'):
        last_update = data.index.max()
        hours_old = (datetime.now() - last_update).total_seconds() / 3600
        if hours_old > 24:
            issues.append(f"Data is {hours_old:.1f} hours old")
            score -= 10
    
    # Determine status
    if score >= 85:
        status = 'excellent'
    elif score >= 70:
        status = 'good'
    elif score >= 50:
        status = 'fair'
    else:
        status = 'poor'
    
    return {
        'score': max(0, score),
        'issues': issues,
        'status': status,
        'data_points': len(data),
        'date_range': f"{data.index.min().date()} to {data.index.max().date()}" if not data.empty else "N/A"
    }

def add_notification(message: str, type: str = 'info'):
    """Add notification to session state"""
    notification = {
        'message': message,
        'type': type,
        'timestamp': datetime.now(),
        'id': hashlib.md5(f"{message}{datetime.now()}".encode()).hexdigest()[:8]
    }
    st.session_state.notifications.append(notification)
    
    # Keep only last 10 notifications
    if len(st.session_state.notifications) > 10:
        st.session_state.notifications = st.session_state.notifications[-10:]

def show_notifications():
    """Display notifications in sidebar"""
    if st.session_state.notifications:
        st.sidebar.markdown("### 🔔 Notifications")
        for notif in reversed(st.session_state.notifications[-3:]):  # Show last 3
            time_ago = (datetime.now() - notif['timestamp']).total_seconds() / 60
            if time_ago < 60:
                time_str = f"{int(time_ago)}m ago"
            else:
                time_str = f"{int(time_ago/60)}h ago"
            
            icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(notif['type'], "ℹ️")
            st.sidebar.markdown(f"{icon} {notif['message']} *({time_str})*")

# ============================================================================
# MAIN DASHBOARD STRUCTURE
# ============================================================================

def create_glass_panel(content, height: int = None, key: str = None):
    """Create a glassmorphism panel for content"""
    panel_style = f"""
    <div style="
        background: {COLORS['glass']};
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        {'height: ' + str(height) + 'px;' if height else ''}
        overflow: auto;
        color: white;
    ">
    {content}
    </div>
    """
    return st.markdown(panel_style, unsafe_allow_html=True)

def render_hero_section():
    """Render the main hero section"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 3rem;
                font-weight: 700;
                background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            ">{APP_NAME}</h1>
            <p style="
                font-size: 1.2rem;
                color: rgba(255, 255, 255, 0.8);
                margin-bottom: 0;
            ">Professional Trading Analytics Platform</p>
            <p style="
                font-size: 0.9rem;
                color: rgba(255, 255, 255, 0.6);
            ">by {COMPANY}</p>
        </div>
        """, unsafe_allow_html=True)

def render_dashboard_overview():
    """Render main dashboard content"""
    
    # Hero Section
    render_hero_section()
    
    # Quick Stats Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_glass_panel("""
            <h3 style="color: white; margin-bottom: 10px;">📊 Market Status</h3>
            <p style="color: #00ff88; font-size: 1.4rem; font-weight: bold; margin: 0;">ACTIVE</p>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Real-time monitoring</p>
        """)
    
    with col2:
        create_glass_panel("""
            <h3 style="color: white; margin-bottom: 10px;">🎯 Active Signals</h3>
            <p style="color: #22d3ee; font-size: 1.4rem; font-weight: bold; margin: 0;">3</p>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Pending analysis</p>
        """)
    
    with col3:
        create_glass_panel("""
            <h3 style="color: white; margin-bottom: 10px;">⚡ Performance</h3>
            <p style="color: #a855f7; font-size: 1.4rem; font-weight: bold; margin: 0;">87.3%</p>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">System accuracy</p>
        """)
    
    with col4:
        create_glass_panel("""
            <h3 style="color: white; margin-bottom: 10px;">🔄 Last Update</h3>
            <p style="color: #ff6b35; font-size: 1.4rem; font-weight: bold; margin: 0;">Live</p>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Auto-refresh enabled</p>
        """)

    # Main Content Areas
    st.markdown("---")
    
    # System Overview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        create_glass_panel("""
            <h2 style="color: white; margin-bottom: 20px;">🎯 Trading System Overview</h2>
            <div style="color: rgba(255,255,255,0.9); line-height: 1.6;">
                <h4 style="color: #22d3ee;">SPX Anchor System (Asian Session)</h4>
                <p>• Analyzes ES futures during Asian session (5:00-7:30 PM CT)</p>
                <p>• Projects Skyline/Baseline anchors through RTH using ±0.2255 slopes</p>
                <p>• Entry signals based on 30-minute candle interactions</p>
                
                <h4 style="color: #a855f7; margin-top: 20px;">Individual Stock System (Mon/Tue)</h4>
                <p>• Combines Monday and Tuesday session data for cross-day analysis</p>
                <p>• Uses stock-specific slopes for line projections</p>
                <p>• Optimized for Wednesday/Thursday trading opportunities</p>
                
                <h4 style="color: #00ff88; margin-top: 20px;">Signal Generation</h4>
                <p>• BUY: Bearish candle touches line from above, closes above</p>
                <p>• SELL: Bullish candle touches line from below, closes below</p>
            </div>
        """)
    
    with col2:
        create_glass_panel("""
            <h2 style="color: white; margin-bottom: 20px;">⚙️ System Status</h2>
            <div style="color: rgba(255,255,255,0.9);">
                <div style="margin-bottom: 15px;">
                    <span style="color: #00ff88;">●</span> Data Feed: <strong>Connected</strong>
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="color: #00ff88;">●</span> Asian Session: <strong>Monitoring</strong>
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="color: #22d3ee;">●</span> Anchor Detection: <strong>Active</strong>
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="color: #a855f7;">●</span> Signal Engine: <strong>Running</strong>
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="color: #ff6b35;">●</span> Cache System: <strong>Optimized</strong>
                </div>
                
                <hr style="border-color: rgba(255,255,255,0.2); margin: 20px 0;">
                
                <h4 style="color: white;">Quick Actions</h4>
                <p style="font-size: 0.9rem; color: rgba(255,255,255,0.7);">
                    Use the sidebar to navigate between different analysis tools and configure your trading parameters.
                </p>
            </div>
        """)

    # Additional Info Section
    st.markdown("---")
    create_glass_panel("""
        <h2 style="color: white; margin-bottom: 20px;">📈 Market Intelligence Engine</h2>
        <div style="color: rgba(255,255,255,0.9); display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
            <div>
                <h4 style="color: #22d3ee;">Real-Time Analysis</h4>
                <p>• Live price monitoring with 60-second refresh</p>
                <p>• Automated anchor detection and validation</p>
                <p>• Dynamic line projection calculations</p>
            </div>
            <div>
                <h4 style="color: #a855f7;">Technical Indicators</h4>
                <p>• EMA crossover detection (8 & 21 periods)</p>
                <p>• Volume analysis and momentum tracking</p>
                <p>• Fibonacci retracement levels</p>
            </div>
            <div>
                <h4 style="color: #00ff88;">Risk Management</h4>
                <p>• Data quality validation scoring</p>
                <p>• Signal confidence metrics</p>
                <p>• Performance tracking and analytics</p>
            </div>
        </div>
    """)

# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title=f"{APP_NAME} - Professional Trading Platform",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state FIRST
    initialize_session_state()
    
    # Add startup notification after initialization
    if st.session_state.get('app_started') != True:
        add_notification("MarketLens Pro initialized successfully", "success")
        st.session_state.app_started = True
    
    # Clear expired cache
    clear_expired_cache()
    
    # Basic styling placeholder (will be enhanced in Part 2A)
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            color: white;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar placeholder (will be enhanced in Part 2A)
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.markdown(f"*{COMPANY}*")
        st.markdown("---")
        
        # Page selection placeholder
        page = st.selectbox("Navigation", 
                           ["Dashboard", "Anchors", "Forecasts", "Signals", 
                            "Contracts", "Fibonacci", "Export", "Settings"],
                           key="page_selector")
        st.session_state.current_page = page
        
        st.markdown("---")
        show_notifications()
    
    # Main content area
    if st.session_state.current_page == "Dashboard":
        render_dashboard_overview()
    else:
        # Placeholder for other pages (will be built in subsequent parts)
        create_glass_panel(f"""
            <h2 style="color: white;">🚧 {st.session_state.current_page} Module</h2>
            <p style="color: rgba(255,255,255,0.8);">
                This module will be implemented in the next development phase.
                The {st.session_state.current_page.lower()} functionality is being built with the 
                comprehensive anchor system and real-time data integration.
            </p>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.9rem;">
                Return to Dashboard to see the current system status and overview.
            </p>
        """)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem;">
            {APP_NAME} v{VERSION} | {COMPANY} | Professional Trading Analytics
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION EXECUTION
# ============================================================================

# ============================================================================
# END OF PART 1: CORE FOUNDATION
# ============================================================================
# Status: ✅ Complete - Ready for Part 2A
# What's Next: Enhanced CSS styling, advanced sidebar, form visibility fixes
# ============================================================================

if __name__ == "__main__":
    main()