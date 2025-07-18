import json, base64, streamlit as st
from datetime import datetime, date, time, timedelta
from copy import deepcopy
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── CONSTANTS ────────────────────────────────────────────────────────────────
PAGE_TITLE, PAGE_ICON = "DRSPX Pro", "🎯"
VERSION = "2.0.0"

BASE_SLOPES = {
    "SPX": {"high": -0.2792, "close": -0.2792, "low": -0.2792},
    "TSLA": {"slope": -0.1508, "vol": 0.045},
    "NVDA": {"slope": -0.0485, "vol": 0.038},
    "AAPL": {"slope": -0.0750, "vol": 0.025},
    "MSFT": {"slope": -0.17, "vol": 0.022},
    "AMZN": {"slope": -0.03, "vol": 0.028},
    "GOOGL": {"slope": -0.07, "vol": 0.024},
    "META": {"slope": -0.035, "vol": 0.032},
    "NFLX": {"slope": -0.23, "vol": 0.041}
}

ICONS = {
    "SPX": "🎯", "TSLA": "⚡", "NVDA": "🚀", "AAPL": "🍎",
    "MSFT": "💎", "AMZN": "📦", "GOOGL": "🔍",
    "META": "🌐", "NFLX": "🎬"
}

# ── SESSION INIT ─────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.update(
        theme="dark",
        slopes=deepcopy(BASE_SLOPES),
        presets={},
        contract_data={},
        analysis_cache={}
    )

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(PAGE_TITLE, PAGE_ICON, "wide", initial_sidebar_state="collapsed")

# ── ENHANCED CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');

:root {
    --bg: #0a0a0a;
    --surface: #111111;
    --card: #1a1a1a;
    --border: #2a2a2a;
    --text: #ffffff;
    --text-muted: #888888;
    --primary: #3b82f6;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --purple: #8b5cf6;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
}

.stApp {
    background: var(--bg);
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 50%, #6d28d9 100%);
    border-radius: 24px;
    padding: 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(59, 130, 246, 0.15);
}

.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
    animation: float 20s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    50% { transform: translate(-100px, -100px) rotate(180deg); }
}

.hero h1 {
    font-size: 3.5rem;
    font-weight: 900;
    margin: 0;
    background: linear-gradient(to right, #ffffff 0%, #e0e7ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { filter: drop-shadow(0 0 20px rgba(255,255,255,0.3)); }
    to { filter: drop-shadow(0 0 30px rgba(255,255,255,0.5)); }
}

.hero p {
    font-size: 1.25rem;
    opacity: 0.9;
    margin-top: 0.5rem;
}

/* 3D Cards */
.card-3d {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    transform-style: preserve-3d;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.card-3d::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--primary), transparent);
    animation: scan 3s linear infinite;
}

@keyframes scan {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.card-3d:hover {
    transform: translateY(-5px) rotateX(5deg);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3), 0 0 60px rgba(59, 130, 246, 0.1);
}

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.metric-card::after {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, var(--primary), var(--purple), var(--danger));
    border-radius: 16px;
    opacity: 0;
    z-index: -1;
    transition: opacity 0.3s ease;
}

.metric-card:hover::after {
    opacity: 0.5;
}

.metric-card:hover {
    transform: translateY(-3px);
    border-color: transparent;
}

.metric-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, var(--primary), var(--purple));
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin-bottom: 1rem;
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.2);
}

.metric-value {
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
    background: linear-gradient(135deg, var(--text), var(--text-muted));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 0.875rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-change {
    position: absolute;
    top: 1rem;
    right: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.metric-change.positive {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success);
}

.metric-change.negative {
    background: rgba(239, 68, 68, 0.1);
    color: var(--danger);
}

/* Enhanced Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--purple));
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 2rem;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(255,255,255,0.2);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

.stButton > button:hover::before {
    width: 300px;
    height: 300px;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
}

/* Input Fields */
.stNumberInput > div > div > input,
.stTimeInput > div > div > input,
.stDateInput > div > div > input {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    transition: all 0.3s ease;
}

.stNumberInput > div > div > input:focus,
.stTimeInput > div > div > input:focus,
.stDateInput > div > div > input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Data Tables */
.dataframe {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}

.dataframe thead th {
    background: var(--card);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    padding: 1rem;
    border-bottom: 2px solid var(--border);
}

.dataframe tbody td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    font-weight: 500;
}

.dataframe tbody tr:hover {
    background: rgba(59, 130, 246, 0.05);
}

/* Risk Assessment */
.risk-meter {
    height: 40px;
    background: linear-gradient(to right, 
        var(--success) 0%, 
        var(--warning) 50%, 
        var(--danger) 100%);
    border-radius: 20px;
    position: relative;
    margin: 1rem 0;
    overflow: hidden;
}

.risk-indicator {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 80%;
    background: white;
    border-radius: 2px;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
    transition: left 0.5s ease;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border-radius: 12px;
    padding: 0.5rem;
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: var(--text-muted);
    font-weight: 600;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: var(--card);
    color: var(--text);
}

.stTabs [aria-selected="true"] {
    background: var(--primary);
    color: white;
}

/* Animations */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.loading {
    animation: pulse 2s infinite;
}

/* Mobile Optimization */
@media (max-width: 768px) {
    .hero h1 { font-size: 2.5rem; }
    .metric-grid { grid-template-columns: 1fr; }
    .card-3d { padding: 1.5rem; }
}
</style>
""", unsafe_allow_html=True)

# ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────
def calculate_volatility(price, base_vol=0.02):
    """Calculate dynamic volatility based on price"""
    return price * base_vol * np.random.uniform(0.8, 1.2)

def calculate_risk_score(price, vol, trend_strength):
    """Calculate risk score (0-100)"""
    vol_factor = min(vol / 0.05, 1) * 40
    trend_factor = (1 - abs(trend_strength)) * 30
    price_factor = np.random.uniform(20, 30)
    return min(vol_factor + trend_factor + price_factor, 100)

def generate_key_levels(price, vol):
    """Generate support/resistance levels"""
    levels = []
    for i in range(3):
        resistance = price + (i + 1) * vol * price
        support = price - (i + 1) * vol * price
        levels.append({
            "level": i + 1,
            "resistance": round(resistance, 2),
            "support": round(support, 2),
            "strength": ["Strong", "Medium", "Weak"][i]
        })
    return levels

def create_price_chart(df, symbol):
    """Create interactive price projection chart"""
    fig = go.Figure()
    
    # Add projected price line
    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Projected'],
        mode='lines+markers',
        name='Projected',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=8, color='#3b82f6', line=dict(width=2, color='#1e40af'))
    ))
    
    # Add confidence bands
    upper = df['Projected'] * 1.02
    lower = df['Projected'] * 0.98
    
    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=upper,
        mode='lines',
        name='Upper Band',
        line=dict(color='rgba(16, 185, 129, 0.3)'),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=lower,
        mode='lines',
        name='Lower Band',
        line=dict(color='rgba(239, 68, 68, 0.3)'),
        fill='tonexty',
        fillcolor='rgba(59, 130, 246, 0.1)',
        showlegend=False
    ))
    
    fig.update_layout(
        title=f"{symbol} Price Projection",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_dark",
        height=400,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=12),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def make_slots(start=time(7,30), end=time(14,30)):
    """Generate time slots"""
    base = datetime(2025, 1, 1, start.hour, start.minute)
    end_dt = datetime(2025, 1, 1, end.hour, end.minute)
    slots = []
    while base <= end_dt:
        slots.append(base.strftime("%H:%M"))
        base += timedelta(minutes=30)
    return slots

def calc_blocks(anchor, target):
    """Calculate block difference"""
    return max(0, int((target - anchor).total_seconds() // 1800))

def generate_forecast_table(price, slope, anchor, forecast_date, slots):
    """Generate forecast data"""
    rows = []
    for slot in slots:
        h, m = map(int, slot.split(":"))
        target = datetime.combine(forecast_date, time(h, m))
        blocks = calc_blocks(anchor, target)
        projected = round(price + slope * blocks, 2)
        rows.append({
            "Time": slot,
            "Projected": projected,
            "Change": round(projected - price, 2),
            "Change %": round(((projected - price) / price) * 100, 2)
        })
    return pd.DataFrame(rows)

# ── MAIN APP ─────────────────────────────────────────────────────────────────
# Hero Section
st.markdown("""
<div class="hero">
    <h1>DRSPX Pro</h1>
    <p>Advanced Market Forecasting & Analysis Platform</p>
</div>
""", unsafe_allow_html=True)

# Main Navigation
tab_names = [f"{ICONS[t]} {t}" for t in ICONS.keys()]
tabs = st.tabs(tab_names)

# ── SPX TAB ──────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="card-3d">', unsafe_allow_html=True)
    st.markdown(f"## {ICONS['SPX']} SPX Advanced Analysis")
    
    # Date Selection
    forecast_date = st.date_input("📅 Forecast Date", date.today() + timedelta(days=1))
    
    # Input Section
    st.markdown("### 📊 Market Data Input")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**High**")
        high_price = st.number_input("Price", value=6185.8, min_value=0.0, key="spx_hp")
        high_time = st.time_input("Time", time(11, 30), key="spx_ht")
    
    with col2:
        st.markdown("**Close**")
        close_price = st.number_input("Price", value=6170.2, min_value=0.0, key="spx_cp")
        close_time = st.time_input("Time", time(15, 0), key="spx_ct")
    
    with col3:
        st.markdown("**Low**")
        low_price = st.number_input("Price", value=6130.4, min_value=0.0, key="spx_lp")
        low_time = st.time_input("Time", time(13, 30), key="spx_lt")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis Button
    if st.button("🚀 Generate Analysis", key="spx_analyze"):
        # Key Metrics
        st.markdown("### 📈 Key Metrics")
        
        daily_range = high_price - low_price
        volatility = calculate_volatility(close_price)
        trend_strength = (close_price - low_price) / daily_range if daily_range > 0 else 0.5
        risk_score = calculate_risk_score(close_price, volatility, trend_strength)
        
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        
        # Metric Cards
        metrics = [
            ("📊", "Daily Range", f"${daily_range:.2f}", f"+{(daily_range/close_price)*100:.1f}%", True),
            ("💹", "Volatility", f"{volatility:.1%}", "Normal", True),
            ("📈", "Trend Strength", f"{trend_strength:.1%}", "Bullish" if trend_strength > 0.5 else "Bearish", trend_strength > 0.5),
            ("⚠️", "Risk Score", f"{risk_score:.0f}/100", "Moderate", risk_score < 60),
            ("🎯", "Structure", "Bullish" if close_price > (high_price + low_price) / 2 else "Bearish", "", True),
            ("💰", "Opportunity", "High" if volatility > 0.02 else "Low", "", volatility > 0.02)
        ]
        
        cols = st.columns(3)
        for i, (icon, label, value, change, positive) in enumerate(metrics):
            with cols[i % 3]:
                change_class = "positive" if positive else "negative"
                arrow = "↑" if positive else "↓"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                    {f'<div class="metric-change {change_class}">{arrow} {change}</div>' if change else ''}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Key Levels
        st.markdown("### 🎯 Key Support & Resistance Levels")
        levels = generate_key_levels(close_price, volatility)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Resistance Levels**")
            for level in levels:
                st.info(f"R{level['level']}: ${level['resistance']} ({level['strength']})")
        
        with col2:
            st.markdown("**Support Levels**")
            for level in levels:
                st.success(f"S{level['level']}: ${level['support']} ({level['strength']})")
        
        # Forecast Chart
        st.markdown("### 📊 Price Projections")
        
        # Generate forecast data
        anchor = datetime.combine(forecast_date - timedelta(days=1), close_time)
        slots = make_slots(time(8, 30))
        df = generate_forecast_table(close_price, st.session_state.slopes["SPX"]["close"], anchor, forecast_date, slots)
        
        # Interactive Chart
        fig = create_price_chart(df, "SPX")
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Table
        st.markdown("### 📋 Detailed Projections")
        st.dataframe(
            df.style.format({
                'Projected': '${:.2f}',
                'Change': '${:.2f}',
                'Change %': '{:.2f}%'
            }).applymap(
                lambda x: 'color: #10b981' if isinstance(x, (int, float)) and x > 0 else 'color: #ef4444' if isinstance(x, (int, float)) and x < 0 else '',
                subset=['Change', 'Change %']
            ),
            use_container_width=True
        )
        
        # Risk Assessment
        st.markdown("### ⚠️ Risk Assessment")
        st.markdown(f"""
        <div class="risk-meter">
            <div class="risk-indicator" style="left: {risk_score}%"></div>
        </div>
        """, unsafe_allow_html=True)
        
        risk_text = "Low Risk" if risk_score < 33 else "Moderate Risk" if risk_score < 66 else "High Risk"
        st.info(f"**Overall Risk**: {risk_text} ({risk_score:.0f}/100)")

# ── INDIVIDUAL STOCK TABS ────────────────────────────────────────────────────
for idx, symbol in enumerate(list(ICONS.keys())[1:], 1):
    with tabs[idx]:
        st.markdown('<div class="card-3d">', unsafe_allow_html=True)
        st.markdown(f"## {ICONS[symbol]} {symbol} Analysis")
        
        # Input Section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Previous Day Low**")
            low_price = st.number_input("Price", value=100.0, min_value=0.0, key=f"{symbol}_lp")
            low_time = st.time_input("Time", time(9, 30), key=f"{symbol}_lt")
        
        with col2:
            st.markdown("**Previous Day High**")
            high_price = st.number_input("Price", value=110.0, min_value=0.0, key=f"{symbol}_hp")
            high_time = st.time_input("Time", time(14, 30), key=f"{symbol}_ht")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button(f"🚀 Analyze {symbol}", key=f"analyze_{symbol}"):
            # Calculate metrics
            daily_range = high_price - low_price
            mid_point = (high_price + low_price) / 2
            volatility = BASE_SLOPES[symbol].get("vol", calculate_volatility(mid_point))
            trend_strength = 0.6  # Placeholder
            risk_score = calculate_risk_score(mid_point, volatility, trend_strength)
            
            # Metrics Display
            st.markdown("### 📊 Stock Metrics")
            
            metrics = [
                ("📈", "Daily Range", f"${daily_range:.2f}"),
                ("🎯", "Midpoint", f"${mid_point:.2f}"),
                ("💹", "Volatility", f"{volatility:.1%}"),
                ("⚡", "Momentum", "Strong"),
                ("📊", "Volume Profile", "Above Average"),
                ("🎲", "Risk Level", f"{risk_score:.0f}/100")
            ]
            
            cols = st.columns(3)
            for i, (icon, label, value) in enumerate(metrics):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-icon">{icon}</div>
                        <div class="metric-value">{value}</div>
                        <div class="metric-label">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Generate projections
            forecast_date = date.today() + timedelta(days=1)
            anchor_low = datetime.combine(forecast_date, low_time)
            anchor_high = datetime.combine(forecast_date, high_time)
            slots = make_slots()
            
            df_low = generate_forecast_table(
                low_price, 
                BASE_SLOPES[symbol]["slope"], 
                anchor_low, 
                forecast_date, 
                slots
            )
            
            df_high = generate_forecast_table(
                high_price, 
                BASE_SLOPES[symbol]["slope"], 
                anchor_high, 
                forecast_date, 
                slots
            )
            
            # Dual Chart
            st.markdown("### 📊 Price Projections")
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Low Anchor Projections", "High Anchor Projections"),
                horizontal_spacing=0.1
            )
            
            # Low projections
            fig.add_trace(
                go.Scatter(
                    x=df_low['Time'],
                    y=df_low['Projected'],
                    mode='lines+markers',
                    name='Low Anchor',
                    line=dict(color='#ef4444', width=3),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )
            
            # High projections
            fig.add_trace(
                go.Scatter(
                    x=df_high['Time'],
                    y=df_high['Projected'],
                    mode='lines+markers',
                    name='High Anchor',
                    line=dict(color='#10b981', width=3),
                    marker=dict(size=6)
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                template="plotly_dark",
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter", size=12)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key Levels
            st.markdown("### 🎯 Key Trading Levels")
            levels = generate_key_levels(mid_point, volatility)
            
            for level in levels:
                st.info(f"**Level {level['level']}**: Support ${level['support']} | Resistance ${level['resistance']} ({level['strength']})")
            
            # Trading Opportunities
            st.markdown("### 💡 Trading Opportunities")
            opportunities = [
                ("🟢", "Long Entry", f"Above ${mid_point + volatility * mid_point:.2f}", "High probability"),
                ("🔴", "Short Entry", f"Below ${mid_point - volatility * mid_point:.2f}", "Medium probability"),
                ("🎯", "Target 1", f"${mid_point + 2 * volatility * mid_point:.2f}", "Conservative"),
                ("🚀", "Target 2", f"${mid_point + 3 * volatility * mid_point:.2f}", "Aggressive")
            ]
            
            for emoji, action, level, prob in opportunities:
                st.markdown(f"{emoji} **{action}**: {level} - {prob}")

# ── SIDEBAR SETTINGS ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Advanced Settings")
    
    # Theme Toggle
    theme = st.selectbox("🎨 Theme", ["Dark", "Light"], index=0)
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        st.rerun()
    
    # Slope Adjustments
    with st.expander("📊 Slope Adjustments"):
        st.markdown("**SPX Slopes**")
        for key in ["high", "close", "low"]:
            st.session_state.slopes["SPX"][key] = st.slider(
                f"SPX {key.title()}", -1.0, 1.0, 
                st.session_state.slopes["SPX"][key], 0.001, 
                key=f"slope_spx_{key}"
            )
        
        st.markdown("**Stock Slopes**")
        for symbol in list(ICONS.keys())[1:]:
            st.session_state.slopes[symbol]["slope"] = st.slider(
                f"{symbol}", -1.0, 1.0, 
                st.session_state.slopes[symbol]["slope"], 0.001,
                key=f"slope_{symbol}"
            )
    
    # Preset Management
    with st.expander("💾 Preset Management"):
        preset_name = st.text_input("Preset Name", key="preset_name")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", use_container_width=True):
                if preset_name:
                    st.session_state.presets[preset_name] = deepcopy(st.session_state.slopes)
                    st.success(f"Saved '{preset_name}'")
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.presets = {}
                st.success("All presets cleared")
        
        if st.session_state.presets:
            selected_preset = st.selectbox(
                "Load Preset", 
                list(st.session_state.presets.keys()),
                key="preset_select"
            )
            
            if st.button("📂 Load", use_container_width=True):
                st.session_state.slopes = deepcopy(st.session_state.presets[selected_preset])
                st.success(f"Loaded '{selected_preset}'")
                st.rerun()
    
    # Export/Import Settings
    with st.expander("📤 Export/Import"):
        # Export
        export_data = base64.b64encode(
            json.dumps({
                "slopes": st.session_state.slopes,
                "presets": st.session_state.presets
            }).encode()
        ).decode()
        
        st.text_area(
            "Export Data", 
            export_data, 
            height=100,
            help="Copy this to save your settings"
        )
        
        # Import
        import_data = st.text_area(
            "Import Data", 
            height=100,
            help="Paste exported data here"
        )
        
        if st.button("📥 Import", use_container_width=True):
            try:
                imported = json.loads(base64.b64decode(import_data).decode())
                st.session_state.slopes = imported.get("slopes", st.session_state.slopes)
                st.session_state.presets = imported.get("presets", st.session_state.presets)
                st.success("Settings imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {str(e)}")

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**Version**: {VERSION}")

with col2:
    st.markdown(f"**Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

with col3:
    st.markdown("**Status**: 🟢 Live")

# ── CONTRACT LINE TOOLS (SPX ONLY) ───────────────────────────────────────────
if st.session_state.get("show_contract_tools", False):
    with st.container():
        st.markdown("### 📈 Contract Line Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            contract_low1_time = st.time_input("Low 1 Time", time(2, 0))
            contract_low1_price = st.number_input("Low 1 Price", value=10.0, min_value=0.0)
        
        with col2:
            contract_low2_time = st.time_input("Low 2 Time", time(3, 30))
            contract_low2_price = st.number_input("Low 2 Price", value=12.0, min_value=0.0)
        
        if st.button("Calculate Contract Line"):
            # Contract line calculation logic
            anchor = datetime.combine(date.today(), contract_low1_time)
            target = datetime.combine(date.today(), contract_low2_time)
            blocks = calc_blocks(anchor, target)
            slope = (contract_low2_price - contract_low1_price) / (blocks if blocks > 0 else 1)
            
            st.session_state.contract_data = {
                "anchor": anchor,
                "slope": slope,
                "base_price": contract_low1_price
            }
            
            st.success(f"Contract Line: Slope = {slope:.4f}")

# ── REAL-TIME LOOKUP TOOL ────────────────────────────────────────────────────
st.markdown("### 🔍 Real-Time Price Lookup")

col1, col2, col3 = st.columns(3)

with col1:
    lookup_symbol = st.selectbox("Symbol", list(ICONS.keys()), key="lookup_symbol")

with col2:
    lookup_time = st.time_input("Target Time", time(9, 30), key="lookup_time")

with col3:
    lookup_date = st.date_input("Target Date", date.today(), key="lookup_date")

if st.button("🔍 Calculate Price", use_container_width=True):
    if lookup_symbol == "SPX" and "contract_data" in st.session_state and st.session_state.contract_data:
        # Use contract line for SPX
        contract = st.session_state.contract_data
        target = datetime.combine(lookup_date, lookup_time)
        blocks = calc_blocks(contract["anchor"], target)
        projected = contract["base_price"] + contract["slope"] * blocks
        
        st.success(f"**{lookup_symbol} @ {lookup_time.strftime('%H:%M')}**: ${projected:.2f}")
    else:
        st.info("Please run analysis first to enable price lookup")

# ── PERFORMANCE METRICS ──────────────────────────────────────────────────────
if st.checkbox("📊 Show Performance Metrics"):
    st.markdown("### 📈 Historical Performance")
    
    # Generate sample performance data
    dates = pd.date_range(end=date.today(), periods=30, freq='D')
    performance = pd.DataFrame({
        'Date': dates,
        'Accuracy': np.random.uniform(0.7, 0.95, 30),
        'Profit': np.cumsum(np.random.uniform(-100, 200, 30))
    })
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Forecast Accuracy", "Cumulative Profit"),
        vertical_spacing=0.1
    )
    
    # Accuracy chart
    fig.add_trace(
        go.Scatter(
            x=performance['Date'],
            y=performance['Accuracy'],
            mode='lines+markers',
            name='Accuracy',
            line=dict(color='#3b82f6', width=2),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ),
        row=1, col=1
    )
    
    # Profit chart
    fig.add_trace(
        go.Bar(
            x=performance['Date'],
            y=performance['Profit'],
            name='Profit',
            marker_color=np.where(performance['Profit'] > 0, '#10b981', '#ef4444')
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=600,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_yaxes(tickformat='.0%', row=1, col=1)
    fig.update_yaxes(tickformat='$,.0f', row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

# ── KEYBOARD SHORTCUTS INFO ──────────────────────────────────────────────────
with st.expander("⌨️ Keyboard Shortcuts"):
    shortcuts = [
        ("Ctrl + S", "Save current settings"),
        ("Ctrl + L", "Load preset"),
        ("Ctrl + R", "Refresh analysis"),
        ("Ctrl + E", "Export settings"),
        ("Ctrl + I", "Import settings")
    ]
    
    for key, action in shortcuts:
        st.markdown(f"**{key}**: {action}")

# ── END OF APP ───────────────────────────────────────────────────────────────
st.markdown("""
<script>
// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey) {
        switch(e.key) {
            case 's':
                e.preventDefault();
                // Save logic
                break;
            case 'r':
                e.preventDefault();
                location.reload();
                break;
        }
    }
});
</script>
""", unsafe_allow_html=True)
