# ─────────────────────────────────────────────────────────────────────────────
#  Dr David’s Market Mind – UI Revamp – Part 1/3
# ─────────────────────────────────────────────────────────────────────────────
import json, base64, streamlit as st
from datetime import datetime, date, time, timedelta
from copy import deepcopy
import pandas as pd

# ── CONSTANTS & ICONS ───────────────────────────────────────────────────────
PAGE_TITLE = "Dr David’s Market Mind"
PAGE_ICON  = "📈"
VERSION    = "1.5.7"

BASE_SLOPES = {
    "SPX_HIGH": -0.2792, "SPX_CLOSE": -0.2792, "SPX_LOW": -0.2792,
    "TSLA": -0.1508, "NVDA": -0.0485, "AAPL": -0.0750,
    "MSFT": -0.17, "AMZN": -0.03, "GOOGL": -0.07,
    "META": -0.035, "NFLX": -0.23,
}
ICONS = {
    "SPX":"🧭","TSLA":"🚗","NVDA":"🧠","AAPL":"🍎",
    "MSFT":"🪟","AMZN":"📦","GOOGL":"🔍",
    "META":"📘","NFLX":"📺"
}

# ── GLOBAL SESSION STATE ─────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.update(
        theme="dark",
        slopes=deepcopy(BASE_SLOPES),
        presets={},
        contract_anchor=None,
        contract_slope=None,
        contract_price=None)

if st.query_params.get("s"):
    try:
        st.session_state.slopes.update(
            json.loads(base64.b64decode(st.query_params["s"][0]).decode()))
    except Exception:
        pass

# ── STREAMLIT PAGE CONFIG ───────────────────────────────────────────────────
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS (centralized branding + glassmorphism) ───────────────────────
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

:root {
  --font: 'Inter', sans-serif;
  --radius: 14px;
  --shadow: 0 8px 32px rgba(0,0,0,.25);
}

body {
  font-family: var(--font);
  background: #0f0f0f;
  color: #e5e5e5;
}

[data-testid="stApp"] {
  background: linear-gradient(135deg, #1e1e2f 0%, #16161d 100%);
}

/* --- animated header --- */
@keyframes slideFade {
  from {transform: translateY(-25px); opacity: 0;}
  to   {transform: translateY(0);    opacity: 1;}
}

.banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--radius);
  padding: 1.2rem 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
  animation: slideFade .6s ease-out;
  text-align: center;
}

.banner h1 {
  margin: 0;
  font-weight: 800;
  font-size: 2.4rem;
  letter-spacing: -.5px;
}

/* --- glass cards --- */
.glass-card {
  background: rgba(255,255,255,.06);
  backdrop-filter: blur(10px) saturate(200%);
  border: 1px solid rgba(255,255,255,.12);
  border-radius: var(--radius);
  padding: 1.4rem 1.2rem;
  box-shadow: var(--shadow);
  transition: transform .25s ease;
}

.glass-card:hover {
  transform: translateY(-6px);
}

/* --- responsive grid --- */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.2rem;
  margin-bottom: 2rem;
}

/* --- sidebar tweaks --- */
[data-testid="stSidebar"] {
  background: rgba(0,0,0,.25);
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="banner">
      <h1>{PAGE_TITLE}</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── RESPONSIVE CARD HELPER ────────────────────────────────────────────────────
def glass_card(kind: str, sym: str, title: str, value: float):
    color = {"high":"#10b981","close":"#3b82f6","low":"#ef4444"}.get(kind, "#888")
    st.markdown(
        f"""
        <div class="glass-card">
          <div style="display:flex;align-items:center;">
            <div style="font-size:2.2rem;margin-right:.8rem;">{sym}</div>
            <div>
              <div style="font-size:.9rem;opacity:.7;">{title}</div>
              <div style="font-size:1.8rem;font-weight:800;color:{color};">{value:.2f}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
# ────────────────────────────── SIDEBAR ──────────────────────────────────────
with st.sidebar:
    # 1. Theme toggle (persisted & animated)
    st.markdown("### 🎨 Theme")
    col_dark, col_light = st.columns(2)
    if col_dark.button("🌙 Dark", key="btn_dark", use_container_width=True):
        st.session_state.theme = "dark"
        st.rerun()
    if col_light.button("☀️ Light", key="btn_light", use_container_width=True):
        st.session_state.theme = "light"
        st.rerun()

    st.divider()

    # 2. Forecast date (with weekday label)
    fcast_date = st.date_input("📅 Forecast Date", value=date.today() + timedelta(days=1))
    wd = fcast_date.weekday()
    day_grp = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][wd]
    st.caption(f"Selected weekday: **{day_grp}**")

    st.divider()

    # 3. Slopes panel – collapsible, but open by default
    with st.expander("📉 Slopes", expanded=True):
        for key in list(st.session_state.slopes):
            st.session_state.slopes[key] = st.slider(
                key, -1.0, 1.0, st.session_state.slopes[key], 0.0001,
                key=f"slope_{key}")

    # 4. Presets – streamlined
    with st.expander("💾 Presets"):
        nm = st.text_input("Name", placeholder="My preset…")
        if st.button("Save", key="save_preset", use_container_width=True):
            if nm.strip():
                st.session_state.presets[nm] = deepcopy(st.session_state.slopes)
                st.success(f"Saved **{nm}**")
        if st.session_state.presets:
            sel = st.selectbox("Load preset", list(st.session_state.presets))
            if st.button("Load", key="load_preset", use_container_width=True):
                st.session_state.slopes.update(st.session_state.presets[sel])
                st.rerun()

    # 5. Share link – copy-friendly
    share_qs = base64.b64encode(json.dumps(st.session_state.slopes).encode()).decode()
    st.write("🔗 Share link")
    st.code(f"?s={share_qs}", language=None)
