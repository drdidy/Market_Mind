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
