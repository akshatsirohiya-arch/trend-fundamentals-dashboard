# trend-fundamentals-dashboard/app.py
# CLEAN VERSION — NO FUNDAMENTALS
# Universe: US-listed common stocks with Market Cap >= chosen threshold (default $1.5B)
# Momentum-only scoring (Slope + TA)

import os
import time
import io

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(layout="wide", page_title="Momentum Scanner (No Fundamentals)")

# ----------------------------------
# CONSTANTS (US SYMBOL SOURCES)
# ----------------------------------

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# FMP Batch Market Cap endpoint
FMP_BATCH_MCAP_URL = "https://financialmodelingprep.com/stable/market-capitalization-batch"


# ----------------------------------
# UTILITIES
# ----------------------------------

def get_fmp_api_key():
    """
    Get FMP API key from Streamlit secrets or environment variable.
    Raises ValueError if not found.
    """
    key = None

    # Try Streamlit secrets (if defined)
    try:
        if "FMP_API_KEY" in st.secrets:
            key = st.secrets["FMP_API_KEY"]
    except Exception:
        key = None

    # Fallback to env var
    if not key:
        key = os.environ.get("FMP_API_KEY")

    if not key:
        raise ValueError(
            "FMP_API_KEY not set. Add it to Streamlit secrets or environment variables."
        )

    return key


def compute_slope(close_series):
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


# ----------------------------------
# SYMBOL UNIVERSE (US LISTED)
# ----------------------------------

@st.cache_data(show_spinner=True, ttl=24 * 60 * 60)
def load_us_symbol_universe():
    """
    Load US-listed symbols (NASDAQ-listed + other US exchanges).
    Applies:
      - Exclude ETFs via ETF flag
      - Exclude Test issues
      - Strict bad_keywords filter on SecurityName
    Returns DataFrame with columns: ['Ticker', 'SecurityName'].
    """

    # ---- NASDAQ-listed ----
    r_nq = requests.get(NASDAQ_LISTED_URL, headers=HTTP_HEADERS, timeout=30)
    r_nq.raise_for_status()
    buf_nq = io.StringIO(r_nq.text)

    df_nq = pd.read_csv(buf_nq, sep="|")
    df_nq = df_nq[df_nq["Symbol"] != "File Creation Time"]

    # Only non-test, non-ETF
    df_nq = df_nq[
        (df_nq["Test Issue"] == "N") & (df_nq["ETF"] == "N")
    ].copy()
    df_nq["Ticker"] = df_nq["Symbol"].astype(str).str.strip()
    df_nq["SecurityName"] = df_nq["Security Name"].astype(str)

    # ---- Other-listed (NYSE, etc.) ----
    r_ol = requests.get(OTHER_LISTED_URL, headers=HTTP_HEADERS, timeout=30)
    r_ol.raise_for_status()
    buf_ol = io.StringIO(r_ol.text)

    df_ol = pd.read_csv(buf_ol, sep="|")
    df_ol = df_ol[df_ol["ACT Symbol"] != "File Creation Time"]
    df_ol = df_ol[
        (df_ol["Test Issue"] == "N") & (df_ol["ETF"] == "N")
    ].copy()
    df_ol["Ticker"] = df_ol["ACT Symbol"].astype(str).str.strip()
    df_ol["SecurityName"] = df_ol["Security Name"].astype(str)

    base = pd.concat(
        [
            df_nq[["Ticker", "SecurityName"]],
            df_ol[["Ticker", "SecurityName"]],
        ],
        ignore_index=True,
    )

    # Drop null / empty tickers & dedupe
    base = base[base["Ticker"].notna()].copy()
    base["Ticker"] = base["Ticker"].astype(str).str.strip()
    base = base[base["Ticker"] != ""]
    base = base.drop_duplicates(subset=["Ticker"]).reset_index(drop=True)

    # Strict keyword filter (you said you're okay keeping this strict)
    bad_keywords = [
        " ETF",
        " ETN",
        " Fund",
        " Trust",
        "Notes",
        "Note",
        "Bond",
        " Preferred",
        " Preference",
        "Pfd",
        "Rights",
        "Right",
        "Unit",
        "Warrant",
        "Depositary",
        "Depositary Share",
        "ADR",
        "Closed End",
        "Index",
    ]
    pattern = "|".join(bad_keywords)
    base = base[
        ~base["SecurityName"].str.contains(pattern, case=False, na=False)
    ]

    return base


@st.cache_data(show_spinner=True, ttl=24 * 60 * 60)
def build_us_universe(min_mcap_usd=1_500_000_000):
    """
    Build universe of US stocks with market cap >= min_mcap_usd.
    Uses FMP Batch Market Cap API for market cap.

    Returns:
      uni  : DataFrame [Ticker, MarketCapUSD, SecurityName]
      stats: dict with debug counts
    """
    api_key = get_fmp_api_key()
    base = load_us_symbol_universe()

    # Make sure tickers are clean strings, non-null
    base = base[base["Ticker"].notna()].copy()
    base["Ticker"] = base["Ticker"].astype(str).str.strip()
    base = base[base["Ticker"] != ""]

    tickers = base["Ticker"].tolist()

    total_symbols = len(tickers)
    missing_mcap = 0
    below_threshold = 0

    rows = []

    # FMP batch endpoint accepts comma-separated symbols.
    chunk_size = 150

    for i in range(0, len(tickers), chunk_size):
        raw_chunk = tickers[i : i + chunk_size]
        # Ensure each is a clean string and drop empties
        chunk = [str(tk).strip() for tk in raw_chunk if pd.notna(tk) and str(tk).strip() != ""]
        if not chunk:
            continue

        symbols_str = ",".join(chunk)

        params = {
            "symbols": symbols_str,
            "apikey": api_key,
        }

        try:
            resp = requests.get(
                FMP_BATCH_MCAP_URL,
                params=params,
                headers=HTTP_HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            # If one batch fails, treat all as missing mcap
            missing_mcap += len(chunk)
            continue

        # FMP returns a list of {symbol, marketCap, ...}
        mcap_map = {}
        if isinstance(data, list):
            for item in data:
                sym = item.get("symbol")
                mcap = item.get("marketCap")
                if sym is not None:
                    mcap_map[str(sym).upper()] = mcap

        for tk in chunk:
            mc = mcap_map.get(tk.upper(), None)
            if mc is None:
                missing_mcap += 1
                continue
            if mc < min_mcap_usd:
                below_threshold += 1
                continue

            rows.append({"Ticker": tk, "MarketCapUSD": mc})

        # light throttle to be polite
        time.sleep(0.1)

    uni = pd.DataFrame(rows)
    if not uni.empty:
        uni = uni.merge(base, on="Ticker", how="left")
        uni = uni.sort_values("MarketCapUSD", ascending=False).reset_index(
            drop=True
        )

    stats = {
        "total_symbols": total_symbols,
        "missing_mcap": missing_mcap,
        "below_threshold": below_threshold,
        "final_count": len(uni),
    }

    return uni, stats


# ----------------------------------
# PROCESS BATCH (MOMENTUM)
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
        mn = df["Slope"].min()
        mx = df["Slope"].max()
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
st.write(
    "Universe: US-listed common stocks with Market Cap ≥ chosen threshold (USD), "
    "strictly filtered by security name (no ETFs/Trusts/ADRs/etc.)."
)

# Sidebar controls
min_mcap_bn = st.sidebar.number_input(
    "Min Market Cap ($Bn)",
    min_value=0.5,
    max_value=500.0,
    value=1.5,  # default
    step=0.5,
)
min_mcap_usd = min_mcap_bn * 1_000_000_000

batch_size = st.sidebar.slider(
    "Batch Size (for price download)", 50, 500, 150, step=50
)

if st.sidebar.button("Refresh Ticker Universe"):
    build_us_universe.clear()
    fetch_prices.clear()
    st.experimental_rerun()

if st.sidebar.button("Clear All Cache"):
    st.cache_data.clear()
    st.experimental_rerun()

# Build universe
with st.spinner("Building US equity universe (symbols + FMP market cap)..."):
    try:
        uni_df, stats = build_us_universe(min_mcap_usd=min_mcap_usd)
    except ValueError as e:
        st.error(str(e))
        st.stop()

if uni_df.empty:
    st.error(
        "Universe is empty. Check FMP_API_KEY, NASDAQ symbol files, or FMP availability."
    )
    st.stop()

st.success(
    f"Universe size: {stats['final_count']} US stocks with Market Cap ≥ ${min_mcap_bn:.2f}B"
)

with st.expander("Universe stats & sample (debug)"):
    st.write(stats)
    st.dataframe(uni_df.head(50))

tickers_list = uni_df["Ticker"].tolist()

# Scan universe in batches
final_df_list = []
for i in range(0, len(tickers_list), batch_size):
    batch = tickers_list[i : i + batch_size]
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

    # Keep your <20% 1M rule
    final = final[final["Ret1M"] < 20]

    st.subheader("Top US Momentum Picks (<20% 1M return)")
    st.dataframe(final.head(250))
else:
    st.error("No results. Check universe or yfinance status.")
