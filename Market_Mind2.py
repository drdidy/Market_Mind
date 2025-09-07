# app.py - Part 1
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — Enhanced Edition Part 1
# Core utilities, data fetching, and enhanced ES-SPX offset tracking
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# ───────────────────────────────────────────────────────────────────────────────
# GLOBALS & CONFIG
# ───────────────────────────────────────────────────────────────────────────────
CT_TZ = pytz.timezone("America/Chicago")
RTH_START = "08:30"
RTH_END   = "14:30"

TOP_SLOPE_DEFAULT    = 0.312
BOTTOM_SLOPE_DEFAULT = 0.25

# Enhanced probability boosters with interaction effects
WEIGHTS_DEFAULT = {"ema":20, "volume":25, "wick":20, "atr":15, "tod":20, "div":0}
INTERACTION_WEIGHTS = {"ema_volume":15, "wick_atr":10, "tod_ema":12}  # New interaction bonuses
KEY_TOD = [(8,30), (10,0), (13,30)]
KEY_TOD_WINDOW_MIN = 7
WICK_MIN_RATIO = 0.6
ATR_LOOKBACK = 14
ATR_HIGH_PCTL = 70
ATR_LOW_PCTL  = 30
RSI_LEN = 14
RSI_WINDOW_MIN = 10

# Bounce quality thresholds
MIN_BOUNCE_VOLUME_RATIO = 1.2  # vs 20-period average
MIN_WICK_QUALITY = 0.4  # wick-to-body ratio for quality bounce
MIN_TIME_AT_LEVEL = 2    # minimum bars at bounce level

# ───────────────────────────────────────────────────────────────────────────────
# PAGE & THEME
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🔮 SPX Prophet Enhanced",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root { --brand:#2563eb; --brand-2:#10b981; --surface:#ffffff; --muted:#f8fafc;
        --text:#0f172a; --subtext:#475569; --border:#e2e8f0; --warn:#f59e0b; --danger:#ef4444; 
        --success:#059669; --info:#0284c7; }
html, body, [class*="css"] { background: var(--muted); color: var(--text); }
.block-container { padding-top: 1.1rem; }
h1, h2, h3 { color: var(--text); }
.card, .metric-card {
  background: rgba(255,255,255,0.9); border: 1px solid var(--border); border-radius: 16px; padding: 16px;
  box-shadow: 0 12px 32px rgba(2,6,23,0.07); backdrop-filter: blur(8px);
}
.metric-title { font-size: .9rem; color: var(--subtext); margin: 0; }
.metric-value { font-size: 1.8rem; font-weight: 700; margin-top: 6px; }
.kicker { font-size: .8rem; color: var(--subtext); }
.badge-open { color:#065f46; background:#d1fae5; border:1px solid #99f6e4; padding:2px 8px; border-radius:999px; font-size:.8rem; font-weight:600; }
.badge-closed { color:#7c2d12; background:#ffedd5; border:1px solid #fed7aa; padding:2px 8px; border-radius:999px; font-size:.8rem; font-weight:600; }
.badge-quality-high { color:#065f46; background:#d1fae5; border:1px solid #99f6e4; padding:2px 8px; border-radius:999px; font-size:.75rem; font-weight:600; }
.badge-quality-medium { color:#92400e; background:#fef3c7; border:1px solid #fcd34d; padding:2px 8px; border-radius:999px; font-size:.75rem; font-weight:600; }
.badge-quality-low { color:#7c2d12; background:#ffedd5; border:1px solid #fed7aa; padding:2px 8px; border-radius:999px; font-size:.75rem; font-weight:600; }
.override-tag { font-size:.75rem; color:#334155; background:#e2e8f0; border:1px solid #cbd5e1; padding:2px 8px; border-radius:999px; display:inline-block; margin-top:6px; }
.alert-divergence { color:#dc2626; background:#fef2f2; border:1px solid #fecaca; padding:8px 12px; border-radius:8px; font-size:.9rem; }
.alert-alignment { color:#059669; background:#f0fdf4; border:1px solid #bbf7d0; padding:8px 12px; border-radius:8px; font-size:.9rem; }
hr { border-top: 1px solid var(--border); }
.dataframe { background: var(--surface); border-radius: 12px; overflow: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED UTILITIES
# ───────────────────────────────────────────────────────────────────────────────
def fmt_ct(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return CT_TZ.localize(dt)
    return dt.astimezone(CT_TZ)

def between_time(df: pd.DataFrame, start_str: str, end_str: str) -> pd.DataFrame:
    return df.between_time(start_str, end_str) if not df.empty else df

def rth_slots_ct(target_date: date) -> List[datetime]:
    start_dt = fmt_ct(datetime.combine(target_date, time(8,30)))
    end_dt   = fmt_ct(datetime.combine(target_date, time(14,30)))
    slots = []
    cur = start_dt
    while cur <= end_dt:
        slots.append(cur)
        cur += timedelta(minutes=30)
    return slots

def gen_slots(start_dt: datetime, end_dt: datetime, step_min: int = 30) -> List[datetime]:
    start_dt = fmt_ct(start_dt); end_dt = fmt_ct(end_dt)
    out = []
    cur = start_dt
    while cur <= end_dt:
        out.append(cur)
        cur += timedelta(minutes=step_min)
    return out

def is_maintenance(dt: datetime) -> bool:
    return dt.hour == 16

def in_weekend_gap(dt: datetime) -> bool:
    wd = dt.weekday()
    if wd == 5: return True
    if wd == 6 and dt.hour < 17: return True
    if wd == 4 and dt.hour >= 17: return True
    return False

def count_effective_blocks(anchor_time: datetime, target_time: datetime) -> float:
    if target_time <= anchor_time:
        return 0.0
    t = anchor_time
    blocks = 0
    while t < target_time:
        t_next = t + timedelta(minutes=30)
        if not is_maintenance(t_next) and not in_weekend_gap(t_next):
            blocks += 1
        t = t_next
    return float(blocks)

def ensure_ohlc_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    for c in ["Open","High","Low","Close"]:
        if c not in df.columns:
            return pd.DataFrame()
    return df

def normalize_to_ct(df: pd.DataFrame, start_d: date, end_d: date) -> pd.DataFrame:
    if df.empty:
        return df
    df = ensure_ohlc_cols(df)
    if df.empty:
        return df
    if df.index.tz is None:
        df.index = df.index.tz_localize("US/Eastern")
    df.index = df.index.tz_convert(CT_TZ)
    sdt = fmt_ct(datetime.combine(start_d, time(0,0)))
    edt = fmt_ct(datetime.combine(end_d, time(23,59)))
    return df.loc[sdt:edt]

@st.cache_data(ttl=120, show_spinner=False)
def fetch_intraday(symbol: str, start_d: date, end_d: date, interval: str) -> pd.DataFrame:
    """Enhanced robust intraday fetch with improved error handling."""
    try:
        t = yf.Ticker(symbol)
        if interval in ["1m","2m","5m","15m"]:
            days = max(1, min(7, (end_d - start_d).days + 2))
            df = t.history(period=f"{days}d", interval=interval, prepost=True,
                           auto_adjust=False, back_adjust=False)
            df = normalize_to_ct(df, start_d - timedelta(days=1), end_d + timedelta(days=1))
            sdt = fmt_ct(datetime.combine(start_d, time(0,0)))
            edt = fmt_ct(datetime.combine(end_d, time(23,59)))
            df = df.loc[sdt:edt]
        else:
            df = t.history(
                start=(start_d - timedelta(days=5)).strftime("%Y-%m-%d"),
                end=(end_d + timedelta(days=2)).strftime("%Y-%m-%d"),
                interval=interval, prepost=True, auto_adjust=False, back_adjust=False,
            )
            df = normalize_to_ct(df, start_d, end_d)
        
        # Data quality check
        if not df.empty and "Close" in df.columns:
            price_changes = df["Close"].pct_change().abs()
            outliers = price_changes > 0.03  # >3% moves in single period
            if outliers.any():
                st.warning(f"⚠️ {symbol}: {outliers.sum()} periods with >3% moves detected")
        
        return df
    except Exception as e:
        st.error(f"Data fetch error for {symbol}: {str(e)}")
        return pd.DataFrame()

def resample_to_30m_ct(min_df: pd.DataFrame) -> pd.DataFrame:
    """Safe 30m resample with volume handling."""
    if min_df.empty or not isinstance(min_df.index, pd.DatetimeIndex):
        return pd.DataFrame()
    df = min_df.sort_index()
    cols = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
    agg = {}
    if "Open" in cols:   agg["Open"] = "first"
    if "High" in cols:   agg["High"] = "max"
    if "Low"  in cols:   agg["Low"]  = "min"
    if "Close" in cols:  agg["Close"]= "last"
    if "Volume" in cols: agg["Volume"]="sum"
    out = df.resample("30T", label="right", closed="right").agg(agg)
    out = out.dropna(subset=[c for c in ["Open","High","Low","Close"] if c in out.columns], how="any")
    return out

def get_prev_day_anchor_close_and_time(df_30m: pd.DataFrame, prev_day: date) -> Tuple[Optional[float], Optional[datetime]]:
    """Return last SPX bar ≤ 3:00 PM CT (close & its time) for prev_day."""
    if df_30m.empty:
        return None, None
    day_start = fmt_ct(datetime.combine(prev_day, time(0,0)))
    day_end   = fmt_ct(datetime.combine(prev_day, time(23,59)))
    d = df_30m.loc[day_start:day_end].copy()
    if d.empty:
        return None, None
    target = fmt_ct(datetime.combine(prev_day, time(15,0)))
    if target in d.index:
        return float(d.loc[target, "Close"]), target
    prior = d.loc[:target]
    if not prior.empty:
        return float(prior.iloc[-1]["Close"]), prior.index[-1]
    return None, None

def current_spx_slopes() -> Tuple[float, float]:
    top = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top, bottom

def project_fan_from_close(close_price: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
    top_slope, bottom_slope = current_spx_slopes()
    rows = []
    for slot in rth_slots_ct(target_day):
        blocks = count_effective_blocks(anchor_time, slot)
        top = close_price + top_slope * blocks
        bot = close_price - bottom_slope * blocks
        rows.append({"TimeDT": slot, "Time": slot.strftime("%H:%M"),
                     "Top": round(top,2), "Bottom": round(bot,2),
                     "Fan_Width": round(top-bot,2)})
    return pd.DataFrame(rows)

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED ES-SPX OFFSET TRACKING (1-HOUR LOOKBACK)
# ───────────────────────────────────────────────────────────────────────────────
def _nearest_le_index(idx: pd.DatetimeIndex, ts: pd.Timestamp) -> Optional[pd.Timestamp]:
    s = idx[idx <= ts]
    return s[-1] if len(s) else None

def get_recent_es_spx_offset(proj_day: date, spx_30m: pd.DataFrame) -> Dict:
    """
    Enhanced offset calculation with 1-hour lookback before market open.
    Returns detailed tracking info including stability metrics.
    """
    market_open = fmt_ct(datetime.combine(proj_day, time(8,30)))
    lookback_start = market_open - timedelta(hours=1)
    
    result = {
        "current_offset": None,
        "stability_score": 0,
        "offset_history": [],
        "data_source": "none",
        "quality": "low"
    }
    
    # Get anchor reference from previous day
    prev_day = proj_day - timedelta(days=1)
    spx_anchor_close, spx_anchor_time = get_prev_day_anchor_close_and_time(spx_30m, prev_day)
    if spx_anchor_close is None:
        return result
    
    def calculate_offset_series(es_df: pd.DataFrame, spx_ref: float) -> List[Dict]:
        """Calculate offset series with timestamps."""
        offsets = []
        if es_df.empty or "Close" not in es_df.columns:
            return offsets
            
        window_data = es_df.loc[lookback_start:market_open]
        for ts, row in window_data.iterrows():
            offset = float(row["Close"]) - spx_ref
            offsets.append({
                "timestamp": ts,
                "es_price": float(row["Close"]),
                "spx_ref": spx_ref,
                "offset": offset
            })
        return offsets
    
    # Try different data sources with quality scoring
    for interval, quality in [("1m", "high"), ("5m", "medium"), ("30m", "low")]:
        es_data = fetch_intraday("ES=F", proj_day - timedelta(days=1), proj_day, interval)
        if es_data.empty:
            continue
            
        offset_series = calculate_offset_series(es_data, spx_anchor_close)
        if not offset_series:
            continue
            
        # Calculate stability score (lower std dev = higher stability)
        offsets_values = [x["offset"] for x in offset_series]
        if len(offsets_values) >= 3:
            std_dev = np.std(offsets_values)
            stability = max(0, 100 - (std_dev * 10))  # Normalize to 0-100
            
            result.update({
                "current_offset": offsets_values[-1],
                "stability_score": round(stability, 1),
                "offset_history": offset_series[-12:],  # Last 12 readings
                "data_source": interval,
                "quality": quality,
                "std_dev": round(std_dev, 2),
                "min_offset": round(min(offsets_values), 2),
                "max_offset": round(max(offsets_values), 2),
                "readings_count": len(offsets_values)
            })
            break
    
    return result

def es_spx_offset_at_anchor(prev_day: date, spx_30m: pd.DataFrame) -> Optional[float]:
    """Legacy function for backward compatibility - now uses enhanced tracking."""
    proj_day = prev_day + timedelta(days=1)
    offset_data = get_recent_es_spx_offset(proj_day, spx_30m)
    return offset_data.get("current_offset")

# ───────────────────────────────────────────────────────────────────────────────
# INDICATORS & SCORING (Enhanced)
# ───────────────────────────────────────────────────────────────────────────────
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(up, index=series.index).ewm(alpha=1/length, adjust=False).mean()
    roll_down = pd.Series(down, index=series.index).ewm(alpha=1/length, adjust=False).mean()
    rs = roll_up / (roll_down + 1e-12)
    return 100 - (100 / (1 + rs))

def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    return pd.concat([tr1,tr2,tr3], axis=1).max(axis=1)

def calculate_bounce_quality(bar: pd.Series, volume_context: pd.Series = None) -> Dict:
    """
    Calculate bounce quality metrics for overnight bounces.
    Returns quality score and component breakdowns.
    """
    o = float(bar.get("Open", np.nan))
    h = float(bar.get("High", np.nan))
    l = float(bar.get("Low", np.nan))
    c = float(bar.get("Close", np.nan))
    v = float(bar.get("Volume", 0))
    
    quality_metrics = {
        "volume_score": 0,
        "wick_score": 0,
        "body_score": 0,
        "total_score": 0,
        "quality_tier": "low"
    }
    
    if any(np.isnan([o, h, l, c])):
        return quality_metrics
    
    # Volume quality (if available)
    if volume_context is not None and len(volume_context) >= 20 and v > 0:
        avg_volume = volume_context.rolling(20).mean().iloc[-1]
        if avg_volume > 0:
            volume_ratio = v / avg_volume
            if volume_ratio >= MIN_BOUNCE_VOLUME_RATIO:
                quality_metrics["volume_score"] = min(40, int(volume_ratio * 20))
    
    # Wick quality (rejection strength)
    body_size = abs(c - o)
    total_range = h - l
    if total_range > 0:
        # For bounce, look for lower wick rejection
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        
        if body_size > 0:
            wick_ratio = lower_wick / body_size
            if wick_ratio >= MIN_WICK_QUALITY:
                quality_metrics["wick_score"] = min(35, int(wick_ratio * 50))
    
    # Body quality (directional strength)
    if total_range > 0:
        body_pct = body_size / total_range
        if body_pct >= 0.3:  # Strong directional move
            quality_metrics["body_score"] = min(25, int(body_pct * 80))
    
    # Calculate total and tier
    total = sum([quality_metrics["volume_score"], quality_metrics["wick_score"], quality_metrics["body_score"]])
    quality_metrics["total_score"] = total
    
    if total >= 70:
        quality_metrics["quality_tier"] = "high"
    elif total >= 40:
        quality_metrics["quality_tier"] = "medium"
    else:
        quality_metrics["quality_tier"] = "low"
    
    return quality_metrics

# ───────────────────────────────────────────────────────────────────────────────
# BIAS / EDGE LOGIC (Enhanced)
# ───────────────────────────────────────────────────────────────────────────────
def compute_bias(price: float, top: float, bottom: float, tol_frac: float) -> str:
    """Enhanced bias calculation with momentum consideration."""
    if bottom <= price <= top:
        width = top - bottom
        center = (top + bottom)/2.0
        band = tol_frac * width
        if center - band <= price <= center + band:
            return "NO BIAS"
        dist_top = abs(top - price)
        dist_bottom = abs(price - bottom)
        return "UP" if dist_bottom < dist_top else "DOWN"
    return "NO BIAS"

def candle_class(open_, close_) -> str:
    if close_ > open_: return "Bullish"
    if close_ < open_: return "Bearish"
    return "Doji"

def touched_line(low, high, line) -> bool:
    return (low <= line <= high)

def classify_edge_touch(bar: pd.Series, top: float, bottom: float) -> Optional[Dict]:
    """Enhanced edge classification with quality metrics."""
    o = float(bar.get("Open", np.nan))
    h = float(bar.get("High", np.nan))
    l = float(bar.get("Low", np.nan))
    c = float(bar.get("Close", np.nan))
    cls = candle_class(o, c)

    inside = (bottom <= c <= top)
    above = (c > top)
    below = (c < bottom)

    # TOP touches
    if touched_line(l, h, top) and cls == "Bearish":
        if inside:
            return {"edge":"Top","case":"TopTouch_BearishClose_Inside",
                    "expected":"Breakdown to Bottom → plan to BUY from Bottom",
                    "direction_hint":"DownToBottomThenBuy",
                    "confidence": "medium"}
        if above:
            return {"edge":"Top","case":"TopTouch_BearishClose_Above",
                    "expected":"Top holds as support → market buys higher",
                    "direction_hint":"BuyHigherFromTop",
                    "confidence": "high"}

    # BOTTOM touches
    if touched_line(l, h, bottom) and cls == "Bullish":
        if inside:
            return {"edge":"Bottom","case":"BottomTouch_BullishClose_Inside",
                    "expected":"Breakout to Top → plan to SELL from Top",
                    "direction_hint":"UpToTopThenSell",
                    "confidence": "medium"}
        if below:
            return {"edge":"Bottom","case":"BottomTouch_BullishClose_Below",
                    "expected":"Bottom fails → market drops further",
                    "direction_hint":"SellFurtherDown",
                    "confidence": "high"}

    return None

# This completes Part 1. The enhanced offset tracking with 1-hour lookback 
# and bounce quality foundations are now in place.





# app.py - Part 2
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — Enhanced Edition Part 2
# Enhanced probability scoring with booster interaction effects and bounce quality
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED PROBABILITY BOOSTERS WITH INTERACTIONS
# ───────────────────────────────────────────────────────────────────────────────
def compute_boosters_score_enhanced(df_30m: pd.DataFrame, idx_30m: pd.Timestamp,
                                   expected_hint: str, weights: Dict[str,int],
                                   interaction_weights: Dict[str,int] = None) -> Tuple[int, Dict[str,int], Dict[str,int]]:
    """
    Enhanced booster scoring with interaction effects.
    Returns: (total_score, individual_components, interaction_bonuses)
    """
    if interaction_weights is None:
        interaction_weights = INTERACTION_WEIGHTS
    
    comps = {k:0 for k in ["ema","volume","wick","atr","tod","div"]}
    interactions = {k:0 for k in ["ema_volume","wick_atr","tod_ema"]}
    
    if df_30m.empty or idx_30m not in df_30m.index:
        return 0, comps, interactions
    
    upto = df_30m.loc[:idx_30m].copy()
    if upto.shape[0] < 10:
        return 0, comps, interactions

    # Individual booster calculations (enhanced)
    expected_near_term = "Up" if expected_hint in ("BuyHigherFromTop","UpToTopThenSell") else "Down"
    
    # EMA 8/21 with strength measurement
    ema8 = ema(upto["Close"], 8)
    ema21 = ema(upto["Close"], 21)
    ema_diff = ema8.iloc[-1] - ema21.iloc[-1]
    ema_strength = abs(ema_diff) / ema21.iloc[-1] * 1000  # Normalize strength
    
    ema_state = "Bullish" if ema8.iloc[-1] > ema21.iloc[-1] else ("Bearish" if ema8.iloc[-1] < ema21.iloc[-1] else "None")
    if (expected_near_term == "Up" and ema_state == "Bullish") or (expected_near_term == "Down" and ema_state == "Bearish"):
        base_ema = weights.get("ema", 0)
        # Bonus for stronger EMA separation
        strength_bonus = min(10, int(ema_strength * 2)) if ema_strength > 0.5 else 0
        comps["ema"] = base_ema + strength_bonus

    # Enhanced volume spike detection
    volume_quality = 0
    if "Volume" in upto.columns and upto["Volume"].notna().any():
        vol_series = upto["Volume"]
        vma_20 = vol_series.rolling(20).mean()
        vma_5 = vol_series.rolling(5).mean()
        
        if vma_20.notna().any() and vma_20.iloc[-1] > 0:
            current_vs_20 = vol_series.iloc[-1] / vma_20.iloc[-1]
            recent_vs_20 = vma_5.iloc[-1] / vma_20.iloc[-1] if vma_5.notna().any() else 1.0
            
            # Standard volume spike
            if current_vs_20 > 1.15:
                comps["volume"] = weights.get("volume", 0)
                volume_quality = 1
                
            # Sustained volume (recent average also elevated)
            if recent_vs_20 > 1.25:
                comps["volume"] += min(10, int((recent_vs_20 - 1.25) * 20))
                volume_quality = 2

    # Enhanced wick rejection analysis
    bar = upto.iloc[-1]
    o, h, l, c = float(bar["Open"]), float(bar["High"]), float(bar["Low"]), float(bar["Close"])
    body = abs(c - o) + 1e-9
    upper_wick = max(0.0, h - max(o, c))
    lower_wick = max(0.0, min(o, c) - l)
    total_range = h - l
    
    wick_quality = 0
    if expected_near_term == "Up":
        if lower_wick / body >= WICK_MIN_RATIO:
            base_wick = weights.get("wick", 0)
            # Bonus for exceptional wick rejection
            wick_ratio = lower_wick / body
            exceptional_bonus = min(15, int((wick_ratio - WICK_MIN_RATIO) * 25)) if wick_ratio > 1.0 else 0
            comps["wick"] = base_wick + exceptional_bonus
            wick_quality = 2 if wick_ratio > 1.0 else 1
    else:
        if upper_wick / body >= WICK_MIN_RATIO:
            base_wick = weights.get("wick", 0)
            wick_ratio = upper_wick / body
            exceptional_bonus = min(15, int((wick_ratio - WICK_MIN_RATIO) * 25)) if wick_ratio > 1.0 else 0
            comps["wick"] = base_wick + exceptional_bonus
            wick_quality = 2 if wick_ratio > 1.0 else 1

    # Enhanced ATR regime analysis
    atr_quality = 0
    tr = true_range(upto)
    atr = tr.rolling(ATR_LOOKBACK).mean()
    if atr.notna().sum() >= ATR_LOOKBACK:
        current_atr = atr.iloc[-1]
        atr_pctl = (atr.rank(pct=True).iloc[-1]) * 100.0
        
        # ATR trend (expanding vs contracting)
        atr_5 = atr.rolling(5).mean().iloc[-1]
        atr_trend = "expanding" if current_atr > atr_5 else "contracting"
        
        if expected_hint in ("BuyHigherFromTop", "UpToTopThenSell"):
            if atr_pctl <= ATR_LOW_PCTL:  # Low volatility good for breakouts
                comps["atr"] = weights.get("atr", 0)
                atr_quality = 2 if atr_trend == "contracting" else 1
        elif expected_hint in ("SellFurtherDown", "DownToBottomThenBuy"):
            if atr_pctl >= ATR_HIGH_PCTL:  # High volatility good for breakdowns
                comps["atr"] = weights.get("atr", 0)
                atr_quality = 2 if atr_trend == "expanding" else 1

    # Enhanced time-of-day scoring
    ts = fmt_ct(idx_30m.to_pydatetime())
    current_minutes = ts.hour * 60 + ts.minute
    tod_quality = 0
    
    for key_hour, key_min in KEY_TOD:
        key_minutes = key_hour * 60 + key_min
        if abs(current_minutes - key_minutes) <= KEY_TOD_WINDOW_MIN:
            base_tod = weights.get("tod", 0)
            # Bonus for exact key times
            if abs(current_minutes - key_minutes) <= 2:
                comps["tod"] = base_tod + 10
                tod_quality = 2
            else:
                comps["tod"] = base_tod
                tod_quality = 1
            break

    # Lightweight divergence (enhanced)
    if weights.get("div", 0) > 0:
        r = rsi(upto["Close"], RSI_LEN)
        if r.notna().sum() >= RSI_LEN + 2:
            window_bars = max(5, RSI_WINDOW_MIN)
            prior = upto.iloc[-window_bars:-1] if upto.shape[0] > window_bars else upto.iloc[:-1]
            if prior.shape[0] > 5:
                current_rsi = r.iloc[-1]
                prior_low = prior["Close"].idxmin()
                prior_high = prior["Close"].idxmax()
                
                if expected_near_term == "Up":
                    if (upto["Close"].iloc[-1] <= prior["Close"].min() and 
                        current_rsi > r.loc[prior_low] + 5):  # Stronger divergence threshold
                        divergence_strength = current_rsi - r.loc[prior_low]
                        comps["div"] = weights.get("div", 0) + min(10, int(divergence_strength / 2))
                else:
                    if (upto["Close"].iloc[-1] >= prior["Close"].max() and 
                        current_rsi < r.loc[prior_high] - 5):
                        divergence_strength = r.loc[prior_high] - current_rsi
                        comps["div"] = weights.get("div", 0) + min(10, int(divergence_strength / 2))

    # INTERACTION EFFECTS
    # EMA + Volume interaction (trend + conviction)
    if comps["ema"] > 0 and comps["volume"] > 0:
        if volume_quality == 2:  # Sustained volume
            interactions["ema_volume"] = interaction_weights.get("ema_volume", 0)

    # Wick + ATR interaction (rejection in appropriate volatility regime)
    if comps["wick"] > 0 and comps["atr"] > 0:
        if wick_quality >= 1 and atr_quality >= 1:
            interactions["wick_atr"] = interaction_weights.get("wick_atr", 0)

    # Time-of-Day + EMA interaction (key time + trend alignment)
    if comps["tod"] > 0 and comps["ema"] > 0:
        if tod_quality >= 1:
            interactions["tod_ema"] = interaction_weights.get("tod_ema", 0)

    # Calculate final score
    individual_total = sum(comps.values())
    interaction_total = sum(interactions.values())
    final_score = int(min(100, max(0, individual_total + interaction_total)))
    
    return final_score, comps, interactions

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED OVERNIGHT ANALYSIS
# ───────────────────────────────────────────────────────────────────────────────
def fetch_overnight_minute_enhanced(prev_day: date, proj_day: date) -> Tuple[pd.DataFrame, str, Dict]:
    """Enhanced overnight fetch with quality metrics."""
    start = fmt_ct(datetime.combine(prev_day, time(17,0)))
    end = fmt_ct(datetime.combine(proj_day, time(8,30)))
    
    quality_metrics = {
        "data_gaps": 0,
        "total_bars": 0,
        "coverage_pct": 0,
        "source_quality": "low"
    }
    
    # Try 1m first (highest quality)
    es_1m = fetch_intraday("ES=F", prev_day, proj_day, "1m")
    if not es_1m.empty:
        overnight_1m = es_1m.loc[start:end].copy()
        if not overnight_1m.empty:
            expected_bars = (end - start).total_seconds() / 60
            actual_bars = len(overnight_1m)
            quality_metrics.update({
                "total_bars": actual_bars,
                "coverage_pct": round((actual_bars / expected_bars) * 100, 1),
                "source_quality": "high"
            })
            return overnight_1m, "1m", quality_metrics
    
    # Try 5m (medium quality)
    es_5m = fetch_intraday("ES=F", prev_day, proj_day, "5m")
    if not es_5m.empty:
        overnight_5m = es_5m.loc[start:end].copy()
        if not overnight_5m.empty:
            expected_bars = (end - start).total_seconds() / (5 * 60)
            actual_bars = len(overnight_5m)
            quality_metrics.update({
                "total_bars": actual_bars,
                "coverage_pct": round((actual_bars / expected_bars) * 100, 1),
                "source_quality": "medium"
            })
            return overnight_5m, "5m", quality_metrics
    
    # Fallback to 30m (low quality)
    es_30m = fetch_intraday("ES=F", prev_day, proj_day, "30m")
    if not es_30m.empty:
        overnight_30m = es_30m.loc[start:end].copy()
        if not overnight_30m.empty:
            expected_bars = (end - start).total_seconds() / (30 * 60)
            actual_bars = len(overnight_30m)
            quality_metrics.update({
                "total_bars": actual_bars,
                "coverage_pct": round((actual_bars / expected_bars) * 100, 1),
                "source_quality": "low"
            })
            return overnight_30m, "30m", quality_metrics
    
    return pd.DataFrame(), "none", quality_metrics

def adjust_to_spx_frame_enhanced(es_df: pd.DataFrame, offset_data: Dict) -> Tuple[pd.DataFrame, Dict]:
    """Enhanced SPX frame adjustment with stability warnings."""
    df = es_df.copy()
    
    adjustment_info = {
        "offset_used": offset_data.get("current_offset", 0),
        "stability_warning": False,
        "quality_warning": False
    }
    
    if offset_data.get("stability_score", 0) < 50:
        adjustment_info["stability_warning"] = True
    
    if offset_data.get("quality") == "low":
        adjustment_info["quality_warning"] = True
    
    offset = offset_data.get("current_offset", 0)
    if offset is not None:
        for col in ["Open","High","Low","Close"]:
            if col in df:
                df[col] = df[col] - offset
    
    return df, adjustment_info

def nearest_30m_index(idx_30m: pd.DatetimeIndex, ts: pd.Timestamp) -> Optional[pd.Timestamp]:
    if idx_30m.empty:
        return None
    loc_df = idx_30m[idx_30m <= ts]
    if len(loc_df) == 0:
        return None
    return loc_df[-1]

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED PROBABILITY DASHBOARD
# ───────────────────────────────────────────────────────────────────────────────
def build_probability_dashboard_enhanced(prev_day: date, proj_day: date,
                                        anchor_close: float, anchor_time: datetime,
                                        tol_frac: float, weights: Dict[str,int],
                                        interaction_weights: Dict[str,int] = None) -> Dict:
    """
    Enhanced probability dashboard with detailed quality metrics.
    Returns comprehensive analysis including bounce quality and interaction effects.
    """
    result = {
        "touches_df": pd.DataFrame(),
        "fan_df": pd.DataFrame(),
        "offset_data": {},
        "data_quality": {},
        "summary_stats": {}
    }
    
    # Generate fan projections
    fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)
    result["fan_df"] = fan_df
    
    # Get SPX reference data
    spx_prev_30m = fetch_intraday("^GSPC", prev_day, prev_day, "30m")
    if spx_prev_30m.empty:
        spx_prev_30m = fetch_intraday("SPY", prev_day, prev_day, "30m")
    
    # Enhanced offset calculation
    offset_data = get_recent_es_spx_offset(proj_day, spx_prev_30m)
    result["offset_data"] = offset_data
    
    if offset_data.get("current_offset") is None:
        return result
    
    # Enhanced overnight data fetch
    on_bars, used_interval, data_quality = fetch_overnight_minute_enhanced(prev_day, proj_day)
    result["data_quality"] = data_quality
    
    if on_bars.empty:
        return result
    
    # Adjust to SPX frame with warnings
    on_adj, adjustment_info = adjust_to_spx_frame_enhanced(on_bars, offset_data)
    result["adjustment_info"] = adjustment_info
    
    # Resample for 30m analysis
    on_adj_30m = resample_to_30m_ct(on_adj)
    
    # Use appropriate timeframe for detection
    detect_df = on_adj if used_interval in ("1m", "5m") else on_adj_30m
    
    top_slope, bottom_slope = current_spx_slopes()
    rows = []
    interaction_summary = {k: 0 for k in ["ema_volume", "wick_atr", "tod_ema"]}
    
    for ts, bar in detect_df.iterrows():
        blocks = count_effective_blocks(anchor_time, ts)
        top = anchor_close + top_slope * blocks
        bottom = anchor_close - bottom_slope * blocks
        
        # Check for edge touch
        touch = classify_edge_touch(bar, top, bottom)
        if touch is None:
            continue
        
        # Find corresponding 30m index for booster analysis
        idx_30m = nearest_30m_index(on_adj_30m.index, ts)
        if idx_30m is None:
            score, comps, interactions = 0, {k:0 for k in ["ema","volume","wick","atr","tod","div"]}, {k:0 for k in ["ema_volume","wick_atr","tod_ema"]}
        else:
            score, comps, interactions = compute_boosters_score_enhanced(
                on_adj_30m, idx_30m, touch["direction_hint"], weights, interaction_weights
            )
        
        # Calculate bounce quality for this touch
        bounce_quality = calculate_bounce_quality(bar, on_adj.get("Volume"))
        
        # Accumulate interaction effects for summary
        for k, v in interactions.items():
            interaction_summary[k] += (1 if v > 0 else 0)
        
        price = float(bar["Close"])
        bias = compute_bias(price, top, bottom, tol_frac)
        
        rows.append({
            "TimeDT": ts, 
            "Time": ts.strftime("%H:%M"),
            "Price": round(price, 2), 
            "Top": round(top, 2), 
            "Bottom": round(bottom, 2),
            "Edge": touch["edge"], 
            "Case": touch["case"],
            "Expectation": touch["expected"], 
            "DirectionHint": touch["direction_hint"],
            "Confidence": touch.get("confidence", "medium"),
            "Bias": bias, 
            "Score": score,
            "EMA_w": comps.get("ema", 0), 
            "Vol_w": comps.get("volume", 0), 
            "Wick_w": comps.get("wick", 0),
            "ATR_w": comps.get("atr", 0), 
            "ToD_w": comps.get("tod", 0), 
            "Div_w": comps.get("div", 0),
            "EMA_Vol_bonus": interactions.get("ema_volume", 0),
            "Wick_ATR_bonus": interactions.get("wick_atr", 0),
            "ToD_EMA_bonus": interactions.get("tod_ema", 0),
            "Bounce_Quality": bounce_quality["quality_tier"],
            "Bounce_Score": bounce_quality["total_score"]
        })
    
    touches_df = pd.DataFrame(rows).sort_values("TimeDT").reset_index(drop=True)
    result["touches_df"] = touches_df
    
    # Summary statistics
    if not touches_df.empty:
        avg_score = touches_df["Score"].mean()
        high_quality_touches = len(touches_df[touches_df["Bounce_Quality"] == "high"])
        top_3_avg = touches_df.nlargest(3, "Score")["Score"].mean()
        
        result["summary_stats"] = {
            "total_touches": len(touches_df),
            "avg_score": round(avg_score, 1),
            "high_quality_bounces": high_quality_touches,
            "top_3_avg_score": round(top_3_avg, 1),
            "interaction_triggers": interaction_summary,
            "readiness_level": "high" if top_3_avg >= 70 else ("medium" if top_3_avg >= 40 else "low")
        }
    
    return result

# ───────────────────────────────────────────────────────────────────────────────
# BOUNCE QUALITY HELPERS
# ───────────────────────────────────────────────────────────────────────────────
def get_bounce_quality_badge(quality_tier: str) -> str:
    """Return HTML badge for bounce quality."""
    if quality_tier == "high":
        return '<span class="badge-quality-high">High Quality</span>'
    elif quality_tier == "medium":
        return '<span class="badge-quality-medium">Medium Quality</span>'
    else:
        return '<span class="badge-quality-low">Low Quality</span>'

def format_interaction_summary(interaction_data: Dict[str, int]) -> str:
    """Format interaction effects summary."""
    active_interactions = [k.replace("_", "+").upper() for k, v in interaction_data.items() if v > 0]
    if not active_interactions:
        return "None"
    return " • ".join(active_interactions)

# This completes Part 2 with enhanced probability scoring, booster interactions,
# and comprehensive bounce quality analysis.




# app.py - Part 3
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — Enhanced Edition Part 3
# BC Forecast improvements with slope divergence alerts and fan-bounce alignment
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED BC FORECAST WITH SLOPE ANALYSIS
# ───────────────────────────────────────────────────────────────────────────────
def analyze_slope_divergence(underlying_slope: float, contract_slope: float, 
                           contract_symbol: str, strike_info: str = None) -> Dict:
    """
    Analyze slope divergence between underlying and contract projections.
    Returns divergence analysis with alerts and opportunities.
    """
    # Expected contract behavior based on Greeks approximation
    # For simplicity, assume calls should move ~3-5x underlying for ATM/ITM
    # This is a rough heuristic - in practice you'd use actual delta
    
    if strike_info:
        # Extract strike from symbol (basic parsing)
        try:
            strike_num = float(''.join(filter(str.isdigit, contract_symbol))) / 100
            # This is very basic - assumes format like "6525c" = 6525.00 strike
        except:
            strike_num = None
    else:
        strike_num = None
    
    # Expected multiplier range (rough approximation)
    if underlying_slope > 0:  # Upward underlying move
        expected_multiplier_range = (2.5, 6.0)  # Calls should amplify
    else:  # Downward underlying move
        expected_multiplier_range = (-6.0, -2.5)  # Calls should amplify negatively
    
    # Calculate actual multiplier
    if abs(underlying_slope) > 0.001:
        actual_multiplier = contract_slope / underlying_slope
    else:
        actual_multiplier = 0
    
    analysis = {
        "underlying_slope": round(underlying_slope, 4),
        "contract_slope": round(contract_slope, 4),
        "actual_multiplier": round(actual_multiplier, 2),
        "expected_range": expected_multiplier_range,
        "divergence_type": "normal",
        "alert_level": "none",
        "opportunity_flag": False,
        "analysis_note": ""
    }
    
    # Analyze divergence patterns
    expected_min, expected_max = expected_multiplier_range
    
    if actual_multiplier < expected_min * 0.7:  # Significantly underperforming
        analysis.update({
            "divergence_type": "underperforming",
            "alert_level": "warning",
            "opportunity_flag": True,
            "analysis_note": f"Contract slope {actual_multiplier:.1f}x vs expected {expected_min:.1f}-{expected_max:.1f}x. Potential undervaluation or high IV."
        })
    elif actual_multiplier > expected_max * 1.3:  # Significantly overperforming
        analysis.update({
            "divergence_type": "overperforming", 
            "alert_level": "caution",
            "opportunity_flag": True,
            "analysis_note": f"Contract slope {actual_multiplier:.1f}x vs expected {expected_min:.1f}-{expected_max:.1f}x. Potential overvaluation or unusual flow."
        })
    elif expected_min <= actual_multiplier <= expected_max:
        analysis.update({
            "divergence_type": "normal",
            "alert_level": "none",
            "analysis_note": f"Contract behavior {actual_multiplier:.1f}x within expected range {expected_min:.1f}-{expected_max:.1f}x."
        })
    else:
        analysis.update({
            "divergence_type": "moderate",
            "alert_level": "info",
            "analysis_note": f"Contract slope {actual_multiplier:.1f}x slightly outside expected {expected_min:.1f}-{expected_max:.1f}x range."
        })
    
    return analysis

def calculate_fan_bounce_alignment(bounce_data: List[Dict], fan_anchor_close: float, 
                                 fan_anchor_time: datetime) -> Dict:
    """
    Analyze how overnight bounces align with fan projections.
    Returns alignment analysis and quality scoring.
    """
    top_slope, bottom_slope = current_spx_slopes()
    alignment_analysis = {
        "bounces": [],
        "alignment_score": 0,
        "quality_assessment": "low",
        "strategic_note": ""
    }
    
    total_alignment_points = 0
    max_possible_points = 0
    
    for i, bounce in enumerate(bounce_data, 1):
        bounce_time = bounce["timestamp"]
        bounce_price = bounce["spx_price"]
        
        # Calculate where fan edges were at bounce time
        blocks = count_effective_blocks(fan_anchor_time, bounce_time)
        fan_top = fan_anchor_close + top_slope * blocks
        fan_bottom = fan_anchor_close - bottom_slope * blocks
        fan_center = (fan_top + fan_bottom) / 2
        fan_width = fan_top - fan_bottom
        
        # Analyze bounce position relative to fan
        if bounce_price >= fan_top:
            position = "above_fan"
            distance_pct = ((bounce_price - fan_top) / fan_width) * 100
        elif bounce_price <= fan_bottom:
            position = "below_fan"
            distance_pct = ((fan_bottom - bounce_price) / fan_width) * 100
        else:
            position = "within_fan"
            # Calculate position within fan (0% = bottom, 100% = top)
            position_in_fan = ((bounce_price - fan_bottom) / fan_width) * 100
            distance_pct = position_in_fan
        
        # Score alignment quality
        alignment_points = 0
        max_possible_points += 100
        
        if position == "within_fan":
            # Bounces within fan are most significant
            if 10 <= distance_pct <= 25:  # Near bottom (ideal for bounce)
                alignment_points = 100
                quality = "excellent"
                note = f"Bounce #{i} at fan bottom edge ({distance_pct:.1f}% from bottom) - ideal setup"
            elif 75 <= distance_pct <= 90:  # Near top (resistance test)
                alignment_points = 90
                quality = "very_good"
                note = f"Bounce #{i} at fan top edge ({distance_pct:.1f}% from bottom) - resistance test"
            elif 35 <= distance_pct <= 65:  # Mid-fan
                alignment_points = 40
                quality = "neutral"
                note = f"Bounce #{i} in fan center ({distance_pct:.1f}% from bottom) - neutral zone"
            else:
                alignment_points = 60
                quality = "good"
                note = f"Bounce #{i} within fan ({distance_pct:.1f}% from bottom)"
        
        elif position == "below_fan":
            if distance_pct <= 15:  # Just below fan
                alignment_points = 85
                quality = "very_good"
                note = f"Bounce #{i} just below fan ({distance_pct:.1f}% below) - potential breakdown test"
            else:
                alignment_points = 30
                quality = "poor"
                note = f"Bounce #{i} far below fan ({distance_pct:.1f}% below)"
        
        else:  # above_fan
            if distance_pct <= 15:  # Just above fan
                alignment_points = 85
                quality = "very_good"
                note = f"Bounce #{i} just above fan ({distance_pct:.1f}% above) - potential breakout test"
            else:
                alignment_points = 30
                quality = "poor"
                note = f"Bounce #{i} far above fan ({distance_pct:.1f}% above)"
        
        total_alignment_points += alignment_points
        
        alignment_analysis["bounces"].append({
            "bounce_number": i,
            "timestamp": bounce_time,
            "spx_price": bounce_price,
            "fan_top": round(fan_top, 2),
            "fan_bottom": round(fan_bottom, 2),
            "fan_center": round(fan_center, 2),
            "position": position,
            "distance_pct": round(distance_pct, 1),
            "alignment_points": alignment_points,
            "quality": quality,
            "strategic_note": note
        })
    
    # Calculate overall alignment score
    if max_possible_points > 0:
        alignment_score = (total_alignment_points / max_possible_points) * 100
        alignment_analysis["alignment_score"] = round(alignment_score, 1)
        
        if alignment_score >= 80:
            alignment_analysis["quality_assessment"] = "excellent"
            alignment_analysis["strategic_note"] = "High-quality fan alignment suggests bounces confirm structural levels"
        elif alignment_score >= 60:
            alignment_analysis["quality_assessment"] = "good"
            alignment_analysis["strategic_note"] = "Good fan alignment provides reliable reference points"
        elif alignment_score >= 40:
            alignment_analysis["quality_assessment"] = "moderate"
            alignment_analysis["strategic_note"] = "Moderate alignment - use with additional confirmation"
        else:
            alignment_analysis["quality_assessment"] = "poor"
            alignment_analysis["strategic_note"] = "Poor fan alignment - bounces may be noise rather than structure"
    
    return alignment_analysis

def enhanced_bc_forecast_projection(b1_dt: datetime, b1_spx: float, b2_dt: datetime, b2_spx: float,
                                  contract_data: List[Dict], proj_day: date,
                                  fan_anchor_close: float, fan_anchor_time: datetime) -> Dict:
    """
    Enhanced BC Forecast with slope divergence analysis and fan alignment.
    """
    # Calculate underlying slope
    blocks_u = count_effective_blocks(b1_dt, b2_dt)
    u_slope = (b2_spx - b1_spx) / blocks_u if blocks_u > 0 else 0.0
    
    # Prepare bounce data for fan alignment
    bounce_data = [
        {"timestamp": b1_dt, "spx_price": b1_spx},
        {"timestamp": b2_dt, "spx_price": b2_spx}
    ]
    
    # Calculate fan-bounce alignment
    fan_alignment = calculate_fan_bounce_alignment(bounce_data, fan_anchor_close, fan_anchor_time)
    
    # Project underlying
    spx_projections = []
    for slot in rth_slots_ct(proj_day):
        blocks = count_effective_blocks(b1_dt, slot)
        price = b1_spx + u_slope * blocks
        spx_projections.append({
            "Time": slot.strftime("%H:%M"),
            "SPX_Projected": round(price, 2),
            "Blocks_From_B1": round(blocks, 1)
        })
    
    spx_df = pd.DataFrame(spx_projections)
    spx_df.insert(0, "Slot", spx_df["Time"].apply(lambda x: "⭐ 8:30" if x == "08:30" else ""))
    
    # Process contracts with slope analysis
    contract_results = []
    slope_analyses = []
    
    for contract in contract_data:
        symbol = contract["symbol"]
        b1_price = contract["b1_price"]
        b2_price = contract["b2_price"]
        b1_high = contract.get("b1_high")
        b2_high = contract.get("b2_high")
        
        # Calculate contract slope
        contract_slope = (b2_price - b1_price) / blocks_u if blocks_u > 0 else 0.0
        
        # Analyze slope divergence
        divergence_analysis = analyze_slope_divergence(u_slope, contract_slope, symbol)
        slope_analyses.append({
            "symbol": symbol,
            "analysis": divergence_analysis
        })
        
        # Project contract prices
        contract_projections = []
        for slot in rth_slots_ct(proj_day):
            blocks = count_effective_blocks(b1_dt, slot)
            price = b1_price + contract_slope * blocks
            contract_projections.append({
                "Time": slot.strftime("%H:%M"),
                f"{symbol}_Proj": round(price, 2)
            })
        
        contract_df = pd.DataFrame(contract_projections)
        
        # Add exit projections if high data provided
        if b1_high is not None and b2_high is not None:
            exit_slope = (b2_high - b1_high) / blocks_u if blocks_u > 0 else 0.0
            exit_projections = []
            for slot in rth_slots_ct(proj_day):
                blocks = count_effective_blocks(b1_dt, slot)
                exit_price = b1_high + exit_slope * blocks
                exit_projections.append({
                    "Time": slot.strftime("%H:%M"),
                    f"{symbol}_ExitRef": round(exit_price, 2)
                })
            exit_df = pd.DataFrame(exit_projections)
            contract_df = contract_df.merge(exit_df, on="Time")
        
        contract_results.append({
            "symbol": symbol,
            "slope": contract_slope,
            "df": contract_df
        })
    
    # Merge all projections
    result_df = spx_df.copy()
    for contract in contract_results:
        result_df = result_df.merge(contract["df"], on="Time", how="left")
    
    return {
        "projection_table": result_df,
        "underlying_slope": u_slope,
        "contract_slopes": {c["symbol"]: c["slope"] for c in contract_results},
        "slope_analyses": slope_analyses,
        "fan_alignment": fan_alignment,
        "quality_summary": {
            "alignment_score": fan_alignment["alignment_score"],
            "alignment_quality": fan_alignment["quality_assessment"],
            "divergence_alerts": len([a for a in slope_analyses if a["analysis"]["alert_level"] in ["warning", "caution"]]),
            "opportunity_flags": len([a for a in slope_analyses if a["analysis"]["opportunity_flag"]])
        }
    }

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED UI HELPERS FOR BC FORECAST
# ───────────────────────────────────────────────────────────────────────────────
def format_slope_analysis_alert(analysis: Dict) -> str:
    """Format slope divergence analysis for UI display."""
    alert_level = analysis["alert_level"]
    divergence_type = analysis["divergence_type"]
    note = analysis["analysis_note"]
    
    if alert_level == "warning":
        return f'<div class="alert-divergence">⚠️ UNDERPERFORMING: {note}</div>'
    elif alert_level == "caution":
        return f'<div class="alert-divergence">🔥 OVERPERFORMING: {note}</div>'
    elif alert_level == "info":
        return f'<div style="color:#0284c7; background:#f0f9ff; border:1px solid #7dd3fc; padding:8px 12px; border-radius:8px; font-size:.9rem;">ℹ️ MODERATE: {note}</div>'
    else:
        return f'<div style="color:#059669; background:#f0fdf4; border:1px solid #bbf7d0; padding:8px 12px; border-radius:8px; font-size:.9rem;">✅ NORMAL: {note}</div>'

def format_fan_alignment_summary(alignment_data: Dict) -> str:
    """Format fan-bounce alignment summary for UI."""
    score = alignment_data["alignment_score"]
    quality = alignment_data["quality_assessment"]
    note = alignment_data["strategic_note"]
    
    if quality == "excellent":
        return f'<div class="alert-alignment">🎯 EXCELLENT ALIGNMENT ({score}%): {note}</div>'
    elif quality == "good":
        return f'<div class="alert-alignment">✅ GOOD ALIGNMENT ({score}%): {note}</div>'
    elif quality == "moderate":
        return f'<div style="color:#92400e; background:#fef3c7; border:1px solid #fcd34d; padding:8px 12px; border-radius:8px; font-size:.9rem;">⚠️ MODERATE ALIGNMENT ({score}%): {note}</div>'
    else:
        return f'<div class="alert-divergence">❌ POOR ALIGNMENT ({score}%): {note}</div>'

def get_bounce_alignment_details(alignment_data: Dict) -> pd.DataFrame:
    """Convert bounce alignment data to DataFrame for display."""
    bounces = alignment_data.get("bounces", [])
    if not bounces:
        return pd.DataFrame()
    
    rows = []
    for bounce in bounces:
        rows.append({
            "Bounce": f"#{bounce['bounce_number']}",
            "Time": bounce["timestamp"].strftime("%H:%M"),
            "SPX Price": bounce["spx_price"],
            "Fan Top": bounce["fan_top"],
            "Fan Bottom": bounce["fan_bottom"],
            "Position": bounce["position"].replace("_", " ").title(),
            "Distance %": f"{bounce['distance_pct']:.1f}%",
            "Quality": bounce["quality"].replace("_", " ").title(),
            "Points": bounce["alignment_points"],
            "Note": bounce["strategic_note"]
        })
    
    return pd.DataFrame(rows)

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED CONTRACT OPPORTUNITY DETECTION
# ───────────────────────────────────────────────────────────────────────────────
def detect_contract_opportunities(slope_analyses: List[Dict], fan_data: Dict = None) -> List[Dict]:
    """
    Detect trading opportunities based on slope divergences and fan alignment.
    """
    opportunities = []
    
    for slope_analysis in slope_analyses:
        symbol = slope_analysis["symbol"]
        analysis = slope_analysis["analysis"]
        
        if not analysis["opportunity_flag"]:
            continue
        
        opportunity = {
            "symbol": symbol,
            "type": analysis["divergence_type"],
            "confidence": "medium",
            "reasoning": [],
            "risk_factors": [],
            "action_suggestion": ""
        }
        
        if analysis["divergence_type"] == "underperforming":
            opportunity["action_suggestion"] = "Consider buying if expecting mean reversion"
            opportunity["reasoning"].append("Contract slope below expected multiplier range")
            opportunity["risk_factors"].append("May indicate high implied volatility or poor liquidity")
            
            if fan_data and fan_data.get("alignment_score", 0) >= 70:
                opportunity["confidence"] = "high"
                opportunity["reasoning"].append("Strong fan alignment supports structural levels")
        
        elif analysis["divergence_type"] == "overperforming":
            opportunity["action_suggestion"] = "Consider selling or taking profits"
            opportunity["reasoning"].append("Contract slope above expected multiplier range")
            opportunity["risk_factors"].append("May indicate unusual flow or low implied volatility")
            
            if fan_data and fan_data.get("alignment_score", 0) >= 70:
                opportunity["confidence"] = "high"
                opportunity["reasoning"].append("Strong fan alignment validates overextension")
        
        opportunities.append(opportunity)
    
    return opportunities

# This completes Part 3 with enhanced BC Forecast analysis including:
# - Slope divergence alerts comparing contract vs underlying behavior
# - Fan-bounce alignment analysis for strategic context
# - Opportunity detection based on divergences and alignment quality
# - Enhanced UI formatting for alerts and analysis display


# app.py - Part 4 (Final Integration)
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — Enhanced Edition Part 4 (Complete App)
# Final UI integration and enhanced Plan Card with all analytics
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED SIDEBAR CONTROLS
# ───────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🔧 Enhanced Controls")
today_ct = datetime.now(CT_TZ).date()
prev_day = st.sidebar.date_input("Previous Trading Day", value=today_ct - timedelta(days=1))
proj_day = st.sidebar.date_input("Projection Day", value=prev_day + timedelta(days=1))
st.sidebar.caption("Anchor uses the **last SPX bar ≤ 3:00 PM CT** on the previous session (manual override available).")

st.sidebar.markdown("---")
st.sidebar.subheader("✍️ Manual Anchor (optional)")
use_manual_close = st.sidebar.checkbox("Enter 3:00 PM CT Close Manually", value=False)
manual_close_val = st.sidebar.number_input("Manual 3:00 PM Close", value=6400.00, step=0.01, format="%.2f",
                                           disabled=not use_manual_close)

st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Advanced Settings", expanded=False):
    st.caption("**Fan Configuration**")
    enable_slope = st.checkbox("Enable slope override",
                               value=("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state))
    top_slope_val = st.number_input("Top slope (+ per 30m)",
                                    value=float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT)),
                                    step=0.001, format="%.3f")
    bottom_slope_val = st.number_input("Bottom slope (− per 30m)",
                                       value=float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT)),
                                       step=0.001, format="%.3f")
    tol_frac = st.slider("Neutrality band (% of fan width)", 0, 40, 20, 1) / 100.0

    st.caption("**Probability Boosters**")
    enable_interactions = st.checkbox("Enable booster interactions", value=True)
    enable_divergence = st.checkbox("Enable oscillator divergence", value=False)
    
    col1, col2 = st.columns(2)
    with col1:
        w_ema = st.slider("EMA 8/21", 0, 40, WEIGHTS_DEFAULT["ema"], 5, key="adv_w_ema")
        w_vol = st.slider("Volume", 0, 40, WEIGHTS_DEFAULT["volume"], 5, key="adv_w_vol")
        w_wick = st.slider("Wick Rejection", 0, 40, WEIGHTS_DEFAULT["wick"], 5, key="adv_w_wick")
    with col2:
        w_atr = st.slider("ATR Regime", 0, 40, WEIGHTS_DEFAULT["atr"], 5, key="adv_w_atr")
        w_tod = st.slider("Time of Day", 0, 40, WEIGHTS_DEFAULT["tod"], 5, key="adv_w_tod")
        w_div = st.slider("Divergence", 0, 40, 10 if enable_divergence else 0, 5, 
                         disabled=not enable_divergence, key="adv_w_div")

    if enable_interactions:
        st.caption("**Interaction Bonuses**")
        w_ema_vol = st.slider("EMA + Volume", 0, 20, INTERACTION_WEIGHTS["ema_volume"], 2)
        w_wick_atr = st.slider("Wick + ATR", 0, 20, INTERACTION_WEIGHTS["wick_atr"], 2)
        w_tod_ema = st.slider("ToD + EMA", 0, 20, INTERACTION_WEIGHTS["tod_ema"], 2)
    else:
        w_ema_vol = w_wick_atr = w_tod_ema = 0

    colA, colB = st.columns(2)
    with colA:
        if st.button("Apply Settings", use_container_width=True):
            if enable_slope:
                st.session_state["top_slope_per_block"] = float(top_slope_val)
                st.session_state["bottom_slope_per_block"] = float(bottom_slope_val)
            else:
                for k in ("top_slope_per_block","bottom_slope_per_block"):
                    st.session_state.pop(k, None)
            
            st.session_state["custom_weights"] = {
                "ema": w_ema, "volume": w_vol, "wick": w_wick,
                "atr": w_atr, "tod": w_tod, "div": w_div
            }
            st.session_state["custom_interactions"] = {
                "ema_volume": w_ema_vol, "wick_atr": w_wick_atr, "tod_ema": w_tod_ema
            }
            st.success("Settings applied!")
    with colB:
        if st.button("Reset All", use_container_width=True):
            for k in ("top_slope_per_block","bottom_slope_per_block","custom_weights","custom_interactions"):
                st.session_state.pop(k, None)
            st.success("Reset to defaults!")

st.sidebar.markdown("---")
btn_anchor = st.sidebar.button("🔮 Refresh SPX Anchors", type="primary", use_container_width=True)
btn_prob = st.sidebar.button("🧠 Refresh Probability Board", type="secondary", use_container_width=True)

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED HEADER METRICS
# ───────────────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
now = datetime.now(CT_TZ)

with c1:
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-title">Current Time (CT)</p>
  <div class="metric-value">🕒 {now.strftime("%H:%M:%S")}</div>
  <div class="kicker">{now.strftime("%A, %B %d, %Y")}</div>
</div>
""", unsafe_allow_html=True)

with c2:
    is_wkday = now.weekday() < 5
    open_dt = now.replace(hour=8, minute=30, second=0, microsecond=0)
    close_dt = now.replace(hour=14, minute=30, second=0, microsecond=0)
    is_open = is_wkday and (open_dt <= now <= close_dt)
    badge = "badge-open" if is_open else "badge-closed"
    text = "Market Open" if is_open else "Closed"
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-title">Market Status</p>
  <div class="metric-value">📊 <span class="{badge}">{text}</span></div>
  <div class="kicker">RTH: 08:30–14:30 CT • Mon–Fri</div>
</div>
""", unsafe_allow_html=True)

with c3:
    ts, bs = current_spx_slopes()
    override_active = ("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state)
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-title">SPX Slopes / 30m</p>
  <div class="metric-value">📐 Top=+{ts:.3f} • Bottom=−{bs:.3f}</div>
  <div class="kicker">Asymmetric fan</div>
  {"<div class='override-tag'>Override active</div>" if override_active else ""}
</div>
""", unsafe_allow_html=True)

with c4:
    # Show enhancement status
    interactions_enabled = bool(st.session_state.get("custom_interactions"))
    enhanced_features = sum([
        1 if "custom_weights" in st.session_state else 0,
        1 if interactions_enabled else 0,
        1 if override_active else 0
    ])
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-title">Enhanced Features</p>
  <div class="metric-value">⚡ {enhanced_features}/3 Active</div>
  <div class="kicker">Weights • Interactions • Slopes</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED TABS IMPLEMENTATION
# ───────────────────────────────────────────────────────────────────────────────
tabAnchors, tabBC, tabProb, tabPlan = st.tabs(
    ["SPX Anchors", "BC Forecast Enhanced", "Probability Board Enhanced", "Plan Card Enhanced"]
)

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 1: SPX ANCHORS (ENHANCED)                                               ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabAnchors:
    st.subheader("SPX Anchors — Enhanced Fan Analysis (⭐ 8:30 highlight)")

    if btn_anchor:
        with st.spinner("Building enhanced anchor fan & strategy…"):
            spx_prev = fetch_intraday("^GSPC", prev_day, prev_day, "30m")
            if spx_prev.empty:
                spx_prev = fetch_intraday("SPY", prev_day, prev_day, "30m")
            if spx_prev.empty:
                st.error("❌ Previous day data missing — can't compute the anchor.")
                st.stop()

            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time  = fmt_ct(datetime.combine(prev_day, time(15,0)))
            else:
                anchor_close, anchor_time = get_prev_day_anchor_close_and_time(spx_prev, prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("Could not find a ≤3:00 PM CT close for the previous day.")
                    st.stop()

            fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

            # Enhanced offset analysis for context
            offset_data = get_recent_es_spx_offset(proj_day, spx_prev)
            
            # Pull RTH data
            spx_proj = fetch_intraday("^GSPC", proj_day, proj_day, "30m")
            if spx_proj.empty:
                spx_proj = fetch_intraday("SPY", proj_day, proj_day, "30m")
            spx_proj_rth = between_time(spx_proj, RTH_START, RTH_END)

            tslope, bslope = current_spx_slopes()
            rows = []
            iter_index = (spx_proj_rth.index if not spx_proj_rth.empty
                          else pd.DatetimeIndex(rth_slots_ct(proj_day)))
            
            for dt in iter_index:
                blocks = count_effective_blocks(anchor_time, dt)
                top = anchor_close + tslope * blocks
                bottom = anchor_close - bslope * blocks
                
                if not spx_proj_rth.empty and dt in spx_proj_rth.index:
                    bar_data = spx_proj_rth.loc[dt]
                    price = float(bar_data["Close"])
                    bias = compute_bias(price, top, bottom, tol_frac)
                    touch = classify_edge_touch(bar_data, top, bottom)
                    note = touch["expected"] if touch else "—"
                    confidence = touch.get("confidence", "—") if touch else "—"
                else:
                    price = np.nan
                    bias = "NO DATA"
                    note = "Fan only"
                    confidence = "—"
                
                rows.append({
                    "Slot": "⭐ 8:30" if dt.strftime("%H:%M")=="08:30" else "",
                    "Time": dt.strftime("%H:%M"),
                    "Price": (round(price,2) if price==price else np.nan),
                    "Bias": bias, 
                    "Top": round(top,2), 
                    "Bottom": round(bottom,2),
                    "Fan_Width": round(top-bottom,2),
                    "Confidence": confidence,
                    "Note": note
                })
            
            strat_df = pd.DataFrame(rows)

            st.session_state["anchors_enhanced"] = {
                "fan_df": fan_df, "strat_df": strat_df,
                "anchor_close": anchor_close, "anchor_time": anchor_time,
                "offset_data": offset_data,
                "prev_day": prev_day, "proj_day": proj_day, "tol_frac": tol_frac
            }

    if "anchors_enhanced" in st.session_state:
        data = st.session_state["anchors_enhanced"]
        fan_df = data["fan_df"]
        strat_df = data["strat_df"]
        offset_data = data["offset_data"]

        # Enhanced metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Anchor Close</p><div class='metric-value'>💠 {data['anchor_close']:.2f}</div><div class='kicker'>{data['anchor_time'].strftime('%Y-%m-%d %H:%M')}</div></div>", unsafe_allow_html=True)
        with m2:
            fan_830 = fan_df[fan_df["Time"] == "08:30"]
            width_830 = float(fan_830["Fan_Width"].iloc[0]) if not fan_830.empty else 0
            st.markdown(f"<div class='metric-card'><p class='metric-title'>8:30 Fan Width</p><div class='metric-value'>🧭 {width_830:.2f}</div><div class='kicker'>Points spread</div></div>", unsafe_allow_html=True)
        with m3:
            if offset_data.get("current_offset") is not None:
                stability = offset_data.get("stability_score", 0)
                quality = offset_data.get("quality", "unknown")
                st.markdown(f"<div class='metric-card'><p class='metric-title'>ES-SPX Offset</p><div class='metric-value'>Δ {offset_data['current_offset']:+.2f}</div><div class='kicker'>Stability: {stability}% ({quality})</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='metric-card'><p class='metric-title'>ES-SPX Offset</p><div class='metric-value'>❌ N/A</div><div class='kicker'>Data unavailable</div></div>", unsafe_allow_html=True)

        st.markdown("### 🎯 Fan Lines (Top / Bottom @ 30-min)")
        st.dataframe(fan_df[["Time","Top","Bottom","Fan_Width"]], use_container_width=True, hide_index=True)

        st.markdown("### 📋 Enhanced Strategy Table")
        st.caption("Enhanced bias logic with confidence levels and edge interaction analysis.")
        display_cols = ["Slot","Time","Price","Bias","Top","Bottom","Fan_Width","Confidence","Note"]
        st.dataframe(strat_df[display_cols], use_container_width=True, hide_index=True)
        
        # Offset stability warnings
        if offset_data.get("stability_warning"):
            st.warning("⚠️ ES-SPX offset stability is low - use caution with overnight-based analysis.")
        if offset_data.get("quality_warning"):
            st.info("ℹ️ Using lower-quality offset data (30m fallback) - consider refreshing closer to market open.")

    else:
        st.info("Use **Refresh SPX Anchors** in the sidebar to see enhanced analysis.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 2: BC FORECAST ENHANCED                                                 ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabBC:
    st.subheader("BC Forecast Enhanced — Slope Analysis & Fan Alignment")
    st.caption("Enhanced with slope divergence alerts and fan-bounce alignment scoring.")

    # Build 30m slot list for sessions
    asia_start = fmt_ct(datetime.combine(prev_day, time(19,0)))
    europe_end = fmt_ct(datetime.combine(proj_day, time(7,0)))
    session_slots = gen_slots(asia_start, europe_end, 30)
    slot_labels = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]

    with st.form("bc_enhanced_form", clear_on_submit=False):
        st.markdown("**Bounces (exactly two):** pick 30-min slots + underlying prices")
        col1, col2 = st.columns(2)
        with col1:
            b1_sel = st.selectbox("Bounce #1 Time (slot)", slot_labels, index=0)
            b1_spx = st.number_input("Bounce #1 SPX Price", value=6500.00, step=0.25, format="%.2f")
        with col2:
            b2_sel = st.selectbox("Bounce #2 Time (slot)", slot_labels, index=min(6, len(slot_labels)-1))
            b2_spx = st.number_input("Bounce #2 SPX Price", value=6512.00, step=0.25, format="%.2f")

        st.markdown("---")
        st.markdown("**Contract A (required)**")
        ca_sym = st.text_input("Contract A Label", value="6525c")
        ca_b1 = st.number_input("A: Price at Bounce #1", value=10.00, step=0.05, format="%.2f")
        ca_b2 = st.number_input("A: Price at Bounce #2", value=12.50, step=0.05, format="%.2f")
        ca_h1 = st.number_input("A: High after Bounce #1 (for exit ref)", value=14.00, step=0.05, format="%.2f")
        ca_h2 = st.number_input("A: High after Bounce #2 (for exit ref)", value=16.00, step=0.05, format="%.2f")

        st.markdown("---")
        st.markdown("**Contract B (optional)**")
        cb_enable = st.checkbox("Add Contract B", value=False)
        if cb_enable:
            cb_sym = st.text_input("Contract B Label", value="6515c")
            cb_b1 = st.number_input("B: Price at Bounce #1", value=9.50, step=0.05, format="%.2f")
            cb_b2 = st.number_input("B: Price at Bounce #2", value=11.80, step=0.05, format="%.2f")
            cb_h1 = st.number_input("B: High after Bounce #1 (for exit ref)", value=13.30, step=0.05, format="%.2f")
            cb_h2 = st.number_input("B: High after Bounce #2 (for exit ref)", value=15.10, step=0.05, format="%.2f")

        submit_bc = st.form_submit_button("📈 Enhanced BC Analysis", type="primary")

    if submit_bc:
        try:
            b1_dt = fmt_ct(datetime.strptime(b1_sel, "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(b2_sel, "%Y-%m-%d %H:%M"))
            
            if b2_dt <= b1_dt:
                st.error("Bounce #2 must occur after Bounce #1.")
            else:
                # Get anchor data for fan alignment
                if "anchors_enhanced" in st.session_state:
                    anchor_data = st.session_state["anchors_enhanced"]
                    fan_anchor_close = anchor_data["anchor_close"]
                    fan_anchor_time = anchor_data["anchor_time"]
                else:
                    # Use manual or fetch anchor
                    if use_manual_close:
                        fan_anchor_close = float(manual_close_val)
                        fan_anchor_time = fmt_ct(datetime.combine(prev_day, time(15,0)))
                    else:
                        spx_prev = fetch_intraday("^GSPC", prev_day, prev_day, "30m")
                        if spx_prev.empty:
                            spx_prev = fetch_intraday("SPY", prev_day, prev_day, "30m")
                        fan_anchor_close, fan_anchor_time = get_prev_day_anchor_close_and_time(spx_prev, prev_day)

                # Prepare contract data
                contract_data = [{
                    "symbol": ca_sym,
                    "b1_price": float(ca_b1),
                    "b2_price": float(ca_b2),
                    "b1_high": float(ca_h1),
                    "b2_high": float(ca_h2)
                }]

                if cb_enable:
                    contract_data.append({
                        "symbol": cb_sym,
                        "b1_price": float(cb_b1),
                        "b2_price": float(cb_b2),
                        "b1_high": float(cb_h1),
                        "b2_high": float(cb_h2)
                    })

                # Run enhanced BC forecast
                bc_result = enhanced_bc_forecast_projection(
                    b1_dt, float(b1_spx), b2_dt, float(b2_spx),
                    contract_data, proj_day, fan_anchor_close, fan_anchor_time
                )

                # Display results
                quality = bc_result["quality_summary"]
                
                # Enhanced metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>Underlying Slope /30m</p><div class='metric-value'>📐 {bc_result['underlying_slope']:+.3f}</div></div>", unsafe_allow_html=True)
                with m2:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>Fan Alignment</p><div class='metric-value'>🎯 {quality['alignment_score']:.1f}%</div><div class='kicker'>{quality['alignment_quality'].title()}</div></div>", unsafe_allow_html=True)
                with m3:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>Divergence Alerts</p><div class='metric-value'>⚠️ {quality['divergence_alerts']}</div><div class='kicker'>Slope anomalies</div></div>", unsafe_allow_html=True)
                with m4:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>Opportunities</p><div class='metric-value'>🎰 {quality['opportunity_flags']}</div><div class='kicker'>Trading signals</div></div>", unsafe_allow_html=True)

                # Fan alignment summary
                st.markdown("### 🎯 Fan-Bounce Alignment Analysis")
                alignment_summary = format_fan_alignment_summary(bc_result["fan_alignment"])
                st.markdown(alignment_summary, unsafe_allow_html=True)

                # Bounce details
                bounce_details = get_bounce_alignment_details(bc_result["fan_alignment"])
                if not bounce_details.empty:
                    st.dataframe(bounce_details, use_container_width=True, hide_index=True)

                # Slope divergence analysis
                st.markdown("### 📊 Slope Divergence Analysis")
                for slope_data in bc_result["slope_analyses"]:
                    symbol = slope_data["symbol"]
                    analysis = slope_data["analysis"]
                    
                    st.markdown(f"**{symbol}**: Slope {analysis['contract_slope']:+.3f} vs Underlying {analysis['underlying_slope']:+.3f} (Multiplier: {analysis['actual_multiplier']:+.1f}x)")
                    alert_html = format_slope_analysis_alert(analysis)
                    st.markdown(alert_html, unsafe_allow_html=True)

                # Opportunity detection
                opportunities = detect_contract_opportunities(bc_result["slope_analyses"], bc_result["fan_alignment"])
                if opportunities:
                    st.markdown("### 🎰 Trading Opportunities")
                    for opp in opportunities:
                        st.markdown(f"**{opp['symbol']}** ({opp['type'].title()}, {opp['confidence'].title()} confidence)")
                        st.markdown(f"- **Action**: {opp['action_suggestion']}")
                        st.markdown(f"- **Reasoning**: {' • '.join(opp['reasoning'])}")
                        if opp['risk_factors']:
                            st.markdown(f"- **Risks**: {' • '.join(opp['risk_factors'])}")

                # Main projection table
                st.markdown("### 🔮 Enhanced NY Session Projection")
                st.dataframe(bc_result["projection_table"], use_container_width=True, hide_index=True)

                st.session_state["bc_enhanced_result"] = bc_result

        except Exception as e:
            st.error(f"Enhanced BC Forecast error: {e}")

    if "bc_enhanced_result" not in st.session_state:
        st.info("Fill the form and click **Enhanced BC Analysis** to see slope divergence alerts and fan alignment.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 3: PROBABILITY BOARD ENHANCED                                           ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabProb:
    st.subheader("Probability Board Enhanced — Interaction Effects & Quality Analysis")

    if btn_prob:
        with st.spinner("Computing enhanced probability analysis with interactions…"):
            spx_prev = fetch_intraday("^GSPC", prev_day, prev_day, "30m")
            if spx_prev.empty:
                spx_prev = fetch_intraday("SPY", prev_day, prev_day, "30m")
            if spx_prev.empty:
                st.error("Could not fetch previous day SPX data.")
                st.stop()

            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time = fmt_ct(datetime.combine(prev_day, time(15,0)))
            else:
                anchor_close, anchor_time = get_prev_day_anchor_close_and_time(spx_prev, prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("Could not find a ≤3:00 PM CT close for the previous day.")
                    st.stop()

            # Get custom weights
            custom_weights = st.session_state.get("custom_weights", WEIGHTS_DEFAULT)
            custom_interactions = st.session_state.get("custom_interactions", INTERACTION_WEIGHTS)

            # Enhanced probability dashboard
            prob_result = build_probability_dashboard_enhanced(
                prev_day, proj_day, anchor_close, anchor_time, tol_frac,
                custom_weights, custom_interactions
            )

            st.session_state["prob_enhanced_result"] = prob_result

    if "prob_enhanced_result" in st.session_state:
        pr = st.session_state["prob_enhanced_result"]
        touches_df = pr["touches_df"]
        offset_data = pr["offset_data"]
        data_quality = pr["data_quality"]
        summary_stats = pr.get("summary_stats", {})

        # Enhanced metrics header
        cA, cB, cC, cD = st.columns(4)
        with cA:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Touch Quality</p><div class='metric-value'>🎯 {summary_stats.get('total_touches', 0)}</div><div class='kicker'>High: {summary_stats.get('high_quality_bounces', 0)}</div></div>", unsafe_allow_html=True)
        with cB:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Readiness Level</p><div class='metric-value'>🔥 {summary_stats.get('readiness_level', 'low').title()}</div><div class='kicker'>Top-3 avg: {summary_stats.get('top_3_avg_score', 0):.1f}</div></div>", unsafe_allow_html=True)
        with cC:
            interaction_summary = format_interaction_summary(summary_stats.get('interaction_triggers', {}))
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Active Interactions</p><div class='metric-value'>⚡ {interaction_summary}</div><div class='kicker'>Booster combinations</div></div>", unsafe_allow_html=True)
        with cD:
            stability = offset_data.get("stability_score", 0)
            coverage = data_quality.get("coverage_pct", 0)
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Data Quality</p><div class='metric-value'>📊 {coverage:.1f}%</div><div class='kicker'>Stability: {stability:.1f}%</div></div>", unsafe_allow_html=True)

        # Data quality warnings
        adj_info = pr.get("adjustment_info", {})
        if adj_info.get("stability_warning"):
            st.warning("⚠️ ES-SPX offset instability detected - scores may be less reliable")
        if adj_info.get("quality_warning"):
            st.info("ℹ️ Using fallback data quality - consider refreshing closer to market open")

        st.markdown("### 📡 Enhanced Overnight Edge Analysis")
        if touches_df.empty:
            st.info("No qualifying edge touches detected for this window.")
        else:
            # Enhanced touch display with quality badges
            enhanced_touches = touches_df.copy()
            enhanced_touches["Quality_Badge"] = enhanced_touches["Bounce_Quality"].apply(
                lambda x: f'<span class="badge-quality-{x.lower()}">{x.title()}</span>'
            )
            
            display_cols = [
                "Time", "Price", "Top", "Bottom", "Edge", "Confidence", "Score",
                "EMA_w", "Vol_w", "Wick_w", "ATR_w", "ToD_w", "Div_w",
                "EMA_Vol_bonus", "Wick_ATR_bonus", "ToD_EMA_bonus",
                "Bounce_Score", "Bounce_Quality"
            ]
            
            st.dataframe(enhanced_touches[display_cols], use_container_width=True, hide_index=True)

            # Interaction effects summary
            if summary_stats.get('interaction_triggers'):
                st.markdown("### ⚡ Booster Interaction Effects")
                for interaction, count in summary_stats['interaction_triggers'].items():
                    if count > 0:
                        interaction_name = interaction.replace('_', ' + ').upper()
                        st.markdown(f"- **{interaction_name}**: Triggered {count} time(s)")

    else:
        st.info("Use **Refresh Probability Board** in the sidebar to see enhanced analysis with interaction effects.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 4: PLAN CARD ENHANCED                                                   ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabPlan:
    st.subheader("Plan Card Enhanced — Comprehensive 8:25 Session Prep")

    anchors_ready = "anchors_enhanced" in st.session_state
    prob_ready = "prob_enhanced_result" in st.session_state
    bc_ready = "bc_enhanced_result" in st.session_state

    if not (anchors_ready and prob_ready):
        missing = []
        if not anchors_ready: missing.append("SPX Anchors")
        if not prob_ready: missing.append("Probability Board")
        st.info(f"Generate **{' and '.join(missing)}** first. BC Forecast optional but recommended for complete analysis.")
    else:
        an = st.session_state["anchors_enhanced"]
        pr = st.session_state["prob_enhanced_result"]
        bc = st.session_state.get("bc_enhanced_result")

        # Enhanced headline metrics
        readiness = pr.get("summary_stats", {}).get("top_3_avg_score", 0)
        quality_level = pr.get("summary_stats", {}).get("readiness_level", "low")
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Anchor & Offset</p><div class='metric-value'>💠 {an['anchor_close']:.2f}</div><div class='kicker'>Δ {an['offset_data'].get('current_offset', 0):+.2f}</div></div>", unsafe_allow_html=True)
        with m2:
            fan_830 = an["fan_df"][an["fan_df"]["Time"] == "08:30"]
            width_830 = float(fan_830["Fan_Width"].iloc[0]) if not fan_830.empty else 0
            st.markdown(f"<div class='metric-card'><p class='metric-title'>8:30 Fan Setup</p><div class='metric-value'>🧭 {width_830:.2f}</div><div class='kicker'>Points width</div></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Readiness Score</p><div class='metric-value'>🔥 {readiness:.1f}</div><div class='kicker'>{quality_level.title()} confidence</div></div>", unsafe_allow_html=True)
        with m4:
            if bc:
                alignment_score = bc["quality_summary"]["alignment_score"]
                alignment_quality = bc["quality_summary"]["alignment_quality"]
                st.markdown(f"<div class='metric-card'><p class='metric-title'>BC Alignment</p><div class='metric-value'>🎯 {alignment_score:.1f}%</div><div class='kicker'>{alignment_quality.title()}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='metric-card'><p class='metric-title'>BC Status</p><div class='metric-value'>➖ N/A</div><div class='kicker'>Not generated</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        
        # Two-column enhanced layout
        colL, colR = st.columns([1, 1])
        
        with colL:
            st.markdown("### 🎯 Enhanced Primary Setup")
            srow = an["strat_df"][an["strat_df"]["Time"] == "08:30"]
            if not srow.empty:
                srow = srow.iloc[0]
                st.markdown(f"**8:30 Analysis:**")
                st.markdown(f"- Bias: **{srow['Bias']}** (Confidence: {srow['Confidence']})")
                st.markdown(f"- Fan: Top {srow['Top']:.2f} / Bottom {srow['Bottom']:.2f}")
                st.markdown(f"- Width: {srow['Fan_Width']:.2f} points")
                st.markdown(f"- Setup: {srow['Note']}")

            # Enhanced probability insights
            st.markdown("### 🧠 Enhanced Probability Analysis")
            if not pr["touches_df"].empty:
                top_touches = pr["touches_df"].nlargest(3, "Score")
                interaction_summary = pr.get("summary_stats", {}).get("interaction_triggers", {})
                
                st.markdown(f"**Top Signals:**")
                for i, (_, r) in enumerate(top_touches.iterrows(), 1):
                    quality_badge = get_bounce_quality_badge(r["Bounce_Quality"])
                    st.markdown(f"{i}. {r['Time']}: **{r['Edge']}** touch → {r['DirectionHint']} (Score: {r['Score']}) {quality_badge}", unsafe_allow_html=True)
                
                if any(v > 0 for v in interaction_summary.values()):
                    active_interactions = [k.replace('_', '+').upper() for k, v in interaction_summary.items() if v > 0]
                    st.markdown(f"**Active Interactions:** {' • '.join(active_interactions)}")
            else:
                st.markdown("- No scored overnight touches available")

        with colR:
            st.markdown("### 💼 Enhanced Trade Execution")
            
            # BC Forecast integration
            if bc:
                st.markdown("**BC Projections @ 8:30:**")
                proj_table = bc["projection_table"]
                row_830 = proj_table[proj_table["Time"] == "08:30"]
                if not row_830.empty:
                    row = row_830.iloc[0]
                    st.markdown(f"- SPX: {float(row['SPX_Projected']):.2f}")
                    
                    # Show contract projections
                    for col in proj_table.columns:
                        if "_Proj" in col and col != "SPX_Projected":
                            contract_name = col.replace("_Proj", "")
                            st.markdown(f"- {contract_name}: {float(row[col]):.2f}")
                
                # Slope alerts
                divergence_alerts = bc["quality_summary"]["divergence_alerts"]
                opportunities = bc["quality_summary"]["opportunity_flags"]
                if divergence_alerts > 0:
                    st.markdown(f"**⚠️ {divergence_alerts} slope divergence alert(s)**")
                if opportunities > 0:
                    st.markdown(f"**🎰 {opportunities} trading opportunity signal(s)**")

            # Enhanced risk management
            st.markdown("**Risk Management:**")
            stability_score = an["offset_data"].get("stability_score", 0)
            if stability_score < 50:
                st.markdown("- ⚠️ Reduce size due to offset instability")
            if readiness >= 70:
                st.markdown("- ✅ Full size appropriate (high confidence)")
            elif readiness >= 40:
                st.markdown("- 📊 Medium size suggested")
            else:
                st.markdown("- 🚨 Small size or skip (low confidence)")

            st.markdown("**Invalidation Levels:**")
            st.markdown("- Hard stop: Close beyond opposite fan edge with confirming volume")
            st.markdown("- Soft stop: Bias flip without edge interaction")
            
            st.markdown("**Targets & Timing:**")
            st.markdown("- Primary: Opposite fan edge")
            st.markdown("- Exit refs: Use BC high projections if available")
            st.markdown("- Key times: 10:00 AM, 1:30 PM decision points")

        # System health summary
        st.markdown("---")
        st.markdown("### 🔧 System Health Summary")
        health_items = []
        
        # Data quality
        data_coverage = pr.get("data_quality", {}).get("coverage_pct", 0)
        if data_coverage >= 80:
            health_items.append("✅ Overnight data coverage excellent")
        elif data_coverage >= 60:
            health_items.append("⚠️ Overnight data coverage moderate")
        else:
            health_items.append("🚨 Overnight data coverage poor")

        # Offset stability
        offset_stability = an["offset_data"].get("stability_score", 0)
        if offset_stability >= 70:
            health_items.append("✅ ES-SPX offset stable")
        elif offset_stability >= 40:
            health_items.append("⚠️ ES-SPX offset moderately stable")
        else:
            health_items.append("🚨 ES-SPX offset unstable")

        # Enhancement status
        custom_weights = "custom_weights" in st.session_state
        custom_interactions = "custom_interactions" in st.session_state
        if custom_weights and custom_interactions:
            health_items.append("⚡ Enhanced scoring active")
        else:
            health_items.append("📊 Using default scoring")

        for item in health_items:
            st.markdown(f"- {item}")

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED FOOTER
# ───────────────────────────────────────────────────────────────────────────────
st.markdown("---")
colF1, colF2, colF3 = st.columns([1, 1, 2])

with colF1:
    if st.button("🔌 Test Data Connection"):
        td = fetch_intraday("^GSPC", today_ct - timedelta(days=3), today_ct, "30m")
        if td.empty:
            td = fetch_intraday("SPY", today_ct - timedelta(days=3), today_ct, "30m")
        if not td.empty:
            st.success(f"OK — received {len(td)} bars (30m).")
        else:
            st.error("Data fetch failed — try different dates.")

with colF2:
    if st.button("📊 System Status"):
        features = {
            "Enhanced Offset": "✅" if st.session_state.get("anchors_enhanced") else "❌",
            "Interaction Effects": "✅" if st.session_state.get("custom_interactions") else "❌",
            "Slope Analysis": "✅" if st.session_state.get("bc_enhanced_result") else "❌",
            "Quality Scoring": "✅" if st.session_state.get("prob_enhanced_result") else "❌"
        }
        for feature, status in features.items():
            st.write(f"{status} {feature}")

with colF3:
    st.caption("🔮 SPX Prophet Enhanced • SPX-only • Enhanced offset tracking • Booster interactions • Slope divergence alerts • Fan-bounce alignment • Quality scoring • ⭐ 8:30 focus")

# This completes the enhanced SPX Prophet application with all requested improvements integrated