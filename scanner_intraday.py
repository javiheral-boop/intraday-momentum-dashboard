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

MIN_CHANGE = 0.004
VOL_MULTIPLIER = 1.2

PULLBACK_TOLERANCE = 0.003

MAX_EXTENSION = 0.012

# ==========================================
# WATCHLIST USA
# ==========================================

WATCHLIST_PRIORITY_USA = [

    "NVDA","TSLA","AMD","META","AAPL","MSFT",
    "PLTR","SMCI","ARM","AMZN","NFLX","COIN",
    "MSTR","AVGO","QCOM","MU","AI","SNOW",
    "PANW","CRWD","SHOP","RBLX","HOOD",
    "UBER","LYFT","DKNG","SOFI","INTC",
    "BA","DIS","GOOGL","PYPL","ADBE",
    "MRVL","ANET","LULU","CELH","CVNA",
    "NET","DDOG","ZS","OKLO","RKLB",
    "IONQ","TEM","SOUN","APP","AFRM"

]

# ==========================================
# WATCHLIST EUROPA
# ==========================================

WATCHLIST_EUROPE = [

    "ASML.AS","SAP.DE","SIE.DE","ALV.DE",
    "MC.PA","OR.PA","TTE.PA",
    "SAN.MC","BBVA.MC","ITX.MC","IBE.MC",
    "NOVO-B.CO","NESN.SW","ROG.SW",
    "ULVR.L","AIR.PA","BNP.PA",
    "ENI.MI","ISP.MI","AD.AS",
    "INGA.AS","BMW.DE","BAS.DE",
    "REP.MC","FER.MC","ACS.MC",
    "AMS.MC","GRF.MC","AENA.MC",
    "KER.PA","RMS.PA","SU.PA",
    "DG.PA","CAP.PA","AI.PA",
    "VOW3.DE","DB1.DE","IFX.DE",
    "MBG.DE","DTE.DE","EOAN.DE",
    "PHIA.AS","ASM.AS","MT.AS",
    "UCB.BR","ABI.BR","ARGX.BR"

]

# ==========================================
# CLEAN
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

        sp500 = [
            x.replace(".", "-")
            for x in sp500
        ]

        return sp500

    except:

        return WATCHLIST_PRIORITY_USA

# ==========================================
# UNIVERSO SEGUN HORA
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

        return WATCHLIST_EUROPE

    # ======================================
    # USA
    # ======================================

    elif 16 <= hora <= 23:

        sp500 = get_sp500_tickers()

        return list(
            set(
                WATCHLIST_PRIORITY_USA +
                sp500[:250]
            )
        )

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

        return clean_df(df)

    except:

        return pd.DataFrame()

# ==========================================
# LIDER
# ==========================================

def es_lider(df):

    try:

        if len(df) < 30:
            return False

        open_price = float(df["Open"].iloc[0])

        current_price = float(
            df["Close"].iloc[-1]
        )

        change = (
            current_price - open_price
        ) / open_price

        if change < MIN_CHANGE:
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
            return False

        # ==================================
        # MOMENTUM
        # ==================================

        ultimos = df["Close"].iloc[-5:]

        if not ultimos.is_monotonic_increasing:
            return False

        return True

    except:

        return False

# ==========================================
# SETUP
# ==========================================

def detectar_setup(df):

    try:

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

        if precio <= orb_high:
            return None

        extension = (
            precio - orb_high
        ) / orb_high

        if extension > MAX_EXTENSION:
            return None

        stop = max(
            orb_low,
            precio * 0.985
        )

        risk = precio - stop

        if risk <= 0:
            return None

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
            "RR": round(rr, 2)

        }

    except:

        return None

# ==========================================
# PROCESAR TICKER
# ==========================================

def procesar_ticker(ticker):

    try:

        df = descargar(ticker)

        if df.empty:
            return None

        if not es_lider(df):
            return None

        setup = detectar_setup(df)

        if setup is None:
            return None

        return {

            "Ticker": ticker,
            **setup

        }

    except:

        return None

# ==========================================
# MAIN
# ==========================================

def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    if not tickers:
        return pd.DataFrame()

    with ThreadPoolExecutor(
        max_workers=25
    ) as executor:

        futures = {

            executor.submit(
                procesar_ticker,
                ticker
            ): ticker

            for ticker in tickers
        }

        for future in as_completed(futures):

            result = future.result()

            if result is not None:

                resultados.append(result)

    df = pd.DataFrame(resultados)

    if df.empty:
        return df

    return df.sort_values(
        "RR",
        ascending=False
    )
