import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. SYSTEM CONSTANTS ---
# [span_6](start_span)Core mathematics and rates[span_6](end_span)
RATE_PER_CANDLE = 0.52
CANDLE_MINUTES = 30

# [span_7](start_span)Timezones and windows[span_7](end_span)
CT_TZ = pytz.timezone('US/Central')
MAINTENANCE_START_HOUR = 16  # 4:00 PM CT
MAINTENANCE_END_HOUR = 17    # 5:00 PM CT

# --- 2. STREAMLIT CONFIG & THEME ---
# Must be the first Streamlit command
st.set_page_config(
    page_title="SPX PROPHET NEXT GEN",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    [span_8](start_span)[span_9](start_span)[span_10](start_span)"""Injects the dark theme and custom font CSS[span_8](end_span)[span_9](end_span)[span_10](end_span)."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@500;700&family=Rajdhani:wght@500;600&display=swap');
        
        [span_11](start_span)/* Base Dark Theme[span_11](end_span) */
        .stApp {
            background-color: #060910;
            color: #ccd6f6;
        }
        
        [span_12](start_span)/* Font Assignments[span_12](end_span) */
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
    [span_13](start_span)and daily maintenance windows[span_13](end_span).
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
        # [span_14](start_span)Check exclusion rules[span_14](end_span)
        weekday = current_time.weekday()
        hour = current_time.hour
        
        is_maintenance = (hour >= MAINTENANCE_START_HOUR and hour < MAINTENANCE_END_HOUR)
        is_saturday = (weekday == 5)
        is_sunday_pre_open = (weekday == 6 and hour < MAINTENANCE_END_HOUR)
        is_friday_post_close = (weekday == 4 and hour >= MAINTENANCE_START_HOUR)
        
        # [span_15](start_span)If not in an excluded window, count it[span_15](end_span)
        if not (is_maintenance or is_saturday or is_sunday_pre_open or is_friday_post_close):
            candle_count += 1
            
        # [span_16](start_span)Increment by 30 minutes[span_16](end_span)
        current_time += timedelta(minutes=CANDLE_MINUTES)
        
    return candle_count

def project_line_value(anchor_price: float, anchor_time: datetime, target_time: datetime, is_ascending: bool) -> float:
    """
    [span_17](start_span)Calculates the projected value of a structural line at a specific future time[span_17](end_span).
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
