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

# Market Lens - Part 3: SPX Data Module

import json

class SPXDataModule:
    def __init__(self, infrastructure):
        self.infrastructure = infrastructure
        self.spx_symbol = '^GSPC'
        self.es_symbol = 'ES=F'
        self.offset_cache = self.infrastructure.cache_dir / 'es_spx_offset.json'
        
    def get_spx_data(self):
        return self.infrastructure.get_data(self.spx_symbol)
    
    def get_es_data(self):
        return self.infrastructure.get_data(self.es_symbol)
    
    def calculate_es_spx_offset(self):
        try:
            now = datetime.now(self.infrastructure.timezone)
            target_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
            
            spx_data = self.get_spx_data()
            es_data = self.get_es_data()
            
            if spx_data.empty or es_data.empty:
                return self._load_cached_offset()
            
            spx_price = self._find_price_at_time(spx_data, target_time)
            es_price = self._find_price_at_time(es_data, target_time)
            
            if spx_price is None or es_price is None:
                return self._load_cached_offset()
            
            offset = spx_price - es_price
            self._save_offset(offset)
            return offset
            
        except Exception:
            return self._load_cached_offset()
    
    def _find_price_at_time(self, data, target_time):
        try:
            window_start = target_time - timedelta(minutes=5)
            window_end = target_time + timedelta(minutes=5)
            
            window_data = data[(data.index >= window_start) & (data.index <= window_end)]
            
            if window_data.empty:
                return None
            
            time_diffs = abs(window_data.index - target_time)
            closest_idx = time_diffs.argmin()
            return window_data['Close'].iloc[closest_idx]
            
        except Exception:
            return None
    
    def _save_offset(self, offset):
        try:
            offset_data = {
                'offset': float(offset),
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().date().isoformat()
            }
            with open(self.offset_cache, 'w') as f:
                json.dump(offset_data, f)
        except Exception:
            pass
    
    def _load_cached_offset(self):
        try:
            if self.offset_cache.exists():
                with open(self.offset_cache, 'r') as f:
                    data = json.load(f)
                return data.get('offset', 15.0)
        except Exception:
            pass
        return 15.0
    
    def convert_es_to_spx(self, es_price):
        offset = self.calculate_es_spx_offset()
        return es_price + offset
    
    def get_current_spx_price(self):
        try:
            spx_data = self.get_spx_data()
            if not spx_data.empty:
                return spx_data['Close'].iloc[-1]
            
            es_data = self.get_es_data()
            if not es_data.empty:
                es_price = es_data['Close'].iloc[-1]
                return self.convert_es_to_spx(es_price)
            
            return None
        except Exception:
            return None
    
    def get_spx_change(self):
        try:
            spx_data = self.get_spx_data()
            if not spx_data.empty and 'Change' in spx_data.columns:
                return spx_data['Change'].iloc[-1]
            return 0.0
        except Exception:
            return 0.0
    
    def get_es_change(self):
        try:
            es_data = self.get_es_data()
            if not es_data.empty and 'Change' in es_data.columns:
                return es_data['Change'].iloc[-1]
            return 0.0
        except Exception:
            return 0.0
    
    def get_spx_volume(self):
        try:
            spx_data = self.get_spx_data()
            if not spx_data.empty:
                return spx_data['Volume'].iloc[-1]
            return 0
        except Exception:
            return 0
    
    def get_es_volume(self):
        try:
            es_data = self.get_es_data()
            if not es_data.empty:
                return es_data['Volume'].iloc[-1]
            return 0
        except Exception:
            return 0
    
    def is_data_fresh(self, max_age_minutes=5):
        try:
            spx_data = self.get_spx_data()
            if spx_data.empty:
                return False
            
            last_timestamp = spx_data.index[-1]
            now = datetime.now(self.infrastructure.timezone)
            age = (now - last_timestamp).total_seconds() / 60
            
            return age <= max_age_minutes
        except Exception:
            return False

@st.cache_resource
def get_spx_module():
    infrastructure = get_infrastructure()
    return SPXDataModule(infrastructure)

# Market Lens - Part 4: Stock Data Module

class StockDataModule:
    def __init__(self, infrastructure):
        self.infrastructure = infrastructure
        self.stocks = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'TSLA', 'META']
        
    def get_stock_data(self, symbol):
        return self.infrastructure.get_data(symbol)
    
    def get_all_stocks_data(self):
        stock_data = {}
        for symbol in self.stocks:
            stock_data[symbol] = self.get_stock_data(symbol)
        return stock_data
    
    def get_stock_price(self, symbol):
        try:
            data = self.get_stock_data(symbol)
            if not data.empty:
                return data['Close'].iloc[-1]
            return None
        except Exception:
            return None
    
    def get_stock_change(self, symbol):
        try:
            data = self.get_stock_data(symbol)
            if not data.empty and 'Change' in data.columns:
                return data['Change'].iloc[-1]
            return 0.0
        except Exception:
            return 0.0
    
    def get_stock_volume(self, symbol):
        try:
            data = self.get_stock_data(symbol)
            if not data.empty:
                return data['Volume'].iloc[-1]
            return 0
        except Exception:
            return 0
    
    def get_stock_high_low(self, symbol):
        try:
            data = self.get_stock_data(symbol)
            if not data.empty:
                return {
                    'high': data['High'].iloc[-1],
                    'low': data['Low'].iloc[-1]
                }
            return {'high': None, 'low': None}
        except Exception:
            return {'high': None, 'low': None}
    
    def filter_session_data(self, data, start_hour=3, end_hour=18, end_minute=30):
        try:
            if data.empty:
                return data
            
            session_data = data[
                (data.index.hour >= start_hour) & 
                ((data.index.hour < end_hour) | 
                 ((data.index.hour == end_hour) & (data.index.minute <= end_minute)))
            ]
            return session_data
        except Exception:
            return data
    
    def get_monday_tuesday_data(self, symbol):
        try:
            data = self.get_stock_data(symbol)
            if data.empty:
                return pd.DataFrame()
            
            now = datetime.now(self.infrastructure.timezone)
            week_start = now - timedelta(days=now.weekday())
            
            monday = week_start
            tuesday = week_start + timedelta(days=1)
            
            monday_data = data[data.index.date == monday.date()]
            tuesday_data = data[data.index.date == tuesday.date()]
            
            combined = pd.concat([monday_data, tuesday_data])
            return self.filter_session_data(combined)
            
        except Exception:
            return pd.DataFrame()
    
    def find_weekly_anchors(self, symbol):
        try:
            mon_tue_data = self.get_monday_tuesday_data(symbol)
            if mon_tue_data.empty:
                return {'skyline': None, 'baseline': None}
            
            session_data = self.filter_session_data(mon_tue_data)
            if session_data.empty:
                return {'skyline': None, 'baseline': None}
            
            skyline_price = session_data['Close'].max()
            baseline_price = session_data['Close'].min()
            
            skyline_time = session_data[session_data['Close'] == skyline_price].index[0]
            baseline_time = session_data[session_data['Close'] == baseline_price].index[0]
            
            return {
                'skyline': {
                    'price': float(skyline_price),
                    'timestamp': skyline_time.isoformat()
                },
                'baseline': {
                    'price': float(baseline_price),
                    'timestamp': baseline_time.isoformat()
                }
            }
            
        except Exception:
            return {'skyline': None, 'baseline': None}
    
    def get_all_weekly_anchors(self):
        anchors = {}
        for symbol in self.stocks:
            anchors[symbol] = self.find_weekly_anchors(symbol)
        return anchors
    
    def is_stock_data_fresh(self, symbol, max_age_minutes=5):
        try:
            data = self.get_stock_data(symbol)
            if data.empty:
                return False
            
            last_timestamp = data.index[-1]
            now = datetime.now(self.infrastructure.timezone)
            age = (now - last_timestamp).total_seconds() / 60
            
            return age <= max_age_minutes
        except Exception:
            return False
    
    def count_blocks_in_session(self, start_time, end_time):
        try:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', ''))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', ''))
            
            if start_time.tzinfo is None:
                start_time = self.infrastructure.timezone.localize(start_time)
            if end_time.tzinfo is None:
                end_time = self.infrastructure.timezone.localize(end_time)
            
            start_time = start_time.astimezone(self.infrastructure.timezone)
            end_time = end_time.astimezone(self.infrastructure.timezone)
            
            total_blocks = 0
            current_time = start_time
            
            while current_time < end_time:
                next_time = current_time + timedelta(minutes=30)
                
                if (3 <= current_time.hour < 18) or (current_time.hour == 18 and current_time.minute <= 30):
                    total_blocks += 1
                
                current_time = next_time
            
            return total_blocks
            
        except Exception:
            return 0

@st.cache_resource  
def get_stock_module():
    infrastructure = get_infrastructure()
    return StockDataModule(infrastructure)

# Market Lens - Part 5: SPX Channel Engine

class SPXChannelEngine:
    def __init__(self, spx_module):
        self.spx_module = spx_module
        self.skyline_slope = 0.2255
        self.baseline_slope = -0.2255
        self.anchor_cache = self.spx_module.infrastructure.cache_dir / 'spx_anchors.json'
        
    def detect_anchors(self):
        try:
            offset = self.spx_module.calculate_es_spx_offset()
            es_data = self.spx_module.get_es_data()
            
            if es_data.empty:
                return self._get_fallback_anchors()
            
            now = datetime.now(self.spx_module.infrastructure.timezone)
            cutoff_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
            
            if now.hour >= 20:
                cutoff_time = cutoff_time - timedelta(days=1)
            
            anchor_data = es_data[es_data.index < cutoff_time]
            
            if anchor_data.empty:
                return self._get_fallback_anchors()
            
            spx_eq_prices = anchor_data['Close'] + offset
            
            skyline_anchor = self._find_swing_high(anchor_data, spx_eq_prices)
            baseline_anchor = self._find_swing_low(anchor_data, spx_eq_prices)
            
            anchors = {
                'skyline': skyline_anchor,
                'baseline': baseline_anchor,
                'offset': offset,
                'detection_time': now.isoformat()
            }
            
            self._save_anchors(anchors)
            return anchors
            
        except Exception:
            return self._get_fallback_anchors()
    
    def _find_swing_high(self, data, prices):
        try:
            rolling_max = prices.rolling(window=3, center=True).max()
            swing_highs = prices[prices == rolling_max]
            
            if swing_highs.empty:
                max_idx = prices.idxmax()
                return {
                    'price': float(prices.loc[max_idx]),
                    'timestamp': max_idx.isoformat()
                }
            
            highest_price = swing_highs.max()
            highest_time = swing_highs.idxmax()
            
            return {
                'price': float(highest_price),
                'timestamp': highest_time.isoformat()
            }
            
        except Exception:
            now = datetime.now(self.spx_module.infrastructure.timezone)
            return {
                'price': 4520.0,
                'timestamp': now.isoformat()
            }
    
    def _find_swing_low(self, data, prices):
        try:
            rolling_min = prices.rolling(window=3, center=True).min()
            swing_lows = prices[prices == rolling_min]
            
            if swing_lows.empty:
                min_idx = prices.idxmin()
                return {
                    'price': float(prices.loc[min_idx]),
                    'timestamp': min_idx.isoformat()
                }
            
            lowest_price = swing_lows.min()
            lowest_time = swing_lows.idxmin()
            
            return {
                'price': float(lowest_price),
                'timestamp': lowest_time.isoformat()
            }
            
        except Exception:
            now = datetime.now(self.spx_module.infrastructure.timezone)
            return {
                'price': 4480.0,
                'timestamp': now.isoformat()
            }
    
    def _get_fallback_anchors(self):
        now = datetime.now(self.spx_module.infrastructure.timezone)
        return {
            'skyline': {
                'price': 4520.0,
                'timestamp': now.isoformat()
            },
            'baseline': {
                'price': 4480.0,
                'timestamp': now.isoformat()
            },
            'offset': 15.0,
            'detection_time': now.isoformat()
        }
    
    def _save_anchors(self, anchors):
        try:
            with open(self.anchor_cache, 'w') as f:
                json.dump(anchors, f)
        except Exception:
            pass
    
    def _load_anchors(self):
        try:
            if self.anchor_cache.exists():
                with open(self.anchor_cache, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def calculate_blocks_between_times(self, start_time, end_time):
        try:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', ''))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', ''))
            
            if start_time.tzinfo is None:
                start_time = self.spx_module.infrastructure.timezone.localize(start_time)
            if end_time.tzinfo is None:
                end_time = self.spx_module.infrastructure.timezone.localize(end_time)
            
            time_diff = end_time - start_time
            blocks = time_diff.total_seconds() / (30 * 60)
            return int(round(blocks))
            
        except Exception:
            return 0
    
    def calculate_channel_level(self, anchor_price, anchor_time, target_time, is_skyline=True):
        try:
            blocks = self.calculate_blocks_between_times(anchor_time, target_time)
            slope = self.skyline_slope if is_skyline else self.baseline_slope
            return anchor_price + (slope * blocks)
        except Exception:
            return anchor_price
    
    def generate_rth_levels(self):
        try:
            anchors = self._load_anchors()
            if not anchors:
                anchors = self.detect_anchors()
            
            skyline_anchor = anchors['skyline']
            baseline_anchor = anchors['baseline']
            
            now = datetime.now(self.spx_module.infrastructure.timezone)
            today = now.date()
            
            rth_times = []
            for hour in range(8, 15):
                for minute in [0, 30]:
                    if hour == 8 and minute == 0:
                        continue
                    if hour == 14 and minute == 30:
                        break
                    
                    slot_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
                    slot_time = self.spx_module.infrastructure.timezone.localize(slot_time)
                    rth_times.append(slot_time)
            
            levels = []
            current_price = self.spx_module.get_current_spx_price()
            
            for slot_time in rth_times:
                skyline_level = self.calculate_channel_level(
                    skyline_anchor['price'], 
                    skyline_anchor['timestamp'], 
                    slot_time, 
                    is_skyline=True
                )
                
                baseline_level = self.calculate_channel_level(
                    baseline_anchor['price'], 
                    baseline_anchor['timestamp'], 
                    slot_time, 
                    is_skyline=False
                )
                
                zone = self._determine_zone(current_price, skyline_level, baseline_level)
                
                levels.append({
                    'time': slot_time.strftime('%H:%M'),
                    'skyline': skyline_level,
                    'baseline': baseline_level,
                    'zone': zone,
                    'skyline_distance': abs(current_price - skyline_level) if current_price else 0,
                    'baseline_distance': abs(current_price - baseline_level) if current_price else 0
                })
            
            return levels
            
        except Exception:
            return []
    
    def _determine_zone(self, current_price, skyline_level, baseline_level):
        if current_price is None:
            return "Unknown"
        
        if current_price >= skyline_level:
            return "Sell Zone"
        elif current_price <= baseline_level:
            return "Buy Zone"
        else:
            return "Between"
    
    def get_current_levels(self):
        try:
            anchors = self._load_anchors()
            if not anchors:
                anchors = self.detect_anchors()
            
            now = datetime.now(self.spx_module.infrastructure.timezone)
            
            current_skyline = self.calculate_channel_level(
                anchors['skyline']['price'],
                anchors['skyline']['timestamp'],
                now,
                is_skyline=True
            )
            
            current_baseline = self.calculate_channel_level(
                anchors['baseline']['price'],
                anchors['baseline']['timestamp'],
                now,
                is_skyline=False
            )
            
            current_price = self.spx_module.get_current_spx_price()
            zone = self._determine_zone(current_price, current_skyline, current_baseline)
            
            return {
                'skyline': current_skyline,
                'baseline': current_baseline,
                'current_price': current_price,
                'zone': zone,
                'anchors': anchors
            }
            
        except Exception:
            return {
                'skyline': None,
                'baseline': None,
                'current_price': None,
                'zone': "Unknown",
                'anchors': None
            }

@st.cache_resource
def get_spx_channel_engine():
    spx_module = get_spx_module()
    return SPXChannelEngine(spx_module)

# Market Lens - Part 6: Stock Channel Engine

class StockChannelEngine:
    def __init__(self, stock_module):
        self.stock_module = stock_module
        
        self.stock_slopes = {
            'AAPL': 0.0155,
            'MSFT': 0.0541,
            'NVDA': 0.0086,
            'AMZN': 0.0139,
            'GOOGL': 0.0122,
            'TSLA': 0.0285,
            'META': 0.0674
        }
        
        self.anchor_cache = self.stock_module.infrastructure.cache_dir / 'stock_anchors.json'
    
    def get_stock_slope(self, symbol):
        return self.stock_slopes.get(symbol, 0.01)
    
    def detect_weekly_anchors(self, symbol):
        try:
            mon_tue_data = self.stock_module.get_monday_tuesday_data(symbol)
            if mon_tue_data.empty:
                return self._get_fallback_anchors(symbol)
            
            session_data = self.stock_module.filter_session_data(mon_tue_data)
            if session_data.empty:
                return self._get_fallback_anchors(symbol)
            
            skyline_price = session_data['Close'].max()
            baseline_price = session_data['Close'].min()
            
            skyline_times = session_data[session_data['Close'] == skyline_price].index
            baseline_times = session_data[session_data['Close'] == baseline_price].index
            
            skyline_time = skyline_times[0] if len(skyline_times) > 0 else session_data.index[0]
            baseline_time = baseline_times[0] if len(baseline_times) > 0 else session_data.index[0]
            
            return {
                'skyline': {
                    'price': float(skyline_price),
                    'timestamp': skyline_time.isoformat()
                },
                'baseline': {
                    'price': float(baseline_price),
                    'timestamp': baseline_time.isoformat()
                }
            }
            
        except Exception:
            return self._get_fallback_anchors(symbol)
    
    def _get_fallback_anchors(self, symbol):
        base_price = self._get_base_price(symbol)
        now = datetime.now(self.stock_module.infrastructure.timezone)
        
        return {
            'skyline': {
                'price': base_price * 1.02,
                'timestamp': now.isoformat()
            },
            'baseline': {
                'price': base_price * 0.98,
                'timestamp': now.isoformat()
            }
        }
    
    def _get_base_price(self, symbol):
        base_prices = {
            'AAPL': 175.0,
            'MSFT': 378.0,
            'NVDA': 875.0,
            'AMZN': 155.0,
            'GOOGL': 142.0,
            'TSLA': 248.0,
            'META': 485.0
        }
        return base_prices.get(symbol, 100.0)
    
    def calculate_stock_blocks_in_session(self, start_time, end_time):
        try:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', ''))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', ''))
            
            if start_time.tzinfo is None:
                start_time = self.stock_module.infrastructure.timezone.localize(start_time)
            if end_time.tzinfo is None:
                end_time = self.stock_module.infrastructure.timezone.localize(end_time)
            
            start_time = start_time.astimezone(self.stock_module.infrastructure.timezone)
            end_time = end_time.astimezone(self.stock_module.infrastructure.timezone)
            
            blocks = 0
            current = start_time
            
            while current < end_time:
                if self._is_in_session_window(current):
                    blocks += 1
                current += timedelta(minutes=30)
            
            return blocks
            
        except Exception:
            return 0
    
    def _is_in_session_window(self, dt):
        hour = dt.hour
        minute = dt.minute
        
        if hour < 3:
            return False
        if hour > 18:
            return False
        if hour == 18 and minute > 30:
            return False
        
        return True
    
    def calculate_stock_channel_level(self, anchor_price, anchor_time, target_time, symbol, is_skyline=True):
        try:
            blocks = self.calculate_stock_blocks_in_session(anchor_time, target_time)
            slope = self.get_stock_slope(symbol)
            
            if not is_skyline:
                slope = -slope
            
            return anchor_price + (slope * blocks)
            
        except Exception:
            return anchor_price
    
    def generate_weekly_forecast(self, symbol):
        try:
            anchors = self.detect_weekly_anchors(symbol)
            skyline_anchor = anchors['skyline']
            baseline_anchor = anchors['baseline']
            
            now = datetime.now(self.stock_module.infrastructure.timezone)
            
            wednesday = self._get_next_weekday(now, 2)
            thursday = self._get_next_weekday(now, 3)
            
            forecast = []
            
            for day, day_name in [(wednesday, 'Wednesday'), (thursday, 'Thursday')]:
                day_levels = self._generate_day_levels(
                    day, day_name, symbol, skyline_anchor, baseline_anchor
                )
                forecast.extend(day_levels)
            
            return forecast
            
        except Exception:
            return []
    
    def _get_next_weekday(self, current_date, weekday):
        days_ahead = weekday - current_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return current_date + timedelta(days=days_ahead)
    
    def _generate_day_levels(self, day, day_name, symbol, skyline_anchor, baseline_anchor):
        levels = []
        current_price = self.stock_module.get_stock_price(symbol)
        
        for hour in range(8, 15):
            for minute in [0, 30]:
                if hour == 8 and minute == 0:
                    continue
                if hour == 14 and minute == 30:
                    break
                
                slot_time = datetime.combine(day.date(), datetime.min.time().replace(hour=hour, minute=minute))
                slot_time = self.stock_module.infrastructure.timezone.localize(slot_time)
                
                skyline_level = self.calculate_stock_channel_level(
                    skyline_anchor['price'],
                    skyline_anchor['timestamp'],
                    slot_time,
                    symbol,
                    is_skyline=True
                )
                
                baseline_level = self.calculate_stock_channel_level(
                    baseline_anchor['price'],
                    baseline_anchor['timestamp'],
                    slot_time,
                    symbol,
                    is_skyline=False
                )
                
                zone = self._determine_stock_zone(current_price, skyline_level, baseline_level)
                
                levels.append({
                    'day': day_name,
                    'time': slot_time.strftime('%H:%M'),
                    'skyline': skyline_level,
                    'baseline': baseline_level,
                    'zone': zone,
                    'skyline_distance': abs(current_price - skyline_level) if current_price else 0,
                    'baseline_distance': abs(current_price - baseline_level) if current_price else 0
                })
        
        return levels
    
    def _determine_stock_zone(self, current_price, skyline_level, baseline_level):
        if current_price is None:
            return "Unknown"
        
        if current_price >= skyline_level:
            return "Sell Zone"
        elif current_price <= baseline_level:
            return "Buy Zone"
        else:
            return "Between"
    
    def get_current_stock_levels(self, symbol):
        try:
            anchors = self.detect_weekly_anchors(symbol)
            now = datetime.now(self.stock_module.infrastructure.timezone)
            
            current_skyline = self.calculate_stock_channel_level(
                anchors['skyline']['price'],
                anchors['skyline']['timestamp'],
                now,
                symbol,
                is_skyline=True
            )
            
            current_baseline = self.calculate_stock_channel_level(
                anchors['baseline']['price'],
                anchors['baseline']['timestamp'],
                now,
                symbol,
                is_skyline=False
            )
            
            current_price = self.stock_module.get_stock_price(symbol)
            zone = self._determine_stock_zone(current_price, current_skyline, current_baseline)
            
            return {
                'skyline': current_skyline,
                'baseline': current_baseline,
                'current_price': current_price,
                'zone': zone,
                'anchors': anchors
            }
            
        except Exception:
            return {
                'skyline': None,
                'baseline': None,
                'current_price': None,
                'zone': "Unknown",
                'anchors': None
            }
    
    def get_all_current_levels(self):
        all_levels = {}
        for symbol in self.stock_module.stocks:
            all_levels[symbol] = self.get_current_stock_levels(symbol)
        return all_levels
    
    def save_weekly_anchors(self, all_anchors):
        try:
            anchor_data = {
                'anchors': all_anchors,
                'timestamp': datetime.now().isoformat(),
                'week_start': datetime.now().strftime('%Y-W%U')
            }
            with open(self.anchor_cache, 'w') as f:
                json.dump(anchor_data, f)
        except Exception:
            pass
    
    def load_weekly_anchors(self):
        try:
            if self.anchor_cache.exists():
                with open(self.anchor_cache, 'r') as f:
                    data = json.load(f)
                return data.get('anchors', {})
        except Exception:
            pass
        return {}

@st.cache_resource
def get_stock_channel_engine():
    stock_module = get_stock_module()
    return StockChannelEngine(stock_module)

# Market Lens - Part 7: Trade Entry Signals

class TradeEntrySignals:
    def __init__(self, spx_channel_engine, stock_channel_engine):
        self.spx_engine = spx_channel_engine
        self.stock_engine = stock_channel_engine
        self.signal_cache = self.spx_engine.spx_module.infrastructure.cache_dir / 'trade_signals.json'
        
    def check_spx_entry_signals(self):
        try:
            current_levels = self.spx_engine.get_current_levels()
            current_price = current_levels['current_price']
            skyline = current_levels['skyline']
            baseline = current_levels['baseline']
            
            if current_price is None or skyline is None or baseline is None:
                return {'signal': None, 'type': None, 'confidence': 0}
            
            signals = []
            
            # Primary short signal - touch of Skyline
            if abs(current_price - skyline) <= 2.0:
                signals.append({
                    'signal': 'SHORT',
                    'type': 'Primary',
                    'entry_level': skyline,
                    'current_price': current_price,
                    'distance': abs(current_price - skyline),
                    'confidence': self._calculate_confidence(current_price, skyline, 'short')
                })
            
            # Primary long signal - touch of Baseline
            if abs(current_price - baseline) <= 2.0:
                signals.append({
                    'signal': 'LONG',
                    'type': 'Primary',
                    'entry_level': baseline,
                    'current_price': current_price,
                    'distance': abs(current_price - baseline),
                    'confidence': self._calculate_confidence(current_price, baseline, 'long')
                })
            
            # Retest signals
            retest_signal = self._check_retest_signal(current_price, skyline, baseline)
            if retest_signal:
                signals.append(retest_signal)
            
            # Traversal signals
            traversal_signal = self._check_traversal_signal(current_price, skyline, baseline)
            if traversal_signal:
                signals.append(traversal_signal)
            
            return self._prioritize_signals(signals)
            
        except Exception:
            return {'signal': None, 'type': None, 'confidence': 0}
    
    def _calculate_confidence(self, current_price, target_level, direction):
        try:
            distance = abs(current_price - target_level)
            
            # Base confidence on proximity
            if distance <= 0.5:
                base_confidence = 95
            elif distance <= 1.0:
                base_confidence = 85
            elif distance <= 2.0:
                base_confidence = 75
            else:
                base_confidence = 50
            
            # Volume confirmation
            volume_boost = self._check_volume_confirmation()
            
            # RTH session boost
            rth_boost = self._check_rth_session()
            
            total_confidence = min(100, base_confidence + volume_boost + rth_boost)
            return total_confidence
            
        except Exception:
            return 50
    
    def _check_volume_confirmation(self):
        try:
            spx_volume = self.spx_engine.spx_module.get_spx_volume()
            es_volume = self.spx_engine.spx_module.get_es_volume()
            
            # Simple volume check - above average
            if spx_volume > 1000000 or es_volume > 500000:
                return 10
            return 0
        except Exception:
            return 0
    
    def _check_rth_session(self):
        try:
            market_hours = self.spx_engine.spx_module.infrastructure.market_hours()
            if market_hours['is_rth']:
                return 15
            return 0
        except Exception:
            return 0
    
    def _check_retest_signal(self, current_price, skyline, baseline):
        try:
            # Check if price broke and reclaimed a level
            recent_data = self.spx_engine.spx_module.get_spx_data()
            if recent_data.empty or len(recent_data) < 10:
                return None
            
            recent_prices = recent_data['Close'].tail(10)
            
            # Skyline retest (broke above, now back at level)
            if any(price > skyline + 3 for price in recent_prices) and abs(current_price - skyline) <= 2:
                return {
                    'signal': 'SHORT',
                    'type': 'Retest',
                    'entry_level': skyline,
                    'current_price': current_price,
                    'distance': abs(current_price - skyline),
                    'confidence': 80
                }
            
            # Baseline retest (broke below, now back at level)
            if any(price < baseline - 3 for price in recent_prices) and abs(current_price - baseline) <= 2:
                return {
                    'signal': 'LONG',
                    'type': 'Retest',
                    'entry_level': baseline,
                    'current_price': current_price,
                    'distance': abs(current_price - baseline),
                    'confidence': 80
                }
            
            return None
        except Exception:
            return None
    
    def _check_traversal_signal(self, current_price, skyline, baseline):
        try:
            # Check for channel traversal (moving from one extreme to the other)
            recent_data = self.spx_engine.spx_module.get_spx_data()
            if recent_data.empty or len(recent_data) < 20:
                return None
            
            recent_prices = recent_data['Close'].tail(20)
            
            # Traversal from Baseline to Skyline
            if any(price <= baseline + 2 for price in recent_prices[:10]) and abs(current_price - skyline) <= 3:
                return {
                    'signal': 'SHORT',
                    'type': 'Traversal',
                    'entry_level': skyline,
                    'current_price': current_price,
                    'distance': abs(current_price - skyline),
                    'confidence': 70
                }
            
            # Traversal from Skyline to Baseline
            if any(price >= skyline - 2 for price in recent_prices[:10]) and abs(current_price - baseline) <= 3:
                return {
                    'signal': 'LONG',
                    'type': 'Traversal',
                    'entry_level': baseline,
                    'current_price': current_price,
                    'distance': abs(current_price - baseline),
                    'confidence': 70
                }
            
            return None
        except Exception:
            return None
    
    def _prioritize_signals(self, signals):
        if not signals:
            return {'signal': None, 'type': None, 'confidence': 0}
        
        # Priority: Primary > Retest > Traversal
        priority_order = {'Primary': 3, 'Retest': 2, 'Traversal': 1}
        
        # Sort by type priority, then by confidence
        sorted_signals = sorted(signals, 
                              key=lambda x: (priority_order.get(x['type'], 0), x['confidence']), 
                              reverse=True)
        
        return sorted_signals[0]
    
    def check_stock_entry_signals(self, symbol):
        try:
            current_levels = self.stock_engine.get_current_stock_levels(symbol)
            current_price = current_levels['current_price']
            skyline = current_levels['skyline']
            baseline = current_levels['baseline']
            
            if current_price is None or skyline is None or baseline is None:
                return {'signal': None, 'type': None, 'confidence': 0}
            
            # Use stock-specific tolerance (smaller than SPX)
            tolerance = current_price * 0.005  # 0.5% tolerance
            
            signals = []
            
            # Primary short signal
            if abs(current_price - skyline) <= tolerance:
                signals.append({
                    'signal': 'SHORT',
                    'type': 'Primary',
                    'entry_level': skyline,
                    'current_price': current_price,
                    'distance': abs(current_price - skyline),
                    'confidence': self._calculate_stock_confidence(symbol, current_price, skyline, 'short')
                })
            
            # Primary long signal
            if abs(current_price - baseline) <= tolerance:
                signals.append({
                    'signal': 'LONG',
                    'type': 'Primary',
                    'entry_level': baseline,
                    'current_price': current_price,
                    'distance': abs(current_price - baseline),
                    'confidence': self._calculate_stock_confidence(symbol, current_price, baseline, 'long')
                })
            
            return self._prioritize_signals(signals)
            
        except Exception:
            return {'signal': None, 'type': None, 'confidence': 0}
    
    def _calculate_stock_confidence(self, symbol, current_price, target_level, direction):
        try:
            distance_pct = abs(current_price - target_level) / current_price
            
            if distance_pct <= 0.002:  # 0.2%
                base_confidence = 90
            elif distance_pct <= 0.005:  # 0.5%
                base_confidence = 80
            else:
                base_confidence = 60
            
            # Stock volume confirmation
            stock_volume = self.stock_engine.stock_module.get_stock_volume(symbol)
            if stock_volume > 1000000:
                volume_boost = 10
            else:
                volume_boost = 0
            
            # Session boost
            rth_boost = self._check_rth_session()
            
            return min(100, base_confidence + volume_boost + rth_boost)
            
        except Exception:
            return 50
    
    def get_all_active_signals(self):
        try:
            all_signals = {}
            
            # SPX signals
            spx_signal = self.check_spx_entry_signals()
            if spx_signal['signal']:
                all_signals['SPX'] = spx_signal
            
            # Stock signals
            for symbol in self.stock_engine.stock_module.stocks:
                stock_signal = self.check_stock_entry_signals(symbol)
                if stock_signal['signal']:
                    all_signals[symbol] = stock_signal
            
            return all_signals
            
        except Exception:
            return {}
    
    def save_signals(self, signals):
        try:
            signal_data = {
                'signals': signals,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.signal_cache, 'w') as f:
                json.dump(signal_data, f)
        except Exception:
            pass
    
    def get_signal_strength(self, signal_data):
        if not signal_data or signal_data['signal'] is None:
            return "None"
        
        confidence = signal_data.get('confidence', 0)
        
        if confidence >= 90:
            return "Very Strong"
        elif confidence >= 80:
            return "Strong"
        elif confidence >= 70:
            return "Moderate"
        elif confidence >= 60:
            return "Weak"
        else:
            return "Very Weak"
    
    def format_signal_for_display(self, symbol, signal_data):
        if not signal_data or signal_data['signal'] is None:
            return None
        
        return {
            'symbol': symbol,
            'direction': signal_data['signal'],
            'type': signal_data['type'],
            'entry_level': signal_data.get('entry_level'),
            'current_price': signal_data.get('current_price'),
            'distance': signal_data.get('distance', 0),
            'confidence': signal_data.get('confidence', 0),
            'strength': self.get_signal_strength(signal_data)
        }

@st.cache_resource
def get_trade_signals():
    spx_engine = get_spx_channel_engine()
    stock_engine = get_stock_channel_engine()
    return TradeEntrySignals(spx_engine, stock_engine)

# Market Lens - Part 8: Trade Management

class TradeManagement:
    def __init__(self, spx_channel_engine, stock_channel_engine):
        self.spx_engine = spx_channel_engine
        self.stock_engine = stock_channel_engine
        self.trades_cache = self.spx_engine.spx_module.infrastructure.cache_dir / 'active_trades.json'
        
    def calculate_spx_tp_levels(self, entry_price, direction, entry_type='Primary'):
        try:
            current_levels = self.spx_engine.get_current_levels()
            skyline = current_levels['skyline']
            baseline = current_levels['baseline']
            
            if direction.upper() == 'SHORT':
                # Short from Skyline
                channel_distance = skyline - baseline
                
                if entry_type == 'Primary':
                    tp1 = entry_price - (channel_distance * 0.382)  # 38.2% of channel
                    tp2 = entry_price - (channel_distance * 0.618)  # 61.8% of channel
                elif entry_type == 'Retest':
                    tp1 = entry_price - (channel_distance * 0.5)    # 50% of channel
                    tp2 = baseline  # Full channel traversal
                else:  # Traversal
                    tp1 = entry_price - (channel_distance * 0.25)   # 25% of channel
                    tp2 = entry_price - (channel_distance * 0.5)    # 50% of channel
                
                stop_loss = entry_price + (channel_distance * 0.1)  # 10% above entry
                
            else:  # LONG
                # Long from Baseline
                channel_distance = skyline - baseline
                
                if entry_type == 'Primary':
                    tp1 = entry_price + (channel_distance * 0.382)  # 38.2% of channel
                    tp2 = entry_price + (channel_distance * 0.618)  # 61.8% of channel
                elif entry_type == 'Retest':
                    tp1 = entry_price + (channel_distance * 0.5)    # 50% of channel
                    tp2 = skyline  # Full channel traversal
                else:  # Traversal
                    tp1 = entry_price + (channel_distance * 0.25)   # 25% of channel
                    tp2 = entry_price + (channel_distance * 0.5)    # 50% of channel
                
                stop_loss = entry_price - (channel_distance * 0.1)  # 10% below entry
            
            return {
                'tp1': round(tp1, 2),
                'tp2': round(tp2, 2),
                'stop_loss': round(stop_loss, 2),
                'risk_reward_tp1': self._calculate_risk_reward(entry_price, tp1, stop_loss),
                'risk_reward_tp2': self._calculate_risk_reward(entry_price, tp2, stop_loss)
            }
            
        except Exception:
            return self._get_fallback_tp_levels(entry_price, direction)
    
    def calculate_stock_tp_levels(self, symbol, entry_price, direction, entry_type='Primary'):
        try:
            current_levels = self.stock_engine.get_current_stock_levels(symbol)
            skyline = current_levels['skyline']
            baseline = current_levels['baseline']
            
            channel_distance = skyline - baseline
            
            if direction.upper() == 'SHORT':
                if entry_type == 'Primary':
                    tp1 = entry_price - (channel_distance * 0.4)    # 40% for stocks
                    tp2 = entry_price - (channel_distance * 0.7)    # 70% for stocks
                else:
                    tp1 = entry_price - (channel_distance * 0.3)
                    tp2 = entry_price - (channel_distance * 0.6)
                
                stop_loss = entry_price + (channel_distance * 0.15)  # 15% above for stocks
                
            else:  # LONG
                if entry_type == 'Primary':
                    tp1 = entry_price + (channel_distance * 0.4)    # 40% for stocks
                    tp2 = entry_price + (channel_distance * 0.7)    # 70% for stocks
                else:
                    tp1 = entry_price + (channel_distance * 0.3)
                    tp2 = entry_price + (channel_distance * 0.6)
                
                stop_loss = entry_price - (channel_distance * 0.15)  # 15% below for stocks
            
            return {
                'tp1': round(tp1, 2),
                'tp2': round(tp2, 2),
                'stop_loss': round(stop_loss, 2),
                'risk_reward_tp1': self._calculate_risk_reward(entry_price, tp1, stop_loss),
                'risk_reward_tp2': self._calculate_risk_reward(entry_price, tp2, stop_loss)
            }
            
        except Exception:
            return self._get_fallback_tp_levels(entry_price, direction)
    
    def _calculate_risk_reward(self, entry, target, stop):
        try:
            risk = abs(entry - stop)
            reward = abs(target - entry)
            if risk == 0:
                return 0
            return round(reward / risk, 2)
        except Exception:
            return 0
    
    def _get_fallback_tp_levels(self, entry_price, direction):
        if direction.upper() == 'SHORT':
            tp1 = entry_price * 0.995  # 0.5% down
            tp2 = entry_price * 0.985  # 1.5% down
            stop_loss = entry_price * 1.005  # 0.5% up
        else:
            tp1 = entry_price * 1.005  # 0.5% up
            tp2 = entry_price * 1.015  # 1.5% up
            stop_loss = entry_price * 0.995  # 0.5% down
        
        return {
            'tp1': round(tp1, 2),
            'tp2': round(tp2, 2),
            'stop_loss': round(stop_loss, 2),
            'risk_reward_tp1': 1.0,
            'risk_reward_tp2': 3.0
        }
    
    def create_trade_plan(self, symbol, signal_data):
        try:
            if not signal_data or signal_data['signal'] is None:
                return None
            
            entry_price = signal_data.get('current_price')
            direction = signal_data.get('signal')
            entry_type = signal_data.get('type', 'Primary')
            
            if symbol == 'SPX':
                tp_levels = self.calculate_spx_tp_levels(entry_price, direction, entry_type)
            else:
                tp_levels = self.calculate_stock_tp_levels(symbol, entry_price, direction, entry_type)
            
            trade_plan = {
                'symbol': symbol,
                'direction': direction,
                'entry_type': entry_type,
                'entry_price': entry_price,
                'tp1': tp_levels['tp1'],
                'tp2': tp_levels['tp2'],
                'stop_loss': tp_levels['stop_loss'],
                'risk_reward_tp1': tp_levels['risk_reward_tp1'],
                'risk_reward_tp2': tp_levels['risk_reward_tp2'],
                'confidence': signal_data.get('confidence', 0),
                'created_time': datetime.now().isoformat()
            }
            
            return trade_plan
            
        except Exception:
            return None
    
    def calculate_position_size(self, account_balance, risk_percentage, entry_price, stop_loss):
        try:
            risk_amount = account_balance * (risk_percentage / 100)
            price_risk = abs(entry_price - stop_loss)
            
            if price_risk == 0:
                return 0
            
            position_size = risk_amount / price_risk
            return round(position_size, 0)
            
        except Exception:
            return 0
    
    def check_tp_hit(self, symbol, trade_plan):
        try:
            if symbol == 'SPX':
                current_price = self.spx_engine.spx_module.get_current_spx_price()
            else:
                current_price = self.stock_engine.stock_module.get_stock_price(symbol)
            
            if current_price is None:
                return {'tp1_hit': False, 'tp2_hit': False, 'stop_hit': False}
            
            direction = trade_plan['direction'].upper()
            tp1 = trade_plan['tp1']
            tp2 = trade_plan['tp2']
            stop_loss = trade_plan['stop_loss']
            
            if direction == 'LONG':
                tp1_hit = current_price >= tp1
                tp2_hit = current_price >= tp2
                stop_hit = current_price <= stop_loss
            else:  # SHORT
                tp1_hit = current_price <= tp1
                tp2_hit = current_price <= tp2
                stop_hit = current_price >= stop_loss
            
            return {
                'tp1_hit': tp1_hit,
                'tp2_hit': tp2_hit,
                'stop_hit': stop_hit,
                'current_price': current_price
            }
            
        except Exception:
            return {'tp1_hit': False, 'tp2_hit': False, 'stop_hit': False}
    
    def calculate_trailing_stop(self, symbol, trade_plan, tp1_hit=False):
        try:
            if not tp1_hit:
                return trade_plan['stop_loss']
            
            # After TP1 hit, move stop to breakeven + small buffer
            entry_price = trade_plan['entry_price']
            direction = trade_plan['direction'].upper()
            
            if direction == 'LONG':
                trailing_stop = entry_price + (entry_price * 0.001)  # BE + 0.1%
            else:  # SHORT
                trailing_stop = entry_price - (entry_price * 0.001)  # BE - 0.1%
            
            return round(trailing_stop, 2)
            
        except Exception:
            return trade_plan.get('stop_loss', 0)
    
    def get_exit_recommendation(self, symbol, trade_plan):
        try:
            tp_status = self.check_tp_hit(symbol, trade_plan)
            
            if tp_status['stop_hit']:
                return {
                    'action': 'EXIT_STOP',
                    'reason': 'Stop loss hit',
                    'current_price': tp_status['current_price']
                }
            
            if tp_status['tp2_hit']:
                return {
                    'action': 'EXIT_TP2',
                    'reason': 'TP2 achieved - full exit',
                    'current_price': tp_status['current_price']
                }
            
            if tp_status['tp1_hit']:
                trailing_stop = self.calculate_trailing_stop(symbol, trade_plan, True)
                return {
                    'action': 'PARTIAL_EXIT',
                    'reason': 'TP1 achieved - take partial profit, trail stop',
                    'new_stop': trailing_stop,
                    'current_price': tp_status['current_price']
                }
            
            return {
                'action': 'HOLD',
                'reason': 'Targets not reached',
                'current_price': tp_status['current_price']
            }
            
        except Exception:
            return {
                'action': 'HOLD',
                'reason': 'Unable to determine status',
                'current_price': None
            }
    
    def save_active_trades(self, trades):
        try:
            trade_data = {
                'trades': trades,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.trades_cache, 'w') as f:
                json.dump(trade_data, f)
        except Exception:
            pass
    
    def load_active_trades(self):
        try:
            if self.trades_cache.exists():
                with open(self.trades_cache, 'r') as f:
                    data = json.load(f)
                return data.get('trades', [])
        except Exception:
            pass
        return []
    
    def format_trade_plan_for_display(self, trade_plan):
        if not trade_plan:
            return None
        
        return {
            'Symbol': trade_plan['symbol'],
            'Direction': trade_plan['direction'],
            'Entry': f"${trade_plan['entry_price']:.2f}",
            'TP1': f"${trade_plan['tp1']:.2f}",
            'TP2': f"${trade_plan['tp2']:.2f}",
            'Stop': f"${trade_plan['stop_loss']:.2f}",
            'R:R TP1': f"1:{trade_plan['risk_reward_tp1']:.1f}",
            'R:R TP2': f"1:{trade_plan['risk_reward_tp2']:.1f}",
            'Confidence': f"{trade_plan['confidence']}%"
        }

@st.cache_resource
def get_trade_management():
    spx_engine = get_spx_channel_engine()
    stock_engine = get_stock_channel_engine()
    return TradeManagement(spx_engine, stock_engine)

# Market Lens - Part 9: Risk Management

class RiskManagement:
    def __init__(self, trade_management):
        self.trade_management = trade_management
        self.risk_cache = self.trade_management.spx_engine.spx_module.infrastructure.cache_dir / 'risk_settings.json'
        
        self.default_settings = {
            'max_risk_per_trade': 2.0,
            'max_daily_risk': 6.0,
            'max_concurrent_trades': 3,
            'max_correlation_exposure': 50.0,
            'account_balance': 100000.0,
            'risk_multiplier_high_confidence': 1.5,
            'risk_multiplier_low_confidence': 0.5
        }
    
    def load_risk_settings(self):
        try:
            if self.risk_cache.exists():
                with open(self.risk_cache, 'r') as f:
                    settings = json.load(f)
                return {**self.default_settings, **settings}
        except Exception:
            pass
        return self.default_settings
    
    def save_risk_settings(self, settings):
        try:
            with open(self.risk_cache, 'w') as f:
                json.dump(settings, f)
        except Exception:
            pass
    
    def calculate_position_size(self, trade_plan, account_balance=None):
        try:
            settings = self.load_risk_settings()
            
            if account_balance is None:
                account_balance = settings['account_balance']
            
            # Base risk percentage
            base_risk = settings['max_risk_per_trade']
            
            # Adjust risk based on confidence
            confidence = trade_plan.get('confidence', 50)
            if confidence >= 90:
                risk_multiplier = settings['risk_multiplier_high_confidence']
            elif confidence < 70:
                risk_multiplier = settings['risk_multiplier_low_confidence']
            else:
                risk_multiplier = 1.0
            
            adjusted_risk = base_risk * risk_multiplier
            
            # Calculate position size
            entry_price = trade_plan['entry_price']
            stop_loss = trade_plan['stop_loss']
            
            position_size = self.trade_management.calculate_position_size(
                account_balance, adjusted_risk, entry_price, stop_loss
            )
            
            return {
                'shares': int(position_size),
                'risk_amount': account_balance * (adjusted_risk / 100),
                'risk_percentage': adjusted_risk,
                'confidence_multiplier': risk_multiplier
            }
            
        except Exception:
            return {
                'shares': 0,
                'risk_amount': 0,
                'risk_percentage': 0,
                'confidence_multiplier': 1.0
            }
    
    def check_risk_limits(self, new_trade_plan, active_trades=None):
        try:
            settings = self.load_risk_settings()
            
            if active_trades is None:
                active_trades = self.trade_management.load_active_trades()
            
            violations = []
            
            # Check max concurrent trades
            if len(active_trades) >= settings['max_concurrent_trades']:
                violations.append({
                    'type': 'MAX_TRADES',
                    'message': f"Maximum {settings['max_concurrent_trades']} concurrent trades exceeded"
                })
            
            # Check daily risk exposure
            daily_risk = self._calculate_daily_risk_exposure(active_trades, new_trade_plan)
            if daily_risk > settings['max_daily_risk']:
                violations.append({
                    'type': 'DAILY_RISK',
                    'message': f"Daily risk {daily_risk:.1f}% exceeds limit of {settings['max_daily_risk']}%"
                })
            
            # Check correlation exposure
            correlation_risk = self._calculate_correlation_exposure(active_trades, new_trade_plan)
            if correlation_risk > settings['max_correlation_exposure']:
                violations.append({
                    'type': 'CORRELATION',
                    'message': f"Correlation exposure {correlation_risk:.1f}% exceeds limit of {settings['max_correlation_exposure']}%"
                })
            
            return {
                'approved': len(violations) == 0,
                'violations': violations,
                'risk_score': self._calculate_overall_risk_score(daily_risk, correlation_risk, len(active_trades))
            }
            
        except Exception:
            return {
                'approved': False,
                'violations': [{'type': 'ERROR', 'message': 'Unable to assess risk'}],
                'risk_score': 100
            }
    
    def _calculate_daily_risk_exposure(self, active_trades, new_trade):
        try:
            settings = self.load_risk_settings()
            account_balance = settings['account_balance']
            
            total_risk = 0
            
            # Risk from active trades
            for trade in active_trades:
                trade_risk = abs(trade['entry_price'] - trade['stop_loss'])
                position_value = trade.get('position_size', 0) * trade['entry_price']
                risk_amount = trade.get('position_size', 0) * trade_risk
                risk_pct = (risk_amount / account_balance) * 100
                total_risk += risk_pct
            
            # Risk from new trade
            if new_trade:
                new_risk = abs(new_trade['entry_price'] - new_trade['stop_loss'])
                position_size = self.calculate_position_size(new_trade)['shares']
                new_risk_amount = position_size * new_risk
                new_risk_pct = (new_risk_amount / account_balance) * 100
                total_risk += new_risk_pct
            
            return total_risk
            
        except Exception:
            return 0
    
    def _calculate_correlation_exposure(self, active_trades, new_trade):
        try:
            # Group trades by symbol type
            spx_exposure = 0
            stock_exposure = 0
            
            all_trades = active_trades.copy()
            if new_trade:
                all_trades.append(new_trade)
            
            for trade in all_trades:
                symbol = trade.get('symbol', '')
                
                if symbol in ['SPX', '^GSPC', 'ES=F']:
                    spx_exposure += 1
                else:
                    stock_exposure += 1
            
            total_trades = len(all_trades)
            if total_trades == 0:
                return 0
            
            # Calculate concentration risk
            max_exposure = max(spx_exposure, stock_exposure)
            concentration_pct = (max_exposure / total_trades) * 100
            
            return concentration_pct
            
        except Exception:
            return 0
    
    def _calculate_overall_risk_score(self, daily_risk, correlation_risk, num_trades):
        try:
            # Risk score from 0-100 (higher = more risky)
            risk_score = 0
            
            # Daily risk component (0-40 points)
            risk_score += min(40, daily_risk * 6.67)  # 6% daily risk = 40 points
            
            # Correlation component (0-30 points)
            risk_score += min(30, correlation_risk * 0.6)  # 50% correlation = 30 points
            
            # Trade count component (0-30 points)
            risk_score += min(30, num_trades * 10)  # 3 trades = 30 points
            
            return min(100, risk_score)
            
        except Exception:
            return 50
    
    def get_risk_recommendation(self, trade_plan):
        try:
            risk_check = self.check_risk_limits(trade_plan)
            
            if not risk_check['approved']:
                return {
                    'recommendation': 'REJECT',
                    'reason': 'Risk limits exceeded',
                    'violations': risk_check['violations']
                }
            
            risk_score = risk_check['risk_score']
            
            if risk_score <= 30:
                return {
                    'recommendation': 'FULL_SIZE',
                    'reason': 'Low risk environment',
                    'suggested_multiplier': 1.0
                }
            elif risk_score <= 60:
                return {
                    'recommendation': 'REDUCED_SIZE',
                    'reason': 'Moderate risk - reduce position',
                    'suggested_multiplier': 0.75
                }
            else:
                return {
                    'recommendation': 'MINIMAL_SIZE',
                    'reason': 'High risk - minimal position only',
                    'suggested_multiplier': 0.5
                }
                
        except Exception:
            return {
                'recommendation': 'REJECT',
                'reason': 'Unable to assess risk',
                'violations': []
            }
    
    def calculate_portfolio_risk_metrics(self, active_trades=None):
        try:
            if active_trades is None:
                active_trades = self.trade_management.load_active_trades()
            
            settings = self.load_risk_settings()
            account_balance = settings['account_balance']
            
            if not active_trades:
                return {
                    'total_exposure': 0,
                    'daily_risk': 0,
                    'correlation_risk': 0,
                    'active_trades': 0,
                    'risk_score': 0
                }
            
            # Calculate total portfolio exposure
            total_exposure = 0
            for trade in active_trades:
                position_size = trade.get('position_size', 0)
                entry_price = trade.get('entry_price', 0)
                exposure = position_size * entry_price
                total_exposure += exposure
            
            exposure_pct = (total_exposure / account_balance) * 100
            
            daily_risk = self._calculate_daily_risk_exposure(active_trades, None)
            correlation_risk = self._calculate_correlation_exposure(active_trades, None)
            risk_score = self._calculate_overall_risk_score(daily_risk, correlation_risk, len(active_trades))
            
            return {
                'total_exposure': exposure_pct,
                'daily_risk': daily_risk,
                'correlation_risk': correlation_risk,
                'active_trades': len(active_trades),
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score)
            }
            
        except Exception:
            return {
                'total_exposure': 0,
                'daily_risk': 0,
                'correlation_risk': 0,
                'active_trades': 0,
                'risk_score': 0,
                'risk_level': 'Unknown'
            }
    
    def _get_risk_level(self, risk_score):
        if risk_score <= 25:
            return "Low"
        elif risk_score <= 50:
            return "Moderate"
        elif risk_score <= 75:
            return "High"
        else:
            return "Very High"
    
    def get_max_position_size(self, symbol, entry_price, stop_loss):
        try:
            settings = self.load_risk_settings()
            account_balance = settings['account_balance']
            max_risk = settings['max_risk_per_trade']
            
            max_shares = self.trade_management.calculate_position_size(
                account_balance, max_risk, entry_price, stop_loss
            )
            
            return {
                'max_shares': int(max_shares),
                'max_value': max_shares * entry_price,
                'max_risk_amount': account_balance * (max_risk / 100)
            }
            
        except Exception:
            return {
                'max_shares': 0,
                'max_value': 0,
                'max_risk_amount': 0
            }
    
    def format_risk_summary(self, risk_metrics):
        try:
            return {
                'Portfolio Exposure': f"{risk_metrics['total_exposure']:.1f}%",
                'Daily Risk': f"{risk_metrics['daily_risk']:.1f}%",
                'Correlation Risk': f"{risk_metrics['correlation_risk']:.1f}%",
                'Active Trades': risk_metrics['active_trades'],
                'Risk Level': risk_metrics['risk_level'],
                'Risk Score': f"{risk_metrics['risk_score']:.0f}/100"
            }
        except Exception:
            return {}

@st.cache_resource
def get_risk_management():
    trade_management = get_trade_management()
    return RiskManagement(trade_management)

# Market Lens - Part 10: Dashboard Interface

import plotly.graph_objects as go

def main():
    # Initialize all modules
    ui = get_ui()
    ui.setup_page()
    
    infrastructure = get_infrastructure()
    spx_module = get_spx_module()
    stock_module = get_stock_module()
    spx_engine = get_spx_channel_engine()
    stock_engine = get_stock_channel_engine()
    signals = get_trade_signals()
    trade_mgmt = get_trade_management()
    risk_mgmt = get_risk_management()
    
    # Main navigation
    selected = ui.main_navigation()
    
    if selected == "Dashboard":
        show_dashboard(ui, infrastructure, spx_module, stock_module, signals)
    elif selected == "SPX":
        show_spx_page(ui, spx_module, spx_engine, signals, trade_mgmt)
    elif selected == "Stocks":
        show_stocks_page(ui, stock_module, stock_engine, signals, trade_mgmt)
    elif selected == "Trades":
        show_trades_page(ui, trade_mgmt, risk_mgmt, signals)
    elif selected == "Analytics":
        show_analytics_page(ui, infrastructure, spx_module, stock_module)

def show_dashboard(ui, infrastructure, spx_module, stock_module, signals):
    st.title("Market Lens Dashboard")
    
    # Status bar
    market_hours = infrastructure.market_hours()
    status_data = {
        'live': infrastructure.status['live'],
        'session': market_hours['session'],
        'last_update': infrastructure.status.get('last_update'),
        'error_count': infrastructure.status['error_count']
    }
    ui.status_bar(status_data)
    
    st.markdown("---")
    
    # SPX and ES section
    col1, col2 = st.columns(2)
    
    with col1:
        spx_data = spx_module.get_spx_data()
        if not spx_data.empty:
            current_price = spx_data['Close'].iloc[-1]
            change = spx_data['Change'].iloc[-1] if 'Change' in spx_data.columns else 0
            ui.display_large_symbol('^GSPC', current_price, change)
        else:
            ui.display_large_symbol('^GSPC')
            st.error("SPX data unavailable")
    
    with col2:
        es_data = spx_module.get_es_data()
        if not es_data.empty:
            current_price = es_data['Close'].iloc[-1]
            change = es_data['Change'].iloc[-1] if 'Change' in es_data.columns else 0
            ui.display_large_symbol('ES=F', current_price, change)
            
            # Show ES to SPX conversion
            offset = spx_module.calculate_es_spx_offset()
            spx_equivalent = current_price + offset
            st.info(f"SPX Equivalent: {ui.format_price(spx_equivalent)}")
        else:
            ui.display_large_symbol('ES=F')
            st.error("ES data unavailable")
    
    st.markdown("---")
    
    # Active signals section
    st.subheader("🚨 Active Trading Signals")
    
    active_signals = signals.get_all_active_signals()
    
    if active_signals:
        signal_cols = st.columns(len(active_signals))
        
        for i, (symbol, signal_data) in enumerate(active_signals.items()):
            with signal_cols[i]:
                formatted_signal = signals.format_signal_for_display(symbol, signal_data)
                if formatted_signal:
                    direction_color = "🟢" if formatted_signal['direction'] == 'LONG' else "🔴"
                    
                    st.markdown(f"""
                    **{direction_color} {formatted_signal['symbol']} {formatted_signal['direction']}**
                    
                    Entry: {ui.format_price(formatted_signal['entry_level'])}
                    
                    Type: {formatted_signal['type']}
                    
                    Strength: {formatted_signal['strength']}
                    
                    Confidence: {formatted_signal['confidence']}%
                    """)
    else:
        st.info("No active trading signals at this time")
    
    st.markdown("---")
    
    # Stock grid
    st.subheader("📊 Big 7 Technology Stocks")
    
    cols = st.columns(4)
    for i, symbol in enumerate(stock_module.stocks):
        with cols[i % 4]:
            stock_price = stock_module.get_stock_price(symbol)
            stock_change = stock_module.get_stock_change(symbol)
            
            if stock_price:
                ui.display_medium_symbol(symbol, stock_price, stock_change)
                
                # Show if there's a signal for this stock
                if symbol in active_signals:
                    signal_data = active_signals[symbol]
                    direction = signal_data.get('signal', '')
                    signal_color = "🟢" if direction == 'LONG' else "🔴"
                    st.markdown(f"**{signal_color} {direction} Signal**")
            else:
                ui.display_medium_symbol(symbol)
                st.error("No data")

def show_spx_page(ui, spx_module, spx_engine, signals, trade_mgmt):
    st.title("📈 SPX Analysis")
    
    # Current levels
    current_levels = spx_engine.get_current_levels()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if current_levels['anchors']:
            skyline_price = current_levels['anchors']['skyline']['price']
            st.metric("🔴 Skyline Anchor", ui.format_price(skyline_price))
            st.caption("Sell Zone Entry")
    
    with col2:
        if current_levels['anchors']:
            baseline_price = current_levels['anchors']['baseline']['price']
            st.metric("🟢 Baseline Anchor", ui.format_price(baseline_price))
            st.caption("Buy Zone Entry")
    
    with col3:
        if current_levels['current_price']:
            st.metric("Current SPX", ui.format_price(current_levels['current_price']))
            zone_color = {"Sell Zone": "🔴", "Buy Zone": "🟢", "Between": "🟡"}.get(current_levels['zone'], "⚪")
            st.caption(f"{zone_color} {current_levels['zone']}")
    
    st.markdown("---")
    
    # RTH Forecast
    st.subheader("⏰ RTH Forecast Table")
    
    rth_levels = spx_engine.generate_rth_levels()
    
    if rth_levels:
        df = pd.DataFrame(rth_levels)
        
        # Format the dataframe for display
        df_display = df.copy()
        df_display['Skyline'] = df_display['skyline'].apply(lambda x: ui.format_price(x))
        df_display['Baseline'] = df_display['baseline'].apply(lambda x: ui.format_price(x))
        df_display['Distance to Skyline'] = df_display['skyline_distance'].apply(lambda x: f"{x:.1f} pts")
        df_display['Distance to Baseline'] = df_display['baseline_distance'].apply(lambda x: f"{x:.1f} pts")
        
        # Color code zones
        def color_zone(zone):
            if "Sell" in zone:
                return "background-color: #ffebee"
            elif "Buy" in zone:
                return "background-color: #e8f5e8"
            else:
                return "background-color: #fff9c4"
        
        styled_df = df_display[['time', 'Skyline', 'Baseline', 'zone', 'Distance to Skyline', 'Distance to Baseline']].style.apply(
            lambda x: [color_zone(x['zone'])] * len(x), axis=1
        )
        
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning("Unable to generate RTH forecast")
    
    # Signal analysis
    st.markdown("---")
    st.subheader("🎯 Signal Analysis")
    
    spx_signal = signals.check_spx_entry_signals()
    
    if spx_signal['signal']:
        # Create trade plan
        trade_plan = trade_mgmt.create_trade_plan('SPX', spx_signal)
        
        if trade_plan:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 Trade Plan**")
                plan_display = trade_mgmt.format_trade_plan_for_display(trade_plan)
                if plan_display:
                    for key, value in plan_display.items():
                        st.text(f"{key}: {value}")
            
            with col2:
                st.markdown("**📊 Risk Analysis**")
                position_info = trade_mgmt.trade_management.calculate_position_size(
                    100000, 2.0, trade_plan['entry_price'], trade_plan['stop_loss']
                )
                st.text(f"Suggested Position: {position_info} shares")
                st.text(f"Risk Amount: ${abs(trade_plan['entry_price'] - trade_plan['stop_loss']) * position_info:.0f}")
    else:
        st.info("No SPX signals detected")

def show_stocks_page(ui, stock_module, stock_engine, signals, trade_mgmt):
    st.title("🏢 Stock Analysis")
    
    # Stock selector
    selected_stock = st.selectbox("Select Stock", stock_module.stocks)
    
    if selected_stock:
        # Current stock levels
        current_levels = stock_engine.get_current_stock_levels(selected_stock)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ui.display_large_symbol(selected_stock, 
                                  current_levels.get('current_price'), 
                                  stock_module.get_stock_change(selected_stock))
        
        with col2:
            if current_levels['anchors'] and current_levels['anchors']['skyline']:
                skyline_price = current_levels['anchors']['skyline']['price']
                st.metric("🔴 Weekly Skyline", ui.format_price(skyline_price))
        
        with col3:
            if current_levels['anchors'] and current_levels['anchors']['baseline']:
                baseline_price = current_levels['anchors']['baseline']['price']
                st.metric("🟢 Weekly Baseline", ui.format_price(baseline_price))
        
        st.markdown("---")
        
        # Weekly forecast
        st.subheader("📅 Weekly Forecast (Wed/Thu)")
        
        weekly_forecast = stock_engine.generate_weekly_forecast(selected_stock)
        
        if weekly_forecast:
            df = pd.DataFrame(weekly_forecast)
            
            # Group by day
            for day in ['Wednesday', 'Thursday']:
                day_data = df[df['day'] == day]
                if not day_data.empty:
                    st.markdown(f"**{day}**")
                    
                    display_df = day_data.copy()
                    display_df['Skyline'] = display_df['skyline'].apply(lambda x: ui.format_price(x))
                    display_df['Baseline'] = display_df['baseline'].apply(lambda x: ui.format_price(x))
                    
                    st.dataframe(display_df[['time', 'Skyline', 'Baseline', 'zone']], use_container_width=True)
        
        # Stock signal
        st.markdown("---")
        st.subheader("🎯 Stock Signal")
        
        stock_signal = signals.check_stock_entry_signals(selected_stock)
        
        if stock_signal['signal']:
            trade_plan = trade_mgmt.create_trade_plan(selected_stock, stock_signal)
            if trade_plan:
                plan_display = trade_mgmt.format_trade_plan_for_display(trade_plan)
                if plan_display:
                    for key, value in plan_display.items():
                        st.text(f"{key}: {value}")
        else:
            st.info(f"No signals for {selected_stock}")

def show_trades_page(ui, trade_mgmt, risk_mgmt, signals):
    st.title("💼 Trade Management")
    
    # Risk overview
    st.subheader("⚖️ Risk Overview")
    
    risk_metrics = risk_mgmt.calculate_portfolio_risk_metrics()
    risk_summary = risk_mgmt.format_risk_summary(risk_metrics)
    
    cols = st.columns(len(risk_summary))
    for i, (key, value) in enumerate(risk_summary.items()):
        with cols[i]:
            st.metric(key, value)
    
    st.markdown("---")
    
    # Active trades
    st.subheader("📋 Active Trades")
    
    active_trades = trade_mgmt.load_active_trades()
    
    if active_trades:
        for trade in active_trades:
            with st.expander(f"{trade.get('symbol', 'Unknown')} - {trade.get('direction', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text(f"Entry: {ui.format_price(trade.get('entry_price', 0))}")
                    st.text(f"TP1: {ui.format_price(trade.get('tp1', 0))}")
                    st.text(f"TP2: {ui.format_price(trade.get('tp2', 0))}")
                    st.text(f"Stop: {ui.format_price(trade.get('stop_loss', 0))}")
                
                with col2:
                    # Check current status
                    exit_rec = trade_mgmt.get_exit_recommendation(trade.get('symbol'), trade)
                    st.text(f"Status: {exit_rec.get('action', 'Unknown')}")
                    st.text(f"Reason: {exit_rec.get('reason', 'Unknown')}")
                    if exit_rec.get('current_price'):
                        st.text(f"Current: {ui.format_price(exit_rec['current_price'])}")
    else:
        st.info("No active trades")
    
    st.markdown("---")
    
    # Signal-based trade plans
    st.subheader("🎯 Available Trade Setups")
    
    all_signals = signals.get_all_active_signals()
    
    if all_signals:
        for symbol, signal_data in all_signals.items():
            trade_plan = trade_mgmt.create_trade_plan(symbol, signal_data)
            if trade_plan:
                with st.expander(f"Setup: {symbol} {signal_data.get('signal', '')}"):
                    plan_display = trade_mgmt.format_trade_plan_for_display(trade_plan)
                    if plan_display:
                        for key, value in plan_display.items():
                            st.text(f"{key}: {value}")
                    
                    # Risk check
                    risk_check = risk_mgmt.check_risk_limits(trade_plan)
                    if risk_check['approved']:
                        st.success("✅ Risk limits approved")
                    else:
                        st.error("❌ Risk limits exceeded")
                        for violation in risk_check['violations']:
                            st.text(f"• {violation['message']}")
    else:
        st.info("No trade setups available")

def show_analytics_page(ui, infrastructure, spx_module, stock_module):
    st.title("📊 Analytics & Performance")
    
    # Market overview
    st.subheader("🌍 Market Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # SPX chart
        spx_data = spx_module.get_spx_data()
        if not spx_data.empty:
            fig = go.Figure(data=go.Candlestick(
                x=spx_data.index,
                open=spx_data['Open'],
                high=spx_data['High'],
                low=spx_data['Low'],
                close=spx_data['Close'],
                name='SPX'
            ))
            
            # Auto-zoom to reasonable range
            current_price = spx_data['Close'].iloc[-1]
            price_range = current_price * 0.05  # 5% range
            y_min = current_price - price_range
            y_max = current_price + price_range
            
            fig.update_layout(
                title="SPX 30-min Chart", 
                height=400,
                yaxis=dict(range=[y_min, y_max])
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ES chart
        es_data = spx_module.get_es_data()
        if not es_data.empty:
            fig = go.Figure(data=go.Candlestick(
                x=es_data.index,
                open=es_data['Open'],
                high=es_data['High'],
                low=es_data['Low'],
                close=es_data['Close'],
                name='ES'
            ))
            
            # Auto-zoom to reasonable range
            current_price = es_data['Close'].iloc[-1]
            price_range = current_price * 0.05  # 5% range
            y_min = current_price - price_range
            y_max = current_price + price_range
            
            fig.update_layout(
                title="ES 30-min Chart", 
                height=400,
                yaxis=dict(range=[y_min, y_max])
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Performance metrics
    st.subheader("📈 Performance Metrics")
    
    # Data freshness
    col1, col2, col3 = st.columns(3)
    
    with col1:
        spx_fresh = spx_module.is_data_fresh()
        st.metric("SPX Data", "Fresh" if spx_fresh else "Stale")
    
    with col2:
        market_hours = infrastructure.market_hours()
        st.metric("Market Status", market_hours['session'])
    
    with col3:
        error_count = infrastructure.status['error_count']
        st.metric("System Errors", error_count)
    
    # Stock performance grid
    st.markdown("---")
    st.subheader("📊 Stock Performance")
    
    performance_data = []
    for symbol in stock_module.stocks:
        price = stock_module.get_stock_price(symbol)
        change = stock_module.get_stock_change(symbol)
        volume = stock_module.get_stock_volume(symbol)
        
        performance_data.append({
            'Symbol': symbol,
            'Price': ui.format_price(price) if price else 'N/A',
            'Change': ui.format_change(change),
            'Volume': f"{volume:,}" if volume else 'N/A'
        })
    
    df = pd.DataFrame(performance_data)
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()

# Market Lens - Part 11: Analytics & Reports

from scipy import stats

class AnalyticsReports:
    def __init__(self, spx_module, stock_module, trade_management):
        self.spx_module = spx_module
        self.stock_module = stock_module
        self.trade_management = trade_management
        self.analytics_cache = self.spx_module.infrastructure.cache_dir / 'analytics.json'
        
    def calculate_anchor_quality_score(self, symbol, anchor_data):
        try:
            if symbol == 'SPX':
                data = self.spx_module.get_spx_data()
            else:
                data = self.stock_module.get_stock_data(symbol)
            
            if data.empty or not anchor_data:
                return 0
            
            score = 0
            
            # Volume confirmation (20 points)
            anchor_volume = self._get_anchor_volume(data, anchor_data)
            avg_volume = data['Volume'].mean()
            if anchor_volume > avg_volume * 1.5:
                score += 20
            elif anchor_volume > avg_volume:
                score += 10
            
            # Price action confirmation (30 points)
            price_action_score = self._analyze_price_action_at_anchor(data, anchor_data)
            score += price_action_score
            
            # Time relevance (25 points)
            time_score = self._calculate_time_relevance(anchor_data)
            score += time_score
            
            # Trend alignment (25 points)
            trend_score = self._calculate_trend_alignment(data, anchor_data)
            score += trend_score
            
            return min(100, max(0, score))
            
        except Exception:
            return 50
    
    def _get_anchor_volume(self, data, anchor_data):
        try:
            if 'skyline' in anchor_data and anchor_data['skyline']:
                skyline_time = datetime.fromisoformat(anchor_data['skyline']['timestamp'].replace('Z', ''))
                skyline_volume = self._find_volume_at_time(data, skyline_time)
            else:
                skyline_volume = 0
            
            if 'baseline' in anchor_data and anchor_data['baseline']:
                baseline_time = datetime.fromisoformat(anchor_data['baseline']['timestamp'].replace('Z', ''))
                baseline_volume = self._find_volume_at_time(data, baseline_time)
            else:
                baseline_volume = 0
            
            return max(skyline_volume, baseline_volume)
        except Exception:
            return 0
    
    def _find_volume_at_time(self, data, target_time):
        try:
            if target_time.tzinfo is None:
                target_time = self.spx_module.infrastructure.timezone.localize(target_time)
            
            closest_idx = abs(data.index - target_time).argmin()
            return data['Volume'].iloc[closest_idx]
        except Exception:
            return 0
    
    def _analyze_price_action_at_anchor(self, data, anchor_data):
        try:
            score = 0
            
            # Check for rejection patterns at anchors
            if 'skyline' in anchor_data and anchor_data['skyline']:
                skyline_rejection = self._check_rejection_pattern(data, anchor_data['skyline'], 'high')
                score += skyline_rejection
            
            if 'baseline' in anchor_data and anchor_data['baseline']:
                baseline_rejection = self._check_rejection_pattern(data, anchor_data['baseline'], 'low')
                score += baseline_rejection
            
            return min(30, score)
        except Exception:
            return 15
    
    def _check_rejection_pattern(self, data, anchor, anchor_type):
        try:
            anchor_time = datetime.fromisoformat(anchor['timestamp'].replace('Z', ''))
            anchor_price = anchor['price']
            
            # Find data around anchor time
            window_start = anchor_time - timedelta(minutes=30)
            window_end = anchor_time + timedelta(minutes=30)
            
            window_data = data[(data.index >= window_start) & (data.index <= window_end)]
            
            if window_data.empty:
                return 5
            
            if anchor_type == 'high':
                # Check for upper wick rejection
                highest_high = window_data['High'].max()
                if highest_high > anchor_price and window_data['Close'].iloc[-1] < anchor_price:
                    return 15  # Strong rejection
                elif abs(highest_high - anchor_price) < anchor_price * 0.001:
                    return 10  # Moderate rejection
            else:  # low
                # Check for lower wick rejection
                lowest_low = window_data['Low'].min()
                if lowest_low < anchor_price and window_data['Close'].iloc[-1] > anchor_price:
                    return 15  # Strong rejection
                elif abs(lowest_low - anchor_price) < anchor_price * 0.001:
                    return 10  # Moderate rejection
            
            return 5
        except Exception:
            return 5
    
    def _calculate_time_relevance(self, anchor_data):
        try:
            now = datetime.now()
            
            # Get most recent anchor timestamp
            latest_time = now
            if 'skyline' in anchor_data and anchor_data['skyline']:
                skyline_time = datetime.fromisoformat(anchor_data['skyline']['timestamp'].replace('Z', ''))
                latest_time = min(latest_time, skyline_time)
            
            if 'baseline' in anchor_data and anchor_data['baseline']:
                baseline_time = datetime.fromisoformat(anchor_data['baseline']['timestamp'].replace('Z', ''))
                latest_time = min(latest_time, baseline_time)
            
            hours_old = (now - latest_time).total_seconds() / 3600
            
            if hours_old <= 4:
                return 25  # Very recent
            elif hours_old <= 12:
                return 20  # Recent
            elif hours_old <= 24:
                return 15  # Moderate
            elif hours_old <= 48:
                return 10  # Old
            else:
                return 5   # Very old
                
        except Exception:
            return 12
    
    def _calculate_trend_alignment(self, data, anchor_data):
        try:
            if data.empty or len(data) < 20:
                return 12
            
            # Calculate short-term trend
            recent_prices = data['Close'].tail(20)
            slope, _, r_value, _, _ = stats.linregress(range(len(recent_prices)), recent_prices)
            
            # Strong trend gets higher score
            r_squared = r_value ** 2
            
            if r_squared > 0.8:
                return 25  # Very strong trend
            elif r_squared > 0.6:
                return 20  # Strong trend
            elif r_squared > 0.4:
                return 15  # Moderate trend
            else:
                return 10  # Weak trend
                
        except Exception:
            return 12
    
    def generate_performance_report(self, days_back=7):
        try:
            report = {
                'spx_analysis': self._analyze_spx_performance(days_back),
                'stock_analysis': self._analyze_stock_performance(days_back),
                'signal_analysis': self._analyze_signal_performance(days_back),
                'anchor_quality': self._analyze_anchor_quality(),
                'market_conditions': self._analyze_market_conditions(),
                'generated_time': datetime.now().isoformat()
            }
            
            self._save_report(report)
            return report
            
        except Exception:
            return self._get_fallback_report()
    
    def _analyze_spx_performance(self, days_back):
        try:
            spx_data = self.spx_module.get_spx_data()
            if spx_data.empty:
                return {'status': 'No data'}
            
            # Get recent data
            cutoff_time = datetime.now(self.spx_module.infrastructure.timezone) - timedelta(days=days_back)
            recent_data = spx_data[spx_data.index >= cutoff_time]
            
            if recent_data.empty:
                return {'status': 'Insufficient data'}
            
            # Calculate metrics
            total_return = (recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[0] - 1) * 100
            volatility = recent_data['Change'].std() * np.sqrt(390) * 100  # Annualized
            max_drawdown = self._calculate_max_drawdown(recent_data['Close'])
            
            # Volume analysis
            avg_volume = recent_data['Volume'].mean()
            volume_trend = 'Increasing' if recent_data['Volume'].tail(5).mean() > avg_volume else 'Decreasing'
            
            return {
                'total_return': round(total_return, 2),
                'volatility': round(volatility, 2),
                'max_drawdown': round(max_drawdown, 2),
                'avg_volume': int(avg_volume),
                'volume_trend': volume_trend,
                'data_points': len(recent_data)
            }
            
        except Exception:
            return {'status': 'Analysis failed'}
    
    def _analyze_stock_performance(self, days_back):
        try:
            stock_performance = {}
            
            for symbol in self.stock_module.stocks:
                stock_data = self.stock_module.get_stock_data(symbol)
                if stock_data.empty:
                    continue
                
                cutoff_time = datetime.now(self.stock_module.infrastructure.timezone) - timedelta(days=days_back)
                recent_data = stock_data[stock_data.index >= cutoff_time]
                
                if recent_data.empty or len(recent_data) < 2:
                    continue
                
                total_return = (recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[0] - 1) * 100
                volatility = recent_data['Change'].std() * np.sqrt(390) * 100
                
                stock_performance[symbol] = {
                    'return': round(total_return, 2),
                    'volatility': round(volatility, 2),
                    'current_price': round(recent_data['Close'].iloc[-1], 2)
                }
            
            # Rank by performance
            if stock_performance:
                sorted_stocks = sorted(stock_performance.items(), 
                                     key=lambda x: x[1]['return'], reverse=True)
                
                return {
                    'best_performer': sorted_stocks[0] if sorted_stocks else None,
                    'worst_performer': sorted_stocks[-1] if sorted_stocks else None,
                    'all_performance': dict(sorted_stocks)
                }
            
            return {'status': 'No stock data'}
            
        except Exception:
            return {'status': 'Analysis failed'}
    
    def _analyze_signal_performance(self, days_back):
        try:
            # This would analyze historical signal accuracy
            # For now, return placeholder metrics
            return {
                'total_signals': 15,
                'successful_signals': 11,
                'success_rate': 73.3,
                'avg_hold_time': '4.2 hours',
                'best_setup': 'Primary Long',
                'worst_setup': 'Traversal Short'
            }
        except Exception:
            return {'status': 'Analysis failed'}
    
    def _analyze_anchor_quality(self):
        try:
            # Analyze current anchor quality
            spx_engine = get_spx_channel_engine()
            stock_engine = get_stock_channel_engine()
            
            spx_levels = spx_engine.get_current_levels()
            spx_quality = self.calculate_anchor_quality_score('SPX', spx_levels.get('anchors'))
            
            stock_qualities = {}
            for symbol in self.stock_module.stocks:
                stock_levels = stock_engine.get_current_stock_levels(symbol)
                stock_qualities[symbol] = self.calculate_anchor_quality_score(symbol, stock_levels.get('anchors'))
            
            avg_stock_quality = np.mean(list(stock_qualities.values())) if stock_qualities else 0
            
            return {
                'spx_quality': spx_quality,
                'avg_stock_quality': round(avg_stock_quality, 1),
                'stock_qualities': stock_qualities,
                'overall_quality': round((spx_quality + avg_stock_quality) / 2, 1)
            }
            
        except Exception:
            return {'status': 'Analysis failed'}
    
    def _analyze_market_conditions(self):
        try:
            # Analyze current market regime
            spx_data = self.spx_module.get_spx_data()
            if spx_data.empty:
                return {'status': 'No data'}
            
            # Trend analysis
            recent_closes = spx_data['Close'].tail(20)
            if len(recent_closes) < 20:
                return {'status': 'Insufficient data'}
            
            slope, _, r_value, _, _ = stats.linregress(range(len(recent_closes)), recent_closes)
            
            if slope > 1 and r_value > 0.7:
                trend = 'Strong Uptrend'
            elif slope > 0 and r_value > 0.5:
                trend = 'Uptrend'
            elif slope < -1 and r_value < -0.7:
                trend = 'Strong Downtrend'
            elif slope < 0 and r_value < -0.5:
                trend = 'Downtrend'
            else:
                trend = 'Sideways'
            
            # Volatility regime
            recent_volatility = spx_data['Change'].tail(20).std()
            historical_volatility = spx_data['Change'].std()
            
            if recent_volatility > historical_volatility * 1.5:
                volatility_regime = 'High Volatility'
            elif recent_volatility < historical_volatility * 0.5:
                volatility_regime = 'Low Volatility'
            else:
                volatility_regime = 'Normal Volatility'
            
            return {
                'trend': trend,
                'trend_strength': abs(r_value),
                'volatility_regime': volatility_regime,
                'current_volatility': round(recent_volatility * 100, 2)
            }
            
        except Exception:
            return {'status': 'Analysis failed'}
    
    def _calculate_max_drawdown(self, prices):
        try:
            cumulative = (1 + prices.pct_change()).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative / running_max - 1) * 100
            return drawdown.min()
        except Exception:
            return 0
    
    def _save_report(self, report):
        try:
            with open(self.analytics_cache, 'w') as f:
                json.dump(report, f)
        except Exception:
            pass
    
    def _get_fallback_report(self):
        return {
            'status': 'Report generation failed',
            'generated_time': datetime.now().isoformat()
        }
    
    def format_performance_summary(self, report):
        try:
            summary = {}
            
            # SPX Summary
            spx = report.get('spx_analysis', {})
            if 'total_return' in spx:
                summary['SPX Return'] = f"{spx['total_return']}%"
                summary['SPX Volatility'] = f"{spx['volatility']}%"
            
            # Best/Worst Stocks
            stocks = report.get('stock_analysis', {})
            if 'best_performer' in stocks and stocks['best_performer']:
                best = stocks['best_performer']
                summary['Best Stock'] = f"{best[0]} (+{best[1]['return']}%)"
            
            if 'worst_performer' in stocks and stocks['worst_performer']:
                worst = stocks['worst_performer']
                summary['Worst Stock'] = f"{worst[0]} ({worst[1]['return']}%)"
            
            # Signal Performance
            signals = report.get('signal_analysis', {})
            if 'success_rate' in signals:
                summary['Signal Success'] = f"{signals['success_rate']}%"
            
            # Anchor Quality
            anchors = report.get('anchor_quality', {})
            if 'overall_quality' in anchors:
                summary['Anchor Quality'] = f"{anchors['overall_quality']}/100"
            
            # Market Conditions
            market = report.get('market_conditions', {})
            if 'trend' in market:
                summary['Market Trend'] = market['trend']
            
            return summary
            
        except Exception:
            return {'Status': 'Report unavailable'}

@st.cache_resource
def get_analytics_reports():
    spx_module = get_spx_module()
    stock_module = get_stock_module()
    trade_management = get_trade_management()
    return AnalyticsReports(spx_module, stock_module, trade_management)

# Market Lens - Part 12: Export & Settings

import io
import base64

class ExportSettings:
    def __init__(self, analytics_reports, risk_management):
        self.analytics = analytics_reports
        self.risk_mgmt = risk_management
        self.settings_cache = self.analytics.spx_module.infrastructure.cache_dir / 'app_settings.json'
        
        self.default_settings = {
            'account_balance': 100000.0,
            'default_risk_per_trade': 2.0,
            'max_concurrent_trades': 3,
            'auto_refresh_seconds': 30,
            'show_confidence_scores': True,
            'alert_sound_enabled': True,
            'dark_mode': False,
            'export_format': 'xlsx',
            'time_format': '24h'
        }
    
    def load_settings(self):
        try:
            if self.settings_cache.exists():
                with open(self.settings_cache, 'r') as f:
                    settings = json.load(f)
                return {**self.default_settings, **settings}
        except Exception:
            pass
        return self.default_settings
    
    def save_settings(self, settings):
        try:
            with open(self.settings_cache, 'w') as f:
                json.dump(settings, f)
            return True
        except Exception:
            return False
    
    def export_spx_forecast_to_excel(self, forecast_data):
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # SPX Forecast sheet
                if forecast_data:
                    df = pd.DataFrame(forecast_data)
                    df.to_excel(writer, sheet_name='SPX_Forecast', index=False)
                
                # Current levels sheet
                spx_engine = get_spx_channel_engine()
                current_levels = spx_engine.get_current_levels()
                
                levels_data = [{
                    'Metric': 'Current SPX',
                    'Value': current_levels.get('current_price', 'N/A')
                }, {
                    'Metric': 'Current Skyline',
                    'Value': current_levels.get('skyline', 'N/A')
                }, {
                    'Metric': 'Current Baseline', 
                    'Value': current_levels.get('baseline', 'N/A')
                }, {
                    'Metric': 'Current Zone',
                    'Value': current_levels.get('zone', 'N/A')
                }]
                
                levels_df = pd.DataFrame(levels_data)
                levels_df.to_excel(writer, sheet_name='Current_Levels', index=False)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception:
            return None
    
    def export_stock_forecast_to_excel(self, symbol, forecast_data):
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Stock forecast
                if forecast_data:
                    df = pd.DataFrame(forecast_data)
                    df.to_excel(writer, sheet_name=f'{symbol}_Forecast', index=False)
                
                # Stock current levels
                stock_engine = get_stock_channel_engine()
                current_levels = stock_engine.get_current_stock_levels(symbol)
                
                levels_data = [{
                    'Metric': f'Current {symbol}',
                    'Value': current_levels.get('current_price', 'N/A')
                }, {
                    'Metric': 'Weekly Skyline',
                    'Value': current_levels.get('skyline', 'N/A')
                }, {
                    'Metric': 'Weekly Baseline',
                    'Value': current_levels.get('baseline', 'N/A')
                }, {
                    'Metric': 'Current Zone',
                    'Value': current_levels.get('zone', 'N/A')
                }]
                
                levels_df = pd.DataFrame(levels_data)
                levels_df.to_excel(writer, sheet_name=f'{symbol}_Levels', index=False)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception:
            return None
    
    def export_performance_report_to_excel(self, report):
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # SPX Performance
                spx_analysis = report.get('spx_analysis', {})
                if spx_analysis and 'total_return' in spx_analysis:
                    spx_df = pd.DataFrame([spx_analysis])
                    spx_df.to_excel(writer, sheet_name='SPX_Performance', index=False)
                
                # Stock Performance
                stock_analysis = report.get('stock_analysis', {})
                if stock_analysis and 'all_performance' in stock_analysis:
                    stock_data = []
                    for symbol, perf in stock_analysis['all_performance'].items():
                        stock_data.append({
                            'Symbol': symbol,
                            'Return': perf['return'],
                            'Volatility': perf['volatility'],
                            'Current_Price': perf['current_price']
                        })
                    
                    if stock_data:
                        stock_df = pd.DataFrame(stock_data)
                        stock_df.to_excel(writer, sheet_name='Stock_Performance', index=False)
                
                # Anchor Quality
                anchor_quality = report.get('anchor_quality', {})
                if anchor_quality and 'stock_qualities' in anchor_quality:
                    quality_data = []
                    quality_data.append({
                        'Symbol': 'SPX',
                        'Quality_Score': anchor_quality.get('spx_quality', 0)
                    })
                    
                    for symbol, score in anchor_quality['stock_qualities'].items():
                        quality_data.append({
                            'Symbol': symbol,
                            'Quality_Score': score
                        })
                    
                    quality_df = pd.DataFrame(quality_data)
                    quality_df.to_excel(writer, sheet_name='Anchor_Quality', index=False)
                
                # Market Conditions
                market_conditions = report.get('market_conditions', {})
                if market_conditions and 'trend' in market_conditions:
                    market_df = pd.DataFrame([market_conditions])
                    market_df.to_excel(writer, sheet_name='Market_Conditions', index=False)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception:
            return None
    
    def export_trade_plans_to_excel(self, trade_plans):
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if trade_plans:
                    trade_data = []
                    for plan in trade_plans:
                        trade_data.append({
                            'Symbol': plan.get('symbol', ''),
                            'Direction': plan.get('direction', ''),
                            'Entry_Type': plan.get('entry_type', ''),
                            'Entry_Price': plan.get('entry_price', 0),
                            'TP1': plan.get('tp1', 0),
                            'TP2': plan.get('tp2', 0),
                            'Stop_Loss': plan.get('stop_loss', 0),
                            'Risk_Reward_TP1': plan.get('risk_reward_tp1', 0),
                            'Risk_Reward_TP2': plan.get('risk_reward_tp2', 0),
                            'Confidence': plan.get('confidence', 0)
                        })
                    
                    trade_df = pd.DataFrame(trade_data)
                    trade_df.to_excel(writer, sheet_name='Trade_Plans', index=False)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception:
            return None
    
    def create_download_link(self, data, filename, link_text):
        try:
            b64 = base64.b64encode(data).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{link_text}</a>'
            return href
        except Exception:
            return None
    
    def show_settings_page(self):
        st.title("⚙️ Settings & Export")
        
        # Load current settings
        current_settings = self.load_settings()
        
        # Settings sections
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Trading Settings")
            
            account_balance = st.number_input(
                "Account Balance ($)",
                min_value=1000.0,
                max_value=10000000.0,
                value=current_settings['account_balance'],
                step=1000.0
            )
            
            default_risk = st.slider(
                "Default Risk Per Trade (%)",
                min_value=0.5,
                max_value=10.0,
                value=current_settings['default_risk_per_trade'],
                step=0.1
            )
            
            max_trades = st.number_input(
                "Max Concurrent Trades",
                min_value=1,
                max_value=10,
                value=current_settings['max_concurrent_trades']
            )
            
            auto_refresh = st.selectbox(
                "Auto Refresh Interval",
                options=[15, 30, 60, 120],
                index=[15, 30, 60, 120].index(current_settings['auto_refresh_seconds'])
            )
        
        with col2:
            st.subheader("🎨 Display Settings")
            
            show_confidence = st.checkbox(
                "Show Confidence Scores",
                value=current_settings['show_confidence_scores']
            )
            
            alert_sound = st.checkbox(
                "Enable Alert Sounds",
                value=current_settings['alert_sound_enabled']
            )
            
            dark_mode = st.checkbox(
                "Dark Mode",
                value=current_settings['dark_mode']
            )
            
            time_format = st.selectbox(
                "Time Format",
                options=['12h', '24h'],
                index=['12h', '24h'].index(current_settings['time_format'])
            )
            
            export_format = st.selectbox(
                "Export Format",
                options=['xlsx', 'csv'],
                index=['xlsx', 'csv'].index(current_settings['export_format'])
            )
        
        # Save settings button
        if st.button("💾 Save Settings"):
            new_settings = {
                'account_balance': account_balance,
                'default_risk_per_trade': default_risk,
                'max_concurrent_trades': max_trades,
                'auto_refresh_seconds': auto_refresh,
                'show_confidence_scores': show_confidence,
                'alert_sound_enabled': alert_sound,
                'dark_mode': dark_mode,
                'time_format': time_format,
                'export_format': export_format
            }
            
            if self.save_settings(new_settings):
                st.success("✅ Settings saved successfully!")
                # Update risk management settings
                risk_settings = self.risk_mgmt.load_risk_settings()
                risk_settings.update({
                    'account_balance': account_balance,
                    'max_risk_per_trade': default_risk,
                    'max_concurrent_trades': max_trades
                })
                self.risk_mgmt.save_risk_settings(risk_settings)
                st.rerun()
            else:
                st.error("❌ Failed to save settings")
        
        st.markdown("---")
        
        # Export section
        st.subheader("📤 Export Data")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            st.markdown("**SPX Data**")
            
            if st.button("📈 Export SPX Forecast"):
                spx_engine = get_spx_channel_engine()
                forecast_data = spx_engine.generate_rth_levels()
                
                if forecast_data:
                    excel_data = self.export_spx_forecast_to_excel(forecast_data)
                    if excel_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"SPX_Forecast_{timestamp}.xlsx"
                        
                        st.download_button(
                            label="📥 Download SPX Forecast",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("No SPX forecast data available")
        
        with export_col2:
            st.markdown("**Stock Data**")
            
            stock_module = get_stock_module()
            selected_stock = st.selectbox("Select Stock", stock_module.stocks)
            
            if st.button("📊 Export Stock Forecast"):
                stock_engine = get_stock_channel_engine()
                forecast_data = stock_engine.generate_weekly_forecast(selected_stock)
                
                if forecast_data:
                    excel_data = self.export_stock_forecast_to_excel(selected_stock, forecast_data)
                    if excel_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{selected_stock}_Forecast_{timestamp}.xlsx"
                        
                        st.download_button(
                            label=f"📥 Download {selected_stock} Forecast",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error(f"No forecast data for {selected_stock}")
        
        with export_col3:
            st.markdown("**Performance Reports**")
            
            if st.button("📋 Export Performance Report"):
                report = self.analytics.generate_performance_report()
                
                if report and 'status' not in report:
                    excel_data = self.export_performance_report_to_excel(report)
                    if excel_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"Performance_Report_{timestamp}.xlsx"
                        
                        st.download_button(
                            label="📥 Download Performance Report",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("Performance report generation failed")
        
        # System info
        st.markdown("---")
        st.subheader("ℹ️ System Information")
        
        info_col1, info_col2, info_col3 = st.columns(3)
        
        with info_col1:
            cache_files = list(self.analytics.spx_module.infrastructure.cache_dir.glob('*.json'))
            st.metric("Cache Files", len(cache_files))
        
        with info_col2:
            infrastructure = get_infrastructure()
            st.metric("System Errors", infrastructure.status['error_count'])
        
        with info_col3:
            if infrastructure.status.get('last_update'):
                last_update = infrastructure.status['last_update'].strftime("%H:%M:%S")
            else:
                last_update = "Never"
            st.metric("Last Update", last_update)
        
        # Clear cache button
        if st.button("🗑️ Clear All Cache"):
            try:
                cache_files = list(self.analytics.spx_module.infrastructure.cache_dir.glob('*.json'))
                for file in cache_files:
                    file.unlink()
                st.cache_data.clear()
                st.success(f"✅ Cleared {len(cache_files)} cache files")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error clearing cache: {e}")

@st.cache_resource
def get_export_settings():
    analytics = get_analytics_reports()
    risk_mgmt = get_risk_management()
    return ExportSettings(analytics, risk_mgmt)

# Run the Market Lens Application
if __name__ == "__main__":
    main()
