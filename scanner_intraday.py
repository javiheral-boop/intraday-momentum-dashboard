# ==========================================
# scanner_intraday.py
# ==========================================

import yfinance as yf
import pandas as pd
import streamlit as st

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

def get_market_tickers():

    return WATCHLIST_USA

# ==========================================
# DOWNLOAD DATA
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

        print(e)

        return None

# ==========================================
# GET DF
# ==========================================

def get_ticker_df(data, ticker):

    try:

        df = data[ticker].copy()

        df = df.dropna()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(-1)

        return df

    except:

        return pd.DataFrame()

# ==========================================
# ATR
# ==========================================

def calcular_atr(df, periodo=14):

    high_low = (
        df["High"] - df["Low"]
    )

    high_close = abs(
        df["High"] -
        df["Close"].shift()
    )

    low_close = abs(
        df["Low"] -
        df["Close"].shift()
    )

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    return tr.rolling(periodo).mean()

# ==========================================
# DETECTOR INTRADAY
# ==========================================

def detectar_intraday(df, ticker):

    try:

        if len(df) < 30:
            return None

        current_price = float(
            df["Close"].iloc[-1]
        )

        open_price = float(
            df["Open"].iloc[0]
        )

        # ==================================
        # CAMBIO DEL DIA
        # ==================================

        day_change = (
            current_price - open_price
        ) / open_price

        if day_change < MIN_DAY_CHANGE:
            return None

        # ==================================
        # VOLUMEN RELATIVO
        # ==================================

        volume_now = df["Volume"].iloc[-1]

        volume_avg = (
            df["Volume"]
            .tail(20)
            .mean()
        )

        rel_volume = (
            volume_now / volume_avg
        )

        if rel_volume < MIN_REL_VOLUME:
            return None

        # ==================================
        # DISTANCIA MAXIMO DIA
        # ==================================

        high_day = df["High"].max()

        distance_high = (
            high_day - current_price
        ) / current_price

        if distance_high > MAX_DISTANCE_HIGH:
            return None

        # ==================================
        # MEDIA 20
        # ==================================

        ma20 = (
            df["Close"]
            .rolling(20)
            .mean()
            .iloc[-1]
        )

        # ==================================
        # VELAS VERDES
        # ==================================

        green = sum(

            df["Close"].tail(5) >
            df["Open"].tail(5)

        )

        # ==================================
        # ATR
        # ==================================

        atr = calcular_atr(df).iloc[-1]

        # ==================================
        # SCORE
        # ==================================

        score = 0

        if current_price > ma20:
            score += 20

        if rel_volume > 1.5:
            score += 20

        if rel_volume > 2:
            score += 20

        if green >= 2:
            score += 20

        if day_change > 0.005:
            score += 20

        # ==================================
        # FILTRO SCORE
        # ==================================

        if score < 60:
            return None

        # ==================================
        # BREAKOUT TRIGGER
        # ==================================

        breakout_trigger = round(
            high_day * 1.001,
            2
        )

        stop = round(
            breakout_trigger - (atr * 1.5),
            2
        )

        target = round(
            breakout_trigger + (atr * 3),
            2
        )

        risk = (
            breakout_trigger - stop
        )

        if risk <= 0:
            return None

        rr = (
            target - breakout_trigger
        ) / risk

        # ==================================
        # ESTADO SETUP
        # ==================================

        estado = ""

        if rel_volume > 2 and green >= 3:

            estado = (
                "🔥 MOMENTUM EXPANSION"
            )

        elif distance_high < 0.01:

            estado = (
                "🟢 PRE BREAKOUT"
            )

        else:

            estado = (
                "🟡 CONTINUATION"
            )

        # ==================================
        # RESULTADO
        # ==================================

        return {

            "Ticker": ticker,

            "Estado": estado,

            "Precio Actual": round(
                current_price,
                2
            ),

            "Entrada":
                breakout_trigger,

            "Target":
                target,

            "Stop":
                stop,

            "RR":
                round(rr, 2),

            "Cambio %": round(
                day_change * 100,
                2
            ),

            "Rel Volume": round(
                rel_volume,
                2
            ),

            "Score":
                score,

            "Hora Señal":
                datetime.now().strftime(
                    "%H:%M"
                )

        }

    except Exception as e:

        print(f"Error {ticker}: {e}")

        return None

# ==========================================
# MAIN
# ==========================================

@st.cache_data(ttl=30)
def scan_intraday():

    resultados = []

    tickers = get_market_tickers()

    data = descargar_market_data(
        tickers
    )

    if data is None:
        return pd.DataFrame()

    for ticker in tickers:

        try:

            df = get_ticker_df(
                data,
                ticker
            )

            result = detectar_intraday(
                df,
                ticker
            )

            if result:
                resultados.append(result)

        except:
            continue

    if not resultados:
        return pd.DataFrame()

    df_final = pd.DataFrame(
        resultados
    )

    df_final = df_final.sort_values(
        by="Score",
        ascending=False
    )

    return df_final.head(15)
