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
        """Limpia y prepara el DataFrame (parseo robusto de fechas, eliminación de filas vacías, etc.).

        Se ejecuta después de la validación.
        """

        # ── 1. Eliminar filas completamente vacías o con solo espacios ──
        df = df.replace(r'^\s*$', pd.NA, regex=True)
        df = df.dropna(how="all").copy()

        # ── 1.5. Normalizar todas las columnas tipo string a minúsculas y limpiarlas ──
        for col_name, spec in self.columns.items():
            if spec.type == "string" and col_name in df.columns:
                df[col_name] = df[col_name].fillna("").astype(str).str.strip().str.lower()

        # ── 2. Parseo robusto de fechas ──
        if self.date_column and self.date_column in df.columns:
            # Si ya es datetime, no lo re-parseamos
            if not pd.api.types.is_datetime64_any_dtype(df[self.date_column]):
                # Convertir a texto limpio en minúsculas
                date_series = df[self.date_column].astype(str).str.strip().str.lower()

                # Mapa de meses en español
                month_map = {
                    "ene": "01", "feb": "02", "mar": "03", "abr": "04",
                    "may": "05", "jun": "06", "jul": "07", "ago": "08",
                    "sep": "09", "set": "09", "oct": "10", "nov": "11", "dic": "12"
                }

                # Reemplazar abreviaciones de mes por separador y número de mes
                # Esto maneja casos como '20may' -> '20/05/', '21/may' -> '21//05/'
                for month, num in month_map.items():
                    date_series = date_series.str.replace(month, f"/{num}/", regex=False)

                # Unificar múltiples barras diagonales, espacios y guiones en una sola barra
                date_series = date_series.str.replace(r'[\s/-]+', '/', regex=True)
                # Limpiar barras al inicio y al final
                date_series = date_series.str.strip('/')

                # Si falta el año (formatos DD/MM o D/M), agregar el año actual
                current_year = pd.Timestamp.today().year
                no_year_mask = date_series.str.match(r"^\d{1,2}/\d{1,2}$")
                date_series = date_series.where(
                    ~no_year_mask, date_series + f"/{current_year}"
                )

                # Convertir final
                df[self.date_column] = pd.to_datetime(
                    date_series, errors="coerce", dayfirst=True
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
