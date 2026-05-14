"""
kpi_cards.py
------------
Renderizado de tarjetas KPI con estilo glassmorphism.
"""

from typing import List

import streamlit as st

from formats.base_format import KPI


def render_kpi(value, label: str, fmt: str = "{:,}") -> None:
    """Renderiza una tarjeta KPI individual con glass-card."""

    formatted = fmt.format(value) if isinstance(value, (int, float)) else str(value)
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="kpi-value">{formatted}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(kpis: List[KPI]) -> None:
    """Renderiza una fila de KPIs en columnas equidistantes."""

    cols = st.columns(len(kpis), gap="large")
    for col, kpi in zip(cols, kpis):
        with col:
            render_kpi(kpi.value, kpi.label, kpi.format)
