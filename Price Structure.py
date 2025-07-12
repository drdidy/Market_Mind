import streamlit as st
from math import log, sqrt, exp
from datetime import datetime, timedelta

# --- Normal CDF Approximation (no scipy) ---
def norm_cdf(x):
    """Cumulative distribution function for standard normal distribution."""
    k = 1.0 / (1.0 + 0.2316419 * abs(x))
    a1, a2, a3, a4, a5 = 0.319381530, -0.356563782, 1.781477937, -1.821255978, 1.330274429
    poly = k * (a1 + k * (a2 + k * (a3 + k * (a4 + k * a5))))
    approx = 1.0 - (1.0 / sqrt(2 * 3.141592653589793)) * exp(-0.5 * x * x) * poly
    return approx if x >= 0 else 1.0 - approx

# --- Option Pricing Core Function ---
def calculate_option_price(S, K, T_min, r=0.01, sigma=0.15, option_type='call'):
    T = T_min / (365 * 24 * 60)  # Convert minutes to years
    if T <= 0:
        return 0.0
    try:
        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
    except:
        return 0.0

    if option_type == 'call':
        price = S * norm_cdf(d1) - K * exp(-r * T) * norm_cdf(d2)
    elif option_type == 'put':
        price = K * exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
    else:
        raise ValueError("Invalid option_type. Use 'call' or 'put'.")
    
    return round(price, 2)

# --- Streamlit App ---
st.set_page_config(page_title="SPX 0DTE Option Calculator", layout="centered")
st.title("📈 SPX 0DTE Option Price Estimator")
st.markdown("Estimate the value of SPX 0DTE options based on projected price and time.")

# --- Inputs ---
col1, col2 = st.columns(2)

with col1:
    entry_time = st.time_input("Current Time", value=datetime.now().time())
    projected_time = st.time_input("Projected Time", value=(datetime.now() + timedelta(minutes=30)).time())

with col2:
    current_price = st.number_input("Current or Projected SPX Price", value=6240.0, step=0.1)
    strike = st.number_input("Option Strike", value=6250.0, step=1.0)

option_type = st.selectbox("Option Type", ['call', 'put'])
iv = st.slider("Implied Volatility (IV %)", min_value=5.0, max_value=40.0, value=15.0, step=0.5)
entry_option_price = st.number_input("Entry Option Price (Optional)", value=0.0, step=0.1)

# --- Time Difference ---
now = datetime.combine(datetime.today(), entry_time)
future = datetime.combine(datetime.today(), projected_time)
if future < now:
    future += timedelta(days=1)

time_diff_minutes = int((future - now).total_seconds() / 60)

# --- Calculation ---
projected_option_price = calculate_option_price(
    S=current_price,
    K=strike,
    T_min=time_diff_minutes,
    sigma=iv / 100,
    option_type=option_type
)

st.markdown(f"### ⏳ Time to Expiry: {time_diff_minutes} minutes")
st.markdown(f"### 💰 Projected Option Price: **${projected_option_price}**")

if entry_option_price > 0:
    pnl = projected_option_price - entry_option_price
    pnl_color = "🟢" if pnl >= 0 else "🔴"
    st.markdown(f"### {pnl_color} P/L: **${round(pnl, 2)}**")

st.caption("This is a simplified Black-Scholes model with adjusted normal CDF. Real-world prices may differ due to volatility skew, gamma risk, and order flow.")
