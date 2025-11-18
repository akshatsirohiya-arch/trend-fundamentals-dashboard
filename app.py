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
"A","AA","AAL","AAMI","AAOI","AAON","AAP","AAPG","AAPL","AAUC","ABE","ABBV","ABCB","ABEV",
"ABG","ABM","ABNB","ABR","ABT","ACA","ACAD","ACGL","ACGLN","ACGLO","ACHC","ACHR","ACIW",
"ACIW","ACLS","ACLX","ACM","ACMR","ACN","ACP","ACT","ADBE","ADC","ADEA","ADI","ADM","ADMA",
"ADNT","ADP","ADPT","ADSK","ADT","ADUS","AEG","AEIS","AEM","AEO","AEP","AER","AES","AFG",
"AFGB","AFGC","AFGD","AFGE","AFL","AFRM","AG","AGCO","AGI","AGIO","AGNC","AGNCL","AGNCM",
"AGNCN","AGNCO","AGNCP","AGO","AGX","AGYS","AHL","AHR","AI","AIG","AIT","AIZ","AIZN","AJG",
"AKAM","AKR","AKRO","AL","ALAB","ALB","ALC","ALE","ALG","ALGM","ALGN","ALHC","ALK","ALKS",
"ALKT","ALLE","ALLY","ALNY","ALRM","ALSN","ALV","ALVO","AM","AMAT","AMBA","AMBP","AMCR",
"AMD","AME","AMED","AMG","AMGN","AMH","AMKR","AMP","AMPX","AMR","AMRC","AMRX","AMSC","AMT",
"AMTM","AMX","AMZN","AN","ANDE","ANET","ANF","ANIP","AOMD","AON","AORT","AOS","APA","APAM",
"APD","APG","APGE","APH","APG","APLD","APLE","APO","APOS","APP","APPF","APPN","APTV","AQN",
"AQNB","AR","ARCB","ARCC","ARDT","ARE","ARES","ARGX","ARLO","ARM","ARMK","ARMN","AROC",
"ARQT","ARR","ARW","ARWR","AS","ASAN","ASB","ASBA","ASGN","ASH","ASM","ASML","ASND","ASO",
"ASR","ASTS","ASX","ATAT","ATEC","ATGE","ATHM","ATHS","ATI","ATKR","ATMU","ATR","ATRC","ATRO",
"ATS","AU","AUPH","AUR","AVA","AVAH","AVAL","AVAV","AVB","AVDL","AVDX","AVGO","AVNT","AVPT",
"AVT","AVTR","AVY","AWI","AWK","AWR","AX","AXON","AXP","AXS","AXSM","AXTA","AYI","AZN","AZO",
"AZZ","B","BA","BABA","BAC","BAH","BALL","BAM","BANC","BANF","BANR","BAP","BATRA","BATRK",
"BAX","BB","BBAI","BBAR","BBD","BBDO","BBIO","BBUC","BBVA","BBWI","BBY","BC","BCC","BCE","BCH",
"BCO","BCPC","BCS","BDC","BDJ","BDX","BE","BEAM","BEKE","BELFA","BELFB","BEN","BEPC","BFAM","BFC","BFH","BG","BGC","BGM","BHC","BHE","BHF","BHFAL","BHFAM","BHFAN","BHFAO","BHFAP",
"BBT","BHP","BIDU","BIIB","BILI","BILL","BIO","BIO","BIPC","BIRK","BITF","BJ","BK","BKD",
"BKE","BKH","BKNG","BKR","BKU","BKV","BL","BLBD","BLCO","BLD","BLDR","BLK","BLKB","BLTE",
"BMA","BMI","BMNR","BMRN","BMY","BN","BNL","BNS","BNT","BNTX","BOH","BOKF","BOOT","BOX",
"BP","BPOP","BR","BRBR","BRFS","BRK/B","BRKR","BRO","BROS","BRX","BRZE","BSAC","BSBR",
"BST","BSTZ","BSX","BSY","BTDR","BTE","BTG","BTO","BTSG","BTU","BUD","BULL","BURL","BUSE",
"BVN","BWA","BWIN","BWLP","BWXT","BX","BXMT","BXMX","BXP","BXSL","BYD","BZ","C","CAAP",
"CACC","CACI","CADE","CAE","CAG","CAH","CAKE","CALM","CALX","CAMT","CAR","CARG","CARR",
"CART","CASH","CASY","CAT","CATY","CAVA","CB","CBOE","CBRE","CBSH","CBT","CBU","CBZ","CC",
"CCB","CCC","CCEP","CCI","KYIV","CCJ","CCK","CCS","CCU","CDE","CDLR","CDNS","CDP","CDRE",
"CDTX","CDW","CE","CECO","CEG","CELC","CELH","CENT","CENTA","CENX","CEPU","CET","CF","CFG",
"CFLT","CFR","CG","CGAU","CGNX","CGON","CHA","CHCO","CHD","CHDN","CHE","PLBL","CHEF",
"CHH","CHKP","CHRD","CHRW","CHT","CHTR","CHWY","CI","CFG","CIB","CIEN","CIFR","CIG","CIGI",
"CINF","CIVI","CL","CLBK","CLBT","CLCO","CLDX","CLF","CLH","CLMT","CLS","CLSK","CLVT","CLX",
"CM","CMA","CMBT","CMC","CMCSA","CME","CMG","CMI","CMPO","CMPR","CMRE","0HR4","CMSA",
"CMSC","CMSD","CNA","CNC","CNH","CNI","CNK","CNM","CNO","CNP","CNQ","CNR","CNS","CNTA",
"CNX","CNXC","COCO","COF","COGT","COHR","COIN","COKE","COLB","COLD","COLM","COMM","COMP",
"CON","COO","COOP","COP","CORT","CORZ","COST","COTY","CP","CPA","CPAY","CPB","CPK","CPNG",
"CPRI","CPRT","CPRX","CPT","CR","CRBD","CRBG","CRC","CRDO","CRGY","CRH","CRK","CRL","CRM",
"CRNX","CROX","CRS","CRSP","CRUS","CRVL","CRWD","CRWV","CSAN","CSCO","CSGP","CSGS","CSIQ",
"CSL","CSQ","CSTM","CSX","CTAS","CTRA","CTRE","CTRI","CTSH","CTVA","CUBB","CUBE","CUBI",
"CUK","CURB","CUZ","CVBF","CVCO","CVI","CVLT","CVNA","CVI","CVS","CVX","CW","CWAN","CWEN",
"CWK","CWST","CWT","CX","CXM","CXT","CXW","CYBR","CYTK","CZR","D","DAC","DAL","DAN","DAR",
"DASH","DAVE","DAY","DB","DBD","DBRG","DBX","DCI","DD","DDOG","DDS","DE","DECK","DEI","DELL",
"DEO","DFH","DG","DGNX","DGX","DHI","DHR","DHT","DINO","DIOD","DIS","DJT","DK","DKNG","DKS",
"DLB","DLO","DLR","DLTR","DNB","DNLI","DNN","DNOW","DNP","DNTH","DOC","DOCN","DOCS","DOCU",
"DOOO","DORM","DOV","DOW","DOX","DPZ","DQ","DRD","DRH","DRI","DRS","DRVN","DSGX","DT","DTB",
"DTG","DTM","DTW","DUK","DUKB","DUOL","DV","DVA","DVN","DX","DXC","DXCM","DXPE","DY","DYN",
"E","EA","EAT","EBAY","EBC","EBR","EC","ECAT","ECG","ECL","ED","EDU","EE","EEFT","EFSC",
"EFSCP","EFX","EFXT","EG","EGO","EGP","EHC","EIX","EL","ELAN","ELF","ELP","ELPC","ELS","ELV",
"EMA","EME","EMN","EMR","ENB","ENIC","ENLT","ENOV","ENPH","ENR","ENS","ENSG","ENTG","ENVA",
"ENVX","EOG","EOSE","EPAC","EPAM","EPR","EPRT","EQH","EQIX","EQNR","EQR","EQT","EQX","ERIC",
"ERIE","EMBJ","ERO","ES","ESAB","ESE","ESI","ESLT","ESNT","ESS","ETY","EVCM","1EVN","EVR",
"EVRG","EVT","EVTC","EW","EWBC","EWTX","EXAS","EXC","EXE","EXEL","EXG","EXK","EXLS","EXP",
"EXPD","EXPE","EXPI","EXPO","EXR","EXTR","EYE","F","FA","FAF","FANG","FAST","FBIN","FBK",
"FBNC","FBYD","FCF","FCFS","FCN","FCNCA","FCNCO","FCNCP","FCPT","FCT","FCX","FDP","FDS","FDX",
"FE","FELE","FER","FERG","FFBC","FFIN","FFIV","FG","FGN","FGSN","FHB","FHI","FHN","FI","FIBK",
"FICO","FIHL","FINV","FIS","FITB","FITBI","FITBO","FITBP","FIVE","FIVN","FIX","FIZZ","FL",
"FLEX","FLG","FLNC","FLO","FLR","FLS","FLUT","FLYW","FMC","FMS","FMX","FN","FNB","FND","FNF",
"FNV","FOLD","FORM","FORTY","FOUR","FOX","FOXA","FR","FRA","FRHC","FRME","FRMEP","FRO","FROG",
"FRPT","FRSH","FRT","FSK","FSLR","FSLY","FSM","FSS","FSV","FTAI","FTAIM","FTAIN","FTDR","FTI",
"FTNT","FTS","FTV","FUBO","FUL","FULT","FULTP","FUN","FUTU","FWONA","FWONK","FYBR","G","GAB","GAP","GATX","GBCI","GBDC","GBTG","GCMG","GD","GDDY","GDS","GDV","GE","GEF",
"GEHC","GEN","GENI","GEO","GEV","GFF","GFI","GFL","GFS","GGAL","GGB","GGG","GH","GHC",
"GIB","GIL","GILD","GIS","GKOS","GL","GLBE","GLNG","GLOB","GLPG","GLPI","GLV","GLW",
"GLXY","GM","GMAB","GS2C","GMED","GMS","GNL","GNRC","GNTX","GNW","GOF","GOGL","GOLF",
"GOOG","GOOGL","GOOS","GPC","GPCR","GPI","GPK","GPN","GPOR","GRAB","GRBK","GRDN",
"GRFS","GRMN","GRND","ABTC","GS","GSAT","GSHD","GSK","GT","GTES","GTLB","GTLS PR B",
"GTM","GTX","GTY","GVA","GWRE","GWW","GXO","H","HAE","HAFN","HAL","HALO","HAS","HASI",
"HAYW","HBAN","HBANL","HBANM","HBANP","HBI","HCA","HCC","HCI","HCM","HCXY","HD","HDB",
"HDL","HE","HESM","HG","HGTY","HGV","HHH","HI","HIG","HII","HIMS","HIVE","HIW","HL",
"HLI","HLIO","HLMN","HLN","HLNE","HLT","HMC","HMN","MCHB","HMY","HNGE","HNI","HOG",
"HOLX","HOMB","HON","HOOD","HPQ","HPE","HPQ","HQY","HR","HRB","HRI","HRL","HRMY","HROWM",
"HSAI","HSBC","HSHP","HSIC","HST","HSY","HTGC","HTH","HTHT","HTO","HTZ","HUBB","HUBG",
"HUBS","HUM","IAS","IBKR","IBM","IBN","IBOC","IBP","IBRX","ICE","ICFI","ICL","ICLR",
"ICUI","IDA","IDCC","IDXX","IDYA","IE","IESC","IEX","IFF","IFS","IHG","IHS","ILMN",
"IMAX","IMCR","IMVT","INCY","INDB","INDV","INFA","INFY","ING","INGM","INGR","INOD",
"INSM","INSP","INSW","INTA","INTC","INTR","INTU","INVA","INVH","IONQ","IONS","IOSP",
"IOT","IP","IPAR","IPG","IPGP","IQ","IQV","IR","IRDM","IREN","IRM","IRON","IRT","IRTC",
"ISRG","IT","ITGR","ITRI","ITT","ITUB","ITW","IVT","IVZ","IX","J","JAMF","JANX","JAZZ",
"JBHT","JBL","JBLU","JBSAY","JBTM","JCI","JD","JEF","JEM","JHG","JHX","JJSF","JKHY",
"JKS","JLL","JNJ","JOE","JOYY","JPC","JPM","JXN","K","KAI","KALU","KAR","KBH","KBH",
"KBR","KD","KDP","KEN","KEP","KEX","KEY","KEYS","KFY","KGC","KGS","KHC","KIM","KKR",
"KLAC","KLG","KLIC","KMB","KMI","KMPB","KMPR","KMT","KMX","KN","KNF","KNSA","KNSL",
"KNTK","KNX","KO","KOF","KR","KRC","KRG","KRMN","KRYS","KSPI","KSS","KT","KTB","KTOS",
"KVUE","KVYO","KWR","KYMR","KYN","L","LAD","LAMR","LASR","LAUR","LAZ","LB","LBRDA",
"LBRDK","LBRDP","LBRT","LBTYA","LBTYB","LBTYK","LC","LCII","LDOS","LEA","LECO","LEGN",
"LEN","LEU","LEVI","LFST","LFUS","LGND","LH","LHX","LI","LIF","LII","LILA","LILAK",
"LIN","LINE","LITE","LIVN","LKQ","LLY","LLYVA","LLYVK","LMAT","LMND","LMT","LNC","LNG",
"LNT","LNTH","LNW","LOAR","LOGI","LOPE","LOW","LPLA","LPLA","LPX","LQDA","LRCX","LRN",
"LSCC","LSPD","LSTR","LTC","LTH","LTM","LU","LULU","LUMN","LUNR","LUV","LVS","LW","LXP",
"LYB","LYFT","LYG","LYV","LZ","M","MA","MAA","MAC","MAG","MAIN","MANH","MANU","MAR",
"MARA","MAS","MASI","MAT","MATX","MBLY","MC","MCD","MCHP","MCK","MCO","MCRI","MCW",
"MCY","MD","MDB","MDGL","MDLZ","MDT","MDU","MEDP","MELI","MEOH","MESO","MET","META",
"METC","METCB","METCZ","MFC","MFG","MGA","MGEE","MGIC","MGM","MGNI","MGR","MGRB","MGRC",
"MGRD","MGRE","MGY","MHK","MHO","MIDD","MIR","MIRM","MKC","MKL","MKSI","MKTX","MLCO",
"MLI","MLM","MLYS","MMC","MMM","MMS","MMSI","MMYT","MNDY","MNKD","MNSO","MNST","MO",
"MOD","MODG","MOH","MOS","MP","MPC","MPW","MPWR","MQ","MRCY","MRK","MRNA","MRP","MRUS",
"MRVL","MRX","MS","MSA","MSCI","MSFT","MSGE","MSGS","MSI","MSM","MSTR","MTB","MTCH",
"MTD","MTDR","MTG","MTH","MTN","MTRN","MTSI","MTSR","MTX","MTZ","MU","MUFG","MUR","MUSA",
"MVST","MWA","MYRG","NABL","NCKAF","NAD","NAMS","NATL","NBIS","NBIX","NBTB","NCLH","NCNO",
"NDAQ","NDSN","NE","NEA","NEE","NEGG","NEM","NET","NEU","NEXT","NFG","NFLX","NG","NGD",
"NGG","NGVT","NHC","NHI","NI","NIC","NICE","NIO","NJR","NKE","NLY","NMIH","NMIH","NMRK",
"NN","NNE","NNI","NNN","NOC","NOG","NOK","NOMD","NOV","NOVT","NOW","NPO","NRG","NSA",
"NSC","NSIT","NSSC","NTAP","NTB","NTCT","NTES","NTNX","NTR","NTRA","NTRS","NTRSO","NTST",
"NU","NUE","NUV","NUVB","NUVL","NVDA","NVEE","NVG","NVMI","NVO","NVR","NVS","NVST","NVT",
"NVTS","NWBI","NWE","NWG","NWN","NWS","NWSA","NXE","NXPI","NXST","NXT","NYAX","NYT","NZF",
"O","OBDC","OC","OCUL","ODD","ODFL","OFG","OGE","OGN","OGS","OHI","OI","OII","OKE","OKLO",
"OKTA","OLED","OLLI","OLN","OLO","OMAB","OWL","OXY","OZK","OZKAP","PAAS","PAC","PACS","PAG",
"PAGS","PAHC","PAM","PANW","PAR","PSKY","PARAA","PARR","PATH","PATK","PAX","PAY","PAYC","PAYO","PAYX","PB","PBA","PBF","PBH",
"PBI","PBR","PCAR","PCG","PCH","PCOR","PCT","PCTY","PCVX","PDD","PDI","PDO","PECO","PEG",
"PEGA","PEN","PENN","PEO","PEP","PFE","PFG","PFGC","PFH","PFS","PFSI","PG","PGNY","PGR",
"PGY","PH","PHG","PHI","PHIN","PHM","PI","PII","PINC","PINS","PIPR","PJT","PK","PKG","PKX",
"PL","PLD","PLMR","PLNT","PLTK","PLTR","PLUG","PLUS","PLXS","PM","PNC","PNFP","PNFPP",
"PNR","PNW","PODD","PONY","POOL","POR","POST","POWI","POWL","PPBI","PPC","PPG","PPL",
"PPTA","PR","PRAX","PRCT","PRDO","PRGO","PRGS","PRH","PRI","PRIM","PRK","PRKS","PRM",
"PRMB","PRS","PRVA","PSA","PSIX","PSN","PSNY","PSNYW","PSO","PSTG","PSX","PTC","PTCT",
"PTEN","PTGX","PTON","PTY","PUK","PVH","PWP","PWR","PYPL","QBTS","QCOM","QFIN","QGEN",
"QLYS","QMMM","QQQX","QRVO","QS","QSR","QTWO","QUBT","QURE","QXO","R","RACE","RAL",
"RAMP","RARE","RBA","RBC","RBLX","RBRK","RCI","RCL","RCUS","RDDT","RDN","RDNT","RDY",
"REG","REGCO","REGCP","REGN","RELX","RELY","REVG","REXR","REYN","REZI","RGA","RGC","RGEN",
"RGLD","RGTI","RH","RHI","RHP","RIG","RIO","RIOT","RITM","RIVN","RJF","RKLB","RKT","RL",
"RLI","RLX","RMBS","RMD","RNA","RNG","RNR","RNST","RNW","ROAD","ROCK","ROG","ROIV","ROK",
"ROKU","ROL","ROP","ROST","RPM","RPRX","RQI","RRC","RRX","RS","RSG","RSI","RTO","RTX",
"RUM","RUN","RUSHA","RUSHB","RVLV","RVMD","RVT","RVTY","RXO","RXRX","RY","RYAAY","RYAN",
"RYN","RYTM","RZB","RZC","S","SA","SAH","SAIA","SAIC","SAIL","SAM","SAND","SANM","SARO",
"SATS","SBAC","SBCF","SBET","SBLK","SBRA","SBS","SBSW","SBUX","SCCO","SCHW","SCI","SCS",
"SDRL","SE","SEB","SEDG","SEE","SEI","SEIC","SEM","SEZL","SFB","SFBS","SFD","SFM","SFNC",
"SGHC","SGI","SGRY","SHAK","SHC","SHCO","SHEL","SHG","SHLS","SHO","SHOO","SHOP","SHW",
"SID","SIG","SIGI","SIGIP","SII","SIM","SIMO","SION","SIRI","SITE","SITM","SJM","SKE","SKM",
"SKT","SKWD","SKX","SKY","SKYW","SLAB","SLB","SLF","SLG","SLGN","SLM","SLMBP","SLNO",
"SLSR","SLVM","SM","SMCI","SMFG","SMG","SMMT","SMTC","SN","SNA","SNAP","SNDK","SNDR",
"SNEX","SNN","SNOW","SNPS","SNREY","SNV","SNX","SNY","SO","SOBO","SOFI","SOJC","SOJD",
"SOJE","SOJF","SOLV","SON","SONO","SOUL","SOUN","SPG","SPGI","SPHR","SPNS","SPNT","SPR",
"SPSC","SPXC","SQM","SRAD","SRE","SREA","SRPT","SRRK","SSB","SSD","SSL","SSNC","SSRM",
"ST","STAG","STC","STE","STEL","STEP","STEW","STLA","STLD","STM","STN","STNE","STNG",
"STR","STRA","STRK","STRL","STT","STVN","STWD","STX","STZ","SU","SUI","SUPN","SVM","SW",
"SWK","SWKS","SWX","SXI","SXT","SYBT","SYF","SYK","SYM","SYNA","SYRE","SYY","T","TAC",
"TAK","TAL","TALO","TAP","TARS","TBB","TBBB","TBBK","TCBI","TCBIO","TCOM","TD","TDC",
"TDG","TDS","TDW","TDY","TEAM","TECH","TECK","TEF","TEL","TEM","TENB","TER","TERN","TEVA",
"TEX","TFC","TFII","TFPM","TFSL","TFX","TGB","TGLS","TGNA","TGS","TGT","TGTX","THC","THG",
"THO","TIC","TIGO","TIGR","TILE","TIMB","TIXT","TJX","TKC","TKO","TKR","TLK","TLN","TLX",
"TMC","TMDX","TME","TMHC","TMO","TMUS","TNET","TNK","TNL","TOL","TOST","TOWN","TPB","TPC",
"TPG","TPH","TPL","TPR","TR","TREX","TRGP","TRI","TRIP","TRMB","TRMD","TRMK","TRN","TRNO",
"TRON","TROW","TRP","TRUP","TRV","TS","TSCO","TSEM","TSIHF","TSLA","TSLX","TSM","TSN","TT",
"TTAM","TTAN","TTC","TTD","TTE","TTEK","TTMI","TTWO","TVTX","TW","TWLO","U","UA","UAA","UAL","UBER","UCB","UDR","UE","UEC","UFPI","UFPT","UGI","UGP","UHAL","UHS",
"UI","UL","ULS","ULTA","UMBF","UMC","UNF","UNFI","UNH","UNM","UNMA","UNP","UPS","UPST",
"UPWK","URBN","URI","USAR","USB","USFD","USLM","AD","UTF","UTG","UTHR","UTI","UUUU","UWMC",
"UZD","UZE","UZF","V","VAC","VAL","VALE","VBTX","VC","VCEL","VCTR","VCYT","VECO","VEEV",
"VEON","VERA","VERX","VET","VFC","VFS","VG","VIAV","VICI","VICR","VIK","VIPS","VIRT","VIST",
"VITL","VIV","VKTX","VLO","VLTO","VLY","VLYPN","VLYPO","VLYPP","VMC","VMI","VNET","VNO",
"VNOM","VNT","VOD","VOYA","VRDN","VRNS","VRRM","VRSK","VRSN","VRT","VRTX","VSAT","VSCO",
"VSEC","VSH","VST","VTMX","VTR","VTRS","VVV","VVX","VYX","VZ","VZLA","W","WAB","WAFD",
"WAFDP","WAL","WAT","WAY","WB","WBA","WBD","WBS","WBTN","WCC","WCN","WD","WDAY","WDC",
"WDFC","WDS","WEC","WELL","WEN","WERN","WEX","WF","WFC","WFG","WFRD","WGS","WH","WHD",
"WHR","WING","WIX","WK","WLK","WLY","WLYB","WM","WMB","WMG","WMK","WMS","WMT","WNS","WOR",
"WPC","WPM","WPP","WRB","WRBY","WS","WSBC","WSBCP","WSC","WSFS","WSM","WSO","WSO","WST",
"WT","WTFC","WTM","WTRG","WTS","WTW","WU","WULF","WWD","WY","WYHG","WYNN","XEL","XENE",
"XMTR","XOM","XP","XPEV","XPO","XYL","XYZ","YELP","YETI","YMM","YOU","YPF","YUM","YUMC",
"Z","ZBH","ZBIO","ZBRA","ZETA","ZG","ZGN","ZIM","ZION","ZIONP","ZLAB","ZM","ZS","ZTO",
"ZTS","ZWS"]





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

    # ---- NEW FILTER YOU WANT ----
    final = final[final["Ret1M"] < 20]

    st.subheader("Top Momentum Picks (<20% 1M return)")
    st.dataframe(final.head(250))

else:
    st.error("No results. Check tickers or yfinance status.")
