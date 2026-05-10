import streamlit as st
import pandas as pd

# ======================================
# CONFIG PAGINA
# ======================================
st.set_page_config(
    page_title="Intraday Momentum Dashboard",
    layout="wide"
)

# ======================================
# TITULO
# ======================================
st.title("🚀 Intraday Momentum Dashboard")

# ======================================
# ESTADO MERCADO
# ======================================
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="🇺🇸 Mercado USA",
        value="BULLISH"
    )

with col2:
    st.metric(
        label="🇪🇺 Mercado Europa",
        value="LATERAL"
    )

# ======================================
# SETUPS
# ======================================
st.subheader("🔥 Setups Activos")

data = pd.DataFrame({

    "Ticker": ["NVDA", "PLTR", "AMD"],

    "Entrada": [921, 28.4, 181],

    "Stop": [912, 27.9, 178],

    "Target": [939, 29.8, 187]

})

st.dataframe(
    data,
    use_container_width=True
)

# ======================================
# CARTERA
# ======================================
st.subheader("💰 Cartera")

portfolio = pd.DataFrame({

    "Ticker": ["NVDA", "TSLA"],

    "PnL %": [2.3, -0.8]

})

st.dataframe(
    portfolio,
    use_container_width=True
)