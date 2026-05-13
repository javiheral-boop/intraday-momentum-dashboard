import streamlit as st
import pandas as pd

from streamlit_autorefresh import st_autorefresh

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

# ==========================================
# AUTO REFRESH
# ==========================================

st_autorefresh(

    interval=30000,

    key="market_refresh"

)

# ==========================================
# TITULO
# ==========================================

st.title(
    "🚀 Momentum Trading Dashboard"
)

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

    st.header(
        "⚡ Recomendaciones Intradía"
    )

    # ======================================
    # SESSION STATE
    # ======================================

    if "intraday_running" not in st.session_state:

        st.session_state.intraday_running = False

    if "intraday_results" not in st.session_state:

        st.session_state.intraday_results = pd.DataFrame()

    # ======================================
    # BOTONES
    # ======================================

    col1, col2 = st.columns(2)

    # ======================================
    # START
    # ======================================

    with col1:

        if st.button(
            "▶️ Iniciar Escaneo"
        ):

            st.session_state.intraday_running = True

    # ======================================
    # STOP
    # ======================================

    with col2:

        if st.button(
            "⏹️ Detener Escaneo"
        ):

            st.session_state.intraday_running = False

    # ======================================
    # INFO
    # ======================================

    if st.session_state.intraday_running:

        st.success(
            "🟢 Scanner activo | Refresh 30s"
        )

    else:

        st.warning(
            "🔴 Scanner detenido"
        )

    # ======================================
    # ESCANEO
    # ======================================

    if st.session_state.intraday_running:

        with st.spinner(

            "Escaneando mercado..."

        ):

            df_intraday = scan_intraday()

            st.session_state.intraday_results = (
                df_intraday
            )

        if not df_intraday.empty:

            st.success(

                f"🔥 Setups encontrados: {len(df_intraday)}"

            )

        else:

            st.warning(

                "⚠️ No hay setups actualmente"

            )

    # ======================================
    # MOSTRAR RESULTADOS
    # ======================================

    if not st.session_state.intraday_results.empty:

        df_show = (
            st.session_state.intraday_results
        )

        # ==================================
        # ORDEN COLUMNAS
        # ==================================

        columnas = [

            "Ticker",

            "Hora Señal",

            "Minutos",

            "Estado",

            "Entrada",

            "Stop",

            "Target",

            "RR",

            "Cambio %",

            "Score"

        ]

        columnas_existentes = [

            c for c in columnas

            if c in df_show.columns

        ]

        df_show = df_show[
            columnas_existentes
        ]

        # ==================================
        # STYLE
        # ==================================

        def color_estado(val):

            if "FRESH" in str(val):

                return (
                    "background-color: #0d4f2f;"
                    "color: white;"
                )

            elif "ACTIVE" in str(val):

                return (
                    "background-color: #7a5c00;"
                    "color: white;"
                )

            elif "LATE" in str(val):

                return (
                    "background-color: #7a0000;"
                    "color: white;"
                )

            return ""

        # ==================================
        # TABLA
        # ==================================

        st.dataframe(

            df_show
            .style
            .map(
                color_estado,
                subset=["Estado"]
            ),

            use_container_width=True,

            hide_index=True

        )

    else:

        st.info(

            "No hay setups actualmente"

        )

# ==========================================
# TAB 2 - SWING
# ==========================================

with tab2:

    st.header(
        "📈 Recomendaciones Swing"
    )

    if st.button(
        "🔄 Escanear Swing"
    ):

        with st.spinner(

            "Buscando oportunidades swing..."

        ):

            df_swing = scan_swing()

        if not df_swing.empty:

            st.success(

                f"📈 Oportunidades encontradas: {len(df_swing)}"

            )

            st.dataframe(

                df_swing,

                use_container_width=True,

                hide_index=True

            )

        else:

            st.warning(

                "⚠️ No hay setups swing"

            )

# ==========================================
# TAB 3 - POSICIONES ABIERTAS
# ==========================================

with tab3:

    st.header(
        "💼 Gestión de Posiciones"
    )

    # ======================================
    # NUEVA POSICION
    # ======================================

    with st.form("new_position"):

        ticker = st.text_input(
            "Ticker"
        )

        buy_price = st.number_input(
            "Precio Compra",
            min_value=0.0
        )

        stop = st.number_input(
            "Stop Loss",
            min_value=0.0
        )

        target = st.number_input(
            "Target",
            min_value=0.0
        )

        shares = st.number_input(

            "Acciones",

            min_value=1,

            step=1

        )

        submit = st.form_submit_button(
            "➕ Añadir Posición"
        )

        if submit:

            add_position(

                ticker,

                buy_price,

                stop,

                target,

                shares

            )

            st.success(
                "✅ Posición añadida"
            )

    # ======================================
    # POSICIONES ABIERTAS
    # ======================================

    st.subheader(
        "📋 Posiciones Abiertas"
    )

    open_df = load_open_positions()

    if not open_df.empty:

        st.dataframe(

            open_df,

            use_container_width=True,

            hide_index=True

        )

    else:

        st.info(
            "No hay posiciones abiertas"
        )

    # ======================================
    # CERRAR POSICION
    # ======================================

    st.subheader(
        "❌ Cerrar Posición"
    )

    if not open_df.empty:

        selected = st.selectbox(

            "Seleccionar ticker",

            open_df["Ticker"]

        )

        sell_price = st.number_input(

            "Precio Venta",

            min_value=0.0

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
                "✅ Trade cerrado"
            )

# ==========================================
# TAB 4 - PNL
# ==========================================

with tab4:

    st.header(
        "📊 Histórico y P&L"
    )

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

        avg_win = (
            wins["PnL"].mean()
            if not wins.empty
            else 0
        )

        avg_loss = (
            losses["PnL"].mean()
            if not losses.empty
            else 0
        )

        # ==================================
        # METRICAS
        # ==================================

        col1, col2, col3, col4 = st.columns(4)

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

        col4.metric(

            "⚖️ Avg Trade",

            round(
                closed_df["PnL"].mean(),
                2
            )

        )

        # ==================================
        # EXTRA STATS
        # ==================================

        st.subheader(
            "📊 Estadísticas"
        )

        col5, col6 = st.columns(2)

        col5.metric(

            "🏆 Avg Win",

            round(avg_win, 2)

        )

        col6.metric(

            "💥 Avg Loss",

            round(avg_loss, 2)

        )

        # ==================================
        # TABLA
        # ==================================

        st.dataframe(

            closed_df,

            use_container_width=True,

            hide_index=True

        )

    else:

        st.info(
            "No hay trades cerrados"
        )
