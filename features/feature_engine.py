import pandas as pd
import numpy as np

from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator
from ta.volume import VolumeWeightedAveragePrice


def normalize_column(data):

    """
    Convierte cualquier columna en Series 1D
    """

    # Si ya es Series
    if isinstance(data, pd.Series):
        return data

    # Si es DataFrame de una sola columna
    if isinstance(data, pd.DataFrame):
        return data.iloc[:, 0]

    # Si es ndarray
    return pd.Series(data).squeeze()


def extract_features(df, market_df=None):

    """
    Extrae features para IA desde dataframe OHLCV
    """

    df = df.copy()

    # ==========================================
    # LIMPIAR MULTIINDEX
    # ==========================================

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # ==========================================
    # VALIDACIONES
    # ==========================================

    required_cols = ["Open", "High", "Low", "Close", "Volume"]

    for col in required_cols:

        if col not in df.columns:
            raise ValueError(f"Falta columna: {col}")

    # ==========================================
    # NORMALIZAR COLUMNAS
    # ==========================================

    for col in required_cols:

        df[col] = normalize_column(df[col])

    # ==========================================
    # INDICADORES
    # ==========================================

    # EMA 9
    ema9 = EMAIndicator(
        close=df["Close"],
        window=9
    )

    df["ema9"] = ema9.ema_indicator()

    # EMA 20
    ema20 = EMAIndicator(
        close=df["Close"],
        window=20
    )

    df["ema20"] = ema20.ema_indicator()

    # ATR
    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    df["atr"] = atr.average_true_range()

    # VWAP
    vwap = VolumeWeightedAveragePrice(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        volume=df["Volume"]
    )

    df["vwap"] = vwap.volume_weighted_average_price()

    # ==========================================
    # ÚLTIMA FILA
    # ==========================================

    latest = df.iloc[-1]

    # ==========================================
    # RELATIVE VOLUME
    # ==========================================

    avg_volume = (
        df["Volume"]
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    relative_volume = (
        latest["Volume"] / avg_volume
        if avg_volume > 0 else 0
    )

    # ==========================================
    # GAP %
    # ==========================================

    previous_close = df["Close"].iloc[-2]

    gap_percent = (
        (latest["Open"] - previous_close)
        / previous_close
    ) * 100

    # ==========================================
    # DISTANCIA VWAP
    # ==========================================

    distance_vwap = (
        (latest["Close"] - latest["vwap"])
        / latest["vwap"]
    ) * 100

    # ==========================================
    # EMA ALIGNMENT
    # ==========================================

    ema_alignment = int(
        latest["ema9"] > latest["ema20"]
    )

    # ==========================================
    # ATR RATIO
    # ==========================================

    candle_range = (
        latest["High"] - latest["Low"]
    )

    atr_ratio = (
        candle_range / latest["atr"]
        if latest["atr"] > 0 else 0
    )

    # ==========================================
    # ABOVE VWAP
    # ==========================================

    above_vwap = int(
        latest["Close"] > latest["vwap"]
    )

    # ==========================================
    # DISTANCIA HIGH
    # ==========================================

    rolling_high = (
        df["High"]
        .rolling(20)
        .max()
        .iloc[-1]
    )

    distance_from_high = (
        (rolling_high - latest["Close"])
        / rolling_high
    ) * 100

    # ==========================================
    # HORA DEL DÍA
    # ==========================================

    if isinstance(df.index, pd.DatetimeIndex):

        hour_of_day = latest.name.hour

    else:

        hour_of_day = 0

    # ==========================================
    # SPY TREND
    # ==========================================

    spy_trend = 0

    if market_df is not None:

        if isinstance(market_df.columns, pd.MultiIndex):
            market_df.columns = market_df.columns.get_level_values(0)

        market_close = normalize_column(
            market_df["Close"]
        )

        market_ema9 = EMAIndicator(
            close=market_close,
            window=9
        ).ema_indicator().iloc[-1]

        market_ema20 = EMAIndicator(
            close=market_close,
            window=20
        ).ema_indicator().iloc[-1]

        spy_trend = int(
            market_ema9 > market_ema20
        )

    # ==========================================
    # FEATURES FINALES
    # ==========================================

    features = {

        "relative_volume": round(relative_volume, 2),

        "gap_percent": round(gap_percent, 2),

        "distance_vwap": round(distance_vwap, 2),

        "ema_alignment": ema_alignment,

        "atr_ratio": round(atr_ratio, 2),

        "above_vwap": above_vwap,

        "distance_from_high": round(distance_from_high, 2),

        "hour_of_day": int(hour_of_day),

        "spy_trend": spy_trend
    }

    return features