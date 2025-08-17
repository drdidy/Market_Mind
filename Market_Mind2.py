# Market Lens - Part 1: Core Infrastructure

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from pathlib import Path
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger('MarketLens')

class DataInfrastructure:
    def __init__(self):
        self.timezone = pytz.timezone('America/Chicago')
        self.cache_dir = Path('.market_lens')
        self.cache_dir.mkdir(exist_ok=True)
        
        self.status = {
            'live': True,
            'last_update': None,
            'error_count': 0
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def fetch_data(self, symbol: str, period: str = "5d", interval: str = "1m"):
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval, prepost=True)
        
        if data.empty:
            raise ValueError(f"No data for {symbol}")
        
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert(self.timezone)
        
        return data
    
    @st.cache_data(ttl=300)
    def get_data(_self, symbol: str):
        try:
            raw_data = _self.fetch_data(symbol)
            resampled = _self.resample_30min(raw_data)
            _self.status['last_update'] = datetime.now(_self.timezone)
            return resampled
        except Exception as e:
            logger.error(f"Data error {symbol}: {e}")
            _self.status['error_count'] += 1
            return pd.DataFrame()
    
    def resample_30min(self, data):
        resampled = data.resample('30T', label='right', closed='right').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        resampled['Change'] = resampled['Close'].pct_change()
        return resampled
    
    def market_hours(self):
        now = datetime.now(self.timezone)
        market_open = now.replace(hour=8, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=0, second=0, microsecond=0)
        
        is_rth = market_open <= now <= market_close
        return {
            'now': now,
            'is_rth': is_rth,
            'session': 'RTH' if is_rth else 'Extended'
        }

@st.cache_resource
def get_infrastructure():
    return DataInfrastructure()

# Market Lens - Part 2: UI Foundation

import streamlit as st
from streamlit_option_menu import option_menu

class UIFoundation:
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'success': '#2ca02c', 
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'dark': '#343a40',
            'light': '#f8f9fa'
        }
        
        self.icons = {
            '^GSPC': '📈',
            'ES=F': '⚡',
            'AAPL': '🍎',
            'MSFT': '🖥️',
            'NVDA': '🎮',
            'AMZN': '📦',
            'GOOGL': '🔍',
            'TSLA': '🚗',
            'META': '👥'
        }
        
        self.names = {
            '^GSPC': 'S&P 500',
            'ES=F': 'E-mini S&P 500',
            'AAPL': 'Apple',
            'MSFT': 'Microsoft',
            'NVDA': 'NVIDIA',
            'AMZN': 'Amazon',
            'GOOGL': 'Google',
            'TSLA': 'Tesla',
            'META': 'Meta'
        }
    
    def setup_page(self):
        st.set_page_config(
            page_title="Market Lens",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        st.markdown("""
        <style>
        .big-icon {
            font-size: 80px;
            text-align: center;
            margin: 20px 0;
        }
        
        .medium-icon {
            font-size: 60px;
            text-align: center;
            margin: 15px 0;
        }
        
        .symbol-title {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .symbol-name {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }
        
        .metric-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        
        .status-good { color: #2ca02c; }
        .status-warning { color: #ff7f0e; }
        .status-danger { color: #d62728; }
        </style>
        """, unsafe_allow_html=True)
    
    def main_navigation(self):
        return option_menu(
            menu_title=None,
            options=["Dashboard", "SPX", "Stocks", "Trades", "Analytics"],
            icons=["speedometer2", "graph-up-arrow", "building", "currency-exchange", "bar-chart"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": "#eee"
                },
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )
    
    def display_large_symbol(self, symbol, price=None, change=None):
        icon = self.icons.get(symbol, '📊')
        name = self.names.get(symbol, symbol)
        
        st.markdown(f'<div class="big-icon">{icon}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="symbol-title">{symbol}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="symbol-name">{name}</div>', unsafe_allow_html=True)
        
        if price is not None:
            change_color = "status-good" if change >= 0 else "status-danger"
            change_text = f"+{change:.2%}" if change >= 0 else f"{change:.2%}"
            
            st.markdown(f"""
            <div class="metric-container">
                <div style="font-size: 32px; font-weight: bold;">${price:,.2f}</div>
                <div class="{change_color}" style="font-size: 18px;">{change_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    def display_medium_symbol(self, symbol, price=None, change=None):
        icon = self.icons.get(symbol, '📊')
        name = self.names.get(symbol, symbol)
        
        st.markdown(f'<div class="medium-icon">{icon}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="symbol-title" style="font-size: 20px;">{symbol}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="symbol-name">{name}</div>', unsafe_allow_html=True)
        
        if price is not None:
            change_color = "status-good" if change >= 0 else "status-danger"
            change_text = f"+{change:.2%}" if change >= 0 else f"{change:.2%}"
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Price", f"${price:,.2f}")
            with col2:
                st.markdown(f'<div class="{change_color}" style="font-size: 16px; padding-top: 8px;">{change_text}</div>', unsafe_allow_html=True)
    
    def status_bar(self, status_data):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_color = "status-good" if status_data.get('live', False) else "status-danger"
            st.markdown(f'<div class="{status_color}">● Live</div>', unsafe_allow_html=True)
        
        with col2:
            session = status_data.get('session', 'Unknown')
            st.markdown(f"**Session:** {session}")
        
        with col3:
            if status_data.get('last_update'):
                time_str = status_data['last_update'].strftime("%H:%M:%S")
                st.markdown(f"**Updated:** {time_str}")
        
        with col4:
            errors = status_data.get('error_count', 0)
            error_color = "status-good" if errors == 0 else "status-warning"
            st.markdown(f'<div class="{error_color}">Errors: {errors}</div>', unsafe_allow_html=True)
    
    def format_price(self, price):
        if pd.isna(price):
            return "N/A"
        return f"${price:,.2f}"
    
    def format_change(self, change):
        if pd.isna(change):
            return "N/A"
        return f"{change:+.2%}"

@st.cache_resource
def get_ui():
    return UIFoundation()
