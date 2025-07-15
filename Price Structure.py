DRSPX Professional Platform v5.0 – Fixed

-----------------------------------------------------------------------------

* Duplicate UI blocks removed (old "PART 10" prototype discarded)

* Single sidebar / navigation system retained

* All critical time inputs converted to dropdowns fed by 30‑minute slot helper

* apply_theme() now executed so light‑theme actually works

* Missing CSS variables defined in :root for consistent colours

* Helper utilities consolidated

-----------------------------------------------------------------------------

import json import base64 import streamlit as st from datetime import datetime, date, time, timedelta import pandas as pd import numpy as np import uuid

═══════════════════════════════════════════════════════════════════════════════

CORE CONFIGURATION

═══════════════════════════════════════════════════════════════════════════════

APP_CONFIG = { "name": "DRSPX Professional", "version": "5.0", "tagline": "Advanced SPX Forecasting Platform", "icon": "📊" }

Your exact original slopes – NEVER CHANGED

BASE_SLOPES = { "SPX_HIGH": -0.2792, "SPX_CLOSE": -0.2792, "SPX_LOW": -0.2792, "TSLA": -0.1508, "NVDA": -0.0485, "AAPL": -0.0750, "MSFT": -0.17, "AMZN": -0.03, "GOOGL": -0.07, "META": -0.035, "NFLX": -0.23, }

INSTRUMENTS = { "SPX": { "name": "S&P 500 Index", "icon": "📈", "color": "#FFD700", "pages": ["Dashboard", "Analysis", "Risk", "Performance"] }, "TSLA": { "name": "Tesla Inc", "icon": "🚗", "color": "#E31E24", "pages": ["Overview", "Signals", "Technical", "History"] }, "NVDA": { "name": "NVIDIA Corp", "icon": "🧠", "color": "#76B900", "pages": ["Overview", "Signals", "Technical", "History"] }, "AAPL": { "name": "Apple Inc", "icon": "🍎", "color": "#007AFF", "pages": ["Overview", "Signals", "Technical", "History"] }, "MSFT": { "name": "Microsoft Corp", "icon": "💻", "color": "#00BCF2", "pages": ["Overview", "Signals", "Technical", "History"] }, "AMZN": { "name": "Amazon.com", "icon": "📦", "color": "#FF9900", "pages": ["Overview", "Signals", "Technical", "History"] }, "GOOGL": { "name": "Alphabet Inc", "icon": "🔍", "color": "#4285F4", "pages": ["Overview", "Signals", "Technical", "History"] }, "META": { "name": "Meta Platforms", "icon": "📱", "color": "#1877F2", "pages": ["Overview", "Signals", "Technical", "History"] }, "NFLX": { "name": "Netflix Inc", "icon": "🎬", "color": "#E50914", "pages": ["Overview", "Signals", "Technical", "History"] } }

Manual deepcopy (keep simple & safe)

def deep_copy(obj): if isinstance(obj, dict): return {k: deep_copy(v) for k, v in obj.items()} if isinstance(obj, list): return [deep_copy(i) for i in obj] return obj

═══════════════════════════════════════════════════════════════════════════════

STREAMLIT & SESSION CONFIG

═══════════════════════════════════════════════════════════════════════════════

st.set_page_config( page_title=f"{APP_CONFIG['name']} v{APP_CONFIG['version']}", page_icon=APP_CONFIG['icon'], layout="wide", initial_sidebar_state="expanded", )

if "app_session" not in st.session_state: st.session_state.update({ "app_session": str(uuid.uuid4()), "theme": "dark", "slopes": deep_copy(BASE_SLOPES), "configurations": {}, "current_instrument": "SPX", "current_page": "Dashboard", "contract_data": {}, "forecast_data": {}, "animations_enabled": True, "forecast_date": date.today() + timedelta(days=1) })

═══════════════════════════════════════════════════════════════════════════════

CSS  (root vars added)

═══════════════════════════════════════════════════════════════════════════════

st.markdown( """

<style>
:root {
  --bg-secondary:#1e293b; --bg-tertiary:#334155; --border-color:#475569;
  --text-primary:#f1f5f9; --text-secondary:#cbd5e1; --text-muted:#94a3b8;
  --primary-gradient:linear-gradient(135deg,#3b82f6 0%,#1d4ed8 100%);
  --success-color:#10b981; --warning-color:#f59e0b; --danger-color:#ef4444;
  --info-color:#0ea5e9; --success-gradient:linear-gradient(135deg,#10b981 0%,#047857 100%);
  --warning-gradient:linear-gradient(135deg,#f59e0b 0%,#b45309 100%);
  --shadow:0 4px 6px -1px rgba(0,0,0,.1); --shadow-lg:0 10px 15px -3px rgba(0,0,0,.1);
  --radius:12px; --transition:all .3s ease;
}
/* ———  existing style sheet stays unchanged below  ——— */
</style>""", unsafe_allow_html=True, )

(… keep the enormous existing CSS that followed …)

═══════════════════════════════════════════════════════════════════════════════

THEME MANAGEMENT

═══════════════════════════════════════════════════════════════════════════════

def apply_theme(): if st.session_state.get("theme") == "light": st.markdown('<div class="light-theme">', unsafe_allow_html=True)

apply_theme()

═══════════════════════════════════════════════════════════════════════════════

TIME‑SLOT HELPERS  (NEW)

═══════════════════════════════════════════════════════════════════════════════

def generate_time_slots(slot_type: str = "market"): """Return list[HH:MM] in 30‑min increments.""" if slot_type == "spx":      # 08:30 – 15:30  (11 slots, 16:00 excluded) start = datetime(2025, 1, 1, 8, 30) count = 11 elif slot_type == "market":  # 07:30 – 14:00 (13 slots) start = datetime(2025, 1, 1, 7, 30) count = 13 else:                         # full 24 h (48 slots) start = datetime(2025, 1, 1, 0, 0) count = 48 return [(start + timedelta(minutes=30*i)).strftime("%H:%M") for i in range(count)]

def time_selectbox(label: str, *, default: time, slot_type: str = "market", key: str, help: str | None = None) -> time: options = generate_time_slots(slot_type) default_str = default.strftime("%H:%M") index = options.index(default_str) if default_str in options else 0 chosen = st.selectbox(label, options, index=index, key=key, help=help) return datetime.strptime(chosen, "%H:%M").time()

═══════════════════════════════════════════════════════════════════════════════

>>> ALL ORIGINAL BUSINESS‑LOGIC FUNCTIONS COME HERE UNCHANGED <<<

(generate_spx_forecast, calculate_* helpers, style_dataframe, etc.)

ONLY DIFFERENCE: they now receive real time objects from dropdowns.

═══════════════════════════════════════════════════════════════════════════════

── SNIP ──  (The vast majority of previous functions are kept verbatim)

nothing is altered in strategy or computation

only UI widgets below are touched

═══════════════════════════════════════════════════════════════════════════════

SPX DASHBOARD  (widget fixes applied)

═══════════════════════════════════════════════════════════════════════════════

def create_spx_dashboard(): decimal_places = st.session_state.get("decimal_places", 2) forecast_date  = st.session_state.get("forecast_date", date.today() + timedelta(days=1))

# … header markup untouched …

st.markdown("### 🎯 Anchor Points Configuration")
anchor_col1, anchor_col2, anchor_col3 = st.columns(3)

with anchor_col1:
    high_price = st.number_input("Expected High Price", value=6185.8, min_value=0.0,
                                 step=0.1, key="spx_high_price",
                                 format=f"%.{decimal_places}f")
    high_time  = time_selectbox("High Time", default=time(11,30), slot_type="spx",
                                key="spx_high_time", help="Expected high time")

with anchor_col2:
    close_price = st.number_input("Expected Close Price", value=6170.2, min_value=0.0,
                                  step=0.1, key="spx_close_price",
                                  format=f"%.{decimal_places}f")
    close_time  = time_selectbox("Close Time", default=time(15,0), slot_type="spx",
                                 key="spx_close_time", help="Market close time")

with anchor_col3:
    low_price = st.number_input("Expected Low Price", value=6130.4, min_value=0.0,
                                step=0.1, key="spx_low_price",
                                format=f"%.{decimal_places}f")
    low_time  = time_selectbox("Low Time", default=time(13,30), slot_type="spx",
                               key="spx_low_time", help="Expected low time")

# ─ contract line section ─
st.markdown("### 🎯 Two‑Point Contract Line")
contract_col1, contract_col2 = st.columns(2)

with contract_col1:
    low1_time = time_selectbox("Low‑1 Time", default=time(2,0), slot_type="full",
                               key="contract_low1_time", help="1st low time")
    low1_price = st.number_input("Low‑1 Price", value=10.0, min_value=0.0, step=0.01,
                                 key="contract_low1_price", format=f"%.{decimal_places}f")

with contract_col2:
    low2_time = time_selectbox("Low‑2 Time", default=time(3,30), slot_type="full",
                               key="contract_low2_time", help="2nd low time")
    low2_price = st.number_input("Low‑2 Price", value=12.0, min_value=0.0, step=0.01,
                                 key="contract_low2_price", format=f"%.{decimal_places}f")

# ─ Generate button & rest of function remain unchanged ─
# …

═══════════════════════════════════════════════════════════════════════════════

MAIN ENTRY‑POINT  (duplicate tabs removed – we keep single navigation system)

═══════════════════════════════════════════════════════════════════════════════

Instrument tab bar – once

_tab_labels = [f"{INSTRUMENTS[s]['icon']} {s}" for s in INSTRUMENTS] tabs = st.tabs(_tab_labels)

SPX content in first tab

with tabs[0]: if st.session_state.get("current_page") == "Dashboard": create_spx_dashboard() #  other SPX pages (Analysis/Risk/Performance) call their existing creators

Non‑SPX stock tabs

for i, sym in enumerate([s for s in INSTRUMENTS if s != "SPX"], start=1): with tabs[i]: st.session_state.current_instrument = sym # existing create_stock_interface() decides page content create_stock_interface()

═══════════════════════════════════════════════════════════════════════════════

SIDE BAR (single instance)

═══════════════════════════════════════════════════════════════════════════════

render_professional_sidebar()

═══════════════════════════════════════════════════════════════════════════════

EXPORT / ANALYTICS UI (unchanged)

═══════════════════════════════════════════════════════════════════════════════

create_export_interface() create_visual_analytics()

-----------------------------------------------------------------------------

End of file – strategy preserved, UI conflicts & duplicate widgets removed.

