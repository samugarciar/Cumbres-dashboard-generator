"""
citas_inmobiliarias.py
----------------------
Formato: Citas Inmobiliarias.
Columnas: Fecha, Hora, Dia, Tercero, Telefono, Inmueble, Asesor, Telefono Asesor.
"""

from typing import List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .base_format import BaseFormat, ColumnSpec, KPI

# ── Paleta premium ──────────────────────────────────────────────
COLOR_SEQUENCE = [
    "#7c4dff", "#448aff", "#18ffff", "#b388ff", "#82b1ff",
    "#80d8ff", "#6200ea", "#304ffe", "#00b8d4", "#aa00ff",
    "#2979ff", "#00e5ff", "#651fff", "#0091ea", "#00bfa5",
]

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="rgba(224,224,255,0.7)", family="Inter"),
    margin=dict(t=60, b=20, l=20, r=20),
    height=420,
)


class CitasInmobiliarias(BaseFormat):
    id = "citas_inmobiliarias"
    name = "Citas Inmobiliarias"
    description = "Seguimiento de citas de propiedad por inmueble y asesor"
    icon = "🏠"
    date_column = "Fecha"
    grouping_options = ["Inmueble", "Asesor"]

    columns = {
        "Fecha":           ColumnSpec(type="datetime", required=True),
        "Hora":            ColumnSpec(type="string",   required=False),
        "Dia":             ColumnSpec(type="string",   required=False),
        "Tercero":         ColumnSpec(type="string",   required=False),
        "Telefono":        ColumnSpec(type="string",   required=False),
        "Inmueble":        ColumnSpec(type="string",   required=True),
        "Asesor":          ColumnSpec(type="string",   required=True),
        "Telefono Asesor": ColumnSpec(type="string",   required=False),
    }

    # ── KPIs ────────────────────────────────────────────────────

    def compute_kpis(self, df: pd.DataFrame) -> List[KPI]:
        return [
            KPI(label="Total de Citas",      value=len(df)),
            KPI(label="Propiedades Unicas",  value=df["Inmueble"].nunique()),
            KPI(label="Asesores Activos",    value=df["Asesor"].nunique()),
        ]

    # ── Gráficos ────────────────────────────────────────────────

    def build_charts(
        self, df: pd.DataFrame, grouping: str
    ) -> List[Tuple[str, go.Figure]]:
        group_counts = (
            df.groupby(grouping)
            .size()
            .reset_index(name="Citas")
            .sort_values("Citas", ascending=False)
        )

        # Donut
        fig_donut = px.pie(
            group_counts,
            names=grouping,
            values="Citas",
            hole=0.55,
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        fig_donut.update_traces(
            textinfo="percent+label",
            textposition="outside",
            textfont=dict(color="rgba(224,224,255,0.8)", size=12),
            marker=dict(line=dict(color="#0f0c29", width=2)),
            hovertemplate=(
                "<b>%{label}</b><br>Citas: %{value}"
                "<br>Porcentaje: %{percent}<extra></extra>"
            ),
        )
        fig_donut.update_layout(
            title=dict(
                text=f"Distribucion por {grouping}",
                font=dict(color="#b388ff", size=16, family="Inter"),
                x=0.5,
            ),
            showlegend=False,
            **_LAYOUT,
        )

        # Barras horizontales
        fig_bar = px.bar(
            group_counts.sort_values("Citas", ascending=True),
            x="Citas",
            y=grouping,
            orientation="h",
            color="Citas",
            color_continuous_scale=["#304ffe", "#7c4dff", "#18ffff"],
        )
        fig_bar.update_traces(
            marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>Citas: %{x}<extra></extra>",
        )
        fig_bar.update_layout(
            title=dict(
                text=f"Citas por {grouping}",
                font=dict(color="#b388ff", size=16, family="Inter"),
                x=0.5,
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                title="",
            ),
            yaxis=dict(showgrid=False, title="", tickfont=dict(size=12)),
            coloraxis_showscale=False,
            **_LAYOUT,
        )

        return [("left", fig_donut), ("right", fig_bar)]
