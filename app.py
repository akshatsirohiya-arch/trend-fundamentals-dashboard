# ===============================
#   Trend + Fundamentals Dashboard
#   All in Streamlit, Stable Build
# ===============================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from sklearn.linear_model import LinearRegression
from datetime import datetime
import altair as alt
import time

st.set_page_config(page_title="Trend + Financial Momentum", layout="wide")

# -----------------------
# CONFIG
# -----------------------
START_DATE = "2018-01-01"
SLOPE_WINDOW = 20
CACHE_TTL = 12 * 3600   # 12 hours

FMP_KEY = st.secrets.get("FMP_API_KEY", None)
if not FMP_KEY:
    st.error("Missing FMP_API_KEY in secrets.")
    st.stop()

# ------------------------------------------------
#  EMBEDDED S&P 500 + NASDAQ 100 + RUSSELL 1000
# ------------------------------------------------

@st.cache_data(ttl=24*3600)
def load_index_tickers():
    universe = [
"A","AAL","AAP","AAPL","ABBV","ABC","ABMD","ABNB","ABT","ACGL","ACN","ADBE","ADI","ADM","ADP","ADSK","AEE",
"AEP","AES","AFL","AFRM","AIG","AIZ","AJG","AKAM","ALB","ALGN","ALK","ALL","ALLE","AMAT","AMCR","AMD","AME",
"AMGN","AMP","AMT","AMZN","ANET","ANSS","AON","AOS","APA","APD","APH","APP","APPF","APTV","ARE","ARLP","ARE",
"ARMK","ASML","ATO","ATVI","AVB","AVGO","AVY","AWK","AXON","AZO","BA","BAC","BALL","BAX","BBWI","BBY","BDX",
"BEN","BF.B","BG","BIIB","BIO","BK","BKNG","BKR","BLK","BLL","BLDR","BMY","BR","BRK.B","BRO","BSX","BTI",
"BURL","BWA","BXP","C","CAG","CAH","CARR","CAT","CB","CBOE","CBRE","CBRL","CCI","CCL","CDAY","CDNS","CDW",
"CE","CEG","CF","CFG","CHD","CHRW","CHTR","CI","CINF","CL","CLX","CMA","CMCSA","CME","CMG","CMI","CMS","CNC",
"CNHI","CNP","COF","COG","COO","COP","COST","CPB","CPRT","CPT","CRL","CRM","CRWD","CSCO","CSGP","CSX","CTAS",
"CTLT","CTSH","CTVA","CTXS","CVS","CVX","CXO","D","DAL","DD","DE","DFS","DG","DGX","DHI","DHR","DIS","DISCA",
"DISH","DLR","DLTR","DOV","DPZ","DRE","DRI","DTE","DUK","DVA","DVN","DXC","EA","EBAY","ECL","ED","EFX","EIX",
"EL","ELV","EMN","EMR","ENPH","EOG","EQIX","EQR","ES","ESS","ETN","ETR","ETSY","EVRG","EW","EXC","EXPD","EXPE",
"EXR","F","FANG","FAST","FB","FBHS","FCX","FDX","FE","FFIV","FIS","FISV","FITB","FLIR","FLR","FLS","FLT","FMC",
"FOX","FOXA","FRC","FRT","FTI","FTNT","FTV","GD","GE","GILD","GIS","GL","GLW","GM","GNRC","GOOG","GOOGL","GPC",
"GPN","GPS","GRMN","GS","GWW","HAL","HAS","HBAN","HBI","HCA","HD","HES","HIG","HII","HLT","HOLX","HON","HPE",
"HPQ","HRL","HSIC","HST","HSY","HUM","HWM","IBM","ICE","IDXX","IEX","IFF","ILMN","INCY","INFO","INTC","INTU",
"IP","IPG","IPGP","IQV","IR","IRM","ISRG","IT","ITW","IVZ","J","JBHT","JCI","JKHY","JNJ","JNPR","JPM","JWN",
"K","KEY","KEYS","KHC","KIM","KLAC","KMB","KMI","KMX","KO","KR","KSS","KSU","L","LB","LDOS","LEG","LEN","LH",
"LHX","LIN","LKQ","LLY","LMT","LNC","LNT","LOW","LRCX","LUMN","LUV","LVS","LW","LYB","M","MA","MAA","MAC","MAR",
"MAS","MAT","MCD","MCHP","MCK","MCO","MDLZ","MDT","MET","MGM","MHK","MKC","MKTX","MLM","MMC","MMM","MNST","MO",
"MPWR","MRK","MRO","MS","MSCI","MSFT","MSI","MTB","MTD","MU","NCLH","NDAQ","NEE","NEM","NFLX","NI","NKE","NLOK",
"NLSN","NOC","NOV","NOW","NRG","NSC","NTAP","NTRS","NUE","NVDA","NVR","NWL","NWS","NWSA","NXPI","O","ODFL","OGN",
"OKE","OMC","ORCL","ORLY","OTIS","OXY","PARA","PAYC","PAYX","PCAR","PCRX","PCTY","PD","PEG","PEP","PFE","PFG",
"PG","PGR","PH","PHM","PKG","PLD","PM","PNC","PNR","PNW","PPG","PPL","PRGO","PRU","PSA","PSX","PTC","PVH","PWR",
"PXD","PYPL","QCOM","QRVO","RCL","RE","REG","REGN","RF","RHI","RJF","RL","RMD","ROK","ROL","ROP","ROST","RSG",
"RTX","SBAC","SBUX","SCHW","SEE","SHW","SIVB","SJM","SLB","SLG","SMCI","SNA","SNPS","SO","SPG","SPGI","SPLK",
"SRE","STT","STX","STZ","SWK","SWKS","SYF","SYK","SYY","T","TAP","TDY","TECH","TEL","TER","TFC","TFX","TGT","TJX",
"TMO","TMUS","TPR","TRMB","TROW","TRV","TSCO","TSLA","TSN","TT","TTWO","TXN","TXT","UAL","UDR","UHS","ULTA",
"UNH","UNP","UPS","URI","USB","V","VAR","VFC","VLO","VMC","VNO","VRSK","VRSN","VRTX","VTR","VTRS","VZ","WAB",
"WAT","WBA","WDC","WEC","WELL","WFC","WHR","WM","WMB","WMT","WRB","WRK","WST","WU","WY","WYNN","XEL","XLNX",
"XOM","XRAY","XYL","YUM","ZBH","ZBRA","ZION","ZTS",
# NASDAQ 100
"AAPL","MSFT","AMZN","NVDA","GOOGL","GOOG","META","PEP","AVGO","COST","TSLA",
"ADBE","CMCSA","NFLX","AMD","CSCO","TXN","INTC","INTU","AMGN","QCOM","AMAT","HON",
"PYPL","ADP","SBUX","CHTR","ISRG","MDLZ","BKNG","GILD","CSX","MRNA","LRCX","ADI",
"MU","LULU","REGN","VRTX","KDP","MNST","ABNB","PANW","TEAM","COP","MELI","CRWD",
"MAR","FTNT","CDNS","ORLY","EA","SNPS","KLAC","WDAY","ADSK","PAYX","DXCM","ODFL",
"PCAR","MCHP","ROST","CTAS","BIDU","CEG","AEP","EXC","ORCL","IDXX","XEL","KHC",
"CTSH","ANSS","VRSK",
# Russell 1000
"A","AAL","AAP","AAPL","ABBV","ABC","ABMD","ABNB","ABT","ACGL","ACN","ADBE","ADI","ADM","ADP","ADSK",
"AEE","AEP","AES","AFL","AIG","AIZ","AJG","AKAM","ALB","ALGN","ALK","ALL","ALLE","AMAT","AMD","AME",
"AMGN","AMP","AMT","AMZN","ANET","ANSS","AON","AOS","APA","APD","APH","APTV","ARE","ATO","AVB","AVGO",
"AVY","AWK","AXON","AZO","BA","BAC","BALL","BAX","BBY","BDX","BEN","BF.B","BG","BIIB","BIO","BK",
"BKNG","BKR","BLK","BLL","BMY","BR","BRK.B","BRO","BSX","BURL","BWA","BXP","C","CAG","CAH","CARR","CAT",
"CB","CBOE","CBRE","CCI","CDAY","CDNS","CDW","CE","CEG","CF","CFG","CHD","CHRW","CHTR","CI","CINF","CL",
"CLX","CMA","CMG","CMI","CMS","CNA","CNC","CNP","COF","COO","COP","COST","CPB","CPRT","CPT","CRL","CRM",
"CRWD","CSCO","CSGP","CSX","CTAS","CTLT","CTSH","CTVA","CVS","CVX","D","DAL","DD","DE","DFS","DG","DGX",
"DHI","DHR","DIS","DLR","DLTR","DOV","DPZ","DRE","DRI","DTE","DUK","DVA","DVN","DXC","EA","EBAY","ECL",
"ED","EFX","EIX","EL","ELV","EMN","EMR","EOG","EQIX","EQR","ES","ESS","ETN","ETR","ETSY","EVRG","EW",
"EXC","EXPD","EXPE","EXR","F","FANG","FAST","FDX","FE","FIS","FISV","FITB","FLS","FLT","FMC","FOX","FOXA",
"FRC","FRT","FTNT","FTV","GD","GE","GILD","GIS","GPC","GPN","GRMN","GS","GWW","HAL","HAS","HBAN","HCA",
"HD","HES","HIG","HII","HLT","HOLX","HON","HPE","HPQ","HRL","HSIC","HST","HSY","HUM","IBM","ICE","IDXX",
"IEX","IFF","ILMN","INCY","INTC","INTU","IP","IPG","IQV","IR","IRM","ISRG","ITW","IVZ","J","JBHT","JCI",
"JKHY","JNJ","JNPR","JPM","JWN","K","KEY","KEYS","KHC","KIM","KLAC","KMB","KMI","KMX","KO","KR","KSS",
"KSU","L","LDOS","LEG","LEN","LH","LHX","LIN","LKQ","LLY","LMT","LNC","LNT","LOW","LRCX","LUMN","LUV",
"LVS","LW","LYB","M","MA","MAA","MAR","MAS","MAT","MCD","MCHP","MCK","MCO","MDLZ","MDT","MET","MGM","MHK",
"MKC","MKTX","MLM","MMM","MNST","MO","MPWR","MRK","MRO","MS","MSCI","MSFT","MSI","MTB","MTD","MU","NCLH",
"NDAQ","NEE","NEM","NI","NKE","NLOK","NLSN","NOC","NOV","NRG","NSC","NTAP","NTRS","NUE","NVDA","NVR","NWL",
"NWS","NWSA","NXPI","O","ODFL","OKE","OMC","ORCL","ORLY","OTIS","OXY","P","PARA","PAYX","PCAR","PCTY","PEP",
"PFE","PFG","PG","PGR","PH","PHM","PKG","PLD","PM","PNC","PNR","PNW","PPG","PPL","PRGO","PRU","PSA","PSX",
"PTC","PVH","PWR","PXD","PYPL","QCOM","QRVO","RCL","REG","REGN","RF","RGLD","RHI","RJF","RL","RMD","ROK",
"ROL","ROP","ROST","RSG","RTX","SBAC","SBUX","SCHW","SEE","SHW","SJM","SLB","SLG","SMCI","SNA","SNPS","SO",
"SPG","SPGI","SPLK","SRE","STT","STX","STZ","SWK","SWKS","SYK","SYY","T","TAP","TDY","TEL","TER","TFC","TFX",
"TGT","TJX","TMO","TMUS","TPR","TRMB","TROW","TRV","TSCO","TSLA","TSN","TT","TTWO","TXN","TXT","UAL","UDR",
"UHS","ULTA","UNH","UNP","UPS","URI","USB","V","VLO","VMC","VNO","VRSK","VRSN","VRTX","VTR","VTRS","VZ",
"WAB","WAT","WBA","WDC","WEC","WELL","WFC","WHR","WM","WMB","WMT","WRB","WRK","WST","WY","WYNN","XEL","XOM",
"XRAY","XYL","YUM","ZBH","ZBRA","ZION","ZTS"
    ]
    return sorted(list(set(universe)))


tickers = load_index_tickers()
st.sidebar.write(f"Universe: **{len(tickers)} tickers**")

# -----------------------
# PRICE DOWNLOAD
# -----------------------
def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

@st.cache_data(ttl=CACHE_TTL)
def fetch_prices(tickers, batch_size):
    all_rows = []
    end = datetime.today().strftime("%Y-%m-%d")

    for batch in chunk(tickers, batch_size):
        try:
            data = yf.download(
                batch, start=START_DATE, end=end,
                group_by='ticker', auto_adjust=True,
                threads=True, progress=False
            )
        except Exception:
            time.sleep(1)
            continue

        for t in batch:
            try:
                df = data[t].reset_index()
                df["Ticker"] = t
                all_rows.append(df[["Ticker","Date","High","Low","Close","Volume"]])
            except:
                continue

    if not all_rows:
        return pd.DataFrame()

    df = pd.concat(all_rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Ticker","Date"])
    return df

# ==================================================
# FUNDAMENTALS (FREE FMP V3 — PER TICKER, CACHED)
# ==================================================
@st.cache_data(ttl=CACHE_TTL)
def fetch_fundamentals(symbol):
    base = "https://financialmodelingprep.com/api/v3"
    params = {"apikey": FMP_KEY, "limit": 2}

    # income
    try:
        inc = requests.get(f"{base}/income-statement/{symbol}", params=params, timeout=7).json()
    except:
        inc = []

    # cashflow
    try:
        cf = requests.get(f"{base}/cash-flow-statement/{symbol}", params=params, timeout=7).json()
    except:
        cf = []

    return inc, cf


# -----------------------
# FULL COMPUTATION
# -----------------------
@st.cache_data(ttl=CACHE_TTL)
def compute_all(tickers, batch_size):

    # ---- Price data ----
    prices = fetch_prices(tickers, batch_size)
    if prices.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = prices.copy()
    df["PrevHigh"] = df.groupby("Ticker")["High"].shift(1)
    df["PrevPrevHigh"] = df.groupby("Ticker")["High"].shift(2)
    df["PrevLow"] = df.groupby("Ticker")["Low"].shift(1)
    df["PrevPrevLow"] = df.groupby("Ticker")["Low"].shift(2)

    df["HH"] = ((df["High"] > df["PrevHigh"]) & (df["PrevHigh"] > df["PrevPrevHigh"])).astype(int)
    df["HL"] = ((df["Low"] > df["PrevLow"]) & (df["PrevLow"] > df["PrevPrevLow"])).astype(int)
    df["Trend"] = ((df["HH"]==1) & (df["HL"]==1)).astype(int)

    # slope
    def slope_fn(x):
        clean = x.dropna().values
        if len(clean) < SLOPE_WINDOW:
            return np.nan
        w = clean[-SLOPE_WINDOW:]
        lr = LinearRegression().fit(np.arange(len(w)).reshape(-1,1), w)
        return float(lr.coef_[0])

    slopes = df.groupby("Ticker")["Close"].apply(slope_fn).to_frame("Slope").reset_index()

    latest = df.sort_values("Date").groupby("Ticker").tail(1)
    snapshot = latest.merge(slopes, on="Ticker", how="left")

    # ---- Fundamentals (per ticker) ----
    frows = []
    for sym in tickers:
        inc, cf = fetch_fundamentals(sym)
        if len(inc) >= 2 and len(cf) >= 2:
            frows.append([
                sym,
                inc[0].get("revenue"), inc[1].get("revenue"),
                inc[0].get("netIncome"), inc[1].get("netIncome"),
                cf[0].get("operatingCashFlow"), cf[1].get("operatingCashFlow")
            ])

    fund_df = pd.DataFrame(
        frows,
        columns=[
            "Ticker","Revenue","PrevRevenue","NetIncome","PrevNetIncome",
            "OperatingCashFlow","PrevOperatingCashFlow"
        ]
    )

    # merge
    snapshot = snapshot.merge(fund_df, on="Ticker", how="left")

    # growth flags
    snapshot["RevenueGrowth"] = (snapshot["Revenue"] > snapshot["PrevRevenue"]).astype(int)
    snapshot["ProfitGrowth"]  = (snapshot["NetIncome"] > snapshot["PrevNetIncome"]).astype(int)
    snapshot["CashflowGrowth"] = (snapshot["OperatingCashFlow"] > snapshot["PrevOperatingCashFlow"]).astype(int)

    snapshot["FinancialScore"] = snapshot[
        ["RevenueGrowth","ProfitGrowth","CashflowGrowth"]
    ].mean(axis=1)

    # Strict filter
    strict = snapshot[
        (snapshot["RevenueGrowth"]==1) &
        (snapshot["ProfitGrowth"]==1) &
        (snapshot["CashflowGrowth"]==1)
    ].copy()

    # Final Score
    if strict["Slope"].notna().any():
        mn, mx = strict["Slope"].min(), strict["Slope"].max()
        strict["SlopeNorm"] = (strict["Slope"] - mn) / (mx - mn + 1e-9)
    else:
        strict["SlopeNorm"] = np.nan

    strict["SlopeAnnualizedReturn"] = (strict["Slope"] / strict["Close"]) * 252 * 100
    strict["FinalScore"] = 0.6*strict["SlopeNorm"].fillna(0) + 0.4*strict["FinancialScore"].fillna(0)

    strict = strict.sort_values("FinalScore", ascending=False).reset_index(drop=True)

    return strict, snapshot


# -----------------------
# SIDEBAR
# -----------------------
st.sidebar.header("Settings")
batch_size = st.sidebar.slider("Price batch size (yfinance)", 50, 200, 100, step=25)

if st.sidebar.button("Clear cache & rerun"):
    st.cache_data.clear()
    st.experimental_rerun()

# -----------------------
# RUN COMPUTATION
# -----------------------
with st.spinner("Loading data and computing scores... (first run = 30–60s)"):
    strict_df, snapshot_all = compute_all(tickers, batch_size)

st.success(f"{len(strict_df)} stocks passed strict fundamental + trend filter")

# -----------------------
# SORTING + TABLE
# -----------------------
st.sidebar.header("Sort and Filter")
sort_col = st.sidebar.selectbox(
    "Sort by",
    ["FinalScore","Slope","SlopeAnnualizedReturn","SlopeNorm","FinancialScore","Close","Volume"]
)
ascending = st.sidebar.checkbox("Ascending", False)

min_score = st.sidebar.slider("Minimum FinalScore", 0.0, 1.0, 0.0, 0.01)

filtered = strict_df[strict_df["FinalScore"] >= min_score]
filtered = filtered.sort_values(sort_col, ascending=ascending)

st.subheader(f"Matching stocks: {len(filtered)}")
st.dataframe(filtered, use_container_width=True, height=550)

# -----------------------
# DETAIL VIEW
# -----------------------
st.subheader("Stock Detail")
sel = st.selectbox("Select Ticker", filtered["Ticker"].tolist())

if sel:
    row = filtered[filtered["Ticker"] == sel].iloc[0]

    c1,c2,c3 = st.columns(3)
    c1.metric("FinalScore", f"{row['FinalScore']:.3f}")
    c2.metric("FinancialScore", f"{row['FinancialScore']:.2f}")
    c3.metric("SlopeAnn %", f"{row['SlopeAnnualizedReturn']:.2f}%")

    hist = yf.Ticker(sel).history(period="6mo")
    if not hist.empty:
        chart = alt.Chart(hist.reset_index()).mark_line().encode(
            x="Date:T", y="Close:Q"
        )
        st.altair_chart(chart, use_container_width=True)

st.caption("Price data: Yahoo Finance | Fundamentals: FMP (free tier) | Universe: SP500 + NASDAQ100 + R1000")
