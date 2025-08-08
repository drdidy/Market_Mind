
# Dr Didy Market Mind — Streamlit-Only, No Charts (World-Class UI)
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dtime
import json
from io import StringIO

# ===============================
# THEME / CSS (Light & Dark)
# ===============================

def theme_css(mode: str):
    # Two full palettes with strong contrast for legibility
    if mode == "Dark":
        palette = {
            "bg": "#0b1020",
            "panel": "#11182a",
            "panel2": "#0f1526",
            "text": "#e7edf6",
            "muted": "#aab4c8",
            "accent": "#5bb0ff",
            "accent2": "#7cf6c5",
            "success": "#27b07a",
            "warn": "#f0b847",
            "danger": "#ff5964",
            "border": "rgba(255,255,255,0.12)",
            "shadow": "0 10px 34px rgba(0,0,0,0.45)"
        }
        gradient = "radial-gradient(1200px 800px at 25% 10%, #0e1a38 0%, #0b1020 45%, #070b15 100%)"
    else:
        palette = {
            "bg": "#f7f9fc",
            "panel": "#ffffff",
            "panel2": "#f1f5fb",
            "text": "#0b1020",
            "muted": "#5d6474",
            "accent": "#0b6cff",
            "accent2": "#0f9d58",
            "success": "#188a5b",
            "warn": "#c07b00",
            "danger": "#cc0f2f",
            "border": "rgba(9,16,32,0.12)",
            "shadow": "0 10px 34px rgba(6,11,20,0.08)"
        }
        gradient = "radial-gradient(1200px 800px at 25% 10%, #e9f0ff 0%, #f7f9fc 50%, #ffffff 100%)"

    return f"""
    <style>
    :root {{
      --bg: {palette["bg"]};
      --panel: {palette["panel"]};
      --panel-2: {palette["panel2"]};
      --text: {palette["text"]};
      --muted: {palette["muted"]};
      --accent: {palette["accent"]};
      --accent-2: {palette["accent2"]};
      --success: {palette["success"]};
      --warn: {palette["warn"]};
      --danger: {palette["danger"]};
      --border: {palette["border"]};
      --shadow: {palette["shadow"]};
    }}

    html, body, [data-testid="stAppViewContainer"] {{
      background: {gradient};
    }}

    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
      background: var(--panel);
      border-right: 1px solid var(--border);
    }}

    h1,h2,h3,h4,h5,h6,label,p,span,div {{
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }}

    .dd-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 16px 18px;
      transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    }}
    .dd-card:hover {{ transform: translateY(-2px); border-color: var(--accent); }}

    .dd-card__title {{ display:flex; align-items:center; gap:.5rem; margin-bottom:.25rem; }}
    .dd-card__sub {{ color: var(--muted); font-size: .92rem; margin-top: .15rem; }}

    .dd-pill {{
      display:inline-flex; align-items:center; gap:.4rem;
      padding: 2px 10px; border-radius:999px; border:1px solid var(--border);
      background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
      font-weight:600; font-size:.84rem; color: var(--text);
    }}

    .dd-section-title {{
      font-size: 1.1rem; font-weight:800; letter-spacing:.2px;
      display:flex; align-items:center; gap:.6rem; margin-bottom:.5rem;
    }}

    .dd-divider {{ height:1px; background: var(--border); margin:.5rem 0 1rem; }}

    .dd-list li {{ margin:.25rem 0; }}

    .dd-footer-note {{ color:var(--muted); font-size:.85rem; margin-top:.75rem; }}

    .metric-row {{ display:flex; gap:12px; flex-wrap:wrap; }}
    .metric {{ padding:12px 14px; border-radius:12px; border:1px solid var(--border); background:var(--panel-2); min-width:160px; }}
    .metric .k {{ font-size:.82rem; color:var(--muted); }}
    .metric .v {{ font-size:1.4rem; font-weight:800; letter-spacing:.3px; }}

    .stDownloadButton button {{
      background: linear-gradient(90deg, var(--accent), #6ee7ff);
      color: #071222; border: 0; border-radius: 12px; padding: 8px 14px; font-weight: 700;
      box-shadow: var(--shadow);
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{ filter:brightness(1.05); transform: translateY(-1px); }}

    .stDataFrame div[data-testid="StyledTable"] {{ font-variant-numeric: tabular-nums; }}
    </style>
    """

def inject_theme(mode: str):
    st.markdown(theme_css(mode), unsafe_allow_html=True)

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
    if "favorites" not in st.session_state:
        st.session_state.favorites = set()
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
# UTILS (No charts — calculations only)
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
        result.append({"Time": t, "Price": price})
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

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

# ===============================
# UI HELPERS (cards, metrics, downloads)
# ===============================
def card(title, sub=None, body_fn=None, badge=None):
    st.markdown('<div class="dd-card">', unsafe_allow_html=True)
    pill = f"<span class='dd-pill'>{badge}</span>" if badge else ""
    st.markdown(f"<div class='dd-card__title'>{pill}<h4 style='margin:0'>{title}</h4></div>", unsafe_allow_html=True)
    if sub:
        st.markdown(f"<div class='dd-card__sub'>{sub}</div>", unsafe_allow_html=True)
    st.markdown("<div class='dd-divider'></div>", unsafe_allow_html=True)
    if body_fn:
        body_fn()
    st.markdown('</div>', unsafe_allow_html=True)

def metric_grid(pairs):
    st.markdown("<div class='metric-row'>", unsafe_allow_html=True)
    for k,v in pairs:
        st.markdown(f"<div class='metric'><div class='k'>{k}</div><div class='v'>{v}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def table(df, key=None):
    st.dataframe(df, use_container_width=True, hide_index=True, key=key)

def download_buttons(df_map: dict):
    cols = st.columns(len(df_map))
    for i, (label, df) in enumerate(df_map.items()):
        with cols[i]:
            st.download_button(
                f"Download {label} CSV",
                data=df_to_csv_bytes(df),
                file_name=f"{label.lower().replace(' ','_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# ===============================
# SIDEBAR (Light/Dark + Presets + Favorites)
# ===============================
def sidebar(state):
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        theme = st.radio("App Mode", ["Dark", "Light"], index=0, help="Choose a high-contrast mode.")
        st.session_state.theme = theme

        st.markdown("### 📐 Base Slopes")
        for k, v in list(state.slopes.items()):
            state.slopes[k] = st.number_input(k, value=float(v), step=0.001, format="%.4f", key=f"slope_{k}")
        st.markdown("---")

        st.markdown("### ⭐ Presets")
        preset_name = st.text_input("Preset name", key="preset_name")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save Preset", use_container_width=True):
                if preset_name:
                    st.session_state.presets[preset_name] = {**state.slopes}
                    st.session_state.favorites.add(preset_name)
                    st.success(f"Saved preset: {preset_name}")
        with c2:
            if st.button("Load Preset", use_container_width=True):
                if preset_name and preset_name in st.session_state.presets:
                    state.slopes.update(st.session_state.presets[preset_name])
                    st.success(f"Loaded preset: {preset_name}")
                else:
                    st.warning("Preset not found.")

        if st.session_state.presets:
            st.markdown("#### Favorites")
            for name in sorted(st.session_state.favorites):
                if name in st.session_state.presets:
                    if st.button(f"Apply • {name}", use_container_width=True, key=f"fav_{name}"):
                        state.slopes.update(st.session_state.presets[name])
                        st.toast(f"Applied preset: {name}")

        st.markdown("### ⏱️ Quick Times")
        st.caption("Speed-fill common times for inputs.")
        quick_times = ["07:30","08:30","10:30","12:00","14:30","15:00","17:00"]
        st.write(", ".join([f"`{t}`" for t in quick_times]))

# ===============================
# FORECASTING VIEWS (Tables only)
# ===============================
TICKERS = ["SPX","TSLA","NVDA","AAPL","MSFT","AMZN","GOOGL","META","NFLX"]

def render_spx_anchor_tables(state):
    slots = time_blocks("08:30","14:30",step_minutes=30, skip_maintenance=True)
    a = state.anchors["SPX"]
    df_high  = project_from_anchor(a["high"]["price"],  a["high"]["time"],  state.slopes["SPX_HIGH"],  slots, skip_maintenance=True)
    df_close = project_from_anchor(a["close"]["price"], a["close"]["time"], state.slopes["SPX_CLOSE"], slots, skip_maintenance=True)
    df_low   = project_from_anchor(a["low"]["price"],   a["low"]["time"],   state.slopes["SPX_LOW"],   slots, skip_maintenance=True)

    def body():
        metric_grid([
            ("High Anchor", f"{a['high']['price']} @ {a['high']['time']}"),
            ("Close Anchor", f"{a['close']['price']} @ {a['close']['time']}"),
            ("Low Anchor", f"{a['low']['price']} @ {a['low']['time']}"),
        ])
        st.markdown("#### From Close Anchor")
        table(df_close, key="spx_close")
        st.markdown("#### From High Anchor")
        table(df_high, key="spx_high")
        st.markdown("#### From Low Anchor")
        table(df_low, key="spx_low")
        download_buttons({"SPX_From_Close": df_close, "SPX_From_High": df_high, "SPX_From_Low": df_low})

    sub = "Projected lines computed in 30‑minute blocks. 16:00–17:00 maintenance block is excluded."
    card("SPX Anchor System", sub=sub, body_fn=body, badge="SPX")

def render_contract_line(state, ticker):
    step = 30
    skip = (ticker == "SPX")
    start = "08:30" if ticker=="SPX" else "07:30"
    end = "14:30"
    slots = time_blocks(start, end, step_minutes=step, skip_maintenance=skip)

    t1 = st.time_input("Low‑1 Time", value=pd.to_datetime(state.contract_params["t1"]).to_pydatetime().time(), key=f"t1_{ticker}").strftime("%H:%M")
    p1 = st.number_input("Low‑1 Price", value=float(state.contract_params["p1"]), step=0.1, key=f"p1_{ticker}")
    t2 = st.time_input("Low‑2 Time", value=pd.to_datetime(state.contract_params["t2"]).to_pydatetime().time(), key=f"t2_{ticker}").strftime("%H:%M")
    p2 = st.number_input("Low‑2 Price", value=float(state.contract_params["p2"]), step=0.1, key=f"p2_{ticker}")

    st.session_state.contract_params.update({"t1":t1,"p1":p1,"t2":t2,"p2":p2})

    slope = contract_slope(p1, t1, p2, t2, step_minutes=step, skip_maintenance=skip)
    try:
        blocks_bt = abs(round((p2-p1)/slope,2)) if slope != 0 else "∞"
    except Exception:
        blocks_bt = "—"

    rows = []
    for t in slots:
        db = blocks_between(t1, t, step_minutes=step, skip_maintenance=skip)
        price = round(p1 + slope * db, 4)
        rows.append({"Time": t, "Price": price})
    df_proj = pd.DataFrame(rows)

    def body():
        metric_grid([("Slope per 30‑min block", f"{slope:.4f}"), ("Blocks between points", f"{blocks_bt}")])
        table(df_proj, key=f"contract_{ticker}")
        download_buttons({f"{ticker}_Contract_Line": df_proj})

    card("Contract Line System", sub=f"{ticker} projection via two‑point slope.", body_fn=body, badge=ticker)

def render_inflection_channel(state):
    five_high = st.number_input("5 PM High", value=100.0, step=0.1, key="ich_high")
    five_low  = st.number_input("5 PM Low",  value=90.0, step=0.1, key="ich_low")
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

    def body():
        table(df_inflect, key="inflect")
        download_buttons({"Inflection_Channel": df_inflect})
        st.markdown("<div class='dd-footer-note'>Anchors: 17:00 extended‑hours candle high & low. Fixed slopes: +0.2214 / −0.4128 per 30‑min block.</div>", unsafe_allow_html=True)

    card("Inflection Point Channel", sub="Symmetrical entry/exit lines from the 17:00 candle.", body_fn=body, badge="SPX")

def render_fib_and_lookup(state, df_proj_for_lookup=None):
    c4, c5 = st.columns([1.1, 1])
    with c4:
        bl = st.number_input("Bounce Low", value=100.0, step=0.1, key="fib_low")
        bh = st.number_input("Bounce High", value=120.0, step=0.1, key="fib_high")
        fib = fibonacci_levels(bl, bh)
        def body_fib():
            table(fib, key="fib_table")
            download_buttons({"Fibonacci_Table": fib})
        card("Fibonacci Bounce Analyzer", sub="Full retracement table with 0.786 flagged as Algorithmic Entry Zone.", body_fn=body_fib, badge="FIB")

    with c5:
        def body_lookup():
            query_time = st.time_input("Lookup Time", value=pd.to_datetime("10:30").to_pydatetime().time(), key="lookup_time").strftime("%H:%M")
            if df_proj_for_lookup is not None and "Time" in df_proj_for_lookup.columns:
                match = df_proj_for_lookup.loc[df_proj_for_lookup["Time"]==query_time]
                if not match.empty:
                    price = match["Price"].iloc[0]
                    st.success(f"Projected contract price at {query_time}: **{price}**")
                else:
                    st.warning("Time not in today's projection slots.")
            else:
                st.info("Generate a Contract Line first to enable lookup.")
        card("Real‑Time Lookup (Contract Line)", sub="Instant projection for any time using current contract parameters.", body_fn=body_lookup, badge="TOOLS")

def render_ticker_page(ticker, state):
    st.markdown(f"### {ticker} • Forecasting Suite")

    # SPX Anchor System
    if ticker == "SPX":
        # Editable anchors (right at the top for clarity)
        with st.expander("Edit SPX Anchors", expanded=False):
            a = state.anchors["SPX"]
            a["high"]["price"] = st.number_input("High Anchor Price", value=float(a["high"]["price"]), step=0.1, key="spx_high_price")
            a["high"]["time"]  = st.time_input("High Time", value=pd.to_datetime(a["high"]["time"]).to_pydatetime().time(), key="spx_high_time").strftime("%H:%M")
            a["close"]["price"] = st.number_input("Close Anchor Price", value=float(a["close"]["price"]), step=0.1, key="spx_close_price")
            a["close"]["time"]  = st.time_input("Close Time", value=pd.to_datetime(a["close"]["time"]).to_pydatetime().time(), key="spx_close_time").strftime("%H:%M")
            a["low"]["price"] = st.number_input("Low Anchor Price", value=float(a["low"]["price"]), step=0.1, key="spx_low_price")
            a["low"]["time"]  = st.time_input("Low Time", value=pd.to_datetime(a["low"]["time"]).to_pydatetime().time(), key="spx_low_time").strftime("%H:%M")
            st.toast("SPX anchors updated.", icon="✅")

        render_spx_anchor_tables(state)

    # Contract Line
    render_contract_line(state, ticker)

    # Inflection Channel
    if ticker == "SPX":
        render_inflection_channel(state)

    # Fibonacci + Lookup
    step = 30
    skip = (ticker == "SPX")
    start = "08:30" if ticker=="SPX" else "07:30"
    end = "14:30"
    slots = time_blocks(start, end, step_minutes=step, skip_maintenance=skip)
    cp = st.session_state.contract_params
    slope = contract_slope(cp["p1"], cp["t1"], cp["p2"], cp["t2"], step_minutes=step, skip_maintenance=skip)
    rows = []
    for t in slots:
        db = blocks_between(cp["t1"], t, step_minutes=step, skip_maintenance=skip)
        price = round(cp["p1"] + slope * db, 4)
        rows.append({"Time": t, "Price": price})
    df_proj_lookup = pd.DataFrame(rows)

    render_fib_and_lookup(state, df_proj_for_lookup=df_proj_lookup)

# ===============================
# PLAYBOOKS
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
    "RTH Breaks: 30‑min close below anchor = prepare for breakdown",
    "Extended Hours: Recovery signals for next‑day strength",
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

def playbooks_hub():
    st.markdown("### Strategy Playbooks")

    cheat = pd.DataFrame([
        {"Ticker": k, "Best Days": v["days"], "Rationale": v["rationale"]}
        for k, v in BEST_TRADING_DAYS.items()
    ])

    card("Best Trading Days — Cheat Sheet", sub="High‑probability scheduling guidance per ticker.", body_fn=lambda: (table(cheat), download_buttons({"Best_Trading_Days": cheat})), badge="GUIDE")

    card("SPX Master Playbook", sub="Guiding principles and rules of engagement.", body_fn=lambda: (
        st.markdown("#### Golden Rules"),
        st.markdown("<ul class='dd-list'>" + "".join([f"<li>{r}</li>" for r in GOLDEN_RULES]) + "</ul>", unsafe_allow_html=True),
        st.markdown("#### Anchor Trading Rules"),
        st.markdown("<ul class='dd-list'>" + "".join([f"<li>{r}</li>" for r in ANCHOR_TRADING]) + "</ul>", unsafe_allow_html=True),
        st.markdown("#### Fibonacci Bounce Rules"),
        st.markdown("<ul class='dd-list'>" + "".join([f"<li>{r}</li>" for r in FIB_RULES]) + "</ul>", unsafe_allow_html=True),
        st.markdown("#### Contract Strategies"),
        st.markdown("<ul class='dd-list'>" + "".join([f"<li>{r}</li>" for r in CONTRACT_STRATS]) + "</ul>", unsafe_allow_html=True),
        st.markdown("#### Time Management"),
        st.markdown("<ul class='dd-list'>" + "".join([f"<li>{r}</li>" for r in TIME_MGMT]) + "</ul>", unsafe_allow_html=True),
        st.markdown("#### Universal Risk Management"),
        st.markdown("<ul class='dd-list'>" + "".join([f"<li>{r}</li>" for r in RISK_MGMT]) + "</ul>", unsafe_allow_html=True),
    ), badge="SPX")

    st.info("Individual stock playbooks can be extended with pre‑trade checklists, session timers, and performance trackers.")

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

    init_state()
    state = get_state()
    inject_theme(state.theme)

    # Header
    left, right = st.columns([1, 0.25])
    with left:
        st.markdown("## Dr Didy Market Mind")
        st.caption("Premium market forecasting • Strategy playbooks • Modern UX — Streamlit‑only edition")
    with right:
        st.markdown("<div class='dd-card'>", unsafe_allow_html=True)
        metric_grid([("Mode", state.theme), ("Presets", str(len(state.presets))), ("Favorites", str(len(state.favorites))) ])
        st.markdown("</div>", unsafe_allow_html=True)

    # Sidebar + tabs
    sidebar(state)
    tab1, tab2 = st.tabs(["📈 Forecasting Tools", "📚 Strategy Playbooks"])

    with tab1:
        sub_tabs = st.tabs(["SPX","TSLA","NVDA","AAPL","MSFT","AMZN","GOOGL","META","NFLX"])
        for i, tk in enumerate(["SPX","TSLA","NVDA","AAPL","MSFT","AMZN","GOOGL","META","NFLX"]):
            with sub_tabs[i]:
                render_ticker_page(tk, state)

    with tab2:
        playbooks_hub()

    st.markdown("<div class='dd-footer-note'>© 2025 Dr Didy Market Mind • Built with Streamlit</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()