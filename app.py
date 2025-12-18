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
"A","AA","AAL","AAOI","AAON","AAP","AAPG","AAPL","AAUC","ABBV","ABCB","ABEV","ABG","ABM",
"ABNB","ABR","ABT","ACA","ACAD","ACGL","ACGLN","ACGLO","ACIW","ACLS","ACLX","ACM","ACMR",
"ACN","ACT","ADBE","ADC","ADI","ADM","ADMA","ADNT","ADP","ADPT","ADSK","ADT","ADUS",
"AEG","AEIS","AEM","AEO","AEP","AER","AES","AFG","AFL","AFRM","AG","AGCO","AGI","AGIO",
"AGNC","AGYS","AHL","AHR","AI","AIG","AIT","AIZ","AJG","AKAM","AKR","AKRO","AL","ALAB",
"ALB","ALC","ALE","ALG","ALGM","ALGN","ALHC","ALK","ALKS","ALKT","ALLE","ALLY","ALNY",
"ALRM","ALSN","ALV","AM","AMAT","AMBA","AMD","AME","AMED","AMG","AMGN","AMH","AMKR",
"AMP","AMR","AMRC","AMRX","AMSC","AMT","AMTM","AMX","AMZN","AN","ANDE","ANET","ANF",
"ANIP","AON","AOS","APA","APAM","APD","APG","APH","APLD","APLE","APO","APP","APPF",
"APPN","APTV","AQN","AQNB","AR","ARCB","ARCC","ARE","ARES","ARGX","ARHS","ARLO","ARM",
"ARMK","AROC","ARQT","ARW","ARWR","AS","ASAN","ASB","ASGN","ASH","ASM","ASML","ASND",
"ASO","ASR","ASTS","ATAT","ATEC","ATGE","ATI","ATKR","ATMU","ATR","ATRC","ATRO","AU",
"AUPH","AUR","AVA","AVAH","AVAV","AVDL","AVGO","AVNT","AVPT","AVT","AVTR","AVY","AWI",
"AWK","AWR","AX","AXON","AXP","AXS","AXSM","AXTA","AYI","AZN","AZO","AZZ",

"BA","BABA","BAC","BAH","BALL","BAM","BANC","BAP","BAX","BB","BBAI","BBAR","BBD","BBDO",
"BBIO","BBVA","BBWI","BBY","BC","BCC","BCE","BCH","BCO","BCPC","BDX","BE","BEAM","BEKE",
"BELFA","BELFB","BEN","BF.A","BF.B","BFH","BG","BHC","BHE","BHP","BIDU","BIIB","BILI",
"BITF","BJ","BK","BKD","BKE","BKH","BKNG","BKR","BL","BLBD","BLCO","BLD","BLDR","BLK",
"BMA","BMI","BMRN","BMY","BN","BNL","BNS","BNTX","BOH","BOKF","BOOT","BOX","BP","BR",
"BRBR","BRK.A","BRK.B","BRO","BROS","BRX","BSAC","BSBR","BSX","BTDR","BTG","BUD","BURL",
"BVN","BWA","BWXT","BX","BXMT","BXP","BXSL","BYD",

"C","CAAP","CACC","CACI","CADE","CAE","CAG","CAH","CAKE","CALM","CALX","CAR","CARG",
"CARR","CASH","CASY","CAT","CATY","CB","CBOE","CBRE","CBSH","CBT","CBU","CBZ","CC",
"CCI","CCJ","CCK","CCL","CCS","CCU","CDE","CDNS","CDW","CE","CECO","CEG","CELC","CELH",
"CENT","CENTA","CENX","CF","CFG","CG","CGNX","CHCO","CHD","CHDN","CHEF","CHKP","CHRD",
"CHRW","CHTR","CHWY","CI","CIB","CIEN","CIG","CINF","CL","CLBK","CLF","CLH","CLS","CLVT",
"CLX","CM","CMA","CMC","CMCSA","CME","CMG","CMI","CNH","CNI","CNK","CNM","CNO","CNP",
"CNQ","CNS","CNX","COF","COHR","COLD","COLB","COLM","COO","COP","COST","COTY","CP",
"CPB","CPNG","CPRT","CPT","CR","CRC","CRH","CRK","CRL","CRM","CRS","CSCO","CSGP","CSGS",
"CSIQ","CSX","CTAS","CTRA","CTSH","CTVA","CUBE","CUZ","CVE","CVNA","CVS","CVX","CW",
"CWK","CWT","CX","CXM","CXW",

"D","DAL","DAN","DAR","DAY","DB","DD","DDS","DE","DECK","DEI","DELL","DEO","DG","DGX",
"DHI","DHR","DINO","DIS","DK","DKNG","DKS","DLB","DLR","DOV","DOW","DPZ","DRD","DRI",
"DT","DTE","DUK","DVA","DVN","DX","DXC","DY",

"E","EA","EAT","EBAY","ECL","ED","EEFT","EFX","EG","EGO","EHC","EIX","EL","ELAN","ELF",
"ELS","EME","EMN","EMR","ENB","ENOV","ENS","ENVA","EOG","EPAM","EPR","EQH","EQNR","EQR",
"EQT","EQX","ERIC","ERIE","ES","ESAB","ESS","ESTC","ETN","ETR","ETSY","EVR","EVTC","EW",
"EXAS","EXC","EXEL","EXLS","EXP","EXPD","EXPE","EXPO","EXR",

"F","FAF","FANG","FAST","FBIN","FBK","FBP","FCF","FCN","FCNCA","FCPT","FCX","FDP","FDS",
"FDX","FE","FELE","FERG","FFBC","FFIN","FFIV","FG","FHB","FHI","FHN","FICO","FIS","FITB",
"FIVE","FIVN","FIX","FIZZ","FL","FLEX","FLNC","FLO","FLR","FLS","FMC","FMS","FMX","FNB",
"FND","FNF","FNV","FORM","FOUR","FOX","FOXA","FR","FRHC","FRME","FRO","FRPT","FRSH","FRT",
"FSK","FSLR","FSM","FSS","FTAI","FTI","FTNT","FTS","FTV","FUL","FULT","FUN","FUTU",

"G","GAP","GATX","GBCI","GBDC","GD","GDDY","GE","GEF","GEN","GEO","GFF","GFI","GFL","GGB",
"GGG","GHC","GIB","GIL","GILD","GIS","GKOS","GL","GLBE","GLNG","GLOB","GLPI","GLW","GM",
"GMED","GMS","GNRC","GNW","GOOG","GOOGL","GOOS","GPC","GPI","GPK","GPN","GPOR","GRBK",
"GRFS","GRMN","GS","GSAT","GSHD","GSK","GT","GTES","GTLB","GTLS","GVA","GWRE","GWW","GXO",

"H","HAE","HAL","HASI","HBAN","HBI","HCA","HD","HESM","HG","HIG","HII","HIMS","HIW","HL",
"HLI","HLIO","HLN","HLT","HMC","HMN","HMY","HNI","HOG","HOLX","HON","HOOD","HPQ","HPE",
"HQY","HR","HRB","HRI","HRL","HSBC","HSIC","HST","HSY","HTGC","HUBB","HUBG","HUBS","HUM",

"IAC","IAS","IBKR","IBM","IBN","IBP","ICE","ICFI","ICL","ICLR","ICUI","IDA","IDCC","IDXX",
"IEX","IFF","IHG","IHS","IIPR","ILMN","IMAX","IMCR","INCY","INDB","ING","INGR","INSM",
"INTC","INTU","INVH","IONS","IOSP","IP","IPAR","IPG","IPGP","IQV","IR","IRM","IRTC","ISRG",
"IT","ITGR","ITT","ITUB","ITW","IVZ",

"J","JAMF","JAZZ","JBHT","JBL","JBLU","JCI","JD","JEF","JHG","JHX","JJSF","JKHY","JLL",
"JNJ","JOE","JPM","JXN",

"K","KAI","KAR","KBH","KBR","KDP","KEX","KEY","KEYS","KFY","KGC","KGS","KHC","KIM","KKR",
"KLAC","KLIC","KMB","KMI","KMPR","KMT","KMX","KN","KNSL","KNTK","KNX","KO","KOF","KR",
"KRC","KRG","KRMN","KSS","KT","KVUE","KVYO","KWR",

"L","LAD","LAMR","LASR","LAUR","LBRDA","LBRDK","LBRDP","LBTYA","LBTYB","LBTYK","LC",
"LCII","LDOS","LEA","LECO","LEGN","LEN","LEU","LEVI","LFUS","LGND","LH","LHX","LII","LIN",
"LITE","LIVN","LKQ","LLY","LMT","LNC","LNG","LOGI","LOPE","LOW","LPLA","LPX","LRCX","LSCC",
"LSTR","LULU","LUMN","LUV","LVS","LW","LYB","LYFT","LYV"

"M","MA","MAA","MAC","MAIN","MANH","MAR","MARA","MAS","MASI","MAT","MATX","MBIN","MBLY",
"MCD","MCHP","MCK","MCO","MCY","MDB","MDGL","MDLZ","MDT","MDU","MEDP","MELI","MEOH",
"MET","META","MFC","MFG","MGA","MGEE","MGIC","MGNI","MGRC","MHK","MHO","MIDD","MIRM",
"MKC","MKSI","MKTX","MLI","MLM","MLYS","MMC","MMM","MMS","MMSI","MNKD","MNST","MO",
"MOD","MODG","MOH","MOS","MP","MPC","MPWR","MQ","MRCY","MRK","MRNA","MRUS","MRVL",
"MS","MSA","MSCI","MSFT","MSI","MSM","MSTR","MTB","MTD","MTDR","MTG","MTH","MTN",
"MTRN","MTX","MTZ","MU","MUR","MUSA","MVST","MWA","MYRG",

"N","NABL","NBIX","NBTB","NCNO","NDAQ","NDSN","NE","NEE","NEM","NET","NEU","NFG",
"NFLX","NG","NICE","NKE","NLY","NMIH","NMRK","NN","NOC","NOG","NOK","NOV","NOW",
"NRG","NSC","NSIT","NSSC","NTAP","NTCT","NTES","NTNX","NTR","NTRA","NTRS","NU",
"NUE","NVDA","NVMI","NVST","NVT","NWBI","NWE","NWL","NWS","NWSA","NXPI","NXST",
"NYT",

"O","OBDC","OC","ODFL","OFG","OGE","OGN","OHI","OI","OKE","OKTA","OLED","OLLI",
"OMAB","OMCL","ON","ONB","OPCH","OPEN","ORCL","ORLY","OS","OSIS","OTEX","OTTR",
"OZK",

"P","PAAS","PAC","PAG","PANW","PATH","PAYC","PAYX","PCAR","PCH","PCTY","PCVX",
"PDD","PECO","PEG","PEGA","PENN","PEP","PFE","PFG","PFGC","PG","PGNY","PGR",
"PH","PHG","PHM","PI","PINS","PIPR","PK","PKG","PLAB","PLD","PLMR","PLNT",
"PLTR","PLUS","PLXS","PM","PNC","PNFP","PNR","PNW","POOL","POWI","POWL","PPG",
"PPL","PR","PRAX","PRCT","PRDO","PRGO","PRI","PRIM","PRK","PRKS","PRVA","PSA",
"PSTG","PSX","PTC","PTCT","PTEN","PTGX","PTON","PWR","PYPL",

"Q","QCOM","QDEL","QFIN","QLYS","QRVO","QS","QTWO",

"R","RACE","RAMP","RBA","RBLX","RBRK","RCI","RCL","RCUS","RDDT","REG","REGN",
"RELY","REYN","RGA","RGEN","RGLD","RGTI","RH","RHI","RHP","RIG","RIO","RIOT",
"RIVN","RKLB","RL","RLI","RMBS","RMD","RNG","RNR","ROG","ROK","ROL","ROP",
"ROST","RPM","RPRX","RRR","RSG","RTX","RUN","RVLV","RXRX","RY","RYTM",

"S","SAIA","SAIC","SANM","SATS","SBAC","SBCF","SBLK","SBRA","SBUX","SCCO",
"SCHW","SCI","SEDG","SEIC","SEZL","SFM","SFNC","SGML","SGRY","SHAK","SHOO",
"SHOP","SIGI","SIMO","SIRI","SITE","SITM","SKWD","SKYW","SLAB","SLB","SLM",
"SLNO","SMCI","SMMT","SMTC","SNA","SNAP","SNDR","SNOW","SNPS","SO","SOFI",
"SON","SONO","SOUN","SPSC","SRAD","SRCE","SRPT","SRRK","SSNC","SSRM","STAG",
"STEP","STLD","STNE","STRA","STRL","STX","SUPN","SWKS","SYF","SYM","SYNA",
"SYRE",

"T","TARS","TBBK","TCBI","TCOM","TEAM","TECH","TENB","TER","TFSL","TGTX",
"TIGO","TIGR","TLN","TLRY","TMDX","TMUS","TOWN","TPG","TR","TREX","TRGP",
"TRMB","TRMK","TROW","TRUP","TSCO","TSEM","TSLA","TTAN","TTD","TTEK","TTMI",
"TTWO","TVTX","TW","TWST","TXG","TXN","TXRH",

"U","UAL","UBER","UFPI","UFPT","ULTA","UMBF","UNIT","UPST","UPWK","URBN",
"USLM","UTHR",

"V","VC","VCEL","VCTR","VCYT","VEEV","VEON","VERA","VERX","VFC","VICI",
"VICR","VKTX","VLO","VLY","VMC","VMI","VNET","VNOM","VNT","VOD","VOYA",
"VRDN","VRNS","VRRM","VRSK","VRSN","VRTX","VSAT","VSEC","VSH","VST","VTRS",

"W","WAFD","WAL","WAT","WBS","WCC","WCN","WDAY","WDC","WEC","WELL","WEN",
"WERN","WEX","WFC","WFG","WHR","WING","WIX","WM","WMB","WMG","WMT","WOR",
"WPC","WRB","WRBY","WSM","WST","WTFC","WTW","WU","WWD","WY","WYNN",

"XEL","XENE","XMTR","XP","XRAY","XYL",

"YELP","YETI","YMM","YOU","YPF","YUM","YUMC",

"Z","ZBH","ZBRA","ZETA","ZG","ZION","ZIONP","ZLAB","ZM","ZS","ZYME"
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
    final = (
        pd.concat(final_df)
        .sort_values("FinalScore", ascending=False)
        .reset_index(drop=True)
    )

    # ---- FILTER ----
    final = final[final["Ret1M"] < 30]

    st.subheader("Top Momentum Picks (<30% 1M return)")
    st.dataframe(final.head(250))

else:
    st.error("No results. Check tickers or yfinance status.")
