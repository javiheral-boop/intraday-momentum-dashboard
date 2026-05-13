# scanner_intraday.py

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

MIN_CHANGE = 0.0025
VOL_MULTIPLIER = 0.9

PULLBACK_TOLERANCE = 0.004

MAX_EXTENSION = 0.03

# ==========================================
# MEMORIA SEÑALES
# ==========================================

if "signal_memory" not in st.session_state:

    st.session_state.signal_memory = {}

# ==========================================
# WATCHLIST USA
# ==========================================

WATCHLIST_PRIORITY_USA = [

    "NVDA","TSLA","AMD","META","AAPL","MSFT",
    "AMZN","GOOGL","PLTR","SMCI","ARM",
    "AVGO","MRVL","MU","QCOM","COHR",
    "ADI","ANET","ASML","LRCX","KLAC",
    "AMAT","ON","MCHP","NXPI","AI",
    "SOUN","APP","AFRM","RKLB","IONQ",
    "TEM","SOFI","HOOD","RBLX","SHOP",
    "SNOW","NET","DDOG","ZS","CRWD",
    "PANW","MSTR","COIN","NFLX","CELH",
    "CVNA","DKNG","UBER","LYFT","LULU",
    "DIS","BA","PYPL","ADBE","INTC"

]

# ==========================================
# WATCHLIST EUROPA
# ==========================================

WATCHLIST_EUROPE = [

    "SAN.MC","BBVA.MC","ITX.MC","IBE.MC",
    "REP.MC","FER.MC","ACS.MC","AMS.MC",
    "GRF.MC","AENA.MC",

    "SAP.DE","SIE.DE","ALV.DE","BMW.DE",
    "BAS.DE","IFX.DE","DB1.DE","VOW3.DE",
    "MBG.DE","DTE.DE","EOAN.DE",

    "MC.PA","OR.PA","TTE.PA","AIR.PA",
    "BNP.PA","KER.PA","RMS.PA","SU.PA",
    "DG.PA","CAP.PA","AI.PA",

    "ASML.AS","AD.AS","INGA.AS",
    "ASM.AS","MT.AS","PHIA.AS",

    "ENI.MI","ISP.MI",

    "UCB.BR","ABI.BR","ARGX.BR",

    "NESN.SW","ROG.SW",

    "ULVR.L",

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
# FILTRO LIDER
# ==========================================

def es_lider(df):

    try:

        if len(df) < 30:

            return False

        open_price = float(
            df["Open"].iloc[0]
        )

        current_price = float(
            df["Close"].iloc[-1]
        )

        # ==================================
        # CAMBIO %
        # ==================================

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
        # MOMENTUM FLEXIBLE
        # ==================================

        ultimos = df["Close"].iloc[-5:]

        green = 0

        for i in range(1, len(ultimos)):

            if ultimos.iloc[i] > ultimos.iloc[i - 1]:

                green += 1

        if green < 3:

            return False

        return True

    except:

        return False

# ==========================================
# DETECTAR SETUP
# ==========================================

def detectar_setup(df):

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

            return None

        # ==================================
        # EXTENSION
        # ==================================

        extension = (
            precio - orb_high
        ) / orb_high

        if extension > MAX_EXTENSION:

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

        # ==================================
        # SCORE
        # ==================================

        score = 0

        # Momentum
        score += min(
            extension * 100 * 8,
            25
        )

        # Calidad riesgo
        score += min(
            risk * 10,
            25
        )

        # RR
        score += min(
            rr * 15,
            30
        )

        # Cercanía breakout
        distance_from_orb = (
            precio - orb_high
        ) / orb_high

        score += max(
            0,
            20 - (
                distance_from_orb * 1000
            )
        )

        score = round(score, 1)

        return {

            "Entrada": round(precio, 2),

            "Stop": round(stop, 2),

            "Target": round(target, 2),

            "RR": round(rr, 2),

            "Cambio %": round(
                extension * 100,
                2
            ),

            "Score": score

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

        # ==================================
        # TIMESTAMP SEÑAL
        # ==================================

        now = datetime.now(
            pytz.timezone("Europe/Madrid")
        )

        signal_memory = (
            st.session_state.signal_memory
        )

        if ticker not in signal_memory:

            signal_memory[ticker] = now

        signal_time = signal_memory[ticker]

        minutes_live = int(

            (
                now - signal_time
            ).total_seconds() / 60

        )

        # ==================================
        # ESTADO
        # ==================================

        if minutes_live <= 5:

            status = "🔥 FRESH"

        elif minutes_live <= 15:

            status = "⚠️ ACTIVE"

        else:

            status = "❌ LATE"

        return {

            "Ticker": ticker,

            "Hora Señal": signal_time.strftime(
                "%H:%M:%S"
            ),

            "Minutos": minutes_live,

            "Estado": status,

            **setup

        }

    except:

        return None

# ==========================================
# MAIN SCAN
# ==========================================

def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    if not tickers:

        return pd.DataFrame()

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

            except:

                continue

    df = pd.DataFrame(resultados)

    if df.empty:

        return df

    # ======================================
    # ORDEN FINAL
    # ======================================

    df = df.sort_values(

        by=[

            "Score",
            "Minutos"

        ],

        ascending=[

            False,
            True

        ]

    )

    return df
