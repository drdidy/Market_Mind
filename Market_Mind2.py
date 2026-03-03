import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import pytz

# --- 1. SYSTEM CONSTANTS ---
RATE_PER_CANDLE = 0.52
CANDLE_MINUTES = 30
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
        .metric-value { font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: bold; color: #00d4ff; }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] { background-color: #0a0e17 !important; border-right: 1px solid #1e293b; }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            height: 50px; white-space: pre-wrap; background-color: transparent;
            border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px;
            font-family: 'Orbitron', sans-serif !important; color: #8892b0;
        }
        .stTabs [aria-selected="true"] { color: #ccd6f6 !important; border-bottom-color: #00d4ff !important; }
        
        /* Ladder Table */
        .ladder-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        .ladder-table th { font-family: 'Orbitron', sans-serif; text-align: left; padding: 12px; border-bottom: 1px solid #1e293b; color: #8892b0; }
        .ladder-table td { font-family: 'JetBrains Mono', monospace; padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .ladder-row-asc { color: #ff5252; } /* Resistance */
        .ladder-row-desc { color: #00e676; } /* Support */
        .ladder-row-key { font-weight: bold; background-color: rgba(255,255,255,0.03); }
        </style>
    """, unsafe_allow_html=True)

# --- 3. CORE MATHEMATICS & TIME HANDLING ---
def count_candles_between(start_dt: datetime, end_dt: datetime) -> int:
    """Counts 30-min intervals excluding weekends/maintenance."""
    if start_dt.tzinfo is None: start_dt = CT_TZ.localize(start_dt)
    if end_dt.tzinfo is None: end_dt = CT_TZ.localize(end_dt)
    if start_dt >= end_dt: return 0
        
    candle_count = 0
    current_time = start_dt
    
    while current_time < end_dt:
        weekday = current_time.weekday()
        hour = current_time.hour
        
        is_maintenance = (hour >= MAINTENANCE_START_HOUR and hour < MAINTENANCE_END_HOUR)
        is_saturday = (weekday == 5)
        is_sunday_pre_open = (weekday == 6 and hour < MAINTENANCE_END_HOUR)
        is_friday_post_close = (weekday == 4 and hour >= MAINTENANCE_START_HOUR)
        
        if not (is_maintenance or is_saturday or is_sunday_pre_open or is_friday_post_close):
            candle_count += 1
            
        current_time += timedelta(minutes=CANDLE_MINUTES)
    return candle_count

def project_line_value(anchor_price: float, anchor_time: datetime, target_time: datetime, is_ascending: bool) -> float:
    candles = count_candles_between(anchor_time, target_time)
    price_change = RATE_PER_CANDLE * candles
    return anchor_price + price_change if is_ascending else anchor_price - price_change

def get_next_trading_day_9am(target_date: date) -> datetime:
    """Finds 9:00 AM CT for the next valid trading day after the target date."""
    next_day = target_date + timedelta(days=1)
    while next_day.weekday() > 4:  # Skip 5 (Sat), 6 (Sun)
        next_day += timedelta(days=1)
    # Combine with 9:00 AM and localize
    dt = datetime.combine(next_day, datetime.min.time()) + timedelta(hours=9)
    return CT_TZ.localize(dt)

# --- 4. DATA ENGINE & AUTO-DETECTION ---
@st.cache_data(ttl=300)
def get_market_data(symbol="ES=F"):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="10d", interval="30m")
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC').tz_convert(CT_TZ)
        else:
            data.index = data.index.tz_convert(CT_TZ)
        return data
    except Exception as e:
        return None

def filter_ny_session(df, target_date):
    target_date_str = target_date.strftime('%Y-%m-%d')
    try:
        day_data = df.loc[target_date_str]
        return day_data.between_time('08:30', '15:00')
    except KeyError:
        return pd.DataFrame()

def detect_inflection_points(ny_data):
    if ny_data.empty or len(ny_data) < 2: return None
        
    bounces, rejections = [], []
    closes = np.asarray(ny_data['Close'])
    times = ny_data.index
    n = len(closes)
    
    for i in range(n):
        if i == 0:
            if closes[0] < closes[1]: bounces.append({'time': times[0], 'price': closes[0]})
            if closes[0] > closes[1]: rejections.append({'time': times[0], 'price': closes[0]})
        elif i == n - 1:
            if closes[n-1] < closes[n-2]: bounces.append({'time': times[n-1], 'price': closes[n-1]})
            if closes[n-1] > closes[n-2]: rejections.append({'time': times[n-1], 'price': closes[n-1]})
        else:
            if closes[i] < closes[i-1] and closes[i] < closes[i+1]: bounces.append({'time': times[i], 'price': closes[i]})
            if closes[i] > closes[i-1] and closes[i] > closes[i+1]: rejections.append({'time': times[i], 'price': closes[i]})
                
    bearish = ny_data[ny_data['Close'] < ny_data['Open']]
    bullish = ny_data[ny_data['Close'] > ny_data['Open']]
    
    hw = {'time': bearish['High'].idxmax(), 'price': bearish.loc[bearish['High'].idxmax(), 'High']} if not bearish.empty else None
    lw = {'time': bullish['Low'].idxmin(), 'price': bullish.loc[bullish['Low'].idxmin(), 'Low']} if not bullish.empty else None
        
    return {'bounces': bounces, 'rejections': rejections, 'hw': hw, 'lw': lw}

def calculate_ladder(inflections, target_9am):
    """Projects all lines to 9AM and identifies key levels."""
    lines = []
    
    # Project Ascending (Resistance)
    if inflections['hw']:
        val = project_line_value(inflections['hw']['price'], inflections['hw']['time'], target_9am, True)
        lines.append({'label': 'HW', 'name': 'Highest Wick', 'dir': 'Ascending', 'val': val, 'is_key': True})
        
    highest_bounce_val = -float('inf')
    hb_ref = None
    for i, b in enumerate(inflections['bounces']):
        val = project_line_value(b['price'], b['time'], target_9am, True)
        line_obj = {'label': f'B{i+1}', 'name': 'Bounce', 'dir': 'Ascending', 'val': val, 'is_key': False}
        lines.append(line_obj)
        if val > highest_bounce_val:
            highest_bounce_val = val
            hb_ref = line_obj
            
    if hb_ref:
        hb_ref['is_key'] = True
        hb_ref['label'] = 'HB'
        hb_ref['name'] = 'Highest Bounce'

    # Project Descending (Support)
    if inflections['lw']:
        val = project_line_value(inflections['lw']['price'], inflections['lw']['time'], target_9am, False)
        lines.append({'label': 'LW', 'name': 'Lowest Wick', 'dir': 'Descending', 'val': val, 'is_key': True})
        
    lowest_rej_val = float('inf')
    lr_ref = None
    for i, r in enumerate(inflections['rejections']):
        val = project_line_value(r['price'], r['time'], target_9am, False)
        line_obj = {'label': f'R{i+1}', 'name': 'Rejection', 'dir': 'Descending', 'val': val, 'is_key': False}
        lines.append(line_obj)
        if val < lowest_rej_val:
            lowest_rej_val = val
            lr_ref = line_obj
            
    if lr_ref:
        lr_ref['is_key'] = True
        lr_ref['label'] = 'LR'
        lr_ref['name'] = 'Lowest Rejection'

    # Sort from highest price to lowest price
    lines.sort(key=lambda x: x['val'], reverse=True)
    return lines

# --- 5. UI COMPONENTS ---
def render_section_banner(icon: str, title: str, subtitle: str, color: str):
    st.markdown(f"""
    <div style="margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid {color}; display: flex; align-items: center; gap: 15px;">
        <div style="font-size: 2.5rem;">{icon}</div>
        <div><h2 class="orbitron" style="margin: 0; padding: 0; color: #ccd6f6;">{title}</h2>
        <span class="rajdhani" style="color: #8892b0; font-size: 1.1rem;">{subtitle}</span></div>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, color="#00d4ff"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="rajdhani" style="color: #8892b0; font-size: 0.9rem; text-transform: uppercase;">{label}</div>
        <div class="metric-value" style="color: {color};">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. MAIN APP ---
def main():
    inject_custom_css()
    
    with st.sidebar:
        st.markdown("<h2 class='orbitron' style='color: #00d4ff; font-size: 1.2rem;'>SYSTEM STATUS</h2>", unsafe_allow_html=True)
        render_metric_card("Engine State", "OPERATIONAL", "#00e676")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3 class='orbitron' style='font-size: 0.9rem;'>SESSION CONTROLS</h3>", unsafe_allow_html=True)
        
        today = datetime.now()
        default_date = today if today.weekday() < 5 else today - timedelta(days=today.weekday()-4)
        target_date = st.date_input("Prior Session Date", default_date)
        manual_offset = st.number_input("ES-SPX Offset", value=0.0, step=0.25)
        st.markdown("---")
        st.button("🔄 Force Data Refresh")

    tab_map, tab_asian, tab_ny, tab_log = st.tabs(["🗺️ STRUCTURAL MAP", "🌏 ASIAN SESSION", "🗽 NY SESSION", "📓 TRADE LOG"])
    es_data = get_market_data()
    
    with tab_map:
        render_section_banner("🗺️", "STRUCTURAL MAP", "Prior NY Session Data & 9 AM Projections", "#00d4ff")
        
        if es_data is not None and len(es_data) > 0:
            ny_data = filter_ny_session(es_data, target_date)
            
            if not ny_data.empty:
                inflections = detect_inflection_points(ny_data)
                target_9am = get_next_trading_day_9am(target_date)
                ladder = calculate_ladder(inflections, target_9am)
                
                col1, col2, col3, col4 = st.columns(4)
                closes = np.asarray(ny_data['Close'])
                opens = np.asarray(ny_data['Open'])
                last_price = float(closes[-1])
                change = last_price - float(opens[0])
                
                with col1: render_metric_card("NY Session Close", f"{last_price:.2f}")
                with col2: render_metric_card("Session Net", f"{change:+.2f}", "#00e676" if change > 0 else "#ff5252")
                with col3: render_metric_card("Target Projection", target_9am.strftime("%m/%d 9:00 AM"), "#ffd740")
                with col4: render_metric_card("Lines Projected", str(len(ladder)), "#b388ff")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Layout: Chart on Left, Ladder on Right
                chart_col, ladder_col = st.columns([1.5, 1])
                
                with chart_col:
                    st.markdown(f"<h3 class='orbitron' style='font-size: 1.1rem;'>PRICE ACTION ({target_date.strftime('%m/%d')})</h3>", unsafe_allow_html=True)
                    fig = go.Figure(data=[go.Candlestick(x=ny_data.index, open=ny_data['Open'], high=ny_data['High'], low=ny_data['Low'], close=ny_data['Close'])])
                    fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), height=450, xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                with ladder_col:
                    st.markdown(f"<h3 class='orbitron' style='font-size: 1.1rem;'>9:00 AM PROJECTED LADDER</h3>", unsafe_allow_html=True)
                    
                    # Build HTML Table
                    html_table = "<table class='ladder-table'><tr><th>Level</th><th>Direction</th><th>Projected Price</th></tr>"
                    for row in ladder:
                        row_class = "ladder-row-asc" if row['dir'] == 'Ascending' else "ladder-row-desc"
                        key_class = "ladder-row-key" if row['is_key'] else ""
                        icon = "🔴" if row['dir'] == 'Ascending' else "🟢"
                        marker = "💎 " if row['is_key'] else ""
                        html_table += f"<tr class='{row_class} {key_class}'>"
                        html_table += f"<td>{marker}{row['label']} ({row['name']})</td>"
                        html_table += f"<td>{icon} {row['dir']}</td>"
                        html_table += f"<td>{row['val']:.2f}</td>"
                        html_table += "</tr>"
                    html_table += "</table>"
                    
                    st.markdown(html_table, unsafe_allow_html=True)

            else:
                st.warning(f"No NY Session data found for {target_date.strftime('%Y-%m-%d')}.")
        else:
            st.warning("Awaiting Market Data...")

    with tab_asian: render_section_banner("🌏", "ASIAN SESSION", "ES Futures Prop Firm Scalping Framework", "#ff9100")
    with tab_ny: render_section_banner("🗽", "NY SESSION", "SPX 0DTE Options Signal Generation", "#b388ff")
    with tab_log: render_section_banner("📓", "TRADE LOG", "Daily Journal & Performance Metrics", "#00e676")

if __name__ == "__main__":
    main()
