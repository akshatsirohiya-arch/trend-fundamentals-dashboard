# trend-fundamentals-dashboard/app.py
# CLEAN VERSION — NO FUNDAMENTALS
# Universe: US-listed common stocks with Market Cap >= chosen threshold (default $1.5B)
# Momentum-only scoring (Slope + TA)

import os
import time
import io
from datetime import datetime, timedelta

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

# Financial Modeling Prep Batch Market Cap endpoint
FMP_BATCH_MCAP_URL = "https://financialmodelingprep.com/stable/market-capitalization-batch"


# ----------------------------------
# UTILITIES
# ----------------------------------

def get_fmp_api_key() -> str:
    """
    Get FMP API key from Streamlit secrets or environment variable.
    Raises ValueError if not found.
    """
    key = None
    try:
        # Streamlit secrets if available
        key = st.secrets.get("FMP_API_KEY", None)
    except Exception:
        key = None

    if not key:
        key = os.environ.get("FMP_API_KEY")

    if not key:
        raise ValueError(
            "FMP_API_KEY not set. Add it to Streamlit secrets or environment variables."
        )
    return key


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
def fetch_prices(tickers, period: str = "6mo", interval: str = "1d"):
    try:
        data = yf.download(tickers, period=period, interval=interval, progress=False)
        return data
    except Exception:
        return None


# ----------------------------------
# SYMBOL UNIVERSE (US LISTED)
# ----------------------------------

@st.cache_data(show_spinner=True, ttl=24 * 60 * 60)
def load_us_symbol_universe() -> pd.DataFrame:
    """
    Load US-listed symbols (NASDAQ-listed + other US exchanges).
    Applies:
      - Exclude ETFs via ETF flag
      - Exclude Test issues
      - Strict bad_keywords filter on SecurityName
    Returns ['Ticker', 'SecurityName'].
    """

    # ---- NASDAQ-listed ----
    r_nq = requests.get(NASDAQ_LISTED_URL, headers=HTTP_HEADERS, timeout=30)
    r_nq.raise_for_status()
    buf_nq = io.StringIO(r_nq.text)

    df_nq = pd.read_csv(buf_nq, sep="|")
    df_nq = df_nq[df_nq["Symbol"] != "File Creation Time"]

    # Only non-test, non-ETF
    df_nq = df_nq[(df_nq["Test Issue"] == "N") & (df_nq["ETF"] == "N")].copy()
    df_nq["Ticker"] = df_nq["Symbol"].str.strip()
    df_nq["SecurityName"] = df_nq["Security Name"].astype(str)

    # ---- Other-listed (NYSE, etc.) ----
    r_ol = requests.get(OTHER_LISTED_URL, headers=HTTP_HEADERS, timeout=30)
    r_ol.raise_for_status()
    buf_ol = io.StringIO(r_ol.text)

    df_ol = pd.read_csv(buf_ol, sep="|")
    df_ol = df_ol[df_ol["ACT Symbol"] != "File Creation Time"]
    df_ol = df_ol[(df_ol["Test Issue"] == "N") & (df_ol["ETF"] == "N")].c
