from database.db_manager import (
    create_tables,
    save_setup,
    get_all_setups
)

# ==========================================
# CREAR TABLAS
# ==========================================

create_tables()

# ==========================================
# FEATURES TEST
# ==========================================

features = {

    "relative_volume": 2.5,
    "gap_percent": 1.8,
    "distance_vwap": 0.7,
    "ema_alignment": 1,
    "atr_ratio": 1.4,
    "above_vwap": 1

}

# ==========================================
# GUARDAR SETUP
# ==========================================

save_setup(

    ticker="NVDA",

    strategy="ORB",

    timeframe="5m",

    technical_score=88,

    ai_score=None,

    features=features,

    entry_price=1210,

    stop_loss=1198,

    take_profit=1235

)

# ==========================================
# LEER DATOS
# ==========================================

rows = get_all_setups()

print("\nSETUPS EN BD:\n")

for row in rows:

    print(row)