import streamlit as st
from scanner import scan_market

# ======================================
# CONFIG
# ======================================
st.set_page_config(
    page_title="Momentum Dashboard",
    layout="wide"
)

# ======================================
# TITULO
# ======================================
st.title("🚀 Intraday Momentum Dashboard")

# ======================================
# BOTON REFRESH
# ======================================
if st.button("🔄 Escanear Mercado"):

    with st.spinner("Escaneando mercado..."):

        df = scan_market()

    st.success(
        f"Setups encontrados: {len(df)}"
    )

    st.dataframe(
        df,
        use_container_width=True
    )
