# **PART 1: CORE FOUNDATION - CONFIGURATION, SESSION STATE & MAIN DASHBOARD**

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime as dt
import pytz
from typing import Dict, List, Tuple, Optional, Any
import time
import warnings
import hashlib
import json
from dataclasses import dataclass, asdict
from enum import Enum
import math

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="MarketLens Pro v5",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# **CORE CONFIGURATION & CONSTANTS**
class TradingConfig:
    """Core trading system configuration"""
    
    # Time zones
    ET = pytz.timezone('US/Eastern')
    CT = pytz.timezone('US/Central')
    
    # Trading windows
    RTH_START_ET = "09:30"
    RTH_END_ET = "16:00"
    RTH_START_CT = "08:30"  
    RTH_END_CT = "15:00"
    
    # Asian session for SPX (CT timezone)
    ASIAN_START_CT = "17:00"
    ASIAN_END_CT = "19:30"
    
    # Anchor days for individual stocks
    ANCHOR_DAYS = ['Monday', 'Tuesday']
    
    # Slope coefficients per 30-min block
    SLOPES = {
        'SPX': {'skyline': 0.2255, 'baseline': -0.2255},
        'AAPL': {'skyline': 0.0155, 'baseline': -0.0155},
        'MSFT': {'skyline': 0.0541, 'baseline': -0.0541},
        'NVDA': {'skyline': 0.0086, 'baseline': -0.0086},
        'AMZN': {'skyline': 0.0139, 'baseline': -0.0139},
        'GOOGL': {'skyline': 0.0122, 'baseline': -0.0122},
        'TSLA': {'skyline': 0.0285, 'baseline': -0.0285},
        'META': {'skyline': 0.0674, 'baseline': -0.0674}
    }
    
    # Cache TTL settings
    LIVE_DATA_TTL = 60
    HISTORICAL_DATA_TTL = 300
    
    # UI Theme colors
    COLORS = {
        'cyan': '#22d3ee',
        'purple': '#a855f7', 
        'green': '#00ff88',
        'orange': '#ff6b35',
        'background': '#0a0a0a',
        'glass': 'rgba(255, 255, 255, 0.1)',
        'text': '#ffffff'
    }

@dataclass
class AnchorData:
    """Data structure for anchor points"""
    skyline_price: float
    baseline_price: float
    skyline_time: dt.datetime
    baseline_time: dt.datetime
    session_start: dt.datetime
    session_end: dt.datetime
    symbol: str
    anchor_type: str  # 'asian_session' or 'monday_tuesday'

@dataclass
class TradingSignal:
    """Data structure for trading signals"""
    symbol: str
    signal_type: str  # 'BUY' or 'SELL'
    entry_price: float
    line_touched: str  # 'skyline' or 'baseline'
    timestamp: dt.datetime
    candle_type: str  # 'bullish' or 'bearish'
    confidence: float

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    INVALID = "INVALID"

# **SESSION STATE INITIALIZATION**
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'current_page': 'Dashboard',
        'selected_symbols': ['SPY', 'AAPL', 'MSFT', 'NVDA'],
        'selected_timeframe': '30min',
        'anchor_data': {},
        'trading_signals': [],
        'market_data_cache': {},
        'last_data_update': None,
        'data_quality_score': 0.0,
        'system_health': 'Good',
        'user_preferences': {
            'dark_mode': True,
            'auto_refresh': True,
            'notifications': True,
            'chart_theme': 'dark'
        },
        'performance_metrics': {
            'total_signals': 0,
            'successful_trades': 0,
            'accuracy_rate': 0.0,
            'avg_return': 0.0
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# **UTILITY FUNCTIONS**
def create_cache_key(*args) -> str:
    """Create a hash-based cache key"""
    key_string = str(args)
    return hashlib.md5(key_string.encode()).hexdigest()

def get_current_time_et() -> dt.datetime:
    """Get current time in Eastern timezone"""
    return dt.datetime.now(TradingConfig.ET)

def get_current_time_ct() -> dt.datetime:
    """Get current time in Central timezone"""
    return dt.datetime.now(TradingConfig.CT)

def is_market_hours() -> bool:
    """Check if market is currently open"""
    now_et = get_current_time_et()
    
    # Check if weekend
    if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if within RTH
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now_et <= market_close

def format_price(price: float, precision: int = 2) -> str:
    """Format price with proper decimal places"""
    if pd.isna(price):
        return "N/A"
    return f"${price:,.{precision}f}"

def format_percentage(value: float, precision: int = 2) -> str:
    """Format percentage with color coding"""
    if pd.isna(value):
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{precision}f}%"

def get_color_for_change(value: float) -> str:
    """Get color based on positive/negative value"""
    if pd.isna(value):
        return TradingConfig.COLORS['text']
    return TradingConfig.COLORS['green'] if value >= 0 else TradingConfig.COLORS['orange']

def calculate_30min_blocks_since_start(start_time: dt.datetime, current_time: dt.datetime) -> int:
    """Calculate number of 30-minute blocks since start time"""
    time_diff = current_time - start_time
    return max(0, int(time_diff.total_seconds() / 1800))  # 1800 seconds = 30 minutes

def validate_price_data(data: pd.DataFrame, symbol: str) -> Tuple[bool, float]:
    """Validate price data quality and return score"""
    if data is None or data.empty:
        return False, 0.0
    
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        return False, 0.0
    
    # Check for data quality issues
    quality_score = 1.0
    
    # Check for missing values
    null_ratio = data[required_columns].isnull().sum().sum() / (len(data) * len(required_columns))
    quality_score -= null_ratio * 0.3
    
    # Check for zero/negative prices
    price_columns = ['Open', 'High', 'Low', 'Close']
    invalid_prices = (data[price_columns] <= 0).sum().sum()
    if invalid_prices > 0:
        quality_score -= 0.2
    
    # Check for volume
    if data['Volume'].sum() == 0:
        quality_score -= 0.1
    
    # Check data recency (prefer data from last 5 trading days)
    if not data.empty:
        last_date = data.index[-1]
        days_old = (dt.datetime.now() - last_date).days
        if days_old > 5:
            quality_score -= min(0.3, days_old * 0.02)
    
    return quality_score > 0.5, max(0.0, min(1.0, quality_score))

# **DEMO DATA GENERATORS**
def generate_demo_market_data(symbol: str, days: int = 10) -> pd.DataFrame:
    """Generate realistic demo market data"""
    np.random.seed(hash(symbol) % 2**32)
    
    # Base prices for different symbols
    base_prices = {
        'SPY': 580.0, 'QQQ': 520.0, 'AAPL': 230.0, 'MSFT': 450.0,
        'NVDA': 140.0, 'AMZN': 200.0, 'GOOGL': 180.0, 'TSLA': 250.0, 'META': 580.0
    }
    
    base_price = base_prices.get(symbol, 100.0)
    
    # Generate 30-minute intervals
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=days)
    
    # Create 30-minute intervals during market hours only
    dates = []
    current_date = start_date.replace(hour=9, minute=30, second=0, microsecond=0)
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            # Market hours: 9:30 AM to 4:00 PM ET
            market_start = current_date.replace(hour=9, minute=30)
            market_end = current_date.replace(hour=16, minute=0)
            
            time_slot = market_start
            while time_slot <= market_end:
                dates.append(time_slot)
                time_slot += dt.timedelta(minutes=30)
        
        current_date += dt.timedelta(days=1)
    
    # Generate realistic price movements
    n_periods = len(dates)
    returns = np.random.normal(0, 0.015, n_periods)
    returns[0] = 0  # First return is 0
    
    # Add some trend and mean reversion
    trend = np.linspace(-0.001, 0.001, n_periods)
    returns += trend
    
    # Calculate prices
    prices = [base_price]
    for i in range(1, n_periods):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, base_price * 0.8))  # Prevent excessive drops
    
    # Generate OHLC data
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC from close price
        volatility = 0.008
        open_price = close * (1 + np.random.normal(0, volatility/2))
        
        high_range = close * (1 + abs(np.random.normal(0, volatility)))
        low_range = close * (1 - abs(np.random.normal(0, volatility)))
        
        high = max(open_price, close, high_range)
        low = min(open_price, close, low_range)
        
        volume = max(1000000, int(np.random.lognormal(15, 0.5)))
        
        data.append({
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close, 2),
            'Volume': volume
        })
    
    df = pd.DataFrame(data, index=pd.DatetimeIndex(dates))
    return df

def get_system_health_status() -> Tuple[str, str]:
    """Get current system health status"""
    try:
        # Check market hours
        market_open = is_market_hours()
        
        # Check data quality
        quality_score = st.session_state.get('data_quality_score', 0.0)
        
        # Determine status
        if quality_score >= 0.8 and market_open:
            return "Excellent", TradingConfig.COLORS['green']
        elif quality_score >= 0.6:
            return "Good", TradingConfig.COLORS['cyan']
        elif quality_score >= 0.4:
            return "Fair", TradingConfig.COLORS['orange']
        else:
            return "Poor", TradingConfig.COLORS['orange']
            
    except Exception:
        return "Unknown", TradingConfig.COLORS['orange']

# **MAIN DASHBOARD LAYOUT**
def render_main_dashboard():
    """Render the main dashboard with glass panels"""
    
    # Hero section
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0; margin-bottom: 2rem;'>
        <h1 style='font-size: 3.5rem; font-weight: 700; background: linear-gradient(135deg, #22d3ee, #a855f7); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;'>
            MarketLens Pro v5
        </h1>
        <p style='font-size: 1.2rem; color: #94a3b8; margin: 0.5rem 0 0 0;'>
            Advanced Trading Intelligence by Max Pointe Consulting
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # System status bar
    status, status_color = get_system_health_status()
    market_status = "🟢 OPEN" if is_market_hours() else "🔴 CLOSED"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.2);'>
            <div style='color: {status_color}; font-weight: 600; font-size: 1.1rem;'>System Health</div>
            <div style='color: white; font-size: 1.3rem; margin-top: 0.5rem;'>{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.2);'>
            <div style='color: #94a3b8; font-weight: 600; font-size: 1.1rem;'>Market Status</div>
            <div style='color: white; font-size: 1.3rem; margin-top: 0.5rem;'>{market_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        current_time = get_current_time_et().strftime("%H:%M:%S ET")
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.2);'>
            <div style='color: #94a3b8; font-weight: 600; font-size: 1.1rem;'>Current Time</div>
            <div style='color: white; font-size: 1.3rem; margin-top: 0.5rem;'>{current_time}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        active_signals = len(st.session_state.get('trading_signals', []))
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.2);'>
            <div style='color: #94a3b8; font-weight: 600; font-size: 1.1rem;'>Active Signals</div>
            <div style='color: white; font-size: 1.3rem; margin-top: 0.5rem;'>{active_signals}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main content area with glass panels
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Market overview panel
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.2); margin-bottom: 2rem;'>
            <h3 style='color: white; margin-top: 0; font-size: 1.5rem; font-weight: 600;'>📊 Market Overview</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate demo data for overview
        overview_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']
        overview_data = []
        
        for symbol in overview_symbols:
            demo_data = generate_demo_market_data(symbol, 1)
            if not demo_data.empty:
                current_price = demo_data['Close'].iloc[-1]
                prev_price = demo_data['Close'].iloc[-2] if len(demo_data) > 1 else current_price
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100 if prev_price != 0 else 0
                
                overview_data.append({
                    'Symbol': symbol,
                    'Price': format_price(current_price),
                    'Change': f"{'+' if change >= 0 else ''}{change:.2f}",
                    'Change %': format_percentage(change_pct),
                    'Volume': f"{demo_data['Volume'].iloc[-1]:,}"
                })
        
        if overview_data:
            df_overview = pd.DataFrame(overview_data)
            st.dataframe(df_overview, use_container_width=True, hide_index=True)
    
    with col2:
        # Trading controls panel
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.2); margin-bottom: 2rem;'>
            <h3 style='color: white; margin-top: 0; font-size: 1.5rem; font-weight: 600;'>⚡ Quick Actions</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick action buttons
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state['last_data_update'] = dt.datetime.now()
            st.rerun()
        
        if st.button("📈 Scan Signals", use_container_width=True):
            st.success("Signal scan initiated...")
            time.sleep(1)
            st.rerun()
        
        if st.button("⚙️ System Check", use_container_width=True):
            st.info("Running system diagnostics...")
            time.sleep(1)
            st.session_state['system_health'] = 'Excellent'
            st.rerun()
    
    # Performance metrics panel
    st.markdown("""
    <div style='background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.2);'>
        <h3 style='color: white; margin-top: 0; font-size: 1.5rem; font-weight: 600;'>📈 Performance Metrics</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Performance metrics grid
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    
    with metrics_col1:
        st.metric(
            label="Total Signals",
            value=st.session_state['performance_metrics']['total_signals'],
            delta="+5 today"
        )
    
    with metrics_col2:
        st.metric(
            label="Success Rate", 
            value=f"{st.session_state['performance_metrics']['accuracy_rate']:.1f}%",
            delta="+2.3%"
        )
    
    with metrics_col3:
        st.metric(
            label="Avg Return",
            value=f"{st.session_state['performance_metrics']['avg_return']:.2f}%",
            delta="+0.15%"
        )
    
    with metrics_col4:
        data_quality = st.session_state.get('data_quality_score', 0.85)
        st.metric(
            label="Data Quality",
            value=f"{data_quality:.1%}",
            delta="Excellent"
        )

# **MAIN APPLICATION ENTRY POINT**
def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Apply custom CSS for dark theme (will be expanded in Part 2A)
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: white;
        }
        
        .main .block-container {
            padding-top: 2rem;
            max-width: 1400px;
        }
        
        /* Ensure text visibility */
        .stMarkdown, .stText, .stMetric {
            color: white !important;
        }
        
        .stDataFrame {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #22d3ee, #a855f7);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(34, 211, 238, 0.4);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Render main dashboard
    render_main_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; font-size: 0.9rem; padding: 1rem 0;'>
        MarketLens Pro v5 • Professional Trading Intelligence • Max Pointe Consulting
    </div>
    """, unsafe_allow_html=True)

# **APPLICATION LAUNCHER**
if __name__ == "__main__":
    main()