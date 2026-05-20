import yfinance as yf
import pandas as pd
import streamlit as st
import pytz

from datetime import datetime

# ==========================================
# CONFIG
# ==========================================

INTERVAL = "5m"
PERIOD = "5d"

MIN_DAY_CHANGE = 0.0015
MAX_DISTANCE_HIGH = 0.03

MIN_REL_VOLUME = 1.3

# ==========================================
# MEMORIA
# ==========================================

if "signal_memory" not in st.session_state:
    st.session_state.signal_memory = {}

# ==========================================
# WATCHLIST
# ==========================================

WATCHLIST_USA = [

    "NVDA","TSLA","AMD","META","AAPL","MSFT",
    "AMZN","GOOGL","PLTR","SMCI","ARM",
    "AVGO","MRVL","MU","QCOM","COHR",
    "APP","AFRM","RKLB","IONQ","SOUN",
    "CRWD","PANW","NET","SNOW","DDOG",
    "MSTR","COIN","SHOP","RBLX","SOFI"

]

# ==========================================
# MARKET TICKERS
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

    except:

        return None

# ==========================================
# GET DF
# ==========================================

def get_ticker_df(data, ticker):

    try:

        df = data[ticker].copy()

        df = df.dropna()

        return df

    except:

        return pd.DataFrame()

# ==========================================
# DETECTOR
# ==========================================

        if rel_volume > 2:
            score += 20

        if green >= 2:
            score += 20

        if day_change > 0.005:
            score += 20

        breakout_trigger = round(
            high_day * 1.001,
            2
        )

        stop = round(
            ma20,
            2
        )

        target = round(
            breakout_trigger +
            ((breakout_trigger - stop) * 2),
            2
        )

        rr = (
            target - breakout_trigger
        ) / (
            breakout_trigger - stop
        )

        if score < 60:
            return None

        return {

            "Ticker": ticker,

            "Entrada": breakout_trigger,
            "Stop": stop,
            "Target": target,

            "RR": round(rr, 2),
            "Cambio %": round(day_change * 100, 2),
            "Rel Volume": round(rel_volume, 2),
            "Score": score,

            "Estado": "🔥 PRE BREAKOUT",
            "Hora Señal": datetime.now().strftime("%H:%M")

        }

    except:

        return None

# ==========================================
# MAIN
# ==========================================

@st.cache_data(ttl=30)
def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    data = descargar_market_data(tickers)

    if data is None:
        return pd.DataFrame()

    for ticker in tickers:

        try:

            df = get_ticker_df(data, ticker)

            result = detectar_intraday(df, ticker)

            if result:
                resultados.append(result)

        except:
            continue

    if not resultados:
        return pd.DataFrame()

    df_final = pd.DataFrame(resultados)

    df_final = df_final.sort_values(
        by="Score",
        ascending=False
    )

    return df_final.head(15)
