import yfinance as yf
import pandas as pd

# ==========================================
# CONFIG
# ==========================================
INTERVAL = "1m"
PERIOD = "1d"

MIN_CHANGE = 0.008
VOL_MULTIPLIER = 1.5

WATCHLIST = [

    "NVDA",
    "TSLA",
    "AMD",
    "PLTR",
    "META",
    "AAPL",
    "MSFT",
    "AMZN",
    "NFLX"

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
# DESCARGA
# ==========================================
def descargar(ticker):

    try:

        df = yf.download(
            ticker,
            interval=INTERVAL,
            period=PERIOD,
            progress=False
        )

        return clean_df(df)

    except:

        return pd.DataFrame()

# ==========================================
# DETECTAR LIDER
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

        return True

    except:

        return False

# ==========================================
# SETUPS
# ==========================================
def detectar_setup(df):

    try:

        if len(df) < 30:
            return None

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

        # STOP
        stop = max(
            orb_low,
            precio * 0.98
        )

        risk = precio - stop

        if risk <= 0:
            return None

        target = precio + (
            risk * 2
        )

        return {

            "entrada": round(precio, 2),

            "stop": round(stop, 2),

            "target": round(target, 2)

        }

    except:

        return None

# ==========================================
# MAIN SCAN
# ==========================================
def scan_market():

    resultados = []

    for ticker in WATCHLIST:

        try:

            df = descargar(ticker)

            if df.empty:
                continue

            if not es_lider(df):
                continue

            setup = detectar_setup(df)

            if setup is None:
                continue

            resultados.append({

                "Ticker": ticker,

                "Entrada": setup["entrada"],

                "Stop": setup["stop"],

                "Target": setup["target"]

            })

        except:

            continue

    return pd.DataFrame(resultados)