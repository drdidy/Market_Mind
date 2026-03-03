import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- 1. SYSTEM CONSTANTS ---
RATE_PER_CANDLE = 0.52
CT_TZ = pytz.timezone('US/Central')
MAINTENANCE_START_HOUR = 16 
MAINTENANCE_END_HOUR = 17 

# --- 2. STREAMLIT CONFIG & THEME ---
st.set_page_config(
    page_title="SPX PROPHET 2.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@500;700&family=Rajdhani:wght@500;600&display=swap');
        
        .stApp { background-color: #060910; color: #ccd6f6; }
        
        /* Typography */
        h1, h2, h3, .orbitron { font-family: 'Orbitron', sans-serif !important; letter-spacing: 2px; }
        p, span, .rajdhani { font-family: 'Rajdhani', sans-serif !important; }
        .jetbrains { font-family: 'JetBrains Mono', monospace !important; }
        
        /* Metric Cards */
        .metric-card {
            background: rgba(17, 25, 40, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .metric-value {
            font-family: 'JetBrains Mono';
            font-size: 1.5rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0a0e17 !important;
            border-right: 1px solid #1e293b;
        }
        
        /* Tab Styling overrides */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
            font-family: 'Orbitron', sans-serif !important;
            color: #8892b0;
        }
        .stTabs [aria-selected="true"] {
            color: #ccd6f6 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINE & AUTO-DETECTION ---
@st.cache_data(ttl=300)
def get_market_data(symbol="ES=F"):
    """Fetches 30m candle data for the last 5 days and ensures Central Time."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="10d", interval="30m")
        # Ensure timezone is Central Time
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC').tz_convert(CT_TZ)
        else:
            data.index = data.index.tz_convert(CT_TZ)
        return data
    except Exception as e:
        return None

def filter_ny_session(df, target_date):
    """Filters data to a specific date and NY session hours (8:30 AM - 3:00 PM CT)."""
    target_date_str = target_date.strftime('%Y-%m-%d')
    try:
        day_data = df.loc[target_date_str]
        # Filter to NY session times
        ny_data = day_data.between_time('08:30', '15:00')
        return ny_data
    except KeyError:
        return pd.DataFrame() # Return empty if date not in data

def detect_inflection_points(ny_data):
    """Scans NY session data to find bounces, rejections, and extreme wicks."""
    if ny_data.empty or len(ny_data) < 2:
        return None
        
    bounces = []
    rejections = []
    
    closes = np.asarray(ny_data['Close'])
    times = ny_data.index
    n = len(closes)
    
    # 1. Line Chart Bounces and Rejections
    for i in range(n):
        if i == 0:
            if closes[0] < closes[1]: bounces.append({'time': times[0], 'price': closes[0]})
            if closes[0] > closes[1]: rejections.append({'time': times[0], 'price': closes[0]})
        elif i == n - 1:
            if closes[n-1] < closes[n-2]: bounces.append({'time': times[n-1], 'price': closes[n-1]})
            if closes[n-1] > closes[n-2]: rejections.append({'time': times[n-1], 'price': closes[n-1]})
        else:
            if closes[i] < closes[i-1] and closes[i] < closes[i+1]:
                bounces.append({'time': times[i], 'price': closes[i]})
            if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
                rejections.append({'time': times[i], 'price': closes[i]})
                
    # 2. Extreme Wicks
    bearish = ny_data[ny_data['Close'] < ny_data['Open']]
    bullish = ny_data[ny_data['Close'] > ny_data['Open']]
    
    hw = None
    if not bearish.empty:
        hw_idx = bearish['High'].idxmax()
        hw = {'time': hw_idx, 'price': bearish.loc[hw_idx, 'High']}
        
    lw = None
    if not bullish.empty:
        lw_idx = bullish['Low'].idxmin()
        lw = {'time': lw_idx, 'price': bullish.loc[lw_idx, 'Low']}
        
    return {
        'bounces': bounces,
        'rejections': rejections,
        'hw': hw,
        'lw': lw
    }

# --- 4. UI COMPONENTS ---
def render_section_banner(icon: str, title: str, subtitle: str, color: str):
    st.markdown(f"""
    <div style="margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid {color}; display: flex; align-items: center; gap: 15px;">
        <div style="font-size: 2.5rem;">{icon}</div>
        <div>
            <h2 class="orbitron" style="margin: 0; padding: 0; color: #ccd6f6;">{title}</h2>
            <span class="rajdhani" style="color: #8892b0; font-size: 1.1rem;">{subtitle}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, color="#00d4ff"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="rajdhani" style="color: #8892b0; font-size: 0.9rem; text-transform: uppercase;">{label}</div>
        <div class="metric-value" style="color: {color};">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APP ---
def main():
    inject_custom_css()
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("<h2 class='orbitron' style='color: #00d4ff; font-size: 1.2rem;'>SYSTEM STATUS</h2>", unsafe_allow_html=True)
        render_metric_card("Engine State", "OPERATIONAL", "#00e676")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<h3 class='orbitron' style='font-size: 0.9rem;'>SESSION CONTROLS</h3>", unsafe_allow_html=True)
        
        # Default to the most recent weekday
        today = datetime.now()
        default_date = today if today.weekday() < 5 else today - timedelta(days=today.weekday()-4)
        target_date = st.date_input("Prior Session Date", default_date)
        
        manual_offset = st.number_input("ES-SPX Offset", value=0.0, step=0.25)
        st.markdown("---")
        st.button("🔄 Force Data Refresh")

    # --- TABS ---
    tab_map, tab_asian, tab_ny, tab_log = st.tabs(["🗺️ STRUCTURAL MAP", "🌏 ASIAN SESSION", "🗽 NY SESSION", "📓 TRADE LOG"])
    
    # FETCH DATA
    es_data = get_market_data()
    
    with tab_map:
        render_section_banner("🗺️", "STRUCTURAL MAP", "Prior NY Session Data & 9 AM Projections", "#00d4ff")
        
        if es_data is not None and len(es_data) > 0:
            ny_data = filter_ny_session(es_data, target_date)
            
            if not ny_data.empty:
                inflections = detect_inflection_points(ny_data)
                
                # Top Metrics
                col1, col2, col3, col4 = st.columns(4)
                closes = np.asarray(ny_data['Close'])
                opens = np.asarray(ny_data['Open'])
                
                last_price = float(closes[-1])
                change = last_price - float(opens[0])
                total_lines = len(inflections['bounces']) + len(inflections['rejections']) + (1 if inflections['hw'] else 0) + (1 if inflections['lw'] else 0)
                
                with col1: render_metric_card("NY Session Close", f"{last_price:.2f}")
                with col2: render_metric_card("Session Net", f"{change:+.2f}", "#00e676" if change > 0 else "#ff5252")
                with col3: render_metric_card("Target Date", target_date.strftime("%Y-%m-%d"), "#ffd740")
                with col4: render_metric_card("Generated Lines", str(total_lines), "#b388ff")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Chart Rendering
                st.markdown(f"<h3 class='orbitron' style='font-size: 1.1rem;'>NY SESSION PRICE ACTION ({target_date.strftime('%m/%d')})</h3>", unsafe_allow_html=True)
                fig = go.Figure(data=[go.Candlestick(x=ny_data.index,
                                open=ny_data['Open'], high=ny_data['High'],
                                low=ny_data['Low'], close=ny_data['Close'])])
                fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display Detected Points
                st.markdown("---")
                st.markdown("<h3 class='orbitron' style='font-size: 1.1rem; color: #ffd740;'>DETECTED ANCHOR POINTS</h3>", unsafe_allow_html=True)
                
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    st.markdown("<h4 class='rajdhani' style='color: #00e676;'>ASCENDING GENERATORS (Support/Resistance)</h4>", unsafe_allow_html=True)
                    if inflections['hw']:
                        st.markdown(f"**🔴 Highest Wick (HW):** <span class='jetbrains'>{inflections['hw']['price']:.2f}</span> at {inflections['hw']['time'].strftime('%H:%M CT')}", unsafe_allow_html=True)
                    for i, b in enumerate(inflections['bounces']):
                        st.markdown(f"**🟢 Bounce {i+1}:** <span class='jetbrains'>{b['price']:.2f}</span> at {b['time'].strftime('%H:%M CT')}", unsafe_allow_html=True)
                        
                with p_col2:
                    st.markdown("<h4 class='rajdhani' style='color: #ff5252;'>DESCENDING GENERATORS (Support/Resistance)</h4>", unsafe_allow_html=True)
                    if inflections['lw']:
                        st.markdown(f"**🟢 Lowest Wick (LW):** <span class='jetbrains'>{inflections['lw']['price']:.2f}</span> at {inflections['lw']['time'].strftime('%H:%M CT')}", unsafe_allow_html=True)
                    for i, r in enumerate(inflections['rejections']):
                        st.markdown(f"**🔴 Rejection {i+1}:** <span class='jetbrains'>{r['price']:.2f}</span> at {r['time'].strftime('%H:%M CT')}", unsafe_allow_html=True)

            else:
                st.warning(f"No NY Session data found for {target_date.strftime('%Y-%m-%d')}. If this is a weekend or holiday, select a valid prior trading session date from the sidebar.")
        else:
            st.warning("Awaiting Market Data...")

    with tab_asian:
        render_section_banner("🌏", "ASIAN SESSION", "ES Futures Prop Firm Scalping Framework", "#ff9100")
    with tab_ny:
        render_section_banner("🗽", "NY SESSION", "SPX 0DTE Options Signal Generation", "#b388ff")
    with tab_log:
        render_section_banner("📓", "TRADE LOG", "Daily Journal & Performance Metrics", "#00e676")

if __name__ == "__main__":
    main()
