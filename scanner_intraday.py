import yfinance as yf
import pandas as pd
import streamlit as st
import pytz

from datetime import datetime

# ==========================================
# CONFIG
# ==========================================

INTERVAL = "5m"
PERIOD = "1d"

MIN_DAY_CHANGE = 0.003
MAX_DISTANCE_HIGH = 0.015

# ==========================================
# MEMORIA
# ==========================================

if "signal_memory" not in st.session_state:

    st.session_state.signal_memory = {}

# ==========================================
# WATCHLIST USA
# ==========================================

WATCHLIST_USA = [

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
    "AENA.MC",

    "SAP.DE","SIE.DE","ALV.DE","BMW.DE",
    "IFX.DE","VOW3.DE",

    "MC.PA","OR.PA","AIR.PA",

    "ASML.AS","AD.AS","INGA.AS",

    "ENI.MI","ISP.MI"

]

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

        return WATCHLIST_USA

# ==========================================
# UNIVERSO
# ==========================================

def get_market_tickers():

    now = datetime.now(
        pytz.timezone("Europe/Madrid")
    )

    hour = now.hour

    # EUROPA
    if 9 <= hour < 16:

        print("🌍 EUROPA")

        return WATCHLIST_EUROPE

    # USA
    elif 16 <= hour <= 23:

        print("🇺🇸 USA")

        sp500 = get_sp500_tickers()

        return list(
            set(
                WATCHLIST_USA +
                sp500[:200]
            )
        )

    return []

# ==========================================
# DESCARGA MASIVA
# ==========================================

@st.cache_data(ttl=30)

def descargar_market_data(tickers):

    try:

        data = yf.download(

            tickers=tickers,

            interval=INTERVAL,

            period=PERIOD,

            group_by="ticker",

            auto_adjust=True,

            threads=True,

            progress=False

        )

        return data

    except Exception as e:

        print(f"ERROR DESCARGA: {e}")

        return None

# ==========================================
# EXTRAER DF
# ==========================================

def get_ticker_df(data, ticker):

    try:

        df = data[ticker].copy()

        df = df.dropna()

        return df

    except:

        return pd.DataFrame()

# ==========================================
# LIDER
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
        day_change = (
            current_price - open_price
        ) / open_price

        if day_change < MIN_DAY_CHANGE:

            return False

        # Momentum reciente
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
        distance = (
            high_20 - precio
        ) / high_20

        if distance > MAX_DISTANCE_HIGH:

            return None

        # Stop
        stop = low_20

        risk = precio - stop

        if risk <= 0:

            return None

        # Target
        target = precio + (
            risk * 2
        )

        rr = (
            target - precio
        ) / risk

        # Momentum score
        momentum = (
            precio -
            float(df["Close"].iloc[-10])
        ) / float(df["Close"].iloc[-10])

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
# MAIN
# ==========================================

def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    print(f"🌍 Tickers: {len(tickers)}")

    if not tickers:

        return pd.DataFrame()

    # ======================================
    # DESCARGA MASIVA
    # ======================================

    data = descargar_market_data(tickers)

    if data is None:

        return pd.DataFrame()

    # ======================================
    # PROCESAR
    # ======================================

    for ticker in tickers:

        try:

            df = get_ticker_df(
                data,
                ticker
            )

            if df.empty:

                continue

            if not es_lider(df):

                continue

            setup = detectar_setup(df)

            if setup is None:

                continue

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

            resultados.append({

                "Ticker": ticker,

                "Hora Señal": signal_time.strftime(
                    "%H:%M:%S"
                ),

                "Minutos": minutes_live,

                "Estado": status,

                **setup

            })

        except Exception as e:

            print(f"ERROR {ticker}: {e}")

            continue

    # ======================================
    # DATAFRAME
    # ======================================

    df = pd.DataFrame(resultados)

    print(f"🎯 SETUPS: {len(df)}")

    if df.empty:

        return df

    return df.sort_values(

        by=[

            "Score",
            "Minutos"

        ],

        ascending=[

            False,
            True

        ]

    )
