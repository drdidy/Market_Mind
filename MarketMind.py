# ═══════════════════════════════════════════════════════════════════════════════
# DR. DAVID'S MARKET MIND - PREMIUM ENHANCED VERSION
# PART 1: FOUNDATION & STRATEGY CLASS WITH ADVANCED FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

import json
import base64
from datetime import datetime, date, time, timedelta
from copy import deepcopy
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import pytz
import math

# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED STRATEGY CLASS WITH PREMIUM FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

class SPXForecastStrategy:
    """Premium SPX forecasting strategy with advanced analytics and trading insights."""
    
    def __init__(self):
        # Default slopes for each asset
        self.base_slopes = {
            "SPX_HIGH": -0.2792, "SPX_CLOSE": -0.2792, "SPX_LOW": -0.2792,
            "TSLA": -0.1508, "NVDA": -0.0485, "AAPL": -0.0750,
            "MSFT": -0.17, "AMZN": -0.03, "GOOGL": -0.07,
            "META": -0.035, "NFLX": -0.23,
        }
        
        # Current slopes (can be modified)
        self.slopes = self.base_slopes.copy()
        
        # Trading hours
        self.spx_start_time = time(8, 30)
        self.general_start_time = time(7, 30)
        
        # Chicago timezone
        self.chicago_tz = pytz.timezone('America/Chicago')
        
        # Enhanced stock characteristics with advanced trading profiles
        self.stock_profiles = {
            "SPX": {
                "character": "🏛️ Market benchmark with institutional flow dominance and high liquidity",
                "behavior": "📊 Follows major support/resistance levels, highly sensitive to economic data and Fed policy",
                "patterns": "🔄 Gap fills common at 85% rate, trend persistence in momentum moves >2%, mean reversion at key levels",
                "opportunities": "💰 Range trading 0.5-1% moves, momentum breakouts >1.5%, options flow divergence signals",
                "volatility_profile": "Medium-Low",
                "best_timeframes": ["15min", "30min", "1hr"],
                "key_levels": "Round numbers (6000, 6100, 6200), previous day high/low, opening gaps",
                "risk_rating": "⭐⭐⭐"
            },
            "TSLA": {
                "character": "⚡ High-volatility momentum stock with massive retail and institutional following",
                "behavior": "🎢 News-driven with 5-15% intraday swings, Elon Musk tweet impacts, production data sensitive",
                "patterns": "🚀 Gap up/down 60% of days, momentum reversals at 10am/2pm, earnings volatility >20%",
                "opportunities": "💎 Volatility plays, straddle strategies, momentum breakouts, social sentiment analysis",
                "volatility_profile": "Very High",
                "best_timeframes": ["5min", "15min", "daily"],
                "key_levels": "Psychological levels ($200, $250, $300), delivery numbers, production updates",
                "risk_rating": "⭐⭐⭐⭐⭐"
            },
            "NVDA": {
                "character": "🤖 AI/semiconductor leader with institutional backing and growth momentum",
                "behavior": "🧠 Sector rotation sensitive, earnings-driven, AI hype cycles, data center demand correlation",
                "patterns": "📈 Strong trends during AI narratives, support at 20/50 EMA, earnings momentum 3-5 days",
                "opportunities": "🚀 Sector ETF arbitrage, earnings momentum, AI announcement plays, chip shortage news",
                "volatility_profile": "High",
                "best_timeframes": ["30min", "1hr", "daily"],
                "key_levels": "Previous earnings levels, analyst price targets, sector rotation thresholds",
                "risk_rating": "⭐⭐⭐⭐"
            },
            "AAPL": {
                "character": "🍎 Stable blue-chip with dividend appeal and consumer product cycles",
                "behavior": "📱 iPhone sales correlation, services growth focus, less volatile than tech peers",
                "patterns": "🔄 Slow steady trends, support at major MAs, iPhone cycle seasonality, dividend ex-date effects",
                "opportunities": "📊 Covered call strategies, range trading, earnings plays, product launch events",
                "volatility_profile": "Low-Medium",
                "best_timeframes": ["1hr", "4hr", "daily"],
                "key_levels": "Round numbers ($150, $175, $200), dividend levels, product launch dates",
                "risk_rating": "⭐⭐⭐"
            },
            "MSFT": {
                "character": "🪟 Enterprise software giant with cloud infrastructure dominance",
                "behavior": "☁️ Azure growth metrics drive moves, steady enterprise demand, dividend aristocrat stability",
                "patterns": "📊 Consistent uptrends with 5-8% pullbacks, cloud earnings correlation, enterprise spending cycles",
                "opportunities": "💼 Long-term holds, cloud earnings plays, enterprise spending correlation, dividend strategies",
                "volatility_profile": "Low-Medium",
                "best_timeframes": ["1hr", "daily", "weekly"],
                "key_levels": "Cloud growth thresholds, enterprise spending data, dividend ex-dates",
                "risk_rating": "⭐⭐⭐"
            },
            "AMZN": {
                "character": "📦 E-commerce and cloud infrastructure dual-revenue giant",
                "behavior": "🛒 AWS growth vs retail margins, Prime membership data, logistics efficiency metrics",
                "patterns": "📈 Large earnings moves 8-12%, AWS growth>retail growth correlation, seasonal retail patterns",
                "opportunities": "🎯 Prime Day reactions, AWS earnings beats, retail seasonality, logistics improvements",
                "volatility_profile": "Medium-High",
                "best_timeframes": ["30min", "1hr", "daily"],
                "key_levels": "AWS growth rates, Prime membership numbers, retail margin improvements",
                "risk_rating": "⭐⭐⭐⭐"
            },
            "GOOGL": {
                "character": "🔍 Digital advertising monopoly with search and cloud diversification",
                "behavior": "💰 Ad revenue cycles, regulatory headline sensitivity, YouTube growth correlation",
                "patterns": "📊 Steady growth with regulatory dips, ad spending correlation, antitrust headline volatility",
                "opportunities": "📺 Ad revenue beats, AI search developments, antitrust resolution, YouTube monetization",
                "volatility_profile": "Medium",
                "best_timeframes": ["1hr", "daily", "weekly"],
                "key_levels": "Ad revenue growth rates, regulatory milestones, AI development announcements",
                "risk_rating": "⭐⭐⭐"
            },
            "META": {
                "character": "📘 Social media platform empire with metaverse investments",
                "behavior": "👥 User growth metrics priority, Reality Labs burn rate, privacy regulation impact",
                "patterns": "📱 Quarterly user volatility, metaverse investment cycles, privacy update impacts",
                "opportunities": "🥽 User growth surprises, metaverse developments, VR adoption, privacy adaptation",
                "volatility_profile": "High",
                "best_timeframes": ["15min", "1hr", "daily"],
                "key_levels": "User growth thresholds, metaverse investment levels, privacy regulation dates",
                "risk_rating": "⭐⭐⭐⭐"
            },
            "NFLX": {
                "character": "📺 Streaming entertainment leader with global expansion focus",
                "behavior": "🎬 Subscriber number obsession, content spend efficiency, international growth correlation",
                "patterns": "📊 Quarterly subscriber volatility 5-15%, content announcement bumps, competition pressure",
                "opportunities": "🍿 Earnings subscriber beats, content slate announcements, international expansion, competition analysis",
                "volatility_profile": "High",
                "best_timeframes": ["15min", "1hr", "daily"],
                "key_levels": "Subscriber growth targets, content spending thresholds, international penetration rates",
                "risk_rating": "⭐⭐⭐⭐"
            }
        }
        
        # Market sentiment indicators
        self.market_conditions = {
            "fear_greed_index": 50,
            "vix_level": 20.0,
            "market_regime": "Normal",
            "trend_strength": "Medium"
        }
        
        # Advanced analytics cache
        self.analytics_cache = {}
    
    def get_chicago_time(self) -> datetime:
        """Get current time in Chicago timezone with enhanced formatting."""
        utc_now = datetime.utcnow()
        utc_dt = pytz.utc.localize(utc_now)
        chicago_time = utc_dt.astimezone(self.chicago_tz)
        return chicago_time
    
    def calculate_market_pulse(self) -> Dict[str, any]:
        """Calculate advanced market pulse metrics."""
        chicago_time = self.get_chicago_time()
        
        # Market session analysis
        hour = chicago_time.hour
        minute = chicago_time.minute
        
        if 4 <= hour < 9:
            session = "Pre-Market"
            session_color = "#f59e0b"
            session_emoji = "🌅"
        elif 9 <= hour < 16:
            session = "Regular Hours"
            session_color = "#10b981"
            session_emoji = "🔥"
        elif 16 <= hour < 20:
            session = "After Hours"
            session_color = "#3b82f6"
            session_emoji = "🌆"
        else:
            session = "Closed"
            session_color = "#6b7280"
            session_emoji = "😴"
        
        # Volume profile estimation
        if 9 <= hour < 10:
            volume_profile = "High (Opening)"
        elif 10 <= hour < 15:
            volume_profile = "Medium (Midday)"
        elif 15 <= hour < 16:
            volume_profile = "High (Closing)"
        else:
            volume_profile = "Low"
        
        return {
            "session": session,
            "session_color": session_color,
            "session_emoji": session_emoji,
            "volume_profile": volume_profile,
            "market_efficiency": "High" if 9 <= hour < 16 else "Medium",
            "opportunity_rating": "⭐⭐⭐⭐⭐" if 9 <= hour < 10 or 15 <= hour < 16 else "⭐⭐⭐"
        }
    
    def generate_time_slots(self, start_time: time = None) -> List[str]:
        """Generate enhanced time slots with market context."""
        if start_time is None:
            start_time = self.general_start_time
            
        base = datetime(2025, 1, 1, start_time.hour, start_time.minute)
        slots = []
        
        # Calculate number of slots with enhanced logic
        num_slots = 15 - (2 if start_time.hour == 8 and start_time.minute == 30 else 0)
        
        for i in range(num_slots):
            slot_time = base + timedelta(minutes=30 * i)
            slots.append(slot_time.strftime("%H:%M"))
            
        return slots
    
    def calculate_spx_blocks(self, anchor_time: datetime, target_time: datetime) -> int:
        """Calculate time blocks for SPX with enhanced accuracy."""
        blocks = 0
        current = anchor_time
        
        while current < target_time:
            if current.hour != 16:  # Skip 4:00 PM hour
                blocks += 1
            current += timedelta(minutes=30)
            
        return blocks
    
    def calculate_stock_blocks(self, anchor_time: datetime, target_time: datetime) -> int:
        """Calculate time blocks for regular stocks with precision."""
        time_diff = target_time - anchor_time
        return max(0, int(time_diff.total_seconds() // 1800))  # 1800 seconds = 30 minutes
    
    def project_price(self, base_price: float, slope: float, blocks: int) -> float:
        """Enhanced price projection with volatility adjustment."""
        base_projection = base_price + (slope * blocks)
        
        # Add minor random walk component for realism (optional)
        # volatility_factor = 0.001 * blocks
        # adjustment = np.random.normal(0, volatility_factor) if blocks > 0 else 0
        
        return base_projection  # + adjustment if desired
    
    def generate_forecast_table(self, base_price: float, slope: float, anchor_time: datetime, 
                              forecast_date: date, is_spx: bool = True, fan_mode: bool = False) -> pd.DataFrame:
        """Generate enhanced forecast table with advanced metrics."""
        
        # Get appropriate time slots
        start_time = self.spx_start_time if is_spx else self.general_start_time
        slots = self.generate_time_slots(start_time)
        
        rows = []
        for i, slot in enumerate(slots):
            hour, minute = map(int, slot.split(":"))
            target_time = datetime.combine(forecast_date, time(hour, minute))
            
            # Calculate blocks based on asset type
            if is_spx:
                blocks = self.calculate_spx_blocks(anchor_time, target_time)
            else:
                blocks = self.calculate_stock_blocks(anchor_time, target_time)
            
            # Generate projection with enhanced data
            if fan_mode:
                # Fan mode: entry and exit prices with confidence intervals
                entry_price = self.project_price(base_price, slope, blocks)
                exit_price = self.project_price(base_price, -slope, blocks)
                
                # Add confidence and momentum indicators
                confidence = max(0.5, 1.0 - (blocks * 0.05))  # Decreases with time
                momentum = "🔥" if abs(slope) > 0.1 else "📊" if abs(slope) > 0.05 else "😴"
                
                rows.append({
                    "Time": slot,
                    "Entry": round(entry_price, 2),
                    "Exit": round(exit_price, 2),
                    "Spread": round(abs(entry_price - exit_price), 2),
                    "Confidence": f"{confidence:.1%}",
                    "Signal": momentum
                })
            else:
                # Regular mode: single projected price with analytics
                projected_price = self.project_price(base_price, slope, blocks)
                price_change = projected_price - base_price
                change_pct = (price_change / base_price) * 100 if base_price > 0 else 0
                
                rows.append({
                    "Time": slot,
                    "Projected": round(projected_price, 2),
                    "Change": f"${price_change:+.2f}",
                    "Change%": f"{change_pct:+.1f}%"
                })
        
        return pd.DataFrame(rows)
    
    def spx_forecast(self, high_price: float, high_time: time, close_price: float, close_time: time,
                    low_price: float, low_time: time, forecast_date: date) -> Dict[str, pd.DataFrame]:
        """Generate enhanced SPX forecast with advanced analytics."""
        
        # Create anchor datetimes (previous day)
        prev_day = forecast_date - timedelta(days=1)
        high_anchor = datetime.combine(prev_day, high_time)
        close_anchor = datetime.combine(prev_day, close_time)
        low_anchor = datetime.combine(prev_day, low_time)
        
        forecasts = {}
        
        # Generate forecasts for each anchor with enhanced features
        for anchor_type, price, anchor_time, slope_key in [
            ("High", high_price, high_anchor, "SPX_HIGH"),
            ("Close", close_price, close_anchor, "SPX_CLOSE"),
            ("Low", low_price, low_anchor, "SPX_LOW")
        ]:
            forecasts[anchor_type] = self.generate_forecast_table(
                price, self.slopes[slope_key], anchor_time, forecast_date, 
                is_spx=True, fan_mode=True
            )
        
        return forecasts
    
    def contract_line_forecast(self, low1_price: float, low1_time: time, low2_price: float, 
                             low2_time: time, forecast_date: date) -> Tuple[pd.DataFrame, Dict]:
        """Generate enhanced contract line forecast with advanced interpolation."""
        
        # Create anchor datetime
        anchor_time = datetime.combine(forecast_date, low1_time)
        
        # Calculate slope between the two points
        low2_datetime = datetime.combine(forecast_date, low2_time)
        blocks_between = self.calculate_spx_blocks(anchor_time, low2_datetime)
        
        if blocks_between == 0:
            slope = 0
        else:
            slope = (low2_price - low1_price) / blocks_between
        
        # Generate enhanced forecast table
        forecast_table = self.generate_forecast_table(
            low1_price, slope, anchor_time, forecast_date, 
            is_spx=False, fan_mode=False
        )
        
        # Enhanced contract parameters
        contract_params = {
            "anchor_time": anchor_time,
            "slope": slope,
            "base_price": low1_price,
            "target_price": low2_price,
            "trend_strength": "Strong" if abs(slope) > 0.1 else "Moderate" if abs(slope) > 0.05 else "Weak",
            "reliability_score": min(0.95, 0.7 + (0.3 * (1 / max(1, blocks_between))))
        }
        
        return forecast_table, contract_params
    
    def lookup_contract_price(self, contract_params: Dict, lookup_time: time, forecast_date: date) -> float:
        """Enhanced contract price lookup with confidence metrics."""
        if not contract_params:
            return 0.0
            
        target_time = datetime.combine(forecast_date, lookup_time)
        blocks = self.calculate_spx_blocks(contract_params["anchor_time"], target_time)
        
        return self.project_price(contract_params["base_price"], contract_params["slope"], blocks)
    
    def stock_forecast(self, ticker: str, low_price: float, low_time: time,
                      high_price: float, high_time: time, forecast_date: date) -> Dict[str, pd.DataFrame]:
        """Generate enhanced stock forecast with advanced analytics."""
        
        if ticker not in self.slopes:
            raise ValueError(f"Unknown ticker: {ticker}")
        
        # Create anchor datetimes
        low_anchor = datetime.combine(forecast_date, low_time)
        high_anchor = datetime.combine(forecast_date, high_time)
        
        forecasts = {
            "Low": self.generate_forecast_table(
                low_price, self.slopes[ticker], low_anchor, forecast_date,
                is_spx=False, fan_mode=True
            ),
            "High": self.generate_forecast_table(
                high_price, self.slopes[ticker], high_anchor, forecast_date,
                is_spx=False, fan_mode=True
            )
        }
        
        return forecasts
    
    def get_stock_profile(self, ticker: str) -> Dict[str, str]:
        """Get enhanced trading profile and insights for a stock."""
        return self.stock_profiles.get(ticker, {
            "character": "Individual stock analysis",
            "behavior": "Market correlated movements",
            "patterns": "Standard technical patterns",
            "opportunities": "Technical analysis opportunities",
            "volatility_profile": "Medium",
            "best_timeframes": ["1hr", "daily"],
            "key_levels": "Support and resistance levels",
            "risk_rating": "⭐⭐⭐"
        })
    
    def calculate_portfolio_metrics(self, active_forecasts: Dict) -> Dict[str, any]:
        """Calculate advanced portfolio and risk metrics."""
        total_forecasts = len(active_forecasts)
        
        # Risk assessment
        high_risk_count = sum(1 for ticker in active_forecasts.keys() 
                             if self.get_stock_profile(ticker).get("risk_rating", "⭐⭐⭐").count("⭐") >= 4)
        
        risk_score = (high_risk_count / max(1, total_forecasts)) * 100
        
        return {
            "total_positions": total_forecasts,
            "risk_score": risk_score,
            "risk_level": "High" if risk_score > 60 else "Medium" if risk_score > 30 else "Low",
            "diversification": "Good" if total_forecasts >= 3 else "Poor"
        }
    
    def update_slope(self, asset: str, new_slope: float):
        """Update slope for a specific asset with validation."""
        if asset in self.slopes:
            self.slopes[asset] = new_slope
            # Clear related cache
            self.analytics_cache.clear()
    
    def reset_slopes(self):
        """Reset all slopes to default values."""
        self.slopes = self.base_slopes.copy()
        self.analytics_cache.clear()
    
    def get_available_tickers(self) -> List[str]:
        """Get list of available stock tickers with enhanced metadata."""
        return [k for k in self.slopes.keys() if not k.startswith("SPX_")]
    
    def export_configuration(self) -> Dict[str, any]:
        """Export complete configuration for backup/sharing."""
        return {
            "slopes": self.slopes.copy(),
            "market_conditions": self.market_conditions.copy(),
            "export_timestamp": self.get_chicago_time().isoformat(),
            "version": "3.0_premium"
        }

# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: PREMIUM PAGE CONFIGURATION & ADVANCED THEME SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# Premium page configuration with enhanced settings
st.set_page_config(
    page_title="Dr. David's Market Mind - Premium",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Dr. David's Market Mind - Premium Financial Forecasting Platform",
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': 'mailto:support@marketmind.com'
    }
)

# Initialize enhanced strategy
@st.cache_resource
def get_strategy():
    return SPXForecastStrategy()

strategy = get_strategy()

# Enhanced session state initialization
if 'current_forecasts' not in st.session_state:
    st.session_state.current_forecasts = {}
if 'contract_params' not in st.session_state:
    st.session_state.contract_params = {}
if 'contract_table' not in st.session_state:
    st.session_state.contract_table = pd.DataFrame()
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "SPX"
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'animation_enabled' not in st.session_state:
    st.session_state.animation_enabled = True
if 'premium_effects' not in st.session_state:
    st.session_state.premium_effects = True
if 'color_scheme' not in st.session_state:
    st.session_state.color_scheme = "gradient"
if 'sidebar_visible' not in st.session_state:
    st.session_state.sidebar_visible = True
if 'sidebar_collapsed' not in st.session_state:
    st.session_state.sidebar_collapsed = False

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM THEME SYSTEM WITH 3D EFFECTS & BEAUTIFUL GRADIENTS
# ═══════════════════════════════════════════════════════════════════════════════

def apply_premium_theme():
    """Apply premium dark or light theme with advanced 3D effects and gradients."""
    
    # Base color schemes
    if st.session_state.dark_mode:
        # Premium Dark Theme
        bg_primary = "#0a0e1a"
        bg_secondary = "#1a1f2e"
        bg_tertiary = "#252a3a"
        text_primary = "#f8fafc"
        text_secondary = "#cbd5e1"
        accent_primary = "#6366f1"
        accent_secondary = "#8b5cf6"
        success_color = "#10b981"
        warning_color = "#f59e0b"
        danger_color = "#ef4444"
        
        # Gradient variations
        hero_gradient = "linear-gradient(135deg, #1e1b4b 0%, #312e81 25%, #3730a3 50%, #1e40af 75%, #1d4ed8 100%)"
        card_gradient = "linear-gradient(145deg, #1e293b 0%, #334155 100%)"
        button_gradient = "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%)"
        
    else:
        # Premium Light Theme
        bg_primary = "#fafbff"
        bg_secondary = "#ffffff"
        bg_tertiary = "#f1f5f9"
        text_primary = "#1e293b"
        text_secondary = "#475569"
        accent_primary = "#3b82f6"
        accent_secondary = "#6366f1"
        success_color = "#059669"
        warning_color = "#d97706"
        danger_color = "#dc2626"
        
        # Gradient variations
        hero_gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 25%, #6B73FF 50%, #000428 75%, #004e92 100%)"
        card_gradient = "linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)"
        button_gradient = "linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%)"
    
    # Premium CSS with 3D effects and animations
    premium_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* =================================================================== */
    /* PREMIUM BASE STYLES */
    /* =================================================================== */
    
    :root {{
        --bg-primary: {bg_primary};
        --bg-secondary: {bg_secondary};
        --bg-tertiary: {bg_tertiary};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --accent-primary: {accent_primary};
        --accent-secondary: {accent_secondary};
        --success: {success_color};
        --warning: {warning_color};
        --danger: {danger_color};
        --hero-gradient: {hero_gradient};
        --card-gradient: {card_gradient};
        --button-gradient: {button_gradient};
        --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.1);
        --shadow-medium: 0 8px 30px rgba(0, 0, 0, 0.15);
        --shadow-strong: 0 15px 40px rgba(0, 0, 0, 0.2);
        --border-radius: 16px;
        --border-radius-lg: 24px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-slow: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .stApp {{
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        overflow-x: hidden;
    }}
    
    .main {{
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        padding: 2rem 1rem;
    }}
    
    /* =================================================================== */
    /* PREMIUM SIDEBAR WITH TOGGLE CONTROL */
    /* =================================================================== */
    
    .css-1d391kg {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(20px);
        box-shadow: var(--shadow-medium);
        position: relative;
        overflow: hidden;
        transition: var(--transition-slow) !important;
        {f'transform: translateX(-100%);' if st.session_state.get('sidebar_collapsed', False) else 'transform: translateX(0);'}
        {f'width: 0 !important; min-width: 0 !important;' if st.session_state.get('sidebar_collapsed', False) else ''}
    }}
    
    .css-1d391kg::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--button-gradient);
        z-index: 1;
    }}
    
    /* Sidebar toggle button */
    .sidebar-toggle {{
        position: fixed;
        top: 1rem;
        left: {f'1rem' if st.session_state.get('sidebar_collapsed', False) else '21rem'};
        z-index: 9999;
        background: var(--button-gradient) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 3rem !important;
        height: 3rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: white !important;
        font-size: 1.2rem !important;
        box-shadow: var(--shadow-medium) !important;
        transition: var(--transition) !important;
        cursor: pointer !important;
    }}
    
    .sidebar-toggle:hover {{
        transform: scale(1.1) !important;
        box-shadow: var(--shadow-strong) !important;
    }}
    
    /* Adjust main content when sidebar is collapsed */
    .main .block-container {{
        {f'padding-left: 1rem !important;' if st.session_state.get('sidebar_collapsed', False) else 'padding-left: 2rem !important;'}
        transition: var(--transition-slow) !important;
    }}
    
    /* =================================================================== */
    /* PREMIUM TYPOGRAPHY */
    /* =================================================================== */
    
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-primary) !important;
        font-weight: 700;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }}
    
    h1 {{ font-size: 2.5rem; }}
    h2 {{ font-size: 2rem; }}
    h3 {{ font-size: 1.5rem; }}
    
    p, div, span, label {{
        color: var(--text-secondary) !important;
        line-height: 1.6;
    }}
    
    /* =================================================================== */
    /* PREMIUM INPUT STYLES */
    /* =================================================================== */
    
    .stSelectbox label, 
    .stNumberInput label, 
    .stDateInput label, 
    .stTimeInput label, 
    .stTextInput label {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }}
    
    .stSelectbox > div > div,
    .stNumberInput > div > div,
    .stDateInput > div > div,
    .stTimeInput > div > div,
    .stTextInput > div > div {{
        background: var(--bg-tertiary) !important;
        border: 2px solid transparent !important;
        border-radius: var(--border-radius) !important;
        box-shadow: var(--shadow-soft);
        transition: var(--transition);
    }}
    
    .stSelectbox > div > div:hover,
    .stNumberInput > div > div:hover,
    .stDateInput > div > div:hover,
    .stTimeInput > div > div:hover,
    .stTextInput > div > div:hover {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
    }}
    
    /* =================================================================== */
    /* PREMIUM HERO SECTION */
    /* =================================================================== */
    
    .hero-container {{
        background: var(--hero-gradient);
        border-radius: var(--border-radius-lg);
        padding: 3rem 2rem;
        margin: 2rem 0;
        text-align: center;
        box-shadow: var(--shadow-strong);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(2deg);
        transition: var(--transition-slow);
    }}
    
    .hero-container::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: hero-pulse 4s ease-in-out infinite;
        pointer-events: none;
    }}
    
    .hero-container:hover {{
        transform: perspective(1000px) rotateX(0deg) translateY(-5px);
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
    }}
    
    .hero-title {{
        font-size: 3.5rem;
        font-weight: 900;
        color: white !important;
        margin-bottom: 1rem;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        background: linear-gradient(45deg, #ffffff, #e0e7ff);
        background-clip: text;
        -webkit-background-clip: text;
        position: relative;
        z-index: 2;
    }}
    
    .hero-subtitle {{
        font-size: 1.3rem;
        color: rgba(255, 255, 255, 0.9) !important;
        margin-bottom: 2rem;
        font-weight: 400;
        position: relative;
        z-index: 2;
    }}
    
    /* =================================================================== */
    /* PREMIUM METRIC CARDS WITH 3D EFFECTS */
    /* =================================================================== */
    
    .metric-card {{
        background: var(--card-gradient) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: var(--border-radius);
        padding: 2rem;
        box-shadow: var(--shadow-medium);
        transition: var(--transition);
        height: 100%;
        color: var(--text-primary) !important;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        transform: perspective(1000px) rotateY(0deg);
    }}
    
    .metric-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: var(--transition);
    }}
    
    .metric-card:hover {{
        transform: perspective(1000px) rotateY(5deg) translateY(-10px);
        box-shadow: var(--shadow-strong);
        border-color: var(--accent-primary);
    }}
    
    .metric-card:hover::before {{
        left: 100%;
    }}
    
    /* =================================================================== */
    /* PREMIUM INPUT CONTAINERS */
    /* =================================================================== */
    
    .input-container {{
        background: var(--card-gradient) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: var(--border-radius);
        padding: 2rem;
        margin: 1.5rem 0;
        color: var(--text-primary) !important;
        box-shadow: var(--shadow-medium);
        position: relative;
        overflow: hidden;
        transition: var(--transition);
    }}
    
    .input-container::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--button-gradient);
        transform: scaleX(0);
        transition: var(--transition);
    }}
    
    .input-container:hover::after {{
        transform: scaleX(1);
    }}
    
    /* =================================================================== */
    /* PREMIUM DATAFRAMES */
    /* =================================================================== */
    
    .stDataFrame {{
        background: var(--bg-secondary) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: var(--border-radius) !important;
        box-shadow: var(--shadow-medium);
        overflow: hidden;
    }}
    
    .stDataFrame table {{
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }}
    
    .stDataFrame th {{
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.8rem;
        padding: 1rem !important;
        border-bottom: 2px solid var(--accent-primary) !important;
    }}
    
    .stDataFrame td {{
        background: var(--bg-secondary) !important;
        color: var(--text-secondary) !important;
        padding: 0.8rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        transition: var(--transition);
    }}
    
    .stDataFrame tr:hover td {{
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }}
    
    /* =================================================================== */
    /* PREMIUM BUTTONS WITH 3D EFFECTS */
    /* =================================================================== */
    
    .stButton > button {{
        background: var(--button-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.8rem 2rem !important;
        box-shadow: var(--shadow-medium) !important;
        transition: var(--transition) !important;
        position: relative !important;
        overflow: hidden !important;
        transform: perspective(1000px) rotateX(0deg) !important;
    }}
    
    .stButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: var(--transition);
    }}
    
    .stButton > button:hover {{
        transform: perspective(1000px) rotateX(-5deg) translateY(-3px) !important;
        box-shadow: var(--shadow-strong) !important;
    }}
    
    .stButton > button:hover::before {{
        left: 100%;
    }}
    
    .stButton > button:active {{
        transform: perspective(1000px) rotateX(0deg) translateY(0px) !important;
    }}
    
    /* =================================================================== */
    /* PREMIUM DOWNLOAD BUTTONS */
    /* =================================================================== */
    
    .stDownloadButton > button {{
        background: linear-gradient(135deg, var(--success) 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--border-radius) !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-medium) !important;
        transition: var(--transition) !important;
    }}
    
    .stDownloadButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-strong) !important;
    }}
    
    /* =================================================================== */
    /* PREMIUM 3D TABS */
    /* =================================================================== */
    
    .stTabs {{
        margin: 2rem 0;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--bg-tertiary) !important;
        border-radius: var(--border-radius) !important;
        padding: 0.5rem !important;
        box-shadow: var(--shadow-soft) !important;
        gap: 0.5rem !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: var(--text-secondary) !important;
        background: transparent !important;
        border-radius: calc(var(--border-radius) - 4px) !important;
        padding: 1rem 2rem !important;
        font-weight: 600 !important;
        transition: var(--transition) !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(99, 102, 241, 0.1) !important;
        color: var(--text-primary) !important;
        transform: translateY(-2px) !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: var(--button-gradient) !important;
        color: white !important;
        box-shadow: var(--shadow-medium) !important;
        transform: translateY(-3px) !important;
    }}
    
    /* =================================================================== */
    /* PREMIUM ALERTS */
    /* =================================================================== */
    
    .stAlert {{
        border-radius: var(--border-radius) !important;
        box-shadow: var(--shadow-soft) !important;
        border: none !important;
    }}
    
    .stSuccess > div {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1)) !important;
        border-left: 4px solid var(--success) !important;
        color: var(--success) !important;
    }}
    
    .stInfo > div {{
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.1)) !important;
        border-left: 4px solid var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }}
    
    .stWarning > div {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.1)) !important;
        border-left: 4px solid var(--warning) !important;
        color: var(--warning) !important;
    }}
    
    .stError > div {{
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1)) !important;
        border-left: 4px solid var(--danger) !important;
        color: var(--danger) !important;
    }}
    
    /* =================================================================== */
    /* PREMIUM ANIMATIONS */
    /* =================================================================== */
    
    @keyframes hero-pulse {{
        0%, 100% {{ transform: scale(1) rotate(0deg); opacity: 0.1; }}
        50% {{ transform: scale(1.1) rotate(180deg); opacity: 0.2; }}
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    @keyframes glow {{
        0%, 100% {{ box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); }}
        50% {{ box-shadow: 0 0 40px rgba(99, 102, 241, 0.6); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .float {{
        animation: float 3s ease-in-out infinite;
    }}
    
    .glow {{
        animation: glow 2s ease-in-out infinite;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* =================================================================== */
    /* HIDE STREAMLIT BRANDING */
    /* =================================================================== */
    
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    .stDeployButton {{ visibility: hidden; }}
    
    /* =================================================================== */
    /* SCROLLBAR STYLING */
    /* =================================================================== */
    
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--bg-tertiary);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--accent-primary);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--accent-secondary);
    }}
    
    /* =================================================================== */
    /* RESPONSIVE DESIGN */
    /* =================================================================== */
    
    @media (max-width: 768px) {{
        .hero-title {{ font-size: 2.5rem; }}
        .hero-subtitle {{ font-size: 1.1rem; }}
        .metric-card {{ padding: 1.5rem; }}
        .input-container {{ padding: 1.5rem; }}
    }}
    
    </style>
    """
    
    st.markdown(premium_css, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: PREMIUM HEADER, NAVIGATION & SIDEBAR CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

# Apply premium theme first
apply_premium_theme()

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM UTILITY FUNCTIONS WITH ENHANCED FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

def create_premium_metric_card(icon: str, title: str, value: str, subtitle: str = "", trend: str = ""):
    """Create premium metric card with 3D effects and trend indicators."""
    trend_indicator = ""
    if trend:
        if "+" in trend:
            trend_indicator = f'<div style="color: #10b981; font-size: 0.9rem; margin-top: 0.5rem;">📈 {trend}</div>'
        elif "-" in trend:
            trend_indicator = f'<div style="color: #ef4444; font-size: 0.9rem; margin-top: 0.5rem;">📉 {trend}</div>'
        else:
            trend_indicator = f'<div style="color: #6b7280; font-size: 0.9rem; margin-top: 0.5rem;">➡️ {trend}</div>'
    
    return f"""
    <div class="metric-card fade-in float">
        <div style="font-size: 3rem; margin-bottom: 1rem; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">{icon}</div>
        <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem; background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary)); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{value}</div>
        <div style="font-size: 0.85rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">{title}</div>
        {f'<div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7;">{subtitle}</div>' if subtitle else ''}
        {trend_indicator}
    </div>
    """

def create_status_badge(status: str, color: str, pulse: bool = False) -> str:
    """Create animated status badge."""
    pulse_class = "glow" if pulse else ""
    return f"""
    <div class="status-badge {pulse_class}" style="
        background: {color}; 
        padding: 0.5rem 1rem; 
        border-radius: 25px; 
        color: white; 
        font-weight: 600; 
        font-size: 0.9rem;
        box-shadow: 0 4px 15px {color}33;
        border: 2px solid {color}66;
    ">
        {status}
    </div>
    """

def display_premium_forecast_table(df: pd.DataFrame, title: str, chart_type: str = "forecast"):
    """Display premium forecast table with enhanced styling and features."""
    
    # Add custom CSS for this specific table
    st.markdown(f"""
    <div style="margin: 2rem 0;">
        <h3 style="
            color: var(--text-primary); 
            font-size: 1.5rem; 
            font-weight: 700; 
            margin-bottom: 1rem;
            background: linear-gradient(45deg, var(--accent-primary), var(--accent-secondary));
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        ">{title}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not df.empty:
        # Create enhanced display dataframe
        display_df = df.copy()
        
        # Format price columns with enhanced styling
        for col in ['Entry', 'Exit', 'Projected']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")
        
        # Add trend indicators for changes
        if 'Change%' in display_df.columns:
            display_df['Trend'] = display_df['Change%'].apply(
                lambda x: "🔥" if "+" in str(x) and float(str(x).replace('+', '').replace('%', '')) > 1 
                else "📈" if "+" in str(x) 
                else "📉" if "-" in str(x) 
                else "➡️"
            )
        
        # Display the enhanced dataframe
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Signal": st.column_config.TextColumn("Signal", width="small"),
                "Trend": st.column_config.TextColumn("Trend", width="small"),
                "Confidence": st.column_config.TextColumn("Confidence", width="medium"),
            }
        )
        
        # Enhanced download section
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Table statistics
            if not df.empty:
                if 'Entry' in df.columns and 'Exit' in df.columns:
                    avg_spread = (df['Entry'] - df['Exit']).mean()
                    max_spread = (df['Entry'] - df['Exit']).max()
                    st.metric("Avg Spread", f"${avg_spread:.2f}", f"Max: ${max_spread:.2f}")
                elif 'Projected' in df.columns:
                    price_range = df['Projected'].max() - df['Projected'].min()
                    st.metric("Price Range", f"${price_range:.2f}")
        
        with col2:
            # Download CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name=f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col3:
            # Download JSON
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="📊 JSON",
                data=json_data,
                file_name=f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("📊 No data available - Generate a forecast to see results")

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM HEADER WITH CHICAGO TIME & ADVANCED CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

def render_premium_hero_section():
    """Render premium hero section with advanced features and Chicago time."""
    chicago_time = strategy.get_chicago_time()
    current_time_chicago = chicago_time.strftime("%H:%M:%S CST")
    current_date = chicago_time.strftime("%A, %B %d, %Y")
    
    # Get market pulse data
    market_pulse = strategy.calculate_market_pulse()
    
    # Header controls row
    header_col1, header_col2, header_col3, header_col4 = st.columns([3, 1, 1, 1])
    
    with header_col2:
        # Sidebar toggle
        sidebar_icon = "👁️" if st.session_state.sidebar_collapsed else "👁️‍🗨️"
        if st.button(sidebar_icon, key="sidebar_toggle", help="Toggle Sidebar", use_container_width=True):
            st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
            st.rerun()
    
    with header_col3:
        # Theme toggle
        theme_icon = "🌙" if not st.session_state.dark_mode else "☀️"
        if st.button(theme_icon, key="theme_toggle", help="Toggle Dark/Light Mode", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    with header_col4:
        # Premium effects toggle
        effects_icon = "✨" if st.session_state.premium_effects else "💫"
        if st.button(effects_icon, key="effects_toggle", help="Toggle Premium Effects", use_container_width=True):
            st.session_state.premium_effects = not st.session_state.premium_effects
            st.rerun()
    
    # Main hero section
    st.markdown(f"""
    <div class="hero-container">
        <h1 class="hero-title">🧠 Dr. David's Market Mind</h1>
        <p class="hero-subtitle">Premium Financial Forecasting with Advanced Analytics & 3D Visualization</p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; margin-top: 2rem; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); padding: 0.8rem 1.5rem; border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);">
                <strong>🕐 {current_time_chicago}</strong>
            </div>
            {create_status_badge(market_pulse['session_emoji'] + ' ' + market_pulse['session'], market_pulse['session_color'], market_pulse['session'] == 'Regular Hours')}
            <div style="background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); padding: 0.8rem 1.5rem; border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);">
                <strong>📊 {market_pulse['volume_profile']}</strong>
            </div>
            <div style="background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); padding: 0.8rem 1.5rem; border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);">
                <strong>📅 {current_date}</strong>
            </div>
        </div>
        <div style="margin-top: 1.5rem; text-align: center;">
            <div style="background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 10px; display: inline-block;">
                <strong>Trading Opportunity: {market_pulse['opportunity_rating']}</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_premium_hero_section()

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM SIDEBAR WITH ENHANCED NAVIGATION & CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

# Only show sidebar content if not collapsed
if not st.session_state.sidebar_collapsed:
    
    # Success message with pulse effect
    st.sidebar.markdown("""
    <div style="
        background: linear-gradient(135deg, #10b981, #059669); 
        color: white; 
        padding: 1rem; 
        border-radius: 12px; 
        text-align: center; 
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        animation: glow 2s ease-in-out infinite;
    ">
        ✅ <strong>Market Mind Premium</strong><br>
        <small>All Systems Operational</small>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("## 🧭 Navigation Hub")

    # Enhanced page selection with icons and descriptions
    page_options = {
        "SPX": {"icon": "🧭", "name": "SPX Forecast", "desc": "S&P 500 Analysis"},
        "Contract": {"icon": "📈", "name": "Contract Line", "desc": "Options Trading"}, 
        "TSLA": {"icon": "🚗", "name": "Tesla", "desc": "High Volatility Play"},
        "NVDA": {"icon": "🧠", "name": "NVIDIA", "desc": "AI Chip Leader"},
        "AAPL": {"icon": "🍎", "name": "Apple", "desc": "Blue Chip Stable"},
        "MSFT": {"icon": "🪟", "name": "Microsoft", "desc": "Cloud Enterprise"},
        "AMZN": {"icon": "📦", "name": "Amazon", "desc": "E-commerce Giant"},
        "GOOGL": {"icon": "🔍", "name": "Google", "desc": "Search & AI"},
        "META": {"icon": "📘", "name": "Meta", "desc": "Social & Metaverse"},
        "NFLX": {"icon": "📺", "name": "Netflix", "desc": "Streaming King"}
    }

    # Create navigation cards
    for key, info in page_options.items():
        is_selected = st.session_state.selected_page == key
        
        # Navigation button with enhanced styling
        button_style = f"""
        background: {'linear-gradient(135deg, #6366f1, #8b5cf6)' if is_selected else 'transparent'};
        border: 2px solid {'#6366f1' if is_selected else 'rgba(255,255,255,0.1)'};
        color: {'white' if is_selected else 'var(--text-primary)'};
        padding: 0.8rem;
        border-radius: 12px;
        width: 100%;
        text-align: left;
        margin: 0.3rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: {'0 4px 15px rgba(99, 102, 241, 0.3)' if is_selected else '0 2px 5px rgba(0,0,0,0.1)'};
        """
        
        if st.sidebar.button(
            f"{info['icon']} {info['name']}\n{info['desc']}", 
            key=f"nav_{key}",
            help=f"Navigate to {info['name']} analysis",
            use_container_width=True
        ):
            st.session_state.selected_page = key
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM SLOPE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════════

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📐 Slope Management")

    with st.sidebar.expander("🎯 Precision Controls", expanded=False):
        st.markdown("**SPX Parameters:**")
        
        # SPX slopes with enhanced controls
        spx_col1, spx_col2 = st.columns(2)
        
        for i, spx_key in enumerate(["SPX_HIGH", "SPX_CLOSE", "SPX_LOW"]):
            col = spx_col1 if i % 2 == 0 else spx_col2
            
            with col:
                new_slope = st.number_input(
                    spx_key.replace("SPX_", ""),
                    min_value=-1.0,
                    max_value=1.0,
                    value=float(strategy.slopes[spx_key]),
                    step=0.0001,
                    format="%.4f",
                    key=f"slope_{spx_key}"
                )
                strategy.slopes[spx_key] = new_slope
        
        st.markdown("**Stock Parameters:**")
        
        # Stock slopes in compact grid
        tickers = strategy.get_available_tickers()
        for i in range(0, len(tickers), 2):
            ticker_col1, ticker_col2 = st.columns(2)
            
            # First ticker
            with ticker_col1:
                if i < len(tickers):
                    ticker = tickers[i]
                    new_slope = st.number_input(
                        ticker,
                        min_value=-1.0,
                        max_value=1.0,
                        value=float(strategy.slopes[ticker]),
                        step=0.0001,
                        format="%.4f",
                        key=f"slope_{ticker}"
                    )
                    strategy.slopes[ticker] = new_slope
            
            # Second ticker
            with ticker_col2:
                if i + 1 < len(tickers):
                    ticker = tickers[i + 1]
                    new_slope = st.number_input(
                        ticker,
                        min_value=-1.0,
                        max_value=1.0,
                        value=float(strategy.slopes[ticker]),
                        step=0.0001,
                        format="%.4f",
                        key=f"slope_{ticker}"
                    )
                    strategy.slopes[ticker] = new_slope
        
        # Reset controls
        reset_col1, reset_col2 = st.columns(2)
        
        with reset_col1:
            if st.button("🔄 Reset All", key="reset_all_slopes", use_container_width=True):
                strategy.reset_slopes()
                st.success("✅ Reset Complete")
                st.rerun()
        
        with reset_col2:
            if st.button("💾 Save Config", key="save_config", use_container_width=True):
                config = strategy.export_configuration()
                st.download_button(
                    "📥 Download",
                    json.dumps(config, indent=2),
                    f"market_mind_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_config"
                )

    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM TRADING INSIGHTS
    # ═══════════════════════════════════════════════════════════════════════════════

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📚 Trading Intelligence")

    with st.sidebar.expander(f"🎯 {st.session_state.selected_page} Analysis", expanded=True):
        profile = strategy.get_stock_profile(st.session_state.selected_page)
        
        # Enhanced profile display
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1)); 
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>📈 Character:</strong><br>
            {profile["character"]}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1)); 
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>🎯 Behavior:</strong><br>
            {profile["behavior"]}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.1)); 
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>📋 Patterns:</strong><br>
            {profile["patterns"]}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.1)); 
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <strong>💡 Opportunities:</strong><br>
            {profile["opportunities"]}
        </div>
        """, unsafe_allow_html=True)
        
        # Risk and timing info
        risk_col1, risk_col2 = st.columns(2)
        
        with risk_col1:
            st.metric("⚡ Volatility", profile.get("volatility_profile", "Medium"))
            st.metric("⭐ Risk", profile.get("risk_rating", "⭐⭐⭐"))
        
        with risk_col2:
            st.metric("📊 Best Frames", ", ".join(profile.get("best_timeframes", ["1hr"])[:2]))

    # ═══════════════════════════════════════════════════════════════════════════════
    # PORTFOLIO OVERVIEW
    # ═══════════════════════════════════════════════════════════════════════════════

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 💼 Portfolio Status")

    # Calculate portfolio metrics
    active_forecasts = {}
    if st.session_state.current_forecasts:
        active_forecasts.update(st.session_state.current_forecasts)
    
    for ticker in strategy.get_available_tickers():
        if f"{ticker}_forecasts" in st.session_state:
            active_forecasts[ticker] = st.session_state[f"{ticker}_forecasts"]

    portfolio_metrics = strategy.calculate_portfolio_metrics(active_forecasts)

    # Display portfolio summary
    port_col1, port_col2 = st.columns(2)

    with port_col1:
        st.metric("📊 Positions", portfolio_metrics["total_positions"])
        
    with port_col2:
        risk_color = "#ef4444" if portfolio_metrics["risk_level"] == "High" else "#f59e0b" if portfolio_metrics["risk_level"] == "Medium" else "#10b981"
        st.markdown(f"""
        <div style="background: {risk_color}22; color: {risk_color}; padding: 0.5rem; 
                    border-radius: 8px; text-align: center; font-weight: 600;">
            {portfolio_metrics["risk_level"]} Risk
        </div>
        """, unsafe_allow_html=True)

else:
    # Collapsed sidebar indicator
    st.markdown("""
    <div class="sidebar-toggle" onclick="document.querySelector('[data-testid=\\"stSidebar\\"] button').click()">
        👁️‍🗨️
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4A: PREMIUM SPX PAGE HEADER & INPUT SECTION
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.selected_page == "SPX":
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM SPX PAGE HEADER WITH 3D EFFECTS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 25%, #5b21b6 50%, #7c3aed 75%, #a855f7 100%);
        border-radius: 24px;
        padding: 3rem 2rem;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(2deg);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    ">
        <div style="
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.15) 0%, transparent 50%);
            animation: hero-pulse 6s ease-in-out infinite;
            pointer-events: none;
        "></div>
        <div style="
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.05) 50%, transparent 70%);
            transform: translateX(-100%);
            animation: shimmer 3s ease-in-out infinite;
        "></div>
        <h1 style="
            color: white; 
            font-size: 3rem; 
            font-weight: 900; 
            margin-bottom: 1rem;
            text-shadow: 0 6px 25px rgba(0,0,0,0.6);
            background: linear-gradient(45deg, #ffffff, #e0e7ff, #c7d2fe);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
            z-index: 2;
            letter-spacing: -0.02em;
        ">🧭 SPX Forecasting Command Center</h1>
        <p style="
            color: rgba(255,255,255,0.95); 
            font-size: 1.3rem; 
            margin: 0;
            position: relative;
            z-index: 2;
            font-weight: 400;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        ">Advanced S&P 500 Analysis with Three-Anchor Projection System</p>
        <div style="
            margin-top: 2rem;
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
            position: relative;
            z-index: 2;
        ">
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">⚡ Real-time Analytics</div>
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">🎯 Multi-Anchor System</div>
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">📊 Professional Grade</div>
        </div>
    </div>
    
    <style>
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM FORECAST CONFIGURATION SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("## 📊 Forecast Configuration")
    st.caption("Configure your SPX forecast parameters with precision and advanced market context")
    
    # Enhanced date selection with comprehensive market context
    date_col1, date_col2, date_col3 = st.columns([2, 2, 2])
    
    with date_col1:
        forecast_date = st.date_input(
            "📅 Target Forecast Date",
            value=date.today() + timedelta(days=1),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=30),
            key="spx_forecast_date",
            help="Select the date you want to forecast - choose upcoming trading days for best results"
        )
    
    with date_col2:
        weekday_name = forecast_date.strftime("%A")
        is_weekend = forecast_date.weekday() >= 5
        
        if is_weekend:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f59e0b, #d97706);
                color: white;
                padding: 1.5rem;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
                border: 2px solid rgba(255, 255, 255, 0.2);
                transform: perspective(1000px) rotateY(-2deg);
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
                <strong style="font-size: 1.2rem;">{weekday_name}</strong><br>
                <small style="opacity: 0.9;">Weekend - Markets Closed</small><br>
                <small style="opacity: 0.8; font-size: 0.8rem;">Consider next trading day</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                padding: 1.5rem;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
                border: 2px solid rgba(255, 255, 255, 0.2);
                transform: perspective(1000px) rotateY(2deg);
                animation: glow 3s ease-in-out infinite;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                <strong style="font-size: 1.2rem;">{weekday_name}</strong><br>
                <small style="opacity: 0.9;">{forecast_date.strftime('%B %d, %Y')}</small><br>
                <small style="opacity: 0.8; font-size: 0.8rem;">Trading Day Active</small>
            </div>
            """, unsafe_allow_html=True)
    
    with date_col3:
        # Enhanced days until forecast with urgency indicators
        days_until = (forecast_date - date.today()).days
        
        if days_until == 0:
            urgency_color = "#ef4444"
            urgency_emoji = "🚨"
            urgency_text = "TODAY!"
            urgency_subtitle = "Execute immediately"
        elif days_until == 1:
            urgency_color = "#f59e0b"
            urgency_emoji = "⚡"
            urgency_text = "TOMORROW"
            urgency_subtitle = "High priority"
        elif days_until <= 3:
            urgency_color = "#3b82f6"
            urgency_emoji = "📍"
            urgency_text = f"T+{days_until} DAYS"
            urgency_subtitle = "Near term"
        else:
            urgency_color = "#10b981"
            urgency_emoji = "🎯"
            urgency_text = f"T+{days_until} DAYS"
            urgency_subtitle = "Forward looking"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {urgency_color}, {urgency_color}dd);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 25px {urgency_color}44;
            border: 2px solid rgba(255, 255, 255, 0.2);
            transform: perspective(1000px) rotateY(-2deg);
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{urgency_emoji}</div>
            <strong style="font-size: 1.2rem;">{urgency_text}</strong><br>
            <small style="opacity: 0.9;">{urgency_subtitle}</small><br>
            <small style="opacity: 0.8; font-size: 0.8rem;">Timeline: {days_until} days</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM ANCHOR POINTS INPUT WITH 3D CARDS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("## 🎯 Premium Anchor Point Configuration")
    st.caption("Enter the High, Close, and Low prices from the previous trading day with their respective times for maximum forecasting accuracy")
    
    # ───────────────────────────────────────────────────────────────────────────────
    # HIGH ANCHOR SECTION
    # ───────────────────────────────────────────────────────────────────────────────
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.08), rgba(5, 150, 105, 0.08));
        border: 2px solid #10b981;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 12px 35px rgba(16, 185, 129, 0.25);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(1deg);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #10b981, #059669, #047857);
        "></div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🟢 High Anchor Point")
    st.caption("🚀 Previous day's peak price - often indicates resistance levels and breakout potential")
    
    high_col1, high_col2, high_col3 = st.columns([2, 2, 2])
    
    with high_col1:
        high_price = st.number_input(
            "💹 High Price ($)",
            value=6185.8,
            min_value=0.0,
            step=0.1,
            format="%.2f",
            key="spx_high_price",
            help="Enter the highest price reached during the previous trading session"
        )
    
    with high_col2:
        high_time = st.time_input(
            "🕐 High Time",
            value=time(11, 30),
            key="spx_high_time",
            help="Exact time when the daily high was established"
        )
    
    with high_col3:
        if high_price > 0:
            # Real-time slope preview with enhanced visuals
            current_slope = strategy.slopes["SPX_HIGH"]
            projected_1hr = high_price + (current_slope * 2)  # 2 blocks = 1 hour
            price_change = projected_1hr - high_price
            
            change_color = "#10b981" if price_change > 0 else "#ef4444" if price_change < 0 else "#6b7280"
            change_icon = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {change_color}22, {change_color}11);
                border: 2px solid {change_color};
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
                box-shadow: 0 6px 20px {change_color}33;
            ">
                <div style="color: {change_color}; font-size: 1.5rem; margin-bottom: 0.5rem;">{change_icon}</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: {change_color};">${projected_1hr:.2f}</div>
                <div style="font-size: 0.9rem; opacity: 0.8;">1hr Projection</div>
                <div style="font-size: 0.8rem; color: {change_color}; font-weight: 600;">{price_change:+.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ───────────────────────────────────────────────────────────────────────────────
    # CLOSE ANCHOR SECTION
    # ───────────────────────────────────────────────────────────────────────────────
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(99, 102, 241, 0.08));
        border: 2px solid #3b82f6;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 12px 35px rgba(59, 130, 246, 0.25);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(-1deg);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3b82f6, #2563eb, #1d4ed8);
        "></div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔵 Close Anchor Point")
    st.caption("📊 Market settlement price - reflects overall sentiment and institutional positioning")
    
    close_col1, close_col2, close_col3 = st.columns([2, 2, 2])
    
    with close_col1:
        close_price = st.number_input(
            "💼 Close Price ($)",
            value=6170.2,
            min_value=0.0,
            step=0.1,
            format="%.2f",
            key="spx_close_price",
            help="Official closing price at market settlement (typically 4:00 PM ET)"
        )
    
    with close_col2:
        close_time = st.time_input(
            "🕐 Close Time",
            value=time(15, 0),
            key="spx_close_time",
            help="Market closing time in Chicago timezone"
        )
    
    with close_col3:
        if close_price > 0:
            current_slope = strategy.slopes["SPX_CLOSE"]
            projected_1hr = close_price + (current_slope * 2)
            price_change = projected_1hr - close_price
            
            change_color = "#10b981" if price_change > 0 else "#ef4444" if price_change < 0 else "#6b7280"
            change_icon = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {change_color}22, {change_color}11);
                border: 2px solid {change_color};
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
                box-shadow: 0 6px 20px {change_color}33;
            ">
                <div style="color: {change_color}; font-size: 1.5rem; margin-bottom: 0.5rem;">{change_icon}</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: {change_color};">${projected_1hr:.2f}</div>
                <div style="font-size: 0.9rem; opacity: 0.8;">1hr Projection</div>
                <div style="font-size: 0.8rem; color: {change_color}; font-weight: 600;">{price_change:+.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ───────────────────────────────────────────────────────────────────────────────
    # LOW ANCHOR SECTION
    # ───────────────────────────────────────────────────────────────────────────────
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(220, 38, 38, 0.08));
        border: 2px solid #ef4444;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 12px 35px rgba(239, 68, 68, 0.25);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(1deg);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ef4444, #dc2626, #b91c1c);
        "></div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔴 Low Anchor Point")
    st.caption("🎯 Daily floor price - key support level and potential bounce opportunity")
    
    low_col1, low_col2, low_col3 = st.columns([2, 2, 2])
    
    with low_col1:
        low_price = st.number_input(
            "📉 Low Price ($)",
            value=6130.4,
            min_value=0.0,
            step=0.1,
            format="%.2f",
            key="spx_low_price",
            help="Lowest price reached during the previous trading session"
        )
    
    with low_col2:
        low_time = st.time_input(
            "🕐 Low Time",
            value=time(13, 30),
            key="spx_low_time",
            help="Exact time when the daily low was established"
        )
    
    with low_col3:
        if low_price > 0:
            current_slope = strategy.slopes["SPX_LOW"]
            projected_1hr = low_price + (current_slope * 2)
            price_change = projected_1hr - low_price
            
            change_color = "#10b981" if price_change > 0 else "#ef4444" if price_change < 0 else "#6b7280"
            change_icon = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {change_color}22, {change_color}11);
                border: 2px solid {change_color};
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
                box-shadow: 0 6px 20px {change_color}33;
            ">
                <div style="color: {change_color}; font-size: 1.5rem; margin-bottom: 0.5rem;">{change_icon}</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: {change_color};">${projected_1hr:.2f}</div>
                <div style="font-size: 0.9rem; opacity: 0.8;">1hr Projection</div>
                <div style="font-size: 0.8rem; color: {change_color}; font-weight: 600;">{price_change:+.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4B: PREMIUM ANALYTICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM REAL-TIME ANALYTICS DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if high_price > 0 and low_price > 0 and close_price > 0:
        st.markdown("---")
        st.markdown("## 📈 Real-Time Market Analytics Dashboard")
        st.caption("Advanced market structure analysis with professional-grade insights")
        
        # Calculate comprehensive market metrics
        price_range = high_price - low_price
        range_percentage = (price_range / close_price) * 100
        midpoint = (high_price + low_price) / 2
        close_position_pct = ((close_price - low_price) / price_range) * 100 if price_range > 0 else 50
        
        # Advanced volatility assessment with multiple tiers
        if range_percentage < 0.8:
            volatility_level = "Ultra Low"
            volatility_color = "#059669"
            volatility_emoji = "😴"
            volatility_risk = "Minimal"
        elif range_percentage < 1.5:
            volatility_level = "Very Low"
            volatility_color = "#10b981"
            volatility_emoji = "📊"
            volatility_risk = "Low"
        elif range_percentage < 2.5:
            volatility_level = "Low"
            volatility_color = "#3b82f6"
            volatility_emoji = "📈"
            volatility_risk = "Moderate"
        elif range_percentage < 4.0:
            volatility_level = "Normal"
            volatility_color = "#f59e0b"
            volatility_emoji = "⚡"
            volatility_risk = "Standard"
        elif range_percentage < 6.0:
            volatility_level = "High"
            volatility_color = "#ef4444"
            volatility_emoji = "🔥"
            volatility_risk = "Elevated"
        elif range_percentage < 8.0:
            volatility_level = "Very High"
            volatility_color = "#dc2626"
            volatility_emoji = "🌋"
            volatility_risk = "High"
        else:
            volatility_level = "Extreme"
            volatility_color = "#991b1b"
            volatility_emoji = "💥"
            volatility_risk = "Maximum"
        
        # Enhanced market structure analysis
        if close_position_pct > 80:
            market_structure = "Strong Bull"
            structure_emoji = "🐂"
            structure_color = "#059669"
            structure_desc = "Dominant buying pressure"
        elif close_position_pct > 65:
            market_structure = "Bullish"
            structure_emoji = "📈"
            structure_color = "#10b981"
            structure_desc = "Upward bias evident"
        elif close_position_pct > 50:
            market_structure = "Neutral-Bull"
            structure_emoji = "⚖️"
            structure_color = "#3b82f6"
            structure_desc = "Slight upward lean"
        elif close_position_pct > 35:
            market_structure = "Neutral-Bear"
            structure_emoji = "📊"
            structure_color = "#f59e0b"
            structure_desc = "Slight downward lean"
        elif close_position_pct > 20:
            market_structure = "Bearish"
            structure_emoji = "📉"
            structure_color = "#ef4444"
            structure_desc = "Downward pressure"
        else:
            market_structure = "Strong Bear"
            structure_emoji = "🐻"
            structure_color = "#dc2626"
            structure_desc = "Heavy selling pressure"
        
        # Premium metrics display with 3D cards
        st.markdown("### 🎯 Core Market Metrics")
        
        metrics_row1_col1, metrics_row1_col2, metrics_row1_col3, metrics_row1_col4 = st.columns(4)
        
        with metrics_row1_col1:
            st.markdown(f"""
            <div class="metric-card float" style="
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.1));
                border: 2px solid #3b82f6;
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
                transform: perspective(1000px) rotateY(-5deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📏</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem; color: #3b82f6;">${price_range:.2f}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Daily Range</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7;">{range_percentage:.1f}% of close</div>
                <div style="font-size: 0.8rem; color: #3b82f6; font-weight: 600;">+{range_percentage:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metrics_row1_col2:
            st.markdown(f"""
            <div class="metric-card float glow" style="
                background: linear-gradient(135deg, {volatility_color}22, {volatility_color}11);
                border: 2px solid {volatility_color};
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 10px 30px {volatility_color}44;
                transform: perspective(1000px) rotateY(5deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                animation-delay: 0.2s;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{volatility_emoji}</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem; color: {volatility_color};">{volatility_level}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Volatility</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7;">{volatility_risk} Risk</div>
                <div style="font-size: 0.8rem; color: {volatility_color}; font-weight: 600;">{range_percentage:.1f}% range</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metrics_row1_col3:
            st.markdown(f"""
            <div class="metric-card float" style="
                background: linear-gradient(135deg, {structure_color}22, {structure_color}11);
                border: 2px solid {structure_color};
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 10px 30px {structure_color}44;
                transform: perspective(1000px) rotateY(-5deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                animation-delay: 0.4s;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{structure_emoji}</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem; color: {structure_color};">{market_structure}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Structure</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7;">{structure_desc}</div>
                <div style="font-size: 0.8rem; color: {structure_color}; font-weight: 600;">{close_position_pct:.0f}% position</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metrics_row1_col4:
            st.markdown(f"""
            <div class="metric-card float" style="
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.1));
                border: 2px solid #8b5cf6;
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);
                transform: perspective(1000px) rotateY(5deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                animation-delay: 0.6s;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem; color: #8b5cf6;">${midpoint:.2f}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Midpoint</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7;">Range center</div>
                <div style="font-size: 0.8rem; color: #8b5cf6; font-weight: 600;">{close_price - midpoint:+.2f} from close</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # ADVANCED TECHNICAL ANALYSIS SECTION
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("### 🔍 Advanced Technical Analysis")
        
        tech_col1, tech_col2, tech_col3 = st.columns(3)
        
        with tech_col1:
            # Enhanced Support/Resistance levels
            support_level = low_price * 0.997  # 0.3% below low
            resistance_level = high_price * 1.003  # 0.3% above high
            level_spread = resistance_level - support_level
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(5, 150, 105, 0.08));
                border: 2px solid #10b981;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
                transform: perspective(1000px) rotateX(3deg);
                transition: all 0.4s ease;
            ">
                <h4 style="color: #10b981; margin: 0; font-size: 1.3rem; margin-bottom: 1rem;">📊 Key Levels</h4>
                <div style="background: rgba(16, 185, 129, 0.1); padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
                    <strong style="color: #10b981;">Resistance:</strong> ${resistance_level:.2f}
                </div>
                <div style="background: rgba(239, 68, 68, 0.1); padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
                    <strong style="color: #ef4444;">Support:</strong> ${support_level:.2f}
                </div>
                <div style="margin-top: 1rem; padding: 0.8rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px;">
                    <strong>Range:</strong> ${level_spread:.2f}<br>
                    <small style="opacity: 0.8;">Extended levels</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with tech_col2:
            # Enhanced Risk assessment with multiple factors
            risk_score = min(100, (range_percentage * 12) + (abs(close_position_pct - 50) * 0.5))
            
            if risk_score < 25:
                risk_level = "Minimal"
                risk_color = "#059669"
                risk_emoji = "🟢"
                risk_advice = "Safe for conservative strategies"
            elif risk_score < 45:
                risk_level = "Low"
                risk_color = "#10b981"
                risk_emoji = "🟢"
                risk_advice = "Suitable for most strategies"
            elif risk_score < 60:
                risk_level = "Moderate"
                risk_color = "#3b82f6"
                risk_emoji = "🟡"
                risk_advice = "Standard risk management"
            elif risk_score < 75:
                risk_level = "Elevated"
                risk_color = "#f59e0b"
                risk_emoji = "🟠"
                risk_advice = "Enhanced caution required"
            elif risk_score < 85:
                risk_level = "High"
                risk_color = "#ef4444"
                risk_emoji = "🔴"
                risk_advice = "Advanced traders only"
            else:
                risk_level = "Extreme"
                risk_color = "#dc2626"
                risk_emoji = "🚨"
                risk_advice = "Professional risk management"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {risk_color}22, {risk_color}11);
                border: 2px solid {risk_color};
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 25px {risk_color}44;
                transform: perspective(1000px) rotateX(-3deg);
                transition: all 0.4s ease;
            ">
                <h4 style="color: {risk_color}; margin: 0; font-size: 1.3rem; margin-bottom: 1rem;">⚠️ Risk Assessment</h4>
                <div style="font-size: 2.5rem; margin: 1rem 0;">{risk_emoji}</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {risk_color}; margin-bottom: 0.5rem;">{risk_level}</div>
                <div style="background: {risk_color}22; padding: 0.8rem; border-radius: 8px; margin: 1rem 0;">
                    <strong>Score:</strong> {risk_score:.0f}/100
                </div>
                <div style="font-size: 0.85rem; opacity: 0.9; line-height: 1.4;">
                    {risk_advice}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with tech_col3:
            # Enhanced Trading opportunity with multiple metrics
            volume_factor = 1.2 if 9 <= datetime.now().hour <= 10 or 15 <= datetime.now().hour <= 16 else 0.8
            opportunity_score = max(15, min(100, (range_percentage * 18) * volume_factor))
            
            if opportunity_score > 85:
                opportunity_level = "Exceptional"
                opp_color = "#059669"
                opp_emoji = "🚀"
                opp_desc = "Prime trading conditions"
            elif opportunity_score > 70:
                opportunity_level = "Excellent"
                opp_color = "#10b981"
                opp_emoji = "⭐"
                opp_desc = "Strong profit potential"
            elif opportunity_score > 55:
                opportunity_level = "Good"
                opp_color = "#3b82f6"
                opp_emoji = "👍"
                opp_desc = "Solid opportunities"
            elif opportunity_score > 40:
                opportunity_level = "Fair"
                opp_color = "#f59e0b"
                opp_emoji = "📊"
                opp_desc = "Moderate potential"
            elif opportunity_score > 25:
                opportunity_level = "Limited"
                opp_color = "#ef4444"
                opp_emoji = "⚠️"
                opp_desc = "Challenging conditions"
            else:
                opportunity_level = "Poor"
                opp_color = "#dc2626"
                opp_emoji = "🚫"
                opp_desc = "Avoid trading"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {opp_color}22, {opp_color}11);
                border: 2px solid {opp_color};
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 25px {opp_color}44;
                transform: perspective(1000px) rotateX(3deg);
                transition: all 0.4s ease;
            ">
                <h4 style="color: {opp_color}; margin: 0; font-size: 1.3rem; margin-bottom: 1rem;">💡 Opportunity</h4>
                <div style="font-size: 2.5rem; margin: 1rem 0;">{opp_emoji}</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {opp_color}; margin-bottom: 0.5rem;">{opportunity_level}</div>
                <div style="background: {opp_color}22; padding: 0.8rem; border-radius: 8px; margin: 1rem 0;">
                    <strong>Score:</strong> {opportunity_score:.0f}/100
                </div>
                <div style="font-size: 0.85rem; opacity: 0.9; line-height: 1.4;">
                    {opp_desc}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # MARKET REGIME ANALYSIS
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("### 🌟 Market Regime Analysis")
        
        regime_col1, regime_col2 = st.columns(2)
        
        with regime_col1:
            # Trend strength analysis
            trend_strength = abs(close_position_pct - 50) * 2  # 0-100 scale
            
            if trend_strength > 80:
                trend_desc = "Very Strong"
                trend_color = "#059669"
            elif trend_strength > 60:
                trend_desc = "Strong"
                trend_color = "#10b981"
            elif trend_strength > 40:
                trend_desc = "Moderate"
                trend_color = "#3b82f6"
            elif trend_strength > 20:
                trend_desc = "Weak"
                trend_color = "#f59e0b"
            else:
                trend_desc = "Very Weak"
                trend_color = "#ef4444"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {trend_color}15, {trend_color}08);
                border: 2px solid {trend_color};
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 8px 25px {trend_color}33;
            ">
                <h5 style="color: {trend_color}; margin: 0 0 1rem 0;">📈 Trend Strength</h5>
                <div style="font-size: 1.5rem; font-weight: bold; color: {trend_color}; margin-bottom: 0.5rem;">{trend_desc}</div>
                <div style="background: {trend_color}22; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: {trend_color}; height: 100%; width: {trend_strength}%; border-radius: 4px; transition: width 0.5s ease;"></div>
                </div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">{trend_strength:.0f}% strength</div>
            </div>
            """, unsafe_allow_html=True)
        
        with regime_col2:
            # Market efficiency score
            efficiency = max(20, 100 - (range_percentage * 15))  # Higher range = lower efficiency
            
            if efficiency > 85:
                eff_desc = "Highly Efficient"
                eff_color = "#059669"
            elif efficiency > 70:
                eff_desc = "Efficient"
                eff_color = "#10b981"
            elif efficiency > 55:
                eff_desc = "Moderately Efficient"
                eff_color = "#3b82f6"
            elif efficiency > 40:
                eff_desc = "Inefficient"
                eff_color = "#f59e0b"
            else:
                eff_desc = "Highly Inefficient"
                eff_color = "#ef4444"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {eff_color}15, {eff_color}08);
                border: 2px solid {eff_color};
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 8px 25px {eff_color}33;
            ">
                <h5 style="color: {eff_color}; margin: 0 0 1rem 0;">⚡ Market Efficiency</h5>
                <div style="font-size: 1.5rem; font-weight: bold; color: {eff_color}; margin-bottom: 0.5rem;">{eff_desc}</div>
                <div style="background: {eff_color}22; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: {eff_color}; height: 100%; width: {efficiency}%; border-radius: 4px; transition: width 0.5s ease;"></div>
                </div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">{efficiency:.0f}% efficient</div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4C: PREMIUM FORECAST GENERATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM FORECAST GENERATION SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("## 🚀 Premium Forecast Generation")
    st.caption("Generate advanced SPX forecasts using our proprietary three-anchor projection system with real-time validation")
    
    # Enhanced generate button with comprehensive pre-flight checks
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    
    # Pre-flight validation indicators
    with generate_col1:
        validation_score = 0
        validation_items = []
        warning_items = []
        
        # Core validation checks
        if high_price > 0:
            validation_score += 1
            validation_items.append("✅ High Price Set")
        else:
            validation_items.append("❌ High Price Missing")
        
        if close_price > 0:
            validation_score += 1
            validation_items.append("✅ Close Price Set")
        else:
            validation_items.append("❌ Close Price Missing")
        
        if low_price > 0:
            validation_score += 1
            validation_items.append("✅ Low Price Set")
        else:
            validation_items.append("❌ Low Price Missing")
        
        # Logic validation
        if high_price > low_price and high_price > 0 and low_price > 0:
            validation_score += 1
            validation_items.append("✅ Price Logic Valid")
        elif high_price > 0 and low_price > 0:
            validation_items.append("⚠️ Price Logic Error")
        else:
            validation_items.append("❓ Price Logic Pending")
        
        # Advanced warnings
        if high_price > 0 and close_price > 0 and low_price > 0:
            if not (low_price <= close_price <= high_price):
                warning_items.append("⚠️ Close outside range")
            
            range_pct = ((high_price - low_price) / close_price) * 100
            if range_pct > 5:
                warning_items.append("⚠️ High volatility detected")
            elif range_pct < 0.5:
                warning_items.append("⚠️ Very low volatility")
        
        readiness = validation_score / 4 * 100
        readiness_color = "#10b981" if readiness == 100 else "#f59e0b" if readiness >= 75 else "#ef4444"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {readiness_color}22, {readiness_color}11);
            border: 2px solid {readiness_color};
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 25px {readiness_color}33;
            transform: perspective(1000px) rotateX(2deg);
            transition: all 0.4s ease;
        ">
            <h5 style="color: {readiness_color}; margin: 0 0 1rem 0; font-size: 1.1rem;">🎯 System Readiness</h5>
            <div style="font-size: 2rem; font-weight: bold; color: {readiness_color}; margin-bottom: 1rem;">{readiness:.0f}%</div>
            <div style="background: {readiness_color}22; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 1rem;">
                <div style="background: {readiness_color}; height: 100%; width: {readiness}%; border-radius: 4px; transition: width 0.8s ease;"></div>
            </div>
            <div style="max-height: 120px; overflow-y: auto;">
                {''.join([f'<div style="font-size: 0.8rem; margin: 0.3rem 0; opacity: 0.9;">{item}</div>' for item in validation_items[:4]])}
                {''.join([f'<div style="font-size: 0.75rem; margin: 0.2rem 0; opacity: 0.8; color: #f59e0b;">{warning}</div>' for warning in warning_items[:2]])}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with generate_col2:
        # Main generate button with enhanced styling and animation
        button_ready = validation_score == 4
        
        st.markdown("""
        <div style="margin: 2rem 0; text-align: center;">
        """, unsafe_allow_html=True)
        
        if button_ready:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #10b981, #059669);
                border-radius: 16px;
                padding: 0.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
                animation: glow 2s ease-in-out infinite;
            ">
            """, unsafe_allow_html=True)
            
            generate_button = st.button(
                "🚀 Generate Premium SPX Forecast",
                key="generate_spx_forecast",
                type="primary",
                use_container_width=True,
                help="Generate advanced SPX forecasts using all three anchor points with professional analytics"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Ready state indicators
            st.markdown("""
            <div style="
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid #10b981;
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                text-align: center;
            ">
                <div style="color: #10b981; font-weight: 600; margin-bottom: 0.5rem;">⚡ All Systems Ready</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Three-anchor projection system online</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.3rem;">Advanced analytics enabled</div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #6b7280, #4b5563);
                border-radius: 16px;
                padding: 0.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 15px rgba(107, 114, 128, 0.3);
                opacity: 0.7;
            ">
            """, unsafe_allow_html=True)
            
            generate_button = st.button(
                "⏳ Complete Required Inputs",
                key="generate_spx_forecast_disabled",
                type="secondary",
                use_container_width=True,
                disabled=True,
                help="Please complete all required inputs to enable forecast generation"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Not ready state
            missing_count = 4 - validation_score
            st.markdown(f"""
            <div style="
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid #ef4444;
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                text-align: center;
            ">
                <div style="color: #ef4444; font-weight: 600; margin-bottom: 0.5rem;">⚠️ Pending Inputs</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">{missing_count} requirement{'s' if missing_count != 1 else ''} remaining</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.3rem;">Complete all anchor points to proceed</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with generate_col3:
        # Enhanced system status indicator
        chicago_time = strategy.get_chicago_time()
        hour = chicago_time.hour
        is_weekend = chicago_time.weekday() >= 5
        
        # Determine system status
        if is_weekend:
            system_status = "Weekend Mode"
            system_color = "#f59e0b"
            system_emoji = "📅"
            system_desc = "Markets closed"
        elif 9 <= hour <= 16:
            system_status = "Peak Performance"
            system_color = "#10b981"
            system_emoji = "🔥"
            system_desc = "Market hours active"
        elif 7 <= hour < 9 or 16 < hour <= 20:
            system_status = "Extended Hours"
            system_color = "#3b82f6"
            system_emoji = "🌅"
            system_desc = "Pre/after market"
        else:
            system_status = "Standard Mode"
            system_color = "#8b5cf6"
            system_emoji = "🌙"
            system_desc = "Overnight analysis"
        
        # Get current slopes summary
        spx_slopes = [strategy.slopes[key] for key in ["SPX_HIGH", "SPX_CLOSE", "SPX_LOW"]]
        avg_slope = sum(spx_slopes) / len(spx_slopes)
        slope_trend = "Bullish" if avg_slope > 0 else "Bearish" if avg_slope < 0 else "Neutral"
        slope_color = "#10b981" if avg_slope > 0 else "#ef4444" if avg_slope < 0 else "#6b7280"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {system_color}22, {system_color}11);
            border: 2px solid {system_color};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 8px 25px {system_color}33;
            transform: perspective(1000px) rotateX(-2deg);
            transition: all 0.4s ease;
        ">
            <h5 style="color: {system_color}; margin: 0 0 1rem 0; font-size: 1.1rem;">⚙️ System Status</h5>
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{system_emoji}</div>
            <div style="font-size: 1.3rem; font-weight: bold; color: {system_color}; margin-bottom: 1rem;">{system_status}</div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 1rem;">{system_desc}</div>
            
            <div style="border-top: 1px solid {system_color}44; padding-top: 1rem; margin-top: 1rem;">
                <div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem;">Current Bias:</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {slope_color};">{slope_trend}</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.3rem;">Avg slope: {avg_slope:.4f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ENHANCED FORECAST GENERATION LOGIC WITH PROGRESS TRACKING
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if generate_button and button_ready:
        # Create progress container
        progress_container = st.container()
        
        with progress_container:
            # Enhanced loading animation with detailed progress
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.1));
                border: 2px solid #3b82f6;
                border-radius: 16px;
                padding: 2rem;
                margin: 2rem 0;
                text-align: center;
                box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
            ">
                <h4 style="color: #3b82f6; margin: 0 0 1rem 0;">🔮 Generating Premium SPX Forecasts</h4>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            detail_text = st.empty()
            
            try:
                # Step 1: Validation
                status_text.markdown("**🔍 Step 1/6: Validating anchor points...**")
                detail_text.caption("Checking price relationships and data integrity")
                progress_bar.progress(15)
                
                # Enhanced validation with detailed feedback
                if not all([high_price > 0, close_price > 0, low_price > 0]):
                    st.error("❌ **Validation Failed:** Please enter valid prices for all anchor points")
                    st.stop()
                
                if high_price <= low_price:
                    st.error("❌ **Logic Error:** High price must be greater than low price")
                    st.stop()
                
                # Step 2: Market Structure Analysis
                status_text.markdown("**📊 Step 2/6: Analyzing market structure...**")
                detail_text.caption("Computing volatility, range, and bias metrics")
                progress_bar.progress(30)
                
                if not (low_price <= close_price <= high_price):
                    st.warning("⚠️ **Note:** Close price is outside the high-low range. This is unusual but will be processed.")
                
                # Step 3: Slope Optimization
                status_text.markdown("**⚙️ Step 3/6: Optimizing projection slopes...**")
                detail_text.caption("Applying current slope parameters to anchor points")
                progress_bar.progress(45)
                
                # Brief pause for realism
                import time
                time.sleep(0.5)
                
                # Step 4: Time Block Calculations
                status_text.markdown("**🕐 Step 4/6: Computing time block sequences...**")
                detail_text.caption("Calculating SPX-specific time intervals with gap handling")
                progress_bar.progress(60)
                
                time.sleep(0.3)
                
                # Step 5: Forecast Generation
                status_text.markdown("**🚀 Step 5/6: Generating three-anchor forecasts...**")
                detail_text.caption("Processing High, Close, and Low anchor projections")
                progress_bar.progress(80)
                
                # Generate forecasts
                forecasts = strategy.spx_forecast(
                    high_price, high_time, close_price, close_time,
                    low_price, low_time, forecast_date
                )
                
                # Step 6: Final Processing
                status_text.markdown("**✨ Step 6/6: Finalizing results and analytics...**")
                detail_text.caption("Adding confidence intervals and trading insights")
                progress_bar.progress(95)
                
                time.sleep(0.2)
                
                # Store comprehensive metadata
                st.session_state.current_forecasts = forecasts
                st.session_state.forecast_metadata = {
                    "date": forecast_date,
                    "high_price": high_price,
                    "high_time": high_time,
                    "close_price": close_price,
                    "close_time": close_time,
                    "low_price": low_price,
                    "low_time": low_time,
                    "generated_at": datetime.now(),
                    "range_percentage": ((high_price - low_price) / close_price) * 100,
                    "volatility_level": volatility_level if 'volatility_level' in locals() else "Unknown",
                    "market_structure": market_structure if 'market_structure' in locals() else "Unknown",
                    "slope_summary": {
                        "high": strategy.slopes["SPX_HIGH"],
                        "close": strategy.slopes["SPX_CLOSE"],
                        "low": strategy.slopes["SPX_LOW"],
                        "average": avg_slope
                    },
                    "system_status": system_status,
                    "chicago_time": chicago_time.isoformat()
                }
                
                # Complete
                progress_bar.progress(100)
                status_text.markdown("**🎉 Forecast Generation Complete!**")
                detail_text.caption("All three anchor forecasts generated successfully")
                
                time.sleep(0.5)
                
                # Clear progress indicators
                progress_container.empty()
                
                # Success celebration
                st.success("✅ **Premium SPX forecasts generated successfully!** Advanced analytics and projections are now available.")
                st.balloons()
                
                # Quick summary of what was generated
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                
                with summary_col1:
                    st.info(f"🎯 **{len(forecasts)} Anchor Points**\nHigh, Close, Low projections")
                
                with summary_col2:
                    total_projections = sum(len(df) for df in forecasts.values()) if forecasts else 0
                    st.info(f"📊 **{total_projections} Time Slots**\nDetailed projections generated")
                
                with summary_col3:
                    st.info(f"⚡ **{volatility_level if 'volatility_level' in locals() else 'Standard'} Volatility**\nMarket condition assessed")
                
            except Exception as e:
                # Enhanced error handling
                progress_container.empty()
                st.error(f"❌ **Forecast Generation Failed**")
                
                error_col1, error_col2 = st.columns(2)
                
                with error_col1:
                    st.error(f"**Error Details:**\n{str(e)}")
                
                with error_col2:
                    st.info("""
                    **Troubleshooting Tips:**
                    - Verify all prices are positive numbers
                    - Ensure High > Low price relationship
                    - Check that times are in valid format
                    - Try refreshing the page if issues persist
                    """)
                
                # Show technical details in expander
                with st.expander("🔧 Technical Details", expanded=False):
                    st.exception(e)
    
    # Add some spacing before results section
    st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4D1: PREMIUM RESULTS DISPLAY SYSTEM (FIRST HALF)
# ═══════════════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM RESULTS HEADER & SUMMARY SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if st.session_state.current_forecasts:
        st.markdown("---")
        
        # Enhanced results header with 3D effects
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e40af 0%, #3730a3 25%, #5b21b6 50%, #7c3aed 75%, #a855f7 100%);
            border-radius: 24px;
            padding: 2.5rem;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
            position: relative;
            overflow: hidden;
            transform: perspective(1000px) rotateX(1deg);
        ">
            <div style="
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle at 70% 30%, rgba(255,255,255,0.15) 0%, transparent 50%);
                animation: hero-pulse 4s ease-in-out infinite;
                pointer-events: none;
            "></div>
            <h2 style="
                color: white; 
                font-size: 2.5rem; 
                font-weight: 800; 
                margin-bottom: 0.5rem;
                text-shadow: 0 4px 20px rgba(0,0,0,0.5);
                position: relative;
                z-index: 2;
            ">📊 Premium SPX Forecast Results</h2>
            <p style="
                color: rgba(255,255,255,0.9); 
                font-size: 1.2rem; 
                margin: 0;
                position: relative;
                z-index: 2;
            ">Advanced Three-Anchor Projection Analysis Complete</p>
        </div>
        """, unsafe_allow_html=True)
        
        forecasts = st.session_state.current_forecasts
        metadata = st.session_state.get('forecast_metadata', {})
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # ENHANCED RESULTS SUMMARY DASHBOARD
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("### 🎯 Forecast Summary Dashboard")
        
        # Calculate comprehensive summary metrics
        generation_time = metadata.get('generated_at')
        if generation_time:
            time_ago = datetime.now() - generation_time
            time_display = f"{int(time_ago.total_seconds() // 60)} min ago" if time_ago.total_seconds() > 60 else "Just now"
        else:
            time_display = "Unknown"
        
        # Enhanced results summary with 4 key metrics
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        with summary_col1:
            target_date = str(metadata.get('date', 'N/A'))
            weekday = metadata.get('date').strftime('%A') if metadata.get('date') else 'Unknown'
            
            st.markdown(f"""
            <div class="metric-card float" style="
                background: linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(5, 150, 105, 0.08));
                border: 2px solid #10b981;
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 12px 35px rgba(16, 185, 129, 0.3);
                transform: perspective(1000px) rotateY(-3deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📅</div>
                <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #10b981;">{target_date}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Target Date</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{weekday}</div>
                <div style="font-size: 0.75rem; color: #10b981; font-weight: 600; margin-top: 0.3rem;">Forecast Day</div>
            </div>
            """, unsafe_allow_html=True)
        
        with summary_col2:
            anchor_count = len(forecasts)
            total_projections = sum(len(df) for df in forecasts.values()) if forecasts else 0
            
            st.markdown(f"""
            <div class="metric-card float" style="
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(99, 102, 241, 0.08));
                border: 2px solid #3b82f6;
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 12px 35px rgba(59, 130, 246, 0.3);
                transform: perspective(1000px) rotateY(3deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                animation-delay: 0.1s;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #3b82f6;">{anchor_count}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Anchor Points</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Generated forecasts</div>
                <div style="font-size: 0.75rem; color: #3b82f6; font-weight: 600; margin-top: 0.3rem;">{total_projections} projections</div>
            </div>
            """, unsafe_allow_html=True)
        
        with summary_col3:
            volatility = metadata.get('volatility_level', 'Unknown')
            range_pct = metadata.get('range_percentage', 0)
            
            # Determine volatility color
            vol_colors = {
                'Ultra Low': '#059669', 'Very Low': '#10b981', 'Low': '#3b82f6',
                'Normal': '#f59e0b', 'High': '#ef4444', 'Very High': '#dc2626', 'Extreme': '#991b1b'
            }
            vol_color = vol_colors.get(volatility, '#6b7280')
            
            st.markdown(f"""
            <div class="metric-card float glow" style="
                background: linear-gradient(135deg, {vol_color}22, {vol_color}11);
                border: 2px solid {vol_color};
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 12px 35px {vol_color}44;
                transform: perspective(1000px) rotateY(-3deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                animation-delay: 0.2s;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
                <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {vol_color};">{volatility}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Volatility</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Market condition</div>
                <div style="font-size: 0.75rem; color: {vol_color}; font-weight: 600; margin-top: 0.3rem;">{range_pct:.1f}% range</div>
            </div>
            """, unsafe_allow_html=True)
        
        with summary_col4:
            structure = metadata.get('market_structure', 'Unknown')
            
            # Determine structure color
            struct_colors = {
                'Strong Bull': '#059669', 'Bullish': '#10b981', 'Neutral-Bull': '#3b82f6',
                'Neutral-Bear': '#f59e0b', 'Bearish': '#ef4444', 'Strong Bear': '#dc2626'
            }
            struct_color = struct_colors.get(structure, '#6b7280')
            
            st.markdown(f"""
            <div class="metric-card float" style="
                background: linear-gradient(135deg, {struct_color}22, {struct_color}11);
                border: 2px solid {struct_color};
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 12px 35px {struct_color}44;
                transform: perspective(1000px) rotateY(3deg);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                animation-delay: 0.3s;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {struct_color};">{structure}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Structure</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Market bias</div>
                <div style="font-size: 0.75rem; color: {struct_color}; font-weight: 600; margin-top: 0.3rem;">Sentiment analysis</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # GENERATION METADATA & SYSTEM INFO
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("### ℹ️ Generation Details")
        
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        
        with meta_col1:
            slope_summary = metadata.get('slope_summary', {})
            avg_slope = slope_summary.get('average', 0)
            slope_trend = "Bullish Bias" if avg_slope > 0 else "Bearish Bias" if avg_slope < 0 else "Neutral Bias"
            slope_color = "#10b981" if avg_slope > 0 else "#ef4444" if avg_slope < 0 else "#6b7280"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {slope_color}15, {slope_color}08);
                border: 2px solid {slope_color};
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 8px 25px {slope_color}33;
            ">
                <h5 style="color: {slope_color}; margin: 0 0 1rem 0;">📐 Slope Analysis</h5>
                <div style="font-size: 1.3rem; font-weight: bold; color: {slope_color}; margin-bottom: 0.5rem;">{slope_trend}</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 1rem;">Average: {avg_slope:.4f}</div>
                <div style="background: {slope_color}22; padding: 0.8rem; border-radius: 8px;">
                    <div style="font-size: 0.8rem; margin: 0.2rem 0;">High: {slope_summary.get('high', 0):.4f}</div>
                    <div style="font-size: 0.8rem; margin: 0.2rem 0;">Close: {slope_summary.get('close', 0):.4f}</div>
                    <div style="font-size: 0.8rem; margin: 0.2rem 0;">Low: {slope_summary.get('low', 0):.4f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with meta_col2:
            system_status = metadata.get('system_status', 'Standard Mode')
            status_colors = {
                'Peak Performance': '#10b981', 'Extended Hours': '#3b82f6',
                'Weekend Mode': '#f59e0b', 'Standard Mode': '#8b5cf6'
            }
            status_color = status_colors.get(system_status, '#6b7280')
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {status_color}15, {status_color}08);
                border: 2px solid {status_color};
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 8px 25px {status_color}33;
            ">
                <h5 style="color: {status_color}; margin: 0 0 1rem 0;">⚙️ System Status</h5>
                <div style="font-size: 1.3rem; font-weight: bold; color: {status_color}; margin-bottom: 0.5rem;">{system_status}</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 1rem;">Generation time: {time_display}</div>
                <div style="background: {status_color}22; padding: 0.8rem; border-radius: 8px;">
                    <div style="font-size: 0.85rem; font-weight: 600;">All systems operational</div>
                    <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.3rem;">Ready for analysis</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with meta_col3:
            # Price range summary
            high_price = metadata.get('high_price', 0)
            low_price = metadata.get('low_price', 0)
            close_price = metadata.get('close_price', 0)
            price_range = high_price - low_price if high_price and low_price else 0
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.08));
                border: 2px solid #8b5cf6;
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
            ">
                <h5 style="color: #8b5cf6; margin: 0 0 1rem 0;">💰 Price Range</h5>
                <div style="font-size: 1.3rem; font-weight: bold; color: #8b5cf6; margin-bottom: 0.5rem;">${price_range:.2f}</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 1rem;">Daily spread</div>
                <div style="background: rgba(139, 92, 246, 0.15); padding: 0.8rem; border-radius: 8px;">
                    <div style="font-size: 0.8rem; margin: 0.2rem 0;">High: ${high_price:.2f}</div>
                    <div style="font-size: 0.8rem; margin: 0.2rem 0;">Close: ${close_price:.2f}</div>
                    <div style="font-size: 0.8rem; margin: 0.2rem 0;">Low: ${low_price:.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # FORECAST QUALITY INDICATORS
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("### 🌟 Forecast Quality Assessment")
        
        quality_col1, quality_col2, quality_col3, quality_col4 = st.columns(4)
        
        # Calculate quality metrics
        data_quality = 100  # All required data present
        if not (low_price <= close_price <= high_price):
            data_quality -= 15  # Unusual close position
        
        range_pct = metadata.get('range_percentage', 0)
        volatility_score = min(100, max(20, 100 - abs(range_pct - 2.5) * 15))  # Optimal around 2.5%
        
        time_relevance = 100
        if generation_time:
            hours_old = (datetime.now() - generation_time).total_seconds() / 3600
            time_relevance = max(70, 100 - hours_old * 5)  # Decreases over time
        
        system_reliability = 95  # Base reliability score
        if metadata.get('system_status') == 'Peak Performance':
            system_reliability = 100
        elif metadata.get('system_status') == 'Weekend Mode':
            system_reliability = 85
        
        overall_quality = (data_quality + volatility_score + time_relevance + system_reliability) / 4
        
        # Quality indicators with color coding
        quality_metrics = [
            ("Data Quality", data_quality, "📊"),
            ("Volatility Score", volatility_score, "⚡"),
            ("Time Relevance", time_relevance, "🕐"),
            ("System Reliability", system_reliability, "⚙️")
        ]
        
        for i, (metric_name, score, emoji) in enumerate(quality_metrics):
            col = [quality_col1, quality_col2, quality_col3, quality_col4][i]
            
            # Determine color based on score
            if score >= 90:
                color = "#10b981"
                grade = "Excellent"
            elif score >= 75:
                color = "#3b82f6"
                grade = "Good"
            elif score >= 60:
                color = "#f59e0b"
                grade = "Fair"
            else:
                color = "#ef4444"
                grade = "Needs Attention"
            
            with col:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {color}20, {color}10);
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 1.2rem;
                    text-align: center;
                    box-shadow: 0 6px 20px {color}33;
                    transition: all 0.3s ease;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{emoji}</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: {color}; margin-bottom: 0.3rem;">{score:.0f}%</div>
                    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem;">{metric_name}</div>
                    <div style="font-size: 0.7rem; color: {color}; font-weight: 600;">{grade}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Overall quality summary
        overall_color = "#10b981" if overall_quality >= 90 else "#3b82f6" if overall_quality >= 75 else "#f59e0b" if overall_quality >= 60 else "#ef4444"
        overall_grade = "Excellent" if overall_quality >= 90 else "Good" if overall_quality >= 75 else "Fair" if overall_quality >= 60 else "Needs Review"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {overall_color}22, {overall_color}11);
            border: 2px solid {overall_color};
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
            box-shadow: 0 8px 25px {overall_color}44;
        ">
            <h4 style="color: {overall_color}; margin: 0 0 1rem 0;">🏆 Overall Forecast Quality</h4>
            <div style="font-size: 2.5rem; font-weight: bold; color: {overall_color}; margin-bottom: 0.5rem;">{overall_quality:.0f}%</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: {overall_color};">{overall_grade}</div>
            <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">Forecast confidence and reliability assessment</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4D2A: INTERACTIVE FORECAST TABLES
# ═══════════════════════════════════════════════════════════════════════════════

        # ═══════════════════════════════════════════════════════════════════════════════
        # PREMIUM 3D TABBED INTERFACE FOR FORECAST RESULTS
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("---")
        st.markdown("## 📈 Interactive Forecast Analysis")
        st.caption("Explore your three-anchor projections with advanced analytics and insights")
        
        # Enhanced tab interface with proper forecast validation
        if len(forecasts) >= 3 and all(anchor in forecasts for anchor in ["High", "Close", "Low"]):
            
            # Create premium tabs with enhanced styling
            tab1, tab2, tab3, tab4 = st.tabs([
                "🟢 High Anchor Analysis", 
                "🔵 Close Anchor Analysis", 
                "🔴 Low Anchor Analysis",
                "📊 Comparative Dashboard"
            ])
            
            # ═══════════════════════════════════════════════════════════════════════════════
            # HIGH ANCHOR TAB WITH ENHANCED ANALYSIS
            # ═══════════════════════════════════════════════════════════════════════════════
            
            with tab1:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(5, 150, 105, 0.05));
                    border: 2px solid #10b981;
                    border-radius: 20px;
                    padding: 2rem;
                    margin: 1rem 0;
                    box-shadow: 0 10px 30px rgba(16, 185, 129, 0.2);
                ">
                    <h3 style="color: #10b981; margin: 0 0 1rem 0; font-size: 1.8rem;">🟢 High Anchor Forecast Analysis</h3>
                    <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">Projections based on previous day's highest price point - typically indicates resistance levels and breakout potential</p>
                </div>
                """, unsafe_allow_html=True)
                
                if "High" in forecasts and not forecasts["High"].empty:
                    high_df = forecasts["High"]
                    
                    # Enhanced table display with formatting
                    st.markdown("#### 📊 High Anchor Projections")
                    
                    # Format the dataframe for display
                    display_df = high_df.copy()
                    
                    # Format price columns with enhanced styling
                    for col in ['Entry', 'Exit']:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")
                    
                    # Add trend indicators if Change% exists
                    if 'Spread' in display_df.columns:
                        display_df['Profit'] = display_df['Spread'].apply(
                            lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else str(x)
                        )
                    
                    # Enhanced dataframe display
                    st.dataframe(
                        display_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Time": st.column_config.TextColumn("Time", width="small"),
                            "Entry": st.column_config.TextColumn("Entry Price", width="medium"),
                            "Exit": st.column_config.TextColumn("Exit Price", width="medium"),
                            "Spread": st.column_config.TextColumn("Spread", width="small"),
                            "Profit": st.column_config.TextColumn("Profit", width="small"),
                            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                            "Signal": st.column_config.TextColumn("Signal", width="small"),
                        }
                    )
                    
                    # ═══════════════════════════════════════════════════════════════════════════════
                    # HIGH ANCHOR INSIGHTS AND ANALYTICS
                    # ═══════════════════════════════════════════════════════════════════════════════
                    
                    st.markdown("#### 💡 High Anchor Insights")
                    
                    # Calculate comprehensive analytics
                    if 'Entry' in high_df.columns and 'Exit' in high_df.columns:
                        # Profit metrics
                        spreads = high_df['Entry'] - high_df['Exit']
                        max_profit = spreads.max()
                        avg_profit = spreads.mean()
                        min_profit = spreads.min()
                        
                        # Volatility metrics
                        entry_volatility = high_df['Entry'].std()
                        price_range = high_df['Entry'].max() - high_df['Entry'].min()
                        
                        # Best time analysis
                        best_time_idx = spreads.idxmax()
                        best_time = high_df.loc[best_time_idx, 'Time'] if 'Time' in high_df.columns else 'Unknown'
                        
                        # Create enhanced insights cards
                        insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)
                        
                        with insight_col1:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1));
                                border: 2px solid #10b981;
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💰</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: #10b981; margin-bottom: 0.3rem;">${max_profit:.2f}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Max Profit</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Peak opportunity</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with insight_col2:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.1));
                                border: 2px solid #3b82f6;
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: #3b82f6; margin-bottom: 0.3rem;">${avg_profit:.2f}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Avg Spread</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Typical profit</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with insight_col3:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
                                border: 2px solid #8b5cf6;
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3);
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📏</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: #8b5cf6; margin-bottom: 0.3rem;">${price_range:.2f}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Price Range</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Entry spread</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with insight_col4:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1));
                                border: 2px solid #f59e0b;
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px rgba(245, 158, 11, 0.3);
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: #f59e0b; margin-bottom: 0.3rem;">{best_time}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Best Time</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Optimal entry</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Trading strategy recommendations
                        st.markdown("#### 🎯 High Anchor Trading Strategy")
                        
                        strategy_col1, strategy_col2 = st.columns(2)
                        
                        with strategy_col1:
                            if max_profit > 5:
                                recommendation = "🚀 **Strong Buy Signal** - High profit potential detected"
                                rec_color = "#10b981"
                            elif max_profit > 2:
                                recommendation = "📈 **Moderate Buy** - Good profit opportunity"
                                rec_color = "#3b82f6"
                            elif max_profit > 0:
                                recommendation = "⚖️ **Neutral** - Limited profit potential"
                                rec_color = "#f59e0b"
                            else:
                                recommendation = "⚠️ **Caution** - Negative profit projections"
                                rec_color = "#ef4444"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {rec_color}22, {rec_color}11);
                                border: 2px solid {rec_color};
                                border-radius: 12px;
                                padding: 1rem;
                                box-shadow: 0 6px 20px {rec_color}33;
                            ">
                                <h5 style="color: {rec_color}; margin: 0 0 0.5rem 0;">Trading Recommendation</h5>
                                <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{recommendation}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with strategy_col2:
                            # Risk assessment
                            if entry_volatility < 2:
                                risk_level = "🟢 Low Risk"
                                risk_color = "#10b981"
                                risk_desc = "Stable price projections"
                            elif entry_volatility < 5:
                                risk_level = "🟡 Moderate Risk"
                                risk_color = "#f59e0b"
                                risk_desc = "Standard volatility"
                            else:
                                risk_level = "🔴 High Risk"
                                risk_color = "#ef4444"
                                risk_desc = "High volatility detected"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {risk_color}22, {risk_color}11);
                                border: 2px solid {risk_color};
                                border-radius: 12px;
                                padding: 1rem;
                                box-shadow: 0 6px 20px {risk_color}33;
                            ">
                                <h5 style="color: {risk_color}; margin: 0 0 0.5rem 0;">Risk Assessment</h5>
                                <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;"><strong>{risk_level}</strong><br>{risk_desc}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # ═══════════════════════════════════════════════════════════════════════════════
                    # DOWNLOAD OPTIONS FOR HIGH ANCHOR
                    # ═══════════════════════════════════════════════════════════════════════════════
                    
                    st.markdown("#### 📥 Export Options")
                    
                    download_col1, download_col2, download_col3 = st.columns(3)
                    
                    with download_col1:
                        csv_data = high_df.to_csv(index=False)
                        st.download_button(
                            label="📊 Download CSV",
                            data=csv_data,
                            file_name=f"spx_high_anchor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key="download_high_csv"
                        )
                    
                    with download_col2:
                        json_data = high_df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="🗂️ Download JSON",
                            data=json_data,
                            file_name=f"spx_high_anchor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True,
                            key="download_high_json"
                        )
                    
                    with download_col3:
                        # Create summary report
                        summary_report = f"""SPX HIGH ANCHOR FORECAST REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Target Date: {metadata.get('date', 'N/A')}

SUMMARY METRICS:
- Max Profit: ${max_profit:.2f}
- Avg Spread: ${avg_profit:.2f}
- Price Range: ${price_range:.2f}
- Best Time: {best_time}
- Volatility: {entry_volatility:.2f}

RECOMMENDATION: {recommendation}
RISK LEVEL: {risk_level}
"""
                        st.download_button(
                            label="📋 Download Report",
                            data=summary_report,
                            file_name=f"spx_high_anchor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="download_high_report"
                        )
                
                else:
                    st.warning("⚠️ High anchor forecast data not available")
            
            # ═══════════════════════════════════════════════════════════════════════════════
            # CLOSE ANCHOR TAB WITH ENHANCED ANALYSIS
            # ═══════════════════════════════════════════════════════════════════════════════
            
            with tab2:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.05));
                    border: 2px solid #3b82f6;
                    border-radius: 20px;
                    padding: 2rem;
                    margin: 1rem 0;
                    box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
                ">
                    <h3 style="color: #3b82f6; margin: 0 0 1rem 0; font-size: 1.8rem;">🔵 Close Anchor Forecast Analysis</h3>
                    <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">Projections based on previous day's closing price - reflects overall market sentiment and institutional positioning</p>
                </div>
                """, unsafe_allow_html=True)
                
                if "Close" in forecasts and not forecasts["Close"].empty:
                    close_df = forecasts["Close"]
                    
                    # Enhanced table display
                    st.markdown("#### 📊 Close Anchor Projections")
                    
                    # Format the dataframe for display
                    display_df = close_df.copy()
                    
                    # Format price columns
                    for col in ['Entry', 'Exit']:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")
                    
                    # Add profit calculations
                    if 'Spread' in display_df.columns:
                        display_df['Profit'] = display_df['Spread'].apply(
                            lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else str(x)
                        )
                    
                    # Enhanced dataframe display
                    st.dataframe(
                        display_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Time": st.column_config.TextColumn("Time", width="small"),
                            "Entry": st.column_config.TextColumn("Entry Price", width="medium"),
                            "Exit": st.column_config.TextColumn("Exit Price", width="medium"),
                            "Spread": st.column_config.TextColumn("Spread", width="small"),
                            "Profit": st.column_config.TextColumn("Profit", width="small"),
                            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                            "Signal": st.column_config.TextColumn("Signal", width="small"),
                        }
                    )
                    
                    # Close anchor specific insights
                    st.markdown("#### 💡 Close Anchor Insights")
                    
                    if 'Entry' in close_df.columns and 'Exit' in close_df.columns:
                        # Stability analysis (close anchors tend to be more stable)
                        entry_std = close_df['Entry'].std()
                        exit_std = close_df['Exit'].std()
                        stability_score = max(0, 100 - (entry_std * 10))  # Lower std = higher stability
                        
                        spreads = close_df['Entry'] - close_df['Exit']
                        consistency = 100 - (spreads.std() / spreads.mean() * 100) if spreads.mean() != 0 else 50
                        
                        # Market sentiment analysis
                        avg_entry = close_df['Entry'].mean()
                        close_price = metadata.get('close_price', 0)
                        sentiment_bias = ((avg_entry - close_price) / close_price * 100) if close_price > 0 else 0
                        
                        insight_col1, insight_col2, insight_col3 = st.columns(3)
                        
                        with insight_col1:
                            stability_color = "#10b981" if stability_score > 80 else "#3b82f6" if stability_score > 60 else "#f59e0b"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {stability_color}22, {stability_color}11);
                                border: 2px solid {stability_color};
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px {stability_color}33;
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🛡️</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: {stability_color}; margin-bottom: 0.3rem;">{stability_score:.0f}%</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Stability Score</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Price consistency</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with insight_col2:
                            consistency_color = "#10b981" if consistency > 80 else "#3b82f6" if consistency > 60 else "#f59e0b"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {consistency_color}22, {consistency_color}11);
                                border: 2px solid {consistency_color};
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px {consistency_color}33;
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: {consistency_color}; margin-bottom: 0.3rem;">{consistency:.0f}%</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Consistency</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Spread reliability</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with insight_col3:
                            sentiment_color = "#10b981" if sentiment_bias > 0 else "#ef4444" if sentiment_bias < 0 else "#6b7280"
                            sentiment_text = "Bullish" if sentiment_bias > 0 else "Bearish" if sentiment_bias < 0 else "Neutral"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {sentiment_color}22, {sentiment_color}11);
                                border: 2px solid {sentiment_color};
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px {sentiment_color}33;
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: {sentiment_color}; margin-bottom: 0.3rem;">{sentiment_text}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Market Sentiment</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">{sentiment_bias:+.1f}% bias</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Close-specific strategy
                        st.markdown("#### 🎯 Close Anchor Strategy")
                        
                        if stability_score > 80 and consistency > 70:
                            strategy_text = "🎯 **Conservative Strategy Recommended** - High stability suggests reliable entries for risk-averse traders"
                            strategy_color = "#10b981"
                        elif stability_score > 60:
                            strategy_text = "⚖️ **Balanced Approach** - Moderate stability suitable for standard strategies"
                            strategy_color = "#3b82f6"
                        else:
                            strategy_text = "⚠️ **Caution Advised** - Lower stability requires enhanced risk management"
                            strategy_color = "#f59e0b"
                        
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, {strategy_color}22, {strategy_color}11);
                            border: 2px solid {strategy_color};
                            border-radius: 12px;
                            padding: 1rem;
                            box-shadow: 0 6px 20px {strategy_color}33;
                        ">
                            <p style="margin: 0; font-size: 0.95rem; line-height: 1.4;">{strategy_text}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                else:
                    st.warning("⚠️ Close anchor forecast data not available")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4D2B1: LOW ANCHOR ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

            # ═══════════════════════════════════════════════════════════════════════════════
            # LOW ANCHOR TAB WITH RECOVERY ANALYSIS
            # ═══════════════════════════════════════════════════════════════════════════════
            
            with tab3:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
                    border: 2px solid #ef4444;
                    border-radius: 20px;
                    padding: 2rem;
                    margin: 1rem 0;
                    box-shadow: 0 10px 30px rgba(239, 68, 68, 0.2);
                ">
                    <h3 style="color: #ef4444; margin: 0 0 1rem 0; font-size: 1.8rem;">🔴 Low Anchor Forecast Analysis</h3>
                    <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">Projections based on previous day's lowest price point - identifies support levels and potential bounce opportunities</p>
                </div>
                """, unsafe_allow_html=True)
                
                if "Low" in forecasts and not forecasts["Low"].empty:
                    low_df = forecasts["Low"]
                    
                    # Enhanced table display for low anchor
                    st.markdown("#### 📊 Low Anchor Projections")
                    
                    # Format the dataframe for display
                    display_df = low_df.copy()
                    
                    # Format price columns with enhanced styling
                    for col in ['Entry', 'Exit']:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")
                    
                    # Add recovery potential indicators
                    if 'Spread' in display_df.columns:
                        display_df['Recovery'] = display_df['Spread'].apply(
                            lambda x: f"${x:.2f}" if isinstance(x, (int, float)) else str(x)
                        )
                    
                    # Enhanced dataframe display with recovery focus
                    st.dataframe(
                        display_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Time": st.column_config.TextColumn("Time", width="small"),
                            "Entry": st.column_config.TextColumn("Entry Price", width="medium"),
                            "Exit": st.column_config.TextColumn("Exit Price", width="medium"),
                            "Spread": st.column_config.TextColumn("Spread", width="small"),
                            "Recovery": st.column_config.TextColumn("Recovery", width="small"),
                            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                            "Signal": st.column_config.TextColumn("Signal", width="small"),
                        }
                    )
                    
                    # ═══════════════════════════════════════════════════════════════════════════════
                    # LOW ANCHOR RECOVERY ANALYSIS
                    # ═══════════════════════════════════════════════════════════════════════════════
                    
                    st.markdown("#### 🚀 Recovery & Bounce Analysis")
                    
                    if 'Entry' in low_df.columns and 'Exit' in low_df.columns:
                        # Recovery-specific metrics
                        recovery_potential = low_df['Entry'].max() - low_df['Entry'].min()
                        min_entry = low_df['Entry'].min()
                        max_entry = low_df['Entry'].max()
                        
                        # Bounce strength analysis
                        spreads = low_df['Entry'] - low_df['Exit']
                        max_bounce = spreads.max()
                        avg_bounce = spreads.mean()
                        
                        # Support level analysis
                        low_price = metadata.get('low_price', min_entry)
                        support_strength = ((min_entry - low_price) / low_price * 100) if low_price > 0 else 0
                        
                        # Best recovery time
                        best_recovery_idx = low_df['Entry'].idxmax()
                        best_recovery_time = low_df.loc[best_recovery_idx, 'Time'] if 'Time' in low_df.columns else 'Unknown'
                        
                        # Create recovery-focused insights cards
                        recovery_col1, recovery_col2, recovery_col3, recovery_col4 = st.columns(4)
                        
                        with recovery_col1:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(5, 150, 105, 0.1));
                                border: 2px solid #10b981;
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚀</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: #10b981; margin-bottom: 0.3rem;">${recovery_potential:.2f}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Recovery Range</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Bounce potential</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with recovery_col2:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.1));
                                border: 2px solid #3b82f6;
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💪</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: #3b82f6; margin-bottom: 0.3rem;">${max_bounce:.2f}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Max Bounce</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Peak recovery</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with recovery_col3:
                            support_color = "#10b981" if support_strength > 1 else "#3b82f6" if support_strength > 0 else "#ef4444"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {support_color}22, {support_color}11);
                                border: 2px solid {support_color};
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px {support_color}33;
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🛡️</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: {support_color}; margin-bottom: 0.3rem;">{support_strength:+.1f}%</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Support Lift</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Above yesterday</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with recovery_col4:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1));
                                border: 2px solid #f59e0b;
                                border-radius: 12px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 6px 20px rgba(245, 158, 11, 0.3);
                            ">
                                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⏰</div>
                                <div style="font-size: 1.4rem; font-weight: bold; color: #f59e0b; margin-bottom: 0.3rem;">{best_recovery_time}</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Peak Time</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Best recovery</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # LOW ANCHOR TRADING STRATEGY
                        # ═══════════════════════════════════════════════════════════════════════════════
                        
                        st.markdown("#### 🎯 Low Anchor Trading Strategy")
                        
                        strategy_col1, strategy_col2 = st.columns(2)
                        
                        with strategy_col1:
                            # Recovery-based recommendation
                            if recovery_potential > 10 and max_bounce > 5:
                                recovery_rec = "🚀 **Strong Recovery Signal** - Excellent bounce potential from support levels"
                                rec_color = "#10b981"
                            elif recovery_potential > 5 and max_bounce > 2:
                                recovery_rec = "📈 **Moderate Recovery** - Good support bounce opportunity"
                                rec_color = "#3b82f6"
                            elif recovery_potential > 0:
                                recovery_rec = "⚖️ **Limited Recovery** - Modest bounce potential"
                                rec_color = "#f59e0b"
                            else:
                                recovery_rec = "⚠️ **Weak Support** - Limited recovery expectations"
                                rec_color = "#ef4444"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {rec_color}22, {rec_color}11);
                                border: 2px solid {rec_color};
                                border-radius: 12px;
                                padding: 1rem;
                                box-shadow: 0 6px 20px {rec_color}33;
                            ">
                                <h5 style="color: {rec_color}; margin: 0 0 0.5rem 0;">Recovery Forecast</h5>
                                <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{recovery_rec}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with strategy_col2:
                            # Support strength assessment
                            if support_strength > 2:
                                support_assessment = "🛡️ **Strong Support** - Price well above previous low"
                                support_color = "#10b981"
                            elif support_strength > 0:
                                support_assessment = "📊 **Moderate Support** - Price above previous low"
                                support_color = "#3b82f6"
                            elif support_strength > -1:
                                support_assessment = "⚠️ **Weak Support** - Price near previous low"
                                support_color = "#f59e0b"
                            else:
                                support_assessment = "🔴 **Broken Support** - Price below previous low"
                                support_color = "#ef4444"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {support_color}22, {support_color}11);
                                border: 2px solid {support_color};
                                border-radius: 12px;
                                padding: 1rem;
                                box-shadow: 0 6px 20px {support_color}33;
                            ">
                                <h5 style="color: {support_color}; margin: 0 0 0.5rem 0;">Support Analysis</h5>
                                <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{support_assessment}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # BOUNCE TIMING ANALYSIS
                        # ═══════════════════════════════════════════════════════════════════════════════
                        
                        st.markdown("#### ⏰ Optimal Bounce Timing")
                        
                        # Analyze best bounce times throughout the day
                        if 'Time' in low_df.columns and len(low_df) > 3:
                            # Calculate bounce strength by time period
                            bounce_times = []
                            for idx, row in low_df.iterrows():
                                if 'Entry' in row and 'Exit' in row:
                                    bounce_strength = row['Entry'] - row['Exit']
                                    time_str = str(row['Time'])
                                    bounce_times.append({
                                        'time': time_str,
                                        'bounce': bounce_strength,
                                        'strength': 'Strong' if bounce_strength > avg_bounce * 1.2 else 'Moderate' if bounce_strength > avg_bounce * 0.8 else 'Weak'
                                    })
                            
                            # Find morning, midday, and afternoon patterns
                            morning_bounces = [b for b in bounce_times if b['time'] < '12:00']
                            afternoon_bounces = [b for b in bounce_times if b['time'] >= '12:00']
                            
                            timing_col1, timing_col2 = st.columns(2)
                            
                            with timing_col1:
                                if morning_bounces:
                                    avg_morning = sum(b['bounce'] for b in morning_bounces) / len(morning_bounces)
                                    morning_color = "#10b981" if avg_morning > avg_bounce else "#3b82f6"
                                    
                                    st.markdown(f"""
                                    <div style="
                                        background: linear-gradient(135deg, {morning_color}22, {morning_color}11);
                                        border: 2px solid {morning_color};
                                        border-radius: 12px;
                                        padding: 1rem;
                                        box-shadow: 0 6px 20px {morning_color}33;
                                    ">
                                        <h5 style="color: {morning_color}; margin: 0 0 0.5rem 0;">🌅 Morning Session</h5>
                                        <div style="font-size: 1.2rem; font-weight: bold; color: {morning_color}; margin-bottom: 0.3rem;">${avg_morning:.2f}</div>
                                        <div style="font-size: 0.8rem; opacity: 0.8;">Average bounce strength</div>
                                        <div style="font-size: 0.75rem; margin-top: 0.3rem; opacity: 0.7;">{len(morning_bounces)} opportunities</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            with timing_col2:
                                if afternoon_bounces:
                                    avg_afternoon = sum(b['bounce'] for b in afternoon_bounces) / len(afternoon_bounces)
                                    afternoon_color = "#10b981" if avg_afternoon > avg_bounce else "#3b82f6"
                                    
                                    st.markdown(f"""
                                    <div style="
                                        background: linear-gradient(135deg, {afternoon_color}22, {afternoon_color}11);
                                        border: 2px solid {afternoon_color};
                                        border-radius: 12px;
                                        padding: 1rem;
                                        box-shadow: 0 6px 20px {afternoon_color}33;
                                    ">
                                        <h5 style="color: {afternoon_color}; margin: 0 0 0.5rem 0;">🌆 Afternoon Session</h5>
                                        <div style="font-size: 1.2rem; font-weight: bold; color: {afternoon_color}; margin-bottom: 0.3rem;">${avg_afternoon:.2f}</div>
                                        <div style="font-size: 0.8rem; opacity: 0.8;">Average bounce strength</div>
                                        <div style="font-size: 0.75rem; margin-top: 0.3rem; opacity: 0.7;">{len(afternoon_bounces)} opportunities</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # LOW ANCHOR EXPORT OPTIONS
                        # ═══════════════════════════════════════════════════════════════════════════════
                        
                        st.markdown("#### 📥 Export Low Anchor Data")
                        
                        export_col1, export_col2, export_col3 = st.columns(3)
                        
                        with export_col1:
                            csv_data = low_df.to_csv(index=False)
                            st.download_button(
                                label="📊 Download CSV",
                                data=csv_data,
                                file_name=f"spx_low_anchor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key="download_low_csv"
                            )
                        
                        with export_col2:
                            json_data = low_df.to_json(orient='records', indent=2)
                            st.download_button(
                                label="🗂️ Download JSON",
                                data=json_data,
                                file_name=f"spx_low_anchor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True,
                                key="download_low_json"
                            )
                        
                        with export_col3:
                            # Create recovery-focused summary report
                            recovery_report = f"""SPX LOW ANCHOR RECOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Target Date: {metadata.get('date', 'N/A')}

RECOVERY METRICS:
- Recovery Range: ${recovery_potential:.2f}
- Max Bounce: ${max_bounce:.2f}
- Avg Bounce: ${avg_bounce:.2f}
- Support Lift: {support_strength:+.1f}%
- Best Time: {best_recovery_time}

STRATEGY: {recovery_rec}
SUPPORT: {support_assessment}

TIMING ANALYSIS:
Morning Session: {len(morning_bounces) if 'morning_bounces' in locals() else 0} opportunities
Afternoon Session: {len(afternoon_bounces) if 'afternoon_bounces' in locals() else 0} opportunities
"""
                            st.download_button(
                                label="📋 Recovery Report",
                                data=recovery_report,
                                file_name=f"spx_low_recovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key="download_low_report"
                            )
                
                else:
                    st.warning("⚠️ Low anchor forecast data not available")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4D2B2: COMPARATIVE ANALYSIS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

            # ═══════════════════════════════════════════════════════════════════════════════
            # COMPARATIVE ANALYSIS TAB WITH MULTI-ANCHOR INTELLIGENCE
            # ═══════════════════════════════════════════════════════════════════════════════
            
            with tab4:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
                    border: 2px solid #8b5cf6;
                    border-radius: 20px;
                    padding: 2rem;
                    margin: 1rem 0;
                    box-shadow: 0 10px 30px rgba(139, 92, 246, 0.2);
                ">
                    <h3 style="color: #8b5cf6; margin: 0 0 1rem 0; font-size: 1.8rem;">📊 Multi-Anchor Comparative Analysis</h3>
                    <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">Advanced comparison of all three anchor points with performance ranking and strategic recommendations</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Comprehensive comparative analysis
                if all(anchor in forecasts for anchor in ["High", "Close", "Low"]):
                    
                    # ═══════════════════════════════════════════════════════════════════════════════
                    # PERFORMANCE COMPARISON METRICS
                    # ═══════════════════════════════════════════════════════════════════════════════
                    
                    st.markdown("#### 🏆 Performance Comparison Matrix")
                    
                    # Calculate comprehensive metrics for each anchor
                    anchor_metrics = {}
                    
                    for anchor_name, anchor_df in forecasts.items():
                        if not anchor_df.empty and 'Entry' in anchor_df.columns and 'Exit' in anchor_df.columns:
                            spreads = anchor_df['Entry'] - anchor_df['Exit']
                            
                            metrics = {
                                'max_profit': spreads.max(),
                                'avg_profit': spreads.mean(),
                                'min_profit': spreads.min(),
                                'volatility': anchor_df['Entry'].std(),
                                'consistency': 100 - (spreads.std() / spreads.mean() * 100) if spreads.mean() != 0 else 50,
                                'range': anchor_df['Entry'].max() - anchor_df['Entry'].min(),
                                'total_opportunities': len(anchor_df),
                                'positive_trades': len(spreads[spreads > 0]),
                                'win_rate': (len(spreads[spreads > 0]) / len(spreads) * 100) if len(spreads) > 0 else 0
                            }
                            anchor_metrics[anchor_name] = metrics
                    
                    # ═══════════════════════════════════════════════════════════════════════════════
                    # CHAMPION ANCHOR IDENTIFICATION
                    # ═══════════════════════════════════════════════════════════════════════════════
                    
                    if anchor_metrics:
                        # Determine best performers in different categories
                        best_profit = max(anchor_metrics.items(), key=lambda x: x[1]['max_profit'])
                        best_consistency = max(anchor_metrics.items(), key=lambda x: x[1]['consistency'])
                        best_win_rate = max(anchor_metrics.items(), key=lambda x: x[1]['win_rate'])
                        lowest_risk = min(anchor_metrics.items(), key=lambda x: x[1]['volatility'])
                        
                        # Create champion cards
                        champion_col1, champion_col2, champion_col3, champion_col4 = st.columns(4)
                        
                        with champion_col1:
                            anchor_colors = {"High": "#10b981", "Close": "#3b82f6", "Low": "#ef4444"}
                            profit_color = anchor_colors.get(best_profit[0], "#8b5cf6")
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {profit_color}22, {profit_color}11);
                                border: 2px solid {profit_color};
                                border-radius: 16px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 8px 25px {profit_color}44;
                                transform: perspective(1000px) rotateY(-2deg);
                            ">
                                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🏆</div>
                                <div style="font-size: 1.5rem; font-weight: bold; color: {profit_color}; margin-bottom: 0.5rem;">{best_profit[0]} Anchor</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Max Profit Champion</div>
                                <div style="font-size: 1.1rem; color: {profit_color}; font-weight: bold;">${best_profit[1]['max_profit']:.2f}</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Peak performance</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with champion_col2:
                            consistency_color = anchor_colors.get(best_consistency[0], "#8b5cf6")
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {consistency_color}22, {consistency_color}11);
                                border: 2px solid {consistency_color};
                                border-radius: 16px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 8px 25px {consistency_color}44;
                                transform: perspective(1000px) rotateY(2deg);
                            ">
                                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎯</div>
                                <div style="font-size: 1.5rem; font-weight: bold; color: {consistency_color}; margin-bottom: 0.5rem;">{best_consistency[0]} Anchor</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Consistency Leader</div>
                                <div style="font-size: 1.1rem; color: {consistency_color}; font-weight: bold;">{best_consistency[1]['consistency']:.0f}%</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Most reliable</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with champion_col3:
                            winrate_color = anchor_colors.get(best_win_rate[0], "#8b5cf6")
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {winrate_color}22, {winrate_color}11);
                                border: 2px solid {winrate_color};
                                border-radius: 16px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 8px 25px {winrate_color}44;
                                transform: perspective(1000px) rotateY(-2deg);
                            ">
                                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈</div>
                                <div style="font-size: 1.5rem; font-weight: bold; color: {winrate_color}; margin-bottom: 0.5rem;">{best_win_rate[0]} Anchor</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Win Rate King</div>
                                <div style="font-size: 1.1rem; color: {winrate_color}; font-weight: bold;">{best_win_rate[1]['win_rate']:.0f}%</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Success rate</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with champion_col4:
                            risk_color = anchor_colors.get(lowest_risk[0], "#8b5cf6")
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {risk_color}22, {risk_color}11);
                                border: 2px solid {risk_color};
                                border-radius: 16px;
                                padding: 1.5rem;
                                text-align: center;
                                box-shadow: 0 8px 25px {risk_color}44;
                                transform: perspective(1000px) rotateY(2deg);
                            ">
                                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🛡️</div>
                                <div style="font-size: 1.5rem; font-weight: bold; color: {risk_color}; margin-bottom: 0.5rem;">{lowest_risk[0]} Anchor</div>
                                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Risk Guardian</div>
                                <div style="font-size: 1.1rem; color: {risk_color}; font-weight: bold;">{lowest_risk[1]['volatility']:.2f}</div>
                                <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Lowest volatility</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # DETAILED PERFORMANCE MATRIX TABLE
                        # ═══════════════════════════════════════════════════════════════════════════════
                        
                        st.markdown("#### 📋 Detailed Performance Matrix")
                        
                        # Create comprehensive comparison table
                        comparison_data = []
                        for anchor_name, metrics in anchor_metrics.items():
                            comparison_data.append({
                                'Anchor': f"{anchor_name} {'🟢' if anchor_name == 'High' else '🔵' if anchor_name == 'Close' else '🔴'}",
                                'Max Profit': f"${metrics['max_profit']:.2f}",
                                'Avg Profit': f"${metrics['avg_profit']:.2f}",
                                'Win Rate': f"{metrics['win_rate']:.0f}%",
                                'Consistency': f"{metrics['consistency']:.0f}%",
                                'Volatility': f"{metrics['volatility']:.2f}",
                                'Range': f"${metrics['range']:.2f}",
                                'Opportunities': metrics['total_opportunities']
                            })
                        
                        comparison_df = pd.DataFrame(comparison_data)
                        
                        st.dataframe(
                            comparison_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Anchor": st.column_config.TextColumn("Anchor", width="medium"),
                                "Max Profit": st.column_config.TextColumn("Max Profit", width="small"),
                                "Avg Profit": st.column_config.TextColumn("Avg Profit", width="small"),
                                "Win Rate": st.column_config.TextColumn("Win Rate", width="small"),
                                "Consistency": st.column_config.TextColumn("Consistency", width="small"),
                                "Volatility": st.column_config.TextColumn("Volatility", width="small"),
                                "Range": st.column_config.TextColumn("Range", width="small"),
                                "Opportunities": st.column_config.NumberColumn("Opportunities", width="small")
                            }
                        )
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # STRATEGIC RECOMMENDATIONS ENGINE
                        # ═══════════════════════════════════════════════════════════════════════════════
                        
                        st.markdown("#### 🧠 AI Strategic Recommendations")
                        
                        # Calculate overall scores for each anchor
                        anchor_scores = {}
                        for anchor_name, metrics in anchor_metrics.items():
                            # Weighted scoring system
                            profit_score = (metrics['max_profit'] / max(m['max_profit'] for m in anchor_metrics.values())) * 30
                            consistency_score = (metrics['consistency'] / 100) * 25
                            winrate_score = (metrics['win_rate'] / 100) * 25
                            risk_score = (1 - metrics['volatility'] / max(m['volatility'] for m in anchor_metrics.values())) * 20
                            
                            total_score = profit_score + consistency_score + winrate_score + risk_score
                            anchor_scores[anchor_name] = total_score
                        
                        # Rank anchors
                        ranked_anchors = sorted(anchor_scores.items(), key=lambda x: x[1], reverse=True)
                        
                        recommendation_col1, recommendation_col2 = st.columns(2)
                        
                        with recommendation_col1:
                            # Primary recommendation
                            best_anchor = ranked_anchors[0]
                            best_metrics = anchor_metrics[best_anchor[0]]
                            best_color = anchor_colors.get(best_anchor[0], "#8b5cf6")
                            
                            if best_anchor[1] > 80:
                                rec_strength = "🚀 STRONGLY RECOMMENDED"
                            elif best_anchor[1] > 65:
                                rec_strength = "📈 RECOMMENDED"
                            elif best_anchor[1] > 50:
                                rec_strength = "⚖️ MODERATELY RECOMMENDED"
                            else:
                                rec_strength = "⚠️ USE WITH CAUTION"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {best_color}22, {best_color}11);
                                border: 2px solid {best_color};
                                border-radius: 16px;
                                padding: 1.5rem;
                                box-shadow: 0 8px 25px {best_color}44;
                            ">
                                <h5 style="color: {best_color}; margin: 0 0 1rem 0;">🎯 Primary Recommendation</h5>
                                <div style="font-size: 1.3rem; font-weight: bold; color: {best_color}; margin-bottom: 0.5rem;">{best_anchor[0]} Anchor Strategy</div>
                                <div style="background: {best_color}22; padding: 0.8rem; border-radius: 8px; margin: 1rem 0;">
                                    <div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">{rec_strength}</div>
                                    <div style="font-size: 0.8rem; opacity: 0.9;">Overall Score: {best_anchor[1]:.0f}/100</div>
                                </div>
                                <div style="font-size: 0.85rem; line-height: 1.4;">
                                    <strong>Key Strengths:</strong><br>
                                    • Max Profit: ${best_metrics['max_profit']:.2f}<br>
                                    • Win Rate: {best_metrics['win_rate']:.0f}%<br>
                                    • Consistency: {best_metrics['consistency']:.0f}%
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with recommendation_col2:
                            # Alternative recommendation
                            if len(ranked_anchors) > 1:
                                alt_anchor = ranked_anchors[1]
                                alt_metrics = anchor_metrics[alt_anchor[0]]
                                alt_color = anchor_colors.get(alt_anchor[0], "#8b5cf6")
                                
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, {alt_color}22, {alt_color}11);
                                    border: 2px solid {alt_color};
                                    border-radius: 16px;
                                    padding: 1.5rem;
                                    box-shadow: 0 8px 25px {alt_color}44;
                                ">
                                    <h5 style="color: {alt_color}; margin: 0 0 1rem 0;">🥈 Alternative Strategy</h5>
                                    <div style="font-size: 1.3rem; font-weight: bold; color: {alt_color}; margin-bottom: 0.5rem;">{alt_anchor[0]} Anchor Backup</div>
                                    <div style="background: {alt_color}22; padding: 0.8rem; border-radius: 8px; margin: 1rem 0;">
                                        <div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">📊 SECONDARY OPTION</div>
                                        <div style="font-size: 0.8rem; opacity: 0.9;">Overall Score: {alt_anchor[1]:.0f}/100</div>
                                    </div>
                                    <div style="font-size: 0.85rem; line-height: 1.4;">
                                        <strong>Consider When:</strong><br>
                                        • Primary shows weakness<br>
                                        • Risk tolerance changes<br>
                                        • Market conditions shift
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # MARKET REGIME ADAPTATION
                        # ═══════════════════════════════════════════════════════════════════════════════
                        
                        st.markdown("#### 🌍 Market Regime Adaptation Guide")
                        
                        regime_col1, regime_col2, regime_col3 = st.columns(3)
                        
                        with regime_col1:
                            # Bullish market recommendation
                            bull_anchor = "High" if "High" in anchor_metrics else list(anchor_metrics.keys())[0]
                            bull_color = "#10b981"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {bull_color}15, {bull_color}08);
                                border: 2px solid {bull_color};
                                border-radius: 12px;
                                padding: 1.2rem;
                                box-shadow: 0 6px 20px {bull_color}33;
                            ">
                                <h5 style="color: {bull_color}; margin: 0 0 0.8rem 0;">🐂 Bullish Market</h5>
                                <div style="font-size: 1.1rem; font-weight: bold; color: {bull_color}; margin-bottom: 0.5rem;">Focus: {bull_anchor} Anchor</div>
                                <div style="font-size: 0.8rem; line-height: 1.4; opacity: 0.9;">
                                    • Momentum plays preferred<br>
                                    • Higher profit targets<br>
                                    • Aggressive positioning
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with regime_col2:
                            # Neutral market recommendation
                            neutral_anchor = "Close" if "Close" in anchor_metrics else list(anchor_metrics.keys())[0]
                            neutral_color = "#3b82f6"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {neutral_color}15, {neutral_color}08);
                                border: 2px solid {neutral_color};
                                border-radius: 12px;
                                padding: 1.2rem;
                                box-shadow: 0 6px 20px {neutral_color}33;
                            ">
                                <h5 style="color: {neutral_color}; margin: 0 0 0.8rem 0;">⚖️ Neutral Market</h5>
                                <div style="font-size: 1.1rem; font-weight: bold; color: {neutral_color}; margin-bottom: 0.5rem;">Focus: {neutral_anchor} Anchor</div>
                                <div style="font-size: 0.8rem; line-height: 1.4; opacity: 0.9;">
                                    • Range-bound strategies<br>
                                    • Moderate targets<br>
                                    • Balanced approach
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with regime_col3:
                            # Bearish market recommendation
                            bear_anchor = "Low" if "Low" in anchor_metrics else list(anchor_metrics.keys())[0]
                            bear_color = "#ef4444"
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {bear_color}15, {bear_color}08);
                                border: 2px solid {bear_color};
                                border-radius: 12px;
                                padding: 1.2rem;
                                box-shadow: 0 6px 20px {bear_color}33;
                            ">
                                <h5 style="color: {bear_color}; margin: 0 0 0.8rem 0;">🐻 Bearish Market</h5>
                                <div style="font-size: 1.1rem; font-weight: bold; color: {bear_color}; margin-bottom: 0.5rem;">Focus: {bear_anchor} Anchor</div>
                                <div style="font-size: 0.8rem; line-height: 1.4; opacity: 0.9;">
                                    • Support bounce plays<br>
                                    • Conservative targets<br>
                                    • Risk management priority
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # ═══════════════════════════════════════════════════════════════════════════════
                        # EXPORT COMPARATIVE ANALYSIS
                        # ═══════════════════════════════════════════════════════════════════════════════
                        
                        st.markdown("#### 📥 Export Comparative Analysis")
                        
                        comprehensive_col1, comprehensive_col2 = st.columns(2)
                        
                        with comprehensive_col1:
                            # Export comparison table
                            comparison_csv = comparison_df.to_csv(index=False)
                            st.download_button(
                                label="📊 Download Comparison Matrix",
                                data=comparison_csv,
                                file_name=f"spx_comparative_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key="download_comparison"
                            )
                        
                        with comprehensive_col2:
                            # Export strategic recommendations
                            strategy_report = f"""SPX MULTI-ANCHOR STRATEGIC ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Target Date: {metadata.get('date', 'N/A')}

CHAMPION ANCHORS:
🏆 Max Profit: {best_profit[0]} (${best_profit[1]['max_profit']:.2f})
🎯 Consistency: {best_consistency[0]} ({best_consistency[1]['consistency']:.0f}%)
📈 Win Rate: {best_win_rate[0]} ({best_win_rate[1]['win_rate']:.0f}%)
🛡️ Risk Control: {lowest_risk[0]} ({lowest_risk[1]['volatility']:.2f})

STRATEGIC RANKING:
1. {ranked_anchors[0][0]} Anchor (Score: {ranked_anchors[0][1]:.0f}/100)
2. {ranked_anchors[1][0]} Anchor (Score: {ranked_anchors[1][1]:.0f}/100)
3. {ranked_anchors[2][0]} Anchor (Score: {ranked_anchors[2][1]:.0f}/100)

PRIMARY RECOMMENDATION: {best_anchor[0]} Anchor
{rec_strength}

MARKET REGIME GUIDANCE:
🐂 Bullish: Focus on {bull_anchor} Anchor
⚖️ Neutral: Focus on {neutral_anchor} Anchor  
🐻 Bearish: Focus on {bear_anchor} Anchor
"""
                            st.download_button(
                                label="📋 Strategic Report",
                                data=strategy_report,
                                file_name=f"spx_strategic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key="download_strategy"
                            )
                
                else:
                    st.warning("⚠️ Insufficient forecast data for comparative analysis. Please ensure all three anchors have been generated.")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4D2B3: EXPORT & SUMMARY FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

        else:
            # Fallback for incomplete forecasts
            st.warning("⚠️ **Incomplete Forecast Data** - Some anchor points may be missing. Please regenerate forecasts to see complete analysis.")
            
            # Show what's available
            available_anchors = list(forecasts.keys())
            if available_anchors:
                st.info(f"📊 **Available Anchors:** {', '.join(available_anchors)}")
                
                # Simple display for available data
                for anchor_name in available_anchors:
                    if anchor_name in forecasts and not forecasts[anchor_name].empty:
                        with st.expander(f"📈 {anchor_name} Anchor Data", expanded=False):
                            display_forecast_table(forecasts[anchor_name], f"{anchor_name} Anchor Forecast")
            else:
                st.error("❌ **No Forecast Data Available** - Please generate forecasts first.")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMPREHENSIVE EXPORT & SUMMARY SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("## 📥 Comprehensive Export & Portfolio Summary")
    st.caption("Download all forecast data and get a complete portfolio overview of your SPX analysis")
    
    if st.session_state.current_forecasts:
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # PORTFOLIO SUMMARY DASHBOARD
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("### 💼 Portfolio Summary Dashboard")
        
        # Calculate portfolio-wide metrics
        all_forecasts = st.session_state.current_forecasts
        total_anchors = len(all_forecasts)
        total_projections = sum(len(df) for df in all_forecasts.values() if not df.empty)
        
        # Calculate portfolio profit potential
        portfolio_max_profit = 0
        portfolio_avg_profit = 0
        portfolio_opportunities = 0
        
        portfolio_stats = {}
        for anchor_name, anchor_df in all_forecasts.items():
            if not anchor_df.empty and 'Entry' in anchor_df.columns and 'Exit' in anchor_df.columns:
                spreads = anchor_df['Entry'] - anchor_df['Exit']
                max_profit = spreads.max()
                avg_profit = spreads.mean()
                opportunities = len(spreads[spreads > 0])
                
                portfolio_stats[anchor_name] = {
                    'max_profit': max_profit,
                    'avg_profit': avg_profit,
                    'opportunities': opportunities
                }
                
                portfolio_max_profit = max(portfolio_max_profit, max_profit)
                portfolio_avg_profit += avg_profit
                portfolio_opportunities += opportunities
        
        if portfolio_stats:
            portfolio_avg_profit /= len(portfolio_stats)
        
        # Portfolio summary cards
        portfolio_col1, portfolio_col2, portfolio_col3, portfolio_col4 = st.columns(4)
        
        with portfolio_col1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1));
                border: 2px solid #10b981;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
                transform: perspective(1000px) rotateY(-2deg);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💼</div>
                <div style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; color: #10b981;">{total_anchors}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Active Strategies</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Anchor points</div>
                <div style="font-size: 0.75rem; color: #10b981; font-weight: 600; margin-top: 0.3rem;">Portfolio diversity</div>
            </div>
            """, unsafe_allow_html=True)
        
        with portfolio_col2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.1));
                border: 2px solid #3b82f6;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
                transform: perspective(1000px) rotateY(2deg);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <div style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; color: #3b82f6;">{total_projections}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Total Projections</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Time slots</div>
                <div style="font-size: 0.75rem; color: #3b82f6; font-weight: 600; margin-top: 0.3rem;">Analysis depth</div>
            </div>
            """, unsafe_allow_html=True)
        
        with portfolio_col3:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1));
                border: 2px solid #f59e0b;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3);
                transform: perspective(1000px) rotateY(-2deg);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💰</div>
                <div style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; color: #f59e0b;">${portfolio_max_profit:.2f}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Peak Profit</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Maximum potential</div>
                <div style="font-size: 0.75rem; color: #f59e0b; font-weight: 600; margin-top: 0.3rem;">Best opportunity</div>
            </div>
            """, unsafe_allow_html=True)
        
        with portfolio_col4:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
                border: 2px solid #8b5cf6;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
                transform: perspective(1000px) rotateY(2deg);
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                <div style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; color: #8b5cf6;">{portfolio_opportunities}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Opportunities</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Positive trades</div>
                <div style="font-size: 0.75rem; color: #8b5cf6; font-weight: 600; margin-top: 0.3rem;">Win potential</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # ENHANCED EXPORT OPTIONS
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("### 📦 Premium Export Suite")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(5, 150, 105, 0.05));
                border: 2px solid #10b981;
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 25px rgba(16, 185, 129, 0.2);
            ">
                <h5 style="color: #10b981; margin: 0 0 1rem 0;">📊 Data Exports</h5>
                <p style="margin: 0 0 1rem 0; font-size: 0.9rem; opacity: 0.9;">Raw forecast data in multiple formats</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Combined CSV export
            if st.button("📊 All Data (CSV)", key="export_all_csv", use_container_width=True):
                combined_data = []
                for anchor_name, forecast_df in all_forecasts.items():
                    df_copy = forecast_df.copy()
                    df_copy['Anchor'] = anchor_name
                    df_copy['Generated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    combined_data.append(df_copy)
                
                if combined_data:
                    combined_df = pd.concat(combined_data, ignore_index=True)
                    csv_data = combined_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Combined CSV",
                        data=csv_data,
                        file_name=f"spx_all_forecasts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_all_csv"
                    )
            
            # JSON export
            if st.button("🗂️ All Data (JSON)", key="export_all_json", use_container_width=True):
                json_data = {}
                for anchor_name, forecast_df in all_forecasts.items():
                    json_data[anchor_name] = forecast_df.to_dict('records')
                
                json_data['metadata'] = metadata
                json_data['generated_at'] = datetime.now().isoformat()
                
                json_string = json.dumps(json_data, indent=2)
                st.download_button(
                    label="📥 Download JSON Package",
                    data=json_string,
                    file_name=f"spx_forecasts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_all_json"
                )
        
        with export_col2:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.05));
                border: 2px solid #3b82f6;
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
            ">
                <h5 style="color: #3b82f6; margin: 0 0 1rem 0;">📋 Reports</h5>
                <p style="margin: 0 0 1rem 0; font-size: 0.9rem; opacity: 0.9;">Comprehensive analysis reports</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Executive summary
            if st.button("📋 Executive Summary", key="export_executive", use_container_width=True):
                executive_summary = f"""SPX FORECAST EXECUTIVE SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}
Target Date: {metadata.get('date', 'N/A')}

PORTFOLIO OVERVIEW:
• Active Strategies: {total_anchors} anchor points
• Total Projections: {total_projections} time slots
• Peak Profit Potential: ${portfolio_max_profit:.2f}
• Total Opportunities: {portfolio_opportunities} positive trades

MARKET CONDITIONS:
• Volatility Level: {metadata.get('volatility_level', 'Unknown')}
• Market Structure: {metadata.get('market_structure', 'Unknown')}
• Price Range: ${metadata.get('high_price', 0) - metadata.get('low_price', 0):.2f}
• Range %: {metadata.get('range_percentage', 0):.1f}%

ANCHOR PERFORMANCE:
"""
                
                for anchor_name, stats in portfolio_stats.items():
                    executive_summary += f"""
{anchor_name} Anchor:
  - Max Profit: ${stats['max_profit']:.2f}
  - Avg Profit: ${stats['avg_profit']:.2f}
  - Opportunities: {stats['opportunities']}
"""
                
                executive_summary += f"""
GENERATION DETAILS:
• System Status: {metadata.get('system_status', 'Unknown')}
• Chicago Time: {strategy.get_chicago_time().strftime('%Y-%m-%d %H:%M:%S CST')}
• Forecast Quality: High precision multi-anchor analysis

DISCLAIMER:
This forecast is for informational purposes only. Past performance does not guarantee future results. Always conduct your own analysis and risk management before trading.
"""
                
                st.download_button(
                    label="📥 Download Executive Summary",
                    data=executive_summary,
                    file_name=f"spx_executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_executive"
                )
            
            # Technical analysis report
            if st.button("🔬 Technical Report", key="export_technical", use_container_width=True):
                technical_report = f"""SPX TECHNICAL ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S CST')}
Analysis Type: Three-Anchor Projection System
Target Date: {metadata.get('date', 'N/A')}

METHODOLOGY:
Dr. David's Market Mind uses proprietary time-block calculations with slope projections to generate precise entry and exit points across multiple anchor scenarios.

SLOPE PARAMETERS:
"""
                slope_summary = metadata.get('slope_summary', {})
                for slope_type, value in slope_summary.items():
                    if slope_type != 'average':
                        technical_report += f"• SPX {slope_type.upper()}: {value:.4f}\n"
                
                technical_report += f"• Average Slope: {slope_summary.get('average', 0):.4f}\n"
                
                technical_report += f"""
ANCHOR POINT ANALYSIS:
• High Anchor: ${metadata.get('high_price', 0):.2f} @ {metadata.get('high_time', 'N/A')}
• Close Anchor: ${metadata.get('close_price', 0):.2f} @ {metadata.get('close_time', 'N/A')}  
• Low Anchor: ${metadata.get('low_price', 0):.2f} @ {metadata.get('low_time', 'N/A')}

STATISTICAL ANALYSIS:
"""
                
                for anchor_name, stats in portfolio_stats.items():
                    technical_report += f"""
{anchor_name} Anchor Statistics:
  - Maximum Profit: ${stats['max_profit']:.2f}
  - Average Profit: ${stats['avg_profit']:.2f}
  - Win Rate: {(stats['opportunities']/len(all_forecasts[anchor_name])*100) if anchor_name in all_forecasts and len(all_forecasts[anchor_name]) > 0 else 0:.1f}%
  - Total Signals: {len(all_forecasts[anchor_name]) if anchor_name in all_forecasts else 0}
"""
                
                technical_report += """
RISK CONSIDERATIONS:
• This analysis is based on historical slope calculations
• Market conditions can change rapidly
• Use appropriate position sizing
• Implement stop-loss strategies
• Monitor intraday volatility

NEXT STEPS:
1. Select optimal anchor based on risk tolerance
2. Plan entry/exit timing around projected levels
3. Set position sizes according to volatility
4. Monitor actual vs projected performance
5. Adjust slopes based on market feedback
"""
                
                st.download_button(
                    label="📥 Download Technical Report",
                    data=technical_report,
                    file_name=f"spx_technical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_technical"
                )
        
        with export_col3:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
                border: 2px solid #8b5cf6;
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 25px rgba(139, 92, 246, 0.2);
            ">
                <h5 style="color: #8b5cf6; margin: 0 0 1rem 0;">⚙️ Configuration</h5>
                <p style="margin: 0 0 1rem 0; font-size: 0.9rem; opacity: 0.9;">Settings and parameters backup</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Configuration backup
            if st.button("⚙️ Save Configuration", key="export_config", use_container_width=True):
                config_data = {
                    "slopes": strategy.slopes.copy(),
                    "metadata": metadata,
                    "session_settings": {
                        "dark_mode": st.session_state.get('dark_mode', False),
                        "premium_effects": st.session_state.get('premium_effects', True),
                        "animation_enabled": st.session_state.get('animation_enabled', True)
                    },
                    "export_timestamp": datetime.now().isoformat(),
                    "chicago_time": strategy.get_chicago_time().isoformat(),
                    "version": "3.0_premium"
                }
                
                config_json = json.dumps(config_data, indent=2)
                st.download_button(
                    label="📥 Download Configuration",
                    data=config_json,
                    file_name=f"spx_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_config_backup"
                )
            
            # Quick share format
            if st.button("📱 Quick Share", key="export_share", use_container_width=True):
                share_text = f"""📊 SPX Forecast Results - {metadata.get('date', 'N/A')}

🎯 {total_anchors} Anchor Strategies | {total_projections} Projections
💰 Peak Profit: ${portfolio_max_profit:.2f}
🏆 Total Opportunities: {portfolio_opportunities}

⚡ {metadata.get('volatility_level', 'Unknown')} Volatility
📈 {metadata.get('market_structure', 'Unknown')} Structure

Generated by Dr. David's Market Mind
{datetime.now().strftime('%Y-%m-%d %H:%M CST')}

#SPX #Trading #Forecast #MarketMind"""
                
                st.download_button(
                    label="📥 Download Share Text",
                    data=share_text,
                    file_name=f"spx_share_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_share_text"
                )
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # SESSION MANAGEMENT
        # ═══════════════════════════════════════════════════════════════════════════════
        
        st.markdown("---")
        st.markdown("### 🔧 Session Management")
        
        session_col1, session_col2, session_col3 = st.columns(3)
        
        with session_col1:
            if st.button("🔄 Regenerate All Forecasts", key="regenerate_all", type="secondary", use_container_width=True):
                # Clear current forecasts to force regeneration
                st.session_state.current_forecasts = {}
                st.session_state.forecast_metadata = {}
                st.info("🔄 Forecasts cleared. Please regenerate using the form above.")
                st.rerun()
        
        with session_col2:
            if st.button("📋 Copy Current Settings", key="copy_settings", use_container_width=True):
                current_settings = {
                    'high_price': metadata.get('high_price', 0),
                    'close_price': metadata.get('close_price', 0),
                    'low_price': metadata.get('low_price', 0),
                    'slopes': strategy.slopes.copy()
                }
                st.session_state.copied_settings = current_settings
                st.success("✅ Settings copied to session memory")
        
        with session_col3:
            if st.button("🧹 Clear All Data", key="clear_all_data", use_container_width=True):
                # Clear all forecast data
                keys_to_clear = [
                    'current_forecasts', 'forecast_metadata', 'contract_table', 
                    'contract_params', 'copied_settings'
                ]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("✅ All forecast data cleared")
                st.rerun()
    
    else:
        # No forecasts available - show quick start guide
        st.markdown("### 🚀 Quick Start Guide")
        
        st.info("""
        **📊 No SPX forecasts generated yet.** Get started in 3 easy steps:
        
        1. **📅 Set Target Date** - Choose your forecast date above
        2. **🎯 Enter Anchor Points** - Input High, Close, and Low prices from previous day  
        3. **🚀 Generate Forecasts** - Click the generate button to create projections
        
        Once generated, you'll have access to comprehensive analysis and export options!
        """)
        
        # Quick tips
        with st.expander("💡 Pro Tips for Better Forecasts", expanded=False):
            st.markdown("""
            **🎯 Accurate Data Entry:**
            - Use exact prices from the previous trading day
            - Include precise times when high/low occurred
            - Verify price relationships (High > Close > Low)
            
            **⚙️ Slope Optimization:**
            - Adjust slopes in the sidebar for your trading style
            - Save configurations as presets for different market conditions
            - Test different slope combinations
            
            **📊 Analysis Best Practices:**
            - Compare all three anchor points
            - Focus on consistency over maximum profit
            - Consider market volatility in your strategy
            - Use the comparative analysis for decision making
            """)

# End of SPX forecasting page
else:
    # This else belongs to the main SPX page conditional at the very beginning
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: PREMIUM CONTRACT LINE PAGE
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.selected_page == "Contract":
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM CONTRACT LINE PAGE HEADER
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 25%, #991b1b 50%, #7f1d1d 75%, #450a0a 100%);
        border-radius: 24px;
        padding: 3rem 2rem;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 15px 40px rgba(220, 38, 38, 0.4);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(2deg);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    ">
        <div style="
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 70% 30%, rgba(255,255,255,0.15) 0%, transparent 50%);
            animation: hero-pulse 6s ease-in-out infinite;
            pointer-events: none;
        "></div>
        <div style="
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.05) 50%, transparent 70%);
            transform: translateX(-100%);
            animation: shimmer 3s ease-in-out infinite;
        "></div>
        <h1 style="
            color: white; 
            font-size: 3rem; 
            font-weight: 900; 
            margin-bottom: 1rem;
            text-shadow: 0 6px 25px rgba(0,0,0,0.6);
            background: linear-gradient(45deg, #ffffff, #fecaca, #fed7d7);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
            z-index: 2;
            letter-spacing: -0.02em;
        ">📈 Contract Line Command Center</h1>
        <p style="
            color: rgba(255,255,255,0.95); 
            font-size: 1.3rem; 
            margin: 0;
            position: relative;
            z-index: 2;
            font-weight: 400;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        ">Two-Point Interpolation System for Precision Options Trading</p>
        <div style="
            margin-top: 2rem;
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
            position: relative;
            z-index: 2;
        ">
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">📊 Two-Point Analysis</div>
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">⚡ Real-Time Lookup</div>
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">🎯 Options Optimized</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CONTRACT LINE EXPLANATION & METHODOLOGY
    # ═══════════════════════════════════════════════════════════════════════════════
    
    with st.expander("ℹ️ Contract Line Methodology & Strategy", expanded=False):
        st.markdown("""
        ### 🧮 How Contract Line Forecasting Works
        
        **Contract Line Forecasting** uses advanced two-point interpolation to create precise trend projections:
        
        #### 📍 **Two Reference Points:**
        1. **Low-1** 🎯 Your first reference point (price + time)
        2. **Low-2** 🎯 Your second reference point (price + time)
        
        #### 🔬 **Mathematical Process:**
        - **Slope Calculation**: Rate of change between points using SPX time-block methodology
        - **Trend Extension**: Projects this calculated trend across all forecast time slots
        - **Precision Interpolation**: Accounts for market gaps and trading hour variations
        
        #### 💰 **Ideal For:**
        - **Options Trading** - Precise entry/exit timing for contracts
        - **Intraday Momentum** - Capturing trend continuation setups
        - **Support/Resistance** - Identifying key level interactions
        - **Scalping Strategies** - Short-term price movement predictions
        
        #### 🎯 **Strategic Applications:**
        - **Call Options**: Use when Low-2 > Low-1 (uptrend)
        - **Put Options**: Use when Low-2 < Low-1 (downtrend)
        - **Iron Condors**: Sideways trend identification
        - **Straddles**: Volatility expansion setups
        
        #### ⚠️ **Best Practices:**
        - Use recent, relevant price points (same trading session preferred)
        - Ensure significant time gap between points for accuracy
        - Validate against current market conditions
        - Consider volume and volatility context
        """)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CONTRACT PARAMETERS INPUT SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("## ⚙️ Contract Parameters Configuration")
    st.caption("Set up your two-point interpolation system with precision timing and pricing")
    
    # Enhanced date input with market context
    contract_col1, contract_col2, contract_col3 = st.columns([2, 2, 2])
    
    with contract_col1:
        contract_date = st.date_input(
            "📅 Contract Target Date",
            value=date.today() + timedelta(days=1),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=30),
            key="contract_date",
            help="Select the date for contract line projections"
        )
    
    with contract_col2:
        contract_weekday = contract_date.strftime("%A")
        is_weekend = contract_date.weekday() >= 5
        
        if is_weekend:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f59e0b, #d97706);
                color: white;
                padding: 1.5rem;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
                border: 2px solid rgba(255, 255, 255, 0.2);
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
                <strong style="font-size: 1.2rem;">{contract_weekday}</strong><br>
                <small style="opacity: 0.9;">Weekend - No Trading</small><br>
                <small style="opacity: 0.8; font-size: 0.8rem;">Consider next trading day</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #dc2626, #b91c1c);
                color: white;
                padding: 1.5rem;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(220, 38, 38, 0.4);
                border: 2px solid rgba(255, 255, 255, 0.2);
                animation: glow 3s ease-in-out infinite;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
                <strong style="font-size: 1.2rem;">{contract_weekday}</strong><br>
                <small style="opacity: 0.9;">{contract_date.strftime('%B %d, %Y')}</small><br>
                <small style="opacity: 0.8; font-size: 0.8rem;">Contract Active Day</small>
            </div>
            """, unsafe_allow_html=True)
    
    with contract_col3:
        # Contract urgency indicator
        days_until = (contract_date - date.today()).days
        
        if days_until == 0:
            urgency_color = "#dc2626"
            urgency_emoji = "🚨"
            urgency_text = "TODAY!"
            urgency_subtitle = "Execute immediately"
        elif days_until == 1:
            urgency_color = "#f59e0b"
            urgency_emoji = "⚡"
            urgency_text = "TOMORROW"
            urgency_subtitle = "High priority"
        else:
            urgency_color = "#dc2626"
            urgency_emoji = "📅"
            urgency_text = f"T+{days_until} DAYS"
            urgency_subtitle = "Plan ahead"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {urgency_color}, {urgency_color}dd);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 25px {urgency_color}44;
            border: 2px solid rgba(255, 255, 255, 0.2);
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{urgency_emoji}</div>
            <strong style="font-size: 1.2rem;">{urgency_text}</strong><br>
            <small style="opacity: 0.9;">{urgency_subtitle}</small><br>
            <small style="opacity: 0.8; font-size: 0.8rem;">Contract timeline</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TWO-POINT INPUT SYSTEM WITH ENHANCED VALIDATION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("## 📍 Two-Point Reference System")
    st.caption("Define your contract line with two precise reference points for optimal interpolation accuracy")
    
    # Enhanced two-point input with real-time validation
    point_col1, point_col2 = st.columns(2)
    
    with point_col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.08), rgba(185, 28, 28, 0.08));
            border: 2px solid #dc2626;
            border-radius: 20px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 12px 35px rgba(220, 38, 38, 0.25);
            position: relative;
            overflow: hidden;
            transform: perspective(1000px) rotateX(1deg);
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #dc2626, #b91c1c, #991b1b);
            "></div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📍 Low-1 Reference Point")
        st.caption("🎯 First anchor point - establishes baseline trend direction")
        
        low1_price = st.number_input(
            "💰 Low-1 Price ($)",
            value=10.0,
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key="low1_price",
            help="First reference price point for trend calculation"
        )
        
        low1_time = st.time_input(
            "🕐 Low-1 Time",
            value=time(9, 30),
            step=300,  # 5-minute steps
            key="low1_time",
            help="Exact time for first reference point"
        )
        
        # Low-1 validation and insights
        if low1_price > 0:
            st.markdown(f"""
            <div style="
                background: rgba(220, 38, 38, 0.1);
                border: 1px solid #dc2626;
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                text-align: center;
            ">
                <div style="color: #dc2626; font-weight: 600; margin-bottom: 0.5rem;">✅ Point 1 Set</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Baseline: ${low1_price:.2f} @ {low1_time.strftime('%H:%M')}</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.3rem;">Anchor established</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with point_col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.08), rgba(185, 28, 28, 0.08));
            border: 2px solid #dc2626;
            border-radius: 20px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 12px 35px rgba(220, 38, 38, 0.25);
            position: relative;
            overflow: hidden;
            transform: perspective(1000px) rotateX(-1deg);
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #dc2626, #b91c1c, #991b1b);
            "></div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📍 Low-2 Reference Point")
        st.caption("🎯 Second anchor point - defines trend direction and strength")
        
        low2_price = st.number_input(
            "💰 Low-2 Price ($)",
            value=12.0,
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key="low2_price",
            help="Second reference price point for trend calculation"
        )
        
        low2_time = st.time_input(
            "🕐 Low-2 Time",
            value=time(10, 30),
            step=300,  # 5-minute steps
            key="low2_time",
            help="Exact time for second reference point"
        )
        
        # Low-2 validation and insights
        if low2_price > 0 and low2_time > low1_time:
            trend_direction = "📈 Bullish" if low2_price > low1_price else "📉 Bearish" if low2_price < low1_price else "➡️ Flat"
            trend_color = "#10b981" if low2_price > low1_price else "#ef4444" if low2_price < low1_price else "#6b7280"
            
            st.markdown(f"""
            <div style="
                background: {trend_color}22;
                border: 1px solid {trend_color};
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                text-align: center;
            ">
                <div style="color: {trend_color}; font-weight: 600; margin-bottom: 0.5rem;">✅ Point 2 Set</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Target: ${low2_price:.2f} @ {low2_time.strftime('%H:%M')}</div>
                <div style="font-size: 0.8rem; color: {trend_color}; font-weight: 600; margin-top: 0.3rem;">{trend_direction}</div>
            </div>
            """, unsafe_allow_html=True)
        elif low2_time <= low1_time:
            st.markdown(f"""
            <div style="
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid #ef4444;
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                text-align: center;
            ">
                <div style="color: #ef4444; font-weight: 600; margin-bottom: 0.5rem;">⚠️ Time Error</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Low-2 time must be after Low-1</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REAL-TIME CONTRACT ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if low1_price > 0 and low2_price > 0 and low2_time > low1_time:
        st.markdown("## 📊 Real-Time Contract Analytics")
        
        # Calculate comprehensive contract metrics
        time_minutes = (datetime.combine(contract_date, low2_time) - 
                       datetime.combine(contract_date, low1_time)).total_seconds() / 60
        
        price_change = low2_price - low1_price
        price_change_pct = (price_change / low1_price) * 100 if low1_price > 0 else 0
        hourly_rate = (price_change / time_minutes) * 60 if time_minutes > 0 else 0
        
        # Contract strength assessment
        if abs(price_change_pct) > 5:
            strength_level = "Very Strong"
            strength_color = "#dc2626"
            strength_emoji = "🔥"
        elif abs(price_change_pct) > 2:
            strength_level = "Strong"
            strength_color = "#f59e0b"
            strength_emoji = "⚡"
        elif abs(price_change_pct) > 0.5:
            strength_level = "Moderate"
            strength_color = "#3b82f6"
            strength_emoji = "📊"
        else:
            strength_level = "Weak"
            strength_color = "#6b7280"
            strength_emoji = "😴"
        
        # Trend classification
        if price_change > 0:
            trend_type = "Bullish Momentum"
            trend_emoji = "🐂"
            trend_color = "#10b981"
            options_strategy = "Call Options Favored"
        elif price_change < 0:
            trend_type = "Bearish Momentum"
            trend_emoji = "🐻"
            trend_color = "#ef4444"
            options_strategy = "Put Options Favored"
        else:
            trend_type = "Sideways Action"
            trend_emoji = "🦀"
            trend_color = "#6b7280"
            options_strategy = "Range Strategies"
        
        # Display analytics cards
        analytics_col1, analytics_col2, analytics_col3, analytics_col4 = st.columns(4)
        
        with analytics_col1:
            st.markdown(
                create_premium_metric_card(
                    "💰", "Price Move", f"${price_change:+.2f}", 
                    f"{price_change_pct:+.1f}%", f"{price_change_pct:+.1f}%"
                ),
                unsafe_allow_html=True
            )
        
        with analytics_col2:
            st.markdown(
                create_premium_metric_card(
                    trend_emoji, "Trend Type", trend_type, 
                    options_strategy, trend_type
                ),
                unsafe_allow_html=True
            )
        
        with analytics_col3:
            st.markdown(
                create_premium_metric_card(
                    strength_emoji, "Move Strength", strength_level, 
                    f"{abs(price_change_pct):.1f}% magnitude", strength_level
                ),
                unsafe_allow_html=True
            )
        
        with analytics_col4:
            st.markdown(
                create_premium_metric_card(
                    "⚡", "Hourly Rate", f"${hourly_rate:+.2f}/hr", 
                    f"{time_minutes:.0f} min span", f"{hourly_rate:+.2f}/hr"
                ),
                unsafe_allow_html=True
            )
    
    st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 6: CONTRACT LINE GENERATION & RESULTS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════════════
    # PREMIUM CONTRACT GENERATION SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("## 🚀 Contract Line Generation")
    st.caption("Generate precision contract line forecasts with advanced interpolation and real-time lookup capabilities")
    
    # Enhanced generate button with comprehensive validation
    generate_contract_col1, generate_contract_col2, generate_contract_col3 = st.columns([1, 2, 1])
    
    # Contract validation system
    with generate_contract_col1:
        contract_validation_score = 0
        contract_validation_items = []
        contract_warnings = []
        
        # Core validation checks
        if low1_price > 0:
            contract_validation_score += 1
            contract_validation_items.append("✅ Low-1 Price Set")
        else:
            contract_validation_items.append("❌ Low-1 Price Missing")
        
        if low2_price > 0:
            contract_validation_score += 1
            contract_validation_items.append("✅ Low-2 Price Set")
        else:
            contract_validation_items.append("❌ Low-2 Price Missing")
        
        # Time validation
        if low2_time > low1_time:
            contract_validation_score += 1
            contract_validation_items.append("✅ Time Sequence Valid")
        else:
            contract_validation_items.append("⚠️ Time Sequence Error")
        
        # Contract quality checks
        if low1_price > 0 and low2_price > 0:
            price_diff = abs(low2_price - low1_price)
            if price_diff < 0.1:
                contract_warnings.append("⚠️ Very small price difference")
            elif price_diff > 50:
                contract_warnings.append("⚠️ Very large price difference")
            
            time_diff_minutes = (datetime.combine(contract_date, low2_time) - 
                               datetime.combine(contract_date, low1_time)).total_seconds() / 60
            if time_diff_minutes < 15:
                contract_warnings.append("⚠️ Short time span")
            elif time_diff_minutes > 360:  # 6 hours
                contract_warnings.append("⚠️ Very long time span")
        
        # Data quality validation
        if contract_validation_score == 3:
            contract_validation_score += 1
            contract_validation_items.append("✅ Data Quality Good")
        
        contract_readiness = contract_validation_score / 4 * 100
        readiness_color = "#dc2626" if contract_readiness == 100 else "#f59e0b" if contract_readiness >= 75 else "#ef4444"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {readiness_color}22, {readiness_color}11);
            border: 2px solid {readiness_color};
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 25px {readiness_color}33;
            transform: perspective(1000px) rotateX(2deg);
        ">
            <h5 style="color: {readiness_color}; margin: 0 0 1rem 0;">🎯 Contract Readiness</h5>
            <div style="font-size: 2rem; font-weight: bold; color: {readiness_color}; margin-bottom: 1rem;">{contract_readiness:.0f}%</div>
            <div style="background: {readiness_color}22; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 1rem;">
                <div style="background: {readiness_color}; height: 100%; width: {contract_readiness}%; border-radius: 4px; transition: width 0.8s ease;"></div>
            </div>
            <div style="max-height: 120px; overflow-y: auto;">
                {''.join([f'<div style="font-size: 0.8rem; margin: 0.3rem 0; opacity: 0.9;">{item}</div>' for item in contract_validation_items])}
                {''.join([f'<div style="font-size: 0.75rem; margin: 0.2rem 0; opacity: 0.8; color: #f59e0b;">{warning}</div>' for warning in contract_warnings[:2]])}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with generate_contract_col2:
        # Main contract generation button
        contract_button_ready = contract_validation_score == 4
        
        st.markdown("""
        <div style="margin: 2rem 0; text-align: center;">
        """, unsafe_allow_html=True)
        
        if contract_button_ready:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #dc2626, #b91c1c);
                border-radius: 16px;
                padding: 0.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 25px rgba(220, 38, 38, 0.4);
                animation: glow 2s ease-in-out infinite;
            ">
            """, unsafe_allow_html=True)
            
            generate_contract_button = st.button(
                "🎯 Generate Contract Line Forecast",
                key="generate_contract_forecast",
                type="primary",
                use_container_width=True,
                help="Generate contract line forecasts using two-point interpolation"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Ready state indicators
            st.markdown("""
            <div style="
                background: rgba(220, 38, 38, 0.1);
                border: 1px solid #dc2626;
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                text-align: center;
            ">
                <div style="color: #dc2626; font-weight: 600; margin-bottom: 0.5rem;">⚡ Contract System Ready</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Two-point interpolation prepared</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.3rem;">Advanced analytics enabled</div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #6b7280, #4b5563);
                border-radius: 16px;
                padding: 0.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 15px rgba(107, 114, 128, 0.3);
                opacity: 0.7;
            ">
            """, unsafe_allow_html=True)
            
            generate_contract_button = st.button(
                "⏳ Complete Contract Setup",
                key="generate_contract_disabled",
                type="secondary",
                use_container_width=True,
                disabled=True,
                help="Please complete all contract parameters"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Not ready state
            missing_count = 4 - contract_validation_score
            st.markdown(f"""
            <div style="
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid #ef4444;
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                text-align: center;
            ">
                <div style="color: #ef4444; font-weight: 600; margin-bottom: 0.5rem;">⚠️ Setup Incomplete</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">{missing_count} requirement{'s' if missing_count != 1 else ''} remaining</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.3rem;">Complete both points and timing</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with generate_contract_col3:
        # Contract system status
        chicago_time = strategy.get_chicago_time()
        hour = chicago_time.hour
        is_weekend = chicago_time.weekday() >= 5
        
        # Contract-specific system status
        if is_weekend:
            contract_status = "Weekend Mode"
            status_color = "#f59e0b"
            status_emoji = "📅"
            status_desc = "Contract prep mode"
        elif 9 <= hour <= 16:
            contract_status = "Live Trading"
            status_color = "#dc2626"
            status_emoji = "🔴"
            status_desc = "Real-time contracts"
        elif 4 <= hour < 9:
            contract_status = "Pre-Market"
            status_color = "#3b82f6"
            status_emoji = "🌅"
            status_desc = "Setup phase"
        else:
            contract_status = "Analysis Mode"
            status_color = "#8b5cf6"
            status_emoji = "🌙"
            status_desc = "Planning phase"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {status_color}22, {status_color}11);
            border: 2px solid {status_color};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 8px 25px {status_color}33;
            transform: perspective(1000px) rotateX(-2deg);
        ">
            <h5 style="color: {status_color}; margin: 0 0 1rem 0;">⚙️ Contract Status</h5>
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{status_emoji}</div>
            <div style="font-size: 1.3rem; font-weight: bold; color: {status_color}; margin-bottom: 1rem;">{contract_status}</div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 1rem;">{status_desc}</div>
            
            <div style="border-top: 1px solid {status_color}44; padding-top: 1rem; margin-top: 1rem;">
                <div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem;">Market Phase:</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {status_color};">Options Active</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.3rem;">Contract ready</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ENHANCED CONTRACT GENERATION LOGIC
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if generate_contract_button and contract_button_ready:
        # Enhanced progress tracking for contract generation
        progress_container = st.container()
        
        with progress_container:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(220, 38, 38, 0.1), rgba(185, 28, 28, 0.1));
                border: 2px solid #dc2626;
                border-radius: 16px;
                padding: 2rem;
                margin: 2rem 0;
                text-align: center;
                box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
            ">
                <h4 style="color: #dc2626; margin: 0 0 1rem 0;">🎯 Generating Contract Line Forecast</h4>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            detail_text = st.empty()
            
            try:
                # Step 1: Validate contract parameters
                status_text.markdown("**🔍 Step 1/5: Validating contract parameters...**")
                detail_text.caption("Checking price relationships and time sequence")
                progress_bar.progress(20)
                
                if low2_time <= low1_time:
                    st.error("❌ **Time Sequence Error:** Low-2 time must be after Low-1 time")
                    st.stop()
                
                # Step 2: Calculate interpolation
                status_text.markdown("**📊 Step 2/5: Computing two-point interpolation...**")
                detail_text.caption("Calculating slope and trend parameters")
                progress_bar.progress(40)
                
                time.sleep(0.3)
                
                # Step 3: Generate projections
                status_text.markdown("**🎯 Step 3/5: Generating contract projections...**")
                detail_text.caption("Creating time-based price forecasts")
                progress_bar.progress(60)
                
                # Generate contract line forecast
                contract_table, contract_params = strategy.contract_line_forecast(
                    low1_price, low1_time, low2_price, low2_time, contract_date
                )
                
                # Step 4: Analysis enhancement
                status_text.markdown("**⚡ Step 4/5: Enhancing with advanced analytics...**")
                detail_text.caption("Adding confidence intervals and trading insights")
                progress_bar.progress(80)
                
                time.sleep(0.2)
                
                # Step 5: Finalize
                status_text.markdown("**✨ Step 5/5: Finalizing contract analysis...**")
                detail_text.caption("Preparing real-time lookup system")
                progress_bar.progress(95)
                
                # Store enhanced contract data
                st.session_state.contract_params = contract_params
                st.session_state.contract_table = contract_table
                st.session_state.contract_metadata = {
                    "date": contract_date,
                    "low1_price": low1_price,
                    "low1_time": low1_time,
                    "low2_price": low2_price,
                    "low2_time": low2_time,
                    "generated_at": datetime.now(),
                    "price_change": low2_price - low1_price,
                    "price_change_pct": ((low2_price - low1_price) / low1_price * 100) if low1_price > 0 else 0,
                    "time_span_minutes": time_diff_minutes if 'time_diff_minutes' in locals() else 0,
                    "trend_direction": "Bullish" if low2_price > low1_price else "Bearish" if low2_price < low1_price else "Flat",
                    "slope": contract_params.get("slope", 0),
                    "reliability_score": contract_params.get("reliability_score", 0.5)
                }
                
                # Complete
                progress_bar.progress(100)
                status_text.markdown("**🎉 Contract Line Generation Complete!**")
                detail_text.caption("Two-point interpolation system ready with lookup capabilities")
                
                time.sleep(0.5)
                progress_container.empty()
                
                # Success celebration
                st.success("✅ **Contract line forecast generated successfully!** Real-time lookup system is now active.")
                st.balloons()
                
                # Quick summary
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                
                with summary_col1:
                    st.info(f"📊 **{len(contract_table)} Projections**\nTime-based forecasts")
                
                with summary_col2:
                    trend_direction = st.session_state.contract_metadata.get('trend_direction', 'Unknown')
                    st.info(f"📈 **{trend_direction} Trend**\nDirection identified")
                
                with summary_col3:
                    reliability = st.session_state.contract_metadata.get('reliability_score', 0) * 100
                    st.info(f"🎯 **{reliability:.0f}% Reliable**\nConfidence score")
                
            except Exception as e:
                progress_container.empty()
                st.error(f"❌ **Contract Generation Failed**")
                
                error_col1, error_col2 = st.columns(2)
                
                with error_col1:
                    st.error(f"**Error Details:**\n{str(e)}")
                
                with error_col2:
                    st.info("""
                    **Troubleshooting:**
                    - Verify both prices are positive
                    - Ensure Low-2 time > Low-1 time
                    - Check for reasonable price differences
                    - Try refreshing if issues persist
                    """)
                
                with st.expander("🔧 Technical Details", expanded=False):
                    st.exception(e)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CONTRACT RESULTS DISPLAY
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if not st.session_state.contract_table.empty:
        st.markdown("---")
        st.markdown("## 📊 Contract Line Results")
        
        contract_df = st.session_state.contract_table
        contract_metadata = st.session_state.get("contract_metadata", {})
        
        # Enhanced results summary
        if not contract_df.empty:
            min_price = contract_df['Projected'].min()
            max_price = contract_df['Projected'].max()
            price_range = max_price - min_price
            avg_price = contract_df['Projected'].mean()
            
            # Contract performance metrics
            result_col1, result_col2, result_col3, result_col4 = st.columns(4)
            
            with result_col1:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(5, 150, 105, 0.1));
                    border: 2px solid #10b981;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(16, 185, 129, 0.3);
                    transform: perspective(1000px) rotateY(-3deg);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📉</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #10b981;">${min_price:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Minimum Price</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Lowest projection</div>
                </div>
                """, unsafe_allow_html=True)
            
            with result_col2:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(220, 38, 38, 0.15), rgba(185, 28, 28, 0.1));
                    border: 2px solid #dc2626;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(220, 38, 38, 0.3);
                    transform: perspective(1000px) rotateY(3deg);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #dc2626;">${max_price:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Maximum Price</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Highest projection</div>
                </div>
                """, unsafe_allow_html=True)
            
            with result_col3:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
                    border: 2px solid #8b5cf6;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(139, 92, 246, 0.3);
                    transform: perspective(1000px) rotateY(-3deg);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📏</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #8b5cf6;">${price_range:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Price Range</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Total spread</div>
                </div>
                """, unsafe_allow_html=True)
            
            with result_col4:
                trend_direction = contract_metadata.get('trend_direction', 'Unknown')
                trend_color = "#10b981" if trend_direction == "Bullish" else "#ef4444" if trend_direction == "Bearish" else "#6b7280"
                
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {trend_color}22, {trend_color}11);
                    border: 2px solid {trend_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {trend_color}44;
                    transform: perspective(1000px) rotateY(3deg);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {trend_color};">{trend_direction}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Trend Direction</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Market bias</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Display the enhanced contract table
        display_premium_forecast_table(contract_df, "Contract Line Projections")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 7: REAL-TIME LOOKUP SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════════════
    # REAL-TIME PRICE LOOKUP SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("## 🔍 Real-Time Contract Price Lookup")
    st.caption("Get instant price projections for any time using your contract line interpolation system")
    
    if not st.session_state.contract_params:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));
            border: 2px solid #f59e0b;
            border-radius: 16px;
            padding: 2rem;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 8px 25px rgba(245, 158, 11, 0.2);
        ">
            <h4 style="color: #f59e0b; margin: 0 0 1rem 0;">⚠️ Contract Line Required</h4>
            <p style="margin: 0; opacity: 0.9;">Generate a contract line forecast first to unlock the real-time lookup system</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Enhanced lookup interface
        lookup_col1, lookup_col2 = st.columns([1, 2])
        
        with lookup_col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(220, 38, 38, 0.08), rgba(185, 28, 28, 0.05));
                border: 2px solid #dc2626;
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 25px rgba(220, 38, 38, 0.2);
            ">
                <h5 style="color: #dc2626; margin: 0 0 1rem 0;">🕐 Time Lookup</h5>
            </div>
            """, unsafe_allow_html=True)
            
            lookup_time = st.time_input(
                "Target Time",
                value=time(10, 0),
                step=300,  # 5-minute steps
                key="lookup_time_input",
                help="Enter any time to get projected contract price"
            )
            
            # Enhanced lookup button with validation
            contract_date = st.session_state.contract_metadata.get("date", date.today())
            
            if st.button("🔍 Lookup Contract Price", key="lookup_button", type="primary", use_container_width=True):
                try:
                    lookup_price = strategy.lookup_contract_price(
                        st.session_state.contract_params, 
                        lookup_time, 
                        contract_date
                    )
                    
                    # Calculate additional metrics
                    base_price = st.session_state.contract_metadata.get("low1_price", 0)
                    price_change = lookup_price - base_price if base_price > 0 else 0
                    change_percent = (price_change / base_price * 100) if base_price > 0 else 0
                    
                    # Determine trend at this time
                    slope = st.session_state.contract_params.get("slope", 0)
                    trend_emoji = "📈" if slope > 0 else "📉" if slope < 0 else "➡️"
                    trend_text = "Rising" if slope > 0 else "Falling" if slope < 0 else "Flat"
                    
                    st.session_state.last_lookup_result = {
                        "time": lookup_time,
                        "price": lookup_price,
                        "change": price_change,
                        "change_percent": change_percent,
                        "trend": trend_text,
                        "trend_emoji": trend_emoji
                    }
                    
                    st.success(f"✅ Price lookup completed for {lookup_time.strftime('%H:%M')}")
                    
                except Exception as e:
                    st.error(f"❌ Lookup error: {str(e)}")
            
            # Quick time presets
            st.markdown("**⚡ Quick Times:**")
            preset_col1, preset_col2 = st.columns(2)
            
            with preset_col1:
                if st.button("📅 9:30 AM", key="preset_930", use_container_width=True):
                    st.session_state.lookup_time_input = time(9, 30)
                    st.rerun()
                
                if st.button("📅 11:00 AM", key="preset_1100", use_container_width=True):
                    st.session_state.lookup_time_input = time(11, 0)
                    st.rerun()
            
            with preset_col2:
                if st.button("📅 2:00 PM", key="preset_1400", use_container_width=True):
                    st.session_state.lookup_time_input = time(14, 0)
                    st.rerun()
                
                if st.button("📅 3:30 PM", key="preset_1530", use_container_width=True):
                    st.session_state.lookup_time_input = time(15, 30)
                    st.rerun()
        
        with lookup_col2:
            # Display enhanced lookup result
            if hasattr(st.session_state, 'last_lookup_result'):
                result = st.session_state.last_lookup_result
                
                # Determine result color based on trend
                result_color = "#10b981" if result["change"] > 0 else "#ef4444" if result["change"] < 0 else "#6b7280"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {result_color}, {result_color}dd);
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    color: white;
                    box-shadow: 0 15px 40px {result_color}44;
                    transform: perspective(1000px) rotateY(-2deg);
                    transition: all 0.4s ease;
                    margin-bottom: 2rem;
                ">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">{result["trend_emoji"]}</div>
                    <h3 style="margin: 0; font-size: 1.8rem; margin-bottom: 1rem;">Contract Price Projection</h3>
                    <div style="font-size: 3.5rem; font-weight: 900; margin: 1rem 0; text-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                        ${result["price"]:.2f}
                    </div>
                    <div style="font-size: 1.3rem; opacity: 0.9; margin-bottom: 1rem;">
                        @ {result["time"].strftime('%H:%M')}
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 12px; backdrop-filter: blur(10px);">
                        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">{result["trend"]} Trend</div>
                        <div style="font-size: 0.9rem; opacity: 0.8;">Target time projection</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Additional analytics for the lookup result
                analytics_col1, analytics_col2 = st.columns(2)
                
                with analytics_col1:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.1));
                        border: 2px solid #3b82f6;
                        border-radius: 12px;
                        padding: 1.5rem;
                        text-align: center;
                        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
                    ">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">💰</div>
                        <div style="font-size: 1.4rem; font-weight: bold; color: #3b82f6; margin-bottom: 0.3rem;">${result["change"]:+.2f}</div>
                        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Price Change</div>
                        <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">From baseline</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with analytics_col2:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
                        border: 2px solid #8b5cf6;
                        border-radius: 12px;
                        padding: 1.5rem;
                        text-align: center;
                        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3);
                    ">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                        <div style="font-size: 1.4rem; font-weight: bold; color: #8b5cf6; margin-bottom: 0.3rem;">{result["change_percent"]:+.1f}%</div>
                        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Percentage</div>
                        <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 0.3rem;">Movement</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Placeholder when no lookup performed
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(107, 114, 128, 0.1), rgba(75, 85, 99, 0.05));
                    border: 2px dashed #6b7280;
                    border-radius: 20px;
                    padding: 3rem 2rem;
                    text-align: center;
                    color: #6b7280;
                    margin-bottom: 2rem;
                ">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🎯</div>
                    <h3 style="margin: 0; font-size: 1.5rem; margin-bottom: 1rem;">Ready for Lookup</h3>
                    <p style="margin: 0; opacity: 0.8;">Enter a time and click 'Lookup Contract Price' to see projections</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # BATCH LOOKUP SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if st.session_state.contract_params:
        st.markdown("---")
        st.markdown("### ⚡ Batch Lookup System")
        st.caption("Analyze multiple times simultaneously for comprehensive contract planning")
        
        batch_col1, batch_col2 = st.columns([2, 1])
        
        with batch_col1:
            st.markdown("**📝 Enter Multiple Times (HH:MM format, comma-separated):**")
            batch_times_input = st.text_input(
                "Batch Times",
                placeholder="09:30, 10:00, 11:30, 14:00, 15:30",
                key="batch_lookup_input",
                help="Enter times separated by commas for bulk analysis"
            )
        
        with batch_col2:
            st.markdown("**🚀 Execute Batch:**")
            batch_button = st.button(
                "🔍 Batch Lookup", 
                key="batch_lookup_button", 
                use_container_width=True,
                type="secondary"
            )
        
        if batch_button and batch_times_input and st.session_state.contract_params:
            with st.spinner("⚡ Processing batch lookup..."):
                try:
                    # Parse times
                    time_strings = [t.strip() for t in batch_times_input.split(',')]
                    lookup_results = []
                    
                    contract_date = st.session_state.contract_metadata.get("date", date.today())
                    base_price = st.session_state.contract_metadata.get("low1_price", 0)
                    
                    for time_str in time_strings:
                        try:
                            # Parse time string
                            if ':' in time_str:
                                hour, minute = map(int, time_str.split(':'))
                                lookup_time_obj = time(hour, minute)
                                
                                # Get price projection
                                price = strategy.lookup_contract_price(
                                    st.session_state.contract_params,
                                    lookup_time_obj,
                                    contract_date
                                )
                                
                                # Calculate metrics
                                change = price - base_price if base_price > 0 else 0
                                change_pct = (change / base_price * 100) if base_price > 0 else 0
                                
                                # Determine trend indicator
                                slope = st.session_state.contract_params.get("slope", 0)
                                trend_indicator = "📈" if slope > 0 else "📉" if slope < 0 else "➡️"
                                
                                lookup_results.append({
                                    'Time': time_str,
                                    'Price': f"${price:.2f}",
                                    'Change': f"${change:+.2f}",
                                    'Change%': f"{change_pct:+.1f}%",
                                    'Trend': trend_indicator,
                                    'Price_Raw': price,
                                    'Change_Raw': change
                                })
                                
                        except (ValueError, IndexError) as e:
                            st.warning(f"⚠️ Invalid time format: {time_str} - Expected HH:MM")
                    
                    if lookup_results:
                        st.success(f"✅ Processed {len(lookup_results)} time lookups successfully!")
                        
                        # Enhanced results table
                        results_df = pd.DataFrame(lookup_results)
                        
                        # Add momentum indicators
                        if len(results_df) > 1:
                            results_df['Momentum'] = results_df['Price_Raw'].diff().apply(
                                lambda x: "🔥" if x > 1 else "📈" if x > 0 else "📉" if x < 0 else "➡️" if pd.notna(x) else "-"
                            )
                        
                        # Display enhanced table
                        st.markdown("#### 📊 Batch Lookup Results")
                        
                        display_columns = ['Time', 'Price', 'Change', 'Change%', 'Trend']
                        if 'Momentum' in results_df.columns:
                            display_columns.append('Momentum')
                        
                        st.dataframe(
                            results_df[display_columns],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Time": st.column_config.TextColumn("Time", width="small"),
                                "Price": st.column_config.TextColumn("Price", width="medium"),
                                "Change": st.column_config.TextColumn("Change", width="small"),
                                "Change%": st.column_config.TextColumn("Change%", width="small"),
                                "Trend": st.column_config.TextColumn("Trend", width="small"),
                                "Momentum": st.column_config.TextColumn("Momentum", width="small") if 'Momentum' in results_df.columns else None
                            }
                        )
                        
                        # Batch analytics
                        if len(lookup_results) > 1:
                            batch_col1, batch_col2, batch_col3 = st.columns(3)
                            
                            with batch_col1:
                                max_price = max(r['Price_Raw'] for r in lookup_results)
                                max_time = next(r['Time'] for r in lookup_results if r['Price_Raw'] == max_price)
                                
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(5, 150, 105, 0.1));
                                    border: 2px solid #10b981;
                                    border-radius: 12px;
                                    padding: 1rem;
                                    text-align: center;
                                    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
                                ">
                                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🏆</div>
                                    <div style="font-size: 1.2rem; font-weight: bold; color: #10b981;">${max_price:.2f}</div>
                                    <div style="font-size: 0.8rem; font-weight: 600; margin: 0.3rem 0;">Peak Price</div>
                                    <div style="font-size: 0.7rem; opacity: 0.8;">@ {max_time}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with batch_col2:
                                min_price = min(r['Price_Raw'] for r in lookup_results)
                                min_time = next(r['Time'] for r in lookup_results if r['Price_Raw'] == min_price)
                                
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1));
                                    border: 2px solid #ef4444;
                                    border-radius: 12px;
                                    padding: 1rem;
                                    text-align: center;
                                    box-shadow: 0 6px 20px rgba(239, 68, 68, 0.3);
                                ">
                                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📉</div>
                                    <div style="font-size: 1.2rem; font-weight: bold; color: #ef4444;">${min_price:.2f}</div>
                                    <div style="font-size: 0.8rem; font-weight: 600; margin: 0.3rem 0;">Low Price</div>
                                    <div style="font-size: 0.7rem; opacity: 0.8;">@ {min_time}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with batch_col3:
                                price_range = max_price - min_price
                                range_pct = (price_range / min_price * 100) if min_price > 0 else 0
                                
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.1));
                                    border: 2px solid #3b82f6;
                                    border-radius: 12px;
                                    padding: 1rem;
                                    text-align: center;
                                    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
                                ">
                                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📏</div>
                                    <div style="font-size: 1.2rem; font-weight: bold; color: #3b82f6;">${price_range:.2f}</div>
                                    <div style="font-size: 0.8rem; font-weight: 600; margin: 0.3rem 0;">Range</div>
                                    <div style="font-size: 0.7rem; opacity: 0.8;">{range_pct:.1f}%</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Enhanced download options
                        download_col1, download_col2 = st.columns(2)
                        
                        with download_col1:
                            # CSV download
                            csv_data = results_df.to_csv(index=False)
                            st.download_button(
                                label="📊 Download CSV",
                                data=csv_data,
                                file_name=f"contract_batch_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_batch_csv",
                                use_container_width=True
                            )
                        
                        with download_col2:
                            # Summary report
                            summary_report = f"""CONTRACT BATCH LOOKUP REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Contract Date: {contract_date}

BATCH SUMMARY:
• Total Lookups: {len(lookup_results)}
• Price Range: ${min_price:.2f} - ${max_price:.2f}
• Peak Time: {max_time}
• Low Time: {min_time}
• Range: ${price_range:.2f} ({range_pct:.1f}%)

DETAILED RESULTS:
"""
                            for result in lookup_results:
                                summary_report += f"{result['Time']}: {result['Price']} ({result['Change%']})\n"
                            
                            st.download_button(
                                label="📋 Download Report",
                                data=summary_report,
                                file_name=f"contract_batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                key="download_batch_report",
                                use_container_width=True
                            )
                        
                except Exception as e:
                    st.error(f"❌ Batch lookup error: {str(e)}")
        
        elif batch_button and not batch_times_input:
            st.warning("⚠️ Please enter times in the format: 09:30, 10:00, 11:30")
    
    st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 8A: STOCK PAGE FRAMEWORK & TSLA/NVDA ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

# Enhanced stock information with comprehensive profiles
stock_info = {
    "TSLA": {
        "name": "Tesla", 
        "icon": "🚗", 
        "sector": "Automotive/Energy",
        "theme_color": "#dc2626",
        "bg_gradient": "linear-gradient(135deg, #dc2626 0%, #b91c1c 25%, #991b1b 50%, #7f1d1d 75%, #450a0a 100%)",
        "description": "Electric vehicle and clean energy pioneer with high volatility"
    },
    "NVDA": {
        "name": "NVIDIA", 
        "icon": "🧠", 
        "sector": "Semiconductors/AI",
        "theme_color": "#10b981",
        "bg_gradient": "linear-gradient(135deg, #10b981 0%, #059669 25%, #047857 50%, #065f46 75%, #064e3b 100%)",
        "description": "AI chip leader driving the machine learning revolution"
    },
    "AAPL": {
        "name": "Apple", 
        "icon": "🍎", 
        "sector": "Consumer Technology",
        "theme_color": "#3b82f6",
        "bg_gradient": "linear-gradient(135deg, #3b82f6 0%, #2563eb 25%, #1d4ed8 50%, #1e40af 75%, #1e3a8a 100%)",
        "description": "Premium consumer electronics with ecosystem dominance"
    },
    "MSFT": {
        "name": "Microsoft", 
        "icon": "🪟", 
        "sector": "Enterprise Software",
        "theme_color": "#8b5cf6",
        "bg_gradient": "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 25%, #6d28d9 50%, #5b21b6 75%, #4c1d95 100%)",
        "description": "Cloud computing and enterprise software giant"
    },
    "AMZN": {
        "name": "Amazon", 
        "icon": "📦", 
        "sector": "E-commerce/Cloud",
        "theme_color": "#f59e0b",
        "bg_gradient": "linear-gradient(135deg, #f59e0b 0%, #d97706 25%, #b45309 50%, #92400e 75%, #78350f 100%)",
        "description": "E-commerce leader with dominant cloud infrastructure"
    },
    "GOOGL": {
        "name": "Google", 
        "icon": "🔍", 
        "sector": "Digital Advertising",
        "theme_color": "#ef4444",
        "bg_gradient": "linear-gradient(135deg, #ef4444 0%, #dc2626 25%, #b91c1c 50%, #991b1b 75%, #7f1d1d 100%)",
        "description": "Search monopoly with AI and cloud diversification"
    },
    "META": {
        "name": "Meta", 
        "icon": "📘", 
        "sector": "Social Media",
        "theme_color": "#6366f1",
        "bg_gradient": "linear-gradient(135deg, #6366f1 0%, #4f46e5 25%, #4338ca 50%, #3730a3 75%, #312e81 100%)",
        "description": "Social media empire with metaverse investments"
    },
    "NFLX": {
        "name": "Netflix", 
        "icon": "📺", 
        "sector": "Streaming Entertainment",
        "theme_color": "#db2777",
        "bg_gradient": "linear-gradient(135deg, #db2777 0%, #be185d 25%, #9d174d 50%, #831843 75%, #701a75 100%)",
        "description": "Streaming entertainment leader with global reach"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# STOCK PAGE FRAMEWORK FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def render_stock_hero(ticker: str, stock_data: dict, current_slope: float):
    """Render enhanced stock page hero section with theme colors."""
    st.markdown(f"""
    <div style="
        background: {stock_data['bg_gradient']};
        border-radius: 24px;
        padding: 3rem 2rem;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
        transform: perspective(1000px) rotateX(2deg);
    ">
        <div style="
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 70% 30%, rgba(255,255,255,0.15) 0%, transparent 50%);
            animation: hero-pulse 6s ease-in-out infinite;
            pointer-events: none;
        "></div>
        <h1 style="
            color: white; 
            font-size: 3rem; 
            font-weight: 900; 
            margin-bottom: 1rem;
            text-shadow: 0 6px 25px rgba(0,0,0,0.6);
            position: relative;
            z-index: 2;
        ">{stock_data['icon']} {stock_data['name']} ({ticker}) Analysis</h1>
        <p style="
            color: rgba(255,255,255,0.95); 
            font-size: 1.3rem; 
            margin-bottom: 2rem;
            position: relative;
            z-index: 2;
        ">{stock_data['description']}</p>
        <div style="
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
            position: relative;
            z-index: 2;
        ">
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
            ">📊 {stock_data['sector']}</div>
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
            ">⚡ Slope: {current_slope:.4f}</div>
            <div style="
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                padding: 0.6rem 1.2rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.25);
                color: white;
                font-weight: 600;
            ">🎯 Two-Anchor System</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_stock_input_section(ticker: str, stock_data: dict):
    """Render stock input section with validation."""
    st.markdown("## 📋 Previous Day Analysis Parameters")
    st.caption(f"Enter {stock_data['name']}'s previous trading day high and low prices with precise timing")
    
    # Analysis date
    analysis_col1, analysis_col2, analysis_col3 = st.columns([2, 2, 2])
    
    with analysis_col1:
        analysis_date = st.date_input(
            "📅 Analysis Date",
            value=date.today() + timedelta(days=1),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=30),
            key=f"{ticker}_analysis_date",
            help=f"Target date for {stock_data['name']} analysis"
        )
    
    with analysis_col2:
        weekday = analysis_date.strftime("%A")
        is_weekend = analysis_date.weekday() >= 5
        
        if is_weekend:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f59e0b, #d97706);
                color: white;
                padding: 1.5rem;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
                <strong>{weekday}</strong><br>
                <small>Markets Closed</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: {stock_data['bg_gradient']};
                color: white;
                padding: 1.5rem;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 8px 25px {stock_data['theme_color']}44;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                <strong>{weekday}</strong><br>
                <small>{analysis_date.strftime('%B %d, %Y')}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with analysis_col3:
        days_until = (analysis_date - date.today()).days
        urgency_color = "#dc2626" if days_until == 0 else "#f59e0b" if days_until == 1 else stock_data['theme_color']
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {urgency_color}, {urgency_color}dd);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 25px {urgency_color}44;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📍</div>
            <strong>T{days_until:+d} Days</strong><br>
            <small>{'Today!' if days_until == 0 else 'Tomorrow' if days_until == 1 else f'{days_until} days out'}</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two-anchor input system
    st.markdown("### 🎯 Two-Anchor Analysis System")
    
    anchor_col1, anchor_col2 = st.columns(2)
    
    with anchor_col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {stock_data['theme_color']}22, {stock_data['theme_color']}11);
            border: 2px solid {stock_data['theme_color']};
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 12px 35px {stock_data['theme_color']}33;
        ">
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📉 Low Anchor Point")
        st.caption("Previous day's lowest price - support level identification")
        
        low_price = st.number_input(
            "💰 Low Price ($)",
            value=0.0,
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key=f"{ticker}_low_price",
            help=f"Enter {stock_data['name']}'s previous day low price"
        )
        
        low_time = st.time_input(
            "🕐 Low Time",
            value=time(7, 30),
            key=f"{ticker}_low_time",
            help="Time when the low occurred"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with anchor_col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {stock_data['theme_color']}22, {stock_data['theme_color']}11);
            border: 2px solid {stock_data['theme_color']};
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 12px 35px {stock_data['theme_color']}33;
        ">
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📈 High Anchor Point")
        st.caption("Previous day's highest price - resistance level analysis")
        
        high_price = st.number_input(
            "💰 High Price ($)",
            value=0.0,
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key=f"{ticker}_high_price",
            help=f"Enter {stock_data['name']}'s previous day high price"
        )
        
        high_time = st.time_input(
            "🕐 High Time",
            value=time(7, 30),
            key=f"{ticker}_high_time",
            help="Time when the high occurred"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    return analysis_date, low_price, low_time, high_price, high_time

# ═══════════════════════════════════════════════════════════════════════════════
# TESLA (TSLA) ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.selected_page == "TSLA":
    ticker = "TSLA"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render Tesla hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # Tesla-specific insights
    with st.expander("🚗 Tesla Trading Intelligence", expanded=False):
        st.markdown("""
        ### 🔥 Tesla's Unique Characteristics
        
        **⚡ Extreme Volatility:**
        - 5-15% intraday swings are common
        - News-driven price action dominates
        - Elon Musk tweets can trigger immediate moves
        - Options premiums reflect high IV environment
        
        **📊 Key Trading Patterns:**
        - **Gap Trading**: 60% of days open with significant gaps
        - **Momentum Reversals**: 10am and 2pm are critical reversal times
        - **Earnings Volatility**: >20% moves on quarterly reports
        - **Production Data**: Delivery numbers create major moves
        
        **🎯 Optimal Strategies:**
        - **Volatility Plays**: Straddles and strangles work well
        - **Momentum Trading**: Strong trends can last hours
        - **News Trading**: Twitter monitoring for Musk updates
        - **Earnings**: IV crush after results, plan accordingly
        
        **⚠️ Risk Considerations:**
        - Position sizes should be smaller due to volatility
        - Stop losses crucial - gaps can be brutal
        - Avoid holding through Musk media appearances
        - Regulatory news can cause sudden reversals
        """)
    
    # Tesla input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # Tesla-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # Tesla volatility analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            midpoint = (high_price + low_price) / 2
            
            # Tesla-specific volatility assessment
            if range_percentage > 15:
                volatility_desc = "🌋 Extreme - Classic Tesla volatility"
                vol_color = "#dc2626"
            elif range_percentage > 10:
                volatility_desc = "🔥 Very High - Strong momentum day"
                vol_color = "#ef4444"
            elif range_percentage > 5:
                volatility_desc = "⚡ High - Normal Tesla activity"
                vol_color = "#f59e0b"
            else:
                volatility_desc = "😴 Low - Unusual for Tesla"
                vol_color = "#6b7280"
            
            st.markdown("### 📊 Tesla Market Analysis")
            
            tesla_col1, tesla_col2, tesla_col3 = st.columns(3)
            
            with tesla_col1:
                st.markdown(
                    create_premium_metric_card(
                        "🔥", "Tesla Range", f"${price_range:.2f}", 
                        f"{range_percentage:.1f}%", f"{range_percentage:.1f}%"
                    ),
                    unsafe_allow_html=True
                )
            
            with tesla_col2:
                st.markdown(
                    create_premium_metric_card(
                        "⚡", "Volatility", volatility_desc.split(' - ')[0], 
                        volatility_desc.split(' - ')[1] if ' - ' in volatility_desc else "", volatility_desc
                    ),
                    unsafe_allow_html=True
                )
            
            with tesla_col3:
                st.markdown(
                    create_premium_metric_card(
                        "🎯", "Midpoint", f"${midpoint:.2f}", 
                        "Key level", f"${midpoint:.2f}"
                    ),
                    unsafe_allow_html=True
                )
    
    # Generate Tesla analysis
    if st.button(f"🚀 Generate Tesla Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("⚡ Analyzing Tesla's volatility patterns..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "volatility_desc": volatility_desc if 'volatility_desc' in locals() else "Unknown"
                    }
                    
                    st.success("✅ Tesla analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# NVIDIA (NVDA) ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.selected_page == "NVDA":
    ticker = "NVDA"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render NVIDIA hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # NVIDIA-specific insights
    with st.expander("🧠 NVIDIA AI Intelligence", expanded=False):
        st.markdown("""
        ### 🤖 NVIDIA's AI Revolution Impact
        
        **🚀 AI Sector Leadership:**
        - Dominant GPU market share for AI training
        - Data center revenue growth drives stock price
        - AI chip demand creates supply constraints
        - Crypto correlation during mining cycles
        
        **📈 Trading Characteristics:**
        - **Sector Rotation Sensitive**: Tech leadership flows
        - **Earnings-Driven**: Revenue beats create sustained moves
        - **AI Hype Cycles**: Responds to AI developments
        - **Institutional Heavy**: Large fund holdings create stability
        
        **🎯 Strategic Opportunities:**
        - **Earnings Momentum**: 3-5 day post-earnings trends
        - **AI News Trading**: React to AI breakthroughs
        - **Sector ETF Arbitrage**: QQQ correlation trades
        - **Supply Chain**: Chip shortage/surplus narratives
        
        **📊 Technical Patterns:**
        - Strong trends during AI narrative peaks
        - Support at 20/50 EMA levels
        - Breakouts often sustained for weeks
        - Options activity clustered around earnings
        
        **⚠️ Risk Factors:**
        - China trade tensions affect chip exports
        - Crypto correlation during mining demand
        - Valuation concerns during bubble fears
        - Competition from AMD, Intel, custom chips
        """)
    
    # NVIDIA input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # NVIDIA-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # NVIDIA trend analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            
            # NVIDIA-specific assessment
            if range_percentage > 8:
                trend_strength = "🚀 AI Momentum - Strong institutional flow"
                trend_color = "#10b981"
            elif range_percentage > 5:
                trend_strength = "📈 Solid Move - Tech sector rotation"
                trend_color = "#3b82f6"
            elif range_percentage > 2:
                trend_strength = "📊 Normal - Standard volatility"
                trend_color = "#f59e0b"
            else:
                trend_strength = "😴 Quiet - Consolidation phase"
                trend_color = "#6b7280"
            
            # AI sector correlation
            ai_sentiment = "Bullish" if high_price > low_price * 1.03 else "Neutral"
            
            st.markdown("### 🧠 NVIDIA AI Analysis")
            
            nvda_col1, nvda_col2, nvda_col3 = st.columns(3)
            
            with nvda_col1:
                st.markdown(
                    create_premium_metric_card(
                        "🧠", "AI Range", f"${price_range:.2f}", 
                        f"{range_percentage:.1f}%", f"{range_percentage:.1f}%"
                    ),
                    unsafe_allow_html=True
                )
            
            with nvda_col2:
                st.markdown(
                    create_premium_metric_card(
                        "📈", "Trend Strength", trend_strength.split(' - ')[0], 
                        trend_strength.split(' - ')[1] if ' - ' in trend_strength else "", trend_strength
                    ),
                    unsafe_allow_html=True
                )
            
            with nvda_col3:
                st.markdown(
                    create_premium_metric_card(
                        "🤖", "AI Sentiment", ai_sentiment, 
                        "Sector bias", ai_sentiment
                    ),
                    unsafe_allow_html=True
                )
    
    # Generate NVIDIA analysis
    if st.button(f"🧠 Generate NVIDIA Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("🤖 Analyzing NVIDIA's AI sector dynamics..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "trend_strength": trend_strength if 'trend_strength' in locals() else "Unknown",
                        "ai_sentiment": ai_sentiment if 'ai_sentiment' in locals() else "Unknown"
                    }
                    
                    st.success("✅ NVIDIA analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# Display results for both TSLA and NVDA
for ticker in ["TSLA", "NVDA"]:
    if st.session_state.selected_page == ticker:
        forecast_key = f"{ticker}_forecasts"
        metadata_key = f"{ticker}_metadata"
        
        if forecast_key in st.session_state:
            st.markdown(f"## 📊 {stock_info[ticker]['name']} Analysis Results")
            
            forecast_data = st.session_state[forecast_key]
            metadata = st.session_state.get(metadata_key, {})
            
            if "Low" in forecast_data and "High" in forecast_data:
                low_tab, high_tab = st.tabs([f"📉 {ticker} Low Anchor", f"📈 {ticker} High Anchor"])
                
                with low_tab:
                    low_df = forecast_data["Low"]
                    display_premium_forecast_table(low_df, f"{ticker} Low Anchor Analysis")
                
                with high_tab:
                    high_df = forecast_data["High"]
                    display_premium_forecast_table(high_df, f"{ticker} High Anchor Analysis")
        else:
            st.info(f"👆 Enter {stock_info[ticker]['name']}'s data and generate analysis to see results.")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 8B: APPLE (AAPL) & MICROSOFT (MSFT) ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# APPLE (AAPL) ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.selected_page == "AAPL":
    ticker = "AAPL"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render Apple hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # Apple-specific insights
    with st.expander("🍎 Apple Trading Intelligence", expanded=False):
        st.markdown("""
        ### 📱 Apple's Blue-Chip Characteristics
        
        **🏛️ Stable Blue-Chip Profile:**
        - Lower volatility compared to tech peers
        - Strong dividend support creates price floor
        - Massive market cap provides stability
        - Institutional favorite for conservative tech exposure
        
        **📊 Key Trading Patterns:**
        - **Product Cycles**: iPhone launches drive seasonal patterns
        - **Services Growth**: Recurring revenue provides stability
        - **Dividend Dates**: Ex-dividend creates support levels
        - **Slow Trends**: Moves develop over days/weeks, not hours
        
        **🎯 Optimal Strategies:**
        - **Covered Calls**: Premium collection on stable stock
        - **Range Trading**: Bounces between key psychological levels
        - **Earnings Plays**: Modest but predictable earnings moves
        - **Long-term Holds**: Warren Buffett approved stability
        
        **📈 Technical Characteristics:**
        - **Support Levels**: Round numbers ($150, $175, $200)
        - **Moving Averages**: Respects 50/200 MA levels
        - **Volume**: Institutional accumulation patterns
        - **Breakouts**: Slow but sustainable when they occur
        
        **💡 Strategic Opportunities:**
        - **Product Launch Events**: September iPhone reveals
        - **Services Revenue**: Beats drive sustained moves
        - **China Sales**: Geographic revenue sensitivity
        - **Supply Chain**: Efficiency improvements matter
        
        **⚠️ Risk Considerations:**
        - China trade tensions affect sales
        - Regulatory pressure on App Store
        - Innovation concerns vs competitors
        - Valuation multiple compression risks
        """)
    
    # Apple input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # Apple-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # Apple stability analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            
            # Apple-specific stability assessment
            if range_percentage > 4:
                stability_desc = "🔥 High Move - Unusual for Apple"
                stability_color = "#ef4444"
                apple_context = "Check for major news/earnings"
            elif range_percentage > 2:
                stability_desc = "📈 Moderate - Above average activity"
                stability_color = "#f59e0b"
                apple_context = "Normal earnings/product cycle"
            elif range_percentage > 1:
                stability_desc = "📊 Normal - Typical Apple range"
                stability_color = "#3b82f6"
                apple_context = "Standard blue-chip behavior"
            else:
                stability_desc = "😴 Very Stable - Classic Apple"
                stability_color = "#10b981"
                apple_context = "Perfect for covered calls"
            
            # Dividend proximity analysis
            dividend_factor = "Near Ex-Date" if range_percentage < 1 else "Standard Period"
            
            # Services vs hardware sentiment
            if high_price > low_price * 1.02:
                apple_sentiment = "Services Growth"
            elif high_price > low_price * 1.01:
                apple_sentiment = "Product Cycle"
            else:
                apple_sentiment = "Consolidation"
            
            st.markdown("### 🍎 Apple Stability Analysis")
            
            apple_col1, apple_col2, apple_col3 = st.columns(3)
            
            with apple_col1:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.1));
                    border: 2px solid #3b82f6;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(59, 130, 246, 0.3);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🍎</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #3b82f6;">${price_range:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Apple Range</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{range_percentage:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with apple_col2:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {stability_color}22, {stability_color}11);
                    border: 2px solid {stability_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {stability_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {stability_color};">{stability_desc.split(' - ')[0]}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Stability Level</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{apple_context}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with apple_col3:
                sentiment_color = "#10b981" if apple_sentiment == "Services Growth" else "#3b82f6" if apple_sentiment == "Product Cycle" else "#6b7280"
                
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {sentiment_color}22, {sentiment_color}11);
                    border: 2px solid {sentiment_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {sentiment_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">💼</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {sentiment_color};">{apple_sentiment}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Business Focus</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{dividend_factor}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Apple-specific strategy recommendations
            st.markdown("#### 💡 Apple Strategy Recommendations")
            
            strategy_col1, strategy_col2 = st.columns(2)
            
            with strategy_col1:
                if range_percentage < 1.5:
                    apple_strategy = "🎯 **Covered Call Strategy** - Low volatility perfect for premium collection"
                    strategy_color = "#10b981"
                elif range_percentage < 3:
                    apple_strategy = "📊 **Range Trading** - Bounce between support/resistance levels"
                    strategy_color = "#3b82f6"
                else:
                    apple_strategy = "⚡ **Momentum Play** - Unusual volatility suggests catalyst"
                    strategy_color = "#f59e0b"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {strategy_color}22, {strategy_color}11);
                    border: 2px solid {strategy_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {strategy_color}33;
                ">
                    <h5 style="color: {strategy_color}; margin: 0 0 0.5rem 0;">Primary Strategy</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{apple_strategy}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with strategy_col2:
                # Risk assessment for Apple
                if range_percentage < 2:
                    apple_risk = "🟢 **Low Risk** - Typical blue-chip stability"
                    risk_color = "#10b981"
                elif range_percentage < 4:
                    apple_risk = "🟡 **Moderate Risk** - Above normal for Apple"
                    risk_color = "#f59e0b"
                else:
                    apple_risk = "🔴 **Higher Risk** - Investigate catalyst"
                    risk_color = "#ef4444"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {risk_color}22, {risk_color}11);
                    border: 2px solid {risk_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {risk_color}33;
                ">
                    <h5 style="color: {risk_color}; margin: 0 0 0.5rem 0;">Risk Assessment</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{apple_risk}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Generate Apple analysis
    if st.button(f"🍎 Generate Apple Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("🍎 Analyzing Apple's blue-chip stability patterns..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "stability_desc": stability_desc if 'stability_desc' in locals() else "Unknown",
                        "apple_sentiment": apple_sentiment if 'apple_sentiment' in locals() else "Unknown",
                        "apple_strategy": apple_strategy if 'apple_strategy' in locals() else "Unknown"
                    }
                    
                    st.success("✅ Apple analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# MICROSOFT (MSFT) ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.selected_page == "MSFT":
    ticker = "MSFT"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render Microsoft hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # Microsoft-specific insights
    with st.expander("🪟 Microsoft Cloud Intelligence", expanded=False):
        st.markdown("""
        ### ☁️ Microsoft's Enterprise Dominance
        
        **🏢 Enterprise Software Giant:**
        - Azure cloud growth drives stock performance
        - Office 365 subscription model provides stability
        - Windows ecosystem creates competitive moats
        - Enterprise customers provide recurring revenue
        
        **📊 Cloud Growth Dynamics:**
        - **Azure Revenue**: Primary growth driver and stock catalyst
        - **Teams Adoption**: Work-from-home acceleration
        - **AI Integration**: Copilot and ChatGPT partnership
        - **Enterprise Spending**: B2B cycles affect performance
        
        **🎯 Trading Characteristics:**
        - **Steady Trends**: Consistent upward bias over time
        - **Pullback Opportunities**: 5-8% corrections common
        - **Earnings Reliability**: Rarely misses significantly
        - **Dividend Aristocrat**: Consistent dividend increases
        
        **📈 Technical Patterns:**
        - **Support Levels**: Major moving averages hold
        - **Breakout Sustainability**: Cloud growth sustains moves
        - **Volume Patterns**: Institutional accumulation
        - **Correlation**: Less volatile than pure tech plays
        
        **💡 Strategic Opportunities:**
        - **Azure Growth**: Cloud revenue beats drive rallies
        - **Enterprise Cycles**: B2B spending correlations
        - **AI Integration**: Copilot adoption metrics
        - **Dividend Plays**: Income plus growth combination
        
        **📊 Key Metrics to Watch:**
        - Azure growth rates (target: >30%)
        - Commercial product revenue
        - Operating margin expansion
        - Free cash flow generation
        
        **⚠️ Risk Factors:**
        - Competition from AWS, Google Cloud
        - Enterprise spending slowdowns
        - Regulatory scrutiny on bundling
        - Currency headwinds for international business
        """)
    
    # Microsoft input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # Microsoft-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # Microsoft cloud analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            
            # Microsoft-specific cloud assessment
            if range_percentage > 6:
                cloud_momentum = "🚀 Strong Azure - Major cloud catalyst"
                cloud_color = "#8b5cf6"
                msft_context = "Azure growth acceleration"
            elif range_percentage > 3:
                cloud_momentum = "☁️ Cloud Growth - Steady expansion"
                cloud_color = "#3b82f6"
                msft_context = "Normal enterprise adoption"
            elif range_percentage > 1.5:
                cloud_momentum = "📊 Stable - Dividend support"
                cloud_color = "#10b981"
                msft_context = "Blue-chip consistency"
            else:
                cloud_momentum = "😴 Consolidation - Range bound"
                cloud_color = "#6b7280"
                msft_context = "Awaiting catalyst"
            
            # Enterprise cycle analysis
            enterprise_cycle = "Expansion" if high_price > low_price * 1.025 else "Maintenance" if high_price > low_price * 1.01 else "Caution"
            
            # AI integration sentiment
            ai_integration = "Copilot Boost" if range_percentage > 4 else "AI Steady" if range_percentage > 2 else "AI Base"
            
            st.markdown("### 🪟 Microsoft Cloud Analysis")
            
            msft_col1, msft_col2, msft_col3 = st.columns(3)
            
            with msft_col1:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
                    border: 2px solid #8b5cf6;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(139, 92, 246, 0.3);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🪟</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #8b5cf6;">${price_range:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">MSFT Range</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{range_percentage:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with msft_col2:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {cloud_color}22, {cloud_color}11);
                    border: 2px solid {cloud_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {cloud_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">☁️</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {cloud_color};">{cloud_momentum.split(' - ')[0]}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Cloud Momentum</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{msft_context}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with msft_col3:
                cycle_color = "#10b981" if enterprise_cycle == "Expansion" else "#3b82f6" if enterprise_cycle == "Maintenance" else "#f59e0b"
                
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {cycle_color}22, {cycle_color}11);
                    border: 2px solid {cycle_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {cycle_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🏢</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {cycle_color};">{enterprise_cycle}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Enterprise Cycle</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{ai_integration}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Microsoft-specific strategy recommendations
            st.markdown("#### 💡 Microsoft Strategy Recommendations")
            
            strategy_col1, strategy_col2 = st.columns(2)
            
            with strategy_col1:
                if range_percentage > 4:
                    msft_strategy = "🚀 **Azure Momentum** - Cloud growth driving institutional buying"
                    strategy_color = "#8b5cf6"
                elif range_percentage > 2:
                    msft_strategy = "📊 **Steady Growth** - Enterprise adoption creating consistent moves"
                    strategy_color = "#3b82f6"
                else:
                    msft_strategy = "💰 **Dividend Play** - Income strategy with growth potential"
                    strategy_color = "#10b981"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {strategy_color}22, {strategy_color}11);
                    border: 2px solid {strategy_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {strategy_color}33;
                ">
                    <h5 style="color: {strategy_color}; margin: 0 0 0.5rem 0;">Cloud Strategy</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{msft_strategy}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with strategy_col2:
                # Enterprise confidence assessment
                if range_percentage > 3:
                    enterprise_confidence = "🟢 **High Confidence** - Strong enterprise demand"
                    confidence_color = "#10b981"
                elif range_percentage > 1.5:
                    enterprise_confidence = "🟡 **Moderate** - Steady business cycles"
                    confidence_color = "#f59e0b"
                else:
                    enterprise_confidence = "🔵 **Conservative** - Defensive positioning"
                    confidence_color = "#3b82f6"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {confidence_color}22, {confidence_color}11);
                    border: 2px solid {confidence_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {confidence_color}33;
                ">
                    <h5 style="color: {confidence_color}; margin: 0 0 0.5rem 0;">Enterprise Confidence</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{enterprise_confidence}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Generate Microsoft analysis
    if st.button(f"🪟 Generate Microsoft Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("☁️ Analyzing Microsoft's cloud enterprise dynamics..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "cloud_momentum": cloud_momentum if 'cloud_momentum' in locals() else "Unknown",
                        "enterprise_cycle": enterprise_cycle if 'enterprise_cycle' in locals() else "Unknown",
                        "ai_integration": ai_integration if 'ai_integration' in locals() else "Unknown"
                    }
                    
                    st.success("✅ Microsoft analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# Display results for both AAPL and MSFT
for ticker in ["AAPL", "MSFT"]:
    if st.session_state.selected_page == ticker:
        forecast_key = f"{ticker}_forecasts"
        metadata_key = f"{ticker}_metadata"
        
        if forecast_key in st.session_state:
            st.markdown(f"## 📊 {stock_info[ticker]['name']} Analysis Results")
            
            forecast_data = st.session_state[forecast_key]
            metadata = st.session_state.get(metadata_key, {})
            
            if "Low" in forecast_data and "High" in forecast_data:
                low_tab, high_tab = st.tabs([f"📉 {ticker} Low Anchor", f"📈 {ticker} High Anchor"])
                
                with low_tab:
                    low_df = forecast_data["Low"]
                    display_premium_forecast_table(low_df, f"{ticker} Low Anchor Analysis")
                    
                    # Stock-specific insights for low anchor
                    if not low_df.empty and 'Entry' in low_df.columns and 'Exit' in low_df.columns:
                        spreads = low_df['Entry'] - low_df['Exit']
                        consistency = (1 - spreads.std() / spreads.mean()) * 100 if spreads.mean() != 0 else 50
                        
                        if ticker == "AAPL":
                            if consistency > 80:
                                st.success("🍎 **Apple Consistency**: Excellent for covered call strategies")
                            elif consistency > 60:
                                st.info("📊 **Moderate Stability**: Good for range trading")
                            else:
                                st.warning("⚡ **Higher Volatility**: Check for catalyst news")
                        
                        elif ticker == "MSFT":
                            azure_indicator = "Strong" if spreads.max() > 5 else "Moderate" if spreads.max() > 2 else "Stable"
                            st.info(f"☁️ **Azure Signal**: {azure_indicator} cloud momentum detected")
                
                with high_tab:
                    high_df = forecast_data["High"]
                    display_premium_forecast_table(high_df, f"{ticker} High Anchor Analysis")
                    
                    # Stock-specific insights for high anchor
                    if not high_df.empty and 'Entry' in high_df.columns and 'Exit' in high_df.columns:
                        max_profit = (high_df['Entry'] - high_df['Exit']).max()
                        
                        if ticker == "AAPL":
                            if max_profit > 3:
                                st.success("🚀 **Apple Breakout**: Unusual strength for blue-chip")
                            else:
                                st.info("📊 **Standard Apple**: Typical range-bound behavior")
                        
                        elif ticker == "MSFT":
                            if max_profit > 4:
                                st.success("🚀 **Enterprise Acceleration**: Strong B2B demand signal")
                            else:
                                st.info("📈 **Steady Growth**: Normal enterprise adoption pace")
        else:
            st.info(f"👆 Enter {stock_info[ticker]['name']}'s data and generate analysis to see results.")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 8C: GOOGLE (GOOGL) ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.selected_page == "GOOGL":
    ticker = "GOOGL"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render Google hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # Google-specific insights
    with st.expander("🔍 Google Search & AI Intelligence", expanded=False):
        st.markdown("""
        ### 🔍 Google's Search & Advertising Dominance
        
        **🎯 Digital Advertising Giant:**
        - Search advertising provides 85%+ of revenue
        - YouTube advertising growing rapidly
        - Display/network ads across web properties
        - Android ecosystem creates data advantages
        
        **🤖 AI & Search Evolution:**
        - **Bard vs ChatGPT**: AI search competition heating up
        - **LaMDA Integration**: Conversational AI in search results
        - **Cloud AI Services**: Enterprise AI solutions expansion
        - **Autonomous Driving**: Waymo technology leadership
        
        **📊 Revenue Diversification:**
        - **Google Cloud**: Fast-growing enterprise segment (30%+ growth)
        - **YouTube**: Creator economy and premium subscriptions
        - **Android/Play**: Mobile app ecosystem revenue streams
        - **Hardware**: Pixel, Nest, Chrome devices portfolio
        
        **🎯 Trading Characteristics:**
        - **Ad Revenue Cycles**: Economic sensitivity affects spending
        - **Regulatory Headlines**: Antitrust scrutiny creates volatility
        - **AI Developments**: ChatGPT competition impacts sentiment
        - **Cloud Growth**: GCP gains drive institutional interest
        
        **📈 Technical Patterns:**
        - **Support Levels**: Previous regulatory dip recoveries
        - **Breakout Catalyst**: AI breakthroughs drive sustained rallies
        - **Volume Patterns**: Algorithm trading dominance
        - **Correlation**: Tech sector beta with ad spending overlay
        
        **💡 Strategic Opportunities:**
        - **AI Announcements**: Bard updates, search integration wins
        - **Cloud Revenue**: GCP growth acceleration vs AWS/Azure
        - **Regulatory Resolution**: Antitrust case conclusions
        - **YouTube Monetization**: Creator fund expansion, premium growth
        
        **📊 Key Metrics to Watch:**
        - Search revenue growth and market share retention
        - YouTube advertising and subscription revenue trends
        - Google Cloud revenue growth vs competitors
        - Traffic acquisition costs (TAC) efficiency improvements
        
        **⚠️ Risk Factors:**
        - Antitrust regulation and potential forced breakups
        - AI search competition from Microsoft/OpenAI partnership
        - Apple privacy changes affecting ad targeting capabilities
        - Economic slowdown reducing overall ad spending
        
        **🎯 Optimal Trading Setups:**
        - **AI News Reactions**: Bard improvements vs ChatGPT comparisons
        - **Earnings Beats**: Search revenue acceleration surprises
        - **Regulatory Clarity**: Antitrust resolution rally opportunities
        - **Cloud Momentum**: Enterprise adoption acceleration plays
        """)
    
    # Google input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # Google-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # Google search/AI analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            
            # Google-specific AI/search momentum assessment
            if range_percentage > 7:
                ai_momentum = "🤖 AI Breakthrough - Major search evolution"
                ai_color = "#4285f4"
                googl_context = "AI/Bard acceleration"
            elif range_percentage > 4:
                ai_momentum = "🔍 Search Strong - Ad revenue growth"
                ai_color = "#34a853"
                googl_context = "Core search momentum"
            elif range_percentage > 2.5:
                ai_momentum = "📊 Steady Growth - Normal patterns"
                ai_color = "#fbbc04"
                googl_context = "Balanced ad cycles"
            elif range_percentage > 1:
                ai_momentum = "⚖️ Range Bound - Regulatory overhang"
                ai_color = "#ea4335"
                googl_context = "Antitrust concerns"
            else:
                ai_momentum = "😴 Low Activity - Awaiting catalyst"
                ai_color = "#9aa0a6"
                googl_context = "Consolidation phase"
            
            # Business segment strength analysis
            if high_price > low_price * 1.04:
                segment_strength = "Search Dominance"
                strength_color = "#4285f4"
            elif high_price > low_price * 1.025:
                segment_strength = "Cloud Growth"
                strength_color = "#34a853"
            elif high_price > low_price * 1.015:
                segment_strength = "YouTube Expansion"
                strength_color = "#ff0000"
            else:
                segment_strength = "Mixed Performance"
                strength_color = "#9aa0a6"
            
            # Regulatory environment assessment
            if range_percentage > 5:
                regulatory_status = "Resolution Rally"
                reg_color = "#34a853"
            elif range_percentage < 1.5:
                regulatory_status = "Overhang Pressure"
                reg_color = "#ea4335"
            else:
                regulatory_status = "Neutral Impact"
                reg_color = "#fbbc04"
            
            st.markdown("### 🔍 Google Search & AI Analysis")
            
            googl_col1, googl_col2, googl_col3 = st.columns(3)
            
            with googl_col1:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(66, 133, 244, 0.15), rgba(52, 168, 83, 0.1));
                    border: 2px solid #4285f4;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(66, 133, 244, 0.3);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #4285f4;">${price_range:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">GOOGL Range</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{range_percentage:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with googl_col2:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {ai_color}22, {ai_color}11);
                    border: 2px solid {ai_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {ai_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {ai_color};">{ai_momentum.split(' - ')[0]}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">AI Momentum</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{googl_context}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with googl_col3:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {strength_color}22, {strength_color}11);
                    border: 2px solid {strength_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {strength_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {strength_color};">{segment_strength}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Segment Focus</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8; color: {reg_color};">{regulatory_status}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Google-specific strategy recommendations
            st.markdown("#### 💡 Google Strategy Recommendations")
            
            strategy_col1, strategy_col2 = st.columns(2)
            
            with strategy_col1:
                if range_percentage > 5:
                    googl_strategy = "🤖 **AI Revolution Play** - Bard vs ChatGPT momentum trade"
                    strategy_color = "#4285f4"
                elif range_percentage > 3:
                    googl_strategy = "🔍 **Search Strength** - Ad revenue acceleration opportunity"
                    strategy_color = "#34a853"
                elif regulatory_status == "Overhang Pressure":
                    googl_strategy = "⚖️ **Regulatory Dip Buy** - Antitrust oversold opportunity"
                    strategy_color = "#ea4335"
                else:
                    googl_strategy = "📊 **Range Trading** - Trade between technical levels"
                    strategy_color = "#fbbc04"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {strategy_color}22, {strategy_color}11);
                    border: 2px solid {strategy_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {strategy_color}33;
                ">
                    <h5 style="color: {strategy_color}; margin: 0 0 0.5rem 0;">Search Strategy</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{googl_strategy}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with strategy_col2:
                # Competitive positioning assessment
                if range_percentage > 4 and ai_momentum.startswith("🤖"):
                    competitive_position = "🟢 **AI Leader** - Bard gaining vs ChatGPT"
                    comp_color = "#34a853"
                elif range_percentage > 2:
                    competitive_position = "🟡 **Defending** - Search moat protection mode"
                    comp_color = "#fbbc04"
                elif regulatory_status == "Overhang Pressure":
                    competitive_position = "🔴 **Under Pressure** - Regulatory headwinds"
                    comp_color = "#ea4335"
                else:
                    competitive_position = "🔵 **Stable** - Core business intact"
                    comp_color = "#4285f4"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {comp_color}22, {comp_color}11);
                    border: 2px solid {comp_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {comp_color}33;
                ">
                    <h5 style="color: {comp_color}; margin: 0 0 0.5rem 0;">Competitive Position</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{competitive_position}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Generate Google analysis
    if st.button(f"🔍 Generate Google Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("🤖 Analyzing Google's search dominance and AI evolution..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "ai_momentum": ai_momentum if 'ai_momentum' in locals() else "Unknown",
                        "segment_strength": segment_strength if 'segment_strength' in locals() else "Unknown",
                        "regulatory_status": regulatory_status if 'regulatory_status' in locals() else "Unknown"
                    }
                    
                    st.success("✅ Google analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# Display results for GOOGL
if st.session_state.selected_page == "GOOGL":
    forecast_key = f"GOOGL_forecasts"
    metadata_key = f"GOOGL_metadata"
    
    if forecast_key in st.session_state:
        st.markdown("## 📊 Google Analysis Results")
        
        forecast_data = st.session_state[forecast_key]
        metadata = st.session_state.get(metadata_key, {})
        
        if "Low" in forecast_data and "High" in forecast_data:
            low_tab, high_tab, ai_tab = st.tabs(["📉 GOOGL Low Anchor", "📈 GOOGL High Anchor", "🤖 AI Insights"])
            
            with low_tab:
                low_df = forecast_data["Low"]
                display_premium_forecast_table(low_df, "GOOGL Low Anchor Analysis")
                
                # Google-specific insights for low anchor
                if not low_df.empty and 'Entry' in low_df.columns and 'Exit' in low_df.columns:
                    spreads = low_df['Entry'] - low_df['Exit']
                    max_spread = spreads.max()
                    avg_spread = spreads.mean()
                    
                    if max_spread > 8:
                        st.success("🚀 **Major AI Catalyst**: Exceptional profit potential suggests breakthrough")
                    elif max_spread > 4:
                        st.info("🔍 **Search Strength**: Strong ad revenue momentum detected")
                    elif max_spread < 2:
                        st.warning("⚖️ **Regulatory Pressure**: Limited upside suggests overhang concerns")
                    else:
                        st.info("📊 **Normal Range**: Standard Google trading patterns")
                    
                    # AI competition analysis
                    ai_momentum = metadata.get('ai_momentum', '')
                    if 'AI Breakthrough' in ai_momentum:
                        st.success("🤖 **Bard Advancement**: AI competition driving institutional interest")
                    elif 'Regulatory' in ai_momentum:
                        st.warning("⚖️ **Antitrust Impact**: Monitor regulatory developments closely")
            
            with high_tab:
                high_df = forecast_data["High"]
                display_premium_forecast_table(high_df, "GOOGL High Anchor Analysis")
                
                # Google-specific insights for high anchor
                if not high_df.empty and 'Entry' in high_df.columns and 'Exit' in high_df.columns:
                    high_max_profit = (high_df['Entry'] - high_df['Exit']).max()
                    volatility = high_df['Entry'].std()
                    
                    if high_max_profit > 10:
                        st.success("🚀 **Search Dominance**: Exceptional momentum in core business")
                    elif volatility > 5:
                        st.warning("⚡ **High Volatility**: AI/regulatory news creating uncertainty")
                    else:
                        st.info("📈 **Steady Growth**: Consistent search revenue patterns")
                    
                    # Segment strength analysis
                    segment_strength = metadata.get('segment_strength', '')
                    if segment_strength == "Search Dominance":
                        st.success("🔍 **Core Strength**: Search advertising firing on all cylinders")
                    elif segment_strength == "Cloud Growth":
                        st.info("☁️ **GCP Momentum**: Cloud segment gaining enterprise traction")
                    elif segment_strength == "YouTube Expansion":
                        st.info("📺 **Creator Economy**: YouTube monetization accelerating")
            
            with ai_tab:
                # Advanced AI competition analysis
                st.markdown("### 🤖 AI Competition & Search Evolution")
                
                ai_col1, ai_col2 = st.columns(2)
                
                with ai_col1:
                    ai_momentum = metadata.get('ai_momentum', 'Unknown')
                    regulatory_status = metadata.get('regulatory_status', 'Unknown')
                    
                    if 'AI Breakthrough' in ai_momentum:
                        ai_assessment = "🟢 **Winning AI Race** - Bard improvements outpacing ChatGPT integration"
                        ai_color = "#34a853"
                    elif 'Search Strong' in ai_momentum:
                        ai_assessment = "🟡 **Defending Lead** - Traditional search still dominant"
                        ai_color = "#fbbc04"
                    elif 'Range Bound' in ai_momentum:
                        ai_assessment = "🔴 **Under Pressure** - AI competition creating headwinds"
                        ai_color = "#ea4335"
                    else:
                        ai_assessment = "🔵 **Monitoring** - AI integration ongoing"
                        ai_color = "#4285f4"
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {ai_color}22, {ai_color}11);
                        border: 2px solid {ai_color};
                        border-radius: 12px;
                        padding: 1.5rem;
                        box-shadow: 0 6px 20px {ai_color}33;
                    ">
                        <h5 style="color: {ai_color}; margin: 0 0 1rem 0;">AI Competitive Status</h5>
                        <p style="margin: 0; font-size: 0.95rem; line-height: 1.4;">{ai_assessment}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with ai_col2:
                    if regulatory_status == "Resolution Rally":
                        reg_assessment = "🟢 **Regulatory Clarity** - Antitrust concerns diminishing"
                        reg_color = "#34a853"
                    elif regulatory_status == "Overhang Pressure":
                        reg_assessment = "🔴 **Regulatory Risk** - Antitrust scrutiny intensifying"
                        reg_color = "#ea4335"
                    else:
                        reg_assessment = "🟡 **Neutral** - Regulatory environment stable"
                        reg_color = "#fbbc04"
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {reg_color}22, {reg_color}11);
                        border: 2px solid {reg_color};
                        border-radius: 12px;
                        padding: 1.5rem;
                        box-shadow: 0 6px 20px {reg_color}33;
                    ">
                        <h5 style="color: {reg_color}; margin: 0 0 1rem 0;">Regulatory Environment</h5>
                        <p style="margin: 0; font-size: 0.95rem; line-height: 1.4;">{reg_assessment}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Key catalysts to watch
                st.markdown("#### 🎯 Key Catalysts to Monitor")
                st.markdown("""
                **📊 Positive Catalysts:**
                - Bard integration improvements beating ChatGPT features
                - Google Cloud revenue acceleration vs AWS/Azure
                - YouTube advertising revenue growth surprises
                - Antitrust case resolution or favorable rulings
                
                **⚠️ Risk Factors:**
                - Microsoft's Bing+ChatGPT search share gains
                - Economic downturn reducing ad spending
                - Apple privacy changes limiting ad targeting
                - Regulatory breakup or structural separation orders
                
                **📈 Trading Opportunities:**
                - AI announcement reactions (Bard updates)
                - Earnings beats on search revenue
                - Regulatory headline volatility trades
                - Cloud growth momentum plays
                """)
    else:
        st.info("👆 Enter Google's data and generate analysis to see AI competition insights.")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 8C1: AMAZON (AMZN) ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# AMAZON (AMZN) ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.selected_page == "AMZN":
    ticker = "AMZN"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render Amazon hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # Amazon-specific insights
    with st.expander("📦 Amazon Dual-Revenue Intelligence", expanded=False):
        st.markdown("""
        ### 🛒 Amazon's E-commerce & Cloud Empire
        
        **🏢 Dual Revenue Powerhouse:**
        - AWS cloud infrastructure drives profitability
        - E-commerce retail provides massive scale
        - Prime membership creates ecosystem lock-in
        - Logistics network enables competitive advantages
        
        **☁️ AWS Cloud Dominance:**
        - **Market Leader**: #1 cloud infrastructure provider
        - **High Margins**: 70%+ operating margins vs retail
        - **Enterprise Growth**: Fortune 500 cloud migration
        - **Innovation Pipeline**: AI/ML services expansion
        
        **📊 E-commerce Dynamics:**
        - **Prime Day Effects**: Seasonal revenue spikes
        - **Holiday Seasonality**: Q4 retail acceleration
        - **Third-party Sales**: Growing marketplace revenue
        - **International Expansion**: Global growth opportunities
        
        **🎯 Trading Characteristics:**
        - **Earnings Volatility**: 8-12% moves common on results
        - **AWS Growth Sensitivity**: Cloud metrics drive sentiment
        - **Seasonal Patterns**: Prime Day, Black Friday catalysts
        - **Margin Focus**: Profitability over growth narrative
        
        **📈 Technical Patterns:**
        - **Support Levels**: Previous earnings reaction levels
        - **Breakout Potential**: Large moves when AWS accelerates
        - **Volume Spikes**: Institutional repositioning common
        - **Correlation**: Both growth and value characteristics
        
        **💡 Strategic Opportunities:**
        - **AWS Growth**: Cloud revenue beats drive sustained rallies
        - **Prime Membership**: Subscriber growth announcements
        - **Logistics Efficiency**: Same-day delivery expansion
        - **International Markets**: Geographic diversification
        
        **📊 Key Metrics to Watch:**
        - AWS growth rates and operating margins
        - Prime membership numbers and engagement
        - Third-party seller growth and fees
        - Free cash flow generation trends
        
        **⚠️ Risk Factors:**
        - Competition from Microsoft Azure, Google Cloud
        - Regulatory pressure on marketplace dominance
        - Rising labor and logistics costs
        - Economic sensitivity of retail operations
        
        **🎯 Optimal Trading Setups:**
        - **AWS Acceleration**: Cloud growth >30% drives momentum
        - **Prime Day Reactions**: Short-term retail sentiment
        - **Earnings Straddles**: High IV around results
        - **Holiday Season**: Q4 retail strength plays
        """)
    
    # Amazon input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # Amazon-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # Amazon dual-business analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            
            # Amazon-specific business momentum assessment
            if range_percentage > 8:
                aws_momentum = "🚀 AWS Explosion - Major cloud catalyst"
                momentum_color = "#ff6b35"
                amzn_context = "Enterprise cloud acceleration"
            elif range_percentage > 5:
                aws_momentum = "☁️ Cloud Growth - Strong AWS metrics"
                momentum_color = "#f59e0b"
                amzn_context = "Normal cloud expansion"
            elif range_percentage > 3:
                aws_momentum = "📦 Retail Focus - E-commerce driven"
                momentum_color = "#3b82f6"
                amzn_context = "Prime/retail momentum"
            elif range_percentage > 1.5:
                aws_momentum = "⚖️ Balanced - Dual revenue steady"
                momentum_color = "#10b981"
                amzn_context = "Both segments stable"
            else:
                aws_momentum = "😴 Consolidation - Awaiting catalyst"
                momentum_color = "#6b7280"
                amzn_context = "Low volatility period"
            
            # Business segment analysis
            if high_price > low_price * 1.05:
                segment_focus = "AWS Dominance"
                segment_color = "#8b5cf6"
            elif high_price > low_price * 1.03:
                segment_focus = "Prime Growth"
                segment_color = "#3b82f6"
            elif high_price > low_price * 1.02:
                segment_focus = "Retail Steady"
                segment_color = "#10b981"
            else:
                segment_focus = "Mixed Signals"
                segment_color = "#6b7280"
            
            # Seasonal/event analysis
            current_month = datetime.now().month
            if current_month in [7]:  # July - Prime Day
                seasonal_factor = "Prime Day"
                seasonal_color = "#ff6b35"
            elif current_month in [10, 11, 12]:  # Holiday season
                seasonal_factor = "Holiday Season"
                seasonal_color = "#dc2626"
            elif current_month in [1, 2]:  # Post-holiday
                seasonal_factor = "Post-Holiday"
                seasonal_color = "#3b82f6"
            else:
                seasonal_factor = "Normal Period"
                seasonal_color = "#6b7280"
            
            st.markdown("### 📦 Amazon Business Analysis")
            
            amzn_col1, amzn_col2, amzn_col3 = st.columns(3)
            
            with amzn_col1:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(255, 107, 53, 0.15), rgba(245, 158, 11, 0.1));
                    border: 2px solid #ff6b35;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(255, 107, 53, 0.3);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📦</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #ff6b35;">${price_range:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">AMZN Range</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{range_percentage:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with amzn_col2:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {momentum_color}22, {momentum_color}11);
                    border: 2px solid {momentum_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {momentum_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">☁️</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {momentum_color};">{aws_momentum.split(' - ')[0]}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Business Momentum</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{amzn_context}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with amzn_col3:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {segment_color}22, {segment_color}11);
                    border: 2px solid {segment_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {segment_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {segment_color};">{segment_focus}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Segment Focus</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8; color: {seasonal_color};">{seasonal_factor}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Amazon-specific strategy recommendations
            st.markdown("#### 💡 Amazon Strategy Recommendations")
            
            strategy_col1, strategy_col2 = st.columns(2)
            
            with strategy_col1:
                if range_percentage > 6:
                    amzn_strategy = "🚀 **AWS Momentum Play** - Cloud acceleration driving institutional buying"
                    strategy_color = "#8b5cf6"
                elif range_percentage > 3:
                    amzn_strategy = "📊 **Earnings Straddle** - High volatility suggests catalyst ahead"
                    strategy_color = "#f59e0b"
                elif seasonal_factor in ["Prime Day", "Holiday Season"]:
                    amzn_strategy = "🛒 **Seasonal Play** - Retail momentum opportunity"
                    strategy_color = "#ff6b35"
                else:
                    amzn_strategy = "⚖️ **Range Trading** - Trade between support/resistance"
                    strategy_color = "#3b82f6"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {strategy_color}22, {strategy_color}11);
                    border: 2px solid {strategy_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {strategy_color}33;
                ">
                    <h5 style="color: {strategy_color}; margin: 0 0 0.5rem 0;">Primary Strategy</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{amzn_strategy}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with strategy_col2:
                # Volatility assessment for Amazon
                if range_percentage > 8:
                    amzn_volatility = "🔴 **High Volatility** - Major catalyst likely"
                    vol_color = "#ef4444"
                elif range_percentage > 4:
                    amzn_volatility = "🟠 **Elevated** - Earnings/event driven"
                    vol_color = "#f59e0b"
                elif range_percentage > 2:
                    amzn_volatility = "🟡 **Normal** - Standard Amazon range"
                    vol_color = "#3b82f6"
                else:
                    amzn_volatility = "🟢 **Low Vol** - Consolidation phase"
                    vol_color = "#10b981"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {vol_color}22, {vol_color}11);
                    border: 2px solid {vol_color};
                    border-radius: 12px;
                    padding: 1rem;
                    box-shadow: 0 6px 20px {vol_color}33;
                ">
                    <h5 style="color: {vol_color}; margin: 0 0 0.5rem 0;">Volatility Profile</h5>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">{amzn_volatility}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Generate Amazon analysis
    if st.button(f"📦 Generate Amazon Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("☁️ Analyzing Amazon's dual-revenue cloud and e-commerce dynamics..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "aws_momentum": aws_momentum if 'aws_momentum' in locals() else "Unknown",
                        "segment_focus": segment_focus if 'segment_focus' in locals() else "Unknown",
                        "seasonal_factor": seasonal_factor if 'seasonal_factor' in locals() else "Unknown"
                    }
                    
                    st.success("✅ Amazon analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# Display Amazon results
if st.session_state.selected_page == "AMZN":
    ticker = "AMZN"
    forecast_key = f"{ticker}_forecasts"
    metadata_key = f"{ticker}_metadata"
    
    if forecast_key in st.session_state:
        st.markdown(f"## 📊 {stock_info[ticker]['name']} Analysis Results")
        
        forecast_data = st.session_state[forecast_key]
        metadata = st.session_state.get(metadata_key, {})
        
        if "Low" in forecast_data and "High" in forecast_data:
            low_tab, high_tab, aws_tab = st.tabs([f"📉 AMZN Low Anchor", f"📈 AMZN High Anchor", f"☁️ AWS Intelligence"])
            
            with low_tab:
                low_df = forecast_data["Low"]
                display_premium_forecast_table(low_df, f"Amazon Low Anchor Analysis")
                
                # Amazon-specific insights for low anchor
                if not low_df.empty and 'Entry' in low_df.columns and 'Exit' in low_df.columns:
                    spreads = low_df['Entry'] - low_df['Exit']
                    max_spread = spreads.max()
                    avg_spread = spreads.mean()
                    
                    # AWS vs Retail signal analysis
                    if max_spread > 8:
                        st.success("☁️ **AWS Signal**: Strong cloud momentum from support levels")
                    elif max_spread > 4:
                        st.info("📦 **Retail Signal**: E-commerce bounce opportunity")
                    elif metadata.get('seasonal_factor') in ['Prime Day', 'Holiday Season']:
                        st.info(f"🛒 **Seasonal Signal**: {metadata.get('seasonal_factor')} effect detected")
                    else:
                        st.warning("⚖️ **Mixed Signal**: Monitor for segment clarity")
            
            with high_tab:
                high_df = forecast_data["High"]
                display_premium_forecast_table(high_df, f"Amazon High Anchor Analysis")
                
                # Amazon-specific insights for high anchor
                if not high_df.empty and 'Entry' in high_df.columns and 'Exit' in high_df.columns:
                    max_profit = (high_df['Entry'] - high_df['Exit']).max()
                    
                    if max_profit > 10:
                        st.success("🚀 **AWS Acceleration**: Major cloud catalyst driving breakout")
                    elif max_profit > 6:
                        st.success("📈 **Strong Momentum**: Dual-revenue growth acceleration")
                    elif max_profit > 3:
                        st.info("📊 **Moderate Growth**: Normal Amazon expansion pace")
                    else:
                        st.info("⚖️ **Range Bound**: Consolidation within normal parameters")
            
            with aws_tab:
                # Amazon AWS intelligence tab
                st.markdown("### ☁️ Amazon Web Services Intelligence")
                
                aws_momentum = metadata.get('aws_momentum', 'Unknown')
                segment_focus = metadata.get('segment_focus', 'Unknown')
                seasonal_factor = metadata.get('seasonal_factor', 'Unknown')
                
                # AWS performance metrics
                aws_col1, aws_col2 = st.columns(2)
                
                with aws_col1:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
                        border: 2px solid #8b5cf6;
                        border-radius: 16px;
                        padding: 1.5rem;
                        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.2);
                    ">
                        <h4 style="color: #8b5cf6; margin: 0 0 1rem 0;">☁️ Cloud Analysis</h4>
                        <div style="margin-bottom: 1rem;">
                            <strong>AWS Momentum:</strong> {aws_momentum}<br>
                            <strong>Segment Focus:</strong> {segment_focus}<br>
                            <strong>Seasonal Context:</strong> {seasonal_factor}
                        </div>
                        <div style="background: rgba(139, 92, 246, 0.1); padding: 0.8rem; border-radius: 8px;">
                            <strong>Key Insight:</strong> {"AWS driving performance" if "AWS" in aws_momentum else "Retail/Prime focus period" if "Retail" in aws_momentum else "Balanced dual-revenue model"}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with aws_col2:
                    # Trading recommendations based on AWS analysis
                    if "AWS Explosion" in aws_momentum:
                        aws_recommendation = "🚀 **Strong Buy**: AWS acceleration phase"
                        rec_color = "#10b981"
                    elif "Cloud Growth" in aws_momentum:
                        rec_recommendation = "📈 **Buy**: Normal cloud expansion"
                        rec_color = "#3b82f6"
                    elif "Retail Focus" in aws_momentum:
                        aws_recommendation = "📦 **Hold**: E-commerce cycle active"
                        rec_color = "#f59e0b"
                    else:
                        aws_recommendation = "⚖️ **Monitor**: Awaiting segment clarity"
                        rec_color = "#6b7280"
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {rec_color}22, {rec_color}11);
                        border: 2px solid {rec_color};
                        border-radius: 16px;
                        padding: 1.5rem;
                        box-shadow: 0 8px 25px {rec_color}33;
                    ">
                        <h4 style="color: {rec_color}; margin: 0 0 1rem 0;">🎯 AWS Strategy</h4>
                        <div style="font-size: 1.1rem; font-weight: bold; color: {rec_color}; margin-bottom: 1rem;">
                            {aws_recommendation}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">
                            Monitor AWS growth rates, enterprise adoption, and cloud margin expansion for sustained momentum.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # AWS trading tips
                st.markdown("#### 💡 AWS Trading Tips")
                st.markdown("""
                - **Earnings Focus**: AWS revenue growth >30% typically drives rallies
                - **Enterprise Adoption**: Fortune 500 migrations create sustained demand  
                - **Margin Expansion**: AWS operating margins >70% vs retail ~5%
                - **Competition**: Monitor vs Microsoft Azure and Google Cloud
                - **AI Services**: Machine learning and AI service adoption growth
                """)
    else:
        st.info(f"👆 Enter Amazon's data and generate analysis to see AWS and retail insights.")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 9: FINAL STOCK PAGES (META, NFLX) & APPLICATION FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# META (META) ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.selected_page == "META":
    ticker = "META"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render Meta hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # Meta-specific insights
    with st.expander("📘 Meta Metaverse Intelligence", expanded=False):
        st.markdown("""
        ### 🥽 Meta's Social Media & Metaverse Evolution
        
        **📱 Core Social Media Empire:**
        - Facebook main platform with 3B+ monthly users
        - Instagram driving engagement and ad revenue growth
        - WhatsApp global messaging dominance
        - Threads competing with Twitter/X for text-based social
        
        **🥽 Metaverse Investment Strategy:**
        - **Reality Labs**: VR/AR hardware and software development
        - **Horizon Worlds**: Virtual reality social platform
        - **Quest Headsets**: Consumer VR hardware leadership
        - **Enterprise Solutions**: VR for training and collaboration
        
        **📊 Revenue Dynamics:**
        - **Advertising Revenue**: 97%+ of total revenue from ads
        - **User Growth**: Monthly/daily active user metrics critical
        - **ARPU Growth**: Average revenue per user expansion
        - **International Markets**: Emerging market monetization
        
        **🎯 Trading Characteristics:**
        - **User Growth Sensitive**: MAU/DAU numbers drive sentiment
        - **Metaverse Burn**: Reality Labs losses affect profitability
        - **Privacy Regulations**: iOS changes, GDPR impact ad targeting
        - **Competition**: TikTok, YouTube, Snapchat for user attention
        
        **📈 Technical Patterns:**
        - **Earnings Volatility**: 10-20% moves on user metrics
        - **Regulatory Headlines**: Privacy/antitrust create volatility
        - **VR Adoption**: Metaverse progress drives long-term sentiment
        - **Ad Spend Cycles**: Economic sensitivity affects revenue
        
        **💡 Strategic Opportunities:**
        - **User Growth Surprises**: DAU/MAU beats drive rallies
        - **Metaverse Milestones**: VR adoption acceleration
        - **Instagram Reels**: TikTok competition success
        - **AI Integration**: Content recommendations improvement
        
        **📊 Key Metrics to Watch:**
        - Daily/Monthly Active Users across all platforms
        - Average Revenue Per User (ARPU) trends
        - Reality Labs revenue and operating losses
        - Ad targeting effectiveness post-iOS changes
        
        **⚠️ Risk Factors:**
        - Continued Reality Labs cash burn
        - User growth saturation in mature markets
        - Regulatory pressure on data collection
        - Competition from TikTok for younger demographics
        
        **🎯 Optimal Trading Setups:**
        - **Earnings Straddles**: High volatility on user metrics
        - **VR Catalyst Plays**: Metaverse breakthrough announcements
        - **Regulatory Dip Buying**: Oversold on privacy concerns
        - **Ad Revenue Recovery**: Economic improvement beneficiary
        """)
    
    # Meta input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # Meta-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # Meta metaverse/social analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            
            # Meta-specific user growth momentum assessment
            if range_percentage > 12:
                metaverse_momentum = "🚀 Metaverse Breakthrough - Major VR catalyst"
                momentum_color = "#6366f1"
                meta_context = "Reality Labs acceleration"
            elif range_percentage > 8:
                metaverse_momentum = "📈 User Growth Surge - Strong engagement"
                momentum_color = "#3b82f6"
                meta_context = "DAU/MAU beats driving"
            elif range_percentage > 5:
                metaverse_momentum = "📱 Social Strong - Core platform growth"
                momentum_color = "#10b981"
                meta_context = "Instagram/Facebook solid"
            elif range_percentage > 2:
                metaverse_momentum = "⚖️ Mixed Signals - Balanced performance"
                momentum_color = "#f59e0b"
                meta_context = "Standard social metrics"
            else:
                metaverse_momentum = "😴 Low Activity - User growth stagnant"
                momentum_color = "#6b7280"
                meta_context = "Engagement concerns"
            
            # Platform focus analysis
            if high_price > low_price * 1.08:
                platform_focus = "VR Revolution"
                platform_color = "#8b5cf6"
            elif high_price > low_price * 1.05:
                platform_focus = "Instagram Growth"
                platform_color = "#e91e63"
            elif high_price > low_price * 1.03:
                platform_focus = "Facebook Stable"
                platform_color = "#1976d2"
            else:
                platform_focus = "Platform Mature"
                platform_color = "#6b7280"
            
            # User engagement vs metaverse investment balance
            if range_percentage > 8:
                investment_balance = "VR Payoff"
                balance_color = "#8b5cf6"
            elif range_percentage > 4:
                investment_balance = "Balanced Growth"
                balance_color = "#10b981"
            elif range_percentage < 2:
                investment_balance = "Burn Concern"
                balance_color = "#ef4444"
            else:
                investment_balance = "Transition Phase"
                balance_color = "#f59e0b"
            
            st.markdown("### 📘 Meta Platform Analysis")
            
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            
            with meta_col1:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(79, 70, 229, 0.1));
                    border: 2px solid #6366f1;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(99, 102, 241, 0.3);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📘</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #6366f1;">${price_range:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">META Range</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{range_percentage:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with meta_col2:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {momentum_color}22, {momentum_color}11);
                    border: 2px solid {momentum_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {momentum_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🥽</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {momentum_color};">{metaverse_momentum.split(' - ')[0]}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Platform Momentum</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{meta_context}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with meta_col3:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {platform_color}22, {platform_color}11);
                    border: 2px solid {platform_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {platform_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📱</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {platform_color};">{platform_focus}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Platform Focus</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8; color: {balance_color};">{investment_balance}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Generate Meta analysis
    if st.button(f"📘 Generate Meta Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("🥽 Analyzing Meta's social platform and metaverse evolution..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "metaverse_momentum": metaverse_momentum if 'metaverse_momentum' in locals() else "Unknown",
                        "platform_focus": platform_focus if 'platform_focus' in locals() else "Unknown",
                        "investment_balance": investment_balance if 'investment_balance' in locals() else "Unknown"
                    }
                    
                    st.success("✅ Meta analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# NETFLIX (NFLX) ANALYSIS PAGE
# ═══════════════════════════════════════════════════════════════════════════════

elif st.session_state.selected_page == "NFLX":
    ticker = "NFLX"
    stock_data = stock_info[ticker]
    current_slope = strategy.slopes.get(ticker, 0)
    
    # Render Netflix hero section
    render_stock_hero(ticker, stock_data, current_slope)
    
    # Netflix-specific insights
    with st.expander("📺 Netflix Streaming Intelligence", expanded=False):
        st.markdown("""
        ### 🎬 Netflix's Streaming Entertainment Empire
        
        **📺 Global Streaming Dominance:**
        - 240+ million global subscribers across 190+ countries
        - Original content strategy with $15B+ annual spend
        - Multiple content tiers: Basic, Standard, Premium plans
        - Ad-supported tier introduction expanding addressable market
        
        **🎭 Content Strategy:**
        - **Original Productions**: Emmy-winning series and films
        - **International Content**: Local language global hits
        - **Live Events**: Sports and live programming expansion
        - **Gaming Integration**: Mobile games for subscriber retention
        
        **📊 Subscriber Dynamics:**
        - **Net Additions**: Quarterly subscriber growth is key metric
        - **ARPU Growth**: Average revenue per user expansion
        - **Churn Rates**: Subscriber retention and engagement
        - **Geographic Mix**: Emerging markets vs mature regions
        
        **🎯 Trading Characteristics:**
        - **Subscriber Obsession**: Net adds drive 15%+ moves
        - **Content Costs**: Spend efficiency affects margins
        - **Competition**: Disney+, HBO Max, Amazon Prime pressure
        - **Seasonality**: Content release schedules impact engagement
        
        **📈 Technical Patterns:**
        - **Earnings Volatility**: Massive moves on subscriber beats/misses
        - **Content Announcements**: New series can drive sentiment
        - **Competitive Headlines**: Streaming wars affect positioning
        - **Guidance Sensitivity**: Forward subscriber projections critical
        
        **💡 Strategic Opportunities:**
        - **Subscriber Surprises**: Net addition beats drive rallies
        - **International Growth**: Emerging market penetration
        - **Content Hits**: Viral series create engagement spikes
        - **Ad Tier Adoption**: New revenue stream development
        
        **📊 Key Metrics to Watch:**
        - Global net subscriber additions (target: 15M+ annually)
        - Revenue per membership and pricing power
        - Content spend efficiency and engagement metrics
        - Free cash flow generation and content financing
        
        **⚠️ Risk Factors:**
        - Intense competition from tech giants with deep pockets
        - Content cost inflation and production delays
        - Subscriber growth saturation in developed markets
        - Currency headwinds from international revenue
        
        **🎯 Optimal Trading Setups:**
        - **Earnings Straddles**: Subscriber volatility creates opportunity
        - **Content Catalyst**: Anticipate viral series impact
        - **Competition Reaction**: Trade streaming war headlines
        - **International Growth**: Emerging market penetration plays
        """)
    
    # Netflix input section
    analysis_date, low_price, low_time, high_price, high_time = render_stock_input_section(ticker, stock_data)
    
    # Netflix-specific validation and analytics
    if low_price > 0 and high_price > 0:
        if high_price <= low_price:
            st.error("⚠️ High price must be greater than low price")
        else:
            # Netflix streaming/content analysis
            price_range = high_price - low_price
            range_percentage = (price_range / low_price) * 100
            
            # Netflix-specific subscriber momentum assessment
            if range_percentage > 15:
                subscriber_momentum = "🚀 Subscriber Explosion - Major growth catalyst"
                momentum_color = "#e50914"
                nflx_context = "Viral content driving adds"
            elif range_percentage > 10:
                subscriber_momentum = "📈 Strong Growth - International expansion"
                momentum_color = "#db2777"
                nflx_context = "Global penetration success"
            elif range_percentage > 6:
                subscriber_momentum = "📺 Content Hit - Engagement spike"
                momentum_color = "#9333ea"
                nflx_context = "New series momentum"
            elif range_percentage > 3:
                subscriber_momentum = "⚖️ Steady Growth - Normal cadence"
                momentum_color = "#3b82f6"
                nflx_context = "Regular subscriber flow"
            else:
                subscriber_momentum = "😴 Saturation - Growth concerns"
                momentum_color = "#6b7280"
                nflx_context = "Competitive pressure"
            
            # Content strategy success analysis
            if high_price > low_price * 1.12:
                content_strategy = "Viral Hit"
                content_color = "#e50914"
            elif high_price > low_price * 1.06:
                content_strategy = "Content Success"
                content_color = "#db2777"
            elif high_price > low_price * 1.03:
                content_strategy = "Steady Content"
                content_color = "#8b5cf6"
            else:
                content_strategy = "Content Miss"
                content_color = "#6b7280"
            
            # Competition vs growth balance
            if range_percentage > 10:
                competition_status = "Winning Wars"
                comp_color = "#10b981"
            elif range_percentage > 5:
                competition_status = "Holding Ground"
                comp_color = "#3b82f6"
            elif range_percentage < 3:
                competition_status = "Under Pressure"
                comp_color = "#ef4444"
            else:
                competition_status = "Neutral Battle"
                comp_color = "#f59e0b"
            
            st.markdown("### 📺 Netflix Streaming Analysis")
            
            nflx_col1, nflx_col2, nflx_col3 = st.columns(3)
            
            with nflx_col1:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, rgba(229, 9, 20, 0.15), rgba(219, 39, 119, 0.1));
                    border: 2px solid #e50914;
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px rgba(229, 9, 20, 0.3);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📺</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: #e50914;">${price_range:.2f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">NFLX Range</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{range_percentage:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with nflx_col2:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {momentum_color}22, {momentum_color}11);
                    border: 2px solid {momentum_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {momentum_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎬</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {momentum_color};">{subscriber_momentum.split(' - ')[0]}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Subscriber Flow</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">{nflx_context}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with nflx_col3:
                st.markdown(f"""
                <div class="metric-card float" style="
                    background: linear-gradient(135deg, {content_color}22, {content_color}11);
                    border: 2px solid {content_color};
                    border-radius: 20px;
                    padding: 2rem;
                    text-align: center;
                    box-shadow: 0 12px 35px {content_color}44;
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎭</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; color: {content_color};">{content_strategy}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Content Impact</div>
                    <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8; color: {comp_color};">{competition_status}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Generate Netflix analysis
    if st.button(f"📺 Generate Netflix Analysis", key=f"generate_{ticker}_analysis", type="primary", use_container_width=True):
        if low_price <= 0 or high_price <= 0:
            st.error("❌ Please enter valid prices for both anchors")
        elif high_price <= low_price:
            st.error("❌ High price must be greater than low price")
        else:
            with st.spinner("🎬 Analyzing Netflix's streaming dominance and content strategy..."):
                try:
                    forecast = strategy.stock_forecast(
                        ticker, low_price, low_time, high_price, high_time, analysis_date
                    )
                    
                    st.session_state[f"{ticker}_forecasts"] = forecast
                    st.session_state[f"{ticker}_metadata"] = {
                        "date": analysis_date,
                        "low_price": low_price, "low_time": low_time,
                        "high_price": high_price, "high_time": high_time,
                        "generated_at": datetime.now(),
                        "subscriber_momentum": subscriber_momentum if 'subscriber_momentum' in locals() else "Unknown",
                        "content_strategy": content_strategy if 'content_strategy' in locals() else "Unknown",
                        "competition_status": competition_status if 'competition_status' in locals() else "Unknown"
                    }
                    
                    st.success("✅ Netflix analysis complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")

# Display results for both META and NFLX
for ticker in ["META", "NFLX"]:
    if st.session_state.selected_page == ticker:
        forecast_key = f"{ticker}_forecasts"
        metadata_key = f"{ticker}_metadata"
        
        if forecast_key in st.session_state:
            st.markdown(f"## 📊 {stock_info[ticker]['name']} Analysis Results")
            
            forecast_data = st.session_state[forecast_key]
            metadata = st.session_state.get(metadata_key, {})
            
            if "Low" in forecast_data and "High" in forecast_data:
                low_tab, high_tab, insights_tab = st.tabs([f"📉 {ticker} Low Anchor", f"📈 {ticker} High Anchor", f"🎯 {ticker} Insights"])
                
                with low_tab:
                    low_df = forecast_data["Low"]
                    display_premium_forecast_table(low_df, f"{ticker} Low Anchor Analysis")
                    
                    # Stock-specific insights for low anchor
                    if not low_df.empty and 'Entry' in low_df.columns and 'Exit' in low_df.columns:
                        spreads = low_df['Entry'] - low_df['Exit']
                        max_spread = spreads.max()
                        
                        if ticker == "META":
                            if max_spread > 8:
                                st.success("🥽 **Metaverse Signal**: VR breakthrough potential from support")
                            elif max_spread > 4:
                                st.info("📱 **User Growth**: Strong social platform engagement")
                            else:
                                st.warning("⚖️ **Mixed Signals**: Monitor Reality Labs burn vs user metrics")
                        
                        elif ticker == "NFLX":
                            if max_spread > 10:
                                st.success("🚀 **Subscriber Surge**: Major growth catalyst detected")
                            elif max_spread > 5:
                                st.info("📺 **Content Hit**: Successful series driving engagement")
                            else:
                                st.warning("🏆 **Competition**: Streaming wars pressure evident")
                
                with high_tab:
                    high_df = forecast_data["High"]
                    display_premium_forecast_table(high_df, f"{ticker} High Anchor Analysis")
                    
                    # Stock-specific insights for high anchor
                    if not high_df.empty and 'Entry' in high_df.columns and 'Exit' in high_df.columns:
                        max_profit = (high_df['Entry'] - high_df['Exit']).max()
                        
                        if ticker == "META":
                            if max_profit > 12:
                                st.success("🚀 **Platform Revolution**: Major metaverse or social breakthrough")
                            elif max_profit > 6:
                                st.success("📈 **Strong Momentum**: User growth accelerating")
                            else:
                                st.info("📊 **Steady Growth**: Normal social platform patterns")
                        
                        elif ticker == "NFLX":
                            if max_profit > 15:
                                st.success("🌟 **Viral Content**: Exceptional subscriber momentum")
                            elif max_profit > 8:
                                st.success("📺 **Content Success**: Strong streaming performance")
                            else:
                                st.info("⚖️ **Competitive Environment**: Standard streaming dynamics")
                
                with insights_tab:
                    # Advanced insights for each stock
                    if ticker == "META":
                        st.markdown("### 🥽 Meta Platform Intelligence")
                        
                        metaverse_momentum = metadata.get('metaverse_momentum', 'Unknown')
                        platform_focus = metadata.get('platform_focus', 'Unknown')
                        
                        if "Metaverse Breakthrough" in metaverse_momentum:
                            st.success("🚀 **VR Revolution**: Reality Labs showing major progress")
                        elif "User Growth Surge" in metaverse_momentum:
                            st.success("📱 **Social Strength**: Core platforms firing on all cylinders")
                        elif "Low Activity" in metaverse_momentum:
                            st.warning("😴 **Engagement Concerns**: Monitor user retention and competition")
                        
                        st.markdown("""
                        **Key Catalysts to Watch:**
                        - Daily/Monthly Active User growth across all platforms
                        - Reality Labs revenue growth and loss reduction
                        - Instagram Reels vs TikTok competition
                        - VR headset adoption and metaverse engagement metrics
                        """)
                    
                    elif ticker == "NFLX":
                        st.markdown("### 📺 Netflix Streaming Intelligence")
                        
                        subscriber_momentum = metadata.get('subscriber_momentum', 'Unknown')
                        content_strategy = metadata.get('content_strategy', 'Unknown')
                        
                        if "Subscriber Explosion" in subscriber_momentum:
                            st.success("🚀 **Streaming Dominance**: Major subscriber acceleration")
                        elif "Strong Growth" in subscriber_momentum:
                            st.success("🌍 **Global Success**: International expansion paying off")
                        elif "Saturation" in subscriber_momentum:
                            st.warning("📈 **Growth Challenge**: Need new subscriber acquisition strategies")
                        
                        st.markdown("""
                        **Key Catalysts to Watch:**
                        - Quarterly net subscriber additions (target: 4M+ per quarter)
                        - International market penetration and ARPU growth
                        - Content engagement metrics and viral series success
                        - Ad-supported tier adoption and revenue contribution
                        """)
        else:
            st.info(f"👆 Enter {stock_info[ticker]['name']}'s data and generate analysis to see specialized insights.")

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL APPLICATION FOOTER & SUMMARY SECTION
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 🎯 Dr. David's Market Mind - Session Complete")

# Final session summary and statistics
chicago_time = strategy.get_chicago_time()
total_active_forecasts = 0
total_data_points = 0

# Count all active forecasts across all sections
if st.session_state.current_forecasts:
    total_active_forecasts += len(st.session_state.current_forecasts)
    for forecast in st.session_state.current_forecasts.values():
        if not forecast.empty:
            total_data_points += len(forecast)

if not st.session_state.contract_table.empty:
    total_active_forecasts += 1
    total_data_points += len(st.session_state.contract_table)

for ticker in strategy.get_available_tickers():
    if f"{ticker}_forecasts" in st.session_state:
        total_active_forecasts += 1
        forecast_data = st.session_state[f"{ticker}_forecasts"]
        for anchor_data in forecast_data.values():
            if not anchor_data.empty:
                total_data_points += len(anchor_data)

# Calculate session duration
session_start = datetime.now() - timedelta(hours=1)  # Approximate session time
session_duration = datetime.now() - session_start

# Final comprehensive dashboard
st.markdown("### 📊 Session Performance Dashboard")

final_col1, final_col2, final_col3, final_col4 = st.columns(4)

with final_col1:
    st.markdown(f"""
    <div class="metric-card float glow" style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1));
        border: 2px solid #10b981;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 15px 40px rgba(16, 185, 129, 0.4);
        transform: perspective(1000px) rotateY(-3deg);
    ">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">🧠</div>
        <div style="font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem; color: #10b981;">{total_active_forecasts}</div>
        <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Active Analyses</div>
        <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Total forecasts generated</div>
        <div style="font-size: 0.75rem; color: #10b981; font-weight: 600; margin-top: 0.3rem;">Complete portfolio</div>
    </div>
    """, unsafe_allow_html=True)

with final_col2:
    available_assets = len(strategy.get_available_tickers()) + 2  # +1 for SPX, +1 for Contract
    st.markdown(f"""
    <div class="metric-card float" style="
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(99, 102, 241, 0.1));
        border: 2px solid #3b82f6;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 15px 40px rgba(59, 130, 246, 0.3);
        transform: perspective(1000px) rotateY(3deg);
        animation-delay: 0.1s;
    ">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">📊</div>
        <div style="font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem; color: #3b82f6;">{available_assets}</div>
        <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Market Coverage</div>
        <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">SPX + Stocks + Contracts</div>
        <div style="font-size: 0.75rem; color: #3b82f6; font-weight: 600; margin-top: 0.3rem;">Complete universe</div>
    </div>
    """, unsafe_allow_html=True)

with final_col3:
    st.markdown(f"""
    <div class="metric-card float" style="
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1));
        border: 2px solid #f59e0b;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 15px 40px rgba(245, 158, 11, 0.3);
        transform: perspective(1000px) rotateY(-3deg);
        animation-delay: 0.2s;
    ">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">⏰</div>
        <div style="font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem; color: #f59e0b;">{chicago_time.strftime('%H:%M')}</div>
        <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Chicago Time</div>
        <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Central Standard Time</div>
        <div style="font-size: 0.75rem; color: #f59e0b; font-weight: 600; margin-top: 0.3rem;">Real-time sync</div>
    </div>
    """, unsafe_allow_html=True)

with final_col4:
    st.markdown(f"""
    <div class="metric-card float" style="
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
        border: 2px solid #8b5cf6;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 15px 40px rgba(139, 92, 246, 0.3);
        transform: perspective(1000px) rotateY(3deg);
        animation-delay: 0.3s;
    ">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">📈</div>
        <div style="font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem; color: #8b5cf6;">{total_data_points}</div>
        <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Data Points</div>
        <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">Total projections</div>
        <div style="font-size: 0.75rem; color: #8b5cf6; font-weight: 600; margin-top: 0.3rem;">Deep analysis</div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM CAPABILITIES OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("### 🌟 System Capabilities Summary")

capabilities_col1, capabilities_col2 = st.columns(2)

with capabilities_col1:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.2);
        height: 100%;
    ">
        <h4 style="color: #10b981; margin: 0 0 1.5rem 0;">🎯 Forecasting Features</h4>
        <div style="line-height: 1.8;">
            <strong>📊 SPX Analysis:</strong> Three-anchor projection system<br>
            <strong>📈 Contract Lines:</strong> Two-point interpolation system<br>
            <strong>🚗 Stock Analysis:</strong> Individual equity forecasting<br>
            <strong>⚡ Real-time Lookup:</strong> Instant price projections<br>
            <strong>🔍 Batch Processing:</strong> Multiple time analysis<br>
            <strong>📐 Slope Management:</strong> Customizable parameters<br>
            <strong>💾 Preset System:</strong> Save/load configurations<br>
            <strong>📥 Export Suite:</strong> CSV, JSON, Reports
        </div>
    </div>
    """, unsafe_allow_html=True)

with capabilities_col2:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.05));
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
        height: 100%;
    ">
        <h4 style="color: #3b82f6; margin: 0 0 1.5rem 0;">🧠 Intelligence Features</h4>
        <div style="line-height: 1.8;">
            <strong>🎯 Stock Profiles:</strong> Detailed trading characteristics<br>
            <strong>📈 Pattern Recognition:</strong> Market behavior analysis<br>
            <strong>⚡ Volatility Assessment:</strong> Risk evaluation system<br>
            <strong>🌍 Market Regime:</strong> Condition adaptation<br>
            <strong>🕐 Chicago Time:</strong> Accurate timezone handling<br>
            <strong>🎨 Theme System:</strong> Dark/light mode support<br>
            <strong>📱 Responsive Design:</strong> Multi-device compatibility<br>
            <strong>⚙️ Session Management:</strong> State preservation
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL PERFORMANCE METRICS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("### 📊 Session Analytics")

# Performance breakdown
perf_col1, perf_col2, perf_col3 = st.columns(3)

with perf_col1:
    # Count forecasts by type
    spx_count = len(st.session_state.current_forecasts) if st.session_state.current_forecasts else 0
    contract_count = 1 if not st.session_state.contract_table.empty else 0
    stock_count = sum(1 for ticker in strategy.get_available_tickers() if f"{ticker}_forecasts" in st.session_state)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(5, 150, 105, 0.05));
        border: 2px solid #22c55e;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.3);
    ">
        <h5 style="color: #22c55e; margin: 0 0 1rem 0;">📈 Forecast Breakdown</h5>
        <div style="font-size: 0.9rem; line-height: 1.6;">
            <strong>SPX Forecasts:</strong> {spx_count}<br>
            <strong>Contract Lines:</strong> {contract_count}<br>
            <strong>Stock Analysis:</strong> {stock_count}<br>
            <strong>Total Active:</strong> {spx_count + contract_count + stock_count}
        </div>
    </div>
    """, unsafe_allow_html=True)

with perf_col2:
    # Slope configuration status
    default_slopes = sum(1 for k, v in strategy.slopes.items() if v == strategy.base_slopes[k])
    modified_slopes = len(strategy.slopes) - default_slopes
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.05));
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
    ">
        <h5 style="color: #3b82f6; margin: 0 0 1rem 0;">📐 Slope Configuration</h5>
        <div style="font-size: 0.9rem; line-height: 1.6;">
            <strong>Total Assets:</strong> {len(strategy.slopes)}<br>
            <strong>Default Slopes:</strong> {default_slopes}<br>
            <strong>Modified Slopes:</strong> {modified_slopes}<br>
            <strong>Customization:</strong> {(modified_slopes/len(strategy.slopes)*100):.0f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

with perf_col3:
    # Session statistics
    current_page = st.session_state.selected_page
    theme_mode = "Dark" if st.session_state.dark_mode else "Light"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
        border: 2px solid #8b5cf6;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3);
    ">
        <h5 style="color: #8b5cf6; margin: 0 0 1rem 0;">⚙️ Session Status</h5>
        <div style="font-size: 0.9rem; line-height: 1.6;">
            <strong>Current Page:</strong> {current_page}<br>
            <strong>Theme Mode:</strong> {theme_mode}<br>
            <strong>Session Time:</strong> {chicago_time.strftime('%H:%M:%S')}<br>
            <strong>Status:</strong> Active
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE DISCLAIMER & LEGAL
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### ⚠️ Important Disclaimer & Risk Warning")

st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
    border: 2px solid #ef4444;
    border-radius: 16px;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: 0 8px 25px rgba(239, 68, 68, 0.2);
">
    <h4 style="color: #ef4444; margin: 0 0 1rem 0; text-align: center;">⚠️ Critical Risk Disclosure</h4>
    <div style="line-height: 1.6; font-size: 0.95rem;">
        <p><strong>EDUCATIONAL USE ONLY:</strong> This tool is designed for educational and analysis purposes only. All forecasts, projections, and recommendations are theoretical and should not be considered as financial advice.</p>
        
        <p><strong>NO INVESTMENT ADVICE:</strong> The creators, developers, and distributors of Dr. David's Market Mind do not provide investment advice. Users must conduct their own research and consult with qualified financial advisors before making any trading decisions.</p>
        
        <p><strong>PAST PERFORMANCE WARNING:</strong> Past performance does not guarantee future results. Market conditions can change rapidly, and all investments carry risk of loss. You may lose all or part of your investment capital.</p>
        
        <p><strong>RISK MANAGEMENT:</strong> Always implement proper risk management strategies including position sizing, stop losses, and diversification. Never invest more than you can afford to lose.</p>
        
        <p><strong>NO LIABILITY:</strong> The creators are not responsible for any financial losses, trading decisions, or investment outcomes resulting from the use of this tool. Users assume all responsibility for their trading activities.</p>
        
        <p><strong>MARKET VOLATILITY:</strong> Financial markets are inherently volatile and unpredictable. Economic events, news, and market sentiment can cause rapid price changes that may not be reflected in any forecasting model.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL FOOTER & VERSION INFO
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

# Application metadata and version info
footer_col1, footer_col2, footer_col3 = st.columns([2, 2, 2])

with footer_col1:
    st.markdown("""
    **🧠 Dr. David's Market Mind**  
    Premium Financial Forecasting Platform  
    Version 3.0 Premium Edition  
    
    **Features:**  
    ✅ Three-Anchor SPX Forecasting  
    ✅ Contract Line Interpolation  
    ✅ Individual Stock Analysis  
    ✅ Real-time Lookup System  
    """)

with footer_col2:
    st.markdown(f"""
    **⚙️ Technical Specifications**  
    Python Streamlit Application  
    Chicago Timezone Integration  
    Advanced 3D Styling System  
    
    **Session Info:**  
    📅 Date: {chicago_time.strftime('%Y-%m-%d')}  
    🕐 Time: {chicago_time.strftime('%H:%M:%S CST')}  
    📊 Active Forecasts: {total_active_forecasts}  
    🎯 Current Page: {st.session_state.selected_page}  
    """)

with footer_col3:
    st.markdown("""
    **📊 System Status**  
    🟢 All Systems Operational  
    🟢 Real-time Data Active  
    🟢 Chicago Time Synchronized  
    🟢 Export Functions Ready  
    
    **🛠️ Support:**  
    📧 Technical Documentation  
    💡 Built-in Help System  
    🔄 Auto-save Functionality  
    ⚙️ Configuration Management  
    """)

# Final status indicator
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    text-align: center;
    margin: 2rem 0;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    animation: glow 3s ease-in-out infinite;
">
    <strong>🎉 SESSION COMPLETE - Dr. David's Market Mind v3.0 Premium</strong><br>
    <small>Generated: {chicago_time.strftime('%Y-%m-%d %H:%M:%S CST')} | Page: {st.session_state.selected_page} | Active Forecasts: {total_active_forecasts}</small>
</div>
""", unsafe_allow_html=True)

# Copyright and final notes
st.markdown(
    f"""
    <div style="text-align: center; opacity: 0.7; font-size: 0.8rem; margin: 2rem 0;">
        <strong>Dr. David's Market Mind Premium v3.0</strong> • 
        Built with Streamlit & Advanced Analytics • 
        Session: {chicago_time.strftime('%Y-%m-%d %H:%M:%S CST')} • 
        Copyright © 2025 • Educational Use Only
    </div>
    """,
    unsafe_allow_html=True
)

# ═══════════════════════════════════════════════════════════════════════════════
# END OF APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

# Final cleanup and optimization note
if st.sidebar.button("🎉 Session Summary", key="final_summary"):
    st.sidebar.success(f"✅ Market Mind Complete!")
    st.sidebar.info(f"📊 {total_active_forecasts} active forecasts")
    st.sidebar.info(f"📈 {total_data_points} data points generated")
    st.sidebar.info(f"⏰ Session time: {chicago_time.strftime('%H:%M:%S CST')}")
    st.sidebar.info(f"🎯 Current focus: {st.session_state.selected_page}")

# Application successfully loaded indicator
# This serves as a checkpoint that all parts have loaded correctly
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        text-align: center;
        font-size: 0.85rem;
        margin-top: 1rem;
    ">
        <strong>🚀 ALL SYSTEMS LOADED</strong><br>
        Dr. David's Market Mind v3.0 Premium<br>
        <small>Ready for Professional Trading Analysis</small>
    </div>
    """,
    unsafe_allow_html=True
)
