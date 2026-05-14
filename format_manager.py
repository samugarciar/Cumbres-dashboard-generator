"""
format_manager.py
-----------------
CRUD para definiciones de formatos personalizados creados desde la UI.
Se almacenan en ``data/custom_formats.json``.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path("data")
CUSTOM_FORMATS_FILE = DATA_DIR / "custom_formats.json"


def _ensure_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CUSTOM_FORMATS_FILE.exists():
        CUSTOM_FORMATS_FILE.write_text("[]", encoding="utf-8")


def _load_all() -> List[Dict]:
    _ensure_file()
    return json.loads(CUSTOM_FORMATS_FILE.read_text(encoding="utf-8"))


def _save_all(definitions: List[Dict]) -> None:
    _ensure_file()
    CUSTOM_FORMATS_FILE.write_text(
        json.dumps(definitions, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def list_custom_formats() -> List[Dict]:
    """Retorna todas las definiciones de formatos personalizados."""
    return _load_all()


def get_custom_format(format_id: str) -> Optional[Dict]:
    """Retorna una definición por su ID."""
    for d in _load_all():
        if d["id"] == format_id:
            return d
    return None


def save_custom_format(definition: Dict) -> Dict:
    """Crea o actualiza una definición de formato.

    Si ``definition`` no tiene ``"id"``, se genera uno nuevo.
    Si ya tiene ``"id"``, se actualiza la entrada existente.
    """

    definitions = _load_all()

    if "id" not in definition or not definition["id"]:
        definition["id"] = f"custom_{uuid.uuid4().hex[:8]}"
        definitions.append(definition)
    else:
        found = False
        for i, d in enumerate(definitions):
            if d["id"] == definition["id"]:
                definitions[i] = definition
                found = True
                break
        if not found:
            definitions.append(definition)

    _save_all(definitions)
    return definition


def delete_custom_format(format_id: str) -> bool:
    """Elimina un formato personalizado por su ID."""

    definitions = _load_all()
    new_defs = [d for d in definitions if d["id"] != format_id]
    deleted = len(new_defs) < len(definitions)
    _save_all(new_defs)
    return deleted
