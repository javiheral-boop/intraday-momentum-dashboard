# ==========================================
# app.py
# ==========================================

import streamlit as st
import pandas as pd

from scanner_intraday import scan_intraday
from scanner_swing import scan_swing

# ==========================================
# CONFIG PAGE
# ==========================================

st.set_page_config(

    page_title="Momentum Trading Dashboard",
    layout="wide"

)

# ==========================================
# STYLE
# ==========================================

st.markdown("""

<style>

.main {
    background-color: #0e1117;
}

h1, h2, h3 {
    color: white;
}

div[data-testid="stDataFrame"] {
    border-radius: 10px;
}

</style>

""", unsafe_allow_html=True)

# ==========================================
# TITLE
# ==========================================

st.title("🚀 Momentum Trading Dashboard V2")

st.markdown("""
Sistema avanzado de detección de:

- Swing pre-breakout
- Momentum expansion
- Pullback continuation
- Intradía momentum
""")

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

with intraday_tab:

    st.header("⚡ Scanner Intradía")

    st.markdown("""
Detecta:

- Pre breakouts
- Momentum intradía
- Continuaciones fuertes
- Volumen anómalo
""")

    with st.spinner("Escaneando mercado intradía..."):

        intraday = scan_intraday()

    if intraday.empty:

        st.warning(
            "⚠️ No hay setups intradía actualmente"
        )

    else:

        st.success(
            f"🔥 {len(intraday)} setups encontrados"
        )

        # ==================================
        # MOMENTUM EXPANSION
        # ==================================

        momentum_df = intraday[
            intraday["Estado"] ==
            "🔥 MOMENTUM EXPANSION"
        ]

        if not momentum_df.empty:

            st.subheader(
                "🔥 MOMENTUM EXPANSION"
            )

            st.info(
                "Operativa: entrar únicamente "
                "si rompe máximo intradía "
                "con volumen fuerte."
            )

            st.dataframe(

                momentum_df.head(5),

                use_container_width=True

            )

        # ==================================
        # PRE BREAKOUT
        # ==================================

        breakout_df = intraday[
            intraday["Estado"] ==
            "🟢 PRE BREAKOUT"
        ]

        if not breakout_df.empty:

            st.subheader(
                "🟢 PRE BREAKOUT"
            )

            st.info(
                "Operativa: colocar BUY STOP "
                "ligeramente por encima "
                "del trigger."
            )

            st.dataframe(

                breakout_df.head(5),

                use_container_width=True

            )

        # ==================================
        # CONTINUATION
        # ==================================

        continuation_df = intraday[
            intraday["Estado"] ==
            "🟡 CONTINUATION"
        ]

        if not continuation_df.empty:

            st.subheader(
                "🟡 CONTINUATION"
            )

            st.info(
                "Operativa: esperar pullback "
                "controlado antes de entrar."
            )

            st.dataframe(

                continuation_df.head(5),

                use_container_width=True

            )

# ==========================================
# SWING
# ==========================================

with swing_tab:

    st.header("📈 Scanner Swing")

    st.markdown("""
Detecta:

- Early breakouts
- Pullback continuation
- Momentum expansion
- Base building
""")

    with st.spinner("Escaneando mercado swing..."):

        swing = scan_swing()

    if swing.empty:

        st.warning(
            "⚠️ No hay setups swing actualmente"
        )

    else:

        st.success(
            f"🚀 {len(swing)} setups encontrados"
        )

        # ==================================
        # EARLY BREAKOUT
        # ==================================

        early_df = swing[
            swing["Setup"] ==
            "EARLY BREAKOUT"
        ]

        if not early_df.empty:

            st.subheader(
                "🟢 EARLY BREAKOUT"
            )

            st.info(
                "Operativa: colocar BUY STOP "
                "antes de ruptura."
            )

            st.dataframe(

                early_df.head(3)[[

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

        # ==================================
        # PULLBACK CONTINUATION
        # ==================================

        pullback_df = swing[
            swing["Setup"] ==
            "PULLBACK CONTINUATION"
        ]

        if not pullback_df.empty:

            st.subheader(
                "🟡 PULLBACK CONTINUATION"
            )

            st.info(
                "Operativa: reinvertir "
                "en rebote sobre soporte."
            )

            st.dataframe(

                pullback_df.head(3)[[

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

        # ==================================
        # MOMENTUM EXPANSION
        # ==================================

        momentum_swing_df = swing[
            swing["Setup"] ==
            "MOMENTUM EXPANSION"
        ]

        if not momentum_swing_df.empty:

            st.subheader(
                "🔥 MOMENTUM EXPANSION"
            )

            st.info(
                "Operativa: seguir momentum "
                "solo con volumen fuerte."
            )

            st.dataframe(

                momentum_swing_df.head(3)[[

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

        # ==================================
        # BASE BUILDING
        # ==================================

        base_df = swing[
            swing["Setup"] ==
            "BASE BUILDING"
        ]

        if not base_df.empty:

            st.subheader(
                "🔵 BASE BUILDING"
            )

            st.info(
                "Operativa: vigilar "
                "consolidación y ruptura."
            )

            st.dataframe(

                base_df.head(3)[[

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

# ==========================================
# FOOTER
# ==========================================

st.markdown("---")

st.caption(
    "Dashboard Momentum Trading V2 | "
    "Pre-breakout + Momentum + RR"
)
