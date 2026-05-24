from models.predict import predict_setup


features = {

    "relative_volume": 3.2,

    "gap_percent": 2.1,

    "distance_vwap": 0.9,

    "ema_alignment": 1,

    "atr_ratio": 1.8,

    "above_vwap": 1,

    "distance_from_high": 1.2,

    "hour_of_day": 10,

    "spy_trend": 1
}

score = predict_setup(features)

print("\nAI SCORE:\n")

print(score)