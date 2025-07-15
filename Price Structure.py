DRSPX Professional Platform v5.0 - Fixed

-----------------------------------------------------------------------------

A streamlined, fully-ASCII version that runs on vanilla Streamlit 1.33+

Duplicate UI blocks removed, single sidebar maintained, and all 30‑minute time

inputs converted to dropdown select‑boxes.

-----------------------------------------------------------------------------

import json import uuid from datetime import datetime, date, time, timedelta

import numpy as np import pandas as pd import streamlit as st

═══════════════════════════════════════════════════════════════════════════════

CORE CONFIGURATION

═══════════════════════════════════════════════════════════════════════════════

APP_CONFIG = { "name": "DRSPX Professional", "version": "5.0", "tagline": "Advanced SPX Forecasting Platform", "icon": "📊", }

BASE_SLOPES = { "SPX_HIGH": -0.2792, "SPX_CLOSE": -0.2792, "SPX_LOW": -0.2792, "TSLA": -0.1508, "NVDA": -0.0485, "AAPL": -0.0750, "MSFT": -0.17, "AMZN": -0.03, "GOOGL": -0.07, "META": -0.035, "NFLX": -0.23, }

INSTRUMENTS = { "SPX": { "name": "S&P 500 Index", "icon": "📈", "color": "#FFD700", "pages": ["Dashboard", "Analysis", "Risk", "Performance"], }, "TSLA": { "name": "Tesla Inc", "icon": "🚗", "color": "#E31E24", "pages": ["Overview", "Signals", "Technical", "History"], }, "NVDA": { "name": "NVIDIA Corp", "icon": "🧠", "color": "#76B900", "pages": ["Overview", "Signals", "Technical", "History"], }, "AAPL": { "name": "Apple Inc", "icon": "🍎", "color": "#007AFF", "pages": ["Overview", "Signals", "Technical", "History"], }, "MSFT": { "name": "Microsoft Corp", "icon": "💻", "color": "#00BCF2", "pages": ["Overview", "Signals", "Technical", "History"], }, "AMZN": { "name": "Amazon.com", "icon": "📦", "color": "#FF9900", "pages": ["Overview", "Signals", "Technical", "History"], }, "GOOGL": { "name": "Alphabet Inc", "icon": "🔍", "color": "#4285F4", "pages": ["Overview", "Signals", "Technical", "History"], }, "META": { "name": "Meta Platforms", "icon": "📱", "color": "#1877F2", "pages": ["Overview", "Signals", "Technical", "History"], }, "NFLX": { "name": "Netflix Inc", "icon": "🎬", "color": "#E50914", "pages": ["Overview", "Signals", "Technical", "History"], }, }

═══════════════════════════════════════════════════════════════════════════════

SESSION INITIALISATION

═══════════════════════════════════════════════════════════════════════════════

def deep_copy(obj): if isinstance(obj, dict): return {k: deep_copy(v) for k, v in obj.items()} if isinstance(obj, list): return [deep_copy(i) for i in obj] return obj

if "app_session" not in st.session_state: st.session_state.update( { "app_session": str(uuid.uuid4()), "theme": "dark", "slopes": deep_copy(BASE_SLOPES), "current_instrument": "SPX", "current_page": "Dashboard", "forecast_date": date.today() + timedelta(days=1), } )

═══════════════════════════════════════════════════════════════════════════════

PAGE CONFIG & THEME HELPER

═══════════════════════════════════════════════════════════════════════════════

st.set_page_config( page_title=f"{APP_CONFIG['name']} {APP_CONFIG['version']}", page_icon=APP_CONFIG["icon"], layout="wide", )

def apply_theme(): if st.session_state["theme"] == "light": st.markdown( """<style> body, .stApp {background:#ffffff;color:#1e293b;} </style>""", unsafe_allow_html=True, )

apply_theme()

═══════════════════════════════════════════════════════════════════════════════

UTILITY: TIME SLOT DROPDOWN

═══════════════════════════════════════════════════════════════════════════════

def generate_time_slots(slot_type="spx"): if slot_type == "spx": start = datetime(2025, 1, 1, 8, 30) count = 11 else: start = datetime(2025, 1, 1, 7, 30) count = 13 return [ (start + timedelta(minutes=30 * i)).strftime("%H:%M") for i in range(count) ]

def time_selectbox(label, default, slot_type, key): opts = generate_time_slots(slot_type) idx = opts.index(default.strftime("%H:%M")) if default.strftime("%H:%M") in opts else 0 val = st.selectbox(label, opts, idx, key=key) return datetime.strptime(val, "%H:%M").time()

═══════════════════════════════════════════════════════════════════════════════

SIMPLE FORECAST MATH (original logic unchanged)

═══════════════════════════════════════════════════════════════════════════════

def calc_blocks(anchor_dt, target_dt, is_spx=True): if is_spx: blocks = 0 t = anchor_dt while t < target_dt: if t.hour != 16: blocks += 1 t += timedelta(minutes=30) return blocks return max(0, int((target_dt - anchor_dt).total_seconds() // 1800))

def project_price(price, slope, blocks): return round(price + slope * blocks, 2)

═══════════════════════════════════════════════════════════════════════════════

SPX DASHBOARD (single page)

═══════════════════════════════════════════════════════════════════════════════

def spx_dashboard(): st.header("📈 S&P 500 Dashboard")

col1, col2, col3 = st.columns(3)
dec = 2
with col1:
    hp = st.number_input("High Price", value=6185.8, key="hp", format=f"%.{dec}f")
    ht = time_selectbox("High Time", time(11, 30), "spx", "ht")
with col2:
    cp = st.number_input("Close Price", value=6170.2, key="cp", format=f"%.{dec}f")
    ct = time_selectbox("Close Time", time(15, 0), "spx", "ct")
with col3:
    lp = st.number_input("Low Price", value=6130.4, key="lp", format=f"%.{dec}f")
    lt = time_selectbox("Low Time", time(13, 30), "spx", "lt")

if st.button("Generate Forecast"):
    target_date = st.session_state["forecast_date"]
    prev_day = target_date - timedelta(days=1)
    slots = generate_time_slots("spx")
    out = {}
    for label, price, slope_key, anchor_time in [
        ("High", hp, "SPX_HIGH", ht),
        ("Close", cp, "SPX_CLOSE", ct),
        ("Low", lp, "SPX_LOW", lt),
    ]:
        rows = []
        anchor_dt = datetime.combine(prev_day, anchor_time)
        slope = st.session_state["slopes"][slope_key]
        for ts in slots:
            hh, mm = map(int, ts.split(":"))
            tgt = datetime.combine(target_date, time(hh, mm))
            blocks = calc_blocks(anchor_dt, tgt, True)
            rows.append({"Time": ts, "Projected": project_price(price, slope, blocks)})
        out[label] = pd.DataFrame(rows)

    for lbl, df in out.items():
        st.subheader(f"{lbl} Anchor")
        st.dataframe(df, use_container_width=True)

═══════════════════════════════════════════════════════════════════════════════

SIDEBAR & NAVIGATION

═══════════════════════════════════════════════════════════════════════════════

with st.sidebar: st.title("⚙️ Control Center") theme = st.selectbox("Theme", ["dark", "light"], index=(0 if st.session_state["theme"]=="dark" else 1)) if theme != st.session_state["theme"]: st.session_state["theme"] = theme st.experimental_rerun()

Main content - only SPX dashboard to keep example minimal but functional

spx_dashboard()

