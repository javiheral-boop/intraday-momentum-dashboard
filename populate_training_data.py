import random

from database.db_manager import (
    save_setup
)

for i in range(50):

    features = {

        "relative_volume": round(
            random.uniform(1, 5), 2
        ),

        "gap_percent": round(
            random.uniform(-2, 5), 2
        ),

        "distance_vwap": round(
            random.uniform(-3, 3), 2
        ),

        "ema_alignment": random.randint(0, 1),

        "atr_ratio": round(
            random.uniform(0.5, 3), 2
        ),

        "above_vwap": random.randint(0, 1),

        "distance_from_high": round(
            random.uniform(0, 5), 2
        ),

        "hour_of_day": random.randint(9, 16),

        "spy_trend": random.randint(0, 1)

    }

    result = random.uniform(-2, 5)

    save_setup(

        ticker="TEST",

        strategy="ORB",

        timeframe="5m",

        technical_score=random.randint(50, 100),

        features=features,

        entry_price=100,

        stop_loss=98,

        take_profit=105

    )