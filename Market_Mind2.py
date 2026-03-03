import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import pytz
import math
from scipy.stats import norm

# --- 1. SYSTEM CONSTANTS ---
RATE_PER_CANDLE = 0.52
CANDLE_MINUTES = 30
CT_TZ = pytz.timezone('US/Central')
MAINTENANCE_START_HOUR = 16 
MAINTENANCE_END_HOUR = 17 

# --- 2. STREAMLIT CONFIG & THEME ---
st.set_page_config(page_title="SPX PROPHET 2.0", layout="wide", initial_sidebar_state="expanded")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');
        
        .stApp { background-color: #030508; color: #e2e8f0; }
        
        h1, h2, h3, h4, .orbitron { font-family: 'Orbitron', sans-serif !important; letter-spacing: 1.5px; }
        p, span, div, .rajdhani { font-family: 'Rajdhani', sans-serif !important; }
        .jetbrains { font-family: 'JetBrains Mono', monospace !important; }
        
        /* Glassmorphism Metric Cards */
        .metric-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px; padding: 16px; text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        .metric-value { font-family: 'JetBrains Mono'; font-size: 1.6rem; font-weight: 800; color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
        
        /* Sidebar */
        section[data-testid="stSidebar"] { background-color: #020617 !important; border-right: 1px solid #1e293b; }
        
        /* Sleek Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 30px; background-color: transparent; border-bottom: 1px solid #1e293b; }
        .stTabs [data-baseweb="tab"] {
            height: 55px; background-color: transparent; border: none;
            font-family: 'Orbitron', sans-serif !important; color: #64748b; font-size: 1rem;
        }
        .stTabs [aria-selected="true"] { color: #f8fafc !important; border-bottom: 2px solid #38bdf8 !important; }
        
        /* Signal Cards */
        .signal-put { background: linear-gradient(135deg, rgba(225, 29, 72, 0.2) 0%, rgba(0,0,0,0) 100%); border-left: 4px solid #e11d48; padding: 20px; border-radius: 6px; }
        .signal-call { background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(0,0,0,0) 100%); border-left: 4px solid #10b981; padding: 20px; border-radius: 6px; }
        .signal-wait { background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(0,0,0,0) 100%); border-left: 4px solid #f59e0b; padding: 20px; border-radius: 6px; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. CORE MATHEMATICS & TIME HANDLING ---
def count_candles_between(start_dt: datetime, end_dt: datetime) -> int:
    if start_dt.tzinfo is None: start_dt = CT_TZ.localize(start_dt)
    if end_dt.tzinfo is None: end_dt = CT_TZ.localize(end_dt)
    if start_dt >= end_dt: return 0
    candle_count = 0
    current_time = start_dt
    while current_time < end_dt:
        wd, hr = current_time.weekday(), current_time.hour
        is_maint = (hr >= MAINTENANCE_START_HOUR and hr < MAINTENANCE_END_HOUR)
        is_sat = (wd == 5)
        is_sun_pre = (wd == 6 and hr < MAINTENANCE_END_HOUR)
        is_fri_post = (wd == 4 and hr >= MAINTENANCE_START_HOUR)
        if not (is_maint or is_sat or is_sun_pre or is_fri_post): candle_count += 1
        current_time += timedelta(minutes=CANDLE_MINUTES)
    return candle_count

def project_line_value(anchor_price: float, anchor_time: datetime, target_time: datetime, is_ascending: bool) -> float:
    return anchor_price + (RATE_PER_CANDLE * count_candles_between(anchor_time, target_time)) if is_ascending else anchor_price - (RATE_PER_CANDLE * count_candles_between(anchor_time, target_time))

def get_target_time(target_date: date, hour: int) -> datetime:
    next_day = target_date + timedelta(days=1)
    while next_day.weekday() > 4: next_day += timedelta(days=1)
    dt = datetime.combine(next_day, datetime.min.time()) + timedelta(hours=hour)
    return CT_TZ.localize(dt)

# Black-Scholes Model
def bs_premium(S, K, T, r, sigma, option_type):
    if T <= 0: return max(0.0, S - K) if option_type == 'C' else max(0.0, K - S)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == 'C': return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    else: return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

# --- 4. DATA ENGINE & AUTO-DETECTION ---
@st.cache_data(ttl=300)
def get_market_data(symbol="ES=F"):
    try:
        data = yf.Ticker(symbol).history(period="10d", interval="30m")
        data.index = data.index.tz_localize('UTC').tz_convert(CT_TZ) if data.index.tz is None else data.index.tz_convert(CT_TZ)
        return data
    except Exception: return None

def filter_ny_session(df, target_date):
    target_date_str = target_date.strftime('%Y-%m-%d')
    try:
        return df.loc[target_date_str].between_time('08:30', '15:00')
    except KeyError:
        return pd.DataFrame()

def detect_inflection_points(ny_data):
    if ny_data.empty or len(ny_data) < 2: return None
    bounces, rejections = [], []
    closes, times = np.asarray(ny_data['Close']), ny_data.index
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
    bearish, bullish = ny_data[ny_data['Close'] < ny_data['Open']], ny_data[ny_data['Close'] > ny_data['Open']]
    hw = {'time': bearish['High'].idxmax(), 'price': bearish.loc[bearish['High'].idxmax(), 'High']} if not bearish.empty else None
    lw = {'time': bullish['Low'].idxmin(), 'price': bullish.loc[bullish['Low'].idxmin(), 'Low']} if not bullish.empty else None
    return {'bounces': bounces, 'rejections': rejections, 'hw': hw, 'lw': lw}

def calculate_ladder(inflections, target_time, offset=0.0):
    lines = []
    if inflections['hw']: lines.append({'label': 'HW', 'name': 'Highest Wick', 'dir': 'Ascending', 'val': project_line_value(inflections['hw']['price'], inflections['hw']['time'], target_time, True) - offset, 'is_key': True})
    hb_val, hb_ref = -float('inf'), None
    for i, b in enumerate(inflections['bounces']):
        val = project_line_value(b['price'], b['time'], target_time, True) - offset
        line = {'label': f'B{i+1}', 'name': 'Bounce', 'dir': 'Ascending', 'val': val, 'is_key': False}
        lines.append(line)
        if val > hb_val: hb_val, hb_ref = val, line
    if hb_ref: hb_ref.update({'is_key': True, 'label': 'HB', 'name': 'Highest Bounce'})

    if inflections['lw']: lines.append({'label': 'LW', 'name': 'Lowest Wick', 'dir': 'Descending', 'val': project_line_value(inflections['lw']['price'], inflections['lw']['time'], target_time, False) - offset, 'is_key': True})
    lr_val, lr_ref = float('inf'), None
    for i, r in enumerate(inflections['rejections']):
        val = project_line_value(r['price'], r['time'], target_time, False) - offset
        line = {'label': f'R{i+1}', 'name': 'Rejection', 'dir': 'Descending', 'val': val, 'is_key': False}
        lines.append(line)
        if val < lr_val: lr_val, lr_ref = val, line
    if lr_ref: lr_ref.update({'is_key': True, 'label': 'LR', 'name': 'Lowest Rejection'})
    lines.sort(key=lambda x: x['val'], reverse=True)
    return lines

# --- 5. LOGIC GENERATORS ---
def generate_ny_signal(ladder, current_price):
    asc_lines = [l for l in ladder if l['dir'] == 'Ascending']
    desc_lines = [l for l in ladder if l['dir'] == 'Descending']
    
    above_all_asc = all(current_price > l['val'] for l in asc_lines) if asc_lines else False
    below_all_asc = all(current_price < l['val'] for l in asc_lines) if asc_lines else False
    above_all_desc = all(current_price > l['val'] for l in desc_lines) if desc_lines else False
    below_all_desc = all(current_price < l['val'] for l in desc_lines) if desc_lines else False

    if below_all_asc and below_all_desc: return "PUT", "Price is below all structural lines. Strong Bearish Trend.", "signal-put"
    if above_all_asc and above_all_desc: return "CALL", "Price broke through all resistance and support. Strong Bullish Trend.", "signal-call"
    if below_all_asc: return "PUT", "Price is below all ascending resistance. Buyers are trapped above.", "signal-put"
    if above_all_asc: return "CALL", "Price broke above all ascending resistance. Bullish continuation.", "signal-call"
    
    nearest_above = next((l for l in reversed(ladder) if l['val'] > current_price), None)
    nearest_below = next((l for l in ladder if l['val'] < current_price), None)
    
    if nearest_above and nearest_below:
        if nearest_above['dir'] == 'Ascending' and nearest_below['dir'] == 'Descending': return "WAIT", f"Choppy. Trapped between Resistance ({nearest_above['label']}) and Support ({nearest_below['label']}).", "signal-wait"
        if nearest_above['dir'] == 'Descending': return "PUT", f"Bearish Lean. Price capped by descending resistance ({nearest_above['label']}).", "signal-put"
        if nearest_below['dir'] == 'Ascending': return "CALL", f"Bullish Lean. Price propped by ascending support ({nearest_below['label']}).", "signal-call"
    
    return "WAIT", "Market context unclear based on current structural positioning.", "signal-wait"

# --- 6. UI RENDERERS ---
def render_metric_card(label, value, color="#38bdf8"):
    st.markdown(f'<div class="metric-card"><div class="rajdhani" style="color: #64748b; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;">{label}</div><div class="metric-value" style="color: {color};">{value}</div></div>', unsafe_allow_html=True)

def render_spatial_ruler(ladder, current_price):
    """Next-Gen Spatial UI: Maps prices accurately to a visual vertical ruler."""
    if not ladder:
        st.write("No structural lines to display.")
        return

    all_prices = [l['val'] for l in ladder] + [current_price]
    max_p, min_p = max(all_prices) + 5, min(all_prices) - 5
    price_range = max_p - min_p if max_p != min_p else 1

    html = f"""<div style="position: relative; height: 600px; background: rgba(15, 23, 42, 0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-top: 1rem; overflow: hidden;">
        <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: rgba(255,255,255,0.1);"></div>"""

    # Render Lines
    for l in ladder:
        top_pct = 100 - (((l['val'] - min_p) / price_range) * 100)
        is_asc = l['dir'] == 'Ascending'
        color = "#f43f5e" if is_asc else "#10b981" # Red/Green
        align = "right" if is_asc else "left"
        left_pos = "0" if is_asc else "50%"
        width = "50%"
        border_side = "border-right" if is_asc else "border-left"
        weight = "800" if l['is_key'] else "400"
        opacity = "1" if l['is_key'] else "0.5"
        
        html += f"""<div style="position: absolute; top: {top_pct}%; left: {left_pos}; width: {width}; transform: translateY(-50%); text-align: {align}; padding: 0 15px; opacity: {opacity};">
            <div style="font-family: 'JetBrains Mono'; font-size: 0.85rem; color: {color}; {border_side}: 2px solid {color}; padding-{align}: 10px;">
                <span style="font-family: 'Orbitron'; font-weight: {weight};">{l['label']}</span> {l['val']:.2f}
            </div>
        </div>"""

    # Render Current Price (Target)
    curr_top = 100 - (((current_price - min_p) / price_range) * 100)
    html += f"""<div style="position: absolute; top: {curr_top}%; left: 0; right: 0; transform: translateY(-50%); z-index: 10;">
        <div style="background: rgba(56, 189, 248, 0.15); border: 1px solid #38bdf8; box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); border-radius: 4px; padding: 8px; width: 250px; margin: 0 auto; text-align: center; backdrop-filter: blur(5px);">
            <div style="color: #e2e8f0; font-family: 'Rajdhani'; font-size: 0.8rem; text-transform: uppercase;">Current Action</div>
            <div style="color: #38bdf8; font-family: 'JetBrains Mono'; font-size: 1.4rem; font-weight: 800;">{current_price:.2f}</div>
        </div>
    </div>"""
    
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# --- 7. MAIN APP ---
def main():
    inject_custom_css()
    
    with st.sidebar:
        st.markdown("<h2 class='orbitron' style='color: #38bdf8; font-size: 1.3rem; text-align: center;'>SYSTEM STATUS</h2>", unsafe_allow_html=True)
        render_metric_card("Engine", "ONLINE", "#10b981")
        st.markdown("<br>", unsafe_allow_html=True)
        
        today = datetime.now()
        default_date = today if today.weekday() < 5 else today - timedelta(days=today.weekday()-4)
        target_date = st.date_input("Prior Session Anchor Date", default_date)
        manual_offset = st.number_input("ES-SPX Offset (Points)", value=0.0, step=0.25)
        st.markdown("---")
        st.button("🔄 Force Data Refresh", use_container_width=True)

    tab_map, tab_asian, tab_ny, tab_log = st.tabs(["🗺️ STRUCTURAL MAP", "🌏 ASIAN SESSION (ES)", "🗽 NY SESSION (SPX)", "📓 TRADE LOG"])
    es_data = get_market_data()
    
    if es_data is None or len(es_data) == 0:
        st.warning("Awaiting Market Data...")
        return
        
    ny_data_raw = filter_ny_session(es_data, target_date)
    if ny_data_raw.empty:
        st.warning(f"No NY Session data found for {target_date.strftime('%Y-%m-%d')}.")
        return

    inflections = detect_inflection_points(ny_data_raw)
    current_live_es = float(np.asarray(es_data['Close'])[-1])
    
    # --- TAB 1: STRUCTURAL MAP ---
    with tab_map:
        st.markdown("### PRIOR NY SESSION & CONE PROJECTION")
        target_9am = get_target_time(target_date, 9)
        ladder = calculate_ladder(inflections, target_9am, offset=0) # Map shows raw ES
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_metric_card("Live ES", f"{current_live_es:.2f}")
        with c2: render_metric_card("Cone Rate", f"{RATE_PER_CANDLE} pt/30m", "#cbd5e1")
        with c3: render_metric_card("Target Projection", target_9am.strftime("%H:%M CT"), "#f59e0b")
        with c4: render_metric_card("Structural Lines", str(len(ladder)), "#c084fc")

        chart_col, ladder_col = st.columns([1.5, 1])
        with chart_col:
            st.markdown("<br>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Candlestick(x=ny_data_raw.index, open=ny_data_raw['Open'], high=ny_data_raw['High'], low=ny_data_raw['Low'], close=ny_data_raw['Close'])])
            fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0), height=600, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        with ladder_col:
            render_spatial_ruler(ladder, current_live_es)

    # --- TAB 2: ASIAN SESSION ---
    with tab_asian:
        st.markdown("### PROP FIRM SCALPING FRAMEWORK (6:00 PM - 7:00 PM CT)")
        target_6pm = get_target_time(target_date, 18)
        asian_ladder = calculate_ladder(inflections, target_6pm, offset=0)
        
        col_calc, col_ladder = st.columns([1, 1.5])
        with col_calc:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.markdown("<h4 class='orbitron' style='color: #f59e0b;'>RISK CALCULATOR</h4>", unsafe_allow_html=True)
            daily_limit = st.number_input("Prop Firm Daily Loss Limit ($)", value=2500, step=100)
            risk_pct = st.slider("Max Risk per Trade (%)", 1, 10, 3)
            stop_pts = st.number_input("Stop Loss Distance (Points)", value=5.0, step=0.5)
            pt_value = 50.0 # ES Point Value
            
            max_risk_dollars = daily_limit * (risk_pct / 100)
            risk_per_contract = stop_pts * pt_value
            max_contracts = math.floor(max_risk_dollars / risk_per_contract) if risk_per_contract > 0 else 0
            
            st.markdown("---")
            render_metric_card("Max Contracts (ES)", str(max_contracts), "#10b981" if max_contracts > 0 else "#e11d48")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_ladder:
            st.markdown("<h4 class='orbitron'>6:00 PM ES PROJECTION</h4>", unsafe_allow_html=True)
            render_spatial_ruler(asian_ladder, current_live_es)

    # --- TAB 3: NY SESSION ---
    with tab_ny:
        st.markdown("### SPX 0DTE OPTIONS ENGINE (9:00 AM CT)")
        current_spx = current_live_es - manual_offset
        ny_ladder = calculate_ladder(inflections, target_9am, offset=manual_offset)
        
        signal, reason, css_class = generate_ny_signal(ny_ladder, current_spx)
        
        st.markdown(f"<div class='{css_class}'><h2 class='orbitron' style='margin:0;'>SIGNAL: {signal}</h2><p class='rajdhani' style='margin:5px 0 0 0; font-size:1.2rem;'>{reason}</p></div><br>", unsafe_allow_html=True)
        
        c_conf, c_options = st.columns(2)
        with c_conf:
            st.markdown("#### 5-FACTOR CONFLUENCE")
            f1 = st.checkbox("1. Asian Alignment (+1)", help="Did Asian session trade in the same direction as the NY signal?")
            f2 = st.checkbox("2. London Sweep Confirmed (+1)", help="Did London sweep Asian highs/lows before reversing?")
            f3 = st.checkbox("3. 8:30 AM Data Absorbed/Aligned (+1)", help="Did economic data move in trade direction?")
            f4 = st.checkbox("4. Opening Drive Aligned (+1)", help="Is the first 15-min candle driving in trade direction?")
            f5 = st.checkbox("5. Line Cluster (+1)", help="Are 3+ lines within 15pts?")
            
            score = sum([f1, f2, f3, f4, f5])
            size = "100% (3 Contracts)" if score >= 4 else "75% (2 Contracts)" if score >= 3 else "50% (1 Contract)" if score >= 2 else "NO TRADE"
            color = "#10b981" if score >= 3 else "#f59e0b" if score >= 2 else "#e11d48"
            render_metric_card(f"Score: {score}/5", f"Position: {size}", color)

        with c_options:
            st.markdown("#### PREMIUM PROJECTION (Black-Scholes)")
            vix = st.number_input("VIX (Implied Volatility %)", value=15.0, step=0.5) / 100
            
            if signal in ["CALL", "PUT"]:
                strike = round((current_spx + 20) / 5) * 5 if signal == "CALL" else round((current_spx - 20) / 5) * 5
                time_entry = 6.0 / 24.0 # Roughly 6 hours left in session
                opt_type = 'C' if signal == "CALL" else 'P'
                
                prem_entry = bs_premium(current_spx, strike, time_entry, 0.0525, vix, opt_type)
                
                st.markdown(f"**Target Strike:** {strike} {signal}")
                st.markdown(f"**Estimated Entry Premium:** ${prem_entry:.2f} per share (${prem_entry * 100:.2f} per contract)")
            else:
                st.info("Awaiting valid directional signal to calculate premiums.")

if __name__ == "__main__":
    main()
