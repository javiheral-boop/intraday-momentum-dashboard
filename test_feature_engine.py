import yfinance as yf

from features.feature_engine import extract_features


# ==========================================
# DESCARGAR DATOS
# ==========================================

df = yf.download(
    "NVDA",
    period="5d",
    interval="5m",
    auto_adjust=False,
    progress=False
)

# ==========================================
# SPY
# ==========================================

spy = yf.download(
    "SPY",
    period="5d",
    interval="5m",
    auto_adjust=False,
    progress=False
)

# ==========================================
# FEATURES
# ==========================================

features = extract_features(df, spy)

print("\nFEATURES IA:\n")

for key, value in features.items():

    print(f"{key}: {value}")