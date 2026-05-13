import pandas as pd
import os

FILE = "data/open_positions.csv"

# ==========================================
# LOAD
# ==========================================
def load_open_positions():

    if not os.path.exists(FILE):

        return pd.DataFrame(columns=[

            "Ticker",
            "Buy",
            "Stop",
            "Target",
            "Shares"

        ])

    return pd.read_csv(FILE)

# ==========================================
# SAVE
# ==========================================
def save_open_positions(df):

    df.to_csv(FILE, index=False)

# ==========================================
# ADD
# ==========================================
def add_position(

    ticker,
    buy,
    stop,
    target,
    shares

):

    df = load_open_positions()

    new = pd.DataFrame([{

        "Ticker": ticker,
        "Buy": buy,
        "Stop": stop,
        "Target": target,
        "Shares": shares

    }])

    df = pd.concat([df, new])

    save_open_positions(df)

# ==========================================
# CLOSE
# ==========================================
def close_position(

    ticker,
    sell_price

):

    from journal import add_closed_trade

    df = load_open_positions()

    row = df[
        df["Ticker"] == ticker
    ].iloc[0]

    pnl = (
        sell_price - row["Buy"]
    ) * row["Shares"]

    add_closed_trade(

        ticker,
        row["Buy"],
        sell_price,
        row["Shares"],
        pnl

    )

    df = df[
        df["Ticker"] != ticker
    ]

    save_open_positions(df)
