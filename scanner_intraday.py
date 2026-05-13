import yfinance as yf
import pandas as pd
import streamlit as st

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from datetime import datetime
import pytz

# ==========================================
# CONFIG
# ==========================================

INTERVAL = "1m"
PERIOD = "1d"

# ==========================================
# FILTROS
# ==========================================

# Movimiento mínimo intradía
MIN_CHANGE = 0.0025

# RVOL más flexible
VOL_MULTIPLIER = 0.9

# Pullback tolerancia
PULLBACK_TOLERANCE = 0.004

# Máxima extensión desde breakout
MAX_EXTENSION = 0.03

# ==========================================
# WATCHLIST USA
# ==========================================

WATCHLIST_PRIORITY_USA = [

    # MAG7
    "NVDA","TSLA","AMD","META","AAPL","MSFT",
    "AMZN","GOOGL",

    # AI / SEMIS
    "SMCI","ARM","AVGO","MRVL","MU","QCOM",
    "COHR","ADI","ANET","ASML","LRCX",
    "KLAC","AMAT","ON","MCHP","NXPI",

    # HIGH BETA
    "PLTR","AI","SOUN","APP","AFRM",
    "RKLB","IONQ","TEM","SOFI","HOOD",
    "RBLX","SHOP","SNOW","NET","DDOG",
    "ZS","CRWD","PANW","MSTR","COIN",

    # CONSUMER / MOMENTUM
    "NFLX","CELH","CVNA","DKNG","UBER",
    "LYFT","LULU","DIS","BA","PYPL",
    "ADBE","INTC"

]

# ==========================================
# WATCHLIST EUROPA
# ==========================================

WATCHLIST_EUROPE = [

    # España
    "SAN.MC","BBVA.MC","ITX.MC","IBE.MC",
    "REP.MC","FER.MC","ACS.MC","AMS.MC",
    "GRF.MC","AENA.MC",

    # Alemania
    "SAP.DE","SIE.DE","ALV.DE","BMW.DE",
    "BAS.DE","IFX.DE","DB1.DE","VOW3.DE",
    "MBG.DE","DTE.DE","EOAN.DE",

    # Francia
    "MC.PA","OR.PA","TTE.PA","AIR.PA",
    "BNP.PA","KER.PA","RMS.PA","SU.PA",
    "DG.PA","CAP.PA","AI.PA",

    # Holanda
    "ASML.AS","AD.AS","INGA.AS",
    "ASM.AS","MT.AS","PHIA.AS",

    # Italia
    "ENI.MI","ISP.MI",

    # Bélgica
    "UCB.BR","ABI.BR","ARGX.BR",

    # Suiza
    "NESN.SW","ROG.SW",

    # UK
    "ULVR.L",

    # Dinamarca
    "NOVO-B.CO"

]

# ==========================================
# CLEAN DF
# ==========================================

def clean_df(df):

    if df is None or df.empty:

        return pd.DataFrame()

    df = df.dropna()

    if isinstance(df.columns, pd.MultiIndex):

        df.columns = df.columns.droplevel(-1)

    return df

# ==========================================
# SP500
# ==========================================

@st.cache_data(ttl=3600)

def get_sp500_tickers():

    try:

        table = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )

        sp500 = table[0]["Symbol"].tolist()

        return [

            x.replace(".", "-")

            for x in sp500

        ]

    except Exception as e:

        print("ERROR SP500:", e)

        return WATCHLIST_PRIORITY_USA

# ==========================================
# UNIVERSO DINAMICO
# ==========================================

def get_market_tickers():

    now = datetime.now(
        pytz.timezone("Europe/Madrid")
    )

    hora = now.hour

    # ======================================
    # EUROPA
    # ======================================

    if 9 <= hora < 16:

        print("🌍 MODO EUROPA")

        return WATCHLIST_EUROPE

    # ======================================
    # USA
    # ======================================

    elif 16 <= hora <= 23:

        print("🇺🇸 MODO USA")

        sp500 = get_sp500_tickers()

        universo = list(

            set(

                WATCHLIST_PRIORITY_USA +

                sp500[:250]

            )

        )

        return universo

    print("⏸️ MERCADO CERRADO")

    return []

# ==========================================
# DESCARGA
# ==========================================

@st.cache_data(ttl=60)

def descargar(ticker):

    try:

        df = yf.download(

            ticker,

            interval=INTERVAL,

            period=PERIOD,

            progress=False,

            threads=True,

            prepost=False

        )

        df = clean_df(df)

        return df

    except Exception as e:

        print(f"ERROR DESCARGA {ticker}: {e}")

        return pd.DataFrame()

# ==========================================
# FILTRO LIDER
# ==========================================

def es_lider(df, ticker=""):

    try:

        if df.empty:

            print(f"{ticker} vacío")

            return False

        if len(df) < 30:

            print(f"{ticker} pocos datos")

            return False

        open_price = float(
            df["Open"].iloc[0]
        )

        current_price = float(
            df["Close"].iloc[-1]
        )

        # ==================================
        # CHANGE
        # ==================================

        change = (
            current_price - open_price
        ) / open_price

        if change < MIN_CHANGE:

            print(
                f"{ticker} cambio insuficiente"
            )

            return False

        # ==================================
        # RVOL
        # ==================================

        vol_actual = float(
            df["Volume"].iloc[-15:].sum()
        )

        vol_media = (

            float(

                df["Volume"]
                .rolling(30)
                .mean()
                .iloc[-1]

            ) * 15

        )

        if vol_actual < (
            vol_media * VOL_MULTIPLIER
        ):

            print(f"{ticker} sin RVOL")

            return False

        # ==================================
        # MA20
        # ==================================

        ma20 = float(

            df["Close"]
            .rolling(20)
            .mean()
            .iloc[-1]

        )

        if current_price < ma20:

            print(f"{ticker} bajo MA20")

            return False

        # ==================================
        # MOMENTUM FLEXIBLE
        # ==================================

        ultimos = df["Close"].iloc[-5:]

        green = 0

        for i in range(1, len(ultimos)):

            if ultimos.iloc[i] > ultimos.iloc[i - 1]:

                green += 1

        if green < 3:

            print(f"{ticker} momentum débil")

            return False

        return True

    except Exception as e:

        print(f"ERROR LIDER {ticker}: {e}")

        return False

# ==========================================
# DETECTAR SETUP
# ==========================================

def detectar_setup(df, ticker=""):

    try:

        if len(df) < 30:

            return None

        # ==================================
        # OPENING RANGE
        # ==================================

        opening = df.iloc[:15]

        orb_high = float(
            opening["High"].max()
        )

        orb_low = float(
            opening["Low"].min()
        )

        precio = float(
            df["Close"].iloc[-1]
        )

        # ==================================
        # BREAKOUT
        # ==================================

        if precio <= orb_high:

            print(f"{ticker} no breakout")

            return None

        # ==================================
        # EXTENSION
        # ==================================

        extension = (
            precio - orb_high
        ) / orb_high

        if extension > MAX_EXTENSION:

            print(f"{ticker} extendido")

            return None

        # ==================================
        # STOP
        # ==================================

        stop = max(

            orb_low,

            precio * 0.985

        )

        risk = precio - stop

        if risk <= 0:

            return None

        # ==================================
        # TARGET
        # ==================================

        target = precio + (
            risk * 2
        )

        rr = (
            target - precio
        ) / risk

        return {

            "Entrada": round(precio, 2),

            "Stop": round(stop, 2),

            "Target": round(target, 2),

            "RR": round(rr, 2),

            "Cambio %": round(
                extension * 100,
                2
            )

        }

    except Exception as e:

        print(f"ERROR SETUP {ticker}: {e}")

        return None

# ==========================================
# PROCESAR TICKER
# ==========================================

def procesar_ticker(ticker):

    try:

        print(f"🔎 {ticker}")

        df = descargar(ticker)

        if df.empty:

            return None

        if not es_lider(df, ticker):

            return None

        setup = detectar_setup(
            df,
            ticker
        )

        if setup is None:

            return None

        print(f"🔥 SETUP {ticker}")

        return {

            "Ticker": ticker,

            **setup

        }

    except Exception as e:

        print(f"ERROR {ticker}: {e}")

        return None

# ==========================================
# MAIN SCAN
# ==========================================

def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    if not tickers:

        return pd.DataFrame()

    print(
        f"🚀 ESCANEANDO {len(tickers)} TICKERS"
    )

    # ======================================
    # ESCANEO PARALELO
    # ======================================

    with ThreadPoolExecutor(
        max_workers=30
    ) as executor:

        futures = {

            executor.submit(
                procesar_ticker,
                ticker
            ): ticker

            for ticker in tickers

        }

        for future in as_completed(futures):

            try:

                result = future.result()

                if result is not None:

                    resultados.append(result)

            except Exception as e:

                print("ERROR FUTURE:", e)

    # ======================================
    # DATAFRAME
    # ======================================

    df = pd.DataFrame(resultados)

    if df.empty:

        print("⚠️ SIN SETUPS")

        return df

    # ======================================
    # SORT
    # ======================================

    df = df.sort_values(

        by=["RR", "Cambio %"],

        ascending=False

    )

    print(
        f"✅ SETUPS ENCONTRADOS: {len(df)}"
    )

    return df
