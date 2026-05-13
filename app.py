import streamlit as st
import pandas as pd

from scanner_intraday import scan_intraday
from scanner_swing import scan_swing

from portfolio import (
    load_open_positions,
    add_position,
    close_position
)

from journal import (
    load_closed_positions
)

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(
    page_title="Momentum Trading Dashboard",
    layout="wide"
)

st.title("🚀 Momentum Trading Dashboard")

# ==========================================
# TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([

    "⚡ Intradía",
    "📈 Swing",
    "💼 Posiciones Abiertas",
    "📊 P&L"

])

# ==========================================
# TAB 1 - INTRADIA
# ==========================================
with tab1:

    st.header("⚡ Recomendaciones Intradía")

    if st.button("🔄 Escanear Intradía"):

        with st.spinner("Escaneando mercado intradía..."):

            df_intraday = scan_intraday()

        st.success(f"Setups encontrados: {len(df_intraday)}")

        st.dataframe(
            df_intraday,
            use_container_width=True
        )

# ==========================================
# TAB 2 - SWING
# ==========================================
with tab2:

    st.header("📈 Recomendaciones Swing")

    if st.button("🔄 Escanear Swing"):

        with st.spinner("Buscando oportunidades swing..."):

            df_swing = scan_swing()

        st.success(f"Top oportunidades: {len(df_swing)}")

        st.dataframe(
            df_swing,
            use_container_width=True
        )

# ==========================================
# TAB 3 - POSICIONES ABIERTAS
# ==========================================
with tab3:

    st.header("💼 Gestión de Posiciones")

    with st.form("new_position"):

        ticker = st.text_input("Ticker")
        buy_price = st.number_input("Precio Compra")
        stop = st.number_input("Stop Loss")
        target = st.number_input("Target")
        shares = st.number_input("Acciones", step=1)

        submit = st.form_submit_button("➕ Añadir Posición")

        if submit:

            add_position(
                ticker,
                buy_price,
                stop,
                target,
                shares
            )

            st.success("Posición añadida")

    st.subheader("📋 Posiciones Abiertas")

    open_df = load_open_positions()

    st.dataframe(
        open_df,
        use_container_width=True
    )

    # ======================================
    # CERRAR POSICION
    # ======================================
    st.subheader("❌ Cerrar Posición")

    if not open_df.empty:

        selected = st.selectbox(
            "Seleccionar ticker",
            open_df["Ticker"]
        )

        sell_price = st.number_input(
            "Precio Venta"
        )

        close_btn = st.button(
            "Cerrar Trade"
        )

        if close_btn:

            close_position(
                selected,
                sell_price
            )

            st.success(
                "Trade cerrado"
            )

# ==========================================
# TAB 4 - PNL
# ==========================================
with tab4:

    st.header("📊 Histórico y P&L")

    closed_df = load_closed_positions()

    if not closed_df.empty:

        total_pnl = closed_df["PnL"].sum()

        wins = closed_df[
            closed_df["PnL"] > 0
        ]

        losses = closed_df[
            closed_df["PnL"] <= 0
        ]

        winrate = (
            len(wins)
            / len(closed_df)
        ) * 100

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "💰 P&L Total",
            round(total_pnl, 2)
        )

        col2.metric(
            "🎯 Win Rate",
            f"{round(winrate,2)}%"
        )

        col3.metric(
            "📈 Trades",
            len(closed_df)
        )

        st.dataframe(
            closed_df,
            use_container_width=True
        )

    else:

        st.info("No hay trades cerrados")
