"""
base_format.py
--------------
Clase abstracta que define el contrato para todos los formatos de datos.
Cada formato nuevo hereda de BaseFormat e implementa sus métodos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import pandas as pd
import plotly.graph_objects as go


@dataclass
class KPI:
    """Representa un indicador clave para renderizar en el dashboard."""

    label: str
    value: Any
    format: str = "{:,}"


@dataclass
class ColumnSpec:
    """Especificación de una columna esperada en el dataset."""

    type: str  # "datetime", "string", "number"
    required: bool = True


class BaseFormat(ABC):
    """Clase base abstracta para formatos de datos.

    Atributos de clase que cada subclase debe definir:
        id:               Identificador único (ej. ``"citas_inmobiliarias"``).
        name:             Nombre para mostrar en el sidebar.
        description:      Descripción breve del formato.
        icon:             Emoji representativo.
        columns:          Dict de ``{nombre_columna: ColumnSpec}``.
        date_column:      Nombre de la columna de fecha para filtros.
        grouping_options: Lista de columnas válidas para agrupar.
    """

    id: str = ""
    name: str = ""
    description: str = ""
    icon: str = ""
    columns: Dict[str, ColumnSpec] = {}
    date_column: str = ""
    grouping_options: List[str] = []

    # ── Validación ──────────────────────────────────────────────

    def validate(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Verifica que el DataFrame contenga las columnas requeridas."""

        errors: List[str] = []
        for col_name, spec in self.columns.items():
            if spec.required and col_name not in df.columns:
                errors.append(f"Columna requerida faltante: '{col_name}'")
        return (len(errors) == 0, errors)

    # ── Preparación ─────────────────────────────────────────────

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y prepara el DataFrame (parseo de fechas, etc.).

        Se ejecuta *después* de la validación.  Si la columna de fecha ya
        tiene dtype datetime, no la reparsea.
        """

        if self.date_column and self.date_column in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[self.date_column]):
                df[self.date_column] = pd.to_datetime(
                    df[self.date_column], errors="coerce", dayfirst=True
                )
        return df

    # ── Métodos abstractos ──────────────────────────────────────

    @abstractmethod
    def compute_kpis(self, df: pd.DataFrame) -> List[KPI]:
        """Retorna la lista de KPIs a renderizar."""
        ...

    @abstractmethod
    def build_charts(
        self, df: pd.DataFrame, grouping: str
    ) -> List[Tuple[str, go.Figure]]:
        """Retorna lista de ``(posición, figura_plotly)``.

        ``posición`` es ``"left"`` o ``"right"`` para el layout de 2 columnas.
        """
        ...
