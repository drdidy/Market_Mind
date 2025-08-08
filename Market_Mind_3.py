# Dr Didy Market Mind — Single-File Streamlit App (No Plotly)
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dtime

# ===============================
# THEME / CSS
# ===============================
THEME_CSS = '''
<style>
:root {
  --bg: #0b1220;
  --panel: #121a2a;
  --panel-2: #0f1524;
  --text: #e6edf7;
  --muted: #a7b0c0;
  --accent: #4da3ff;
  --accent-2: #7cf6c5;
  --success: #2fb67c;
  --warn: #f0b847;
  --danger: #ff5263;
  --shadow: 0 8px 30px rgba(0,0,0,0.35);
}

html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 800px at 20% 10%, #0d1831 0%, var(--bg) 40%, #0a0f1a 100%);
}

section.main > div { padding-top: 0.5rem; }

h1, h2, h3, h4, h5, h6, label, p, span, div {
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
}

[data-testid="stHeader"] { background: transparent; }

.dd-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  box-shadow: var(--shadow);
  padding: 16px 18px;
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}
.dd-card:hover {
  transform: translateY(-2px);
  border-color: rgba(125, 207, 255, 0.4);
  box-shadow: 0 10px 34px rgba(0,0,0,0.45);
}

.dd-metric { display: flex; justify-content: space-between; align-items: baseline; }
.dd-metric .label { color: var(--muted); font-size: 0.9rem; }
.dd-metric .value { font-size: 1.6rem; font-weight: 700; letter-spacing: 0.3px; }
.dd-metric .status { font-size: 0.9rem; opacity: 0.9; }

button[kind="primary"], .stButton>button {
  background: linear-gradient(90deg, var(--accent), #6ee7ff);
  color: #071222; border: 0; border-radius: 12px; padding: 8px 14px; font-weight: 700;
  box-shadow: var(--shadow);
}
.stButton>button:hover { filter: brightness(1.05); transform: translateY(-1px); }

.dd-badge {
  display: inline-block; padding: 2px 8px; border-radius: 999px;
  background: rgba(124, 246, 197, 0.15); color: var(--accent-2); font-weight: 600; font-size: 0.8rem;
}

[data-testid="stSidebar"] {
  background: var(--panel);
  border-right: 1px solid rgba(255,255,255,0.08);
}

hr { border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 8px 0 16px; }
</style>
'''

def inject_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)

def top_nav(title="Dr Didy Market Mind"):
    st.markdown(f"<h1 style='margin-bottom:0'>{title}</h1>", unsafe_allow_html=True)
    st.caption("Premium market forecasting • Strategy playbooks • Modern UX")

# ===============================
# CONSTANTS / SESSION STATE
# ===============================
BASE_SLOPES = {
    "SPX_HIGH": -0.2792, "SPX_CLOSE": -0.2792, "SPX_LOW": -0.2792,
    "TSLA": -0.1508, "NVDA": -0.0485, "AAPL": -0.0750,
    "MSFT": -0.17, "AMZN": -0.03, "GOOGL": -0.07,
    "META": -0.035, "NFLX": -0.23
}

DEFAULT_ANCHORS = {
    "SPX": {
        "high": {"price": 6185.8, "time": "11:30"},
        "close": {"price": 6170.2, "time": "15:00"},
        "low": {"price": 6130.4, "time": "13:30"},
    }
}

BEST_TRADING_DAYS = {
    "NVDA": {"days": "Tue / Thu", "rationale": "Highest volatility and option-flow mid-week"},
    "META": {"days": "Tue / Thu", "rationale": "News-feed reprice, AI headlines often drop Tue/Thu"},
    "TSLA": {"days": "Mon / Wed", "rationale": "Post-weekend gamma squeeze & mid-week momentum"},
    "AAPL": {"days": "Mon / Wed", "rationale": "Earnings drift & supply-chain headlines"},
    "AMZN": {"days": "Wed / Thu", "rationale": "Mid-week marketplace volume & OPEX flow"},
    "GOOGL": {"days": "Thu / Fri", "rationale": "Search-ad spend updates tilt end-week"},
    "NFLX": {"days": "Tue / Fri", "rationale": "Subscriber metrics chatter on Tue, positioning unwind on Fri"}
}

def init_state():
    if "theme" not in st.session_state:
        st.session_state.theme = "Dark"
    if "slopes" not in st.session_state:
        st.session_state.slopes = BASE_SLOPES.copy()
    if "presets" not in st.session_state:
        st.session_state.presets = {}
    if "contract_params" not in st.session_state:
        st.session_state.contract_params = {"t1": "02:00", "p1": 10.0, "t2": "03:30", "p2": 12.0}
    if "forecasts_generated" not in st.session_state:
        st.session_state.forecasts_generated = False
    if "selected_playbook" not in st.session_state:
        st.session_state.selected_playbook = "SPX Master Playbook"
    if "anchors" not in st.session_state:
        st.session_state.anchors = DEFAULT_ANCHORS

def get_state():
    return st.session_state

# ===============================
# UTILS
# ===============================
TIME_FMT = "%H:%M"

def parse_time(tstr: str) -> datetime:
    return datetime.combine(datetime.today().date(), datetime.strptime(tstr, TIME_FMT).time())

def time_blocks(start="08:30", end="14:30", step_minutes=30, skip_maintenance=False):
    t = parse_time(start)
    endt = parse_time(end)
    out = []
    while t <= endt:
        if not (skip_maintenance and t.time() >= dtime(16,0) and t.time() < dtime(17,0)):
            out.append(t.strftime(TIME_FMT))
        t += timedelta(minutes=step_minutes)
    return out

def blocks_between(t1: str, t2: str, step_minutes=30, skip_maintenance=False):
    times = time_blocks("00:00", "23:30", step_minutes, skip_maintenance)
    try:
        i1, i2 = times.index(t1), times.index(t2)
        return abs(i2 - i1)
    except ValueError:
        dt1, dt2 = parse_time(t1), parse_time(t2)
        return int(abs((dt2 - dt1).total_seconds()) // (step_minutes * 60))

def project_from_anchor(anchor_price: float, anchor_time: str, slope_per_block: float, slots: list, step_minutes=30, skip_maintenance=False):
    base_idx = time_blocks("00:00", "23:30", step_minutes, skip_maintenance).index(anchor_time)
    result = []
    for t in slots:
        idx = time_blocks("00:00", "23:30", step_minutes, skip_maintenance).index(t)
        delta_blocks = idx - base_idx
        price = round(anchor_price + slope_per_block * delta_blocks, 4)
        result.append({"time": t, "price": price})
    return pd.DataFrame(result)

def contract_slope(p1: float, t1: str, p2: float, t2: str, step_minutes=30, skip_maintenance=False):
    blocks = blocks_between(t1, t2, step_minutes, skip_maintenance)
    if blocks == 0:
        return 0.0
    return (p2 - p1) / blocks

def fibonacci_levels(low: float, high: float):
    diff = high - low
    levels = {
        "0.236": high - 0.236 * diff,
        "0.382": high - 0.382 * diff,
        "0.500": high - 0.500 * diff,
        "0.618": high - 0.618 * diff,
        "0.786": high - 0.786 * diff,
        "1.000": low
    }
    rows = [{"Level": k, "Price": round(v, 4), "Flag": "Algorithmic Entry Zone" if k == "0.786" else ""} for k, v in levels.items()]
    return pd.DataFrame(rows)

# ===============================
# UI COMPONENTS
# ===============================
def card(title, body, badge=None):
    st.markdown('<div class="dd-card">', unsafe_allow_html=True)
    if badge:
        st.markdown(f'<span class="dd-badge">{badge}</span>', unsafe_allow_html=True)
    st.markdown(f"#### {title}")
    body()
    st.markdown('</div>', unsafe_allow_html=True)

def metric(label, value, status=None):
    st.markdown('<div class="dd-metric">', unsafe_allow_html=True)
    st.markdown(f'<div class="label">{label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="value">{value}</div>', unsafe_allow_html=True)
    if status:
        st.markdown(f'<div class="status">{status}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def table(df, use_container_width=True):
    st.dataframe(df, use_container_width=use_container_width, hide_index=True)

def line_chart(df, x, y, name="Projection", anchors=None):
    # Streamlit's built-in chart (no Plotly)
    # Ensure the x column is the index for correct ordering
    df_plot = df[[x, y]].copy()
    df_plot = df_plot.set_index(x)
    st.line_chart(df_plot, height=380)
    # Show anchors context below as text since we can't annotate
    if anchors:
        desc = "; ".join([f"{a['label']} @ {a['time']} = {a['price']}" for a in anchors])
        st.caption(f"Anchors: {desc}")

# ===============================
# SIDEBAR
# ===============================
def sidebar_settings(state):
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        theme = st.radio("Theme", ["Dark"], index=0, help="Dark theme is optimized.")
        st.session_state.theme = theme

        st.markdown("### 📐 Base Slopes")
        for k, v in list(state.slopes.items()):
            state.slopes[k] = st.number_input(k, value=float(v), step=0.001, format="%.4f")
        st.markdown("—")
        preset_name = st.text_input("Preset name")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save Preset"):
                if preset_name:
                    st.session_state.presets[preset_name] = {**state.slopes}
                    st.success(f"Saved preset: {preset_name}")
        with c2:
            if st.button("Load Preset") and preset_name and preset_name in st.session_state.presets:
                state.slopes.update(st.session_state.presets[preset_name])
                st.success(f"Loaded preset: {preset_name}")

# ===============================
# STRATEGY TEXT
# ===============================
GOLDEN_RULES = [
    "Exit levels are exits — never entries",
    "Anchors are magnets, not timing signals",
    "Market will give you entry — don't force it",
    "Consistency beats perfection",
    "When in doubt, stay out",
    "SPX ignores 16:00–17:00 maintenance block"
]

ANCHOR_TRADING = [
    "RTH Breaks: 30-min close below anchor = prepare for breakdown",
    "Extended Hours: Recovery signals for next-day strength",
    "Mon/Wed/Fri: No anchor touches = potential sell day"
]

FIB_RULES = [
    "SPX line touch + bounce → contract often follows pattern",
    "0.786 retracement in next hour candle = algorithmic entry",
    "Confirm with confluence (time/volume/structure)"
]

CONTRACT_STRATS = [
    "Tuesday Play: Two overnight lows +$400–$500 to set slope",
    "Thursday Play: Wednesday pricing often telegraphs direction"
]

TIME_MGMT = [
    "Session timing: 9:30–10:00 range discovery",
    "Entries: 10:30–11:30 windows; avoid chop",
    "Mind volume patterns; confirm on multiple timeframes"
]

RISK_MGMT = [
    "Position Sizing: Risk ≤ 2% per idea; scale in thirds",
    "Stops: −15% hard stops; +25% trails; 15:45 time stops",
    "Context: Respect VIX, avoid earnings, observe FOMC",
    "Psychology: Daily loss limits; avoid revenge trades and euphoria",
    "Targets: ≥55% win rate, ≥1:1.5 risk/reward"
]

# ===============================
# FORECASTING VIEWS
# ===============================
TICKERS = ["SPX","TSLA","NVDA","AAPL","MSFT","AMZN","GOOGL","META","NFLX"]

def render_ticker_page(ticker, state):
    st.markdown(f"### {ticker} • Forecasting Suite")
    c1, c2, c3 = st.columns([1.2, 1, 1])

    # -------- SPX Anchor System --------
    if ticker == "SPX":
        with c1:
            st.markdown("#### SPX Anchor System")
            hcol, ccol, lcol = st.columns(3)
            with hcol:
                spx_high = st.number_input("High Anchor Price", value=float(state.anchors["SPX"]["high"]["price"]), step=0.1)
                spx_high_t = st.time_input("High Time", value=pd.to_datetime(state.anchors["SPX"]["high"]["time"]).to_pydatetime().time())
                spx_high_t = spx_high_t.strftime("%H:%M")
            with ccol:
                spx_close = st.number_input("Close Anchor Price", value=float(state.anchors["SPX"]["close"]["price"]), step=0.1)
                spx_close_t = st.time_input("Close Time", value=pd.to_datetime(state.anchors["SPX"]["close"]["time"]).to_pydatetime().time())
                spx_close_t = spx_close_t.strftime("%H:%M")
            with lcol:
                spx_low = st.number_input("Low Anchor Price", value=float(state.anchors["SPX"]["low"]["price"]), step=0.1)
                spx_low_t = st.time_input("Low Time", value=pd.to_datetime(state.anchors["SPX"]["low"]["time"]).to_pydatetime().time())
                spx_low_t = spx_low_t.strftime("%H:%M")

            slots = time_blocks("08:30","14:30",step_minutes=30, skip_maintenance=True)
            anchors = [
                {"label":"High", "time": spx_high_t, "price": spx_high},
                {"label":"Close", "time": spx_close_t, "price": spx_close},
                {"label":"Low", "time": spx_low_t, "price": spx_low},
            ]

            df_high = project_from_anchor(spx_high, spx_high_t, state.slopes["SPX_HIGH"], slots, skip_maintenance=True)
            df_close = project_from_anchor(spx_close, spx_close_t, state.slopes["SPX_CLOSE"], slots, skip_maintenance=True)
            df_low = project_from_anchor(spx_low, spx_low_t, state.slopes["SPX_LOW"], slots, skip_maintenance=True)

            st.markdown("**Projected Lines (30-min blocks; 16:00-17:00 maintenance skipped)**")
            st.write("From High")
            line_chart(df_high, "time", "price", name="From High", anchors=anchors)
            st.write("From Close")
            line_chart(df_close, "time", "price", name="From Close", anchors=anchors)
            st.write("From Low")
            line_chart(df_low, "time", "price", name="From Low", anchors=anchors)

            st.markdown("##### Projection Table (From Close Anchor)")
            table(df_close.rename(columns={"time":"Time","price":"Price"}))

    # -------- Contract Line System --------
    with c2:
        st.markdown("#### Contract Line System")
        t1 = st.time_input("Low-1 Time", value=pd.to_datetime(state.contract_params["t1"]).to_pydatetime().time()).strftime("%H:%M")
        p1 = st.number_input("Low-1 Price", value=float(state.contract_params["p1"]), step=0.1)
        t2 = st.time_input("Low-2 Time", value=pd.to_datetime(state.contract_params["t2"]).to_pydatetime().time()).strftime("%H:%M")
        p2 = st.number_input("Low-2 Price", value=float(state.contract_params["p2"]), step=0.1)

        st.session_state.contract_params.update({"t1":t1,"p1":p1,"t2":t2,"p2":p2})

        step = 30
        skip = (ticker == "SPX")
        start = "08:30" if ticker=="SPX" else "07:30"
        end = "14:30"
        slots = time_blocks(start, end, step_minutes=step, skip_maintenance=skip)
        slope = contract_slope(p1, t1, p2, t2, step_minutes=step, skip_maintenance=skip)
        try:
            blocks_bt = abs(round((p2-p1)/slope,2)) if slope != 0 else "∞"
        except Exception:
            blocks_bt = "—"
        st.caption(f"Slope per block: **{slope:.4f}** (blocks between points: {blocks_bt})")

        proj = []
        for t in slots:
            db = blocks_between(t1, t, step_minutes=step, skip_maintenance=skip)
            price = round(p1 + slope * db, 4)
            proj.append({"time": t, "price": price})
        df_proj = pd.DataFrame(proj)

        line_chart(df_proj, "time", "price", name="Contract Line")
        table(df_proj.rename(columns={"time":"Time","price":"Price"}))

    # -------- Inflection Point Channel --------
    with c3:
        st.markdown("#### Inflection Point Channel (from 17:00 candle)")
        five_high = st.number_input("5PM High", value=100.0, step=0.1)
        five_low = st.number_input("5PM Low", value=90.0, step=0.1)
        asc = +0.2214  # from 5pm low
        desc = -0.4128 # from 5pm high
        slots = time_blocks("07:00","14:30", step_minutes=30, skip_maintenance=True)
        rows = []
        for i, t in enumerate(slots):
            rows.append({
                "Time": t,
                "Exit/Entry (Ascending)": round(five_low + asc * (i+1), 4),
                "Entry/Exit (Descending)": round(five_high + desc * (i+1), 4)
            })
        df_inflect = pd.DataFrame(rows)
        table(df_inflect)

    st.divider()

    # -------- Fibonacci + Real-Time Lookup --------
    c4, c5 = st.columns([1.1, 1])
    with c4:
        st.markdown("#### Fibonacci Bounce Analyzer")
        bl = st.number_input("Bounce Low", value=100.0, step=0.1)
        bh = st.number_input("Bounce High", value=120.0, step=0.1)
        fib = fibonacci_levels(bl, bh)
        table(fib)

    with c5:
        st.markdown("#### Real-Time Lookup (Contract Line)")
        query_time = st.time_input("Lookup Time", value=pd.to_datetime("10:30").to_pydatetime().time()).strftime("%H:%M")
        try:
            price = df_proj.loc[df_proj["time"] == query_time, "price"].iloc[0]
            st.success(f"Projected contract price at {query_time}: **{price}**")
        except Exception:
            st.warning("Time not in today's projection slots.")

# ===============================
# PLAYBOOK VIEWS
# ===============================
def playbooks_hub():
    st.markdown("### Strategy Playbooks")

    cheat = pd.DataFrame([
        {"Ticker": k, "Best Days": v["days"], "Rationale": v["rationale"]}
        for k, v in BEST_TRADING_DAYS.items()
    ])
    card("Best Trading Days — Cheat Sheet", lambda: table(cheat))

    st.markdown("### SPX Master Playbook")
    card("Golden Rules", lambda: st.write("\n".join([f"• {r}" for r in GOLDEN_RULES])))
    card("Anchor Trading Rules", lambda: st.write("\n".join([f"• {r}" for r in ANCHOR_TRADING])))
    card("Fibonacci Bounce Rules", lambda: st.write("\n".join([f"• {r}" for r in FIB_RULES])))
    card("Contract Strategies", lambda: st.write("\n".join([f"• {r}" for r in CONTRACT_STRATS])))
    card("Time Management", lambda: st.write("\n".join([f"• {r}" for r in TIME_MGMT])))

    st.markdown("### Universal Risk Management")
    card("Risk Framework", lambda: st.write("\n".join([f"• {r}" for r in RISK_MGMT])))
    st.info("Individual stock playbooks can be expanded with historical stats, scheduler, and checklists.")

# ===============================
# APP ENTRY
# ===============================
def main():
    st.set_page_config(
        page_title="Dr Didy Market Mind",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    inject_theme()
    init_state()
    state = get_state()

    top_nav()

    # Sidebar settings
    sidebar_settings(state)

    # Tabs
    tab1, tab2 = st.tabs(["📈 Forecasting Tools", "📚 Strategy Playbooks"])

    with tab1:
        sub_tabs = st.tabs(TICKERS)
        for i, tk in enumerate(TICKERS):
            with sub_tabs[i]:
                render_ticker_page(tk, state)

    with tab2:
        playbooks_hub()

if __name__ == "__main__":
    main()