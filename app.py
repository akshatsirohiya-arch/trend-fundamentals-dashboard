# app.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import altair as alt
from datetime import datetime
from sklearn.linear_model import LinearRegression
from math import ceil
import time

st.set_page_config(page_title="Trend+Fundamentals Dashboard", layout="wide")

# -----------------------
# Config
# -----------------------
START_DATE = "2018-01-01"
SLOPE_WINDOW = 20
BATCH_SIZE = 200    # tune down if timeouts occur
CACHE_TTL_SECONDS = 12 * 3600  # 12 hours

# Get FMP API key from Streamlit secrets or env
FMP_KEY = st.secrets.get("FMP_API_KEY", None) or st.experimental_get_query_params().get("fmp", [None])[0]
if not FMP_KEY:
    st.warning("No FMP API key found in Streamlit secrets. Please add FMP_API_KEY to app secrets.")
    # App will still try price-only mode, but fundamentals will be missing.

# -----------------------
# Helpers: batching, slope
# -----------------------
def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def compute_slope_last20(series, window=SLOPE_WINDOW):
    clean = series.dropna().values
    if len(clean) < window:
        return np.nan
    window_vals = clean[-window:]
    X = np.arange(len(window_vals)).reshape(-1,1)
    lr = LinearRegression().fit(X, window_vals)
    return float(lr.coef_[0])

# -----------------------
# Bulk fundamentals from FMP
# -----------------------
@st.cache_data(ttl=CACHE_TTL_SECONDS)
def fetch_fmp_bulk_income(year=None, period='annual', api_key=None):
    """Fetch bulk income statements (CSV or JSON) from FMP."""
    # v4 bulk endpoint pattern; returns CSV for a specific year/period
    # Example: https://financialmodelingprep.com/api/v4/income-statement-bulk?year=2023&period=annual&apikey=KEY
    base = "https://financialmodelingprep.com/api/v4/income-statement-bulk"
    params = {}
    if year:
        params['year'] = year
    if period:
        params['period'] = period
    params['apikey'] = api_key
    r = requests.get(base, params=params, timeout=60)
    r.raise_for_status()
    # FMP bulk endpoints return CSV content often — attempt parse as CSV
    try:
        df = pd.read_csv(pd.compat.StringIO(r.text))
    except Exception:
        # fallback: try json
        df = pd.DataFrame(r.json())
    return df

@st.cache_data(ttl=CACHE_TTL_SECONDS)
def fetch_fmp_bulk_cashflow(year=None, period='annual', api_key=None):
    base = "https://financialmodelingprep.com/api/v4/cash-flow-statement-bulk"
    params = {}
    if year:
        params['year'] = year
    if period:
        params['period'] = period
    params['apikey'] = api_key
    r = requests.get(base, params=params, timeout=60)
    r.raise_for_status()
    try:
        df = pd.read_csv(pd.compat.StringIO(r.text))
    except Exception:
        df = pd.DataFrame(r.json())
    return df

# -----------------------
# Get list of US tickers (NASDAQ/NYSE/AMEX)
# -----------------------
@st.cache_data(ttl=24*3600)
def get_us_tickers():
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
    other_url  = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
    nasdaq = pd.read_csv(nasdaq_url, sep="|", dtype=str)
    other = pd.read_csv(other_url, sep="|", dtype=str)
    tickers = pd.concat([nasdaq['Symbol'], other['ACT Symbol'].fillna('')]).dropna().unique().tolist()
    tickers = [t.strip() for t in tickers if isinstance(t, str) and t.strip().isalpha()]
    return sorted(list(set(tickers)))

# -----------------------
# Fetch prices in batches (yfinance)
# -----------------------
@st.cache_data(ttl=CACHE_TTL_SECONDS)
def fetch_prices_for_tickers(tickers, start_date=START_DATE, end_date=None, batch_size=BATCH_SIZE):
    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")
    all_rows = []
    batches = list(chunk_list(tickers, batch_size))
    for i, batch in enumerate(batches, start=1):
        try:
            data = yf.download(batch, start=start_date, end=end_date, group_by='ticker', threads=True, auto_adjust=True, progress=False)
        except Exception as e:
            time.sleep(1)
            try:
                data = yf.download(batch, start=start_date, end=end_date, group_by='ticker', threads=True, auto_adjust=True, progress=False)
            except Exception:
                continue
        for t in batch:
            try:
                df_t = data[t].reset_index()
                df_t['Ticker'] = t
                all_rows.append(df_t[['Ticker','Date','Open','High','Low','Close','Volume']])
            except Exception:
                # sometimes tickers missing
                continue
    if not all_rows:
        return pd.DataFrame(columns=['Ticker','Date','Open','High','Low','Close','Volume'])
    full = pd.concat(all_rows, ignore_index=True)
    full['Date'] = pd.to_datetime(full['Date'])
    for c in ['Open','High','Low','Close','Volume']:
        full[c] = pd.to_numeric(full[c], errors='coerce')
    return full.sort_values(['Ticker','Date']).reset_index(drop=True)

# -----------------------
# Main compute function
# -----------------------
@st.cache_data(ttl=CACHE_TTL_SECONDS)
def compute_universe(tickers, fmp_key, batch_size):
    # 1) prices
    prices = fetch_prices_for_tickers(tickers, batch_size=batch_size)

    # 2) compute HH/HL/trend per row
    df = prices.copy()
    df['PrevHigh'] = df.groupby('Ticker')['High'].shift(1)
    df['PrevPrevHigh'] = df.groupby('Ticker')['High'].shift(2)
    df['PrevLow'] = df.groupby('Ticker')['Low'].shift(1)
    df['PrevPrevLow'] = df.groupby('Ticker')['Low'].shift(2)
    df['HH'] = ((df['High'] > df['PrevHigh']) & (df['PrevHigh'] > df['PrevPrevHigh'])).astype(int)
    df['HL'] = ((df['Low'] > df['PrevLow']) & (df['PrevLow'] > df['PrevPrevLow'])).astype(int)
    df['Trend'] = ((df['HH'] == 1) & (df['HL'] == 1)).astype(int)

    # 3) compute slope per ticker
    slopes = df.groupby('Ticker')['Close'].apply(lambda s: compute_slope_last20(s)).reset_index()
    slopes.columns = ['Ticker','Slope']

    # 4) snapshot latest row per ticker
    latest = df.sort_values('Date').groupby('Ticker').tail(1).reset_index(drop=True)
    snapshot = latest.merge(slopes, on='Ticker', how='left')

    # 5) fetch bulk fundamentals (use current year)
    income_df = None
    cash_df = None
    try:
        year = datetime.today().year
        income_df = fetch_fmp_bulk_income(year=year, period='annual', api_key=fmp_key)
        cash_df = fetch_fmp_bulk_cashflow(year=year, period='annual', api_key=fmp_key)
    except Exception as e:
        # fallback: try without year (API may return all)
        try:
            income_df = fetch_fmp_bulk_income(api_key=fmp_key)
            cash_df = fetch_fmp_bulk_cashflow(api_key=fmp_key)
        except Exception:
            income_df = pd.DataFrame()
            cash_df = pd.DataFrame()

    # Normalize column names & keys: income_df should have symbol & revenue/netIncome; cash_df should have symbol & operatingCashFlow
    # Try common column names: 'symbol' or 'ticker', 'revenue'/'revenueTTM'/'totalRevenue', 'netIncome'/'netIncomeTTM'
    def extract_latest_value(df_in, symbol_col_options, value_name_options):
        # returns dict symbol -> latest value (float)
        if df_in is None or df_in.empty:
            return {}
        df_local = df_in.copy()
        # find symbol column
        symbol_col = None
        for c in ['symbol','ticker','symbolId','Symbol']:
            if c in df_local.columns:
                symbol_col = c
                break
        if symbol_col is None:
            return {}
        # pick likely value column
        value_col = None
        for c in value_name_options:
            if c in df_local.columns:
                value_col = c
                break
        if value_col is None:
            return {}
        # group by symbol and take most recent (if 'date' column present use it)
        if 'date' in df_local.columns:
            df_local['date'] = pd.to_datetime(df_local['date'], errors='coerce')
            df_local = df_local.sort_values(['symbol' if symbol_col=='symbol' else symbol_col,'date'], ascending=[True,False])
        # drop duplicates keep first
        df_local = df_local[[symbol_col, value_col]].dropna(subset=[value_col])
        mapping = df_local.groupby(symbol_col).first()[value_col].to_dict()
        return mapping

    # define value column options for revenue, net income, operating cash flow:
    revenue_opts = ['revenue', 'totalRevenue', 'Revenue', 'revenueTTM']
    netincome_opts = ['netIncome', 'netIncomeTTM', 'Net Income', 'netIncomeBeforeExtras']
    opcf_opts = ['operatingCashFlow', 'operatingCashFlowTTM', 'operatingCashflow', 'operatingCashFlowNet']

    income_rev_map = extract_latest_value(income_df, ['symbol','ticker'], revenue_opts)
    income_net_map = extract_latest_value(income_df, ['symbol','ticker'], netincome_opts)
    cash_opcf_map = extract_latest_value(cash_df, ['symbol','ticker'], opcf_opts)

    # map into snapshot
    snapshot['Revenue'] = snapshot['Ticker'].map(income_rev_map)
    snapshot['NetIncome'] = snapshot['Ticker'].map(income_net_map)
    snapshot['OperatingCashFlow'] = snapshot['Ticker'].map(cash_opcf_map)

    # 6) financial momentum (strict A): require Revenue↑, NetIncome↑, OCF↑ comparing latest vs previous year if available
    # We will attempt to infer previous year by looking into the bulk frames: find previous year entries if available
    def build_growth_flags(df_fin, value_cols_options):
        # returns dict symbol -> (latest_value, prev_value)
        res = {}
        if df_fin is None or df_fin.empty:
            return {}
        # symbol col search
        sym_col = next((c for c in ['symbol','ticker','Symbol'] if c in df_fin.columns), None)
        if sym_col is None:
            return {}
        # date/year column search
        date_col = next((c for c in ['date','filingDate','calendarYear'] if c in df_fin.columns), None)
        # value col selection
        val_col = next((c for c in value_cols_options if c in df_fin.columns), None)
        if val_col is None:
            return {}
        # group by symbol and sort by date => keep latest and previous
        df_local = df_fin[[sym_col, val_col] + ([date_col] if date_col else [])].dropna(subset=[val_col])
        if date_col:
            df_local[date_col] = pd.to_datetime(df_local[date_col], errors='coerce')
            df_local = df_local.sort_values([sym_col, date_col], ascending=[True, False])
        res_map = {}
        for symbol, group in df_local.groupby(sym_col):
            vals = group[val_col].values
            if len(vals) >= 2:
                res_map[symbol] = (float(vals[0]), float(vals[1]))
            elif len(vals) == 1:
                res_map[symbol] = (float(vals[0]), np.nan)
        return res_map

    rev_pairs = build_growth_flags(income_df, revenue_opts)
    net_pairs = build_growth_flags(income_df, netincome_opts)
    ocf_pairs = build_growth_flags(cash_df, opcf_opts)

    # now assign growth flags
    def growth_flag_from_pairs(pairs_map, symbol):
        try:
            a, b = pairs_map.get(symbol, (np.nan, np.nan))
            if pd.notna(a) and pd.notna(b):
                return 1 if a > b else 0
            else:
                return np.nan
        except:
            return np.nan

    snapshot['RevenueGrowth'] = snapshot['Ticker'].apply(lambda s: growth_flag_from_pairs(rev_pairs, s))
    snapshot['ProfitGrowth'] = snapshot['Ticker'].apply(lambda s: growth_flag_from_pairs(net_pairs, s))
    snapshot['CashflowGrowth'] = snapshot['Ticker'].apply(lambda s: growth_flag_from_pairs(ocf_pairs, s))

    # FinancialScore
    snapshot['FinancialScore'] = snapshot[['RevenueGrowth','ProfitGrowth','CashflowGrowth']].mean(axis=1)

    # 7) Strict filter A
    strict = snapshot[
        (snapshot['RevenueGrowth'] == 1) &
        (snapshot['ProfitGrowth'] == 1) &
        (snapshot['CashflowGrowth'] == 1)
    ].copy()

    # 8) normalize slope and compute annualized slope %
    if strict['Slope'].notna().any():
        mn = strict['Slope'].min()
        mx = strict['Slope'].max()
        strict['SlopeNorm'] = (strict['Slope'] - mn) / (mx - mn) if mx != mn else 0.0
    else:
        strict['SlopeNorm'] = np.nan

    strict['SlopeAnnualizedReturn'] = (strict['Slope'] / strict['Close']) * 252 * 100

    strict['FinalScore'] = 0.6 * strict['SlopeNorm'].fillna(0) + 0.4 * strict['FinancialScore'].fillna(0)

    strict = strict.sort_values('FinalScore', ascending=False).reset_index(drop=True)

    return strict, snapshot

# -----------------------
# UI
# -----------------------
st.title("📈 Trend + Fundamentals Dashboard (Strict Filter: Revenue↑, Profit↑, Cashflow↑)")

with st.spinner("Fetching tickers & data (cached)..."):
    tickers = get_us_tickers()
    st.write(f"Tickers discovered: {len(tickers)}")

st.sidebar.header("Options")
universe_size = st.sidebar.selectbox("Universe size", ("All US tickers (~6000)", "Top 2500 by exchange list", "Custom (first N)"))
if universe_size == "Top 2500 by exchange list":
    tickers = tickers[:2500]
elif universe_size.startswith("Custom"):
    n = st.sidebar.number_input("N tickers", min_value=200, max_value=len(tickers), value=2500, step=100)
    tickers = tickers[:n]

# Batch size selection (no global modification needed)
batch_size_ui = st.sidebar.slider("Batch size (yfinance)", 50, 400, BATCH_SIZE, step=50)

# Pass this batch size to compute_universe() directly (instead of global update)


if st.sidebar.button("Force refresh caches"):
    st.cache_data.clear()
    st.experimental_rerun()

# compute
with st.spinner("Computing signals and merging fundamentals (this may take a few minutes first time)..."):
    strict_df, snapshot_all = compute_universe(tickers, FMP_KEY, batch_size_ui)


st.success(f"{len(strict_df)} tickers passed strict fundamentals filter")

# Sidebar filters for display and sorting
st.sidebar.header("Display / Sorting")
sort_options = [
    "FinalScore","Slope","SlopeAnnualizedReturn","SlopeNorm","FinancialScore",
    "Close","Volume","RevenueGrowth","ProfitGrowth","CashflowGrowth","Trend"
]
sort_by = st.sidebar.selectbox("Sort by", sort_options, index=0)
asc = st.sidebar.checkbox("Sort ascending", value=False)
min_final = st.sidebar.slider("Min FinalScore", float(0.0), float(1.0), float(0.0), step=0.01)
trend_only = st.sidebar.checkbox("Trend only (HH & HL)", value=False)

display_df = strict_df[strict_df['FinalScore'] >= min_final]
if trend_only:
    display_df = display_df[display_df['Trend'] == 1]
display_df = display_df.sort_values(sort_by, ascending=asc).reset_index(drop=True)

st.subheader(f"Stocks meeting strict criteria: {len(display_df)}")
st.dataframe(display_df, height=600)

st.subheader("Ticker detail")
ticker = st.selectbox("Ticker", display_df['Ticker'].unique())
if ticker:
    row = display_df[display_df['Ticker'] == ticker].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("FinalScore", f"{row['FinalScore']:.3f}")
    c2.metric("FinancialScore", f"{row['FinancialScore']:.2f}")
    c3.metric("Slope Annualized %", f"{row['SlopeAnnualizedReturn']:.2f}%")
    st.write(row[['Ticker','Date','Close','High','Low','Volume','HH','HL','Trend','Slope','SlopeAnnualizedReturn']])

    # price history (6 months)
    hist = yf.Ticker(ticker).history(period="6mo")
    if not hist.empty:
        chart = alt.Chart(hist.reset_index()).mark_line().encode(x='Date:T', y='Close:Q')
        st.altair_chart(chart, use_container_width=True)

st.caption("Notes: fundamentals come from FinancialModelingPrep bulk endpoints. Price data from yfinance. Initial full run may take minutes; results cached for performance.")
