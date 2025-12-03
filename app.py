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
# Official NASDAQ symbol directories: NASDAQ-listed + other exchanges
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,applicatio
