import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# CONFIG
# ==========================================

MIN_VOLUME = 300000

ATR_STOP = 2
ATR_TARGET = 3

# ==========================================
# EUROPA
# ==========================================

WATCHLIST_EUROPE = [

    "SAN.MC","BBVA.MC","ITX.MC","IBE.MC",
    "REP.MC","SAP.DE","SIE.DE","ALV.DE",
    "BAS.DE","BMW.DE","MC.PA","OR.PA",
    "TTE.PA","AIR.PA","BNP.PA","ASML.AS",
    "INGA.AS","AD.AS","ENEL.MI","ENI.MI",
    "ISP.MI","NESN.SW","ROG.SW",
    "NOVO-B.CO","ULVR.L"

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

        return [

            "AAPL","MSFT","NVDA",
            "AMZN","GOOGL","META"

        ]

# ==========================================
# UNIVERSO
# ==========================================

def get_universe():

    usa = get_sp500_tickers()

    europa = WATCHLIST_EUROPE

    return list(set(

    usa[:150] +

    [

        "NVDA","SMCI","PLTR","COHR",
        "ADI","AVGO","MRVL","MU",
        "ARM","TSLA","META","AAPL",
        "MSFT","AMZN","GOOGL",
        "CRWD","PANW","SNOW",
        "NET","DDOG","SHOP",
        "MSTR","COIN","RKLB"

    ]

    + europa
    ))

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

        [
            high_low,
            high_close,
            low_close
        ],

        axis=1

    ).max(axis=1)

    return tr.rolling(
        periodo
    ).mean()

# ==========================================
# MAIN
# ==========================================

@st.cache_data(ttl=60)

def scan_swing():

    resultados = []

    tickers = get_universe()

    tickers = tickers[:500]

    try:

        data = yf.download(

            tickers,

            period="1y",

            group_by="ticker",

            threads=True,

            progress=False

        )

    except:

        return pd.DataFrame()

    # ======================================
    # SPY
    # ======================================

    try:

        spy = yf.download(
            "SPY",
            period="1y",
            progress=False
        )

        spy = clean_df(spy)

        spy_close = spy["Close"]

        spy_sma200 = (
            spy_close
            .rolling(200)
            .mean()
        )

        # ==================================
        # FILTRO MERCADO
        # ==================================

        if (
            spy_close.iloc[-1]
            < spy_sma200.iloc[-1]
        ):

            return pd.DataFrame()

        idx_return = (
            spy_close
            .pct_change(126)
            .iloc[-1]
        )

    except:

        return pd.DataFrame()

    # ======================================
    # LOOP
    # ======================================

    for ticker in tickers:

        try:

            df = clean_df(
                data[ticker]
            )

            if len(df) < 200:
                continue

            # ==================================
            # VOLUMEN
            # ==================================

            if (
                df["Volume"]
                .iloc[-1]
                < MIN_VOLUME
            ):
                continue

            close = df["Close"]

            current = close.iloc[-1]

            sma50 = (
                close
                .rolling(50)
                .mean()
                .iloc[-1]
            )

            sma200 = (
                close
                .rolling(200)
                .mean()
                .iloc[-1]
            )

            # ==================================
            # TENDENCIA
            # ==================================

            if not (
                current > sma50 > sma200
            ):
                continue

            # ==================================
            # MOMENTUM
            # ==================================

            momentum = (
                close
                .pct_change(126)
                .iloc[-1]
            )

            rs = momentum - idx_return

            # ==================================
            # VOLATILIDAD
            # ==================================

            volatility = (

                close
                .pct_change()
                .rolling(63)
                .std()
                .iloc[-1]

            )

            # ==================================
            # BREAKOUT
            # ==================================

            max_prev = (
                df["High"]
                .iloc[-6:-1]
                .max()
            )

            if current <= max_prev:
                continue

            # ==================================
            # ATR
            # ==================================

            atr = calcular_atr(df).iloc[-1]

            stop = (
                current -
                ATR_STOP * atr
            )

            target = (
                current +
                ATR_TARGET * atr
            )

            rr = (
                target - current
            ) / (
                current - stop
            )

            trend = current / sma200

            resultados.append({

                "Ticker": ticker,

                "Momentum": round(
                    momentum,
                    3
                ),

                "RS": round(
                    rs,
                    3
                ),

                "Trend": round(
                    trend,
                    3
                ),

                "Volatility": round(
                    volatility,
                    3
                ),

                "Entrada": round(
                    current,
                    2
                ),

                "Stop": round(
                    stop,
                    2
                ),

                "Target": round(
                    target,
                    2
                ),

                "RR": round(
                    rr,
                    2
                )

            })

        except:

            continue

    df = pd.DataFrame(resultados)

    if df.empty:
        return df

    # ======================================
    # SCORE
    # ======================================

    df["Momentum_rank"] = (
        df["Momentum"]
        .rank(pct=True)
    )

    df["RS_rank"] = (
        df["RS"]
        .rank(pct=True)
    )

    df["Trend_rank"] = (
        df["Trend"]
        .rank(pct=True)
    )

    df["Vol_rank"] = 1 - (
        df["Volatility"]
        .rank(pct=True)
    )

    df["Score"] = (

        0.35 * df["Momentum_rank"] +
        0.30 * df["RS_rank"] +
        0.25 * df["Trend_rank"] +
        0.10 * df["Vol_rank"]

    )

    final = df.sort_values(
        "Score",
        ascending=False
    )

    return final.head(5)
