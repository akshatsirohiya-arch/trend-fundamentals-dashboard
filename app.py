# trend-fundamentals-dashboard/app.py
# CLEAN VERSION — NO FUNDAMENTALS
# Universe: All US-listed common stocks with Market Cap >= chosen threshold (default $1.5B)
# Momentum-only scoring (Slope + TA)

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import io
import time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Momentum Scanner (No Fundamentals)")

# ----------------------------------
# CONSTANTS (US SYMBOL SOURCES)
# ----------------------------------
# Official NASDAQ symbol directories: NASDAQ-listed + other exchanges:contentReference[oaicite:1]{index=1}
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ----------------------------------
# UTILITIES
# ----------------------------------

def compute_slope(close_series: pd.Series) -> float:
    y = close_series.values
    x = np.arange(len(y))
    if len(y) < 5:
        return np.nan
    try:
        slope = np.polyfit(x, y, 1)[0]
        return slope
    except Exception:
        return np.nan

@st.cache_data(show_spinner=False)
def fetch_prices(tickers, period="6mo", interval="1d"):
    try:
        data = yf.download(tickers, period=period, interval=interval, progress=False)
        return data
    except Exception:
        return None

def get_market_cap_yf(ticker: str):
    """
    Get market cap from yfinance in USD.
    Tries fast_info first, then falls back to info.
    """
    try:
        t = yf.Ticker(ticker)
        mc = None

        fast = getattr(t, "fast_info", None)
        if fast is not None:
            mc = fast.get("market_cap", None)

        if mc is None:
            info = t.info or {}
            mc = info.get("marketCap", None)

        return mc
    except Exception:
        return None

@st.cache_data(show_spinner=True, ttl=24 * 60 * 60)
def load_us_symbol_universe() -> pd.DataFrame:
    """
    Load US-listed symbols (NASDAQ-listed + other US exchanges),
    filter out ETFs, test issues, and obvious non-common stuff.
    Returns a DataFrame with at least: ['Ticker', 'SecurityName'].
    """

    # ---- NASDAQ-listed ----
    r_nq = requests.get(NASDAQ_LISTED_URL, headers=HTTP_HEADERS, timeout=30)
    r_nq.raise_for_status()
    buf_nq = io.StringIO(r_nq.text)

    df_nq = pd.read_csv(buf_nq, sep="|")
    # Drop the last "File Creation Time" row
    df_nq = df_nq[df_nq["Symbol"] != "File Creation Time"]

    # Keep only non-test, non-ETF
    df_nq = df_nq[(df_nq["Test Issue"] == "N") & (df_nq["ETF"] == "N")].copy()
    df_nq["Ticker"] = df_nq["Symbol"].str.strip()
    df_nq["SecurityName"] = df_nq["Security Name"].astype(str)

    # ---- Other-listed (NYSE, NYSE American, ARCA, etc.) ----
    r_ol = requests.get(OTHER_LISTED_URL, headers=HTTP_HEADERS, timeout=30)
    r_ol.raise_for_status()
    buf_ol = io.StringIO(r_ol.text)

    df_ol = pd.read_csv(buf_ol, sep="|")
    # Drop "File Creation Time" row
    df_ol = df_ol[df_ol["ACT Symbol"] != "File Creation Time"]

    # Keep only non-test, non-ETF
    df_ol = df_ol[(df_ol["Test Issue"] == "N") & (df_ol["ETF"] == "N")].copy()
    df_ol["Ticker"] = df_ol["ACT Symbol"].str.strip()
    df_ol["SecurityName"] = df_ol["Security Name"].astype(str)

    # Concatenate bases
    base = pd.concat(
        [
            df_nq[["Ticker", "SecurityName"]],
            df_ol[["Ticker", "SecurityName"]],
        ],
        ignore_index=True,
    )

    # Basic clean-up: drop duplicates
    base = base.drop_duplicates(subset=["Ticker"]).reset_index(drop=True)

    # Optional: filter out obvious non-common-equity instruments by name
    bad_keywords = [
        " ETF", " ETN", " Fund", " Trust", "Notes", "Note", "Bond",
        " Preferred", " Preference", "Pfd", "Rights", "Right",
        "Unit", "Warrant", "Depositary", "Depositary Share",
        "ADR", "Closed End", "Index",
    ]
    pattern = "|".join(bad_keywords)

    base = base[~base["SecurityName"].str.contains(pattern, case=False, na=False)]

    return base


@st.cache_data(show_spinner=True, ttl=24 * 60 * 60)
def build_us_universe(min_mcap_usd: float = 1_500_000_000) -> pd.DataFrame:
    """
    Build universe of US common stocks with market cap >= min_mcap_usd.
    Market cap in USD via yfinance.
    """
    base = load_us_symbol_universe()
    tickers = base["Ticker"].tolist()

    rows = []
    for i, tk in enumerate(tickers, start=1):
        mc = get_market_cap_yf(tk)
        if mc is None:
            continue

        if mc >= min_mcap_usd:
            rows.append(
                {
                    "Ticker": tk,
                    "MarketCapUSD": mc,
                }
            )

        # Gentle throttling to avoid hammering yfinance
        time.sleep(0.03)

    uni = pd.DataFrame(rows)
    if uni.empty:
        return uni

    uni = uni.merge(base, on="Ticker", how="left")
    uni = uni.sort_values("MarketCapUSD", ascending=False).reset_index(drop=True)
    return uni


# ----------------------------------
# PROCESS BATCH
# ----------------------------------

def process_batch(tickers):
    data = fetch_prices(tickers)
    if data is None or "Close" not in data:
        return pd.DataFrame()

    close_df = data["Close"]
    rows = []

    for tk in close_df.columns:
        s = close_df[tk].dropna()
        if len(s) < 10:
            continue

        slope = compute_slope(s[-60:])  # last 60 bars
        ret_1m = (s.iloc[-1] / s.iloc[-21] - 1) * 100 if len(s) >= 22 else np.nan
        ret_3m = (s.iloc[-1] / s.iloc[-63] - 1) * 100 if len(s) >= 64 else np.nan

        rows.append(
            {
                "Ticker": tk,
                "Close": s.iloc[-1],
                "Slope": slope,
                "Ret1M": ret_1m,
                "Ret3M": ret_3m,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Normalize slope
    if df["Slope"].notna().any():
        mn, mx = df["Slope"].min(), df["Slope"].max()
        df["SlopeNorm"] = (df["Slope"] - mn) / (mx - mn + 1e-9)
    else:
        df["SlopeNorm"] = 0

    # Final score
    df["FinalScore"] = (
        0.7 * df["SlopeNorm"].fillna(0)
        + 0.15 * df["Ret1M"].fillna(0)
        + 0.15 * df["Ret3M"].fillna(0)
    )

    return df.sort_values("FinalScore", ascending=False).reset_index(drop=True)


# ----------------------------------
# STREAMLIT UI
# ----------------------------------

st.title("Momentum Scanner — Auto Universe (No Fundamentals)")
st.write("Universe: US-listed common stocks with Market Cap ≥ chosen threshold (USD)")

# Sidebar controls
min_mcap_bn = st.sidebar.number_input(
    "Min Market Cap ($Bn)",
    min_value=0.5,
    max_value=500.0,
    value=1.5,   # your requested default
    step=0.5,
)
min_mcap_usd = min_mcap_bn * 1_000_000_000

batch_size = st.sidebar.slider("Batch Size", 50, 500, 150, step=50)

if st.sidebar.button("Refresh Ticker Universe"):
    build_us_universe.clear()
    fetch_prices.clear()
    st.experimental_rerun()

if st.sidebar.button("Clear All Cache"):
    st.cache_data.clear()
    st.experimental_rerun()

# Build universe
with st.spinner("Building US equity universe from NASDAQ symbol files + yfinance..."):
    uni_df = build_us_universe(min_mcap_usd=min_mcap_usd)

if uni_df.empty:
    st.error("Universe is empty. NASDAQ symbol files or yfinance may be unavailable/blocked.")
    st.stop()

st.success(
    f"Universe size: {len(uni_df)} US stocks with Market Cap ≥ ${min_mcap_bn:.2f}B"
)

with st.expander("Show universe (ticker, name, market cap)"):
    st.dataframe(uni_df[["Ticker", "SecurityName", "MarketCapUSD"]])

# Scan these tickers
tickers_list = uni_df["Ticker"].tolist()

final_df_list = []
for i in range(0, len(tickers_list), batch_size):
    batch = tickers_list[i: i + batch_size]
    st.write(
        f"Processing {len(batch)} tickers "
        f"({i+1}–{i+len(batch)} of {len(tickers_list)})..."
    )
    out = process_batch(batch)
    if not out.empty:
        final_df_list.append(out)

if final_df_list:
    final = (
        pd.concat(final_df_list)
        .sort_values("FinalScore", ascending=False)
        .reset_index(drop=True)
    )

    # Keep your <20% 1M rule, same as before
    final = final[final["Ret1M"] < 20]

    st.subheader("Top US Momentum Picks (<20% 1M return)")
    st.dataframe(final.head(250))
else:
    st.error("No results. Check universe or yfinance status.")
