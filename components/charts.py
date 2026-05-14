"""
charts.py
---------
Renderizado de gráficos Plotly dentro de contenedores glass.
"""

from typing import List, Tuple

import plotly.graph_objects as go
import streamlit as st


def render_charts(chart_pairs: List[Tuple[str, go.Figure]]) -> None:
    """Renderiza gráficos en un layout de dos columnas.

    Parameters
    ----------
    chart_pairs : list of (position, figure)
        ``position`` es ``"left"`` o ``"right"``.
    """

    left_charts = [fig for pos, fig in chart_pairs if pos == "left"]
    right_charts = [fig for pos, fig in chart_pairs if pos == "right"]

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        for fig in left_charts:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        for fig in right_charts:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
