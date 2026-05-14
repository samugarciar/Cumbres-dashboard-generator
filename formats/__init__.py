"""
formats — Auto-descubrimiento de formatos de datos.

Carga formatos de dos fuentes:
1. Clases Python en este paquete (plugins de código).
2. Definiciones JSON creadas por el usuario desde la UI.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Optional

from .base_format import BaseFormat

_FORMATS_REGISTRY: Dict[str, BaseFormat] = {}


def _discover_code_formats() -> None:
    """Escanea el paquete en busca de subclases de BaseFormat."""

    package_dir = Path(__file__).parent
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        if module_name.startswith("_") or module_name in ("base_format", "custom_format"):
            continue
        module = importlib.import_module(f".{module_name}", package=__name__)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseFormat)
                and attr is not BaseFormat
                and getattr(attr, "id", "")
            ):
                _FORMATS_REGISTRY[attr.id] = attr()


def _load_custom_formats() -> None:
    """Carga formatos personalizados desde el JSON del format_manager."""

    # Importación tardía para evitar dependencia circular
    from format_manager import list_custom_formats
    from .custom_format import CustomFormat

    for definition in list_custom_formats():
        try:
            fmt = CustomFormat(definition)
            _FORMATS_REGISTRY[fmt.id] = fmt
        except Exception:
            pass  # Definición corrupta — ignorar


def reload_formats() -> None:
    """Recarga todos los formatos (código + custom). Llamar después de crear/editar/eliminar."""

    _FORMATS_REGISTRY.clear()
    _discover_code_formats()
    _load_custom_formats()


# ── Carga inicial ───────────────────────────────────────────────
_discover_code_formats()
_load_custom_formats()


# ── API pública ─────────────────────────────────────────────────


def get_all_formats() -> Dict[str, BaseFormat]:
    """Retorna el diccionario ``{format_id: instancia}``."""
    return _FORMATS_REGISTRY


def get_format(format_id: str) -> Optional[BaseFormat]:
    """Retorna un formato por su ID, o ``None``."""
    return _FORMATS_REGISTRY.get(format_id)


def detect_format_from_df(df) -> Optional[BaseFormat]:
    """Intenta detectar el formato de un DataFrame por sus columnas."""

    best_match: Optional[BaseFormat] = None
    best_score = 0

    for fmt in _FORMATS_REGISTRY.values():
        valid, _ = fmt.validate(df)
        if not valid:
            continue
        score = sum(1 for c in fmt.columns if c in df.columns)
        if score > best_score:
            best_score = score
            best_match = fmt

    return best_match
