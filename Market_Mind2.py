import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. SYSTEM CONSTANTS ---
RATE_PER_CANDLE = 0.52
CANDLE_MINUTES = 30
CT_TZ = pytz.timezone('US/Central')
MAINTENANCE_START_HOUR = 16  # 4:00 PM CT
MAINTENANCE_END_HOUR = 17    # 5:00 PM CT

# --- 2. STREAMLIT CONFIG & THEME ---
st.set_page_config(
    page_title="SPX PROPHET 2.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    [span_3](start_span)[span_4](start_span)"""Injects the dark theme and custom font CSS[span_3](end_span)[span_4](end_span)."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@500;700&family=Rajdhani:wght@500;600&display=swap');
        
        /* Base Dark Theme */
        .stApp {
            background-color: #060910;
            color: #ccd6f6;
        }
        
        /* Font Assignments */
        h1, h2, h3, .orbitron {
            font-family: 'Orbitron', sans-serif !important;
        }
        p, span, .rajdhani {
            font-family: 'Rajdhani', sans-serif !important;
        }
        code, .jetbrains, .price-display {
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        /* Tab Styling overrides to fit dark theme */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
            font-family: 'Orbitron', sans-serif !important;
            color: #8892b0;
        }
        .stTabs [aria-selected="true"] {
            color: #ccd6f6 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. CORE MATHEMATICS & TIME HANDLING ---
def count_candles_between(start_dt: datetime, end_dt: datetime) -> int:
    [span_5](start_span)"""Counts 30-min intervals excluding weekends/maintenance[span_5](end_span)."""
    if start_dt.tzinfo is None: start_dt = CT_TZ.localize(start_dt)
    if end_dt.tzinfo is None: end_dt = CT_TZ.localize(end_dt)
    if start_dt >= end_dt: return 0
        
    candle_count = 0
    current_time = start_dt
    
    while current_time < end_dt:
        weekday = current_time.weekday()
        hour = current_time.hour
        
        is_maintenance = (hour >= MAINTENANCE_START_HOUR and hour < MAINTENANCE_END_HOUR)
        is_saturday = (weekday == 5)
        is_sunday_pre_open = (weekday == 6 and hour < MAINTENANCE_END_HOUR)
        is_friday_post_close = (weekday == 4 and hour >= MAINTENANCE_START_HOUR)
        
        if not (is_maintenance or is_saturday or is_sunday_pre_open or is_friday_post_close):
            candle_count += 1
            
        current_time += timedelta(minutes=CANDLE_MINUTES)
        
    return candle_count

# --- 4. UI COMPONENTS ---
def render_section_banner(icon: str, title: str, subtitle: str, color: str):
    [span_6](start_span)"""Renders a highly styled section header[span_6](end_span)."""
    html = f"""
    <div style="margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid {color}; display: flex; align-items: center; gap: 15px;">
        <div style="font-size: 2.5rem;">{icon}</div>
        <div>
            <h2 class="orbitron" style="margin: 0; padding: 0; color: #ccd6f6;">{title}</h2>
            <span class="rajdhani" style="color: #8892b0; font-size: 1.1rem;">{subtitle}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- 5. MAIN APPLICATION LAYOUT ---
def main():
    inject_custom_css()
    
    # [span_7](start_span)Sidebar[span_7](end_span)
    with st.sidebar:
        st.markdown("<h2 class='orbitron' style='color: #00d4ff;'>SPX PROPHET 2.0</h2>", unsafe_allow_html=True)
        st.markdown("---")
        st.write("Controls and Settings will populate here.")
        
    # [span_8](start_span)Main Tabs[span_8](end_span)
    tab_map, tab_asian, tab_ny, tab_log = st.tabs([
        "🗺️ STRUCTURAL MAP", 
        "🌏 ASIAN SESSION", 
        "🗽 NY SESSION", 
        "📓 TRADE LOG"
    ])
    
    with tab_map:
        [span_9](start_span)render_section_banner("🗺️", "STRUCTURAL MAP", "Prior NY Session Data & 9 AM Projections", "#00d4ff") # Cyan[span_9](end_span)
        st.info("The yfinance historical ES=F data and line ladder will be rendered here.")
        
    with tab_asian:
        [span_10](start_span)render_section_banner("🌏", "ASIAN SESSION", "ES Futures Prop Firm Scalping Framework", "#ff9100") # Orange[span_10](end_span)
        st.info("6:00 PM decision points and position sizing calculator will go here.")
        
    with tab_ny:
        [span_11](start_span)render_section_banner("🗽", "NY SESSION", "SPX 0DTE Options Signal Generation", "#b388ff") # Purple[span_11](end_span)
        st.info("9:00 AM signal cards, Black-Scholes premium projections, and confluence scoring will go here.")
        
    with tab_log:
        [span_12](start_span)render_section_banner("📓", "TRADE LOG", "Daily Journal & Performance Metrics", "#00e676") # Green[span_12](end_span)
        st.info("Rich text editor and Plotly equity curves will go here.")

if __name__ == "__main__":
    main()
