import sqlite3
import json
from datetime import datetime


DATABASE_NAME = "database/trades.db"


def get_connection():

    return sqlite3.connect(DATABASE_NAME)


def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS setups (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        created_at TEXT,

        ticker TEXT,

        strategy TEXT,

        timeframe TEXT,

        technical_score REAL,

        ai_score REAL,

        entry_price REAL,

        stop_loss REAL,

        take_profit REAL,

        status TEXT,

        result REAL,

        features_json TEXT

    )

    """)

    conn.commit()

    conn.close()

    print("✅ Tabla setups creada correctamente")


def save_setup(
    ticker,
    strategy,
    timeframe,
    technical_score,
    features,
    ai_score=None,
    entry_price=None,
    stop_loss=None,
    take_profit=None
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO setups (

        created_at,
        ticker,
        strategy,
        timeframe,
        technical_score,
        ai_score,
        entry_price,
        stop_loss,
        take_profit,
        status,
        result,
        features_json

    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        datetime.utcnow().isoformat(),

        ticker,

        strategy,

        timeframe,

        technical_score,

        ai_score,

        entry_price,

        stop_loss,

        take_profit,

        "OPEN",

        None,

        json.dumps(features)

    ))

    conn.commit()

    conn.close()

    print(f"✅ Setup guardado: {ticker}")


def get_all_setups():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT * FROM setups

    """)

    rows = cursor.fetchall()

    conn.close()

    return rows