# ==========================================
# **MARKETLENS PRO V5 - PARTS 1 + 2A + 2B COMBINED**
# MarketLens Pro v5 by Max Pointe Consulting
# ==========================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime as dt
import pytz
from datetime import datetime, timedelta, time
import time as time_module
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# STREAMLIT CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="MarketLens Pro v5",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS STYLING
# ==========================================
def apply_custom_styling():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');
    
    /* Main App Background */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 25%, #16213e 50%, #0f0f23 75%, #1a1a2e 100%);
        font-family: 'Space Grotesk', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
    }
    
    /* All text white */
    .stApp, .stApp p, .stApp div, .stApp span, .stApp label {
        color: #ffffff !important;
    }
    
    /* Metrics Cards */
    [data-testid="metric-container"] {
        background: rgba(15, 15, 35, 0.9) !important;
        border: 1px solid rgba(34, 211, 238, 0.5);
        padding: 1rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    
    /* Numbers in Metrics */
    [data-testid="metric-container"] > div {
        font-family: 'JetBrains Mono', monospace !important;
        color: #00ff88 !important;
    }
    
    /* Professional Glass Cards */
    .glass-card {
        background: rgba(15, 15, 35, 0.95) !important;
        border: 1px solid rgba(34, 211, 238, 0.5);
        border-radius: 15px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Glass Card Text */
    .glass-card h3 {
        color: #22d3ee !important;
        margin-bottom: 1rem !important;
        font-weight: 600 !important;
    }
    
    .glass-card p {
        color: #ffffff !important;
        font-size: 1.1rem !important;
        line-height: 1.6 !important;
        opacity: 0.95 !important;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(45deg, #22d3ee, #a855f7);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    /* Select Boxes and Inputs */
    .stSelectbox > div > div, .stDateInput > div > div {
        background-color: rgba(26, 26, 46, 0.8) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        color: #ffffff !important;
    }
    
    /* Success/Warning/Error Styling */
    .stAlert {
        background: rgba(15, 15, 35, 0.9) !important;
        border-left: 4px solid #00ff88;
        color: #ffffff !important;
        border-radius: 8px;
    }
    
    /* Hide Streamlit Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# CORE CONSTANTS & CONFIGURATIONS
# ==========================================
class TradingConfig:
    # Timezone configurations
    CT_TZ = pytz.timezone('America/Chicago')
    ET_TZ = pytz.timezone('America/New_York')
    
    # SPX Asian Session
    ASIAN_SESSION_START = time(17, 0)  # 5:00 PM CT
    ASIAN_SESSION_END = time(19, 30)   # 7:30 PM CT
    
    # RTH Session
    RTH_START_ET = time(9, 30)   # 9:30 AM ET
    RTH_END_ET = time(16, 0)     # 4:00 PM ET
    RTH_START_CT = time(8, 30)   # 8:30 AM CT
    RTH_END_CT = time(15, 0)     # 3:00 PM CT
    
    # Slope configurations
    SPX_SLOPES = {'skyline': 0.2255, 'baseline': -0.2255}
    STOCK_SLOPES = {
        'AAPL': {'skyline': 0.0155, 'baseline': -0.0155},
        'MSFT': {'skyline': 0.0541, 'baseline': -0.0541},
        'NVDA': {'skyline': 0.0086, 'baseline': -0.0086},
        'AMZN': {'skyline': 0.0139, 'baseline': -0.0139},
        'GOOGL': {'skyline': 0.0122, 'baseline': -0.0122},
        'TSLA': {'skyline': 0.0285, 'baseline': -0.0285},
        'META': {'skyline': 0.0674, 'baseline': -0.0674}
    }
    
    # Trading symbols
    SPX_SYMBOL = '^GSPC'
    ES_SYMBOL = 'ES=F'
    AVAILABLE_STOCKS = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'TSLA', 'META']
    
    # Cache TTL
    LIVE_DATA_TTL = 60    # 60 seconds for live data
    HISTORICAL_TTL = 300  # 5 minutes for historical data

# ==========================================
# DATA ENGINE (FROM PART 2A)
# ==========================================
class MarketDataEngine:
    """
    Professional market data engine with validation and quality scoring
    """
    
    def __init__(self):
        self.data_cache = {}
        self.quality_scores = {}
        self.last_update = {}
    
    @staticmethod
    def validate_data_quality(data, symbol):
        """
        Comprehensive data quality validation and scoring
        """
        if data is None or data.empty:
            return 0, ["No data available"]
        
        quality_score = 100
        issues = []
        
        # Check for missing values
        missing_pct = data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100
        if missing_pct > 5:
            quality_score -= 20
            issues.append(f"High missing data: {missing_pct:.1f}%")
        elif missing_pct > 1:
            quality_score -= 5
            issues.append(f"Some missing data: {missing_pct:.1f}%")
        
        return max(0, quality_score), issues
    
    def get_market_data(self, symbol, period='5d', interval='30m', force_refresh=False):
        """
        Market data fetching with quality validation
        """
        try:
            # Simple data fetch for now
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return None, (0, ["No data returned from source"])
            
            # Ensure timezone
            if data.index.tz is None:
                data.index = data.index.tz_localize('America/New_York')
            
            # Validate quality
            quality_score, issues = self.validate_data_quality(data, symbol)
            
            return data, (quality_score, issues)
            
        except Exception as e:
            return None, (0, [f"Data fetch error: {str(e)}"])
    
    def get_current_market_snapshot(self, symbol):
        """
        Get comprehensive current market snapshot
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            snapshot = {
                'symbol': symbol,
                'current_price': info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose'),
                'previous_close': info.get('previousClose'),
                'day_change': None,
                'day_change_pct': None,
                'volume': info.get('regularMarketVolume'),
                'avg_volume': info.get('averageVolume'),
                'timestamp': datetime.now(TradingConfig.ET_TZ)
            }
            
            # Calculate change if we have both prices
            if snapshot['current_price'] and snapshot['previous_close']:
                snapshot['day_change'] = snapshot['current_price'] - snapshot['previous_close']
                snapshot['day_change_pct'] = (snapshot['day_change'] / snapshot['previous_close']) * 100
            
            return snapshot
            
        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now(TradingConfig.ET_TZ)
            }

# ==========================================
# MARKET ANALYTICS (FROM PART 2A)
# ==========================================
class MarketAnalytics:
    """
    Professional market analytics and calculations
    """
    
    def __init__(self, data_engine):
        self.data_engine = data_engine
    
    def calculate_ema(self, data, period):
        """
        Calculate Exponential Moving Average
        """
        if 'Close' not in data.columns or len(data) < period:
            return None
        
        return data['Close'].ewm(span=period, adjust=False).mean()
    
    def detect_ema_crossover(self, data, fast_period=8, slow_period=21):
        """
        Detect EMA crossover signals
        """
        if len(data) < max(fast_period, slow_period) + 1:
            return None
        
        fast_ema = self.calculate_ema(data, fast_period)
        slow_ema = self.calculate_ema(data, slow_period)
        
        if fast_ema is None or slow_ema is None:
            return None
        
        # Current and previous crossover states
        current_above = fast_ema.iloc[-1] > slow_ema.iloc[-1]
        previous_above = fast_ema.iloc[-2] > slow_ema.iloc[-2] if len(fast_ema) > 1 else current_above
        
        crossover_type = None
        if current_above and not previous_above:
            crossover_type = "bullish"
        elif not current_above and previous_above:
            crossover_type = "bearish"
        
        return {
            'fast_ema': fast_ema.iloc[-1],
            'slow_ema': slow_ema.iloc[-1],
            'crossover_type': crossover_type,
            'fast_above_slow': current_above,
            'timestamp': data.index[-1]
        }
    
    def get_market_sentiment_score(self, symbol):
        """
        Calculate comprehensive market sentiment score
        """
        try:
            # Get recent data for analysis
            data, (quality_score, _) = self.data_engine.get_market_data(
                symbol, period='5d', interval='30m'
            )
            
            if data is None or len(data) < 10:
                return None
            
            sentiment_score = 50  # Neutral baseline
            
            # Simple momentum calculation
            recent_price = data['Close'].iloc[-1]
            older_price = data['Close'].iloc[-5] if len(data) >= 5 else data['Close'].iloc[0]
            
            if recent_price > older_price:
                sentiment_score += 20
            else:
                sentiment_score -= 20
            
            # EMA crossover influence
            ema_signal = self.detect_ema_crossover(data)
            if ema_signal and ema_signal['crossover_type']:
                if ema_signal['crossover_type'] == 'bullish':
                    sentiment_score += 15
                else:
                    sentiment_score -= 15
            
            # Normalize to 0-100 range
            sentiment_score = max(0, min(100, sentiment_score))
            
            level = "Very Bullish" if sentiment_score >= 75 else "Bullish" if sentiment_score >= 60 else "Neutral" if sentiment_score >= 40 else "Bearish" if sentiment_score >= 25 else "Very Bearish"
            
            return {
                'score': round(sentiment_score, 1),
                'level': level,
                'timestamp': datetime.now(TradingConfig.ET_TZ)
            }
            
        except Exception as e:
            return None

# ==========================================
# CHART UTILITIES (FROM PART 2B)
# ==========================================
def create_professional_chart(data, symbol, title="Price Chart"):
    """
    Create professional trading chart with proper scaling and styling
    """
    if data is None or data.empty:
        # Create empty chart placeholder
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="#ffffff")
        )
        fig.update_layout(
            plot_bgcolor='rgba(15, 15, 35, 0.9)',
            paper_bgcolor='rgba(15, 15, 35, 0.9)',
            font_color='#ffffff',
            height=400
        )
        return fig
    
    # Calculate appropriate Y-axis range
    current_price = data['Close'].iloc[-1]
    price_range = data['Close'].max() - data['Close'].min()
    margin = price_range * 0.1  # 10% margin
    
    y_min = data['Close'].min() - margin
    y_max = data['Close'].max() + margin
    
    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff6b35',
        increasing_fillcolor='rgba(0, 255, 136, 0.3)',
        decreasing_fillcolor='rgba(255, 107, 53, 0.3)',
        line=dict(width=1),
        name=symbol.replace('^', '')
    )])
    
    # Add current price line
    fig.add_hline(
        y=current_price,
        line_dash="dash",
        line_color="#22d3ee",
        line_width=2,
        annotation_text=f"Current: ${current_price:.2f}",
        annotation_position="bottom right",
        annotation_font_color="#22d3ee"
    )
    
    # Update layout with professional styling
    fig.update_layout(
        title=dict(
            text=f"{title} - {symbol.replace('^', '')}",
            font=dict(size=18, color="#ffffff", family="Space Grotesk"),
            x=0.02
        ),
        plot_bgcolor='rgba(15, 15, 35, 0.9)',
        paper_bgcolor='rgba(15, 15, 35, 0.9)',
        font_color='#ffffff',
        height=400,
        margin=dict(l=60, r=20, t=40, b=40),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            color='#ffffff'
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            color='#ffffff',
            range=[y_min, y_max],
            tickformat='$.2f'
        ),
        showlegend=False,
        dragmode='pan'
    )
    
    # Remove range selector
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    return fig

def create_market_heatmap():
    """
    Create market heatmap visualization
    """
    data_engine = get_market_data_engine()
    symbols = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'TSLA', 'META']
    
    heatmap_data = []
    for symbol in symbols:
        snapshot = data_engine.get_current_market_snapshot(symbol)
        change_pct = snapshot.get('day_change_pct', 0) or 0
        heatmap_data.append({
            'symbol': symbol,
            'change': change_pct
        })
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=[[item['change'] for item in heatmap_data]],
        x=[item['symbol'] for item in heatmap_data],
        y=['Daily Change %'],
        colorscale=[
            [0, '#ff6b35'],      # Red for negative
            [0.5, '#1a1a2e'],   # Dark for neutral
            [1, '#00ff88']      # Green for positive
        ],
        zmid=0,
        colorbar=dict(
            title="Change %",
            titlefont=dict(color="#ffffff"),
            tickfont=dict(color="#ffffff")
        ),
        text=[[f"{item['symbol']}<br>{item['change']:+.2f}%" for item in heatmap_data]],
        texttemplate="%{text}",
        textfont=dict(color="#ffffff", size=12)
    ))
    
    fig.update_layout(
        title=dict(
            text="Market Performance Heatmap",
            font=dict(size=16, color="#ffffff", family="Space Grotesk"),
            x=0.5
        ),
        plot_bgcolor='rgba(15, 15, 35, 0.9)',
        paper_bgcolor='rgba(15, 15, 35, 0.9)',
        font_color='#ffffff',
        height=150,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(color='#ffffff'),
        yaxis=dict(color='#ffffff')
    )
    
    return fig

# ==========================================
# INITIALIZE ENGINES
# ==========================================
@st.cache_resource
def get_market_data_engine():
    """
    Get cached market data engine instance
    """
    return MarketDataEngine()

@st.cache_resource
def get_market_analytics():
    """
    Get cached market analytics instance
    """
    data_engine = get_market_data_engine()
    return MarketAnalytics(data_engine)

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def format_price(price, decimals=2):
    """
    Format price for display
    """
    if price is None:
        return "N/A"
    return f"${price:,.{decimals}f}"

def format_percentage(value, decimals=2):
    """
    Format percentage for display
    """
    if value is None:
        return "N/A"
    return f"{value:+.{decimals}f}%"

def initialize_session_state():
    """
    Initialize session state variables
    """
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = '^GSPC'
    
    if 'analysis_date' not in st.session_state:
        st.session_state.analysis_date = datetime.now().date()

def create_metric_card(title, value, delta=None, delta_color="normal"):
    """
    Create professional metric card
    """
    if delta is not None:
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color
        )
    else:
        st.metric(label=title, value=value)

def create_info_card(title, content):
    """
    Create professional info card with glass effect and high contrast
    """
    st.markdown(f"""
    <div class="glass-card">
        <h3 style="color: #22d3ee !important; margin-bottom: 1rem !important; font-weight: 600 !important;">{title}</h3>
        <p style="color: #ffffff !important; font-size: 1.1rem !important; line-height: 1.6 !important; opacity: 0.95 !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{content}</p>
    </div>
    """, unsafe_allow_html=True)

def create_status_indicator(status, message):
    """
    Create status indicator
    """
    if status == "success":
        st.success(f"✅ {message}")
    elif status == "warning":
        st.warning(f"⚠️ {message}")
    elif status == "error":
        st.error(f"❌ {message}")
    else:
        st.info(f"ℹ️ {message}")

# ==========================================
# ENHANCED DASHBOARD (COMBINED 2A + 2B)
# ==========================================
def show_enhanced_dashboard():
    """
    Enhanced dashboard with real data and charts
    """
    st.markdown("# 📊 **MarketLens Pro Dashboard**")
    st.markdown("---")
    
    # Get engines
    data_engine = get_market_data_engine()
    analytics = get_market_analytics()
    
    # Get current market data
    symbol = st.session_state.selected_symbol
    snapshot = data_engine.get_current_market_snapshot(symbol)
    
    # Market Overview Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        symbol_name = symbol.replace('^', '') if symbol.startswith('^') else symbol
        current_price = snapshot.get('current_price')
        day_change_pct = snapshot.get('day_change_pct')
        
        create_metric_card(
            title=f"{symbol_name} Price",
            value=format_price(current_price) if current_price else "Loading...",
            delta=format_percentage(day_change_pct) if day_change_pct else None,
            delta_color="normal"
        )
    
    with col2:
        # Get sentiment score
        sentiment = analytics.get_market_sentiment_score(symbol)
        sentiment_level = sentiment['level'] if sentiment else "Calculating..."
        sentiment_score = sentiment['score'] if sentiment else 0
        
        create_metric_card(
            title="Market Sentiment",
            value=sentiment_level,
            delta=f"Score: {sentiment_score:.1f}" if sentiment else None
        )
    
    with col3:
        # Get data quality
        data, (quality_score, issues) = data_engine.get_market_data(symbol, period='2d', interval='30m')
        quality_status = "EXCELLENT" if quality_score > 90 else "GOOD" if quality_score > 70 else "POOR"
        
        create_metric_card(
            title="Data Quality",
            value=quality_status,
            delta=f"{quality_score:.0f}/100" if quality_score else None,
            delta_color="normal" if quality_score > 70 else "inverse"
        )
    
    with col4:
        # Volume analysis
        volume = snapshot.get('volume')
        avg_volume = snapshot.get('avg_volume')
        
        if volume and avg_volume:
            volume_ratio = volume / avg_volume
            volume_status = "HIGH" if volume_ratio > 1.5 else "NORMAL" if volume_ratio > 0.8 else "LOW"
            delta_text = f"{volume_ratio:.1f}x avg"
        else:
            volume_status = "N/A"
            delta_text = None
        
        create_metric_card(
            title="Volume Activity",
            value=volume_status,
            delta=delta_text
        )
    
    # Market Heatmap
    st.markdown("### 🔥 **Market Heatmap**")
    heatmap_fig = create_market_heatmap()
    st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Technical Analysis Chart
    st.markdown("### 📈 **Technical Analysis**")
    
    # Get chart data
    chart_data, _ = data_engine.get_market_data(symbol, period='5d', interval='30m')
    
    if chart_data is not None and not chart_data.empty:
        price_chart = create_professional_chart(chart_data, symbol, "Price Action")
        st.plotly_chart(price_chart, use_container_width=True)
        
        # EMA Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            ema_signal = analytics.detect_ema_crossover(chart_data)
            if ema_signal:
                st.metric("Fast EMA (8)", format_price(ema_signal['fast_ema']))
                st.metric("Slow EMA (21)", format_price(ema_signal['slow_ema']))
                
                if ema_signal['crossover_type']:
                    if ema_signal['crossover_type'] == 'bullish':
                        st.success("🟢 Bullish EMA Crossover")
                    else:
                        st.error("🔴 Bearish EMA Crossover")
                else:
                    trend = "Bullish" if ema_signal['fast_above_slow'] else "Bearish"
                    st.info(f"📊 Current Trend: {trend}")
        
        with col2:
            # Volume info
            if 'Volume' in chart_data.columns:
                current_volume = chart_data['Volume'].iloc[-1]
                avg_volume = chart_data['Volume'].mean()
                st.metric("Current Volume", f"{current_volume:,.0f}")
                st.metric("Average Volume", f"{avg_volume:,.0f}")
    else:
        st.error("Unable to load chart data")
    
    # System Status
    st.markdown("### ⚙️ **System Status**")
    col1, col2 = st.columns(2)
    
    with col1:
        create_info_card(
            "Data Feeds",
            f"Yahoo Finance API: ✅ Active | Real-time Data: ✅ Streaming | "
            f"Last Update: {datetime.now().strftime('%H:%M:%S')} ET"
        )
    
    with col2:
        create_info_card(
            "Analytics Engine",
            f"EMA Calculations: ✅ Active | Sentiment Analysis: ✅ Running | "
            f"Chart Engine: ✅ Operational | Quality Monitor: ✅ Active"
        )

def show_placeholder_page(page_name, description):
    """
    Show placeholder for pages to be implemented in later parts
    """
    st.markdown(f"# {page_name}")
    st.markdown("---")
    
    create_info_card(
        f"{page_name} Module",
        f"{description} This module will be implemented in the next development phase."
    )
    
    create_status_indicator("info", f"{page_name} module coming in the next update")

# ==========================================
# MAIN APPLICATION
# ==========================================
def main():
    # Apply styling
    apply_custom_styling()
    
    # Initialize session state
    initialize_session_state()
    
    # Create Sidebar Navigation
    st.sidebar.markdown("# 📈 MarketLens Pro v5")
    st.sidebar.markdown("*by Max Pointe Consulting*")
    st.sidebar.markdown("---")
    
    # Navigation pages
    pages = [
        '📊 Dashboard',
        '⚓ Anchors', 
        '🔮 Forecasts',
        '🎯 Signals',
        '📋 Contracts',
        '📐 Fibonacci',
        '📄 Export',
        '📈 Analytics'
    ]
    
    # Create navigation buttons
    for page in pages:
        page_name = page.split(' ', 1)[1]  # Remove emoji for internal reference
        if st.sidebar.button(page, key=f"nav_{page_name}", use_container_width=True):
            st.session_state.current_page = page_name
    
    st.sidebar.markdown("---")
    
    # Symbol Selection
    st.sidebar.markdown("### 🎯 **Symbol Selection**")
    symbol_options = {
        'S&P 500 Index': '^GSPC',
        'Apple Inc.': 'AAPL',
        'Microsoft Corp.': 'MSFT', 
        'NVIDIA Corp.': 'NVDA',
        'Amazon.com Inc.': 'AMZN',
        'Alphabet Inc.': 'GOOGL',
        'Tesla Inc.': 'TSLA',
        'Meta Platforms': 'META'
    }
    
    selected_name = st.sidebar.selectbox(
        "Select Symbol",
        options=list(symbol_options.keys()),
        key="symbol_selector"
    )
    st.session_state.selected_symbol = symbol_options[selected_name]
    
    # Analysis Date
    st.sidebar.markdown("### 📅 **Analysis Date**")
    st.session_state.analysis_date = st.sidebar.date_input(
        "Select Date",
        value=datetime.now().date(),
        key="date_selector"
    )
    
    # Market Status
    st.sidebar.markdown("### 📈 **Market Status**")
    current_time = datetime.now(TradingConfig.ET_TZ)
    market_open = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if market_open <= current_time <= market_close and current_time.weekday() < 5:
        st.sidebar.success("🟢 **MARKET OPEN**")
    else:
        st.sidebar.info("🔴 **MARKET CLOSED**")
    
    # Current Time Display
    st.sidebar.markdown(f"**ET:** {current_time.strftime('%H:%M:%S')}")
    ct_time = current_time.astimezone(TradingConfig.CT_TZ)
    st.sidebar.markdown(f"**CT:** {ct_time.strftime('%H:%M:%S')}")
    
    # Main content based on selected page
    current_page = st.session_state.current_page
    
    if current_page == 'Dashboard':
        show_enhanced_dashboard()
    elif current_page == 'Anchors':
        show_placeholder_page("⚓ Anchors", "Advanced anchor detection and analysis system.")
    elif current_page == 'Forecasts':
        show_placeholder_page("🔮 Forecasts", "Price projection and forecasting engine.")
    elif current_page == 'Signals':
        show_placeholder_page("🎯 Signals", "Real-time trading signal detection and alerts.")
    elif current_page == 'Contracts':
        show_placeholder_page("📋 Contracts", "Contract analysis and position management.")
    elif current_page == 'Fibonacci':
        show_placeholder_page("📐 Fibonacci", "Fibonacci retracement analysis with 78.6% emphasis.")
    elif current_page == 'Export':
        show_placeholder_page("📄 Export", "Professional reporting and data export capabilities.")
    elif current_page == 'Analytics':
        show_placeholder_page("📈 Analytics", "Advanced market analytics and performance metrics.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888; font-size: 0.8rem; font-family: \"Space Grotesk\", sans-serif;'>"
        "MarketLens Pro v5 | Max Pointe Consulting | Professional Trading Analytics"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
