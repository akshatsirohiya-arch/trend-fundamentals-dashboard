# trend-fundamentals-dashboard/app.py
# CLEAN VERSION — NO FUNDAMENTALS
# Supports large universes (Russell 2000 + custom small caps)
# Momentum-only scoring (Slope + TA)

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Momentum Scanner (No Fundamentals)")

# ----------------------------------
# LOAD TICKERS (Russell + custom)
# ----------------------------------
TICKERS = [
    "AAPL","MSFT","AMZN","GOOGL","META","TSLA","NVDA","AVGO","NFLX","AMD",
    "CRM","ADBE","PYPL","INTC","QCOM","CSCO","ORCL","SHOP","SQ","UBER",
    "COIN","PLTR","SMCI","TSM","MU","MAR","ABNB","BKNG","JPM","MS",
    "GS","V","MA","AXP","BAC","C","WFC","SPGI","MSCI","BLK",
    "XOM","CVX","COP","SLB","HAL","OXY","BP","SHEL","TTE","PBR",
    "UNH","LLY","PFE","MRK","ABBV","BMY","ISRG","SYK","ZBH","DHR",
    "JNJ","GEHC","REGN","VRTX","AMGN","GILD","BIIB","ILMN","RGEN","CGEN",
    "NKE","HD","LOW","COST","TGT","WMT","TJX","DG","ROST","UL",
    "PG","CL","KMB","EL","KO","PEP","MNST","KDP","KHC","MDLZ",
    "MCD","SBUX","YUM","CMG","DPZ","QSR","WEN","DRI","TXN","LRCX",
    "AMAT","ASML","KLAC","INTU","NOW","PANW","FTNT","ZS","CRWD","OKTA",
    "MDB","SNOW","DDOG","NET","ESTC","TEAM","WDAY","TWLO","DOCU","ZS",
    "T","VZ","TMUS","CHTR","CMCSA","DIS","PARA","WBD","FOX","LYV",
    "BA","LMT","NOC","RTX","GD","HON","GE","CAT","DE","MMM",
    "F","GM","STLA","RIVN","LCID","TM","HMC","NIO","LI","XPEV",
    "UPS","FDX","DAL","UAL","AAL","LUV","JBLU","RCL","CCL","NCLH",
    "UNP","CSX","NSC","CP","CNI","KSU","ET","KMI","WMB","MPLX",
    "NEE","DUK","SO","AEP","SRE","D","ED","XEL","PEG","EIX",
    "JKS","FSLR","ENPH","SEDG","RUN","DQ","CSIQ","MAXN","SPWR","BE",
    "BIDU","BABA","PDD","JD","TCEHY","NTES","IQ","YUMC","TAL","EDU",
    "HDB","IBN","INFY","TCS","WIT","RELIANCE.NS","TATAMOTORS.NS","HDFCBANK.NS",
    "ICICIBANK.NS","KOTAKBANK.NS","BHARTIARTL.NS","ADANIENTERPRISES.NS",
    "ADANIPORTS.NS","LT.NS","MARUTI.NS","BAJAJFINSV.NS","BAJFINANCE.NS",
    "DMART.NS","ULTRACEMCO.NS","ASIANPAINT.NS","HINDUNILVR.NS","TCS.NS","ITC.NS",
    "TATAPOWER.NS","TATASTEEL.NS","ONGC.NS","COALINDIA.NS","JSWSTEEL.NS",
    "SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS","APOLLOHOSP.NS",
    "MUTHOOTFIN.NS","CHOLAFIN.NS","TITAN.NS","M&M.NS","HEROMOTOCO.NS",
    "EICHERMOT.NS","BRITANNIA.NS","HAVELLS.NS","VOLTAS.NS","RECLTD.NS",
    "POWERGRID.NS","AMBUJACEM.NS","SHREECEM.NS","BEL.NS","BOSCHLTD.NS"
]


# ----------------------------------
# UTILITIES
# ----------------------------------

def compute_slope(close_series):
    y = close_series.values
    x = np.arange(len(y))
    if len(y) < 5:
        return np.nan
    try:
        slope = np.polyfit(x, y, 1)[0]
        return slope
    except:
        return np.nan

@st.cache_data(show_spinner=False)
def fetch_prices(tickers, period="6mo", interval="1d"):
    try:
        data = yf.download(tickers, period=period, interval=interval, progress=False)
        return data
    except Exception:
        return None

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
    if df["Slope"].notna().any():
        mn, mx = df["Slope"].min(), df["Slope"].max()
        df["SlopeNorm"] = (df["Slope"] - mn) / (mx - mn + 1e-9)
    else:
        df["SlopeNorm"] = 0

    # Final score
    df["FinalScore"] = (
        0.7 * df["SlopeNorm"].fillna(0) +
        0.15 * df["Ret1M"].fillna(0) +
        0.15 * df["Ret3M"].fillna(0)
    )

    return df.sort_values("FinalScore", ascending=False).reset_index(drop=True)

# ----------------------------------
# STREAMLIT UI
# ----------------------------------

st.title("Momentum Scanner — Clean Version (No Fundamentals)")
st.write("Fast TA-only ranking for Russell 2000 + Small Caps")

batch_size = st.sidebar.slider("Batch Size", 50, 500, 150, step=50)
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.experimental_rerun()

# PROCESS

final_df = []
for i in range(0, len(TICKERS), batch_size):
    batch = TICKERS[i: i + batch_size]
    st.write(f"Processing {len(batch)} tickers...")
    out = process_batch(batch)
    if not out.empty:
        final_df.append(out)

if final_df:
    final = pd.concat(final_df).sort_values("FinalScore", ascending=False).reset_index(drop=True)
    st.subheader("Top Momentum Picks")
    st.dataframe(final.head(50))
else:
    st.error("No results. Check tickers or yfinance status.")
