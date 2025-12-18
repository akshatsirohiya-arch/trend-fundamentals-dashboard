# trend-fundamentals-dashboard/app.py
# CLEAN VERSION — AUTOMATED UNIVERSE
# Momentum-only scanner (Slope + Returns)
# Universe: US equities with Market Cap > $1.5B

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(layout="wide", page_title="Momentum Scanner (Auto Universe)")

# ----------------------------------
# UNIVERSE BUILDING (CLOUD SAFE)
# ----------------------------------

@st.cache_data(show_spinner=False)
def load_us_equity_master():
    """
    Cloud-safe US equity universe.
    Source: GitHub mirror of NASDAQ + NYSE symbols.
    """
    try:
        url = (
            "https://raw.githubusercontent.com/"
            "rreichel3/US-Stock-Symbols/main/all/all_tickers.csv"
        )
        df = pd.read_csv(url)

        # Keep only common stocks
        df = df[
            (df["exchange"].isin(["NYSE", "NASDAQ"])) &
            (df["type"] == "Stock")
        ]

        # Remove prefs / warrants / weird tickers
        df = df[~df["symbol"].str.contains(r"\.|/|-", regex=True)]

        return sorted(df["symbol"].unique())

    except Exception as e:
        st.error("❌ Failed to load US ticker universe")
        st.stop()


@st.cache_data(show_spinner=True)
def filter_by_market_cap(tickers, min_mcap):
    """Filter tickers by market cap using yfinance"""
    valid = []

    for tk in tickers:
        try:
            info = yf.Ticker(tk).fast_info
            mcap = info.get("marketCap", None)
            if mcap and mcap >= min_mcap:
                valid.append(tk)
        except:
            continue

    return valid


@st.cache_data(show_spinner=True)
def build_universe(min_mcap):
    master = load_us_equity_master()
    universe = filter_by_market_cap(master, min_mcap)
    return universe

# ----------------------------------
# TECHNICAL UTILITIES
# ----------------------------------

def compute_slope(close_series):
    if len(close_series) < 5:
        return np.nan
    y = close_series.values
    x = np.arange(len(y))
    try:
        return np.polyfit(x, y, 1)[0]
    except:
        return np.nan


@st.cache_data(show_spinner=False)
def fetch_prices(tickers, period="6mo", interval="1d"):
    try:
        return yf.download(
            tickers,
            period=period,
            interval=interval,
            progress=False,
            threads=True,
            auto_adjust=True,
        )
    except:
        return None


# ----------------------------------
# BATCH PROCESSING
# ----------------------------------

def process_batch(tickers):
    data = fetch_prices(tickers)
    if data is None or "Close" not in data:
        return pd.DataFrame()

    close_df = data["Close"]
    rows = []

    for tk in close_df.columns:
        s = close_df[tk].dropna()
        if len(s) < 64:
            continue

        slope = compute_slope(s[-60:])
        ret_1m = (s.iloc[-1] / s.iloc[-21] - 1) * 100
        ret_3m = (s.iloc[-1] / s.iloc[-63] - 1) * 100

        rows.append({
            "Ticker": tk,
            "Close": s.iloc[-1],
            "Slope": slope,
            "Ret1M": ret_1m,
            "Ret3M": ret_3m,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Normalize slope
    mn, mx = df["Slope"].min(), df["Slope"].max()
    df["SlopeNorm"] = (df["Slope"] - mn) / (mx - mn + 1e-9)

    # Final momentum score
    df["FinalScore"] = (
        0.7 * df["SlopeNorm"] +
        0.15 * df["Ret1M"] +
        0.15 * df["Ret3M"]
    )

    return df.sort_values("FinalScore", ascending=False).reset_index(drop=True)


# ----------------------------------
# STREAMLIT UI
# ----------------------------------

st.title("Momentum Scanner — Automated Universe")
st.write("US equities | Market Cap > $1.5B | Momentum-only")

# Sidebar controls
min_mcap = st.sidebar.selectbox(
    "Minimum Market Cap",
    options=[1_000_000_000, 1_500_000_000, 2_000_000_000],
    index=1,
    format_func=lambda x: f"${x/1e9:.1f}B"
)

batch_size = st.sidebar.slider("Batch Size", 50, 400, 150, step=50)

if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.experimental_rerun()

# ----------------------------------
# BUILD UNIVERSE
# ----------------------------------

with st.spinner("Building universe..."):
    TICKERS = build_universe(min_mcap)

MAX_TICKERS = 2000
if len(TICKERS) > MAX_TICKERS:
    st.warning(f"Universe capped at {MAX_TICKERS} tickers for stability")
    TICKERS = TICKERS[:MAX_TICKERS]

st.success(f"Universe size: {len(TICKERS)} stocks")

# ----------------------------------
# RUN SCANNER
# ----------------------------------

final_df = []

for i in range(0, len(TICKERS), batch_size):
    batch = TICKERS[i: i + batch_size]
    st.write(f"Processing {i + len(batch)} / {len(TICKERS)}")
    out = process_batch(batch)
    if not out.empty:
        final_df.append(out)

if final_df:
    final = (
        pd.concat(final_df)
        .sort_values("FinalScore", ascending=False)
        .reset_index(drop=True)
    )

    # ---- YOUR FILTER ----
    final = final[final["Ret1M"] < 30]

    st.subheader("Top Momentum Picks (<30% 1M Return)")
    st.dataframe(final.head(250), use_container_width=True)

else:
    st.error("No results. Check yfinance or reduce universe size.")
