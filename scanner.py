import streamlit as st
import pandas as pd

from streamlit_autorefresh import st_autorefresh

from scanner_intraday import scan_intraday
from scanner_swing import scan_swing

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
# TITLE
# ==========================================

st.title(
    "🚀 Momentum Trading Dashboard V2"
)

# ==========================================
# TABS
# ==========================================

intraday_tab, swing_tab = st.tabs([
    "⚡ Intradía",
    "📈 Swing"
])

# ==========================================
# INTRADAY
# ==========================================

        st.dataframe(
            intraday,
            use_container_width=True
        )

# ==========================================
# SWING
# ==========================================

with swing_tab:

    st.header("📈 Swing Trading")

    with st.spinner("Analizando setups..."):

        swing = scan_swing()

    if swing.empty:

        st.warning(
            "⚠️ No hay setups swing"
        )

    else:

        setups = [

            "EARLY BREAKOUT",
            "PULLBACK CONTINUATION",
            "MOMENTUM EXPANSION",
            "BASE BUILDING"

        ]

        for setup in setups:

            df_setup = swing[
                swing["Setup"] == setup
            ].head(3)

            if df_setup.empty:
                continue

            st.subheader(f"📌 {setup}")

            operativa = df_setup[
                "Operativa"
            ].iloc[0]

            st.info(operativa)

            st.dataframe(
                df_setup[[

                    "Ticker",
                    "Precio Actual",

                    "Entrada Trigger USD",
                    "Target USD",
                    "Stop USD",

                    "Entrada Trigger EUR",
                    "Target EUR",
                    "Stop EUR",

                    "RR",
                    "Score",
                    "Rel Volume",
                    "Momentum 20D",
                    "Distance Breakout %",
                    "Extension %"

                ]],

                use_container_width=True

            )
