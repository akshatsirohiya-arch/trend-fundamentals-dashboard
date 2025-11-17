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
"AA","KDK","AAL","AAMI","AAOI","AAON","AAP","AAPG","AAT","AAUC","ABE","ABCB",
"ABCL","ABG","ABL","ABLLL","ABM","ABR","ABUS","ACA","ACAD","ACDC","ACEL","ACHC",
"ACHR","ACIW","ACLS","ACLX","ACM","ACMR","ACP","ACT","ACVA","ADC","ADEA","ADMA",
"ADNT","ADPT","ADT","ADTN","ADUS","AEG","AEHR","AEIS","AEO","AER","AES","AESI",
"AEVA","AFG","AFGB","AFGC","AFGD","AFGE","AFRM","AFYA","AG","AGCO","AGI","AGIO",
"AGNC","AGNCL","AGNCM","AGNCN","AGNCO","AGNCP","AGO","AGRO","AGX","AGYS","AHCO",
"AHG","AHH","AHL","AHR","AI","AIN","AIO","AIOT","AIP","AIT","AIV","AIZ","AIZN",
"AKAM","AKR","AKRO","AL","ALB","ALE","ALEX","ALG","ALGM","ALGN","ALGT","ALHC",
"ALIT","ALK","ALKS","ALKT","ALLE","ALLY","ALNT","ALRM","ALSN","ALV","ALVO","ALX",
"AM","AMAL","AMBA","AMBP","AMC","AMCR","AMED","AMG","AMH","AMKR","AMLX","AMN",
"AMPH","AMPL","AMPX","AMR","AMRC","AMRK","AMRX","AMSC","AMSF","AMTB","AMTM","AMWD",
"AN","ANAB","ANDE","ANF","ANIP","AOD","AOMD","AORT","AOS","AOSL","APA","APAM",
"APG","APGE","APLD","APLE","APOG","APPF","APPN","APPS","APTV","AQN","AQNB","AQST",
"AR","ARCB","ARCC","ARCO","ARDT","ARDX","ARE","ARHS","ARI","ARIS","ARLO","ARMK",
"ARMN","AROC","ARQT","ARR","ARRY","ARVN","ARW","ARWR","AS","ASA","ASAN","ASB",
"ASBA","ASGI","ASGN","ASH","ASIC","ASND","ASO","ASPI","ASR","ASST","ASTE","ASTH",
"ASTS","ATAI","ATAT","ATEC","ATEN","ATGE","ATHM","ATHS","ATI","ATKR","ATLC","ATLCL",
"ATLCP","ATLCZ","ATMU","ATO","ATR","ATRC","ATRO","ATS","ATUS","ATXS","AUB","AUPH",
"AUR","AVA","AVAH","AVAL","AVAV","AVBP","AVDL","AVDX","AVNT","AVO","AVPT","AVT",
"AVTR","AVXL","AVY","AWF","AWI","AWR","AX","AXGN","AXL","AXS","AXSM","AXTA","AYI",
"AZTA","AZZ","BAH","BAK","BALL","BALY","BANC","BANF","BANR","BAP","BASE","BATRA",
"BATRK","BAX","BB","BBAI","BBAR","BBDC","BBIO","BBN","BBNX","BBSI","BBUC","BBW",
"BBWI","BBY","BC","BCAL","BCAX","BCC","BCH","BCO","BCPC","BCRX","BCSF","BCX","BDC",
"BDJ","BEAM","BEKE","BELFA","BELFB","BEN","BEPC","BETR","BFG","BFAM","BFC","BFH",
"BFS","BFST","BG","BGC","BGM","BH","BHC","BHE","BHF","BHFAL","BHFAM","BHFAN","BHFAO",
"BHFAP","BHK","BBT","BHRB","BHVN","BIIB","BILI","BILL","BIO","BIPC","BIRK","BIT",
"BITF","BJ","BJRI","BKD","BKE","BKH","BKSY","BKU","BKV","BL","BLBD","BLCO","BLD",
"BLDP","BLDR","BLFS","BLKB","BLND","BLTE","BLX","BMA","BMEZ","BMI","BMNR","BMRN",
"BNL","BNT","BNTX","BOE","BOH","BOKF","BOOT","BORR","BOW","BOX","BPOP","BRBR","BRDG",
"BRFS","BRKL","BRKR","BRN","BROS","BRSP","BRX","BRZE","BSAC","BSBR","STEX","BST",
"BSTZ","BSY","BTBT","BTDR","BTE","BTG","BTO","BTSG","BTU","BTX","BTZ","BUI","BULL",
"BUR","BURL","BUSE","BVN","BVS","BWA","BWIN","BWLP","BWXT","BXMT","BXMX","BXP","BXSL",
"BY","BYD","BYND","BZ","BZH","CAAP","CABO","CAC","CACC","CACI","CADE","CAE","CAG",
"CAKE","CALM","CALX","CAMT","CAN","CANG","CAR","CARG","CARS","CART","CASH","CASY",
"CATY","CAVA","CBL","CBRL","CBSH","CBT","CBU","CBZ","CC","CCB","CCBG","CCC","CCEC",
"KYIV","CCK","CCNE","CCNEP","CCO","CCOI","CCS","CCU","CDE","CDLR","CDNA","CDP","CDRE",
"CDTX","CDW","CE","CECO","CELC","CELH","CENT","CENTA","CENX","CEPU","CERT","CET",
"CEVA","CF","CFFN","CFG","CFLT","CFR","CG","CGAU","CGBD","CGBDL","CGNT","CGNX","CGON",
"CHA","CHCO","CHD","CHDN","CHE","PLBL","CHEF","CHH","CHI","CHKP","CHRD","CHRW","CHWY",
"CHY","CIB","CIFR","CIG","CIGI","CII","CIM","CIMN","CIMO","CINT","CIVI","CLB","CLBK",
"CLBT","CLCO","CLDX","CLF","CLH","CLMT","CLOV","CLSK","CLVT","CLX","CMA","CMBT","CMC",
"CMP","CMPO","CMPR","CMPX","CMRE","CMSA","CMSC","CMSD","CNA","CNC","CNH","CNK","CNL",
"CNM","CNMD","CNNE","CNO","CNOB","CNOBP","CNR","CNS","CNTA","CNX","CNXC","CNXN",
"COCO","COGT","COHR","COHU","COKE","COLB","COLD","COLL","COLM","COMM","COMP","CON",
"COO","COOP","CORT","CORZ","COTY","COUR","CPA","CPAC","CPAY","CPB","CPF","CPK","CPRI",
"CPRX","CPT","CR","CRAI","CRBD","CRBG","CRC","CRESY","CRF","CRGY","CRK","CRL","CRMD",
"CRML","CRNX","CRON","CROX","CRS","CRSP","CRSR","CRTO","CRUS","CRVL","CSAN","CSGS",
"CSIQ","CSL","CSQ","CSR","CSTL","CSTM","CSV","CSWC","CSWCZ","CTBI","CTEV","CTLP",
"CTMX","CTOS","CTRA","CTRE","CTRI","CTS","CUBB","CUBE","CUBI","CURB","CUZ","CVAC",
"CVBF","CVCO","CVI","CVLT","CW","CWAN","CWEN","CWH","CWK","CWST","CWT","CX","CXM",
"CXT","CXW","CYD","CYTK","CZR","DAC","DAKT","DAN","DAO","DAR","DAVE","DAWN","DAY",
"DBD","DBRG","DBX","DCBO","DCI","DCO","DCOM","DCOMG","DCOMP","DD","DDS","DEA","DEC",
"DECK","DEFT","DEI","DFH","DFIN","DG","DGICA","DGICB","DGII","DGNX","DGX","DHC","DHCNI",
"DHCNL","DHT","DIAX","DINO","DIOD","DJT","DK","DKNG","DKS","DLB","DLO","DLTR","DLX","DLY",
"DNB","DNLI","DNN","DNOW","DNP","DNTH","DNUT","DOC","DOCN","DOCS","DOCU","DOLE","DOOO",
"DORM","DOV","DOW","DOX","DPZ","DQ","DRD","DRH","DRI","DRS","DRVN","DSGR","DSGX","DSL",
"DSU","DT","DTM","DUOL","DV","DVA","DVAX","DVN","DX","DXC","DXCM","DXPE","DY","DYN",
"EAT","EBC","EC","ECAT","ECC","ECCC","ECCF","ECCU","ECCV","ECCW","ECCX","ECG","ECO",
"ECPG","ECVT","ECX","EDN","EDU","EE","EEFT","EEX","EFC","EFSC","EFSCP","EFXT","EG","EGO",
"EGP","EH","EHC","EIG","EIX","ELAN","ELF","ELME","ELP","ELPC","ELS","ELVN","EMA","EMBC",
"EMD","EMN","EMO","EMX","ENIC","ENLT","ENOV","ENPH","ENR","ENS","ENSG","ENTG","ENVA","ENVX",
"EOI","EOS","EOSE","EPAC","EPAM","EPC","EPR","EPRT","EQBK","EQH","EQR","EQX","ERAS","ERIE",
"ERII","EMBJ","ERO","ESAB","ESE","ESI","ESNT","ESPR","ESQ","ESRT","ESS","ETWO","ETY","EU",
"EVCM","EVER","EVEX","EVGO","EVLV","EVO","EVR","EVRG","EVT","EVTC","EVV","EWBC","EWTX",
"EXAS","EXEL","EXG","EXK","EXLS","EXOD","EXP","EXPD","EXPI","EXPO","EXTR","EYE","EYPT",
"EZPW","FA","FAF","FBIN","FBK","FBNC","FBRT","FBYD","FCBC","FCF","FCFS","FCN","FCNCA",
"FCNCO","FCNCP","FCPT","FCT","FDP","FDS","FDUS","FELE","FFBC","FFC","FFIN","FFIV","FG",
"FGN","FGSN","FHB","FHI","FHN","FIBK","FIGS","FIHL","FINV","FIVE","FIVN","FIZZ","FL",
"FLEX","FLG","FLGT","FLNC","FLNG","FLO","FLOC","FLR","FLS","FLYW","FMBH","FMC","FMS","FN",
"FNB","FND","FNF","FOLD","FOR","FORD","FORM","FORTY","FOUR","FOXF","FPF","FR","FRA",
"FRGE","FRHC","FRME","FRMEP","FRO","FROG","FRPT","FRSH","FRT","FSBC","FSK","FSLY","FSM",
"FSS","FSUN","FSV","FTAI","FTAIM","FTAIN","FTDR","FTI","FTRE","FTV","FUBO","FUL","FULT",
"FULTP","FUN","FUTU","FVRR","FWRD","FWRG","FYBR","G","GAB","GABC","GAP","GATX","GAU",
"GB","GBCI","GBDC","GBTG","GBX","GCI","GCMG","GCT","GDDY","GDEN","GDOT","GDRX","GDS",
"GDV","GDYN","GEF","GEN","GENI","GEO","GERN","GES","GETY","GFF","GFL","GFS","GGAL",
"GGB","GGG","GGN","GH","GHC","GHLD","GHM","GHRS","GIC","GIII","GIL","GILT","GKOS","GL",
"GLBE","GLDD","GLNG","GLOB","GLP","GLPG","GLPI","GLUE","GLV","GLXY","GMAB","GMED","GMS",
"GNK","GNL","GNRC","GNTX","GNW","GO","GOF","GOGL","GOGO","GOLF","GOOS","GOTU","GPC",
"GPCR","GPI","GPK","GPN","GPOR","GPRE","GRAB","GRBK","GRC","GRDN","GRFS","GRND","GRNT",
"GRPN","GSAT","GSBC","GSBD","GSHD","GSL","GSM","GT","GTES","GTLB","GTX","GTY","GVA","GWRE",
"GXO","GYRE","H","HAE","HAFC","HAL","HALO","HAS","HASI","HAYW","HBAN","HBANL","HBANM",
"HBANP","HBI","HBNC","HBT","HCC","HCI","HCM","HCSG","HCXY","HDL","HE","HEPS","HESM","HFWA",
"HG","HGTY","HGV","HHH","HI","HIFS","HII","HIMS","HIMX","HIPO","HIVE","HIW","HL","HLF",
"HLI","HLIO","HLIT","HLMN","HLNE","HLX","HMN","HMY","HNI","HNRG","HOG","HOLX","HOMB",
"HOPE","HOUS","HOV","HOVNP","HPQ","HPI","HPK","HPP","HPS","HQH","HQY","HR","HRB",
"HRI","HRL","HRMY","HROW","HROWL","HROWM","HRTG","HSAI","HSHP","HSIC","HSII","HST","HSTM",
"HTB","HTBK","HTD","HTGC","HTH","HTHT","HTO","HTZ","HUBB","HUBG","HUBS","IAS","IAUX",
"IBCP","IBOC","IBP","IBRX","IBTA","ICFI","ICL","ICLR","ICUI","IDA","IDCC","IDT","IDYA",
"IE","IESC","IEX","IFF","IFN","IFS","IGIC","IGR","IHG","IHRT","IHS","IIIN","IIIV","IIPR",
"ILMN","IMAX","IMCR","IMKTA","IMNM","IMOS","IMTX","IMVT","INBX","INCY","INDB","INDI",
"INDV","INFA","INGM","INGR","INMD","INN","INNV","INOD","INR","INSP","INSW","INTA","INTR",
"INVA","INVH","INVX","IONQ","IONS","IOSP","IOT","IOVA","IP","IPAR","IPG","IPGP","IPX",
"IQ","IRDM","IREN","IRMD","IRON","IRS","IRT","IRTC","IT","ITGR","ITRG","ITRI","ITRN","ITT",
"IVT","IVZ","J","JAMF","JANX","JAZZ","JBGS","JBHT","JBI","JBL","JBLU","JBSAY","JBSS","JBTM",
"JEF","JEM","JFR","JHG","JHX","JJSF","JKHY","JKS","JLL","JMIA","JOE","JOYY","JPC","JQC",
"JSM","JXN","KAI","KALU","KAR","KARO","KBH","KBDC","KBR","KD","KE","KEN","KEP","KEX","KEY",
"KFY","KGS","KIM","KLC","KLG","KLIC","KMPB","KMPR","KMT","KMTS","KMX","KN","KNF","KNSA",
"KNSL","KNTK","KNX","KOD","KODK","KOF","KOS","KRC","KRG","KRMN","KRNT","KRYS","KSS","KT",
"KTB","KTOS","KURA","KVYO","KW","KWR","KYMR","KYN","L","LAC","LAD","LADR","LAES","LAMR",
"LAR","LASR","LAUR","LAZ","LB","LBRDA","LBRDK","LBRDP","LBRT","LBTYA","LBTYB","LBTYK",
"LC","LCII","LDI","LDP","LEA","LECO","LEG","LEGN","LENZ","LEU","LEVI","LFST","LFUS","LGIH",
"LGND","LH","LI","LIF","LII","LILA","LILAK","LIND","LINE","LITE","LIVN","LKFN","LKQ","LLYVA",
"LLYVK","LMAT","LMB","LMND","LNC","LNN","LNT","LNTH","LNW","LOAR","LOB","LOGI","LOMA",
"LOPE","LOT","LPG","LPX","LQDA","LQDT","LRN","LSCC","LSPD","LSTR","LTBR","LTC","LTH","LU",
"LUCK","LULU","LUMN","LUNR","LUV","LUXE","LVWR","LW","LWLG","LX","LXP","LXU","LYB","LYFT",
"LZ","LZB","M","MAA","MAAS","MAC","MAG","MAIN","MAN","MANH","MANU","MARA","MAS","MASI",
"MAT","MATV","MATW","MATX","MAX","MAZE","MBC","MBIN","MBINL","MBINM","MBINN","MBLY","MBWM",
"MBX","MC","MCB","MCBS","MCRI","MCW","MCY","MD","MDGL","MDU","MDXG","MEDP","MEG","MEGI",
"MEOH","MESO","METC","METCB","METCL","METCZ","MFA","MFAN","MFAO","MFH","MFIC","MFICL",
"MGA","MGEE","MGIC","MGM","MGNI","MGR","MGRB","MGRC","MGRD","MGRE","MGRT","MGTX","MGY",
"MHD","MHK","MHO","MIDD","MIR","MIRM","MKC","MKSI","MKTX","MLCO","MLI","MLKN","MLNK",
"MLTX","MLYS","MMI","MMS","MMSI","MMU","MMYT","MNDY","MNKD","MNMD","MNSO","MNTN","MOD","MODG",
"MOFG","MOH","MOMO","MOS","MP","MPB","MPW","MQ","MQY","MRC","MRCY","MRNA","MRP","MRTN",
"MRUS","MRVI","MRX","MSA","MSC","MSDL","MSEX","MSGE","MSGS","MSM","MTA","MTAL","MTCH","MTDR",
"MTG","MTH","MTN","MTRN","MTSI","MTSR","MTUS","MTX","MTZ","MUC","MUJ","MUR","MUSA","MUX",
"MVST","MWA","MXL","MYE","MYI","MYRG","NABL","NAD","NAK","NAMS","NAT","NATL","NAVI","NB",
"NBBK","NBHC","NBIX","NBN","NBR","NBTB","NBTX","NBXG","NCDL","NCLH","NCNO","NDMO","NDSN","NE",
"NEA","NEGG","NEO","NEOG","NESR","NEU","NEXA","NEXT","NFG","NFGC","NFJ","NG","NGD","NGVC",
"NGVT","NHC","NHI","NI","NIC","NICE","NIE","NIO","NJR","NKTR","NKX","NLY","NMAX","NMFC",
"NMFCZ","NMIH","NMRK","NMZ","NN","NNE","NNI","NNN","NNNN","NOAH","NOG","NOMD","NOV","NOVT",
"NPK","NPKI","NPO","NPWR","NRDS","NRIX","NRK","NSA","NSIT","NSP","NSSC","NTAP","NTB","NTCT",
"NTGR","NTLA","NTNX","NTRS","NTRSO","NTST","NUTX","NUV","NUVB","NUVL","NVAX","NVCR","NVEE",
"NVG","NVGS","NVMI","NVR","NVRI","NVST","NVT","NVTS","NWBI","NWE","NWL","NWN","NWS","NWSA",
"NXE","NXP","NXRT","NXST","NXT","NYAX","ADAM","ADAMG","ADAMI","ADAML","ADAMM","ADAMN","ADAMZ",
"NYT","NZF","OBDC","OBK","OC","OCFC","OCS","OCSL","ORBS","OCUL","ODC","ODD","ODP","ODV","OFG",
"OGE","OGN","OGS","OHI","OI","OII","OKLO","OKTA","OLED","OLLI","OLN","OLO","OLPX","OMAB","OWL",
"OXLC","OXLCG","OXLCI","OXLCL","OXLCN","OXLCO","OXLCP","OXLCZ","OZK","OZKAP","PAAS","PAC","PACS",
"PAG","PAGS","PAHC","PAR","PSKY","PARAA","PARR","PATH","PATK","PAX","PAXS","PAY","PAYC","PAYO",
"PB","PBF","PBH","PBI","PCH","PCN","PCOR","PCRX","PCT","PCTY","PCVX","PD","PDFS","PDI","PDM",
"PDO","PDT","PDX","PEB","PEBO","PECO","PEGA","PEN","PENG","PENN","PFBC","PFG","PFGC","PFLT",
"PFN","PFS","PFSI","PGEN","PGNY","PGRE","PGY","PHAR","PHAT","PHI","PHIN","PHK","PHLT","PHM",
"PHR","PHVS","PI","PII","PINC","PINS","PIPR","PJT","PK","PKG","PKX","PL","PLAB","PLMR","PLNT",
"PLOW","PLPC","PLSE","PLTK","PLUG","PLUS","PLXS","PLYM","PML","PMT","PMTU","PMTV","PNFP","PNFPP",
"PNR","PNTG","PNW","PODD","PONY","POOL","POR","POST","POWI","POWL","PPBI","PPC","PPG","PPTA","PR",
"PRAX","PRCH","PRCT","PRDO","PRG","PRGO","PRGS","PRI","PRIM","PRK","PRKS","PRLB","PRM","PRMB","PRME",
"PRO","PROK","PRSU","PRVA","PSEC","PSIX","PSN","PSNL","PSNY","PSNYW","PSO","PTA","PTC","PTCT","PTEN",
"PTGX","PTON","PTY","PUMP","PVH","PVLA","PWP","PX","PZZA","QBTS","QCRH","QD","QDEL","QFIN","QGEN",
"QLYS","QMMM","QNST","QQQX","QRVO","QS","QSR","QTWO","QUBT","QURE","QXO","R","RA","RAMP","RAPP","RAPT",
"RARE","RBC","RBCAA","RBRK","RCAT","RCUS","RDN","RDNT","RDVT","RDW","RDWR","RDY","REAL","REAX","REG",
"REGCO","REGCP","RELY","REPL","RERE","RES","REVG","REX","REXR","REYN","REZI","RGA","RGC","RGEN","RGLD",
"RGTI","RH","RHI","RHLD","RHP","RIG","RIGL","RIOT","RITM","RIVN","RKLB","RL","RLAY","RLI","RLJ","RLX","RMBS",
"RMT","RNA","RNG","RNP","RNR","RNST","RNW","ROAD","ROCK","ROG","ROIV","ROKU","ROOT","RPD","RPM","RPRX","RQI",
"RR","RRC","RRX","RS","RSG","RSI","RSKD","RTO","RUM","RUN","RUSHA","RUSHB","RVLV","RVMD","RVT","RVTY","RWT",
"RWTN","RWTO","RWTP","RXO","RXRX","RYAN","RYI","RYN","RYTM","RZB","RZC","RZLT","RZLV","S","SA","SABR","SAFE","SAFT",
"SAH","SAIA","SAIC","SAIL","SAM","SANA","SAND","SANM","SARO","SATS","SBAC","SBCF","SBET","SBGI","SBH","SBLK",
"SBRA","SBS","SBSI","SBSW","SCHL","SCI","SCL","SCS","SCSC","SDGR","SDHC","SDRL","SEB","SEDG","SEE","SEI","SEIC",
"SEM","SEMR","SENEA","SENEB","SEPN","SERV","SEZL","SFB","SFBS","SFD","SFM","SFNC","SG","SGHC","SGI","SGML","SGRY",
"SHAK","SHC","SHCO","SHLS","SHO","SHOO","SIBN","SID","SIFY","SIG","SIGI","SIGIP","SII","SILA","SIM","SIMO","SION",
"SIRI","SITE","SITM","SJM","SKE","SKM","SKT","SKWD","SKX","SKY","SKYH","SKYT","SKYW","SLAB","SLDP","SLG","SLGN",
"SLI","SLM","SLMBP","SLNO","SLRC","SLSR","SLVM","SM","SMA","SMBC","SMBK","SMCI","SMG","SMMT","SMTC","SMWB","SN",
"SNA","SNAP","SNCY","SNDR","SNDX","SNEX","SNN","SNV","SNX","SOBO","SOLV","SON","SONO","SOUN","SPB","SPHR","SPIR",
"SPNS","SPNT","SPR","SPRY","SPSC","SPTN","SPXC","SQM","SRAD","SRCE","SRPT","SRRK","SSB","SSD","SSII","SSL","SSNC",
"SSRM","SSTK","SSYS","ST","STAA","STAG","STBA","STC","STEL","STEP","STEW","STGW","STK","STKL","STLD","STM","STN",
"STNE","STNG","STOK","STR","STRA","STRL","STVN","STWD","STZ","SUI","SUPN","SUPV","SVM","SVRA","SVV","SW","SWIM",
"SWK","SWKS","SWX","SXI","SXT","SYBT","SYNA","SYRE","TAC","TAL","TALO","TAP","TARS","TASK","TBBK","TBLA","TBPH",
"TCBI","TCBIO","TCBK","TDC","TDOC","TDS","TDUP","TDW","TDY","TE","TECH","TECK","TEF","TEM","TEN","TENB","TEO",
"TERN","TEX","TFII","TFIN","TFPM","TFSL","TFX","TGB","TGLS","TGNA","TGS","TGTX","TH","THC","THFF","THG","THO","THQ",
"THR","THRM","THS","TIC","TIGO","TIGR","TILE","TIMB","TIPT","TIXT","TKC","TKR","TLK","TLN","TLRY","TLX","TMC","TMDX",
"TMHC","TMP","TMQ","TNC","TNDM","TNET","TNGX","TNK","TNL","TOL","TOST","TOWN","TPB","TPC","TPG","TPH","TPL","TPR",
"TR","TREE","TREX","TRIN","TRINI","TRINZ","TRIP","TRMB","TRMD","TRMK","TRML","TRN","TRNO","TROW","TRS","TRST","TRTX",
"TRUP","TRVI","TS","TSAT","TSEM","TSHA","TSLX","TSN","TTC","TTD","TTEK","TTI","TTMI","TUYA","TV","TVTX","TW","TWLO",
"TWO","U","UA","UAA","UAMY","UCB","UCTT","UDMY","UDR","UE","UEC","UFCS","UFPI","UFPT","UGI","UGP","UHAL","UHS","ULCC",
"ULS","ULTA","UMBF","UMC","UMH","UNF","UNFI","UNIT","UNM","UNMA","UP","UPB","UPBD","UPST","UPWK","URBN","URG","URGN",
"UROY","USAR","USAS","USFD","USLM","USPH","UTF","UTG","UTHR","UTI","UTL","UTZ","UUUU","UVE","UVSP","UVV","UWMC","UXIN",
"UZD","UZE","UZF","VAC","VAL","VALN","VBTX","VC","VCEL","VCTR","VCYT","VECO","VEL","VEON","VERA","VERX","VET","VFC",
"VFS","VG","VIAV","VICR","VINP","VIPS","VIR","VIRT","VIST","VITL","VIV","VKTX","VLRS","VLTO","VLY","VLYPN","VLYPO",
"VLYPP","VMEO","VMI","VMO","VNET","VNO","VNOM","VNT","VOYA","VRDN","VRE","VRNS","VRNT","VRRM","VRSN","VRTS","VSAT",
"VSCO","VSEC","VSH","VSTS","VTEX","VTLE","VTOL","VTRS","VTS","VTYX","VVV","VVX","VYX","VZLA","W","WABC","WAFD","WAFDP",
"WAL","WAT","WAY","WB","WBA","WBS","WBTN","WCC","WD","WDFC","WEN","WERN","WEX","WF","WFG","WFRD","WGO","WGS","WH","WHD",
"WHR","WINA","WING","WIX","WK","WKC","WLDN","WLFC","WLK","WLY","WLYB","WMG","WMK","WMS","WNS","WOLF","WOOF","WOR","WPC",
"WPP","WRBY","WRLD","WS","WSBC","WSBCP","WSC","WSFS","WSM","WSO","WSR","WST","WT","WTFC","WTM","WTRG","WTS","WTTR","WU",
"WULF","WVE","WWD","WWW","WY","WYNN","XENE","XERS","XHR","XIFR","XMTR","XNCR","XP","XPEL","XPO","XPRO","XYF","YALA","YB",
"YELP","YETI","YEXT","YMM","YOU","YPF","YSG","YUMC","Z","ZBH","ZBIO","ZBRA","ZD","ZETA","ZG","ZGN","ZIM","ZION","ZIONP",
"ZLAB","ZM","ZTO","ZWS","ZYME"
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
