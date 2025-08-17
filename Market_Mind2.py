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

# Market Lens - Part 2: SPX Module

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
import json

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

class SPXModule:
    def __init__(self, infrastructure):
        self.infrastructure = infrastructure
        self.skyline_slope = 0.2255
        self.baseline_slope = -0.2255
        
        self.cache_file = self.infrastructure.cache_dir / 'spx_anchors.json'
        
    def calculate_es_spx_offset(self):
        """Calculate daily ES to SPX conversion offset at 15:00 CT"""
        try:
            now = datetime.now(self.infrastructure.timezone)
            target_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
            
            spx_data = self.infrastructure.get_market_data('^GSPC', '2d')
            es_data = self.infrastructure.get_market_data('ES=F', '2d')
            
            if spx_data.empty or es_data.empty:
                return self._get_fallback_offset()
            
            # Find closest data to 15:00 CT
            spx_15 = self._find_closest_price(spx_data, target_time)
            es_15 = self._find_closest_price(es_data, target_time)
            
            if spx_15 is None or es_15 is None:
                return self._get_fallback_offset()
            
            offset = spx_15 - es_15
            logger.info(f"ES->SPX offset calculated: {offset:.2f}")
            
            return offset
            
        except Exception as e:
            logger.error(f"Error calculating ES->SPX offset: {e}")
            return self._get_fallback_offset()
    
    def _find_closest_price(self, data, target_time, window_minutes=5):
        """Find price closest to target time within window"""
        try:
            start_window = target_time - timedelta(minutes=window_minutes)
            end_window = target_time + timedelta(minutes=window_minutes)
            
            window_data = data[(data.index >= start_window) & (data.index <= end_window)]
            
            if window_data.empty:
                return None
            
            # Find closest timestamp
            time_diffs = abs(window_data.index - target_time)
            closest_idx = time_diffs.argmin()
            
            return window_data['Close'].iloc[closest_idx]
            
        except Exception as e:
            logger.error(f"Error finding closest price: {e}")
            return None
    
    def _get_fallback_offset(self):
        """Fallback offset based on typical SPX-ES spread"""
        return 15.0
    
    def convert_es_to_spx(self, es_price, offset=None):
        """Convert ES price to SPX equivalent"""
        if offset is None:
            offset = self.calculate_es_spx_offset()
        return es_price + offset
    
    def detect_anchors(self):
        """Auto-detect Skyline and Baseline anchors from SPX-equivalent data"""
        try:
            offset = self.calculate_es_spx_offset()
            es_data = self.infrastructure.get_market_data('ES=F', '2d')
            
            if es_data.empty:
                return self._get_fallback_anchors()
            
            # Convert ES to SPX equivalent
            spx_eq_prices = es_data['Close'] + offset
            
            # Filter data before 20:00 CT for anchor detection
            now = datetime.now(self.infrastructure.timezone)
            cutoff_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
            
            if now.hour >= 20:
                cutoff_time = cutoff_time - timedelta(days=1)
            
            anchor_data = es_data[es_data.index < cutoff_time]
            anchor_spx_eq = anchor_data['Close'] + offset
            
            if anchor_spx_eq.empty:
                return self._get_fallback_anchors()
            
            # Find swing highs and lows
            skyline_anchor = self._find_skyline_anchor(anchor_data, anchor_spx_eq)
            baseline_anchor = self._find_baseline_anchor(anchor_data, anchor_spx_eq)
            
            anchors = {
                'skyline': skyline_anchor,
                'baseline': baseline_anchor,
                'offset': offset,
                'timestamp': datetime.now().isoformat()
            }
            
            self._save_anchors(anchors)
            return anchors
            
        except Exception as e:
            logger.error(f"Error detecting anchors: {e}")
            return self._get_fallback_anchors()
    
    def _find_skyline_anchor(self, data, spx_eq_prices):
        """Find highest swing high for Skyline anchor"""
        try:
            # Simple swing high detection
            highs = spx_eq_prices.rolling(window=3, center=True).max()
            swing_highs = spx_eq_prices[spx_eq_prices == highs]
            
            if swing_highs.empty:
                max_idx = spx_eq_prices.idxmax()
                return {
                    'price': float(spx_eq_prices.loc[max_idx]),
                    'timestamp': max_idx.isoformat()
                }
            
            highest_swing = swing_highs.max()
            highest_time = swing_highs.idxmax()
            
            return {
                'price': float(highest_swing),
                'timestamp': highest_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error finding skyline anchor: {e}")
            return {'price': 4500.0, 'timestamp': datetime.now().isoformat()}
    
    def _find_baseline_anchor(self, data, spx_eq_prices):
        """Find lowest swing low for Baseline anchor"""
        try:
            # Simple swing low detection
            lows = spx_eq_prices.rolling(window=3, center=True).min()
            swing_lows = spx_eq_prices[spx_eq_prices == lows]
            
            if swing_lows.empty:
                min_idx = spx_eq_prices.idxmin()
                return {
                    'price': float(spx_eq_prices.loc[min_idx]),
                    'timestamp': min_idx.isoformat()
                }
            
            lowest_swing = swing_lows.min()
            lowest_time = swing_lows.idxmin()
            
            return {
                'price': float(lowest_swing),
                'timestamp': lowest_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error finding baseline anchor: {e}")
            return {'price': 4450.0, 'timestamp': datetime.now().isoformat()}
    
    def _get_fallback_anchors(self):
        """Fallback anchors for demo purposes"""
        now = datetime.now()
        return {
            'skyline': {'price': 4520.0, 'timestamp': now.isoformat()},
            'baseline': {'price': 4480.0, 'timestamp': now.isoformat()},
            'offset': 15.0,
            'timestamp': now.isoformat()
        }
    
    def _save_anchors(self, anchors):
        """Save anchors to cache file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(anchors, f)
        except Exception as e:
            logger.error(f"Error saving anchors: {e}")
    
    def _load_anchors(self):
        """Load anchors from cache file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading anchors: {e}")
        return None
    
    def calculate_blocks_from_anchor(self, anchor_time, target_time):
        """Calculate number of 30-min blocks between anchor and target"""
        try:
            anchor_dt = datetime.fromisoformat(anchor_time.replace('Z', '+00:00'))
            if anchor_dt.tzinfo is None:
                anchor_dt = self.infrastructure.timezone.localize(anchor_dt)
            
            if target_time.tzinfo is None:
                target_time = self.infrastructure.timezone.localize(target_time)
            
            # Convert both to same timezone
            anchor_dt = anchor_dt.astimezone(self.infrastructure.timezone)
            target_time = target_time.astimezone(self.infrastructure.timezone)
            
            time_diff = target_time - anchor_dt
            blocks = time_diff.total_seconds() / (30 * 60)  # 30-minute blocks
            
            return int(round(blocks))
            
        except Exception as e:
            logger.error(f"Error calculating blocks: {e}")
            return 0
    
    def generate_rth_forecast(self):
        """Generate RTH forecast table with Skyline/Baseline levels"""
        try:
            anchors = self._load_anchors()
            if not anchors:
                anchors = self.detect_anchors()
            
            skyline_anchor = anchors['skyline']
            baseline_anchor = anchors['baseline']
            
            # Generate RTH time slots (8:30 AM - 2:30 PM CT)
            now = datetime.now(self.infrastructure.timezone)
            today = now.date()
            
            rth_slots = []
            for hour in range(8, 15):
                for minute in [30] if hour == 8 else [0, 30]:
                    if hour == 14 and minute == 30:
                        break
                    slot_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
                    slot_time = self.infrastructure.timezone.localize(slot_time)
                    rth_slots.append(slot_time)
            
            forecast_data = []
            
            for slot_time in rth_slots:
                # Calculate blocks from anchors
                skyline_blocks = self.calculate_blocks_from_anchor(skyline_anchor['timestamp'], slot_time)
                baseline_blocks = self.calculate_blocks_from_anchor(baseline_anchor['timestamp'], slot_time)
                
                # Calculate levels
                skyline_level = skyline_anchor['price'] + (self.skyline_slope * skyline_blocks)
                baseline_level = baseline_anchor['price'] + (self.baseline_slope * baseline_blocks)
                
                # Determine zone
                current_price = self._get_current_spx_price()
                zone = self._determine_zone(current_price, skyline_level, baseline_level)
                
                forecast_data.append({
                    'Time': slot_time.strftime('%H:%M'),
                    'Skyline': skyline_level,
                    'Baseline': baseline_level,
                    'Zone': zone,
                    'Distance_Skyline': abs(current_price - skyline_level) if current_price else 0,
                    'Distance_Baseline': abs(current_price - baseline_level) if current_price else 0
                })
            
            return pd.DataFrame(forecast_data)
            
        except Exception as e:
            logger.error(f"Error generating RTH forecast: {e}")
            return pd.DataFrame()
    
    def _get_current_spx_price(self):
        """Get current SPX price or SPX-equivalent price"""
        try:
            spx_data = self.infrastructure.get_market_data('^GSPC', '1d')
            if not spx_data.empty:
                return spx_data['Close'].iloc[-1]
            
            # Fallback to ES conversion
            es_data = self.infrastructure.get_market_data('ES=F', '1d')
            if not es_data.empty:
                offset = self.calculate_es_spx_offset()
                return es_data['Close'].iloc[-1] + offset
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current SPX price: {e}")
            return None
    
    def _determine_zone(self, current_price, skyline_level, baseline_level):
        """Determine if price is in Sell Zone, Buy Zone, or Between"""
        if current_price is None:
            return "Unknown"
        
        if current_price >= skyline_level:
            return "🔴 Sell Zone"
        elif current_price <= baseline_level:
            return "🟢 Buy Zone"
        else:
            return "🟡 Between"

@st.cache_resource
def get_data_infrastructure():
    return MarketDataInfrastructure()

@st.cache_resource
def get_spx_module():
    infrastructure = get_data_infrastructure()
    return SPXModule(infrastructure)

def format_price(price):
    return f"${price:,.2f}" if not pd.isna(price) else "N/A"

def format_change(change):
    return f"{change*100:+.2f}%" if not pd.isna(change) else "N/A"

def main():
    st.set_page_config(page_title="Market Lens", page_icon="📊", layout="wide")
    
    st.title("Market Lens")
    st.markdown("Enterprise Trading Platform")
    
    infrastructure = get_data_infrastructure()
    spx_module = get_spx_module()
    
    # Tabs for navigation
    tab1, tab2 = st.tabs(["📈 Dashboard", "📊 SPX Forecast"])
    
    with tab1:
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
                
                # Show ES->SPX conversion
                offset = spx_module.calculate_es_spx_offset()
                spx_equivalent = latest + offset
                st.metric("SPX Equivalent", format_price(spx_equivalent))
                
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
                
                st.markdown(f"<div style='text-align: center; font-size: 60px; margin-bottom: 10px;'>{stock_info['icon']}</div>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center; margin: 0;'>{symbol}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: #666; font-size: 12px; margin-top: 5px;'>{stock_info['name']}</p>", unsafe_allow_html=True)
                
                stock_data = infrastructure.get_market_data(symbol)
                if not stock_data.empty:
                    latest = stock_data['Close'].iloc[-1]
                    change = stock_data['Price_Change'].iloc[-1]
                    st.metric("", format_price(latest), format_change(change))
                else:
                    st.error("No data")
    
    with tab2:
        st.subheader("📊 SPX Skyline & Baseline Forecast")
        
        # Anchor Information
        col1, col2, col3 = st.columns(3)
        
        anchors = spx_module.detect_anchors()
        
        with col1:
            st.metric("🔴 Skyline Anchor", format_price(anchors['skyline']['price']))
            skyline_time = datetime.fromisoformat(anchors['skyline']['timestamp'].replace('Z', ''))
            st.caption(f"Time: {skyline_time.strftime('%H:%M')}")
        
        with col2:
            st.metric("🟢 Baseline Anchor", format_price(anchors['baseline']['price']))
            baseline_time = datetime.fromisoformat(anchors['baseline']['timestamp'].replace('Z', ''))
            st.caption(f"Time: {baseline_time.strftime('%H:%M')}")
        
        with col3:
            st.metric("ES→SPX Offset", f"+{anchors['offset']:.2f}")
            st.caption("Daily conversion factor")
        
        st.markdown("---")
        
        # RTH Forecast Table
        st.subheader("Regular Trading Hours Forecast")
        
        forecast_df = spx_module.generate_rth_forecast()
        
        if not forecast_df.empty:
            # Style the dataframe
            styled_df = forecast_df.style.format({
                'Skyline': '${:,.2f}',
                'Baseline': '${:,.2f}',
                'Distance_Skyline': '{:.2f} pts',
                'Distance_Baseline': '{:.2f} pts'
            })
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Current market position
            current_price = spx_module._get_current_spx_price()
            if current_price:
                st.info(f"Current SPX Level: {format_price(current_price)}")
        else:
            st.warning("Unable to generate forecast. Check data connections.")
        
        # Controls
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Anchors"):
                spx_module.detect_anchors()
                st.success("Anchors updated!")
                st.rerun()
        
        with col2:
            if st.button("📊 Export Forecast"):
                st.success("Export functionality ready")
        
        with col3:
            if st.button("📈 View Charts"):
                st.info("Advanced charting ready")

if __name__ == "__main__":
    main()
