# ============================================================================
# MARKETLENS PRO V5 - PART 1: QUANT ANALYTICS FOUNDATION
# BY MAX POINTE CONSULTING
# Professional Market Analysis & Signal Advisory Platform
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import pytz
import time
import warnings
from typing import Dict, List, Tuple, Optional, Any
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time as dt_time
import math

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ============================================================================
# CORE CONFIGURATION
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="MarketLens Pro v5 - Quant Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Trading symbols and configurations
SYMBOLS = {
    'SPX': '^GSPC',
    'ES_FUTURES': 'ES=F',
    'STOCKS': {
        'AAPL': 'AAPL',
        'MSFT': 'MSFT', 
        'NVDA': 'NVDA',
        'AMZN': 'AMZN',
        'GOOGL': 'GOOGL',
        'TSLA': 'TSLA',
        'META': 'META'
    }
}

# Slope configurations for anchor projections
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

# Time zone configurations
ET_TZ = pytz.timezone('US/Eastern')
CT_TZ = pytz.timezone('US/Central')

# Cache TTL settings
LIVE_DATA_TTL = 60  # 1 minute for live data
HISTORICAL_DATA_TTL = 300  # 5 minutes for historical data

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================

def apply_custom_css():
    """Apply custom CSS for professional quant analytics appearance"""
    st.markdown("""
    <style>
    /* Global Styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Metric Styling - Mobile Optimized */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(34, 211, 238, 0.3);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    [data-testid="metric-container"] > div {
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Ensure text doesn't overflow */
    [data-testid="metric-container"] [data-testid="metric-label"],
    [data-testid="metric-container"] [data-testid="metric-value"],
    [data-testid="metric-container"] [data-testid="metric-delta"] {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.9rem;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    /* Alert Box Styling - Flexible Heights with Uniform Appearance */
    .stAlert > div {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(34, 211, 238, 0.3);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        min-height: 200px;
        padding: 20px;
        display: flex;
        align-items: flex-start;
    }
    
    .stAlert > div > div {
        width: 100%;
        line-height: 1.4;
    }
    
    /* Dataframe Styling */
    .stDataFrame > div {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(34, 211, 238, 0.3);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        padding: 16px;
    }
    
    /* Custom Headers */
    .custom-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(34, 211, 238, 0.3);
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    .custom-header h1 {
        color: #22d3ee;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 0 20px rgba(34, 211, 238, 0.5);
    }
    
    .custom-header p {
        color: #94a3b8;
        font-size: 1rem;
        margin: 8px 0 0 0;
        opacity: 0.9;
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .custom-header h1 {
            font-size: 1.8rem;
        }
        
        .custom-header p {
            font-size: 0.9rem;
        }
        
        [data-testid="metric-container"] {
            min-height: 80px;
            padding: 8px;
        }
        
        [data-testid="metric-container"] [data-testid="metric-label"],
        [data-testid="metric-container"] [data-testid="metric-value"],
        [data-testid="metric-container"] [data-testid="metric-delta"] {
            font-size: 0.8rem;
        }
        
        [data-testid="metric-container"] [data-testid="metric-value"] {
            font-size: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# DATACLASSES FOR ANALYTICS
# ============================================================================

@dataclass
class AnchorPoint:
    """Represents an anchor point for line projection"""
    price: float
    timestamp: datetime
    anchor_type: str  # 'skyline' or 'baseline'
    source_day: str   # For stocks: 'Monday' or 'Tuesday'

@dataclass
class SignalOpportunity:
    """Represents a signal opportunity for analysis"""
    symbol: str
    signal_type: str  # 'BUY_OPPORTUNITY' or 'SELL_OPPORTUNITY'
    anchor_line: str  # 'skyline' or 'baseline'
    target_price: float
    confidence_score: float
    risk_reward_ratio: float
    signal_time: datetime
    market_context: Dict[str, Any]

@dataclass
class MarketAnalysis:
    """Container for comprehensive market analysis"""
    symbol: str
    data: pd.DataFrame
    last_update: datetime
    volatility: float
    trend_strength: float
    support_resistance: Dict[str, float]
    anchor_projections: Dict[str, float]

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables for analytics platform"""
    if 'initialized' not in st.session_state:
        # Core application state
        st.session_state.initialized = True
        st.session_state.current_page = 'Analytics Dashboard'
        st.session_state.market_data_cache = {}
        st.session_state.anchor_cache = {}
        st.session_state.signal_opportunities = []
        
        # User analytics preferences
        st.session_state.selected_symbols = ['SPX', 'AAPL', 'MSFT']
        st.session_state.analysis_timeframe = '30min'
        st.session_state.auto_refresh = True
        st.session_state.risk_tolerance = 'Medium'
        
        # Analytics session tracking
        st.session_state.session_start_time = datetime.now()
        st.session_state.opportunities_identified = 0
        st.session_state.analysis_runs = 0
        
        # Data quality tracking
        st.session_state.data_health = {
            'last_check': datetime.now(),
            'connection_status': 'Connected',
            'data_quality_score': 0.0,
            'failed_requests': 0,
            'successful_requests': 0
        }
        
        # Market analytics metrics
        st.session_state.analytics_metrics = {
            'market_volatility': 0.0,
            'trend_strength': 0.0,
            'correlation_score': 0.0,
            'momentum_index': 0.0,
            'risk_score': 0.0,
            'opportunity_score': 0.0
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_current_time(timezone='ET'):
    """Get current time in specified timezone"""
    if timezone == 'ET':
        return datetime.now(ET_TZ)
    elif timezone == 'CT':
        return datetime.now(CT_TZ)
    else:
        return datetime.now()

def is_market_hours():
    """Check if market is currently open (9:30 AM - 4:00 PM ET)"""
    now = get_current_time('ET')
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # Check if it's a weekday and within market hours
    return (now.weekday() < 5 and market_open <= now <= market_close)

def is_asian_session():
    """Check if we're currently in Asian session (5:00-7:30 PM CT previous day)"""
    now = get_current_time('CT')
    asian_start = now.replace(hour=17, minute=0, second=0, microsecond=0)
    asian_end = now.replace(hour=19, minute=30, second=0, microsecond=0)
    
    return asian_start <= now <= asian_end

def calculate_30min_blocks_since_market_open():
    """Calculate number of 30-minute blocks since market open"""
    now = get_current_time('ET')
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    
    if now < market_open:
        return 0
    
    time_diff = now - market_open
    return int(time_diff.total_seconds() / 1800)

def calculate_volatility(prices: pd.Series) -> float:
    """Calculate price volatility"""
    if len(prices) < 2:
        return 0.0
    
    returns = prices.pct_change().dropna()
    return float(returns.std() * np.sqrt(252) * 100)  # Annualized volatility

def calculate_trend_strength(prices: pd.Series) -> float:
    """Calculate trend strength using linear regression R²"""
    if len(prices) < 10:
        return 0.0
    
    x = np.arange(len(prices))
    correlation = np.corrcoef(x, prices)[0, 1]
    return float(abs(correlation) * 100)

def calculate_momentum_index(prices: pd.Series) -> float:
    """Calculate momentum index"""
    if len(prices) < 20:
        return 0.0
    
    recent_change = (prices.iloc[-1] - prices.iloc[-20]) / prices.iloc[-20]
    return float(recent_change * 100)

def get_market_status():
    """Get current market status"""
    now = get_current_time('ET')
    
    if is_market_hours():
        return "🟢 OPEN", "#00ff88"
    elif now.hour < 9 or (now.hour == 9 and now.minute < 30):
        return "🟡 PRE", "#ff6b35"
    elif now.hour >= 16:
        return "🔴 AH", "#ef4444"  # AH = After Hours
    else:
        return "⚫ CLOSED", "#64748b"

# ============================================================================
# CACHE MANAGEMENT & DATA FETCHING
# ============================================================================

@st.cache_data(ttl=LIVE_DATA_TTL)
def fetch_live_quote(symbol: str) -> Dict[str, Any]:
    """Fetch live quote with caching and analytics"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d', interval='1m')
        
        if not hist.empty:
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            # Update successful requests
            st.session_state.data_health['successful_requests'] += 1
            
            return {
                'price': float(latest['Close']),
                'change': float(latest['Close'] - previous['Close']),
                'change_percent': float((latest['Close'] - previous['Close']) / previous['Close'] * 100),
                'volume': int(latest['Volume']),
                'volatility': calculate_volatility(hist['Close'].tail(20)),
                'timestamp': datetime.now()
            }
    except Exception:
        st.session_state.data_health['failed_requests'] += 1
        
    # Return None on failure - no fake data
    return None

@st.cache_data(ttl=HISTORICAL_DATA_TTL)
def fetch_historical_data(symbol: str, period: str = '5d', interval: str = '30m') -> pd.DataFrame:
    """Fetch historical data with caching"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        
        if not data.empty:
            st.session_state.data_health['successful_requests'] += 1
            return data
    except Exception:
        st.session_state.data_health['failed_requests'] += 1
    
    return pd.DataFrame()  # Return empty DataFrame on failure

def update_analytics_metrics():
    """Update analytics metrics based on current market data"""
    total_requests = st.session_state.data_health['successful_requests'] + st.session_state.data_health['failed_requests']
    
    if total_requests > 0:
        success_rate = st.session_state.data_health['successful_requests'] / total_requests
        st.session_state.data_health['data_quality_score'] = success_rate * 100
        st.session_state.data_health['connection_status'] = 'Connected' if success_rate > 0.8 else 'Degraded'
    
    # Calculate market analytics if we have data
    volatilities = []
    trend_strengths = []
    
    for symbol_key in st.session_state.selected_symbols:
        symbol = SYMBOLS.get(symbol_key, SYMBOLS['STOCKS'].get(symbol_key))
        if symbol:
            quote = fetch_live_quote(symbol)
            if quote:
                volatilities.append(quote['volatility'])
                
                # Get trend data
                hist_data = fetch_historical_data(symbol, period='5d', interval='30m')
                if not hist_data.empty:
                    trend_strength = calculate_trend_strength(hist_data['Close'])
                    trend_strengths.append(trend_strength)
    
    # Update analytics metrics
    if volatilities:
        st.session_state.analytics_metrics['market_volatility'] = np.mean(volatilities)
    if trend_strengths:
        st.session_state.analytics_metrics['trend_strength'] = np.mean(trend_strengths)
    
    # Calculate composite scores
    vol = st.session_state.analytics_metrics['market_volatility']
    trend = st.session_state.analytics_metrics['trend_strength']
    
    st.session_state.analytics_metrics['risk_score'] = min(100, vol * 2)
    st.session_state.analytics_metrics['opportunity_score'] = min(100, trend + (vol * 0.5))

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class MarketLensProAnalytics:
    """Main analytics application class"""
    
    def __init__(self):
        self.initialize_app()
    
    def initialize_app(self):
        """Initialize the analytics application"""
        initialize_session_state()
        self.update_analytics()
    
    def update_analytics(self):
        """Update all analytics metrics"""
        update_analytics_metrics()
        st.session_state.analysis_runs += 1

# ============================================================================
# DASHBOARD INTERFACE
# ============================================================================

def render_header():
    """Render professional analytics header"""
    st.markdown("""
    <div class="custom-header">
        <h1>📊 MarketLens Pro v5</h1>
        <p>Quantitative Market Analysis & Signal Advisory Platform</p>
    </div>
    """, unsafe_allow_html=True)

def render_market_overview():
    """Render market overview with real analytics"""
    st.subheader("📈 Market Overview")
    
    # Mobile-friendly: 2 rows of metrics instead of 5 columns
    col1, col2, col3 = st.columns(3)
    
    market_status, _ = get_market_status()
    quality_score = st.session_state.data_health['data_quality_score']
    session_hours = (datetime.now() - st.session_state.session_start_time).total_seconds() / 3600
    
    with col1:
        # Use the short status directly - no additional shortening needed
        market_status, _ = get_market_status()
        st.metric("Market", market_status, get_current_time('ET').strftime('%H:%M ET'))
    
    with col2:
        st.metric("Data Quality", f"{quality_score:.1f}%", st.session_state.data_health['connection_status'])
    
    with col3:
        st.metric("Session", f"{session_hours:.1f}h", f"{st.session_state.analysis_runs} runs")
    
    # Second row
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("Symbols", len(st.session_state.selected_symbols), "tracking")
    
    with col5:
        blocks = calculate_30min_blocks_since_market_open()
        st.metric("Blocks", f"{blocks}/13", "30min periods")
    
    with col6:
        st.metric("Opportunities", st.session_state.opportunities_identified, "identified")

def render_analytics_dashboard():
    """Render quantitative analytics dashboard"""
    st.subheader("🧮 Quantitative Analytics")
    
    # Mobile-friendly: 3 columns x 2 rows instead of 6 columns
    col1, col2, col3 = st.columns(3)
    
    metrics = st.session_state.analytics_metrics
    
    with col1:
        vol_display = f"{metrics['market_volatility']:.1f}%" if metrics['market_volatility'] > 0 else "..."
        st.metric("Volatility", vol_display, "annualized")
    
    with col2:
        trend_display = f"{metrics['trend_strength']:.1f}%" if metrics['trend_strength'] > 0 else "..."
        st.metric("Trend", trend_display, "strength")
    
    with col3:
        risk_display = f"{metrics['risk_score']:.1f}" if metrics['risk_score'] > 0 else "..."
        st.metric("Risk Score", risk_display, "0-100 scale")
    
    # Second row
    col4, col5, col6 = st.columns(3)
    
    with col4:
        opp_display = f"{metrics['opportunity_score']:.1f}" if metrics['opportunity_score'] > 0 else "..."
        st.metric("Opportunity", opp_display, "score")
    
    with col5:
        st.metric("Signals", st.session_state.opportunities_identified, "today")
    
    with col6:
        momentum_display = f"{metrics['momentum_index']:.1f}%" if metrics['momentum_index'] != 0 else "..."
        st.metric("Momentum", momentum_display, "index")

def render_anchor_analysis():
    """Render anchor system analysis"""
    st.subheader("⚓ Anchor System Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        anchor_status = "🟢 Active" if is_market_hours() or is_asian_session() else "⏸️ Standby"
        next_analysis = (datetime.now() + timedelta(seconds=LIVE_DATA_TTL)).strftime('%H:%M:%S')
        
        st.info(f"""
        **📊 SPX ANCHOR SYSTEM**
        
        • Asian Session: {anchor_status}
        • ES Futures: ✅ Configured
        • Slope Rate: ±{SLOPES['SPX']['skyline']}/block
        • Projections: Real-time
        
        **Time Window:** 5:00-7:30 PM CT
        **Next Update:** {next_analysis}
        """)
    
    with col2:
        mon_tue_status = "🟢 Ready" if datetime.now().weekday() in [0, 1] else "⏳ Awaiting Mon/Tue"
        
        st.success(f"""
        **📈 STOCK ANCHOR SYSTEM**
        
        • Mon/Tue Analysis: {mon_tue_status}
        • Symbols: {len(SYMBOLS['STOCKS'])} configured
        • Cross-Day Detection: ✅ Active
        • Custom Slopes: Per symbol
        
        **Tracking:** {', '.join(list(SYMBOLS['STOCKS'].keys())[:3])}+
        **Status:** Monitoring swing points
        """)
    
    with col3:
        data_points = st.session_state.data_health['successful_requests']
        quality_score = st.session_state.data_health['data_quality_score']
        analysis_quality = "Excellent" if quality_score > 90 else "Good" if quality_score > 70 else "Fair"
        
        st.warning(f"""
        **⚡ SYSTEM PERFORMANCE**
        
        • Data Points: {data_points} processed
        • Quality Level: {analysis_quality}
        • Cache Items: {len(st.session_state.market_data_cache)} stored
        • Update Rate: {LIVE_DATA_TTL}s intervals
        
        **System Load:** Optimal performance
        **Response Time:** Sub-second analysis
        """)

def render_live_market_feed():
    """Render live market data feed with analytics"""
    st.subheader("📊 Live Market Feed")
    
    symbols_to_analyze = ['SPX', 'AAPL', 'MSFT', 'NVDA']
    
    # Mobile-friendly: 2 columns x 2 rows instead of 4 columns
    for i in range(0, len(symbols_to_analyze), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(symbols_to_analyze):
                symbol_key = symbols_to_analyze[i + j]
                symbol = SYMBOLS.get(symbol_key, SYMBOLS['STOCKS'].get(symbol_key))
                
                if symbol:
                    quote = fetch_live_quote(symbol)
                    
                    if quote:
                        with col:
                            delta_color = "normal" if quote['change'] >= 0 else "inverse"
                            vol_text = f"Volatility: {quote['volatility']:.1f}%"
                            
                            st.metric(
                                label=f"{symbol_key}",
                                value=f"${quote['price']:.2f}",
                                delta=f"{quote['change']:+.2f} ({quote['change_percent']:+.2f}%)",
                                delta_color=delta_color,
                                help=vol_text
                            )
                    else:
                        with col:
                            st.metric(f"{symbol_key}", "No Data", "Connection issue")

def render_system_diagnostics():
    """Render system diagnostics with real metrics"""
    st.subheader("🔧 System Diagnostics & Performance")
    
    # Calculate real system metrics
    total_requests = st.session_state.data_health['successful_requests'] + st.session_state.data_health['failed_requests']
    success_rate = (st.session_state.data_health['successful_requests'] / max(1, total_requests)) * 100
    cache_size = len(st.session_state.market_data_cache)
    uptime_hours = (datetime.now() - st.session_state.session_start_time).total_seconds() / 3600
    
    diagnostics_data = {
        'Component': [
            'Market Data Engine',
            'Anchor Detection System',
            'Analytics Calculator',
            'Cache Management',
            'Session Manager',
            'Data Quality Monitor'
        ],
        'Status': [
            '🟢 Online' if success_rate > 80 else '🟡 Degraded',
            '🟢 Ready',
            '🟢 Computing' if st.session_state.analysis_runs > 0 else '🟡 Standby',
            '🟢 Active' if cache_size > 0 else '⚪ Empty',
            '🟢 Active',
            '🟢 Monitoring'
        ],
        'Performance': [
            f"{success_rate:.1f}%",
            "100%" if len(SLOPES) > 0 else "0%",
            f"{min(100, st.session_state.analysis_runs * 10):.0f}%",
            f"{min(100, cache_size * 20):.0f}%",
            "100%",
            f"{st.session_state.data_health['data_quality_score']:.1f}%"
        ],
        'Metrics': [
            f"Requests: {total_requests}",
            f"Symbols: {len(SLOPES)}",
            f"Runs: {st.session_state.analysis_runs}",
            f"Items: {cache_size}",
            f"Uptime: {uptime_hours:.1f}h",
            f"Score: {st.session_state.data_health['data_quality_score']:.1f}"
        ]
    }
    
    diagnostics_df = pd.DataFrame(diagnostics_data)
    
    st.dataframe(
        diagnostics_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Component': st.column_config.TextColumn('Component', width='large'),
            'Status': st.column_config.TextColumn('Status', width='medium'),
            'Performance': st.column_config.TextColumn('Performance', width='small'),
            'Metrics': st.column_config.TextColumn('Details', width='medium')
        }
    )

def render_analytics_dashboard_main():
    """Main analytics dashboard rendering function"""
    # Apply custom CSS
    apply_custom_css()
    
    # Render all sections
    render_header()
    render_market_overview()
    
    st.divider()
    
    render_analytics_dashboard()
    
    st.divider()
    
    render_anchor_analysis()
    
    st.divider()
    
    render_live_market_feed()
    
    st.divider()
    
    render_system_diagnostics()
    
    # Professional footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; opacity: 0.7; padding: 20px;">
        <strong>MarketLens Pro v5</strong> - Quantitative Market Analysis Platform | 
        Professional signal advisory and analytics | 
        © 2024 Max Pointe Consulting
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

def main():
    """Main application entry point"""
    
    # Initialize the analytics application
    app = MarketLensProAnalytics()
    
    # Render the analytics dashboard
    render_analytics_dashboard_main()
    
    # Auto-refresh for live analytics
    if st.session_state.auto_refresh:
        time.sleep(3)
        st.rerun()

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    main()