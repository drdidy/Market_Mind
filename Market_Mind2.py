# spx_prophet.py
# SPX Prophet — Where Structure Becomes Foresight.

import streamlit as st
import pandas as pd
from datetime import time as dtime
from typing import Optional, Tuple

APP_NAME = "SPX Prophet"
TAGLINE = "Where Structure Becomes Foresight."

# Core structural settings
SLOPE_MAG = 0.475        # SPX rails slope in points per 30 minutes
DEFAULT_TP_FACTOR = 0.30 # default contract TP factor vs SPX move
RTH_START_MIN = 8 * 60 + 30  # 08:30 in minutes from midnight
RTH_END_MIN = 14 * 60 + 30   # 14:30


# ===============================
# ULTRA LIGHT / ELEGANT UI
# ===============================

def inject_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(ellipse 1800px 1200px at 20% 10%, rgba(99, 102, 241, 0.06), transparent 60%),
          radial-gradient(ellipse 1600px 1400px at 80% 90%, rgba(56, 189, 248, 0.06), transparent 60%),
          linear-gradient(180deg, #ffffff 0%, #f8fafc 40%, #eef2ff 100%);
        background-attachment: fixed;
        color: #0f172a;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .block-container {
        padding-top: 3rem;
        padding-bottom: 4rem;
        max-width: 1400px;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 50% 0%, rgba(129, 140, 248, 0.10), transparent 75%),
            linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.40);
        box-shadow:
            6px 0 30px rgba(15, 23, 42, 0.10);
    }

    [data-testid="stSidebar"] h3 {
        font-size: 1.5rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1e293b, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.4rem;
        letter-spacing: -0.03em;
    }

    [data-testid="stSidebar"] hr {
        margin: 1.8rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg,
            transparent,
            rgba(148, 163, 184, 0.8),
            transparent);
    }

    /* HERO */
    .hero-header {
        position: relative;
        background:
            radial-gradient(ellipse at top, rgba(129, 140, 248, 0.20), transparent 65%),
            radial-gradient(ellipse at bottom, rgba(59, 130, 246, 0.18), transparent 65%),
            linear-gradient(135deg, #ffffff, #f9fafb);
        border-radius: 32px;
        padding: 36px 32px 32px 32px;
        margin-bottom: 32px;
        border: 1px solid rgba(148, 163, 184, 0.40);
        box-shadow:
            0 24px 70px rgba(15, 23, 42, 0.16);
        overflow: hidden;
        text-align: center;
        animation: heroSoftGlow 6s ease-in-out infinite;
    }

    @keyframes heroSoftGlow {
        0%, 100% { box-shadow: 0 24px 70px rgba(15, 23, 42, 0.16); }
        50% { box-shadow: 0 28px 80px rgba(79, 70, 229, 0.30); }
    }

    .hero-badge-row {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(5, 150, 105, 0.08));
        border: 1px solid rgba(16, 185, 129, 0.35);
        font-size: 0.8rem;
        font-weight: 700;
        color: #047857;
        text-transform: uppercase;
        letter-spacing: 0.10em;
    }

    .status-indicator::before {
        content: '';
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #22c55e;
        box-shadow: 0 0 12px rgba(34, 197, 94, 0.80);
    }

    .status-tagline {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.03);
        border: 1px solid rgba(148, 163, 184, 0.50);
        font-size: 0.8rem;
        font-weight: 600;
        color: #475569;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 900;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #0f172a 0%, #4f46e5 45%, #0ea5e9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 4px 0 4px 0;
        letter-spacing: -0.06em;
        line-height: 1.05;
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        margin-top: 4px;
        margin-bottom: 0;
        font-weight: 500;
    }

    /* CARDS */
    .spx-card {
        position: relative;
        background:
            radial-gradient(circle at 0% 0%, rgba(129, 140, 248, 0.10), transparent 60%),
            radial-gradient(circle at 100% 100%, rgba(45, 212, 191, 0.14), transparent 60%),
            linear-gradient(135deg, #ffffff, #f9fafb);
        border-radius: 26px;
        border: 1px solid rgba(148, 163, 184, 0.45);
        box-shadow:
            0 18px 50px rgba(15, 23, 42, 0.10);
        padding: 26px 26px 26px 26px;
        margin-bottom: 26px;
        transition: all 0.35s ease;
        overflow: hidden;
    }

    .spx-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: -120%;
        width: 60%;
        height: 100%;
        background: linear-gradient(90deg,
            transparent,
            rgba(129, 140, 248, 0.10),
            transparent);
        transform: skewX(-18deg);
        transition: left 0.8s ease;
    }

    .spx-card:hover {
        transform: translateY(-4px);
        box-shadow:
            0 24px 60px rgba(15, 23, 42, 0.14);
        border-color: rgba(79, 70, 229, 0.50);
    }

    .spx-card:hover::after {
        left: 140%;
    }

    .icon-large {
        font-size: 3rem;
        background: linear-gradient(135deg, #4f46e5, #0ea5e9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 6px;
        display: inline-block;
    }

    .spx-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 16px;
        border-radius: 999px;
        border: 1px solid rgba(129, 140, 248, 0.60);
        background: rgba(248, 250, 252, 0.96);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #4f46e5;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .spx-pill::before {
        content: '●';
        font-size: 0.7rem;
    }

    .spx-card h4 {
        font-size: 1.5rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        color: #0f172a;
        margin: 4px 0 4px 0;
        letter-spacing: -0.03em;
    }

    .spx-sub {
        color: #475569;
        font-size: 0.98rem;
        line-height: 1.7;
        font-weight: 400;
    }

    /* SECTION HEADERS */
    .section-header {
        font-size: 1.4rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        color: #0f172a;
        margin: 1.8rem 0 0.9rem 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .section-header::before {
        content: '';
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, #4f46e5, #0ea5e9);
        box-shadow: 0 0 12px rgba(79, 70, 229, 0.70);
    }

    /* METRIC CARDS */
    .spx-metric {
        padding: 18px 18px;
        border-radius: 18px;
        background:
            radial-gradient(circle at 0% 0%, rgba(129, 140, 248, 0.12), transparent 60%),
            linear-gradient(135deg, #ffffff, #f9fafb);
        border: 1px solid rgba(148, 163, 184, 0.60);
        box-shadow: 0 14px 40px rgba(15, 23, 42, 0.10);
    }

    .spx-metric-label {
        font-size: 0.70rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #64748b;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .spx-metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: #0f172a;
    }

    /* BUTTONS */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #4f46e5, #0ea5e9);
        color: #ffffff;
        border-radius: 999px;
        border: none;
        padding: 10px 20px;
        font-weight: 700;
        font-size: 0.86rem;
        letter-spacing: 0.14em;
        box-shadow:
            0 14px 34px rgba(79, 70, 229, 0.30);
        cursor: pointer;
        transition: all 0.25s ease;
        text-transform: uppercase;
    }

    .stButton>button:hover,
    .stDownloadButton>button:hover {
        transform: translateY(-2px);
        box-shadow:
            0 18px 40px rgba(79, 70, 229, 0.38);
    }

    /* INPUTS */
    .stNumberInput>div>div>input,
    .stTimeInput>div>div>input {
        background: #ffffff !important;
        border: 1px solid rgba(148, 163, 184, 0.80) !important;
        border-radius: 14px !important;
        color: #0f172a !important;
        padding: 10px 12px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stSelectbox>div>div {
        background: #ffffff !important;
        border-radius: 14px !important;
        border: 1px solid rgba(148, 163, 184, 0.80) !important;
        box-shadow: none !important;
    }

    .stRadio>div>label {
        background: #ffffff;
        padding: 8px 16px;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.80);
        font-size: 0.90rem;
        font-weight: 600;
        color: #475569;
    }

    .stRadio>div>label[data-selected="true"] {
        border-color: #4f46e5;
        background: rgba(79, 70, 229, 0.10);
        color: #1e293b;
    }

    label {
        font-size: 0.90rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        margin-bottom: 4px !important;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(248, 250, 252, 0.92);
        padding: 6px;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.70);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 999px;
        color: #64748b;
        font-weight: 600;
        font-size: 0.90rem;
        padding: 6px 16px;
        border: none;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #0ea5e9);
        color: #ffffff;
    }

    /* DATAFRAME */
    .stDataFrame {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
        border: 1px solid rgba(148, 163, 184, 0.70);
    }

    .stDataFrame div[data-testid="StyledTable"] {
        font-variant-numeric: tabular-nums;
        font-size: 0.90rem;
        font-family: 'JetBrains Mono', monospace;
        background: #ffffff;
    }

    .muted {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.7;
        padding: 12px 14px;
        background: #f8fafc;
        border-left: 3px solid #4f46e5;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }

    .app-footer {
        margin-top: 2.5rem;
        padding-top: 1.2rem;
        border-top: 1px solid rgba(148, 163, 184, 0.40);
        text-align: center;
        color: #94a3b8;
        font-size: 0.90rem;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def hero():
    st.markdown(
        f"""
        <div class="hero-header">
            <div class="hero-badge-row">
                <div class="status-indicator">System Active</div>
                <div class="status-tagline">Structure First. Emotion Last.</div>
            </div>
            <h1 class="hero-title">{APP_NAME}</h1>
            <p class="hero-subtitle">{TAGLINE}</p>
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
    st.markdown(f"<div class='section-header'>{text}</div>", unsafe_allow_html=True)


# ===============================
# TIME / BLOCK HELPERS (GENERIC)
# ===============================

def time_to_minutes(t: dtime) -> int:
    return t.hour * 60 + t.minute


def compute_block_index(t: dtime, day_flag: str) -> int:
    """
    Map a time + day relation into a 30-minute block index
    relative to today's RTH start 08:30 (block 0).
    day_flag: "Previous session", "Current session", "Next session"
    """
    m_t = time_to_minutes(t)
    m_rth0 = RTH_START_MIN
    day_offset = {"Previous session": -1, "Current session": 0, "Next session": 1}[day_flag]
    minutes_diff = day_offset * 1440 + m_t - m_rth0
    return round(minutes_diff / 30.0)


def build_rth_grid() -> pd.DataFrame:
    rows = []
    k = 0
    m = RTH_START_MIN
    while m <= RTH_END_MIN:
        hh = m // 60
        mm = m % 60
        rows.append({
            "Block": k,
            "Time": f"{hh:02d}:{mm:02d}"
        })
        k += 1
        m += 30
    return pd.DataFrame(rows)


# ===============================
# CHANNEL / EM / CONTRACT ENGINES
# ===============================

def build_channel_from_pivots(
    high_price: float,
    high_time: dtime,
    high_day_flag: str,
    low_price: float,
    low_time: dtime,
    low_day_flag: str,
    slope_sign: int,
) -> Tuple[pd.DataFrame, float]:
    s = slope_sign * SLOPE_MAG
    k_hi = compute_block_index(high_time, high_day_flag)
    k_lo = compute_block_index(low_time, low_day_flag)

    b_top = high_price - s * k_hi
    b_bottom = low_price - s * k_lo
    channel_height = b_top - b_bottom

    base = build_rth_grid()
    base["Top Rail"] = s * base["Block"] + b_top
    base["Bottom Rail"] = s * base["Block"] + b_bottom

    df = base[["Time", "Top Rail", "Bottom Rail"]].copy()
    return df, float(channel_height)


def build_em_channel(
    em_value: float,
    em_anchor_price: float,
    em_anchor_time: dtime,
    em_anchor_day_flag: str,
    orientation: str,
) -> Tuple[pd.DataFrame, float]:
    """
    EM is applied as a sloped band around a center line.
    Center uses ±SLOPE_MAG depending on orientation.
    EM_value decides vertical range (± EM/2 around the center).
    """
    if em_value <= 0:
        raise ValueError("EM value must be positive.")

    s = SLOPE_MAG if orientation == "Up" else -SLOPE_MAG
    k_anchor = compute_block_index(em_anchor_time, em_anchor_day_flag)
    em_half = em_value / 2.0

    b_center = em_anchor_price - s * k_anchor
    b_top = b_center + em_half
    b_bottom = b_center - em_half

    base = build_rth_grid()
    base["EM Top"] = s * base["Block"] + b_top
    base["EM Bottom"] = s * base["Block"] + b_bottom

    df = base[["Time", "EM Top", "EM Bottom"]].copy()
    return df, em_value


def build_contract_line(
    anchor_a_price: float,
    anchor_a_time: dtime,
    anchor_a_day_flag: str,
    anchor_b_price: float,
    anchor_b_time: dtime,
    anchor_b_day_flag: str,
) -> Tuple[pd.DataFrame, float]:
    k_a = compute_block_index(anchor_a_time, anchor_a_day_flag)
    k_b = compute_block_index(anchor_b_time, anchor_b_day_flag)

    if k_a == k_b:
        slope_contract = 0.0
    else:
        slope_contract = (anchor_b_price - anchor_a_price) / (k_b - k_a)

    c0 = anchor_a_price - slope_contract * k_a

    base = build_rth_grid()
    base["Contract Line"] = slope_contract * base["Block"] + c0

    df = base[["Time", "Contract Line"]].copy()
    return df, float(slope_contract)


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

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.markdown(
            f"<span class='spx-sub' style='font-size:0.95rem;'>{TAGLINE}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        st.markdown("#### Core Parameters")
        st.write(f"Rails slope: **{SLOPE_MAG:.3f} pts / 30m**")

        tp_factor = st.slider(
            "Contract TP factor vs SPX move",
            min_value=0.10,
            max_value=0.70,
            value=DEFAULT_TP_FACTOR,
            step=0.05,
            help="If the SPX moves one full channel, how much of that move do you want as a realistic contract target?",
            key="tp_factor_slider",
        )

        st.caption(f"Contract factor: **{tp_factor:.2f} × SPX move**")
        st.markdown("---")

        st.markdown("#### Notes")
        st.caption(
            "Underlying: 16:00–17:00 CT maintenance\n\n"
            "Contracts: 16:00–19:00 CT maintenance\n\n"
            "RTH projection grid: 08:30–14:30 CT (30m blocks)."
        )

    # ---------- HERO ----------
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
    # TAB 1: RAILS + EM
    # ==========================
    with tabs[0]:
        card(
            "Structure Engine",
            "Define your underlying channel from pivots and overlay the expected move channel that frames the day.",
            badge="Rails and Expected Move Setup",
            icon="🧱",
        )

        # ---- Underlying rails ----
        section_header("⚙️ Underlying Pivots (Channel)")

        st.markdown(
            "<div class='spx-sub'>"
            "Use the key swing high and low that define your overnight / prior session channel. "
            "You can place them on the previous session, current session, or next session. "
            "Both ascending and descending rails are always built."
            "</div>",
            unsafe_allow_html=True,
        )

        c_hi, c_lo = st.columns(2)
        with c_hi:
            st.markdown("**High Pivot**")
            high_price = st.number_input(
                "High pivot price",
                value=6721.10,
                step=0.25,
                key="pivot_high_price",
            )
            high_time = st.time_input(
                "High pivot time (CT)",
                value=dtime(18, 0),
                step=1800,
                key="pivot_high_time",
            )
            high_day_flag = st.selectbox(
                "High pivot day",
                ["Previous session", "Current session", "Next session"],
                index=0,
                key="pivot_high_day",
            )

        with c_lo:
            st.markdown("**Low Pivot**")
            low_price = st.number_input(
                "Low pivot price",
                value=6652.60,
                step=0.25,
                key="pivot_low_price",
            )
            low_time = st.time_input(
                "Low pivot time (CT)",
                value=dtime(14, 30),
                step=1800,
                key="pivot_low_time",
            )
            low_day_flag = st.selectbox(
                "Low pivot day",
                ["Previous session", "Current session", "Next session"],
                index=0,
                key="pivot_low_day",
            )

        section_header("📊 Channel Regime (for bias)")
        channel_mode = st.radio(
            "Which direction are you primarily interested in?",
            ["Ascending", "Descending", "Both"],
            index=2,
            horizontal=True,
            key="channel_mode_choice",
        )

        st.markdown("<br/>", unsafe_allow_html=True)

        col_btn = st.columns([1, 3])[0]
        with col_btn:
            if st.button("⚡ Build Rails", key="build_rails_btn", use_container_width=True):
                try:
                    df_asc, h_asc = build_channel_from_pivots(
                        high_price, high_time, high_day_flag,
                        low_price, low_time, low_day_flag,
                        slope_sign=+1,
                    )
                    df_desc, h_desc = build_channel_from_pivots(
                        high_price, high_time, high_day_flag,
                        low_price, low_time, low_day_flag,
                        slope_sign=-1,
                    )
                    st.session_state["rails_asc_df"] = df_asc
                    st.session_state["rails_desc_df"] = df_desc
                    st.session_state["rails_asc_height"] = h_asc
                    st.session_state["rails_desc_height"] = h_desc
                    st.success("Rails generated successfully. Check tables below and the Daily Foresight tab.")
                except Exception as e:
                    st.error(f"Error generating rails: {e}")

        df_asc = st.session_state.get("rails_asc_df")
        df_desc = st.session_state.get("rails_desc_df")
        h_asc = st.session_state.get("rails_asc_height")
        h_desc = st.session_state.get("rails_desc_height")

        section_header("📊 Underlying Rails • RTH 08:30–14:30 CT")

        if df_asc is None and df_desc is None:
            st.info("Build rails to see projections.")
        else:
            if df_asc is not None and h_asc is not None:
                st.markdown("**📈 Ascending Channel**")
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.dataframe(df_asc, use_container_width=True, hide_index=True, height=320)
                with c2:
                    st.markdown(metric_card("Channel Height (Asc)", f"{h_asc:.2f} pts"), unsafe_allow_html=True)
                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.download_button(
                        "Download ascending rails CSV",
                        df_asc.to_csv(index=False).encode(),
                        "spx_rails_ascending.csv",
                        "text/csv",
                        key="dl_rails_asc",
                        use_container_width=True,
                    )

            if df_desc is not None and h_desc is not None:
                st.markdown("**📉 Descending Channel**")
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.dataframe(df_desc, use_container_width=True, hide_index=True, height=320)
                with c2:
                    st.markdown(metric_card("Channel Height (Desc)", f"{h_desc:.2f} pts"), unsafe_allow_html=True)
                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.download_button(
                        "Download descending rails CSV",
                        df_desc.to_csv(index=False).encode(),
                        "spx_rails_descending.csv",
                        "text/csv",
                        key="dl_rails_desc",
                        use_container_width=True,
                    )

        # ---- EM Channel ----
        section_header("📊 EM Channel (Expected Move)")

        st.markdown(
            "<div class='spx-sub'>"
            "Use the market’s daily expected move as a sloped band. "
            "The EM band tracks the slope and frames the day’s likely range."
            "</div>",
            unsafe_allow_html=True,
        )

        c_em1, c_em2, c_em3 = st.columns(3)
        with c_em1:
            em_value = st.number_input(
                "Expected Move (points)",
                value=80.01,
                min_value=0.0,
                step=0.25,
                key="em_value_input",
            )
        with c_em2:
            em_anchor_price = st.number_input(
                "EM anchor price",
                value=6676.10,
                step=0.25,
                key="em_anchor_price_input",
            )
        with c_em3:
            em_anchor_time = st.time_input(
                "EM anchor time (CT)",
                value=dtime(17, 0),
                step=1800,
                key="em_anchor_time_input",
            )

        c_em_day, c_em_orient = st.columns(2)
        with c_em_day:
            em_anchor_day_flag = st.selectbox(
                "EM anchor day",
                ["Previous session", "Current session", "Next session"],
                index=0,
                key="em_anchor_day_flag",
            )
        with c_em_orient:
            em_orientation = st.radio(
                "EM orientation",
                ["Up", "Down"],
                index=0,
                horizontal=True,
                key="em_orientation",
            )

        col_btn_em = st.columns([1, 3])[0]
        with col_btn_em:
            if st.button("⚡ Build EM Channel", key="build_em_btn", use_container_width=True):
                try:
                    em_df, em_range = build_em_channel(
                        em_value=em_value,
                        em_anchor_price=em_anchor_price,
                        em_anchor_time=em_anchor_time,
                        em_anchor_day_flag=em_anchor_day_flag,
                        orientation=em_orientation,
                    )
                    st.session_state["em_df"] = em_df
                    st.session_state["em_range"] = em_range
                    st.success("EM channel generated successfully. It will overlay in the Daily Foresight tab.")
                except Exception as e:
                    st.error(f"Error generating EM channel: {e}")

        em_df = st.session_state.get("em_df")
        em_range = st.session_state.get("em_range")

        if em_df is not None:
            st.markdown("**📊 EM Channel Projection • RTH 08:30–14:30 CT**")
            c1, c2 = st.columns([3, 1])
            with c1:
                st.dataframe(em_df, use_container_width=True, hide_index=True, height=260)
            with c2:
                st.markdown(metric_card("EM Range", f"{em_range:.2f} pts"), unsafe_allow_html=True)
                st.markdown(metric_card("EM Slope", f"{('+' if em_orientation=='Up' else '-')}{SLOPE_MAG:.3f} / 30m"), unsafe_allow_html=True)

        end_card()

    # ==========================
    # TAB 2: CONTRACT
    # ==========================
    with tabs[1]:
        card(
            "Contract Line Setup",
            "Use two contract prices on the same 30-minute grid to define a clean line. "
            "This is the structural contract slope you compare to SPX rails and EM.",
            badge="Contract Engine",
            icon="📐",
        )

        section_header("⚓ Anchor A — Origin of Contract Line")
        c_a1, c_a2, c_a3 = st.columns(3)
        with c_a1:
            anchor_a_price = st.number_input(
                "Contract price at Anchor A",
                value=10.0,
                step=0.1,
                key="contract_anchor_a_price",
            )
        with c_a2:
            anchor_a_time = st.time_input(
                "Anchor A time (CT)",
                value=dtime(15, 0),
                step=1800,
                key="contract_anchor_a_time",
            )
        with c_a3:
            anchor_a_day_flag = st.selectbox(
                "Anchor A day",
                ["Previous session", "Current session", "Next session"],
                index=0,
                key="contract_anchor_a_day",
            )

        section_header("⚓ Anchor B — Second Contract Point")
        c_b1, c_b2, c_b3 = st.columns(3)
        with c_b1:
            anchor_b_price = st.number_input(
                "Contract price at Anchor B",
                value=8.0,
                step=0.1,
                key="contract_anchor_b_price",
            )
        with c_b2:
            anchor_b_time = st.time_input(
                "Anchor B time (CT)",
                value=dtime(7, 30),
                step=1800,
                key="contract_anchor_b_time",
            )
        with c_b3:
            anchor_b_day_flag = st.selectbox(
                "Anchor B day",
                ["Previous session", "Current session", "Next session"],
                index=1,
                key="contract_anchor_b_day",
            )

        st.markdown("<br/>", unsafe_allow_html=True)
        col_btn = st.columns([1, 3])[0]
        with col_btn:
            if st.button("⚡ Build Contract Line", key="build_contract_btn", use_container_width=True):
                try:
                    df_contract, slope_contract = build_contract_line(
                        anchor_a_price=anchor_a_price,
                        anchor_a_time=anchor_a_time,
                        anchor_a_day_flag=anchor_a_day_flag,
                        anchor_b_price=anchor_b_price,
                        anchor_b_time=anchor_b_time,
                        anchor_b_day_flag=anchor_b_day_flag,
                    )
                    st.session_state["contract_df"] = df_contract
                    st.session_state["contract_slope"] = slope_contract
                    st.success("Contract projection generated successfully. It will be used in the Daily Foresight tab.")
                except Exception as e:
                    st.error(f"Error generating contract projection: {e}")

        df_contract = st.session_state.get("contract_df")
        slope_contract = st.session_state.get("contract_slope")

        section_header("📊 Contract Projection • RTH 08:30–14:30 CT")
        if df_contract is None:
            st.info("Build a contract line to see projected prices.")
        else:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.dataframe(df_contract, use_container_width=True, hide_index=True, height=320)
            with c2:
                st.markdown(metric_card("Contract Slope", f"{slope_contract:+.4f} / 30m"), unsafe_allow_html=True)
                st.download_button(
                    "Download contract line CSV",
                    df_contract.to_csv(index=False).encode(),
                    "contract_line.csv",
                    "text/csv",
                    key="dl_contract_line",
                    use_container_width=True,
                )

                # If rails exist, show realized factor vs SPX slope
                h_active_for_factor = st.session_state.get("rails_asc_height") or st.session_state.get("rails_desc_height")
                if slope_contract is not None and h_active_for_factor:
                    realized_factor = abs(slope_contract) / SLOPE_MAG
                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.markdown(metric_card("Realized Slope Factor", f"{realized_factor:.2f} × SPX slope"), unsafe_allow_html=True)

        end_card()

    # ==========================
    # TAB 3: DAILY FORESIGHT
    # ==========================
    with tabs[2]:
        card(
            "Daily Foresight",
            "Rails, EM band, and contract line combined into a time-based playbook. "
            "This is your panoramic map for the session.",
            badge="Foresight",
            icon="🔮",
        )

        df_asc = st.session_state.get("rails_asc_df")
        df_desc = st.session_state.get("rails_desc_df")
        h_asc = st.session_state.get("rails_asc_height")
        h_desc = st.session_state.get("rails_desc_height")
        em_df = st.session_state.get("em_df")
        em_range = st.session_state.get("em_range")
        df_contract = st.session_state.get("contract_df")
        slope_contract = st.session_state.get("contract_slope")
        tp_factor = st.session_state.get("tp_factor_slider", DEFAULT_TP_FACTOR)

        if df_asc is None and df_desc is None:
            st.warning("No underlying rails found. Build them in the Rails and EM Setup tab first.")
            end_card()
        else:
            # Choose active underlying direction
            options = []
            if df_asc is not None:
                options.append("Ascending")
            if df_desc is not None:
                options.append("Descending")
            if not options:
                st.warning("Rails data missing. Build rails first.")
                end_card()
            else:
                active_dir = st.radio(
                    "Active underlying direction for today's playbook",
                    options,
                    index=0,
                    horizontal=True,
                    key="foresight_active_dir",
                )

                if active_dir == "Ascending":
                    df_ch = df_asc
                    h_ch = h_asc
                else:
                    df_ch = df_desc
                    h_ch = h_desc

                if h_ch is None:
                    h_ch = 0.0

                # Build base grid and merge everything for panoramic table
                base = build_rth_grid()[["Time"]].copy()
                merged = base.copy()

                if df_asc is not None:
                    df_temp = df_asc.rename(
                        columns={"Top Rail": "Top Asc", "Bottom Rail": "Bottom Asc"}
                    )
                    merged = merged.merge(df_temp, on="Time", how="left")

                if df_desc is not None:
                    df_temp = df_desc.rename(
                        columns={"Top Rail": "Top Desc", "Bottom Rail": "Bottom Desc"}
                    )
                    merged = merged.merge(df_temp, on="Time", how="left")

                if em_df is not None:
                    merged = merged.merge(em_df, on="Time", how="left")

                if df_contract is not None:
                    merged = merged.merge(df_contract, on="Time", how="left")

                # Contract move sizing based on channel
                blocks_in_channel = h_ch / SLOPE_MAG if SLOPE_MAG != 0 else 0.0
                if slope_contract is not None and blocks_in_channel != 0:
                    contract_move_full = slope_contract * blocks_in_channel
                    contract_move_abs = abs(contract_move_full)
                    realized_factor = abs(slope_contract) / SLOPE_MAG
                else:
                    contract_move_full = 0.0
                    contract_move_abs = 0.0
                    realized_factor = None

                tp_contract_move = h_ch * tp_factor

                # ------- Structure summary -------
                section_header("📊 Structure Summary")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(
                        metric_card("Active Underlying", active_dir),
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        metric_card("Channel Height", f"{h_ch:.2f} pts"),
                        unsafe_allow_html=True,
                    )
                with c3:
                    if realized_factor is not None:
                        st.markdown(
                            metric_card("Realized Factor", f"{realized_factor:.2f} × SPX"),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            metric_card("Realized Factor", "N/A"),
                            unsafe_allow_html=True,
                        )
                with c4:
                    if em_range is not None:
                        st.markdown(
                            metric_card("EM Range", f"{em_range:.2f} pts"),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            metric_card("EM Range", "Not set"),
                            unsafe_allow_html=True,
                        )

                # ------- Inside-channel trade idea -------
                section_header("📈 Inside-Channel Play Size")

                st.markdown(
                    f"""
                    <div class='spx-sub'>
                    <p><strong>Structural SPX move for a full rail-to-rail swing:</strong> ~{h_ch:.2f} points.</p>
                    <p><strong>Contract move if the line tracks the whole channel (from anchors):</strong> ~{contract_move_abs:.2f} units.</p>
                    <p><strong>Your conservative TP based on factor {tp_factor:.2f}:</strong> ~{tp_contract_move:.2f} contract units per full channel move.</p>
                    <p class='muted'>
                    This lets you say: “If SPX completes a full channel swing, I only need about {tp_factor:.2f} of that move on the contract.” 
                    The app gives you a realistic TP that sits inside what the structure can give.
                    </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # ------- Contract estimator -------
                section_header("🧮 Contract Trade Estimator")

                if df_contract is None:
                    st.info("Build a contract line in the Contract Line Setup tab to use the estimator.")
                else:
                    times = merged["Time"].tolist()
                    col_e, col_x, col_side = st.columns(3)
                    with col_e:
                        entry_time = st.selectbox(
                            "Entry time on the grid",
                            times,
                            index=0,
                            key="foresight_entry_time",
                        )
                    with col_x:
                        exit_time = st.selectbox(
                            "Exit time on the grid",
                            times,
                            index=min(len(times) - 1, 4),
                            key="foresight_exit_time",
                        )
                    with col_side:
                        side_choice = st.radio(
                            "Position type",
                            ["Auto", "Long Call", "Long Put"],
                            index=0,
                            key="foresight_side",
                        )

                    if side_choice == "Auto":
                        # Simple rule: ascending bias -> calls, descending -> puts
                        side = "Long Call" if active_dir == "Ascending" else "Long Put"
                    else:
                        side = side_choice

                    entry_row = merged[merged["Time"] == entry_time].iloc[0]
                    exit_row = merged[merged["Time"] == exit_time].iloc[0]
                    entry_contract = float(entry_row["Contract Line"])
                    exit_contract = float(exit_row["Contract Line"])
                    pnl_contract = exit_contract - entry_contract

                    # TP level from the entry using your TP factor
                    sign = 1 if side == "Long Call" else -1
                    tp_price = entry_contract + sign * tp_contract_move

                    c1_est, c2_est, c3_est, c4_est = st.columns(4)
                    with c1_est:
                        st.markdown(metric_card("Side", side), unsafe_allow_html=True)
                    with c2_est:
                        st.markdown(metric_card("Entry Contract", f"{entry_contract:.2f}"), unsafe_allow_html=True)
                    with c3_est:
                        st.markdown(metric_card("Exit Contract", f"{exit_contract:.2f}"), unsafe_allow_html=True)
                    with c4_est:
                        st.markdown(metric_card("Projected P&L", f"{pnl_contract:+.2f} units"), unsafe_allow_html=True)

                    st.markdown(
                        metric_card("TP from structure", f"{tp_price:.2f} (from entry)"),
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        "<div class='muted'>"
                        "<strong>How to use this:</strong> pick where you expect to enter on the line, "
                        "pick a planned exit time, and compare the projected move to what the market actually gave. "
                        "The TP level is your “inside the structure” target, not the maximum the market can offer."
                        "</div>",
                        unsafe_allow_html=True,
                    )

                # ------- Time-aligned panoramic map -------
                section_header("🗺️ Time-Aligned Map (Rails + EM + Contract)")

                st.caption(
                    "Every row is a 30-minute RTH slot. You see ascending and descending rails, EM band, "
                    "and the contract line at the same time point."
                )

                st.dataframe(merged, use_container_width=True, hide_index=True, height=480)

                st.markdown(
                    "<div class='muted'>"
                    "<strong>Reading this map:</strong> the grid doesn’t tell you when the tag will happen. "
                    "It tells you what your structure expects if the tag happens at a given time. "
                    "You manage risk and execution around that structure."
                    "</div>",
                    unsafe_allow_html=True,
                )

        end_card()

    # ==========================
    # TAB 4: ABOUT
    # ==========================
    with tabs[3]:
        card("About SPX Prophet", TAGLINE, badge="Overview", icon="ℹ️")

        st.markdown(
            """
            <div class='spx-sub'>
            <p>SPX Prophet is built on three simple structural ideas:</p>
            <ul>
                <li><strong>Rails:</strong> Two pivots define ascending and descending channels with a fixed slope of 0.475 points per 30 minutes.</li>
                <li><strong>Expected Move:</strong> The market's daily EM is treated as a sloped band, not a flat horizontal line.</li>
                <li><strong>Contract Line:</strong> Two contract prices define a straight line that lives on the same 30-minute grid as SPX.</li>
            </ul>
            <p>
            The app does not pretend to be a full options pricing engine. 
            It gives you a clean structural map so that when price returns to your rails, 
            you already know what the contract should be structurally worth.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        end_card()

    st.markdown(
        "<div class='app-footer'>© 2025 SPX Prophet • Where Structure Becomes Foresight.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()