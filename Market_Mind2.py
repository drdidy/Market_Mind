import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. SYSTEM CONSTANTS ---
RATE_PER_CANDLE = 0.52
CT_TZ = pytz.timezone('US/Central')
MAINTENANCE_START_HOUR = 16 
MAINTENANCE_END_HOUR = 17 

# --- 2. STREAMLIT CONFIG & THEME ---
st.set_page_config(
    page_title="SPX PROPHET 2.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@500;700&family=Rajdhani:wght@500;600&display=swap');
        
        .stApp { background-color: #060910; color: #ccd6f6; }
        
        /* Typography */
        h1, h2, h3, .orbitron { font-family: 'Orbitron', sans-serif !important; letter-spacing: 2px; }
        p, span, .rajdhani { font-family: 'Rajdhani', sans-serif !important; }
        .jetbrains { font-family: 'JetBrains Mono', monospace !important; }
        
        /* Metric Cards */
        .metric-card {
            background: rgba(17, 25, 40, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .metric-value {
            font-family: 'JetBrains Mono';
            font-size: 1.5rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0a0e17 !important;
            border-right: 1px solid #1e293b;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=300)
def get_market_data(symbol="ES=F"):
    """Fetches 30m candle data for the last 5 days."""
    try:
        data = yf.download(symbol, period="5d", interval="30m")
        return data
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return None

# --- 4. UI COMPONENTS ---
def render_section_banner(icon: str, title: str, subtitle: str, color: str):
    st.markdown(f"""
    <div style="margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid {color}; display: flex; align-items: center; gap: 15px;">
        <div style="font-size: 2.5rem;">{icon}</div>
        <div>
            <h2 class="orbitron" style="margin: 0; padding: 0; color: #ccd6f6;">{title}</h2>
            <span class="rajdhani" style="color: #8892b0; font-size: 1.1rem;">{subtitle}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, color="#00d4ff"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="rajdhani" style="color: #8892b0; font-size: 0.9rem; text-transform: uppercase;">{label}</div>
        <div class="metric-value" style="color: {color};">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APP ---
def main():
    inject_custom_css()
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("<h2 class='orbitron' style='color: #00d4ff; font-size: 1.2rem;'>SYSTEM STATUS</h2>", unsafe_allow_html=True)
        render_metric_card("Engine State", "OPERATIONAL", "#00e676")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<h3 class='orbitron' style='font-size: 0.9rem;'>SESSION CONTROLS</h3>", unsafe_allow_html=True)
        target_date = st.date_input("Analysis Date", datetime.now())
        manual_offset = st.number_input("ES-SPX Offset", value=0.0, step=0.25)
        
        st.markdown("---")
        st.button("🔄 Force Data Refresh")

    # --- TABS ---
    tab_map, tab_asian, tab_ny, tab_log = st.tabs(["🗺️ STRUCTURAL MAP", "🌏 ASIAN SESSION", "🗽 NY SESSION", "📓 TRADE LOG"])
    
    # FETCH DATA
    es_data = get_market_data()
    
    with tab_map:
        render_section_banner("🗺️", "STRUCTURAL MAP", "Prior NY Session Data & 9 AM Projections", "#00d4ff")
        
        if es_data is not None:
            col1, col2, col3, col4 = st.columns(4)
            last_price = es_data['Close'].iloc[-1]
            change = last_price - es_data['Open'].iloc[-1]
            
            with col1: render_metric_card("Current ES", f"{last_price:.2f}")
            with col2: render_metric_card("24h Change", f"{change:+.2f}", "#00e676" if change > 0 else "#ff5252")
            with col3: render_metric_card("Cone Rate", "0.52")
            with col4: render_metric_card("Active Lines", "0")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Placeholder for the Chart
            st.markdown("<h3 class='orbitron' style='font-size: 1.1rem;'>30M PRICE ACTION</h3>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Candlestick(x=es_data.index,
                            open=es_data['Open'], high=es_data['High'],
                            low=es_data['Low'], close=es_data['Close'])])
            fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), height=400)
            st.plotly_chart(fig, use_container_視野=True)
        else:
            st.warning("Connecting to Liquidity Provider (yfinance)...")

    # (Other tabs remain as placeholders for now)

if __name__ == "__main__":
    main()
