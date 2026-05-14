"""
data_manager.py
---------------
Gestión de datasets locales: upload, persistencia en Parquet y registro
en un archivo JSON central (``data/registry.json``).
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

DATA_DIR = Path("data")
DATASETS_DIR = DATA_DIR / "datasets"
REGISTRY_FILE = DATA_DIR / "registry.json"


# ── Helpers internos ────────────────────────────────────────────


def _ensure_dirs() -> None:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_FILE.exists():
        REGISTRY_FILE.write_text("[]", encoding="utf-8")


def _load_registry() -> List[Dict]:
    _ensure_dirs()
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def _save_registry(registry: List[Dict]) -> None:
    _ensure_dirs()
    REGISTRY_FILE.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── API pública ─────────────────────────────────────────────────


def list_datasets(format_id: Optional[str] = None) -> List[Dict]:
    """Lista datasets registrados, opcionalmente filtrados por formato."""

    registry = _load_registry()
    if format_id:
        registry = [d for d in registry if d["format"] == format_id]
    return registry


def get_dataset(dataset_id: str) -> Optional[Dict]:
    """Retorna la metadata de un dataset por su ID."""

    for d in _load_registry():
        if d["id"] == dataset_id:
            return d
    return None


def load_dataset_df(dataset_id: str) -> Optional[pd.DataFrame]:
    """Lee el Parquet de un dataset y lo retorna como DataFrame."""

    ds = get_dataset(dataset_id)
    if ds is None:
        return None
    return pd.read_parquet(ds["file_path"])


def save_dataset(
    df: pd.DataFrame,
    name: str,
    format_id: str,
    original_filename: str,
    dataset_id: Optional[str] = None,
) -> Dict:
    """Guarda un DataFrame como dataset nuevo o actualiza uno existente.

    Parameters
    ----------
    df : pd.DataFrame
        Datos ya validados y preparados.
    name : str
        Nombre descriptivo del dataset.
    format_id : str
        ID del formato al que pertenece.
    original_filename : str
        Nombre del archivo original subido.
    dataset_id : str, optional
        Si se proporciona, actualiza el dataset existente.

    Returns
    -------
    dict
        Entrada del registro (nueva o actualizada).
    """

    _ensure_dirs()
    registry = _load_registry()
    now = datetime.now().isoformat(timespec="seconds")

    if dataset_id:
        # ── Actualizar existente ──
        entry = None
        for d in registry:
            if d["id"] == dataset_id:
                entry = d
                break
        if entry is None:
            raise ValueError(f"Dataset '{dataset_id}' no encontrado.")

        df.to_parquet(entry["file_path"], index=False)
        entry["updated_at"] = now
        entry["row_count"] = len(df)
        entry["original_filename"] = original_filename
    else:
        # ── Crear nuevo ──
        dataset_id = uuid.uuid4().hex[:8]
        safe_name = (
            "".join(c if c.isalnum() or c in "-_ " else "" for c in name)
            .strip()
            .replace(" ", "_")
            .lower()
        )
        file_path = str(DATASETS_DIR / f"{dataset_id}_{safe_name}.parquet")
        df.to_parquet(file_path, index=False)

        entry = {
            "id": dataset_id,
            "name": name,
            "format": format_id,
            "source": "upload",
            "original_filename": original_filename,
            "uploaded_at": now,
            "updated_at": now,
            "row_count": len(df),
            "file_path": file_path,
        }
        registry.append(entry)

    _save_registry(registry)
    return entry


def delete_dataset(dataset_id: str) -> bool:
    """Elimina un dataset (archivo Parquet y entrada del registro)."""

    registry = _load_registry()
    new_registry = []
    deleted = False

    for d in registry:
        if d["id"] == dataset_id:
            try:
                os.remove(d["file_path"])
            except FileNotFoundError:
                pass
            deleted = True
        else:
            new_registry.append(d)

    _save_registry(new_registry)
    return deleted
