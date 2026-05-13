import pandas as pd
import os

FILE = "data/closed_positions.csv"

# ==========================================
# LOAD
# ==========================================
def load_closed_positions():

    if not os.path.exists(FILE):

        return pd.DataFrame(columns=[

            "Ticker",
            "Buy",
            "Sell",
            "Shares",
            "PnL"

        ])

    return pd.read_csv(FILE)

# ==========================================
# SAVE
# ==========================================
def save_closed_positions(df):

    df.to_csv(FILE, index=False)

# ==========================================
# ADD
# ==========================================
def add_closed_trade(

    ticker,
    buy,
    sell,
    shares,
    pnl

):

    df = load_closed_positions()

    new = pd.DataFrame([{

        "Ticker": ticker,
        "Buy": buy,
        "Sell": sell,
        "Shares": shares,
        "PnL": round(pnl,2)

    }])

    df = pd.concat([df, new])

    save_closed_positions(df)