import pandas as pd
import os

# ==========================================
# PATHS
# ==========================================

DATA_DIR = "data"

OPEN_FILE = os.path.join(
    DATA_DIR,
    "open_positions.csv"
)

# ==========================================
# CREAR CARPETA
# ==========================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

# ==========================================
# LOAD
# ==========================================

def load_open_positions():

    if not os.path.exists(OPEN_FILE):

        return pd.DataFrame(columns=[

            "Ticker",
            "Buy",
            "Stop",
            "Target",
            "Shares"

        ])

    return pd.read_csv(OPEN_FILE)

# ==========================================
# SAVE
# ==========================================

def save_open_positions(df):

    df.to_csv(
        OPEN_FILE,
        index=False
    )

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

        "Ticker": ticker.upper(),
        "Buy": buy,
        "Stop": stop,
        "Target": target,
        "Shares": shares

    }])

    df = pd.concat(
        [df, new],
        ignore_index=True
    )

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

        ticker=ticker,
        buy=row["Buy"],
        sell=sell_price,
        shares=row["Shares"],
        pnl=pnl

    )

    df = df[
        df["Ticker"] != ticker
    ]

    save_open_positions(df)
