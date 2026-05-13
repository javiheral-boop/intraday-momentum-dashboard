import pandas as pd
import os

# ==========================================
# PATHS
# ==========================================

DATA_DIR = "data"

CLOSED_FILE = os.path.join(
    DATA_DIR,
    "closed_positions.csv"
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

def load_closed_positions():

    if not os.path.exists(CLOSED_FILE):

        return pd.DataFrame(columns=[

            "Ticker",
            "Buy",
            "Sell",
            "Shares",
            "PnL"

        ])

    return pd.read_csv(CLOSED_FILE)

# ==========================================
# SAVE
# ==========================================

def save_closed_positions(df):

    df.to_csv(
        CLOSED_FILE,
        index=False
    )

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
        "PnL": round(pnl, 2)

    }])

    df = pd.concat(
        [df, new],
        ignore_index=True
    )

    save_closed_positions(df)
