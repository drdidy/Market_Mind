# Market Lens - Session 1: Core Foundation & Branding
# Enterprise-Ready Market Forecasting Platform

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import time

# Handle imports gracefully
try:
    import pandas as pd
    import numpy as np
    import yfinance as yf
    import pytz
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False

# ===========================
# SESSION 1: FOUNDATION & BRANDING
# ===========================

# Configure Streamlit page
st.set_page_config(
    page_title="Market Lens",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Market Lens - Professional Market Forecasting Platform"
    }
)

# Custom CSS for Enterprise Branding
def load_custom_css():
    st.markdown("""
    <style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for theming */
    :root {
        --primary-color: #2563eb;
        --secondary-color: #1e40af;
        --success-color: #059669;
        --warning-color: #d97706;
        --danger-color: #dc2626;
        --background-dark: #0f172a;
        --background-light: #f8fafc;
        --card-bg-light: #ffffff;
        --card-bg-dark: #1e293b;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
    }
    
    /* Main app styling */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1400px;
    }
    
    /* Custom header styling */
    .market-lens-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2);
        text-align: center;
    }
    
    .market-lens-title {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .market-lens-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Professional card styling */
    .metric-card {
        background: var(--card-bg-light);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-live {
        background-color: #dcfce7;
        color: #166534;
    }
    
    .status-degraded {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .status-fallback {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    /* Zone styling */
    .sell-zone {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-left: 4px solid var(--danger-color);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .buy-zone {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 4px solid var(--success-color);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .between-zone {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-left: 4px solid var(--text-secondary);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: var(--background-light);
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Professional icons */
    .icon-large {
        font-size: 4rem;
        margin: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .spx-icon {
        color: #2563eb;
    }
    
    .stock-icon {
        color: #059669;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Branding and Constants
class MarketLensBranding:
    """Core branding and terminology for Market Lens"""
    
    # Channel terminology - use consistently throughout UI
    SKYLINE = "Skyline"  # Upper channel
    BASELINE = "Baseline"  # Lower channel
    
    # Zone labels for user display
    SELL_ZONE = "Sell Zone"
    BUY_ZONE = "Buy Zone"
    BETWEEN_ZONE = "Between Channels"
    
    # Status indicators
    STATUS_LIVE = "Live"
    STATUS_DEGRADED = "Degraded" 
    STATUS_FALLBACK = "Fallback"
    
    # Colors for consistency
    COLORS = {
        'primary': '#2563eb',
        'secondary': '#1e40af',
        'success': '#059669',
        'warning': '#d97706',
        'danger': '#dc2626',
        'skyline': '#dc2626',  # Red for sell zone
        'baseline': '#059669',  # Green for buy zone
        'between': '#64748b'   # Gray for between
    }
    
    # Big 7 stocks for initial setup
    BIG_7_STOCKS = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation', 
        'NVDA': 'NVIDIA Corporation',
        'AMZN': 'Amazon.com Inc.',
        'GOOGL': 'Alphabet Inc.',
        'TSLA': 'Tesla Inc.',
        'META': 'Meta Platforms Inc.'
    }
    
    # SPX symbols
    SPX_SYMBOLS = {
        'SPX_INDEX': '^GSPC',
        'ES_FUTURES': 'ES=F'
    }

class MarketLensConfig:
    """Configuration constants for Market Lens"""
    
    # Timezone (handle gracefully if pytz not available)
    if DEPENDENCIES_AVAILABLE:
        TIMEZONE = pytz.timezone('America/Chicago')  # Central Time
    else:
        TIMEZONE = None
    
    # Data intervals and caching
    CACHE_TTL = 300  # 5 minutes
    RETRY_ATTEMPTS = 3
    RETRY_BACKOFF = 2  # seconds
    
    # Directory for data persistence
    DATA_DIR = '.market_lens'
    SLOPES_FILE = os.path.join(DATA_DIR, 'slopes.json')
    
    # Create data directory if it doesn't exist
    @classmethod
    def ensure_data_dir(cls):
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)

def render_header():
    """Render the main Market Lens header with branding"""
    st.markdown("""
    <div class="market-lens-header">
        <h1 class="market-lens-title">📈 Market Lens</h1>
        <p class="market-lens-subtitle">Professional Market Forecasting Platform</p>
    </div>
    """, unsafe_allow_html=True)

def render_large_icons():
    """Render large, appealing icons for SPX and stocks"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div class="icon-large spx-icon">📊</div>
            <h3 style="margin: 0; color: #2563eb;">SPX Index</h3>
            <p style="color: #64748b; margin: 0.5rem 0 0 0;">S&P 500 Forecasting</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div class="icon-large stock-icon">🏢</div>
            <h3 style="margin: 0; color: #059669;">Stocks</h3>
            <p style="color: #64748b; margin: 0.5rem 0 0 0;">Individual Stock Analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div class="icon-large" style="color: #d97706;">⚡</div>
            <h3 style="margin: 0; color: #d97706;">Real-Time</h3>
            <p style="color: #64748b; margin: 0.5rem 0 0 0;">Live Market Data</p>
        </div>
        """, unsafe_allow_html=True)

def render_status_badge(status: str) -> str:
    """Render a status badge with appropriate styling"""
    status_class = f"status-{status.lower()}"
    return f'<span class="status-badge {status_class}">{status}</span>'

def show_dependency_error():
    """Show dependency installation instructions"""
    st.error("📦 **Dependencies Required**")
    st.markdown("""
    Please install the required packages to run Market Lens:
    
    ```bash
    pip install streamlit pandas numpy yfinance pytz plotly openpyxl requests python-dateutil
    ```
    
    Or use the requirements.txt file:
    ```bash
    pip install -r requirements.txt
    ```
    
    Then restart your Streamlit application.
    """)

def main():
    """Main application entry point for Session 1"""
    
    # Load custom styling
    load_custom_css()
    
    # Check dependencies first
    if not DEPENDENCIES_AVAILABLE:
        render_header()
        show_dependency_error()
        st.stop()
    
    # Initialize configuration
    MarketLensConfig.ensure_data_dir()
    
    # Render header
    render_header()
    
    # Welcome message for Session 1
    st.markdown("""
    ## 🎯 Session 1: Foundation & Branding Complete!
    
    Welcome to **Market Lens** - your enterprise-grade market forecasting platform. This session establishes:
    
    ### ✅ What's Implemented:
    - **Professional Branding**: Clean, enterprise-ready UI with Market Lens identity
    - **Core Terminology**: Skyline (upper channel) and Baseline (lower channel) throughout
    - **Visual Appeal**: Large, attractive icons and professional color scheme
    - **Enterprise Styling**: Hover effects, gradients, and polished components
    - **Configuration Structure**: Timezone (CT), caching, and data management setup
    - **Big 7 Stocks**: Pre-configured with AAPL, MSFT, NVDA, AMZN, GOOGL, TSLA, META
    - **Status System**: Live/Degraded/Fallback indicators for data reliability
    
    ### 🎨 Design Features:
    """)
    
    # Show the large icons
    render_large_icons()
    
    # Demo status badges
    st.markdown("### Status Indicators:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Data Status</h4>
            {render_status_badge("Live")}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Market Status</h4>
            {render_status_badge("Degraded")}
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Forecast Status</h4>
            {render_status_badge("Fallback")}
        </div>
        """, unsafe_allow_html=True)
    
    # Show zone styling examples
    st.markdown("### Channel Zone Styling:")
    
    st.markdown("""
    <div class="sell-zone">
        <strong>🔴 Sell Zone (Skyline)</strong><br>
        Price approaching or touching upper channel - potential short opportunity
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="buy-zone">
        <strong>🟢 Buy Zone (Baseline)</strong><br>
        Price approaching or touching lower channel - potential long opportunity
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="between-zone">
        <strong>⚪ Between Channels</strong><br>
        Price trading between Skyline and Baseline - neutral zone
    </div>
    """, unsafe_allow_html=True)
    
    # Configuration preview
    st.markdown("### 🔧 Enterprise Configuration:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Data Management:**
        - Cache TTL: 5 minutes
        - Retry attempts: 3
        - Timezone: America/Chicago
        - Data directory: `.market_lens/`
        """)
    
    with col2:
        st.markdown(f"""
        **Big 7 Stocks Ready:**
        {', '.join(MarketLensBranding.BIG_7_STOCKS.keys())}
        
        **SPX Symbols:**
        - Index: ^GSPC
        - Futures: ES=F
        """)
    
    # Interactive demo section
    st.markdown("### 🚀 Interactive Preview:")
    
    # Sample forecast table preview
    if st.button("🎯 Preview Forecast Table", help="See what the forecast tables will look like"):
        sample_data = {
            'Time (CT)': ['08:30', '09:00', '09:30', '10:00', '10:30'],
            'Skyline': [5850.25, 5852.50, 5854.75, 5857.00, 5859.25],
            'Baseline': [5825.75, 5823.50, 5821.25, 5819.00, 5816.75],
            'Zone': ['Sell Zone', 'Between', 'Buy Zone', 'Between', 'Sell Zone'],
            'Distance': ['-12.5 pts', '+5.2 pts', '+8.7 pts', '-2.1 pts', '-15.8 pts']
        }
        
        # Create DataFrame for display
        df_sample = pd.DataFrame(sample_data)
        
        st.markdown("**Sample SPX Forecast Table:**")
        st.dataframe(df_sample, use_container_width=True)
        
        st.success("✅ This is how your professional forecast tables will look in Sessions 2-8!")
    
    # Next session preview
    st.markdown("""
    ---
    ### 🚀 Ready for Session 2?
    
    **Next up: Data Infrastructure & yfinance Integration**
    - Real-time data fetching with robust error handling
    - SPX (^GSPC) and ES Futures (ES=F) integration  
    - 30-minute resampling and CT timezone handling
    - Intelligent caching with retry mechanisms
    - Data validation and fallback strategies
    
    **Type "2" when you're ready to continue!**
    """)

if __name__ == "__main__":
    main()
