import sqlite3
import json
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

import joblib


DATABASE_NAME = "database/trades.db"


# ==========================================
# CONECTAR DB
# ==========================================

conn = sqlite3.connect(DATABASE_NAME)

query = """

SELECT
    features_json,
    result

FROM setups

WHERE result IS NOT NULL

"""

df = pd.read_sql(query, conn)

conn.close()

# ==========================================
# VALIDAR DATOS
# ==========================================

if len(df) < 10:

    raise ValueError(
        "Necesitas más datos históricos"
    )

# ==========================================
# PARSEAR FEATURES JSON
# ==========================================

features_list = []

for _, row in df.iterrows():

    features = json.loads(
        row["features_json"]
    )

    features["target"] = int(
        row["result"] > 0
    )

    features_list.append(features)

# ==========================================
# DATAFRAME FINAL
# ==========================================

dataset = pd.DataFrame(features_list)

# ==========================================
# FEATURES / TARGET
# ==========================================

X = dataset.drop(columns=["target"])

y = dataset["target"]

# ==========================================
# TRAIN TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.2,

    shuffle=False

)

# ==========================================
# MODELO XGBOOST
# ==========================================

model = XGBClassifier(

    n_estimators=100,

    max_depth=4,

    learning_rate=0.05,

    random_state=42

)

# ==========================================
# ENTRENAR
# ==========================================

model.fit(X_train, y_train)

# ==========================================
# PREDICCIONES
# ==========================================

predictions = model.predict(X_test)

# ==========================================
# MÉTRICAS
# ==========================================

print("\nRESULTADOS MODELO:\n")

print(

    classification_report(
        y_test,
        predictions
    )

)

# ==========================================
# GUARDAR MODELO
# ==========================================

joblib.dump(
    model,
    "models/xgboost_model.pkl"
)

print("\n✅ Modelo guardado correctamente")