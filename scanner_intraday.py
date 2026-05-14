# scanner_intraday.py

import yfinance as yf
import pandas as pd
import numpy as np
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
# FILTROS FLEXIBLES
# ==========================================

MIN_CHANGE = 0.0015          # 0.15%
VOL_MULTIPLIER = 0.7

MAX_EXTENSION = 0.05         # 5%

# ==========================================
# MEMORIA
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

    "ASML.AS","AD.AS","INGA.AS",
    "ASM.AS","MT.AS","PHIA.AS",

    "ENI.MI","ISP.MI",

    "NESN.SW","ROG.SW",

    "ULVR.L",

    "NOVO-B.CO"

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

        return [

            x.replace(".", "-")

            for x in sp500

        ]

    except:

        return WATCHLIST_PRIORITY_USA

# ==========================================
# UNIVERSO
# ==========================================

def get_market_tickers():

    now = datetime.now(
        pytz.timezone("Europe/Madrid")
    )

    hora = now.hour

    # EUROPA
    if 9 <= hora < 16:

        return WATCHLIST_EUROPE

    # USA
    elif 16 <= hora <= 23:

        sp500 = get_sp500_tickers()

        return list(

            set(

                WATCHLIST_PRIORITY_USA +

                sp500[:300]

            )

        )

    return []

# ==========================================
# DESCARGA
# ==========================================

@st.cache_data(ttl=30)

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
# LIDER FLEXIBLE
# ==========================================

def es_lider(df):

    try:

        if len(df) < 20:
            return False

        open_price = float(
            df["Open"].iloc[0]
        )

        current_price = float(
            df["Close"].iloc[-1]
        )

        # Cambio diario
        change = (
            current_price - open_price
        ) / open_price

        if change < 0.003:
            return False

        # Momentum últimos minutos
        ultimos = df["Close"].iloc[-5:]

        green = 0

        for i in range(1, len(ultimos)):

            if ultimos.iloc[i] > ultimos.iloc[i - 1]:

                green += 1

        if green < 3:
            return False

        # MA20
        ma20 = float(
            df["Close"]
            .rolling(20)
            .mean()
            .iloc[-1]
        )

        if current_price < ma20:
            return False

        return True

    except:

        return False

# ==========================================
# SETUP
# ==========================================

def detectar_setup(df):

    try:

        if len(df) < 20:
            return None

        precio = float(
            df["Close"].iloc[-1]
        )

        high_20 = float(
            df["High"]
            .iloc[-20:]
            .max()
        )

        low_20 = float(
            df["Low"]
            .iloc[-20:]
            .min()
        )

        # Cerca de máximos
        distance_high = (
            high_20 - precio
        ) / high_20

        if distance_high > 0.01:
            return None

        # Stop dinámico
        stop = low_20

        risk = precio - stop

        if risk <= 0:
            return None

        target = precio + (
            risk * 2
        )

        rr = (
            target - precio
        ) / risk

        # Score
        momentum = (
            precio - df["Close"].iloc[-10]
        ) / df["Close"].iloc[-10]

        score = (
            momentum * 1000
        ) + (rr * 20)

        return {

            "Entrada": round(precio, 2),

            "Stop": round(stop, 2),

            "Target": round(target, 2),

            "RR": round(rr, 2),

            "Cambio %": round(
                momentum * 100,
                2
            ),

            "Score": round(score, 1)

        }

    except:

        return None
        
# ==========================================
# PROCESAR
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
        # STATUS
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
# MAIN
# ==========================================

def procesar_ticker_debug(ticker):

    try:

        df = descargar(ticker)

        if df.empty:

            return None

        # DATA OK
        data_ok = {
            "estado": "data_ok"
        }

        if not es_lider(df):

            return data_ok

        # LIDER
        lider = {
            "estado": "lider"
        }

        setup = detectar_setup(df)

        if setup is None:

            return lider

        # SETUP REAL
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

        if minutes_live <= 5:

            status = "🔥 FRESH"

        elif minutes_live <= 15:

            status = "⚠️ ACTIVE"

        else:

            status = "❌ LATE"

        return {

            "estado": "setup",

            "data": {

                "Ticker": ticker,

                "Hora Señal": signal_time.strftime(
                    "%H:%M:%S"
                ),

                "Minutos": minutes_live,

                "Estado": status,

                **setup

            }

        }

    except Exception as e:

        print(f"❌ ERROR {ticker}: {e}")

        return None

def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    print(f"\n🌍 Total tickers: {len(tickers)}")

    if not tickers:

        print("❌ No hay tickers")
        return pd.DataFrame()

    total_ok_data = 0
    total_lider = 0
    total_setup = 0

    with ThreadPoolExecutor(
        max_workers=40
    ) as executor:

        futures = {

            executor.submit(
                procesar_ticker_debug,
                ticker
            ): ticker

            for ticker in tickers

        }

        for future in as_completed(futures):

            result = future.result()

            if result is None:
                continue

            estado = result["estado"]

            if estado == "data_ok":
                total_ok_data += 1

            elif estado == "lider":
                total_lider += 1

            elif estado == "setup":

                total_setup += 1

                resultados.append(
                    result["data"]
                )

    print(f"✅ Datos OK: {total_ok_data}")
    print(f"🔥 Líderes: {total_lider}")
    print(f"🎯 Setups: {total_setup}")

    df = pd.DataFrame(resultados)

    if df.empty:

        return df

    return df.sort_values(
        by=["Score", "Minutos"],
        ascending=[False, True]
    )

    return df
