import yfinance as yf
import pandas as pd

WATCHLIST = [

    "NVDA","META","AAPL",
    "MSFT","AMZN","TSLA",
    "ASML","SAP","MC.PA"

]

# ==========================================
# MAIN
# ==========================================
def scan_swing():

    resultados = []

    for ticker in WATCHLIST:

        try:

            df = yf.download(
                ticker,
                period="1y",
                progress=False
            )

            if len(df) < 200:
                continue

            close = df["Close"]

            sma50 = close.rolling(50).mean()
            sma200 = close.rolling(200).mean()

            momentum = (
                close.iloc[-1]
                / close.iloc[-126]
            ) - 1

            if not (
                close.iloc[-1]
                > sma50.iloc[-1]
                > sma200.iloc[-1]
            ):
                continue

            score = (
                momentum * 100
            )

            precio = close.iloc[-1]

            atr = (
                df["High"] - df["Low"]
            ).rolling(14).mean().iloc[-1]

            stop = precio - atr * 2

            target = precio + atr * 3

            resultados.append({

                "Ticker": ticker,
                "Score": round(score,2),
                "Entrada": round(precio,2),
                "Stop": round(stop,2),
                "Target": round(target,2)

            })

        except:
            continue

    final = pd.DataFrame(resultados)

    if final.empty:
        return final

    return final.sort_values(
        "Score",
        ascending=False
    ).head(2)