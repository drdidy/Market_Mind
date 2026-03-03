import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. SYSTEM CONSTANTS ---
# Core mathematics and rates
RATE_PER_CANDLE = 0.52
CANDLE_MINUTES = 30

# Timezones and windows
CT_TZ = pytz.timezone('US/Central')
MAINTENANCE_START_HOUR = 16  # 4:00 PM CT
MAINTENANCE_END_HOUR = 17    # 5:00 PM CT

# --- 2. STREAMLIT CONFIG & THEME ---
# MUST be the very first Streamlit command
st.set_page_config(
    page_title="SPX PROPHET NEXT GEN",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    """Injects the dark theme and custom font CSS."""
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
        </style>
    """, unsafe_allow_html=True)

# --- 3. CORE MATHEMATICS & TIME HANDLING ---
def count_candles_between(start_dt: datetime, end_dt: datetime) -> int:
    """
    Counts 30-minute intervals between two datetimes, excluding weekends 
    and daily maintenance windows.
    """
    # Ensure both datetimes are timezone aware (Central Time)
    if start_dt.tzinfo is None:
        start_dt = CT_TZ.localize(start_dt)
    if end_dt.tzinfo is None:
        end_dt = CT_TZ.localize(end_dt)
        
    if start_dt >= end_dt:
        return 0
        
    candle_count = 0
    current_time = start_dt
    
    while current_time < end_dt:
        # Check exclusion rules
        weekday = current_time.weekday()
        hour = current_time.hour
        
        is_maintenance = (hour >= MAINTENANCE_START_HOUR and hour < MAINTENANCE_END_HOUR)
        is_saturday = (weekday == 5)
        is_sunday_pre_open = (weekday == 6 and hour < MAINTENANCE_END_HOUR)
        is_friday_post_close = (weekday == 4 and hour >= MAINTENANCE_START_HOUR)
        
        # If not in an excluded window, count it
        if not (is_maintenance or is_saturday or is_sunday_pre_open or is_friday_post_close):
            candle_count += 1
            
        # Increment by 30 minutes
        current_time += timedelta(minutes=CANDLE_MINUTES)
        
    return candle_count

def project_line_value(anchor_price: float, anchor_time: datetime, target_time: datetime, is_ascending: bool) -> float:
    """
    Calculates the projected value of a structural line at a specific future time.
    """
    candles = count_candles_between(anchor_time, target_time)
    price_change = RATE_PER_CANDLE * candles
    
    if is_ascending:
        return anchor_price + price_change
    else:
        return anchor_price - price_change

# --- INITIALIZATION ---
if __name__ == "__main__":
    inject_custom_css()
    st.title("SPX PROPHET NEXT GEN")
    st.write("System Foundation Initialized.")
