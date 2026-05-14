# scanner_intraday.py

import yfinance as yf
import pandas as pd
import streamlit as st
import pytz

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from datetime import datetime

# ==========================================
# CONFIG
# ==========================================

INTERVAL = "5m"
PERIOD = "1d"

MAX_WORKERS = 25

# ==========================================
# FILTROS
# ==========================================

MIN_DAY_CHANGE = 0.003      # +0.3%
MAX_DISTANCE_HIGH = 0.012   # 1.2%

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

    "ASML.AS","AD.AS","INGA.AS",
    "ASM.AS","MT.AS","PHIA.AS",

    "ENI.MI","ISP.MI",

    "NESN.SW","ROG.SW",

    "ULVR.L",

    "NOVO-B.CO"

]

# ==========================================
# CLEAN DF
# ==========================================

def clean_df(df):

    if df is None:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    df = df.dropna()

    if df.empty:
        return pd.DataFrame()

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

    except Exception as e:

        print(f"ERROR SP500: {e}")

        return WATCHLIST_PRIORITY_USA

# ==========================================
# UNIVERSO
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

    print("⏰ MERCADO CERRADO")

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

            threads=False,

            prepost=False,

            auto_adjust=True

        )

        df = clean_df(df)

        if df.empty:

            return pd.DataFrame()

        return df

    except Exception as e:

        print(f"❌ ERROR DESCARGA {ticker}: {e}")

        return pd.DataFrame()

# ==========================================
# FILTRO LIDER
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

        # ==================================
        # CAMBIO DIARIO
        # ==================================

        day_change = (
            current_price - open_price
        ) / open_price

        if day_change < MIN_DAY_CHANGE:

            return False

        # ==================================
        # MOMENTUM
        # ==================================

        ultimos = df["Close"].iloc[-5:]

        velas_verdes = 0

        for i in range(1, len(ultimos)):

            if ultimos.iloc[i] > ultimos.iloc[i - 1]:

                velas_verdes += 1

        if velas_verdes < 3:

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

        return True

    except Exception as e:

        print(f"❌ ERROR LIDER: {e}")

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

        # ==================================
        # MAXIMOS RECIENTES
        # ==================================

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

        # ==================================
        # CERCA DE MAXIMOS
        # ==================================

        distance_high = (
            high_20 - precio
        ) / high_20

        if distance_high > MAX_DISTANCE_HIGH:

            return None

        # ==================================
        # STOP
        # ==================================

        stop = low_20

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
        # MOMENTUM
        # ==================================

        momentum = (

            precio -

            float(df["Close"].iloc[-10])

        ) / float(df["Close"].iloc[-10])

        # ==================================
        # SCORE
        # ==================================

        score = (
            (momentum * 1000) +
            (rr * 20)
        )

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

    except Exception as e:

        print(f"❌ ERROR SETUP: {e}")

        return None

# ==========================================
# PROCESAR TICKER
# ==========================================

def procesar_ticker(ticker):

    try:

        df = descargar(ticker)

        if df.empty:

            return None

        # ==================================
        # FILTRO LIDER
        # ==================================

        if not es_lider(df):

            return None

        # ==================================
        # SETUP
        # ==================================

        setup = detectar_setup(df)

        if setup is None:

            return None

        # ==================================
        # TIMESTAMP
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
        # STATUS
        # ==================================

        if minutes_live <= 5:

            status = "🔥 FRESH"

        elif minutes_live <= 15:

            status = "⚠️ ACTIVE"

        else:

            status = "❌ LATE"

        resultado = {

            "Ticker": ticker,

            "Hora Señal": signal_time.strftime(
                "%H:%M:%S"
            ),

            "Minutos": minutes_live,

            "Estado": status,

            **setup

        }

        print(f"✅ SETUP: {ticker}")

        return resultado

    except Exception as e:

        print(f"❌ ERROR TICKER {ticker}: {e}")

        return None

# ==========================================
# MAIN
# ==========================================

def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    print(f"\n🌍 TOTAL TICKERS: {len(tickers)}")

    if not tickers:

        return pd.DataFrame()

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
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

                print(f"❌ ERROR FUTURE: {e}")

                continue

    df = pd.DataFrame(resultados)

    print(f"🎯 TOTAL SETUPS: {len(df)}")

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
