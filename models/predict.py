import pandas as pd
import joblib


MODEL_PATH = "models/xgboost_model.pkl"


# ==========================================
# CARGAR MODELO
# ==========================================

model = joblib.load(MODEL_PATH)


def predict_setup(features):

    """
    Devuelve score IA para setup
    """

    # ==========================================
    # DATAFRAME
    # ==========================================

    X = pd.DataFrame([features])

    # ==========================================
    # PREDECIR PROBABILIDAD
    # ==========================================

    probability = model.predict_proba(X)[0][1]

    # ==========================================
    # SCORE %
    # ==========================================

    ai_score = round(
        probability * 100,
        2
    )

    return ai_score