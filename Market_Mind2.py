# Market Lens - Session 1: Core Foundation & Branding
# Enterprise-Ready Market Forecasting Platform

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
from datetime import datetime, timedelta
import pytz
from typing import Dict, Tuple, Optional, List
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
        position: relative;
        overflow: hidden;
    }
    
    .market-lens-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        pointer-events: none;
    }
    
    .market-lens-title {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 4px 8px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
    }
    
    .market-lens-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        font-weight: 400;
        margin: 1rem 0 0 0;
        opacity: 0.95;
        position: relative;
        z-index: 1;
    }
    
    /* Professional card styling */
    .metric-card {
        background: var(--card-bg-light);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-color), var(--success-color));
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 32px rgba(0, 0, 0, 0.12);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.6rem 1.2rem;
        border-radius: 25px;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .status-live {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        color: #166534;
        border: 1px solid #16a34a;
    }
    
    .status-degraded {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: #92400e;
        border: 1px solid #d97706;
    }
    
    .status-fallback {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #991b1b;
        border: 1px solid #dc2626;
    }
    
    /* Zone styling */
    .sell-zone {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 2px solid var(--danger-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .sell-zone::before {
        content: '🔴';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
    }
    
    .buy-zone {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 2px solid var(--success-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .buy-zone::before {
        content: '🟢';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
    }
    
    .between-zone {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 2px solid var(--text-secondary);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .between-zone::before {
        content: '⚪';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
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
        border-radius: 12px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
    }
    
    /* Professional icons */
    .icon-large {
        font-size: 5rem;
        margin: 1.5rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    
    .icon-large:hover {
        transform: scale(1.1);
    }
    
    .spx-icon {
        color: #2563eb;
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        border-radius: 50%;
        padding: 1rem;
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
    }
    
    .stock-icon {
        color: #059669;
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        border-radius: 50%;
        padding: 1rem;
        box-shadow: 0 8px 16px rgba(5, 150, 105, 0.3);
    }
    
    .realtime-icon {
        color: #d97706;
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        border-radius: 50%;
        padding: 1rem;
        box-shadow: 0 8px 16px rgba(217, 119, 6, 0.3);
    }
    
    /* Feature showcase */
    .feature-showcase {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
        border: 1px solid var(--border-color);
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin: 2rem 0;
    }
    
    /* Animation */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
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
    
    # Timezone
    TIMEZONE = pytz.timezone('America/Chicago')  # Central Time
    
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
    <div class="market-lens-header fade-in">
        <h1 class="market-lens-title">📈 Market Lens</h1>
        <p class="market-lens-subtitle">Professional Market Forecasting Platform</p>
    </div>
    """, unsafe_allow_html=True)

def render_large_icons():
    """Render large, appealing icons for SPX and stocks"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;" class="fade-in">
            <div class="icon-large spx-icon">📊</div>
            <h3 style="margin: 1rem 0 0.5rem 0; color: #2563eb; font-weight: 600;">SPX Index</h3>
            <p style="color: #64748b; margin: 0; font-size: 1.1rem;">S&P 500 Forecasting</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;" class="fade-in">
            <div class="icon-large stock-icon">🏢</div>
            <h3 style="margin: 1rem 0 0.5rem 0; color: #059669; font-weight: 600;">Individual Stocks</h3>
            <p style="color: #64748b; margin: 0; font-size: 1.1rem;">Big 7 Analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;" class="fade-in">
            <div class="icon-large realtime-icon">⚡</div>
            <h3 style="margin: 1rem 0 0.5rem 0; color: #d97706; font-weight: 600;">Real-Time Data</h3>
            <p style="color: #64748b; margin: 0; font-size: 1.1rem;">Live Market Feeds</p>
        </div>
        """, unsafe_allow_html=True)

def render_status_badge(status: str) -> str:
    """Render a status badge with appropriate styling"""
    status_class = f"status-{status.lower()}"
    return f'<span class="status-badge {status_class}">{status}</span>'

def create_sample_forecast_table():
    """Create a beautiful sample forecast table for demo"""
    sample_data = {
        'Time (CT)': ['08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00'],
        'Skyline': [5850.25, 5852.50, 5854.75, 5857.00, 5859.25, 5861.50, 5863.75, 5866.00],
        'Baseline': [5825.75, 5823.50, 5821.25, 5819.00, 5816.75, 5814.50, 5812.25, 5810.00],
        'Current Zone': ['Sell Zone', 'Between', 'Buy Zone', 'Between', 'Sell Zone', 'Between', 'Buy Zone', 'Between'],
        'Distance': ['-12.5 pts', '+5.2 pts', '+8.7 pts', '-2.1 pts', '-15.8 pts', '+3.4 pts', '+11.2 pts', '-1.8 pts']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Style the dataframe
    styled_df = df.style.apply(
        lambda x: ['background-color: #fee2e2; color: #991b1b' if v == 'Sell Zone' 
                   else 'background-color: #dcfce7; color: #166534' if v == 'Buy Zone'
                   else 'background-color: #f1f5f9; color: #64748b' for v in x], 
        subset=['Current Zone']
    ).format({
        'Skyline': '{:.2f}',
        'Baseline': '{:.2f}'
    })
    
    return styled_df

def main():
    """Main application entry point for Session 1"""
    
    # Initialize configuration
    MarketLensConfig.ensure_data_dir()
    
    # Load custom styling
    load_custom_css()
    
    # Render header
    render_header()
    
    # Welcome message for Session 1
    st.markdown("""
    <div class="feature-showcase fade-in">
    <h2 style="color: #1e293b; margin-top: 0;">🎯 Session 1: Foundation & Branding Complete!</h2>
    
    <p style="font-size: 1.2rem; color: #64748b; line-height: 1.6;">
    Welcome to <strong>Market Lens</strong> - your enterprise-grade market forecasting platform. This session establishes the professional foundation that users will love to pay for.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show the large icons
    render_large_icons()
    
    # Feature highlights
    st.markdown("""
    <div class="feature-grid">
        <div class="metric-card fade-in">
            <h3 style="color: #2563eb; margin-top: 0;">🎨 Premium Design</h3>
            <ul style="color: #64748b; line-height: 1.8;">
                <li>Enterprise-grade CSS with animations</li>
                <li>Professional color scheme & typography</li>
                <li>Hover effects and smooth transitions</li>
                <li>Clean, modern interface design</li>
            </ul>
        </div>
        
        <div class="metric-card fade-in">
            <h3 style="color: #059669; margin-top: 0;">🏢 Enterprise Branding</h3>
            <ul style="color: #64748b; line-height: 1.8;">
                <li>Skyline/Baseline terminology</li>
                <li>Status indicators & zone styling</li>
                <li>Professional Market Lens identity</li>
                <li>User-friendly language (no jargon)</li>
            </ul>
        </div>
        
        <div class="metric-card fade-in">
            <h3 style="color: #d97706; margin-top: 0;">⚡ Ready for Scale</h3>
            <ul style="color: #64748b; line-height: 1.8;">
                <li>Big 7 stocks pre-configured</li>
                <li>Chicago timezone setup</li>
                <li>Data persistence structure</li>
                <li>Extensible architecture</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo status badges
    st.markdown("### 📊 System Status Indicators:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin-top: 0;">Data Feed</h4>
            {render_status_badge("Live")}
            <p style="color: #64748b; margin: 0.5rem 0 0 0;">Real-time market data</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin-top: 0;">Forecast Engine</h4>
            {render_status_badge("Degraded")}
            <p style="color: #64748b; margin: 0.5rem 0 0 0;">Using backup calculations</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin-top: 0;">Export System</h4>
            {render_status_badge("Fallback")}
            <p style="color: #64748b; margin: 0.5rem 0 0 0;">Limited functionality</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show zone styling examples
    st.markdown("### 🎯 Channel Zone Styling:")
    
    st.markdown("""
    <div class="sell-zone fade-in">
        <h4 style="margin: 0 0 0.5rem 0; color: #991b1b;">Sell Zone (Skyline)</h4>
        <p style="margin: 0; color: #7f1d1d;">Price approaching or touching upper channel - potential short opportunity with defined risk management.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="buy-zone fade-in">
        <h4 style="margin: 0 0 0.5rem 0; color: #166534;">Buy Zone (Baseline)</h4>
        <p style="margin: 0; color: #14532d;">Price approaching or touching lower channel - potential long opportunity with favorable risk/reward.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="between-zone fade-in">
        <h4 style="margin: 0 0 0.5rem 0; color: #475569;">Between Channels</h4>
        <p style="margin: 0; color: #64748b;">Price trading between Skyline and Baseline - neutral zone, wait for clear signals.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Interactive demo section
    st.markdown("### 🚀 Interactive Forecast Preview:")
    
    if st.button("🎯 Preview Professional Forecast Table", help="See what your enterprise forecast tables will look like"):
        st.markdown("**Sample SPX Forecast Table - Enterprise Format:**")
        styled_table = create_sample_forecast_table()
        st.dataframe(styled_table, use_container_width=True, hide_index=True)
        
        st.success("✅ This is the professional-grade forecast format your users will see in Sessions 2-8!")
        st.info("💡 **Enterprise Features Coming:** Real-time data, Excel export, interactive charts, and advanced analytics!")
    
    # Configuration showcase
    st.markdown("### 🔧 Enterprise Configuration Ready:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🛠️ Technical Foundation:**
        - Cache TTL: 5 minutes
        - Retry attempts: 3 with backoff
        - Timezone: America/Chicago
        - Data directory: `.market_lens/`
        - Error handling: Graceful degradation
        """)
    
    with col2:
        st.markdown(f"""
        **📈 Market Coverage Ready:**
        - **Big 7 Stocks:** {', '.join(MarketLensBranding.BIG_7_STOCKS.keys())}
        - **SPX Index:** ^GSPC
        - **ES Futures:** ES=F
        - **Data Source:** yfinance (professional grade)
        """)
    
    # Next session preview
    st.markdown("""
    <div class="feature-showcase fade-in">
    <h3 style="color: #1e293b; margin-top: 0;">🚀 Ready for Session 2A?</h3>
    
    <h4 style="color: #2563eb;">Next: Data Infrastructure Foundation</h4>
    <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #2563eb;">
        <ul style="margin: 0; color: #64748b; line-height: 1.8;">
            <li><strong>Enterprise Caching</strong> with 100MB disk cache & 5-min TTL</li>
            <li><strong>Intelligent Retry Logic</strong> with exponential backoff</li>
            <li><strong>Data Validation</strong> for price ranges & freshness</li>
            <li><strong>Error Handling</strong> with graceful degradation</li>
            <li><strong>Timezone Management</strong> auto-converts to Chicago time</li>
        </ul>
    </div>
    
    <p style="margin: 1.5rem 0 0 0; font-size: 1.2rem; font-weight: 600; color: #2563eb;">
    Type "2A" when you're ready to add the data infrastructure! 🔧
    </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
