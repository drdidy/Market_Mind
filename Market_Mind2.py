#
# spx_prophet.py
# SPX Prophet — Institutional Edition
# Where Structure Becomes Foresight.

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time as dtime
from typing import Tuple, Optional

APP_NAME = "SPX Prophet"
TAGLINE = "Where Structure Becomes Foresight."
SLOPE_MAG = 0.475  # pts / 30min
BASE_DATE = datetime(2000, 1, 1, 15, 0)  # just for RTH date scaffolding


# ===============================
# ELEGANT LIGHT UI
# ===============================

def inject_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

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
        font-size: 1.8rem;
        font-weight: 900;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #6366f1 0%, #3b82f6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
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

    /* CENTERED HERO HEADER */
    .hero-header {
        position: relative;
        background:
            radial-gradient(ellipse at top left, rgba(99, 102, 241, 0.12), transparent 60%),
            radial-gradient(ellipse at bottom right, rgba(59, 130, 246, 0.12), transparent 60%),
            linear-gradient(135deg, #ffffff, #fafbff);
        border-radius: 32px;
        padding: 40px 56px;
        margin-bottom: 32px;
        border: 2px solid rgba(99, 102, 241, 0.2);
        box-shadow:
            0 32px 80px -12px rgba(99, 102, 241, 0.15),
            0 16px 40px -8px rgba(0, 0, 0, 0.08),
            inset 0 2px 4px rgba(255, 255, 255, 0.9),
            inset 0 -2px 4px rgba(99, 102, 241, 0.05);
        overflow: hidden;
        animation: heroGlow 6s ease-in-out infinite;
        text-align: center;
    }

    @keyframes heroGlow {
        0%, 100% { box-shadow: 0 32px 80px -12px rgba(99, 102, 241, 0.15), 0 16px 40px -8px rgba(0, 0, 0, 0.08); }
        50% { box-shadow: 0 32px 80px -12px rgba(99, 102, 241, 0.25), 0 16px 40px -8px rgba(99, 102, 241, 0.12); }
    }

    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6366f1, #3b82f6, #06b6d4, #3b82f6, #6366f1);
        background-size: 200% 100%;
        animation: shimmer 4s linear infinite;
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    .hero-title {
        font-size: 3.1rem;
        font-weight: 900;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1e293b 0%, #6366f1 40%, #3b82f6 70%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.05em;
        line-height: 1.1;
        animation: titleFloat 3s ease-in-out infinite;
    }

    @keyframes titleFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
    }

    .hero-subtitle {
        font-size: 1.25rem;
        color: #64748b;
        margin-top: 10px;
        font-weight: 500;
        font-family: 'Poppins', sans-serif;
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 18px;
        border-radius: 999px;
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
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(0.85); }
    }

    /* CARDS */
    .spx-card {
        position: relative;
        background:
            radial-gradient(circle at 8% 8%, rgba(99, 102, 241, 0.08), transparent 50%),
            radial-gradient(circle at 92% 92%, rgba(59, 130, 246, 0.08), transparent 50%),
            linear-gradient(135deg, #ffffff, #fefeff);
        border-radius: 28px;
        border: 1.5px solid rgba(148, 163, 184, 0.4);
        box-shadow:
            0 22px 60px -18px rgba(15, 23, 42, 0.25),
            0 10px 30px -16px rgba(15, 23, 42, 0.15),
            inset 0 1px 3px rgba(255, 255, 255, 0.9);
        padding: 28px 30px;
        margin-bottom: 28px;
        transition: all 0.35s ease;
        overflow: hidden;
    }

    .spx-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow:
            0 30px 70px -18px rgba(15, 23, 42, 0.35),
            0 16px 32px -18px rgba(99, 102, 241, 0.25),
            inset 0 1px 4px rgba(255, 255, 255, 1);
    }

    .spx-card h4 {
        font-size: 1.6rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1f2937 0%, #4f46e5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 10px 0;
        letter-spacing: -0.02em;
    }

    .icon-large {
        font-size: 2.6rem;
        background: linear-gradient(135deg, #4f46e5, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        display: inline-block;
    }

    .spx-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 18px;
        border-radius: 999px;
        border: 1.5px solid rgba(79, 70, 229, 0.25);
        background:
            linear-gradient(135deg, rgba(129, 140, 248, 0.18), rgba(59, 130, 246, 0.14)),
            #ffffff;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #4f46e5;
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
        font-size: 1.4rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1e293b 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 1.8rem 0 1.1rem 0;
        padding-bottom: 0.6rem;
        border-bottom: 2px solid rgba(148, 163, 184, 0.6);
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
            0 0 14px rgba(99, 102, 241, 0.7),
            0 4px 10px rgba(99, 102, 241, 0.25);
    }

    .spx-metric {
        padding: 22px 20px;
        border-radius: 20px;
        background:
            radial-gradient(circle at top left, rgba(129, 140, 248, 0.15), transparent 70%),
            #ffffff;
        border: 1.5px solid rgba(148, 163, 184, 0.6);
        box-shadow:
            0 16px 36px -20px rgba(15, 23, 42, 0.35),
            inset 0 1px 3px rgba(255, 255, 255, 0.9);
        transition: all 0.3s ease;
    }

    .spx-metric:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.6);
        box-shadow:
            0 22px 50px -24px rgba(79, 70, 229, 0.5),
            inset 0 1px 4px rgba(255, 255, 255, 1);
    }

    .spx-metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #64748b;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .spx-metric-value {
        font-size: 1.6rem;
        font-weight: 900;
        font-family: 'JetBrains Mono', monospace;
        background: linear-gradient(135deg, #111827 0%, #4f46e5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .muted {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.7;
        padding: 14px 16px;
        background:
            linear-gradient(135deg, rgba(148, 163, 184, 0.07), rgba(148, 163, 184, 0.03)),
            #ffffff;
        border-left: 3px solid #6366f1;
        border-radius: 10px;
        margin: 10px 0 4px 0;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
    }

    /* INPUTS */
    .stNumberInput>div>div>input,
    .stTimeInput>div>div>input {
        background: #ffffff !important;
        border: 1.5px solid rgba(148, 163, 184, 0.9) !important;
        border-radius: 14px !important;
        color: #0f172a !important;
        padding: 10px 12px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
        box-shadow:
            0 4px 14px rgba(15, 23, 42, 0.08),
            inset 0 1px 2px rgba(255, 255, 255, 0.9) !important;
        transition: all 0.2s ease !important;
    }

    .stNumberInput>div>div>input:focus,
    .stTimeInput>div>div>input:focus {
        border-color: #6366f1 !important;
        box-shadow:
            0 0 0 3px rgba(129, 140, 248, 0.25),
            0 8px 20px rgba(129, 140, 248, 0.25) !important;
        background: #f9fafb !important;
    }

    .stRadio>div {
        gap: 8px;
        flex-wrap: wrap;
    }

    .stRadio>div>label {
        background: #ffffff;
        padding: 8px 16px;
        border-radius: 999px;
        border: 1.5px solid rgba(148, 163, 184, 0.8);
        font-size: 0.9rem;
        font-weight: 600;
        color: #475569;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
        transition: all 0.2s ease;
    }

    .stRadio>div>label[data-selected="true"] {
        background: linear-gradient(135deg, rgba(129, 140, 248, 0.2), rgba(96, 165, 250, 0.18));
        border-color: #6366f1;
        color: #4f46e5;
        box-shadow:
            0 6px 16px rgba(129, 140, 248, 0.35),
            inset 0 1px 2px rgba(255, 255, 255, 0.9);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.98));
        padding: 8px;
        border-radius: 999px;
        border: 1.5px solid rgba(148, 163, 184, 0.7);
        box-shadow:
            0 12px 30px rgba(15, 23, 42, 0.16),
            inset 0 1px 2px rgba(255, 255, 255, 0.9);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 999px;
        color: #64748b;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 8px 20px;
        border: none;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #3b82f6);
        color: #ffffff;
        box-shadow:
            0 8px 24px rgba(79, 70, 229, 0.4),
            inset 0 1px 2px rgba(255, 255, 255, 0.5);
    }

    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #3b82f6 50%, #06b6d4 100%);
        color: #ffffff;
        border-radius: 999px;
        border: none;
        padding: 10px 22px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.08em;
        box-shadow:
            0 10px 24px rgba(79, 70, 229, 0.35),
            0 4px 12px rgba(15, 23, 42, 0.22);
        cursor: pointer;
        transition: all 0.25s ease;
        text-transform: uppercase;
    }

    .stButton>button:hover, .stDownloadButton>button:hover {
        transform: translateY(-2px);
        box-shadow:
            0 14px 32px rgba(79, 70, 229, 0.45),
            0 6px 16px rgba(15, 23, 42, 0.25);
    }

    .stDataFrame {
        border-radius: 20px;
        overflow: hidden;
        box-shadow:
            0 20px 50px rgba(15, 23, 42, 0.16),
            0 8px 20px rgba(15, 23, 42, 0.08);
        border: 1.5px solid rgba(148, 163, 184, 0.7);
    }

    .app-footer {
        margin-top: 3rem;
        padding-top: 1.2rem;
        border-top: 1.5px solid rgba(148, 163, 184, 0.7);
        text-align: center;
        color: #64748b;
        font-size: 0.9rem;
    }

    label {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        margin-bottom: 4px !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
        <div class="hero-header">
            <div class="status-indicator">Session Map Ready</div>
            <h1 class="hero-title">SPX Prophet</h1>
            <p class="hero-subtitle">Where Structure Becomes Foresight.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, sub: Optional[str] = None, badge: Optional[str] = None, icon: str = ""):
    st.markdown('<div class="spx-card">', unsafe_allow_html=True)
    if badge:
        st.markdown(f"<div class='spx-pill'>{badge}</div>", unsafe_allow_html=True)
    if icon:
        st.markdown(f"<span class='icon-large'>{icon}</span>", unsafe_allow_html=True)
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    if sub:
        st.markdown(f"<div class='spx-sub'>{sub}</div>", unsafe_allow_html=True)


def end_card():
    st.markdown("</div>", unsafe_allow_html=True)


def metric_card(label: str, value: str) -> str:
    return f"""
    <div class="spx-metric">
        <div class="spx-metric-label">{label}</div>
        <div class="spx-metric-value">{value}</div>
    </div>
    """


def section_header(text: str):
    st.markdown(f"<h3 class='section-header'>{text}</h3>", unsafe_allow_html=True)


# ===============================
# TIME / BLOCK HELPERS
# ===============================

def time_to_blocks(t: dtime) -> int:
    """
    Synthetic 30-minute block index for one session:
    15:00 previous day = 0
    23:30 previous = 17
    00:00 = 18
    ...
    08:30 = 35
    ...
    14:30 = 47
    """
    if t.hour < 15:
        base = 18  # blocks from 15:00 -> 23:30 inclusive = 18 blocks
        idx = base + t.hour * 2 + (1 if t.minute >= 30 else 0)
    else:
        idx = (t.hour - 15) * 2 + (1 if t.minute >= 30 else 0)
    return idx


def rth_slots() -> pd.DataFrame:
    """
    Return RTH times as a DataFrame with Time string and block index.
    """
    next_day = BASE_DATE.date() + timedelta(days=1)
    start = datetime(next_day.year, next_day.month, next_day.day, 8, 30)
    end = datetime(next_day.year, next_day.month, next_day.day, 14, 30)
    times = pd.date_range(start=start, end=end, freq="30min")
    df = pd.DataFrame({
        "Time": times.strftime("%H:%M"),
        "Block": [time_to_blocks(t.time()) for t in times]
    })
    return df


# ===============================
# CHANNEL ENGINES
# ===============================

def build_underlying_channel(
    high_price: float,
    high_time: dtime,
    low_price: float,
    low_time: dtime,
    slope_sign: int,
) -> Tuple[pd.DataFrame, float]:
    s = slope_sign * SLOPE_MAG
    k_hi = time_to_blocks(high_time)
    k_lo = time_to_blocks(low_time)

    b_top = high_price - s * k_hi
    b_bottom = low_price - s * k_lo
    channel_height = b_top - b_bottom

    slots = rth_slots()
    rows = []
    for _, row in slots.iterrows():
        k = row["Block"]
        top = s * k + b_top
        bottom = s * k + b_bottom
        rows.append({
            "Time": row["Time"],
            "Top Rail": round(top, 4),
            "Bottom Rail": round(bottom, 4),
        })
    df = pd.DataFrame(rows)
    return df, round(channel_height, 4)


def build_em_channel(
    em_value: float,
    base_price: float,
    base_time: dtime,
    slope_sign: int,
) -> Tuple[pd.DataFrame, float]:
    """
    EM channel: lower rail anchored at base_price at base_time,
    channel height = em_value, slope = slope_sign * SLOPE_MAG.
    """
    s = slope_sign * SLOPE_MAG
    k_base = time_to_blocks(base_time)

    # lower rail line: L(k) = s*k + b_low; with L(k_base) = base_price
    b_low = base_price - s * k_base
    # upper rail is offset by em_value at every block
    b_top = b_low + em_value

    slots = rth_slots()
    rows = []
    for _, row in slots.iterrows():
        k = row["Block"]
        low = s * k + b_low
        top = s * k + b_top
        rows.append({
            "Time": row["Time"],
            "EM Bottom": round(low, 4),
            "EM Top": round(top, 4),
        })
    df = pd.DataFrame(rows)
    return df, round(em_value, 4)


# ===============================
# CONTRACT ENGINE
# ===============================

def build_contract_projection(
    anchor_a_time: dtime,
    anchor_a_price: float,
    anchor_b_time: dtime,
    anchor_b_price: float,
) -> Tuple[pd.DataFrame, float]:
    k_a = time_to_blocks(anchor_a_time)
    k_b = time_to_blocks(anchor_b_time)
    if k_a == k_b:
        slope = 0.0
    else:
        slope = (anchor_b_price - anchor_a_price) / (k_b - k_a)

    # contract line: C(k) = slope * k + b_c
    b_c = anchor_a_price - slope * k_a

    slots = rth_slots()
    rows = []
    for _, row in slots.iterrows():
        k = row["Block"]
        price = slope * k + b_c
        rows.append({
            "Time": row["Time"],
            "Contract Price": round(price, 4),
        })
    df = pd.DataFrame(rows)
    return df, round(slope, 6)


# ===============================
# HELPERS: ACTIVE MODES
# ===============================

def get_active_underlying_channel() -> Tuple[Optional[str], Optional[pd.DataFrame], Optional[float]]:
    mode = st.session_state.get("channel_mode", "Ascending & Descending")
    df_asc = st.session_state.get("under_asc_df")
    df_desc = st.session_state.get("under_desc_df")
    h_asc = st.session_state.get("under_asc_height")
    h_desc = st.session_state.get("under_desc_height")

    if mode == "Ascending only":
        return "Ascending", df_asc, h_asc
    if mode == "Descending only":
        return "Descending", df_desc, h_desc
    if mode == "Ascending & Descending":
        choice = st.selectbox(
            "Active channel for playbook",
            ["Ascending", "Descending"],
            index=0,
            key="active_under_channel_select",
        )
        if choice == "Ascending":
            return "Ascending", df_asc, h_asc
        else:
            return "Descending", df_desc, h_desc
    return None, None, None


def get_active_em_channel() -> Tuple[Optional[str], Optional[pd.DataFrame], Optional[float]]:
    mode = st.session_state.get("em_mode", "On (Ascending & Descending)")
    df_em_asc = st.session_state.get("em_asc_df")
    df_em_desc = st.session_state.get("em_desc_df")
    h_em = st.session_state.get("em_height")

    if mode == "Off":
        return None, None, None
    if mode == "On (Ascending & Descending)":
        choice = st.selectbox(
            "Active EM channel",
            ["Ascending EM", "Descending EM"],
            index=0,
            key="active_em_channel_select",
        )
        if choice == "Ascending EM":
            return "Ascending EM", df_em_asc, h_em
        else:
            return "Descending EM", df_em_desc, h_em
    return None, None, None


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
        st.markdown(f"<span class='spx-sub'>{TAGLINE}</span>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### Core Assumptions")
        st.caption(
            "• Uniform rail slope: **±0.475 pts / 30 min**\n"
            "• Time grid: 30-minute blocks\n"
            "• Synthetic session: 15:00 previous day → 14:30 RTH"
        )
        st.markdown("---")
        st.markdown("#### Notes")
        st.caption(
            "SPX maintenance: 16:00–17:00 CT\n\n"
            "Options maintenance: 16:00–19:00 CT\n\n"
            "RTH grid: 08:30–14:30 CT."
        )

    hero()

    tabs = st.tabs([
        "🧱 Rails & EM Setup",
        "📐 Contract Engine",
        "🔮 Daily Foresight",
        "ℹ️ About",
    ])

    # ==========================
    # TAB 1 — RAILS & EM
    # ==========================
    with tabs[0]:
        card(
            "Underlying Rails",
            "Use your trusted engulfing pivots to project both ascending and descending channels across RTH.",
            badge="Structure Engine",
            icon="🧱",
        )

        section_header("Pivot Configuration")
        st.markdown(
            "<div class='spx-sub'>"
            "Choose the key high and low reversals you trust for this session. "
            "The engine uses a single synthetic time line from the previous 15:00 through the next RTH."
            "</div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**High Pivot**")
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
            st.markdown("**Low Pivot**")
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

        section_header("Channel Mode")
        channel_mode = st.radio(
            "How do you want to read today's structure?",
            ["Ascending only", "Descending only", "Ascending & Descending"],
            index=2,
            key="channel_mode",
            horizontal=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn = st.columns([1, 3])[0]
        with col_btn:
            if st.button("Build Underlying Rails", key="build_under_rails_btn", use_container_width=True):
                df_asc, h_asc = build_underlying_channel(
                    high_price=high_price,
                    high_time=high_time,
                    low_price=low_price,
                    low_time=low_time,
                    slope_sign=+1,
                )
                df_desc, h_desc = build_underlying_channel(
                    high_price=high_price,
                    high_time=high_time,
                    low_price=low_price,
                    low_time=low_time,
                    slope_sign=-1,
                )
                st.session_state["under_asc_df"] = df_asc
                st.session_state["under_desc_df"] = df_desc
                st.session_state["under_asc_height"] = h_asc
                st.session_state["under_desc_height"] = h_desc
                st.success("Rails projected for both ascending and descending modes.")

        df_asc = st.session_state.get("under_asc_df")
        df_desc = st.session_state.get("under_desc_df")
        h_asc = st.session_state.get("under_asc_height")
        h_desc = st.session_state.get("under_desc_height")

        section_header("Underlying Channel Projections • RTH 08:30–14:30 CT")
        if df_asc is None or df_desc is None:
            st.info("Build the rails to see RTH projections.")
        else:
            st.markdown("**Ascending channel**", unsafe_allow_html=True)
            c_top = st.columns([3, 1])
            with c_top[0]:
                st.dataframe(df_asc, use_container_width=True, hide_index=True, height=260)
            with c_top[1]:
                st.markdown(metric_card("Channel height (Asc)", f"{h_asc:.2f} pts"), unsafe_allow_html=True)
                st.download_button(
                    "Download ascending rails CSV",
                    df_asc.to_csv(index=False).encode(),
                    "underlying_ascending_rails.csv",
                    "text/csv",
                    key="dl_under_asc",
                    use_container_width=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Descending channel**", unsafe_allow_html=True)
            c_bot = st.columns([3, 1])
            with c_bot[0]:
                st.dataframe(df_desc, use_container_width=True, hide_index=True, height=260)
            with c_bot[1]:
                st.markdown(metric_card("Channel height (Desc)", f"{h_desc:.2f} pts"), unsafe_allow_html=True)
                st.download_button(
                    "Download descending rails CSV",
                    df_desc.to_csv(index=False).encode(),
                    "underlying_descending_rails.csv",
                    "text/csv",
                    key="dl_under_desc",
                    use_container_width=True,
                )

        end_card()

        # ---------- Expected Move ----------
        card(
            "Expected Move Channel",
            "Apply the same structural slope to the daily expected move by anchoring the lower rail at the opening area.",
            badge="EM Engine",
            icon="📊",
        )

        section_header("Expected Move Inputs")
        em_value = st.number_input(
            "Expected move (points)",
            value=80.0,
            step=1.0,
            key="em_value",
        )
        em_base_price = st.number_input(
            "EM lower rail anchor price (e.g., overnight open)",
            value=6700.0,
            step=0.5,
            key="em_base_price",
        )
        em_base_time = st.time_input(
            "EM lower rail anchor time (CT)",
            value=dtime(17, 0),
            step=1800,
            key="em_base_time",
        )

        em_mode = st.radio(
            "EM usage",
            ["On (Ascending & Descending)", "Off"],
            index=0,
            key="em_mode",
            horizontal=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn2 = st.columns([1, 3])[0]
        with col_btn2:
            if st.button("Build EM Channels", key="build_em_btn", use_container_width=True):
                df_em_asc, h_em = build_em_channel(
                    em_value=em_value,
                    base_price=em_base_price,
                    base_time=em_base_time,
                    slope_sign=+1,
                )
                df_em_desc, _ = build_em_channel(
                    em_value=em_value,
                    base_price=em_base_price,
                    base_time=em_base_time,
                    slope_sign=-1,
                )
                st.session_state["em_asc_df"] = df_em_asc
                st.session_state["em_desc_df"] = df_em_desc
                st.session_state["em_height"] = h_em
                st.success("EM channels projected for both ascending and descending modes.")

        df_em_asc = st.session_state.get("em_asc_df")
        df_em_desc = st.session_state.get("em_desc_df")

        section_header("EM Channel Projections • RTH 08:30–14:30 CT")
        if df_em_asc is None or df_em_desc is None:
            st.info("Build the EM channels to see their RTH structure.")
        else:
            st.markdown("**Ascending EM channel**", unsafe_allow_html=True)
            st.dataframe(df_em_asc, use_container_width=True, hide_index=True, height=220)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Descending EM channel**", unsafe_allow_html=True)
            st.dataframe(df_em_desc, use_container_width=True, hide_index=True, height=220)

        end_card()

    # ==========================
    # TAB 2 — CONTRACT ENGINE
    # ==========================
    with tabs[1]:
        card(
            "Contract Engine",
            "Two anchor prices define a straight contract line on the same 30-minute grid. "
            "A multiplier then gives you a realistic take-profit target per channel move.",
            badge="Options Structure",
            icon="📐",
        )

        # Use pivot times as shortcuts if available
        ph_time: dtime = st.session_state.get("pivot_high_time", dtime(15, 0))
        pl_time: dtime = st.session_state.get("pivot_low_time", dtime(3, 0))

        section_header("Anchor A — Origin")
        anchor_a_source = st.radio(
            "Use which time for Anchor A?",
            ["High pivot time", "Low pivot time", "Custom time"],
            index=0,
            key="contract_anchor_a_source",
            horizontal=True,
        )

        if anchor_a_source == "High pivot time":
            anchor_a_time = ph_time
            st.markdown(
                f"<div class='muted'>Anchor A time set to high pivot time: <b>{anchor_a_time.strftime('%H:%M')}</b> CT.</div>",
                unsafe_allow_html=True,
            )
        elif anchor_a_source == "Low pivot time":
            anchor_a_time = pl_time
            st.markdown(
                f"<div class='muted'>Anchor A time set to low pivot time: <b>{anchor_a_time.strftime('%H:%M')}</b> CT.</div>",
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
            value=5.0,
            step=0.1,
            key="contract_anchor_a_price",
        )

        section_header("Anchor B — Second Reference")
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
                value=12.0,
                step=0.1,
                key="contract_anchor_b_price",
            )

        section_header("Contract Multiplier")
        contract_factor = st.number_input(
            "Contract gain factor per point of SPX (conservative)",
            value=0.30,
            step=0.05,
            min_value=0.05,
            max_value=1.00,
            key="contract_factor",
        )
        st.markdown(
            "<div class='muted'>"
            "This does not try to match every explosive move exactly. "
            "It gives you a realistic target like: <em>for each 1 point in SPX, expect about 0.3 in the contract</em>. "
            "You can adjust it based on your own stats."
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn = st.columns([1, 3])[0]
        with col_btn:
            if st.button("Build Contract Line", key="build_contract_btn", use_container_width=True):
                try:
                    df_contract, slope_contract = build_contract_projection(
                        anchor_a_time=anchor_a_time,
                        anchor_a_price=anchor_a_price,
                        anchor_b_time=anchor_b_time,
                        anchor_b_price=anchor_b_price,
                    )
                    st.session_state["contract_df"] = df_contract
                    st.session_state["contract_slope"] = slope_contract
                    st.session_state["contract_factor_value"] = contract_factor
                    st.success("Contract line projected successfully across RTH.")
                except Exception as e:
                    st.error(f"Error generating contract projection: {e}")

        df_contract = st.session_state.get("contract_df")
        slope_contract = st.session_state.get("contract_slope")

        section_header("Contract Projection • RTH 08:30–14:30 CT")
        if df_contract is None:
            st.info("Build the contract projection to see the line.")
        else:
            c_top = st.columns([3, 1])
            with c_top[0]:
                st.dataframe(df_contract, use_container_width=True, hide_index=True, height=320)
            with c_top[1]:
                st.markdown(metric_card("Contract slope", f"{slope_contract:+.4f} / 30m"), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    "Download contract CSV",
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
            "Daily Foresight Card",
            "Underlying rails, EM channels, and contract structure merged into a single, time-based playbook.",
            badge="Session Blueprint",
            icon="🔮",
        )

        df_mode, df_ch, h_ch = get_active_underlying_channel()
        em_mode_label, df_em_active, h_em = get_active_em_channel()
        df_contract = st.session_state.get("contract_df")
        slope_contract = st.session_state.get("contract_slope")
        contract_factor = st.session_state.get("contract_factor_value", 0.30)

        if df_ch is None or h_ch is None:
            st.warning("No active underlying channel. Build rails first in the Rails & EM tab.")
            end_card()
        elif df_contract is None or slope_contract is None:
            st.warning("No contract line. Build it first in the Contract Engine tab.")
            end_card()
        else:
            # Merge panoramic table
            base = df_ch.copy()
            base = base.merge(df_contract, on="Time", how="left")
            if df_em_active is not None:
                base = base.merge(df_em_active, on="Time", how="left")
            else:
                base["EM Bottom"] = None
                base["EM Top"] = None

            base["Mid Rail"] = (base["Top Rail"] + base["Bottom Rail"]) / 2.0
            base["Rail Width"] = base["Top Rail"] - base["Bottom Rail"]

            # Contract gain per full inside-channel move (factor-based)
            contract_gain_est = contract_factor * h_ch

            # Confidence level based on EM alignment
            confidence = "Unknown"
            if df_em_active is None or h_em is None or em_mode_label is None:
                confidence = "No EM — structure only"
            else:
                # Check overlap at open (08:30 row)
                row_open = base[base["Time"] == "08:30"]
                if not row_open.empty:
                    r = row_open.iloc[0]
                    if (r["EM Bottom"] is not None) and (r["EM Top"] is not None):
                        em_inside = (r["EM Bottom"] <= r["Top Rail"]) and (r["EM Top"] >= r["Bottom Rail"])
                        same_direction = (
                            (df_mode == "Ascending" and "Ascending" in em_mode_label)
                            or (df_mode == "Descending" and "Descending" in em_mode_label)
                        )
                        if same_direction and em_inside:
                            confidence = "High — rails and EM agree"
                        elif same_direction and not em_inside:
                            confidence = "Medium — direction agrees, levels differ"
                        else:
                            confidence = "Low — EM and rails disagree"
                    else:
                        confidence = "EM missing at open"
                else:
                    confidence = "No 08:30 row found"

            section_header("Structure Summary")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(metric_card("Active channel", df_mode or "Not set"), unsafe_allow_html=True)
            with c2:
                st.markdown(metric_card("Channel height", f"{h_ch:.2f} pts"), unsafe_allow_html=True)
            with c3:
                st.markdown(metric_card("Contract TP per channel", f"{contract_gain_est:.2f} units"), unsafe_allow_html=True)

            c4, c5 = st.columns(2)
            with c4:
                em_label = em_mode_label or "EM off"
                st.markdown(metric_card("EM channel", em_label), unsafe_allow_html=True)
            with c5:
                st.markdown(metric_card("Confidence", confidence), unsafe_allow_html=True)

            section_header("Inside-Channel Play")
            st.markdown(
                f"""
                <div class='spx-sub'>
                <p><strong style="color:#16a34a;">🟢 Long idea</strong> — Buy near the lower rail, aim for the upper rail.</p>
                <ul style="margin-left:18px;">
                    <li>SPX structure move: about <strong>{h_ch:.2f} pts</strong> in your favor.</li>
                    <li>Conservative contract take-profit: about <strong>{contract_gain_est:.2f}</strong> units based on factor {contract_factor:.2f}.</li>
                </ul>
                <p><strong style="color:#dc2626;">🔴 Short idea</strong> — Sell near the upper rail, aim for the lower rail.</p>
                <ul style="margin-left:18px;">
                    <li>Same structural distance, opposite direction.</li>
                    <li>Use the same contract TP size in the opposite sign.</li>
                </ul>
                <p style="color:#64748b; margin-top:4px;"><em>
                This is a structural target. Actual options moves can exceed this when volatility expands.
                </em></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            section_header("Contract Trade Estimator")
            times = base["Time"].tolist()
            if times:
                col_e, col_x = st.columns(2)
                with col_e:
                    entry_time = st.selectbox(
                        "Entry time (rail touch / contract entry)",
                        times,
                        index=0,
                        key="est_entry_time",
                    )
                with col_x:
                    exit_time = st.selectbox(
                        "Exit time (planned)",
                        times,
                        index=min(len(times) - 1, 4),
                        key="est_exit_time",
                    )

                entry_row = base[base["Time"] == entry_time].iloc[0]
                exit_row = base[base["Time"] == exit_time].iloc[0]
                entry_contract = float(entry_row["Contract Price"])
                exit_contract = float(exit_row["Contract Price"])
                pnl_contract = exit_contract - entry_contract

                c1e, c2e, c3e = st.columns(3)
                with c1e:
                    st.markdown(metric_card("Entry contract", f"{entry_contract:.2f}"), unsafe_allow_html=True)
                with c2e:
                    st.markdown(metric_card("Exit contract", f"{exit_contract:.2f}"), unsafe_allow_html=True)
                with c3e:
                    st.markdown(metric_card("Projected Δ from line", f"{pnl_contract:+.2f} units"), unsafe_allow_html=True)

                st.markdown(
                    "<div class='muted'><strong>How to read this:</strong> "
                    "This P&L is purely from the straight contract line. "
                    "Compare it with what the market actually gave you on that day — "
                    "the extra is your volatility / skew bonus.</div>",
                    unsafe_allow_html=True,
                )

            section_header("Time-Aligned Map (Panoramic View)")
            st.caption("Every row is a 30-minute slot in RTH. Use it as a structural map rather than a prediction of exact turns.")
            # Reorder columns for clarity
            columns_order = [
                "Time",
                "Top Rail",
                "Bottom Rail",
                "Mid Rail",
                "Rail Width",
                "EM Top",
                "EM Bottom",
                "Contract Price",
            ]
            for col in columns_order:
                if col not in base.columns:
                    base[col] = None
            base_view = base[columns_order]
            st.dataframe(base_view, use_container_width=True, hide_index=True, height=420)

            st.markdown(
                "<div class='muted'><strong>Interpretation:</strong> "
                "The grid does not tell you when price will touch a rail. "
                "It tells you what your structure expects <em>if</em> that touch happens at that time. "
                "Your edge is in comparing this clean structure with what the market actually does.</div>",
                unsafe_allow_html=True,
            )

            end_card()

    # ==========================
    # TAB 4 — ABOUT
    # ==========================
    with tabs[3]:
        card("About SPX Prophet", TAGLINE, badge="Institutional Edition", icon="ℹ️")
        st.markdown(
            """
            <div class="spx-sub">
            <p><strong>SPX Prophet</strong> is built around a simple, disciplined idea:</p>
            <p style="font-size:1.05rem; color:#4f46e5; font-weight:600; margin:10px 0;">
            Two pivots define the rails. The slope and expected move carry that structure into the session.
            </p>
            <ul style="margin-left:18px;">
                <li>Underlying channels: ascending and descending rails with a uniform slope of <strong>±0.475 pts / 30m</strong>.</li>
                <li>Expected move channels: same structural slope, with the EM as the channel height.</li>
                <li>Contract line: a straight options path defined by two anchor prices on the same 30m grid.</li>
                <li>Contract TP: a conservative multiplier of SPX structure, tuned by your own stats.</li>
            </ul>
            <p>
            The goal is not to guess every tick. The goal is to give you a clean,
            repeatable framework so that when SPX returns to your rails, you already know
            what the contract is structurally worth and what a reasonable take-profit looks like.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='muted'><strong>Reminder:</strong> "
            "All times are CT. The synthetic time grid spans from the prior 15:00 through the RTH of interest.</div>",
            unsafe_allow_html=True,
        )
        end_card()

    st.markdown(
        "<div class='app-footer'>© 2025 SPX Prophet • Where Structure Becomes Foresight.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()