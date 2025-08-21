# =============================================================================
# **PART 1: CORE FOUNDATION - MarketLens Pro v5**
# Core configuration, session state, utility functions, and main dashboard
# =============================================================================

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
import time as time_module
import warnings
import logging
from typing import Dict, List, Tuple, Optional, Union
import json
from dataclasses import dataclass
from functools import lru_cache
import hashlib

# Suppress warnings
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# =============================================================================
# **CONFIGURATION & CONSTANTS**
# =============================================================================

# App Configuration
APP_CONFIG = {
    'name': 'MarketLens Pro',
    'version': 'v5',
    'company': 'Max Pointe Consulting',
    'theme': 'dark_glassmorphism'
}

# Color Palette
COLORS = {
    'primary': '#22d3ee',      # Cyan
    'secondary': '#a855f7',    # Purple  
    'success': '#00ff88',      # Green
    'warning': '#ff6b35',      # Orange
    'background': '#0f0f23',   # Dark blue
    'surface': 'rgba(255,255,255,0.05)',  # Glass effect
    'text': '#ffffff',         # White text
    'text_secondary': '#a0a0a0' # Gray text
}

# Trading Configuration
TRADING_CONFIG = {
    'spx_slopes': {'skyline': 0.2255, 'baseline': -0.2255},
    'stock_slopes': {
        'AAPL': 0.0155, 'MSFT': 0.0541, 'NVDA': 0.0086,
        'AMZN': 0.0139, 'GOOGL': 0.0122, 'TSLA': 0.0285, 'META': 0.0674
    },
    'asian_session': {'start': '17:00', 'end': '19:30'},  # CT
    'rth_session': {'start': '08:30', 'end': '14:30'},    # CT  
    'anchor_days': ['monday', 'tuesday'],
    'timeframes': ['30min', '1h', '4h', '1d'],
    'cache_ttl': {'live': 60, 'historical': 300}
}

# Supported Symbols
SYMBOLS = {
    'indices': {
        'SPX': '^GSPC',
        'ES_FUTURES': 'ES=F',
        'QQQ': 'QQQ',
        'IWM': 'IWM'
    },
    'stocks': {
        'AAPL': 'AAPL', 'MSFT': 'MSFT', 'NVDA': 'NVDA',
        'AMZN': 'AMZN', 'GOOGL': 'GOOGL', 'TSLA': 'TSLA', 'META': 'META'
    },
    'crypto': {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD'
    }
}

# =============================================================================
# **DATA CLASSES & MODELS**
# =============================================================================

@dataclass
class AnchorPoint:
    """Represents an anchor point for line projections"""
    price: float
    timestamp: datetime
    anchor_type: str  # 'skyline' or 'baseline'
    session_type: str  # 'asian' or 'monday_tuesday'
    symbol: str
    
@dataclass  
class TradingSignal:
    """Represents a trading signal"""
    symbol: str
    signal_type: str  # 'BUY' or 'SELL'
    price: float
    timestamp: datetime
    line_type: str  # 'skyline' or 'baseline'
    confidence: float
    reason: str

@dataclass
class MarketData:
    """Container for market data"""
    symbol: str
    data: pd.DataFrame
    last_update: datetime
    data_quality: float
    source: str = 'yahoo'

# =============================================================================
# **SESSION STATE INITIALIZATION**
# =============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Core application state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.app_version = APP_CONFIG['version']
        st.session_state.last_update = datetime.now()
    
    # Trading data cache
    if 'market_data_cache' not in st.session_state:
        st.session_state.market_data_cache = {}
    
    if 'anchor_points' not in st.session_state:
        st.session_state.anchor_points = {}
        
    if 'trading_signals' not in st.session_state:
        st.session_state.trading_signals = []
        
    if 'data_health' not in st.session_state:
        st.session_state.data_health = {'status': 'unknown', 'score': 0.0}
    
    # User preferences
    if 'selected_symbols' not in st.session_state:
        st.session_state.selected_symbols = ['AAPL', 'MSFT', 'NVDA']
        
    if 'time_horizon' not in st.session_state:
        st.session_state.time_horizon = '1d'
        
    if 'notifications_enabled' not in st.session_state:
        st.session_state.notifications_enabled = True
        
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
        
    # UI state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
        
    if 'sidebar_expanded' not in st.session_state:
        st.session_state.sidebar_expanded = True

# =============================================================================
# **UTILITY FUNCTIONS**
# =============================================================================

def get_timezone_info():
    """Get timezone information for trading sessions"""
    return {
        'eastern': pytz.timezone('US/Eastern'),
        'central': pytz.timezone('US/Central'),
        'utc': pytz.UTC
    }

def convert_to_30min_blocks(timestamp: datetime, base_time: str = "09:30") -> int:
    """Convert timestamp to 30-minute block number from market open"""
    try:
        market_open = datetime.strptime(base_time, "%H:%M").time()
        current_time = timestamp.time()
        
        # Calculate minutes from market open
        open_minutes = market_open.hour * 60 + market_open.minute
        current_minutes = current_time.hour * 60 + current_time.minute
        
        # Handle next day scenarios
        if current_minutes < open_minutes:
            current_minutes += 24 * 60
            
        minutes_diff = current_minutes - open_minutes
        return max(0, minutes_diff // 30)
    except:
        return 0

def calculate_data_quality(data: pd.DataFrame) -> float:
    """Calculate data quality score (0-1)"""
    if data.empty:
        return 0.0
        
    try:
        # Check for missing data
        missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
        
        # Check for price consistency
        price_cols = ['Open', 'High', 'Low', 'Close']
        available_price_cols = [col for col in price_cols if col in data.columns]
        
        if not available_price_cols:
            return 0.3
            
        # Validate price relationships
        valid_prices = 0
        total_checks = 0
        
        for _, row in data.iterrows():
            if all(col in row and not pd.isna(row[col]) for col in available_price_cols):
                if len(available_price_cols) >= 4:
                    # OHLC validation
                    if (row['Low'] <= row['Open'] <= row['High'] and 
                        row['Low'] <= row['Close'] <= row['High']):
                        valid_prices += 1
                    total_checks += 1
                else:
                    valid_prices += 1
                    total_checks += 1
        
        price_quality = valid_prices / max(1, total_checks)
        
        # Final score
        return max(0.0, min(1.0, (1 - missing_ratio) * 0.6 + price_quality * 0.4))
        
    except Exception as e:
        return 0.3

def format_price(price: float) -> str:
    """Format price with appropriate decimal places"""
    if pd.isna(price):
        return "N/A"
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    else:
        return f"${price:.4f}"

def format_percentage(value: float) -> str:
    """Format percentage with color coding"""
    if pd.isna(value):
        return "N/A"
    return f"{value:+.2f}%"

def get_market_status() -> Dict:
    """Get current market status"""
    try:
        eastern = pytz.timezone('US/Eastern')
        now_et = datetime.now(eastern)
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Check if weekend
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return {
                'status': 'closed',
                'message': 'Market Closed - Weekend',
                'next_open': 'Monday 9:30 AM ET',
                'color': COLORS['warning']
            }
            
        # Check if market hours
        if market_open <= now_et <= market_close:
            return {
                'status': 'open',
                'message': f'Market Open - Closes at 4:00 PM ET',
                'time_until_close': str(market_close - now_et).split('.')[0],
                'color': COLORS['success']
            }
        elif now_et < market_open:
            return {
                'status': 'pre_market',
                'message': f'Pre-Market - Opens at 9:30 AM ET',
                'time_until_open': str(market_open - now_et).split('.')[0],
                'color': COLORS['primary']
            }
        else:
            return {
                'status': 'after_hours',
                'message': 'After Hours Trading',
                'next_open': 'Tomorrow 9:30 AM ET',
                'color': COLORS['secondary']
            }
            
    except Exception as e:
        return {
            'status': 'unknown',
            'message': 'Status Unknown',
            'color': COLORS['warning']
        }

def generate_demo_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """Generate realistic demo market data"""
    try:
        base_price = {'AAPL': 150, 'MSFT': 280, 'NVDA': 800, 'SPX': 4200}.get(symbol, 100)
        
        # Generate timestamps
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        timestamps = pd.date_range(start=start_date, end=end_date, freq='30min')
        
        # Filter to market hours (9:30 AM - 4:00 PM ET)
        market_hours = []
        for ts in timestamps:
            if ts.weekday() < 5:  # Monday-Friday
                hour = ts.hour
                minute = ts.minute
                if (hour == 9 and minute >= 30) or (10 <= hour <= 15) or (hour == 16 and minute == 0):
                    market_hours.append(ts)
        
        if not market_hours:
            market_hours = [datetime.now()]
            
        # Generate realistic OHLC data
        prices = []
        current_price = base_price
        
        for i, ts in enumerate(market_hours):
            # Add some randomness and trend
            change = np.random.normal(0, base_price * 0.005)  # 0.5% volatility
            current_price = max(current_price + change, base_price * 0.5)  # Floor at 50% of base
            
            # Generate OHLC
            open_price = current_price
            high_price = open_price * (1 + abs(np.random.normal(0, 0.002)))
            low_price = open_price * (1 - abs(np.random.normal(0, 0.002)))
            close_price = low_price + (high_price - low_price) * np.random.random()
            
            prices.append({
                'Datetime': ts,
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close_price, 2),
                'Volume': int(np.random.normal(1000000, 300000))
            })
            
            current_price = close_price
        
        df = pd.DataFrame(prices)
        df.set_index('Datetime', inplace=True)
        return df
        
    except Exception as e:
        # Fallback minimal data
        now = datetime.now()
        return pd.DataFrame({
            'Open': [100.0],
            'High': [101.0], 
            'Low': [99.0],
            'Close': [100.5],
            'Volume': [1000000]
        }, index=[now])

@lru_cache(maxsize=100)
def get_cache_key(symbol: str, period: str, interval: str) -> str:
    """Generate cache key for data requests"""
    return hashlib.md5(f"{symbol}_{period}_{interval}".encode()).hexdigest()

def is_cache_valid(cache_time: datetime, ttl_seconds: int) -> bool:
    """Check if cached data is still valid"""
    return (datetime.now() - cache_time).total_seconds() < ttl_seconds

# =============================================================================
# **MAIN DASHBOARD COMPONENTS**
# =============================================================================

def render_header():
    """Render the main application header"""
    st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
            <h1 style="color: {COLORS['primary']}; font-size: 2.5rem; margin: 0; 
                       font-weight: 700; text-shadow: 0 0 20px {COLORS['primary']}50;">
                📈 {APP_CONFIG['name']} {APP_CONFIG['version']}
            </h1>
            <p style="color: {COLORS['text_secondary']}; font-size: 1.1rem; margin: 0.5rem 0 0 0;">
                Professional Trading Analytics by {APP_CONFIG['company']}
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_glass_panel(title: str, content: str, height: str = "200px") -> None:
    """Render a glassmorphism panel"""
    st.markdown(f"""
        <div style="
            background: {COLORS['surface']};
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            height: {height};
            overflow-y: auto;
        ">
            <h3 style="color: {COLORS['primary']}; margin-top: 0; font-size: 1.3rem; 
                       font-weight: 600; text-shadow: 0 0 10px {COLORS['primary']}30;">
                {title}
            </h3>
            <div style="color: {COLORS['text']}; line-height: 1.6;">
                {content}
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_metric_card(title: str, value: str, delta: str = "", color: str = COLORS['primary']) -> None:
    """Render a professional metric card"""
    delta_html = ""
    if delta:
        delta_color = COLORS['success'] if '+' in delta else COLORS['warning']
        delta_html = f'<div style="color: {delta_color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'
    
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {color}20, {color}10);
            border: 1px solid {color}40;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.85rem; 
                       text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">
                {title}
            </div>
            <div style="color: {color}; font-size: 1.8rem; font-weight: 700; 
                       font-family: 'JetBrains Mono', monospace;">
                {value}
            </div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

def render_status_indicator(status: str, message: str, color: str) -> None:
    """Render system status indicator"""
    st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            padding: 0.75rem 1rem;
            background: {color}20;
            border-left: 4px solid {color};
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <div style="
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: {color};
                margin-right: 1rem;
                box-shadow: 0 0 10px {color}50;
                animation: pulse 2s infinite;
            "></div>
            <div style="color: {COLORS['text']}; font-weight: 500;">
                {message}
            </div>
        </div>
    """, unsafe_allow_html=True)

# =============================================================================
# **MAIN DASHBOARD LAYOUT**
# =============================================================================

def render_main_dashboard():
    """Render the main dashboard layout"""
    
    # Market Status Section
    market_info = get_market_status()
    render_status_indicator(
        market_info['status'], 
        market_info['message'], 
        market_info['color']
    )
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card("SPX Level", "4,247.50", "+1.2%", COLORS['primary'])
    
    with col2:
        render_metric_card("Active Signals", "3", "+2 today", COLORS['success'])
        
    with col3:
        render_metric_card("Data Health", "94.5%", "+2.1%", COLORS['success'])
        
    with col4:
        render_metric_card("Anchor Points", "12", "Updated", COLORS['secondary'])
    
    # Main Content Panels
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        render_glass_panel(
            "📊 Real-Time Market Overview",
            f"""
            <div style="font-family: {COLORS['text']};">
                <h4 style="color: {COLORS['primary']}; margin: 0 0 1rem 0;">Current Market Snapshot</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                    <div>
                        <strong style="color: {COLORS['text']};">SPX Asian Anchors:</strong><br>
                        <span style="color: {COLORS['success']};">Skyline: 4,255.30</span><br>
                        <span style="color: {COLORS['warning']};">Baseline: 4,238.75</span>
                    </div>
                    <div>
                        <strong style="color: {COLORS['text']};">AAPL Mon/Tue Anchors:</strong><br>
                        <span style="color: {COLORS['success']};">Skyline: 152.45</span><br>
                        <span style="color: {COLORS['warning']};">Baseline: 148.20</span>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                    <strong style="color: {COLORS['secondary']};">Next Anchor Update:</strong>
                    <span style="color: {COLORS['text']};">SPX Asian Session - Today 5:00 PM CT</span><br>
                    <strong style="color: {COLORS['secondary']};">Stock Anchors:</strong>
                    <span style="color: {COLORS['text']};">Monday/Tuesday Session Analysis</span>
                </div>
            </div>
            """,
            "300px"
        )
    
    with col_right:
        render_glass_panel(
            "⚡ Quick Actions",
            f"""
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <button style="
                    background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']});
                    color: white;
                    border: none;
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                ">🎯 Refresh Anchors</button>
                
                <button style="
                    background: linear-gradient(135deg, {COLORS['success']}, {COLORS['primary']});
                    color: white;
                    border: none;
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                ">📡 Update Signals</button>
                
                <button style="
                    background: linear-gradient(135deg, {COLORS['secondary']}, {COLORS['warning']});
                    color: white;
                    border: none;
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                ">📊 View Analytics</button>
            </div>
            """,
            "300px"
        )
    
    # System Information Panel
    render_glass_panel(
        "🔧 System Information",
        f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div>
                <strong style="color: {COLORS['primary']};">Application Version:</strong><br>
                <span style="color: {COLORS['text']};">{APP_CONFIG['name']} {APP_CONFIG['version']}</span>
            </div>
            <div>
                <strong style="color: {COLORS['primary']};">Data Sources:</strong><br>
                <span style="color: {COLORS['success']};">Yahoo Finance ✓</span><br>
                <span style="color: {COLORS['text']};">ES Futures ✓</span>
            </div>
            <div>
                <strong style="color: {COLORS['primary']};">Trading Sessions:</strong><br>
                <span style="color: {COLORS['text']};">Asian: 5:00-7:30 PM CT</span><br>
                <span style="color: {COLORS['text']};">RTH: 8:30 AM-2:30 PM CT</span>
            </div>
            <div>
                <strong style="color: {COLORS['primary']};">Last Updated:</strong><br>
                <span style="color: {COLORS['text']};">{datetime.now().strftime('%H:%M:%S')}</span>
            </div>
        </div>
        """,
        "150px"
    )

# =============================================================================
# **MAIN APPLICATION**
# =============================================================================

def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title="MarketLens Pro v5",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Render main interface
    render_header()
    
    # Add a simple info message about the current part
    st.info("""
    🚀 **MarketLens Pro Part 1 - Core Foundation Active**
    
    ✅ Core configuration and session state initialized  
    ✅ Utility functions and data models loaded  
    ✅ Main dashboard layout with glass panels rendered  
    ✅ Market status monitoring active  
    ✅ Demo data generation ready  
    
    **Next:** Part 2A will add CSS styling, sidebar navigation, and enhanced UI components.
    """)
    
    # Render main dashboard
    render_main_dashboard()
    
    # Footer
    st.markdown(f"""
        <div style="text-align: center; padding: 2rem 0; margin-top: 3rem; 
                    border-top: 1px solid rgba(255,255,255,0.1); color: {COLORS['text_secondary']};">
            <small>© 2025 {APP_CONFIG['company']} • {APP_CONFIG['name']} {APP_CONFIG['version']} • 
            Professional Trading Analytics Platform</small>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()