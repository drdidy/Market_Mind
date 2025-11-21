# spx_prophet_app.py
# SPX Prophet — Light Mode, Rail + EM + Contract Planner

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time as dtime
from typing import Tuple, Optional

APP_NAME = "SPX Prophet"
TAGLINE = "Where Structure Becomes Foresight."
SLOPE_MAG = 0.475          # underlying rail slope (pts per 30 minutes)
CONTRACT_FACTOR = 0.3      # conservative factor to map SPX move → contract move
BASE_DATE = datetime(2000, 1, 1, 15, 0)


# ===============================
# STUNNING LIGHT MODE UI
# ===============================

def inject_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(ellipse 1800px 1200px at 20% 10%, rgba(99, 102, 241, 0.08), transparent 60%),
          radial-gradient(ellipse 1600px 1400px at 80% 90%, rgba(59, 130, 246, 0.08), transparent 60%),
          radial-gradient(circle 1200px at 50% 50%, rgba(167, 139, 250, 0.05), transparent),
          linear-gradient(180deg, #ffffff 0%, #f8fafc 30%, #f1f5f9 60%, #f8fafc 100%);
        background-attachment: fixed;
        color: #0f172a;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .block-container {
        padding-top: 3.5rem;
        padding-bottom: 4rem;
        max-width: 1400px;
    }

    /* CENTERED APP TITLE */
    .app-header {
        text-align: center;
        margin-bottom: 1rem;
    }
    .app-header-title {
        font-size: 2.2rem;
        font-weight: 900;
        font-family: 'Poppins', sans-serif;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #1e293b 0%, #6366f1 40%, #3b82f6 70%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .app-header-tagline {
        font-size: 1rem;
        color: #64748b;
        font-weight: 500;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.08), transparent 70%),
            linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
        border-right: 2px solid rgba(99, 102, 241, 0.15);
        box-shadow:
            8px 0 40px rgba(99, 102, 241, 0.08),
            4px 0 20px rgba(0, 0, 0, 0.03);
    }

    [data-testid="stSidebar"] h3 {
        font-size: 1.6rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #6366f1 0%, #3b82f6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
        letter-spacing: -0.04em;
    }

    [data-testid="stSidebar"] hr {
        margin: 1.5rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(99, 102, 241, 0.3) 20%,
            rgba(59, 130, 246, 0.5) 50%,
            rgba(99, 102, 241, 0.3) 80%,
            transparent 100%);
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
    }

    [data-testid="stSidebar"] h4 {
        color: #6366f1;
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }

    /* HERO */
    .hero-header {
        position: relative;
        background:
            radial-gradient(ellipse at top left, rgba(99, 102, 241, 0.12), transparent 60%),
            radial-gradient(ellipse at bottom right, rgba(59, 130, 246, 0.12), transparent 60%),
            linear-gradient(135deg, #ffffff, #fafbff);
        border-radius: 32px;
        padding: 32px 40px;
        margin-bottom: 32px;
        border: 2px solid rgba(99, 102, 241, 0.2);
        box-shadow:
            0 24px 70px -12px rgba(99, 102, 241, 0.15),
            0 12px 32px -8px rgba(0, 0, 0, 0.08),
            inset 0 2px 4px rgba(255, 255, 255, 0.9),
            inset 0 -2px 4px rgba(99, 102, 241, 0.05);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .hero-header-left {
        max-width: 70%;
    }

    .hero-title {
        font-size: 2.7rem;
        font-weight: 900;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1e293b 0%, #6366f1 40%, #3b82f6 70%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.05em;
        line-height: 1.1;
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        margin-top: 8px;
        font-weight: 500;
        font-family: 'Poppins', sans-serif;
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 16px;
        border-radius: 100px;
        background:
            linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.12)),
            #ffffff;
        border: 2px solid rgba(16, 185, 129, 0.3);
        font-size: 0.8rem;
        font-weight: 700;
        color: #059669;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        box-shadow:
            0 8px 24px rgba(16, 185, 129, 0.15),
            inset 0 1px 2px rgba(255, 255, 255, 0.8);
        margin-bottom: 12px;
    }

    .status-indicator::before {
        content: '';
        width: 9px;
        height: 9px;
        border-radius: 999px;
        background: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.6);
    }

    .hero-right-chip {
        padding: 10px 16px;
        border-radius: 16px;
        background: #fff;
        border: 1px solid rgba(148, 163, 184, 0.4);
        color: #475569;
        font-size: 0.85rem;
        box-shadow:
            0 8px 24px rgba(148, 163, 184, 0.25),
            inset 0 1px 2px rgba(255, 255, 255, 0.9);
    }

    /* CARDS */
    .spx-card {
        position: relative;
        background:
            radial-gradient(circle at 8% 8%, rgba(99, 102, 241, 0.08), transparent 50%),
            radial-gradient(circle at 92% 92%, rgba(59, 130, 246, 0.08), transparent 50%),
            linear-gradient(135deg, #ffffff, #fefeff);
        border-radius: 28px;
        border: 2px solid rgba(99, 102, 241, 0.16);
        box-shadow:
            0 24px 70px -12px rgba(99, 102, 241, 0.12),
            0 12px 32px -8px rgba(0, 0, 0, 0.06),
            inset 0 2px 4px rgba(255, 255, 255, 0.9);
        padding: 28px 30px;
        margin-bottom: 28px;
        transition: all 0.35s ease;
        overflow: hidden;
    }

    .spx-card:hover {
        transform: translateY(-6px);
        border-color: rgba(99, 102, 241, 0.35);
        box-shadow:
            0 36px 90px -16px rgba(99, 102, 241, 0.22),
            0 18px 40px -10px rgba(0, 0, 0, 0.10),
            inset 0 2px 5px rgba(255, 255, 255, 1);
    }

    .spx-card h4 {
        font-size: 1.7rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1e293b 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 10px 0;
        letter-spacing: -0.03em;
    }

    .icon-large {
        font-size: 2.6rem;
        background: linear-gradient(135deg, #6366f1, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        display: block;
        text-shadow: 0 6px 18px rgba(99, 102, 241, 0.3);
    }

    .spx-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 999px;
        border: 1px solid rgba(99, 102, 241, 0.3);
        background:
            linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(59, 130, 246, 0.10)),
            #ffffff;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #6366f1;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .spx-sub {
        color: #475569;
        font-size: 0.98rem;
        line-height: 1.7;
        font-weight: 400;
    }

    .section-header {
        font-size: 1.5rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1e293b 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 2.2rem 0 1rem 0;
        padding-bottom: 0.7rem;
        border-bottom: 2px solid transparent;
        border-image: linear-gradient(90deg, #6366f1, #3b82f6, transparent) 1;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .section-header::before {
        content: '';
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, #6366f1, #3b82f6);
        box-shadow:
            0 0 16px rgba(99, 102, 241, 0.6),
            0 3px 9px rgba(99, 102, 241, 0.3);
    }

    /* METRICS */
    .spx-metric {
        position: relative;
        padding: 22px 20px;
        border-radius: 22px;
        background:
            radial-gradient(circle at top left, rgba(99, 102, 241, 0.10), transparent 70%),
            linear-gradient(135deg, #ffffff, #fefeff);
        border: 1px solid rgba(99, 102, 241, 0.25);
        box-shadow:
            0 18px 46px rgba(99, 102, 241, 0.14),
            0 8px 18px rgba(0, 0, 0, 0.04),
            inset 0 1px 3px rgba(255, 255, 255, 0.9);
    }

    .spx-metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #64748b;
        font-weight: 700;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .spx-metric-label::before {
        content: '●';
        color: #6366f1;
        font-size: 0.55rem;
    }

    .spx-metric-value {
        font-size: 1.7rem;
        font-weight: 900;
        font-family: 'JetBrains Mono', monospace;
        background: linear-gradient(135deg, #1e293b 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
    }

    /* BUTTONS */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #3b82f6 50%, #06b6d4 100%);
        color: #ffffff;
        border-radius: 999px;
        border: none;
        padding: 12px 26px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.08em;
        box-shadow:
            0 14px 30px rgba(99, 102, 241, 0.25),
            0 6px 14px rgba(0, 0, 0, 0.08),
            inset 0 1px 2px rgba(255, 255, 255, 0.3);
        cursor: pointer;
        transition: all 0.25s ease;
        text-transform: uppercase;
    }

    .stButton>button:hover, .stDownloadButton>button:hover {
        transform: translateY(-2px);
        box-shadow:
            0 16px 36px rgba(99, 102, 241, 0.32),
            0 8px 18px rgba(0, 0, 0, 0.10),
            inset 0 1px 3px rgba(255, 255, 255, 0.4);
    }

    /* INPUTS */
    .stNumberInput>div>div>input,
    .stTimeInput>div>div>input {
        background: #ffffff !important;
        border: 2px solid rgba(99, 102, 241, 0.20) !important;
        border-radius: 16px !important;
        color: #0f172a !important;
        padding: 10px 14px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
        box-shadow:
            0 4px 14px rgba(99, 102, 241, 0.08),
            inset 0 1px 2px rgba(255, 255, 255, 0.8) !important;
    }

    .stRadio>div {
        gap: 12px;
    }
    .stRadio>div>label {
        background: #ffffff;
        padding: 10px 20px;
        border-radius: 999px;
        border: 2px solid rgba(148, 163, 184, 0.6);
        font-size: 0.9rem;
        font-weight: 600;
        color: #475569;
        box-shadow: 0 3px 10px rgba(148, 163, 184, 0.3);
        transition: all 0.2s ease;
    }
    .stRadio>div>label[data-selected="true"] {
        border-color: #6366f1;
        color: #6366f1;
        box-shadow:
            0 6px 16px rgba(99, 102, 241, 0.3),
            inset 0 1px 2px rgba(255, 255, 255, 0.9);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.96));
        padding: 8px;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.6);
        box-shadow:
            0 10px 26px rgba(148, 163, 184, 0.3),
            inset 0 1px 2px rgba(255, 255, 255, 0.9);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 999px;
        color: #64748b;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 8px 18px;
        border: none;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #3b82f6);
        color: #ffffff;
        box-shadow:
            0 8px 20px rgba(99, 102, 241, 0.35),
            inset 0 1px 2px rgba(255, 255, 255, 0.3);
    }

    .stDataFrame {
        border-radius: 20px;
        overflow: hidden;
        box-shadow:
            0 18px 50px rgba(148, 163, 184, 0.28),
            0 8px 22px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(148, 163, 184, 0.6);
    }

    .stDataFrame div[data-testid="StyledTable"] {
        font-variant-numeric: tabular-nums;
        font-size: 0.86rem;
        font-family: 'JetBrains Mono', monospace;
        background: #ffffff;
    }

    .muted {
        color: #475569;
        font-size: 0.94rem;
        line-height: 1.7;
        padding: 16px 18px;
        background:
            linear-gradient(135deg, rgba(148, 163, 184, 0.08), rgba(100, 116, 139, 0.06)),
            #ffffff;
        border-left: 4px solid #6366f1;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(148, 163, 184, 0.25);
        margin-top: 8px;
    }

    label {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        margin-bottom: 4px !important;
    }

    .app-footer {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(148, 163, 184, 0.6);
        text-align: center;
        color: #64748b;
        font-size: 0.92rem;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def hero():
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-header-title">{APP_NAME}</div>
            <div class="app-header-tagline">{TAGLINE}</div>
        </div>
        <div class="hero-header">
            <div class="hero-header-left">
                <div class="status-indicator">System Active</div>
                <h1 class="hero-title">Structure First. Emotion Last.</h1>
                <p class="hero-subtitle">
                    Two pivots define your rails. Expected move frames your day.
                    Contracts follow the structure, not the noise.
                </p>
            </div>
            <div class="hero-header-right">
                <div class="hero-right-chip">
                    Slope: <strong>{SLOPE_MAG:.3f} pts / 30 min</strong><br/>
                    Contract factor: <strong>{CONTRACT_FACTOR:.2f}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, sub: Optional[str] = None, badge: Optional[str] = None, icon: str = ""):
    st.markdown('<div class="spx-card">', unsafe_allow_html=True)
    if icon:
        st.markdown(f"<span class='icon-large'>{icon}</span>", unsafe_allow_html=True)
    if badge:
        st.markdown(f"<div class='spx-pill'>{badge}</div>", unsafe_allow_html=True)
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    if sub:
        st.markdown(f"<div class='spx-sub'>{sub}</div>", unsafe_allow_html=True)


def end_card():
    st.markdown("</div>", unsafe_allow_html=True)


def metric_card(label: str, value: str) -> str:
    return f"""
    <div class='spx-metric'>
        <div class='spx-metric-label'>{label}</div>
        <div class='spx-metric-value'>{value}</div>
    </div>
    """


def section_header(text: str):
    st.markdown(f"<h3 class='section-header'>{text}</h3>", unsafe_allow_html=True)


# ===============================
# TIME / BLOCK HELPERS
# ===============================

def make_dt_from_time(t: dtime) -> datetime:
    """Map a clock time onto the abstract grid using BASE_DATE as anchor."""
    if t.hour >= 15:
        return BASE_DATE.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
    else:
        next_day = BASE_DATE.date() + timedelta(days=1)
        return datetime(next_day.year, next_day.month, next_day.day, t.hour, t.minute)


def align_30min(dt: datetime) -> datetime:
    minute = 0 if dt.minute < 15 else (30 if dt.minute < 45 else 0)
    if dt.minute >= 45:
        dt = dt + timedelta(hours=1)
    return dt.replace(minute=minute, second=0, microsecond=0)


def blocks_from_base(dt: datetime) -> int:
    diff = dt - BASE_DATE
    return int(round(diff.total_seconds() / 1800.0))


def rth_slots() -> pd.DatetimeIndex:
    """30-minute grid for RTH 08:30–14:30 CT on the 'next day' of BASE_DATE."""
    next_day = BASE_DATE.date() + timedelta(days=1)
    start = datetime(next_day.year, next_day.month, next_day.day, 8, 30)
    end = datetime(next_day.year, next_day.month, next_day.day, 14, 30)
    return pd.date_range(start=start, end=end, freq="30min")


# ===============================
# UNDERLYING CHANNEL ENGINE
# ===============================

def build_channel(
    high_price: float,
    high_time: dtime,
    low_price: float,
    low_time: dtime,
    slope_sign: int,
) -> Tuple[pd.DataFrame, float]:
    """Main SPX rails channel from high and low pivots."""
    s = slope_sign * SLOPE_MAG
    dt_hi = align_30min(make_dt_from_time(high_time))
    dt_lo = align_30min(make_dt_from_time(low_time))
    k_hi = blocks_from_base(dt_hi)
    k_lo = blocks_from_base(dt_lo)

    b_top = high_price - s * k_hi
    b_bottom = low_price - s * k_lo
    channel_height = b_top - b_bottom

    slots = rth_slots()
    rows = []
    for dt in slots:
        k = blocks_from_base(dt)
        top = s * k + b_top
        bottom = s * k + b_bottom
        rows.append(
            {
                "Time": dt.strftime("%H:%M"),
                "Top Rail": round(top, 4),
                "Bottom Rail": round(bottom, 4),
            }
        )
    df = pd.DataFrame(rows)
    return df, round(channel_height, 4)


# ===============================
# EXPECTED MOVE CHANNEL ENGINE
# ===============================

def build_em_channel(
    anchor_price: float,
    anchor_time: dtime,
    em_value: float,
    direction: str,
) -> pd.DataFrame:
    """
    Expected move channel using EM size and an anchor price/time.

    direction: "Up" → slope +SLOPE_MAG oriented upward
               "Down" → slope -SLOPE_MAG oriented downward
    """
    s = SLOPE_MAG if direction == "Up" else -SLOPE_MAG

    dt_anchor = align_30min(make_dt_from_time(anchor_time))
    k_anchor = blocks_from_base(dt_anchor)

    # Lower rail anchored at anchor_price, other rail EM away in structural space
    base_line = anchor_price
    other_line = anchor_price + em_value if direction == "Up" else anchor_price - em_value

    b_base = base_line - s * k_anchor
    b_other = other_line - s * k_anchor

    slots = rth_slots()
    rows = []
    for dt in slots:
        k = blocks_from_base(dt)
        p1 = s * k + b_base
        p2 = s * k + b_other
        em_lower = min(p1, p2)
        em_upper = max(p1, p2)
        rows.append(
            {
                "Time": dt.strftime("%H:%M"),
                "EM Lower": round(em_lower, 4),
                "EM Upper": round(em_upper, 4),
            }
        )
    return pd.DataFrame(rows)


# ===============================
# CONTRACT ENGINE
# ===============================

def build_contract_projection(
    anchor_a_time: dtime,
    anchor_a_price: float,
    anchor_b_time: dtime,
    anchor_b_price: float,
) -> Tuple[pd.DataFrame, float]:
    """
    Straight line on same 30m grid for contract, using two structural anchor prices.
    """
    dt_a = align_30min(make_dt_from_time(anchor_a_time))
    dt_b = align_30min(make_dt_from_time(anchor_b_time))
    k_a = blocks_from_base(dt_a)
    k_b = blocks_from_base(dt_b)

    if k_a == k_b:
        slope = 0.0
    else:
        slope = (anchor_b_price - anchor_a_price) / (k_b - k_a)

    b_contract = anchor_a_price - slope * k_a

    slots = rth_slots()
    rows = []
    for dt in slots:
        k = blocks_from_base(dt)
        price = slope * k + b_contract
        rows.append(
            {
                "Time": dt.strftime("%H:%M"),
                "Contract Price": round(price, 4),
            }
        )
    df = pd.DataFrame(rows)
    return df, round(slope, 6)


# ===============================
# DAILY FORESIGHT HELPERS
# ===============================

def get_active_channel() -> Tuple[Optional[str], Optional[pd.DataFrame], Optional[float]]:
    mode = st.session_state.get("channel_mode")
    df_asc = st.session_state.get("channel_asc_df")
    df_desc = st.session_state.get("channel_desc_df")
    h_asc = st.session_state.get("channel_asc_height")
    h_desc = st.session_state.get("channel_desc_height")

    if mode == "Ascending":
        return "Ascending", df_asc, h_asc
    if mode == "Descending":
        return "Descending", df_desc, h_desc
    if mode == "Both":
        scenario = st.selectbox(
            "Active scenario for Foresight",
            ["Ascending", "Descending"],
            index=0,
            key="foresight_scenario",
        )
        if scenario == "Ascending":
            return "Ascending", df_asc, h_asc
        else:
            return "Descending", df_desc, h_desc
    return None, None, None


def classify_day_quality(channel_height: float) -> str:
    if channel_height is None or channel_height <= 0:
        return "Unknown"
    if channel_height < 40:
        return "Avoid (too tight)"
    if channel_height < 80:
        return "Caution (compressed)"
    return "Tradeable (ample range)"


def classify_time_window(time_str: str) -> str:
    h, m = map(int, time_str.split(":"))
    if h < 10:
        return "Open Window"
    if h < 12:
        return "Mid Session"
    return "Late Session"


# ===============================
# MAIN APP
# ===============================

def main():
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    # Sidebar
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.caption(TAGLINE)
        st.markdown("---")

        st.markdown("#### Core Parameters")
        st.write(f"Rails slope: **{SLOPE_MAG} pts / 30m**")
        st.write(f"Contract factor: **{CONTRACT_FACTOR:.2f} × SPX move**")

        st.markdown("---")
        st.markdown("#### Notes")
        st.caption(
            "Underlying: 16:00–17:00 CT maintenance\n\n"
            "Contracts: 16:00–19:00 CT maintenance\n\n"
            "RTH projection grid: 08:30–14:30 CT (30m blocks)."
        )

    hero()

    tabs = st.tabs(
        [
            "🧱 Rails and EM Setup",
            "📐 Contract Line Setup",
            "🔮 Daily Foresight",
            "ℹ️ About",
        ]
    )

    # ==========================
    # TAB 1 — RAILS + EM
    # ==========================
    with tabs[0]:
        card(
            "Rails and Expected Move Setup",
            "Define your underlying channel from pivots and overlay the expected move channel that frames the day.",
            badge="Structure Engine",
            icon="🧱",
        )

        section_header("⚙️ Underlying Pivots (Channel)")
        st.markdown(
            "<div class='spx-sub'>"
            "Use the key swing high and low that define the overnight channel. "
            "Times are flexible — you decide which 30-minute pivots matter."
            "</div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### High Pivot")
            high_price = st.number_input(
                "High pivot price",
                value=5200.0,
                step=0.25,
                key="pivot_high_price",
            )
            high_time = st.time_input(
                "High pivot time (CT)",
                value=dtime(19, 30),
                step=1800,
                key="pivot_high_time",
            )
        with c2:
            st.markdown("#### Low Pivot")
            low_price = st.number_input(
                "Low pivot price",
                value=5100.0,
                step=0.25,
                key="pivot_low_price",
            )
            low_time = st.time_input(
                "Low pivot time (CT)",
                value=dtime(3, 0),
                step=1800,
                key="pivot_low_time",
            )

        section_header("📊 Channel Regime")
        mode = st.radio(
            "Select your channel mode",
            ["Ascending", "Descending", "Both"],
            index=0,
            key="channel_mode",
            horizontal=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn = st.columns([1, 3])[0]
        with col_btn:
            if st.button("⚡ Build Rails", key="build_channel_btn", use_container_width=True):
                # Ascending
                if mode in ("Ascending", "Both"):
                    df_asc, h_asc = build_channel(
                        high_price=high_price,
                        high_time=high_time,
                        low_price=low_price,
                        low_time=low_time,
                        slope_sign=+1,
                    )
                    st.session_state["channel_asc_df"] = df_asc
                    st.session_state["channel_asc_height"] = h_asc
                else:
                    st.session_state["channel_asc_df"] = None
                    st.session_state["channel_asc_height"] = None

                # Descending
                if mode in ("Descending", "Both"):
                    df_desc, h_desc = build_channel(
                        high_price=high_price,
                        high_time=high_time,
                        low_price=low_price,
                        low_time=low_time,
                        slope_sign=-1,
                    )
                    st.session_state["channel_desc_df"] = df_desc
                    st.session_state["channel_desc_height"] = h_desc
                else:
                    st.session_state["channel_desc_df"] = None
                    st.session_state["channel_desc_height"] = None

                st.success("Rails generated. Check projections below and in Daily Foresight.")

        df_asc = st.session_state.get("channel_asc_df")
        df_desc = st.session_state.get("channel_desc_df")
        h_asc = st.session_state.get("channel_asc_height")
        h_desc = st.session_state.get("channel_desc_height")

        section_header("📊 Underlying Rails • RTH 08:30–14:30 CT")

        if df_asc is None and df_desc is None:
            st.info("Build at least one rails channel to see projections.")
        else:
            if df_asc is not None:
                st.markdown(
                    "<h4 style='font-size:1.2rem; margin:16px 0;'>📈 Ascending Channel</h4>",
                    unsafe_allow_html=True,
                )
                c_top = st.columns([3, 1])
                with c_top[0]:
                    st.dataframe(df_asc, use_container_width=True, hide_index=True, height=350)
                with c_top[1]:
                    st.markdown(
                        metric_card("Channel Height", f"{h_asc:.2f} pts"),
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "Download CSV",
                        df_asc.to_csv(index=False).encode(),
                        "spx_ascending_rails.csv",
                        "text/csv",
                        key="dl_asc_channel",
                        use_container_width=True,
                    )

            if df_desc is not None:
                st.markdown(
                    "<h4 style='font-size:1.2rem; margin:24px 0 16px;'>📉 Descending Channel</h4>",
                    unsafe_allow_html=True,
                )
                c_bot = st.columns([3, 1])
                with c_bot[0]:
                    st.dataframe(df_desc, use_container_width=True, hide_index=True, height=350)
                with c_bot[1]:
                    st.markdown(
                        metric_card("Channel Height", f"{h_desc:.2f} pts"),
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "Download CSV",
                        df_desc.to_csv(index=False).encode(),
                        "spx_descending_rails.csv",
                        "text/csv",
                        key="dl_desc_channel",
                        use_container_width=True,
                    )

        end_card()

        # EM CHANNEL SECTION
        card(
            "Expected Move Channel",
            "Use the market's daily expected move as a sloped channel anchored to your chosen price.",
            badge="EM Channel",
            icon="📊",
        )

        section_header("📈 EM Inputs")
        c1, c2, c3 = st.columns(3)
        with c1:
            em_value = st.number_input(
                "Expected Move (points)",
                value=80.0,
                step=1.0,
                key="em_value",
            )
        with c2:
            em_anchor_price = st.number_input(
                "EM anchor price",
                value=5200.0,
                step=0.5,
                key="em_anchor_price",
            )
        with c3:
            em_anchor_time = st.time_input(
                "EM anchor time (CT)",
                value=dtime(17, 0),
                step=1800,
                key="em_anchor_time",
            )

        em_direction = st.radio(
            "EM orientation",
            ["Up", "Down"],
            index=0,
            key="em_direction",
            horizontal=True,
        )

        col_btn_em = st.columns([1, 3])[0]
        with col_btn_em:
            if st.button("⚡ Build EM Channel", key="build_em_btn", use_container_width=True):
                df_em = build_em_channel(
                    anchor_price=em_anchor_price,
                    anchor_time=em_anchor_time,
                    em_value=em_value,
                    direction=em_direction,
                )
                st.session_state["em_df"] = df_em
                st.session_state["em_value"] = em_value
                st.session_state["em_direction"] = em_direction
                st.success("Expected move channel generated for RTH grid.")

        df_em = st.session_state.get("em_df")
        if df_em is None:
            st.info("Build the EM channel to see EM projections.")
        else:
            st.markdown(
                "<h4 style='font-size:1.2rem; margin:20px 0;'>🎯 EM Channel • RTH 08:30–14:30 CT</h4>",
                unsafe_allow_html=True,
            )
            st.dataframe(df_em, use_container_width=True, hide_index=True, height=350)
        end_card()

    # ==========================
    # TAB 2 — CONTRACT LINE
    # ==========================
    with tabs[1]:
        card(
            "Contract Line Setup",
            "Anchor a straight contract line on the same grid so you can map rail moves into realistic option targets.",
            badge="Contract Engine",
            icon="📐",
        )

        ph_time: dtime = st.session_state.get("pivot_high_time", dtime(19, 30))
        pl_time: dtime = st.session_state.get("pivot_low_time", dtime(3, 0))

        section_header("⚓ Anchor A — Contract Origin")
        anchor_a_source = st.radio(
            "Use which time for Anchor A",
            ["High pivot time", "Low pivot time", "Custom time"],
            index=0,
            key="contract_anchor_a_source",
            horizontal=True,
        )

        if anchor_a_source == "High pivot time":
            anchor_a_time = ph_time
            st.markdown(
                f"<div class='muted'>Anchor A time set to high pivot time: "
                f"<b>{anchor_a_time.strftime('%H:%M')}</b> CT</div>",
                unsafe_allow_html=True,
            )
        elif anchor_a_source == "Low pivot time":
            anchor_a_time = pl_time
            st.markdown(
                f"<div class='muted'>Anchor A time set to low pivot time: "
                f"<b>{anchor_a_time.strftime('%H:%M')}</b> CT</div>",
                unsafe_allow_html=True,
            )
        else:
            anchor_a_time = st.time_input(
                "Custom Anchor A time (CT)",
                value=dtime(1, 0),
                step=1800,
                key="contract_anchor_a_time_custom",
            )

        anchor_a_price = st.number_input(
            "Contract price at Anchor A time",
            value=10.0,
            step=0.1,
            key="contract_anchor_a_price",
        )

        section_header("⚓ Anchor B — Second Contract Point")
        c1, c2 = st.columns(2)
        with c1:
            anchor_b_time = st.time_input(
                "Anchor B time (CT)",
                value=dtime(7, 30),
                step=1800,
                key="contract_anchor_b_time",
            )
        with c2:
            anchor_b_price = st.number_input(
                "Contract price at Anchor B time",
                value=8.0,
                step=0.1,
                key="contract_anchor_b_price",
            )

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn = st.columns([1, 3])[0]
        with col_btn:
            if st.button("⚡ Build Contract Line", key="build_contract_btn", use_container_width=True):
                try:
                    df_contract, slope_contract = build_contract_projection(
                        anchor_a_time=anchor_a_time,
                        anchor_a_price=anchor_a_price,
                        anchor_b_time=anchor_b_time,
                        anchor_b_price=anchor_b_price,
                    )
                    st.session_state["contract_df"] = df_contract
                    st.session_state["contract_slope"] = slope_contract
                    st.success("Contract line generated across RTH grid.")
                except Exception as e:
                    st.error(f"Error generating contract projection: {e}")

        df_contract = st.session_state.get("contract_df")
        slope_contract = st.session_state.get("contract_slope")

        section_header("📊 Contract Projection • RTH 08:30–14:30 CT")

        if df_contract is None:
            st.info("Build a contract projection to see projected prices.")
        else:
            c_top = st.columns([3, 1])
            with c_top[0]:
                st.dataframe(df_contract, use_container_width=True, hide_index=True, height=350)
            with c_top[1]:
                st.markdown(
                    metric_card("Contract Slope", f"{slope_contract:+.4f} / 30m"),
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Download CSV",
                    df_contract.to_csv(index=False).encode(),
                    "contract_projection.csv",
                    "text/csv",
                    key="dl_contract",
                    use_container_width=True,
                )
        end_card()

    # ==========================
    # TAB 3 — DAILY FORESIGHT
    # ==========================
    with tabs[2]:
        card(
            "Daily Foresight",
            "Rails, EM channel, and contract line combined into one simple map and a trade planner.",
            badge="Foresight",
            icon="🔮",
        )

        df_mode, df_ch, h_ch = get_active_channel()
        df_contract = st.session_state.get("contract_df")
        df_em = st.session_state.get("em_df")
        em_value = st.session_state.get("em_value")

        if df_ch is None or h_ch is None:
            st.warning("No active rails channel found. Build rails in the first tab.")
            end_card()
        else:
            # Merge everything on Time
            merged = df_ch.copy()
            if df_em is not None:
                merged = merged.merge(df_em, on="Time", how="left")
            if df_contract is not None:
                merged = merged.merge(df_contract, on="Time", how="left")

            # Add windows and contract targets using factor
            if "Contract Price" in merged.columns:
                base = merged["Contract Price"].astype(float)
            else:
                base = pd.Series([float("nan")] * len(merged))

            long_t1_delta = CONTRACT_FACTOR * 0.2 * h_ch
            long_t2_delta = CONTRACT_FACTOR * 0.3 * h_ch

            merged["Window"] = merged["Time"].apply(classify_time_window)
            merged["Contract T1 Long"] = (base + long_t1_delta).round(2)
            merged["Contract T2 Long"] = (base + long_t2_delta).round(2)
            merged["Contract T1 Short"] = (base - long_t1_delta).round(2)
            merged["Contract T2 Short"] = (base - long_t2_delta).round(2)

            # SUMMARY
            section_header("📊 Structure Summary")
            day_quality = classify_day_quality(h_ch)
            contract_full = CONTRACT_FACTOR * h_ch

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    metric_card("Day Quality", day_quality),
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    metric_card("Channel Height", f"{h_ch:.2f} pts"),
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    metric_card("Contract Move / Full Swing", f"{contract_full:.2f} units"),
                    unsafe_allow_html=True,
                )

            if em_value is not None:
                st.markdown(
                    "<div class='muted'>"
                    f"Expected move entered: <b>{em_value:.2f} pts</b>. "
                    "Use it as the outer frame for what the day is allowed to do."
                    "</div>",
                    unsafe_allow_html=True,
                )

            # INSIDE CHANNEL PLAY
            section_header("📈 Inside Channel Play (Clean Swing)")

            st.markdown(
                f"""
                <div class='spx-sub'>
                  <p><strong style='color:#6366f1;'>Long idea</strong> → Buy at bottom rail, aim for top rail.</p>
                  <ul style='margin-left:20px;'>
                    <li>Underlying move ≈ <strong style='color:#10b981;'>{h_ch:.2f} pts</strong></li>
                    <li>Contract expectation (full swing) ≈ <strong style='color:#10b981;'>{contract_full:.2f} units</strong></li>
                    <li>Base take profit bands:
                      <ul style='margin-left:18px;'>
                        <li>T1 ≈ 0.2 × contract swing</li>
                        <li>T2 ≈ 0.3 × contract swing (push only if price runs clean)</li>
                      </ul>
                    </li>
                  </ul>

                  <p><strong style='color:#6366f1;'>Short idea</strong> → Sell at top rail, aim for bottom rail.</p>
                  <ul style='margin-left:20px;'>
                    <li>Same size of move in the opposite direction on both SPX and the contract estimate.</li>
                  </ul>

                  <p style='margin-top:8px; color:#64748b;'>
                    This is a structural expectation from your rails, not a full options model.
                    Real P and L can overshoot when volatility and skew help you.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # TRADE PLANNER
            section_header("🎯 Trade Planner")

            times = merged["Time"].tolist()
            if times and "Contract Price" in merged.columns:
                col_side, col_entry, col_exit = st.columns(3)
                with col_side:
                    side = st.radio(
                        "Direction",
                        ["Call (long)", "Put (short)"],
                        index=0,
                        key="planner_side",
                        horizontal=False,
                    )
                with col_entry:
                    entry_time = st.selectbox(
                        "Entry time (when rail touch is expected)",
                        times,
                        index=0,
                        key="planner_entry_time",
                    )
                with col_exit:
                    exit_time = st.selectbox(
                        "Exit time",
                        times,
                        index=min(len(times) - 1, 4),
                        key="planner_exit_time",
                    )

                entry_row = merged[merged["Time"] == entry_time].iloc[0]
                exit_row = merged[merged["Time"] == exit_time].iloc[0]

                entry_contract = float(entry_row["Contract Price"])
                exit_contract = float(exit_row["Contract Price"])

                # Also show structural T1/T2 around entry
                entry_t1_long = float(entry_row["Contract T1 Long"])
                entry_t2_long = float(entry_row["Contract T2 Long"])
                entry_t1_short = float(entry_row["Contract T1 Short"])
                entry_t2_short = float(entry_row["Contract T2 Short"])

                pnl_raw = exit_contract - entry_contract
                if side.startswith("Put"):
                    pnl_side = -pnl_raw
                else:
                    pnl_side = pnl_raw

                c1p, c2p, c3p = st.columns(3)
                with c1p:
                    st.markdown(
                        metric_card("Entry Contract", f"{entry_contract:.2f}"),
                        unsafe_allow_html=True,
                    )
                with c2p:
                    st.markdown(
                        metric_card("Exit Contract", f"{exit_contract:.2f}"),
                        unsafe_allow_html=True,
                    )
                with c3p:
                    st.markdown(
                        metric_card("Projected P&L (structural)", f"{pnl_side:+.2f} units"),
                        unsafe_allow_html=True,
                    )

                # Show suggested T1/T2 for the chosen side
                if side.startswith("Call"):
                    t1 = entry_t1_long
                    t2 = entry_t2_long
                else:
                    t1 = entry_t1_short
                    t2 = entry_t2_short

                st.markdown(
                    f"""
                    <div class='muted'>
                      <strong>Suggested contract targets from structure:</strong><br/>
                      Entry at <b>{entry_contract:.2f}</b> at <b>{entry_time}</b>.<br/>
                      T1 ≈ <b>{t1:.2f}</b> (lock core profit)<br/>
                      T2 ≈ <b>{t2:.2f}</b> (runner only if price stays clean in your favor).<br/><br/>
                      Compare these to what the actual market gives you. Any extra above these levels is
                      the volatility and skew bonus for the day.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info(
                    "Build a contract line in the second tab to unlock the trade planner targets."
                )

            # TIME-ALIGNED MAP
            section_header("🗺️ Time-Aligned Map")

            st.caption(
                "Every row is a 30-minute slot in RTH. "
                "If SPX tags a rail around that time, this shows the structural contract baseline "
                "and conservative T1 / T2 bands for calls and puts."
            )

            # Order columns for readability
            cols_order = []
            for col in ["Time", "Window", "Top Rail", "Bottom Rail", "EM Upper", "EM Lower",
                        "Contract Price", "Contract T1 Long", "Contract T2 Long",
                        "Contract T1 Short", "Contract T2 Short"]:
                if col in merged.columns:
                    cols_order.append(col)
            show_df = merged[cols_order]
            st.dataframe(show_df, use_container_width=True, hide_index=True, height=500)

            st.markdown(
                "<div class='muted'><strong>Reading the map:</strong> "
                "The table is not predicting where price will be. "
                "It simply tells you what your structure expects <em>if</em> a rail interaction "
                "happens at a given time. You then compare that with what the market actually paid "
                "you on the contract and learn how volatility behaved.</div>",
                unsafe_allow_html=True,
            )

            end_card()

    # ==========================
    # TAB 4 — ABOUT
    # ==========================
    with tabs[3]:
        card("About SPX Prophet", TAGLINE, badge="Overview", icon="ℹ️")
        st.markdown(
            """
            <div class='spx-sub'>
            <p>SPX Prophet is built around a simple structural idea:</p>

            <p style='font-size:1.1rem; color:#6366f1; font-weight:600; margin:16px 0;'>
            Two pivots define the rails. The expected move frames the outer walls.
            Your contract line is just the translation of that structure into option space.
            </p>

            <ul style='margin-left:22px;'>
                <li>Rails use a uniform slope of <strong>±0.475 points per 30 minutes</strong>.</li>
                <li>You pick the swing high and low that really matter for that overnight structure.</li>
                <li>The expected move is applied as a sloped channel, not a flat horizontal line.</li>
                <li>Contracts follow a straight structural line between two anchor prices.</li>
                <li>A conservative factor (here <strong>0.30</strong>) turns channel height into realistic contract targets.</li>
            </ul>

            <p style='margin-top:18px;'>
            The goal is not to predict every tick. The goal is to give you a calm, repeatable map so that
            when SPX returns to your rails, you already know what you expect the contract to be worth and where
            you plan to get paid.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='muted'>"
            "<strong>Note:</strong> You can tighten or loosen the contract factor over time as you collect data. "
            "Starting lower, as we do here, makes it easier to consistently hit your targets and build confidence."
            "</div>",
            unsafe_allow_html=True,
        )
        end_card()

    st.markdown(
        "<div class='app-footer'>© 2025 SPX Prophet • Where Structure Becomes Foresight.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()