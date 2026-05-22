"""
custom_format.py
----------------
Formato dinámico que se construye a partir de una definición JSON
creada por el usuario desde la UI, en lugar de estar hardcodeado.
"""

from typing import Any, Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .base_format import BaseFormat, ColumnSpec, KPI

# ── Constantes visuales ─────────────────────────────────────────
_COLORS = [
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

# ── Mapa de tipo legible → tipo interno ─────────────────────────
TYPE_MAP = {
    "Texto": "string",
    "Fecha": "datetime",
    "Numero": "number",
    "string": "string",
    "datetime": "datetime",
    "number": "number",
}


class CustomFormat(BaseFormat):
    """Formato construido dinámicamente desde un diccionario de definición.

    Estructura esperada de ``definition``::

        {
            "id": "custom_abc123",
            "name": "Mi Formato",
            "icon": "📊",
            "first_row_header": true,
            "columns": [
                {"name": "Fecha", "type": "Fecha", "required": true},
                {"name": "Cliente", "type": "Texto", "required": true},
                ...
            ],
            "date_column": "Fecha",
            "grouping_options": ["Cliente", "Estado"],
            "kpis": [
                {"type": "count", "label": "Total Registros"},
                {"type": "unique", "column": "Cliente", "label": "Clientes Unicos"},
                {"type": "sum",    "column": "Monto",   "label": "Monto Total"},
                {"type": "avg",    "column": "Monto",   "label": "Monto Promedio"},
            ]
        }
    """

    def __init__(self, definition: Dict[str, Any]):
        self._def = definition
        self.id = definition["id"]
        self.name = definition.get("name", "Sin nombre")
        self.description = definition.get("description", "")
        self.icon = definition.get("icon", "📄")
        self.first_row_header = definition.get("first_row_header", True)
        self.date_column = definition.get("date_column", "")
        self.grouping_options = definition.get("grouping_options", [])
        self._kpi_defs = definition.get("kpis", [])

        # Construir columns dict
        self.columns = {}
        for col in definition.get("columns", []):
            internal_type = TYPE_MAP.get(col["type"], "string")
            self.columns[col["name"]] = ColumnSpec(
                type=internal_type, required=col.get("required", False)
            )

    # ── KPIs ────────────────────────────────────────────────────

    def compute_kpis(self, df: pd.DataFrame) -> List[KPI]:
        results: List[KPI] = []

        for kdef in self._kpi_defs:
            ktype = kdef.get("type", "count")
            label = kdef.get("label", ktype)
            col = kdef.get("column", "")

            if ktype == "count":
                results.append(KPI(label=label, value=len(df)))

            elif ktype == "unique" and col in df.columns:
                results.append(KPI(label=label, value=df[col].nunique()))

            elif ktype == "sum" and col in df.columns:
                val = pd.to_numeric(df[col], errors="coerce").sum()
                results.append(KPI(label=label, value=round(val, 2)))

            elif ktype == "avg" and col in df.columns:
                val = pd.to_numeric(df[col], errors="coerce").mean()
                fmt = "{:,.2f}"
                results.append(KPI(label=label, value=round(val, 2), format=fmt))

        # Fallback: si no se definieron KPIs, mostrar conteo
        if not results:
            results.append(KPI(label="Total Registros", value=len(df)))

        return results

    # ── Gráficos ────────────────────────────────────────────────

    def build_charts(
        self, df: pd.DataFrame, grouping: str
    ) -> List[Tuple[str, go.Figure]]:
        group_counts = (
            df.groupby(grouping)
            .size()
            .reset_index(name="Total")
            .sort_values("Total", ascending=False)
        )

        # Donut — ocultar etiquetas de segmentos pequeños (< 5%)
        total = group_counts["Total"].sum()
        pcts = group_counts["Total"] / total if total > 0 else group_counts["Total"]
        text_positions = ["outside" if p >= 0.05 else "none" for p in pcts]

        fig_donut = px.pie(
            group_counts,
            names=grouping,
            values="Total",
            hole=0.55,
            color_discrete_sequence=_COLORS,
        )
        fig_donut.update_traces(
            textinfo="percent+label",
            textposition=text_positions,
            textfont=dict(color="rgba(224,224,255,0.8)", size=12),
            marker=dict(line=dict(color="#0f0c29", width=2)),
            hovertemplate=(
                "<b>%{label}</b><br>Total: %{value}"
                "<br>%{percent}<extra></extra>"
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
            group_counts.sort_values("Total", ascending=True),
            x="Total",
            y=grouping,
            orientation="h",
            color="Total",
            color_continuous_scale=["#304ffe", "#7c4dff", "#18ffff"],
        )
        fig_bar.update_traces(
            marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>Total: %{x}<extra></extra>",
        )
        fig_bar.update_layout(
            title=dict(
                text=f"Total por {grouping}",
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
