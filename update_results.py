import random
import sqlite3

from database.db_manager import (
    update_result
)

conn = sqlite3.connect(
    "database/trades.db"
)

cursor = conn.cursor()

cursor.execute("""

SELECT id FROM setups

""")

rows = cursor.fetchall()

conn.close()

for row in rows:

    setup_id = row[0]

    result = round(
        random.uniform(-3, 5),
        2
    )

    update_result(
        setup_id,
        result
    )