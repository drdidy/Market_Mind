# Market Lens - Part 1: Data & Infrastructure

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from pathlib import Path
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import plotly.graph_objects as go

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MarketLens')

class MarketDataInfrastructure:
    def __init__(self):
        self.timezone = pytz.timezone('America/Chicago')
        self.cache_dir = Path('.market_lens')
        self.cache_dir.mkdir(exist_ok=True)
        
        self.SPX_SYMBOL = '^GSPC'
        self.ES_SYMBOL = 'ES=F'
        self.DEFAULT_STOCKS = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'TSLA', 'META']
        
        self.STOCK_ICONS = {
            'AAPL': '🍎', 'MSFT': '🖥️', 'NVDA': '🎮', 'AMZN': '📦',
            'GOOGL': '🔍', 'TSLA': '🚗', 'META': '👥', '^GSPC': '📈', 'ES=F': '⚡'
        }
        
        self.STOCK_NAMES = {
            'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.', 'NVDA': 'NVIDIA Corp.',
            'AMZN': 'Amazon.com Inc.', 'GOOGL': 'Alphabet Inc.', 'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.', '^GSPC': 'S&P 500 Index', 'ES=F': 'E-mini S&P 500'
        }
        
        self.data_status = {'live': True, 'last_update': None, 'error_count': 0}
    
    def get_stock_info(self, symbol: str):
        return {
            'symbol': symbol,
            'name': self.STOCK_NAMES.get(symbol, symbol),
            'icon': self.STOCK_ICONS.get(symbol, '📊')
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    def fetch_raw_data(self, symbol: str, period: str = "5d", interval: str = "1m"):
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval, prepost=True)
        
        if data.empty:
            raise ValueError(f"No data for {symbol}")
        
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert(self.timezone)
        
        return data
    
    @st.cache_data(ttl=300)
    def get_market_data(_self, symbol: str, period: str = "5d"):
        try:
            raw_data = _self.fetch_raw_data(symbol, period, "1m")
            resampled = _self._resample_to_30min(raw_data)
            _self.data_status['last_update'] = datetime.now(_self.timezone)
            return resampled
        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            _self.data_status['error_count'] += 1
            return pd.DataFrame()
    
    def _resample_to_30min(self, data):
        resampled = data.resample('30T', label='right', closed='right').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()
        
        resampled['Price_Change'] = resampled['Close'].pct_change()
        resampled['Volatility'] = resampled['Price_Change'].rolling(20).std()
        
        return resampled
    
    def create_chart(self, symbol: str, data):
        if data.empty:
            return None
        
        fig = go.Figure(data=go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], 
            low=data['Low'], close=data['Close'], name=symbol
        ))
        
        stock_info = self.get_stock_info(symbol)
        fig.update_layout(
            title=f"{stock_info['name']} - 30min",
            template="plotly_white", height=300, showlegend=False
        )
        
        return fig
    
    def get_market_hours(self):
        now = datetime.now(self.timezone)
        market_open = now.replace(hour=8, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=0, second=0, microsecond=0)
        
        is_rth = market_open <= now <= market_close
        return {
            'current_time': now,
            'is_rth': is_rth,
            'session': 'RTH' if is_rth else 'Extended'
        }

@st.cache_resource
def get_data_infrastructure():
    return MarketDataInfrastructure()

def format_price(price):
    return f"${price:,.2f}" if not pd.isna(price) else "N/A"

def format_change(change):
    return f"{change*100:+.2f}%" if not pd.isna(change) else "N/A"

def main():
    st.set_page_config(page_title="Market Lens", page_icon="📊", layout="wide")
    
    st.title("Market Lens")
    st.markdown("Enterprise Trading Platform")
    
    infrastructure = get_data_infrastructure()
    
    # Status Bar
    col1, col2, col3, col4 = st.columns(4)
    hours = infrastructure.get_market_hours()
    
    with col1:
        st.metric("Status", "Live")
    with col2:
        st.metric("Session", hours['session'])
    with col3:
        st.metric("Time", hours['current_time'].strftime("%H:%M CT"))
    with col4:
        st.metric("Errors", infrastructure.data_status['error_count'])
    
    st.markdown("---")
    
    # SPX & ES Section
    col1, col2 = st.columns(2)
    
    with col1:
        spx_info = infrastructure.get_stock_info('^GSPC')
        st.markdown(f"<div style='text-align: center; font-size: 80px;'>{spx_info['icon']}</div>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>{spx_info['name']}</h2>", unsafe_allow_html=True)
        
        spx_data = infrastructure.get_market_data('^GSPC')
        if not spx_data.empty:
            latest = spx_data['Close'].iloc[-1]
            change = spx_data['Price_Change'].iloc[-1]
            st.metric("Level", format_price(latest), format_change(change))
            
            chart = infrastructure.create_chart('^GSPC', spx_data)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
    
    with col2:
        es_info = infrastructure.get_stock_info('ES=F')
        st.markdown(f"<div style='text-align: center; font-size: 80px;'>{es_info['icon']}</div>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>{es_info['name']}</h2>", unsafe_allow_html=True)
        
        es_data = infrastructure.get_market_data('ES=F')
        if not es_data.empty:
            latest = es_data['Close'].iloc[-1]
            change = es_data['Price_Change'].iloc[-1]
            st.metric("Level", format_price(latest), format_change(change))
            
            chart = infrastructure.create_chart('ES=F', es_data)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    # Big 7 Stocks
    st.subheader("Big 7 Technology Stocks")
    
    cols = st.columns(4)
    for i, symbol in enumerate(infrastructure.DEFAULT_STOCKS):
        with cols[i % 4]:
            stock_info = infrastructure.get_stock_info(symbol)
            
            # Large centered icon
            st.markdown(f"<div style='text-align: center; font-size: 60px; margin-bottom: 10px;'>{stock_info['icon']}</div>", unsafe_allow_html=True)
            
            # Symbol and name
            st.markdown(f"<h3 style='text-align: center; margin: 0;'>{symbol}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #666; font-size: 12px; margin-top: 5px;'>{stock_info['name']}</p>", unsafe_allow_html=True)
            
            # Data
            stock_data = infrastructure.get_market_data(symbol)
            if not stock_data.empty:
                latest = stock_data['Close'].iloc[-1]
                change = stock_data['Price_Change'].iloc[-1]
                st.metric("", format_price(latest), format_change(change))
            else:
                st.error("No data")
    
    # Controls
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("📊 Export Data"):
            st.success("Export functionality ready")
    
    with col3:
        if st.button("⚙️ Settings"):
            st.info("Settings panel ready")

if __name__ == "__main__":
    main()
