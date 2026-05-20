import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# CONFIG
# ==========================================

MIN_VOLUME = 300000

ATR_STOP = 1.8
ATR_TARGET = 3.5

USD_EUR = 0.92

# ==========================================
# WATCHLIST EUROPA
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

        return [
            "AAPL","MSFT","NVDA",
            "AMZN","GOOGL","META"
        ]

# ==========================================
# UNIVERSO
# ==========================================

def get_universe():

    usa = get_sp500_tickers()

    growth = [

        "NVDA","SMCI","PLTR","COHR",
        "ADI","AVGO","MRVL","MU",
        "ARM","TSLA","META","AAPL",
        "MSFT","AMZN","GOOGL",
        "CRWD","PANW","SNOW",
        "NET","DDOG","SHOP",
        "MSTR","COIN","RKLB",
        "SOUN","IONQ","AI"

    ]

    return list(set(
        usa[:250] + growth + WATCHLIST_EUROPE
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
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    return tr.rolling(periodo).mean()

# ==========================================
# SETUP DETECTOR
# ==========================================


            setup = "BASE BUILDING"

            action_text = (
                "🔵 Vigilar consolidación"
                " y ruptura"
            )

        eur_trigger = round(
            breakout_trigger * USD_EUR,
            2
        )

        eur_target = round(
            target_price * USD_EUR,
            2
        )

        eur_stop = round(
            stop_price * USD_EUR,
            2
        )

        return {

            "Ticker": ticker,
            "Setup": setup,
            "Operativa": action_text,

            "Precio Actual": round(current_price, 2),

            "Entrada Trigger USD": breakout_trigger,
            "Target USD": target_price,
            "Stop USD": stop_price,

            "Entrada Trigger EUR": eur_trigger,
            "Target EUR": eur_target,
            "Stop EUR": eur_stop,

            "RR": round(rr, 2),
            "Score": int(score),

            "Momentum 20D": round(momentum_20 * 100, 2),
            "Rel Volume": round(rel_volume, 2),
            "Distance Breakout %": round(distance_breakout * 100, 2),
            "Extension %": round(extension * 100, 2)

        }

    except:

        return None

# ==========================================
# MAIN
# ==========================================

@st.cache_data(ttl=120)
def scan_swing():

    resultados = []

    tickers = get_universe()

    try:

        data = yf.download(

            tickers=tickers,
            period="1y",
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False

        )

    except:

        return pd.DataFrame()

    for ticker in tickers:

        try:

            df = data[ticker].copy()

            result = detectar_setup(df, ticker)

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

    return df_final
