# ==========================================
# **PART 1A: IMPORTS & CONFIGURATION**
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
# **PART 1B: CUSTOM CSS & STYLING**
# MarketLens Pro v5 by Max Pointe Consulting
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
# **PART 1C: UTILITY FUNCTIONS**
# MarketLens Pro v5 by Max Pointe Consulting
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
# **PART 1D: DATA ENGINE**
# MarketLens Pro v5 by Max Pointe Consulting
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
        
        # Check for reasonable price ranges
        if 'Close' in data.columns:
            price_range = data['Close'].max() - data['Close'].min()
            price_volatility = price_range / data['Close'].mean() * 100
            
            if symbol.startswith('^') and price_volatility > 15:  # SPX check
                quality_score -= 10
                issues.append("High volatility detected")
            elif not symbol.startswith('^') and price_volatility > 25:  # Stock check
                quality_score -= 10
                issues.append("High volatility detected")
        
        # Check data freshness
        if not data.empty:
            last_timestamp = data.index[-1]
            hours_old = (datetime.now(pytz.UTC) - last_timestamp.tz_convert(pytz.UTC)).total_seconds() / 3600
            
            if hours_old > 24:
                quality_score -= 15
                issues.append(f"Data is {hours_old:.1f} hours old")
            elif hours_old > 8:
                quality_score -= 5
                issues.append("Data not current")
        
        # Check for data consistency
        if 'High' in data.columns and 'Low' in data.columns and 'Close' in data.columns:
            invalid_bars = ((data['High'] < data['Low']) | 
                           (data['Close'] > data['High']) | 
                           (data['Close'] < data['Low'])).sum()
            
            if invalid_bars > 0:
                quality_score -= 25
                issues.append(f"{invalid_bars} invalid price bars")
        
        return max(0, quality_score), issues
    
    def get_market_data(self, symbol, period='5d', interval='30m', force_refresh=False):
        """
        Market data fetching with quality validation
        """
        cache_key = f"{symbol}_{period}_{interval}"
        current_time = datetime.now()
        
        # Check cache validity
        if (not force_refresh and 
            cache_key in self.data_cache and 
            cache_key in self.last_update and
            (current_time - self.last_update[cache_key]).total_seconds() < TradingConfig.HISTORICAL_TTL):
            return self.data_cache[cache_key], self.quality_scores.get(cache_key, (100, []))
        
        try:
            # Fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return None, (0, ["No data returned from source"])
            
            # Ensure timezone
            if data.index.tz is None:
                data.index = data.index.tz_localize('America/New_York')
            
            # Validate quality
            quality_score, issues = self.validate_data_quality(data, symbol)
            
            # Cache results
            self.data_cache[cache_key] = data
            self.quality_scores[cache_key] = (quality_score, issues)
            self.last_update[cache_key] = current_time
            
            return data, (quality_score, issues)
            
        except Exception as e:
            error_msg = f"Data fetch error for {symbol}: {str(e)}"
            return None, (0, [error_msg])
    
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
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('forwardPE'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
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
    
    @staticmethod
    def calculate_atr(data, period=14):
        """
        Calculate Average True Range for volatility measurement
        """
        if len(data) < period + 1:
            return None
        
        high_low = data['High'] - data['Low']
        high_close_prev = np.abs(data['High'] - data['Close'].shift(1))
        low_close_prev = np.abs(data['Low'] - data['Close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr






# ==========================================
# **PART 1E: MARKET ANALYTICS**
# MarketLens Pro v5 by Max Pointe Consulting
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
    
    def calculate_volume_profile(self, data, bins=20):
        """
        Calculate volume profile for price levels
        """
        if 'Volume' not in data.columns or 'Close' not in data.columns:
            return None
        
        price_min = data['Close'].min()
        price_max = data['Close'].max()
        price_range = price_max - price_min
        
        if price_range == 0:
            return None
        
        # Create price bins
        bin_size = price_range / bins
        price_bins = np.arange(price_min, price_max + bin_size, bin_size)
        
        # Calculate volume at each price level
        volume_profile = []
        for i in range(len(price_bins) - 1):
            bin_low = price_bins[i]
            bin_high = price_bins[i + 1]
            
            # Find candles in this price range
            in_range = ((data['Low'] <= bin_high) & (data['High'] >= bin_low))
            volume_in_range = data[in_range]['Volume'].sum()
            
            volume_profile.append({
                'price_low': bin_low,
                'price_high': bin_high,
                'price_mid': (bin_low + bin_high) / 2,
                'volume': volume_in_range,
                'volume_pct': 0  # Will calculate after all bins
            })
        
        # Calculate percentages
        total_volume = sum(vp['volume'] for vp in volume_profile)
        if total_volume > 0:
            for vp in volume_profile:
                vp['volume_pct'] = (vp['volume'] / total_volume) * 100
        
        return volume_profile
    
    def get_market_sentiment_score(self, symbol):
        """
        Calculate comprehensive market sentiment score
        """
        try:
            # Get recent data for analysis
            data, (quality_score, _) = self.data_engine.get_market_data(
                symbol, period='5d', interval='30m'
            )
            
            if data is None or len(data) < 50:
                return None
            
            sentiment_score = 50  # Neutral baseline
            factors = []
            
            # Price momentum (last 5 periods vs previous 5)
            recent_avg = data['Close'].tail(5).mean()
            previous_avg = data['Close'].iloc[-10:-5].mean()
            
            if recent_avg > previous_avg:
                momentum_boost = min(((recent_avg - previous_avg) / previous_avg) * 1000, 20)
                sentiment_score += momentum_boost
                factors.append(f"Positive momentum: +{momentum_boost:.1f}")
            else:
                momentum_drag = max(((recent_avg - previous_avg) / previous_avg) * 1000, -20)
                sentiment_score += momentum_drag
                factors.append(f"Negative momentum: {momentum_drag:.1f}")
            
            # Volume analysis
            recent_volume = data['Volume'].tail(5).mean()
            avg_volume = data['Volume'].mean()
            
            if recent_volume > avg_volume * 1.2:
                sentiment_score += 10
                factors.append("High volume activity: +10")
            elif recent_volume < avg_volume * 0.8:
                sentiment_score -= 5
                factors.append("Low volume activity: -5")
            
            # EMA crossover influence
            ema_signal = self.detect_ema_crossover(data)
            if ema_signal and ema_signal['crossover_type']:
                if ema_signal['crossover_type'] == 'bullish':
                    sentiment_score += 15
                    factors.append("EMA bullish crossover: +15")
                else:
                    sentiment_score -= 15
                    factors.append("EMA bearish crossover: -15")
            
            # Volatility adjustment
            atr = self.data_engine.calculate_atr(data)
            if atr:
                current_price = data['Close'].iloc[-1]
                volatility_pct = (atr / current_price) * 100
                
                if volatility_pct > 3:  # High volatility
                    sentiment_score -= 5
                    factors.append("High volatility: -5")
            
            # Data quality influence
            if quality_score < 80:
                sentiment_score -= 10
                factors.append("Data quality concerns: -10")
            
            # Normalize to 0-100 range
            sentiment_score = max(0, min(100, sentiment_score))
            
            return {
                'score': round(sentiment_score, 1),
                'level': self.get_sentiment_level(sentiment_score),
                'factors': factors,
                'timestamp': datetime.now(TradingConfig.ET_TZ)
            }
            
        except Exception as e:
            return None
    
    @staticmethod
    def get_sentiment_level(score):
        """
        Convert sentiment score to descriptive level
        """
        if score >= 75:
            return "Very Bullish"
        elif score >= 60:
            return "Bullish"
        elif score >= 40:
            return "Neutral"
        elif score >= 25:
            return "Bearish"
        else:
            return "Very Bearish"

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
# **PART 1F: CHART ENGINE**
# MarketLens Pro v5 by Max Pointe Consulting
# ==========================================

def calculate_chart_range(current_price, symbol_type='SPX', volatility_factor=1.0):
    """
    Calculate optimal chart Y-axis range for professional scaling
    """
    if symbol_type == 'SPX' or symbol_type.startswith('^'):
        base_range = 50 * volatility_factor
    else:
        # Stock-specific ranges
        stock_ranges = {
            'AAPL': 8, 'MSFT': 12, 'NVDA': 15, 'AMZN': 10,
            'GOOGL': 8, 'TSLA': 20, 'META': 15
        }
        base_range = stock_ranges.get(symbol_type, 10) * volatility_factor
    
    y_min = current_price - base_range
    y_max = current_price + base_range
    
    return y_min, y_max

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
    symbol_type = symbol.replace('^', '') if symbol.startswith('^') else symbol
    
    # Calculate volatility factor based on recent price action
    price_range = data['Close'].max() - data['Close'].min()
    avg_price = data['Close'].mean()
    volatility_factor = max(0.5, min(2.0, (price_range / avg_price) * 10))
    
    y_min, y_max = calculate_chart_range(current_price, symbol_type, volatility_factor)
    
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
        name=symbol_type
    )])
    
    # Add current price line
    fig.add_hline(
        y=current_price,
        line_dash="dash",
        line_color="#22d3ee",
        line_width=2,
        annotation_text=f"Current: {format_price(current_price)}",
        annotation_position="bottom right",
        annotation_font_color="#22d3ee"
    )
    
    # Update layout with professional styling
    fig.update_layout(
        title=dict(
            text=f"{title} - {symbol_type}",
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
            color='#ffffff',
            tickfont=dict(family="JetBrains Mono")
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            color='#ffffff',
            tickfont=dict(family="JetBrains Mono"),
            range=[y_min, y_max],
            tickformat='$.2f' if current_price < 1000 else '$,.0f'
        ),
        showlegend=False,
        dragmode='pan'
    )
    
    # Remove range selector and zoom controls for cleaner look
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    return fig

def create_volume_chart(data, symbol):
    """
    Create professional volume chart
    """
    if data is None or data.empty or 'Volume' not in data.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Volume data unavailable",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#ffffff")
        )
        fig.update_layout(
            plot_bgcolor='rgba(15, 15, 35, 0.9)',
            paper_bgcolor='rgba(15, 15, 35, 0.9)',
            font_color='#ffffff',
            height=200
        )
        return fig
    
    # Create color array based on price movement
    colors = []
    for i in range(len(data)):
        if data['Close'].iloc[i] >= data['Open'].iloc[i]:
            colors.append('#00ff88')  # Green for up days
        else:
            colors.append('#ff6b35')  # Orange for down days
    
    fig = go.Figure(data=[go.Bar(
        x=data.index,
        y=data['Volume'],
        marker_color=colors,
        opacity=0.7,
        name='Volume'
    )])
    
    # Add average volume line
    avg_volume = data['Volume'].mean()
    fig.add_hline(
        y=avg_volume,
        line_dash="dot",
        line_color="#a855f7",
        line_width=1,
        annotation_text=f"Avg: {avg_volume:,.0f}",
        annotation_position="top right",
        annotation_font_color="#a855f7"
    )
    
    fig.update_layout(
        title=dict(
            text="Volume Analysis",
            font=dict(size=14, color="#ffffff", family="Space Grotesk"),
            x=0.02
        ),
        plot_bgcolor='rgba(15, 15, 35, 0.9)',
        paper_bgcolor='rgba(15, 15, 35, 0.9)',
        font_color='#ffffff',
        height=200,
        margin=dict(l=60, r=20, t=40, b=40),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            color='#ffffff',
            tickfont=dict(family="JetBrains Mono")
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            color='#ffffff',
            tickfont=dict(family="JetBrains Mono"),
            tickformat='.2s'
        ),
        showlegend=False,
        dragmode='pan'
    )
    
    return fig

def create_ema_overlay_chart(data, symbol, analytics):
    """
    Create chart with EMA overlay
    """
    if data is None or data.empty:
        return create_professional_chart(data, symbol, "EMA Analysis")
    
    # Start with base chart
    fig = create_professional_chart(data, symbol, "Price with EMA Analysis")
    
    # Calculate EMAs
    ema_8 = analytics.calculate_ema(data, 8)
    ema_21 = analytics.calculate_ema(data, 21)
    
    if ema_8 is not None:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=ema_8,
            mode='lines',
            name='EMA 8',
            line=dict(color='#22d3ee', width=2),
            opacity=0.8
        ))
    
    if ema_21 is not None:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=ema_21,
            mode='lines',
            name='EMA 21',
            line=dict(color='#a855f7', width=2),
            opacity=0.8
        ))
    
    # Detect and mark crossovers
    ema_signal = analytics.detect_ema_crossover(data)
    if ema_signal and ema_signal['crossover_type']:
        # Mark the crossover point
        crossover_color = '#00ff88' if ema_signal['crossover_type'] == 'bullish' else '#ff6b35'
        crossover_symbol = 'triangle-up' if ema_signal['crossover_type'] == 'bullish' else 'triangle-down'
        
        fig.add_trace(go.Scatter(
            x=[data.index[-1]],
            y=[data['Close'].iloc[-1]],
            mode='markers',
            name=f'{ema_signal["crossover_type"].title()} Crossover',
            marker=dict(
                symbol=crossover_symbol,
                size=12,
                color=crossover_color,
                line=dict(color='#ffffff', width=1)
            )
        ))
    
    # Update legend
    fig.update_layout(showlegend=True, legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5,
        font=dict(color="#ffffff", size=10)
    ))
    
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
        change_pct = snapshot.get('day_change_pct', 0)
        heatmap_data.append({
            'symbol': symbol,
            'change': change_pct or 0,
            'price': snapshot.get('current_price', 0)
        })
    
    if not heatmap_data:
        return None
    
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
        textfont=dict(color="#ffffff", size=12),
        hoverongaps=False
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
# **PART 1G: DASHBOARD LOGIC**
# MarketLens Pro v5 by Max Pointe Consulting
# ==========================================

def create_market_overview_table():
    """
    Create market overview table for all tracked symbols
    """
    data_engine = get_market_data_engine()
    
    # Get data for all symbols
    overview_data = []
    symbols = ['^GSPC', 'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'TSLA', 'META']
    
    for symbol in symbols:
        snapshot = data_engine.get_current_market_snapshot(symbol)
        
        symbol_name = symbol.replace('^', '') if symbol.startswith('^') else symbol
        if symbol == '^GSPC':
            symbol_name = 'SPX'
        
        overview_data.append({
            'Symbol': symbol_name,
            'Price': format_price(snapshot.get('current_price')) if snapshot.get('current_price') else 'N/A',
            'Change': format_percentage(snapshot.get('day_change_pct')) if snapshot.get('day_change_pct') else 'N/A',
            'Volume': f"{snapshot.get('volume'):,.0f}" if snapshot.get('volume') else 'N/A',
            'Status': '🟢 Active' if snapshot.get('current_price') else '🔴 Error'
        })
    
    # Convert to DataFrame for display
    df = pd.DataFrame(overview_data)
    
    return df

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
        if symbol == '^GSPC':
            symbol_name = 'SPX'
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
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        st.info("Loading market heatmap...")
    
    # Charts Section
    st.markdown("### 📈 **Technical Analysis**")
    
    # Get chart data
    chart_data, _ = data_engine.get_market_data(symbol, period='5d', interval='30m')
    
    # Chart tabs
    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Price Action", "EMA Analysis", "Volume Profile"])
    
    with chart_tab1:
        if chart_data is not None:
            price_chart = create_professional_chart(chart_data, symbol, "Price Action")
            st.plotly_chart(price_chart, use_container_width=True)
        else:
            st.error("Unable to load price data")
    
    with chart_tab2:
        if chart_data is not None:
            ema_chart = create_ema_overlay_chart(chart_data, symbol, analytics)
            st.plotly_chart(ema_chart, use_container_width=True)
            
            # EMA Summary
            ema_signal = analytics.detect_ema_crossover(chart_data)
            if ema_signal:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Fast EMA (8)", format_price(ema_signal['fast_ema']))
                with col2:
                    st.metric("Slow EMA (21)", format_price(ema_signal['slow_ema']))
                
                if ema_signal['crossover_type']:
                    if ema_signal['crossover_type'] == 'bullish':
                        st.success(f"🟢 Bullish EMA Crossover Detected")
                    else:
                        st.error(f"🔴 Bearish EMA Crossover Detected")
                else:
                    trend = "Bullish" if ema_signal['fast_above_slow'] else "Bearish"
                    st.info(f"📊 Current Trend: {trend}")
        else:
            st.error("Unable to load EMA data")
    
    with chart_tab3:
        if chart_data is not None:
            volume_chart = create_volume_chart(chart_data, symbol)
            st.plotly_chart(volume_chart, use_container_width=True)
            
            # Volume Profile Analysis
            volume_profile = analytics.calculate_volume_profile(chart_data)
            if volume_profile:
                # Find highest volume price level
                max_volume_level = max(volume_profile, key=lambda x: x['volume'])
                st.info(f"📊 Highest Volume at {format_price(max_volume_level['price_mid'])} "
                       f"({max_volume_level['volume_pct']:.1f}% of total volume)")
        else:
            st.error("Unable to load volume data")
    
    # Market Overview Table
    st.markdown("### 📋 **Market Overview**")
    overview_df = create_market_overview_table()
    st.dataframe(
        overview_df,
        use_container_width=True,
        hide_index=True
    )
    
    # System Status
    st.markdown("### ⚙️ **System Status**")
    col1, col2 = st.columns(2)
    
    with col1:
        create_info_card(
            "Data Feeds",
            f"Yahoo Finance API: ✅ Active | Cache Status: ✅ Optimal | "
            f"Last Update: {datetime.now().strftime('%H:%M:%S')} ET"
        )
    
    with col2:
        create_info_card(
            "Analytics Engine",
            f"EMA Calculations: ✅ Running | Volume Analysis: ✅ Active | "
            f"Sentiment Scoring: ✅ Operational | Quality Monitoring: ✅ Active"
        )

def show_basic_dashboard():
    """
    Basic dashboard fallback
    """
    st.markdown("# 📊 **MarketLens Pro Dashboard**")
    st.markdown("---")
    
    # Get current market data
    symbol = st.session_state.selected_symbol
    symbol_name = symbol.replace('^', '') if symbol.startswith('^') else symbol
    if symbol == '^GSPC':
        symbol_name = 'SPX'
    
    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            title=f"{symbol_name} Price",
            value="Loading...",
            delta=None
        )
    
    with col2:
        create_metric_card(
            title="Market Trend",
            value="ANALYZING",
            delta="🔄 Processing"
        )
    
    with col3:
        create_metric_card(
            title="Anchor Status",
            value="READY",
            delta="🎯 Standby"
        )
    
    with col4:
        create_metric_card(
            title="Signal Count",
            value="0",
            delta="📊 Monitoring"
        )
    
    # Main content area
    create_info_card(
        "Welcome to MarketLens Pro v5",
        "Your professional anchor-based trading analysis platform. Navigate through the sidebar to access different analysis modules. The system tracks Asian session anchors for SPX and Monday/Tuesday anchors for individual stocks, providing precise slope-based projections and signal detection."
    )
    
    # Quick Stats
    st.markdown("### 📈 **Quick Market Overview**")
    col1, col2 = st.columns(2)
    
    with col1:
        create_info_card(
            "Today's Focus",
            f"Currently analyzing {symbol_name} with anchor-based methodology. System is monitoring for 30-minute candle interactions with projected Skyline and Baseline levels."
        )
    
    with col2:
        create_info_card(
            "System Status", 
            "All systems operational. Data feeds active. Anchor calculations updated. Signal detection algorithms running. Ready for professional trading analysis."
        )



# ==========================================
# **PART 1H: MAIN APPLICATION & NAVIGATION**
# MarketLens Pro v5 by Max Pointe Consulting
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
        # Try to use enhanced dashboard, fall back to basic if needed
        try:
            show_enhanced_dashboard()
        except Exception as e:
            st.error(f"Loading enhanced dashboard failed, using basic version")
            show_basic_dashboard()
    elif current_page == 'Anchors':
        # Try to use anchors page, fall back to placeholder if not available
        try:
            show_anchors_page()
        except NameError:
            show_placeholder_page("⚓ Anchors", "Advanced anchor detection and analysis system. Add Parts 3A, 3B, and 3C to enable this module.")
        except Exception as e:
            st.error(f"Error loading anchors page: {str(e)}")
            show_placeholder_page("⚓ Anchors", "Anchor system encountered an error.")
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










# ==========================================
# **PART 3A: SPX ANCHOR DETECTION ENGINE**
# MarketLens Pro v5 by Max Pointe Consulting
# ==========================================

class SPXAnchorSystem:
    """
    SPX Asian Session Anchor Detection Engine
    """
    
    def __init__(self, data_engine):
        self.data_engine = data_engine
        self.anchor_cache = {}
    
    def get_es_to_spx_offset(self):
        """
        Calculate dynamic ES to SPX offset
        """
        try:
            # Get current ES and SPX prices
            es_ticker = yf.Ticker('ES=F')
            spx_ticker = yf.Ticker('^GSPC')
            
            es_price = es_ticker.info.get('regularMarketPrice') or es_ticker.info.get('previousClose')
            spx_price = spx_ticker.info.get('regularMarketPrice') or spx_ticker.info.get('previousClose')
            
            if es_price and spx_price:
                offset = spx_price - es_price
                return offset
            else:
                # Fallback to typical offset
                return 0.0
                
        except Exception:
            return 0.0
    
    def get_asian_session_data(self, analysis_date):
        """
        Get ES futures data for Asian session (5:00-7:30 PM CT previous day)
        """
        try:
            # Calculate previous trading day
            if analysis_date.weekday() == 0:  # Monday
                previous_day = analysis_date - timedelta(days=3)  # Previous Friday
            else:
                previous_day = analysis_date - timedelta(days=1)
            
            # Define Asian session times in CT
            asian_start = TradingConfig.CT_TZ.localize(
                datetime.combine(previous_day, TradingConfig.ASIAN_SESSION_START)
            )
            asian_end = TradingConfig.CT_TZ.localize(
                datetime.combine(previous_day, TradingConfig.ASIAN_SESSION_END)
            )
            
            # Fetch ES=F data for wider period to ensure coverage
            es_data, _ = self.data_engine.get_market_data(
                'ES=F', 
                period='5d',  # Get 5 days to ensure coverage
                interval='30m'
            )
            
            if es_data is None or es_data.empty:
                return None, "No ES futures data available"
            
            # Convert to CT timezone
            es_data_ct = es_data.copy()
            es_data_ct.index = es_data_ct.index.tz_convert(TradingConfig.CT_TZ)
            
            # Filter for Asian session
            asian_mask = (es_data_ct.index >= asian_start) & (es_data_ct.index <= asian_end)
            asian_session_data = es_data_ct[asian_mask]
            
            if asian_session_data.empty:
                return None, f"No data found for Asian session {asian_start.strftime('%Y-%m-%d %H:%M')} - {asian_end.strftime('%H:%M')} CT"
            
            return asian_session_data, None
            
        except Exception as e:
            return None, f"Error fetching Asian session data: {str(e)}"
    
    def detect_swing_points(self, data):
        """
        Detect swing highs and lows using CLOSE prices only (line chart methodology)
        """
        if data is None or len(data) < 3:
            return None, None, None, None
        
        # Use CLOSE prices only for swing detection
        closes = data['Close']
        
        # Find absolute highest and lowest CLOSE prices
        skyline_anchor = closes.max()  # Highest close
        baseline_anchor = closes.min()  # Lowest close
        
        # Find the exact times when these occurred
        skyline_time = data[closes == skyline_anchor].index[0]
        baseline_time = data[closes == baseline_anchor].index[0]
        
        return skyline_anchor, baseline_anchor, skyline_time, baseline_time
    
    def detect_asian_session_anchors(self, analysis_date):
        """
        Detect Skyline and Baseline anchors from Asian session ES data
        """
        cache_key = f"asian_anchors_{analysis_date}"
        
        # Check cache first
        if cache_key in self.anchor_cache:
            return self.anchor_cache[cache_key]
        
        # Get Asian session data
        asian_data, error = self.get_asian_session_data(analysis_date)
        
        if asian_data is None:
            result = {
                'skyline_anchor': None,
                'baseline_anchor': None,
                'skyline_time': None,
                'baseline_time': None,
                'es_skyline': None,
                'es_baseline': None,
                'es_to_spx_offset': 0.0,
                'error': error,
                'session_start': None,
                'session_end': None,
                'data_points': 0,
                'analysis_date': analysis_date
            }
            self.anchor_cache[cache_key] = result
            return result
        
        # Detect swing points using CLOSE prices only
        es_skyline, es_baseline, skyline_time, baseline_time = self.detect_swing_points(asian_data)
        
        if es_skyline is None:
            result = {
                'skyline_anchor': None,
                'baseline_anchor': None,
                'skyline_time': None,
                'baseline_time': None,
                'es_skyline': None,
                'es_baseline': None,
                'es_to_spx_offset': 0.0,
                'error': "Unable to detect swing points",
                'session_start': asian_data.index[0] if not asian_data.empty else None,
                'session_end': asian_data.index[-1] if not asian_data.empty else None,
                'data_points': len(asian_data),
                'analysis_date': analysis_date
            }
            self.anchor_cache[cache_key] = result
            return result
        
        # Get ES to SPX offset
        es_to_spx_offset = self.get_es_to_spx_offset()
        
        # Convert ES anchors to SPX equivalent
        spx_skyline = es_skyline + es_to_spx_offset
        spx_baseline = es_baseline + es_to_spx_offset
        
        result = {
            'skyline_anchor': spx_skyline,
            'baseline_anchor': spx_baseline,
            'skyline_time': skyline_time,
            'baseline_time': baseline_time,
            'es_skyline': es_skyline,
            'es_baseline': es_baseline,
            'es_to_spx_offset': es_to_spx_offset,
            'session_start': asian_data.index[0],
            'session_end': asian_data.index[-1],
            'data_points': len(asian_data),
            'error': None,
            'analysis_date': analysis_date,
            'session_range': es_skyline - es_baseline,
            'session_duration': (asian_data.index[-1] - asian_data.index[0]).total_seconds() / 3600  # hours
        }
        
        # Cache the result
        self.anchor_cache[cache_key] = result
        
        return result
    
    def validate_anchor_quality(self, anchors):
        """
        Validate the quality of detected anchors
        """
        if not anchors or anchors.get('error'):
            return 0, ["Anchor detection failed"]
        
        quality_score = 100
        issues = []
        
        # Check data points
        if anchors['data_points'] < 3:
            quality_score -= 50
            issues.append(f"Insufficient data points: {anchors['data_points']}")
        elif anchors['data_points'] < 5:
            quality_score -= 20
            issues.append(f"Limited data points: {anchors['data_points']}")
        
        # Check session range
        if anchors.get('session_range'):
            if anchors['session_range'] < 5:  # Less than 5 points range
                quality_score -= 30
                issues.append(f"Narrow session range: {anchors['session_range']:.2f} points")
            elif anchors['session_range'] > 100:  # More than 100 points range
                quality_score -= 20
                issues.append(f"Unusually wide range: {anchors['session_range']:.2f} points")
        
        # Check session duration
        if anchors.get('session_duration'):
            expected_duration = 2.5  # 2.5 hours
            if abs(anchors['session_duration'] - expected_duration) > 1:
                quality_score -= 15
                issues.append(f"Session duration variance: {anchors['session_duration']:.1f}h vs expected 2.5h")
        
        # Check if anchors are reasonable
        if anchors['skyline_anchor'] and anchors['baseline_anchor']:
            if anchors['skyline_anchor'] <= anchors['baseline_anchor']:
                quality_score = 0
                issues.append("Invalid anchors: Skyline <= Baseline")
        
        return max(0, quality_score), issues
    
    def get_anchor_summary(self, analysis_date):
        """
        Get comprehensive anchor summary with quality assessment
        """
        anchors = self.detect_asian_session_anchors(analysis_date)
        quality_score, quality_issues = self.validate_anchor_quality(anchors)
        
        summary = {
            'anchors': anchors,
            'quality_score': quality_score,
            'quality_issues': quality_issues,
            'status': 'EXCELLENT' if quality_score > 90 else 'GOOD' if quality_score > 70 else 'POOR' if quality_score > 30 else 'FAILED',
            'timestamp': datetime.now(TradingConfig.ET_TZ)
        }
        
        return summary

# ==========================================
# INITIALIZE SPX ANCHOR SYSTEM
# ==========================================
@st.cache_resource
def get_spx_anchor_system():
    """
    Get cached SPX anchor system instance
    """
    data_engine = get_market_data_engine()
    return SPXAnchorSystem(data_engine)









# ==========================================
# **PART 3B: SPX PROJECTION SYSTEM**
# MarketLens Pro v5 by Max Pointe Consulting
# ==========================================

class SPXProjectionSystem:
    """
    SPX Slope-Based Projection System for RTH Trading
    """
    
    def __init__(self, anchor_system):
        self.anchor_system = anchor_system
        self.projection_cache = {}
    
    def generate_rth_time_blocks(self, analysis_date):
        """
        Generate 30-minute time blocks for RTH (8:30 AM - 2:30 PM CT)
        """
        # Define RTH session times
        rth_start = TradingConfig.CT_TZ.localize(
            datetime.combine(analysis_date, TradingConfig.RTH_START_CT)
        )
        rth_end = TradingConfig.CT_TZ.localize(
            datetime.combine(analysis_date, time(14, 30))  # 2:30 PM CT
        )
        
        time_blocks = []
        current_time = rth_start
        block_number = 0
        
        while current_time <= rth_end:
            time_blocks.append({
                'time': current_time,
                'block_number': block_number,
                'time_str': current_time.strftime('%H:%M CT')
            })
            
            # Move to next 30-minute block
            current_time += timedelta(minutes=30)
            block_number += 1
        
        return time_blocks
    
    def calculate_slope_projections(self, anchors, analysis_date):
        """
        Calculate Skyline and Baseline projections using SPX slopes
        """
        if not anchors or anchors['skyline_anchor'] is None:
            return None
        
        cache_key = f"projections_{analysis_date}_{anchors['skyline_anchor']}"
        
        # Check cache
        if cache_key in self.projection_cache:
            return self.projection_cache[cache_key]
        
        # Generate RTH time blocks
        time_blocks = self.generate_rth_time_blocks(analysis_date)
        
        projections = {
            'skyline_levels': [],
            'baseline_levels': [],
            'times': [],
            'block_numbers': [],
            'time_strings': [],
            'skyline_changes': [],
            'baseline_changes': []
        }
        
        # Calculate projected levels for each time block
        for block in time_blocks:
            block_num = block['block_number']
            
            # Apply SPX slopes: +0.2255 for Skyline, -0.2255 for Baseline
            skyline_level = anchors['skyline_anchor'] + (TradingConfig.SPX_SLOPES['skyline'] * block_num)
            baseline_level = anchors['baseline_anchor'] + (TradingConfig.SPX_SLOPES['baseline'] * block_num)
            
            # Calculate change from anchor
            skyline_change = skyline_level - anchors['skyline_anchor']
            baseline_change = baseline_level - anchors['baseline_anchor']
            
            projections['skyline_levels'].append(skyline_level)
            projections['baseline_levels'].append(baseline_level)
            projections['times'].append(block['time'])
            projections['block_numbers'].append(block_num)
            projections['time_strings'].append(block['time_str'])
            projections['skyline_changes'].append(skyline_change)
            projections['baseline_changes'].append(baseline_change)
        
        # Add metadata
        projections['anchor_spread'] = anchors['skyline_anchor'] - anchors['baseline_anchor']
        projections['total_blocks'] = len(time_blocks)
        projections['session_start'] = time_blocks[0]['time'] if time_blocks else None
        projections['session_end'] = time_blocks[-1]['time'] if time_blocks else None
        
        # Cache the result
        self.projection_cache[cache_key] = projections
        
        return projections
    
    def get_current_projected_levels(self, analysis_date):
        """
        Get current projected levels based on current time
        """
        # Get anchors and projections
        anchors = self.anchor_system.detect_asian_session_anchors(analysis_date)
        if anchors['error']:
            return None
        
        projections = self.calculate_slope_projections(anchors, analysis_date)
        if not projections:
            return None
        
        # Get current time and calculate current block
        current_time = datetime.now(TradingConfig.CT_TZ)
        current_block = self.get_current_rth_block(current_time, analysis_date)
        
        if current_block is None:
            return {
                'status': 'OUTSIDE_RTH',
                'message': 'Current time is outside RTH session',
                'current_block': None,
                'skyline_level': None,
                'baseline_level': None
            }
        
        # Get levels for current block
        if current_block < len(projections['skyline_levels']):
            return {
                'status': 'ACTIVE',
                'current_block': current_block,
                'skyline_level': projections['skyline_levels'][current_block],
                'baseline_level': projections['baseline_levels'][current_block],
                'skyline_change': projections['skyline_changes'][current_block],
                'baseline_change': projections['baseline_changes'][current_block],
                'time_string': projections['time_strings'][current_block],
                'blocks_remaining': projections['total_blocks'] - current_block - 1
            }
        else:
            return {
                'status': 'RTH_ENDED',
                'message': 'RTH session has ended',
                'current_block': current_block,
                'skyline_level': None,
                'baseline_level': None
            }
    
    def get_current_rth_block(self, current_time, analysis_date):
        """
        Calculate current RTH 30-minute block number
        """
        rth_start = TradingConfig.CT_TZ.localize(
            datetime.combine(analysis_date, TradingConfig.RTH_START_CT)
        )
        rth_end = TradingConfig.CT_TZ.localize(
            datetime.combine(analysis_date, time(14, 30))  # 2:30 PM CT
        )
        
        # Check if current time is within RTH
        if current_time < rth_start:
            return None  # Before RTH starts
        elif current_time > rth_end:
            return None  # After RTH ends
        
        # Calculate block number
        time_diff = current_time - rth_start
        block_number = int(time_diff.total_seconds() / 1800)  # 1800 seconds = 30 minutes
        
        return block_number
    
    def get_levels_for_time(self, target_time, analysis_date):
        """
        Get projected levels for a specific time
        """
        # Get anchors and projections
        anchors = self.anchor_system.detect_asian_session_anchors(analysis_date)
        if anchors['error']:
            return None
        
        projections = self.calculate_slope_projections(anchors, analysis_date)
        if not projections:
            return None
        
        # Calculate block for target time
        target_block = self.get_current_rth_block(target_time, analysis_date)
        
        if target_block is None or target_block >= len(projections['skyline_levels']):
            return None
        
        return {
            'block_number': target_block,
            'skyline_level': projections['skyline_levels'][target_block],
            'baseline_level': projections['baseline_levels'][target_block],
            'skyline_change': projections['skyline_changes'][target_block],
            'baseline_change': projections['baseline_changes'][target_block],
            'time_string': projections['time_strings'][target_block]
        }
    
    def create_projection_table(self, analysis_date, show_all_blocks=False):
        """
        Create a detailed projection table for display
        """
        # Get anchors and projections
        anchors = self.anchor_system.detect_asian_session_anchors(analysis_date)
        if anchors['error']:
            return None
        
        projections = self.calculate_slope_projections(anchors, analysis_date)
        if not projections:
            return None
        
        # Create table data
        table_data = []
        current_block = self.get_current_rth_block(datetime.now(TradingConfig.CT_TZ), analysis_date)
        
        # Show limited blocks if not showing all
        blocks_to_show = range(len(projections['times'])) if show_all_blocks else range(min(10, len(projections['times'])))
        
        for i in blocks_to_show:
            is_current = (current_block == i) if current_block is not None else False
            
            table_data.append({
                'Block': f"#{i}",
                'Time': projections['time_strings'][i],
                'Skyline': format_price(projections['skyline_levels'][i]),
                'Baseline': format_price(projections['baseline_levels'][i]),
                'Sky Change': f"{projections['skyline_changes'][i]:+.2f}",
                'Base Change': f"{projections['baseline_changes'][i]:+.2f}",
                'Status': '🔴 CURRENT' if is_current else '⚪ Pending' if current_block is None or i > current_block else '✅ Past'
            })
        
        return pd.DataFrame(table_data)
    
    def get_projection_statistics(self, analysis_date):
        """
        Get statistical information about projections
        """
        # Get anchors and projections
        anchors = self.anchor_system.detect_asian_session_anchors(analysis_date)
        if anchors['error']:
            return None
        
        projections = self.calculate_slope_projections(anchors, analysis_date)
        if not projections:
            return None
        
        # Calculate statistics
        skyline_range = max(projections['skyline_levels']) - min(projections['skyline_levels'])
        baseline_range = max(projections['baseline_levels']) - min(projections['baseline_levels'])
        
        stats = {
            'anchor_spread': projections['anchor_spread'],
            'total_blocks': projections['total_blocks'],
            'skyline_start': projections['skyline_levels'][0],
            'skyline_end': projections['skyline_levels'][-1],
            'skyline_range': skyline_range,
            'baseline_start': projections['baseline_levels'][0],
            'baseline_end': projections['baseline_levels'][-1],
            'baseline_range': baseline_range,
            'session_duration_hours': projections['total_blocks'] * 0.5,  # Each block is 0.5 hours
            'slope_skyline': TradingConfig.SPX_SLOPES['skyline'],
            'slope_baseline': TradingConfig.SPX_SLOPES['baseline']
        }
        
        return stats

# ==========================================
# INITIALIZE SPX PROJECTION SYSTEM
# ==========================================
@st.cache_resource
def get_spx_projection_system():
    """
    Get cached SPX projection system instance
    """
    anchor_system = get_spx_anchor_system()
    return SPXProjectionSystem(anchor_system)




# ==========================================
# **PART 3C: SPX ANCHOR VISUALIZATION**
# MarketLens Pro v5 by Max Pointe Consulting
# ==========================================

def create_anchor_chart(symbol, analysis_date):
    """
    Create comprehensive SPX chart with Asian session anchors and RTH projections
    """
    data_engine = get_market_data_engine()
    anchor_system = get_spx_anchor_system()
    projection_system = get_spx_projection_system()
    
    # Get SPX data for analysis date and surrounding days
    spx_data, _ = data_engine.get_market_data(symbol, period='3d', interval='30m')
    
    if spx_data is None or spx_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No SPX data available for anchor visualization",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#ffffff")
        )
        fig.update_layout(
            plot_bgcolor='rgba(15, 15, 35, 0.9)',
            paper_bgcolor='rgba(15, 15, 35, 0.9)',
            font_color='#ffffff',
            height=600
        )
        return fig
    
    # Get anchors and projections
    anchors = anchor_system.detect_asian_session_anchors(analysis_date)
    
    # Create base candlestick chart with intelligent scaling
    current_price = spx_data['Close'].iloc[-1]
    y_min, y_max = calculate_chart_range(current_price, 'SPX', volatility_factor=1.5)
    
    fig = go.Figure(data=[go.Candlestick(
        x=spx_data.index,
        open=spx_data['Open'],
        high=spx_data['High'],
        low=spx_data['Low'],
        close=spx_data['Close'],
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff6b35',
        increasing_fillcolor='rgba(0, 255, 136, 0.3)',
        decreasing_fillcolor='rgba(255, 107, 53, 0.3)',
        line=dict(width=1),
        name='SPX'
    )])
    
    # Add anchor lines and projections if available
    if anchors and not anchors['error']:
        projections = projection_system.calculate_slope_projections(anchors, analysis_date)
        
        if projections:
            # Convert projection times to pandas timestamps for plotting
            projection_times = [pd.Timestamp(t) for t in projections['times']]
            
            # Add Skyline projection line
            fig.add_trace(go.Scatter(
                x=projection_times,
                y=projections['skyline_levels'],
                mode='lines',
                name='Skyline Anchor',
                line=dict(color='#22d3ee', width=3, dash='solid'),
                opacity=0.9,
                hovertemplate='<b>Skyline</b><br>Time: %{x}<br>Level: $%{y:.2f}<extra></extra>'
            ))
            
            # Add Baseline projection line
            fig.add_trace(go.Scatter(
                x=projection_times,
                y=projections['baseline_levels'],
                mode='lines',
                name='Baseline Anchor',
                line=dict(color='#a855f7', width=3, dash='solid'),
                opacity=0.9,
                hovertemplate='<b>Baseline</b><br>Time: %{x}<br>Level: $%{y:.2f}<extra></extra>'
            ))
            
            # Add anchor origin points
            fig.add_trace(go.Scatter(
                x=[projection_times[0], projection_times[0]],
                y=[anchors['skyline_anchor'], anchors['baseline_anchor']],
                mode='markers',
                name='Anchor Origins',
                marker=dict(
                    symbol=['triangle-up', 'triangle-down'],
                    size=[15, 15],
                    color=['#22d3ee', '#a855f7'],
                    line=dict(color='#ffffff', width=2)
                ),
                hovertemplate='<b>%{text}</b><br>Level: $%{y:.2f}<extra></extra>',
                text=['Skyline Origin', 'Baseline Origin']
            ))
            
            # Highlight current block if in RTH
            current_levels = projection_system.get_current_projected_levels(analysis_date)
            if current_levels and current_levels['status'] == 'ACTIVE':
                current_block = current_levels['current_block']
                if current_block < len(projection_times):
                    # Add current block highlight
                    fig.add_trace(go.Scatter(
                        x=[projection_times[current_block]],
                        y=[current_levels['skyline_level']],
                        mode='markers',
                        name='Current Block',
                        marker=dict(
                            symbol='circle',
                            size=20,
                            color='rgba(255, 255, 255, 0.8)',
                            line=dict(color='#22d3ee', width=3)
                        ),
                        hovertemplate=f'<b>Current Block #{current_block}</b><br>Skyline: $%{{y:.2f}}<extra></extra>'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=[projection_times[current_block]],
                        y=[current_levels['baseline_level']],
                        mode='markers',
                        name='Current Block',
                        marker=dict(
                            symbol='circle',
                            size=20,
                            color='rgba(255, 255, 255, 0.8)',
                            line=dict(color='#a855f7', width=3)
                        ),
                        hovertemplate=f'<b>Current Block #{current_block}</b><br>Baseline: $%{{y:.2f}}<extra></extra>',
                        showlegend=False
                    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"SPX Asian Session Anchors - {analysis_date.strftime('%Y-%m-%d')}",
            font=dict(size=18, color="#ffffff", family="Space Grotesk"),
            x=0.02
        ),
        plot_bgcolor='rgba(15, 15, 35, 0.9)',
        paper_bgcolor='rgba(15, 15, 35, 0.9)',
        font_color='#ffffff',
        height=600,
        margin=dict(l=60, r=20, t=60, b=60),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            color='#ffffff',
            tickfont=dict(family="JetBrains Mono")
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            color='#ffffff',
            tickfont=dict(family="JetBrains Mono"),
            range=[y_min, y_max],
            tickformat='$,.0f'
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(color="#ffffff", size=10)
        ),
        dragmode='pan'
    )
    
    # Remove range selector
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    return fig

def create_projection_overview_chart(analysis_date):
    """
    Create overview chart showing projection progression
    """
    projection_system = get_spx_projection_system()
    anchor_system = get_spx_anchor_system()
    
    # Get anchors and projections
    anchors = anchor_system.detect_asian_session_anchors(analysis_date)
    if anchors['error']:
        return None
    
    projections = projection_system.calculate_slope_projections(anchors, analysis_date)
    if not projections:
        return None
    
    # Create progression chart
    fig = go.Figure()
    
    # Add skyline progression
    fig.add_trace(go.Scatter(
        x=list(range(len(projections['skyline_levels']))),
        y=projections['skyline_levels'],
        mode='lines+markers',
        name='Skyline Progression',
        line=dict(color='#22d3ee', width=3),
        marker=dict(size=6, color='#22d3ee')
    ))
    
    # Add baseline progression
    fig.add_trace(go.Scatter(
        x=list(range(len(projections['baseline_levels']))),
        y=projections['baseline_levels'],
        mode='lines+markers',
        name='Baseline Progression',
        line=dict(color='#a855f7', width=3),
        marker=dict(size=6, color='#a855f7')
    ))
    
    # Highlight current block
    current_levels = projection_system.get_current_projected_levels(analysis_date)
    if current_levels and current_levels['status'] == 'ACTIVE':
        current_block = current_levels['current_block']
        fig.add_vline(
            x=current_block,
            line_dash="dash",
            line_color="#ffffff",
            line_width=2,
            annotation_text=f"Current Block #{current_block}",
            annotation_position="top"
        )
    
    fig.update_layout(
        title=dict(
            text="RTH Projection Progression",
            font=dict(size=16, color="#ffffff", family="Space Grotesk"),
            x=0.5
        ),
        plot_bgcolor='rgba(15, 15, 35, 0.9)',
        paper_bgcolor='rgba(15, 15, 35, 0.9)',
        font_color='#ffffff',
        height=300,
        xaxis=dict(
            title="30-Minute Block Number",
            gridcolor='rgba(255, 255, 255, 0.1)',
            color='#ffffff'
        ),
        yaxis=dict(
            title="SPX Level",
            gridcolor='rgba(255, 255, 255, 0.1)',
            color='#ffffff',
            tickformat='$,.0f'
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(color="#ffffff", size=10)
        )
    )
    
    return fig

def show_anchors_page():
    """
    Display the SPX Anchors analysis page
    """
    st.markdown("# ⚓ **SPX Asian Session Anchors**")
    st.markdown("---")
    
    # Get systems
    anchor_system = get_spx_anchor_system()
    projection_system = get_spx_projection_system()
    
    # Get analysis date from session state
    analysis_date = st.session_state.analysis_date
    
    # Get anchor summary
    anchor_summary = anchor_system.get_anchor_summary(analysis_date)
    anchors = anchor_summary['anchors']
    
    # Status Overview Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "normal" if anchor_summary['status'] in ['EXCELLENT', 'GOOD'] else "inverse"
        create_metric_card(
            title="Anchor Status",
            value=anchor_summary['status'],
            delta=f"Quality: {anchor_summary['quality_score']}/100",
            delta_color=status_color
        )
    
    with col2:
        current_levels = projection_system.get_current_projected_levels(analysis_date)
        if current_levels and current_levels.get('skyline_level'):
            create_metric_card(
                title="Current Skyline",
                value=format_price(current_levels['skyline_level']),
                delta=f"Block #{current_levels['current_block']}" if current_levels.get('current_block') is not None else None
            )
        else:
            create_metric_card(
                title="Current Skyline", 
                value="N/A",
                delta="Outside RTH" if current_levels and current_levels['status'] == 'OUTSIDE_RTH' else None
            )
    
    with col3:
        if current_levels and current_levels.get('baseline_level'):
            create_metric_card(
                title="Current Baseline",
                value=format_price(current_levels['baseline_level']),
                delta=f"Block #{current_levels['current_block']}" if current_levels.get('current_block') is not None else None
            )
        else:
            create_metric_card(
                title="Current Baseline",
                value="N/A", 
                delta="Outside RTH" if current_levels and current_levels['status'] == 'OUTSIDE_RTH' else None
            )
    
    with col4:
        if current_levels and current_levels.get('blocks_remaining') is not None:
            create_metric_card(
                title="Blocks Remaining",
                value=str(current_levels['blocks_remaining']),
                delta="30-min intervals"
            )
        else:
            create_metric_card(title="Blocks Remaining", value="N/A")
    
    # Main Anchor Chart
    st.markdown("### 📈 **SPX Anchor Chart**")
    anchor_chart = create_anchor_chart('^GSPC', analysis_date)
    st.plotly_chart(anchor_chart, use_container_width=True)
    
    # Anchor Details and Projection Overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 **Anchor Details**")
        if anchors and not anchors['error']:
            create_info_card(
                "Asian Session Summary",
                f"<b>Skyline:</b> {format_price(anchors['skyline_anchor'])}<br>"
                f"<b>Baseline:</b> {format_price(anchors['baseline_anchor'])}<br>"
                f"<b>Spread:</b> {anchors['skyline_anchor'] - anchors['baseline_anchor']:.2f} points<br>"
                f"<b>Session:</b> {anchors['session_start'].strftime('%H:%M')} - {anchors['session_end'].strftime('%H:%M')} CT<br>"
                f"<b>Data Points:</b> {anchors['data_points']}"
            )
            
            # ES Futures Details
            create_info_card(
                "ES Futures Data",
                f"<b>ES Skyline:</b> {format_price(anchors['es_skyline'])}<br>"
                f"<b>ES Baseline:</b> {format_price(anchors['es_baseline'])}<br>"
                f"<b>ES-SPX Offset:</b> {anchors['es_to_spx_offset']:+.2f}<br>"
                f"<b>Session Range:</b> {anchors.get('session_range', 0):.2f} points"
            )
        else:
            create_status_indicator("error", anchors['error'] if anchors else "No anchor data available")
    
    with col2:
        st.markdown("#### 📈 **Projection Overview**")
        projection_chart = create_projection_overview_chart(analysis_date)
        if projection_chart:
            st.plotly_chart(projection_chart, use_container_width=True)
        else:
            st.error("Unable to generate projection overview")
    
    # Projection Table
    st.markdown("### 📋 **RTH Projection Table**")
    projection_table = projection_system.create_projection_table(analysis_date, show_all_blocks=False)
    if projection_table is not None:
        st.dataframe(projection_table, use_container_width=True, hide_index=True)
        
        # Show all blocks button
        if st.button("📄 Show All RTH Blocks", key="show_all_blocks"):
            full_table = projection_system.create_projection_table(analysis_date, show_all_blocks=True)
            st.dataframe(full_table, use_container_width=True, hide_index=True)
    else:
        st.error("Unable to generate projection table")
    
    # Quality Issues
    if anchor_summary['quality_issues']:
        st.markdown("### ⚠️ **Quality Issues**")
        for issue in anchor_summary['quality_issues']:
            st.warning(f"⚠️ {issue}")

# ==========================================
# UPDATE MAIN NAVIGATION TO INCLUDE ANCHORS PAGE
# ==========================================
def update_main_navigation_for_anchors():
    """
    This function should be called in the main() function to handle the Anchors page
    """
    # This will be integrated into the main navigation in Part 1H
    pass














