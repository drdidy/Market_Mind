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
