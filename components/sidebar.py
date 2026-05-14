"""
sidebar.py
----------
Lógica completa del sidebar: selección de origen, formato (con gestión),
dataset, agrupación y filtros de fecha.
"""

import datetime
from typing import Dict

import streamlit as st

from formats import get_all_formats, reload_formats
import data_manager
import format_manager as fm


def render_sidebar() -> Dict:
    """Renderiza el sidebar completo y retorna un diccionario de configuración.

    Claves especiales del diccionario retornado:
        mode : "dashboard" | "create_format" | "edit_format"
            Determina qué renderiza el área principal.
    """

    config: Dict = {}

    with st.sidebar:
        # ── Origen ──────────────────────────────────────────────
        st.markdown("### Origen de Datos")
        source_label = st.radio(
            "Selecciona el origen",
            options=["Archivo Local", "Google Sheets"],
            index=0,
            horizontal=True,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Formato ─────────────────────────────────────────────
        st.markdown("### Formato")

        # Recargar formatos para capturar cambios recientes
        reload_formats()
        all_formats = get_all_formats()

        # Construir opciones: formatos existentes + "Crear nuevo"
        format_labels = {
            f"{fmt.icon}  {fmt.name}": fid for fid, fmt in all_formats.items()
        }
        format_labels["＋  Crear nuevo formato"] = "__create__"

        selected_label = st.selectbox(
            "Formato de datos",
            options=list(format_labels.keys()),
            label_visibility="collapsed",
        )
        selected_id = format_labels[selected_label]

        # Si eligió "Crear nuevo", retornar modo especial
        if selected_id == "__create__":
            config["mode"] = "create_format"
            return config

        format_id = selected_id
        active_format = all_formats[format_id]

        # Info del formato + botones de gestión para formatos custom
        with st.expander("Columnas esperadas", expanded=False):
            for col_name, spec in active_format.columns.items():
                marker = "●" if spec.required else "○"
                st.caption(f"{marker}  `{col_name}` — {spec.type}")

        # Mostrar editar/eliminar solo para formatos custom
        if format_id.startswith("custom_"):
            edit_col, del_col = st.columns(2)
            with edit_col:
                if st.button("Editar", use_container_width=True, key="edit_fmt"):
                    config["mode"] = "edit_format"
                    config["edit_format_id"] = format_id
                    return config
            with del_col:
                if st.button("Eliminar", use_container_width=True, key="del_fmt"):
                    fm.delete_custom_format(format_id)
                    reload_formats()
                    st.rerun()

        st.markdown("---")

        # ── Controles según origen ──────────────────────────────
        if source_label == "Google Sheets":
            st.markdown("### Google Sheets")
            sheet_url = st.text_input(
                "URL del Google Sheet",
                placeholder="https://docs.google.com/spreadsheets/d/...",
            )
            worksheet_name = st.text_input(
                "Nombre de la pestana", value="Hoja 1"
            )
            config["source"] = "sheets"
            config["sheet_url"] = sheet_url
            config["worksheet_name"] = worksheet_name

        else:
            st.markdown("### Dataset Local")
            datasets = data_manager.list_datasets(format_id)

            if datasets:
                ds_options = {d["name"]: d["id"] for d in datasets}
                ds_options["── Subir nuevo archivo ──"] = "__new__"
                selected_ds = st.selectbox(
                    "Dataset guardado",
                    options=list(ds_options.keys()),
                )
                selected_ds_id = ds_options[selected_ds]
            else:
                selected_ds_id = "__new__"
                st.info("No hay datasets guardados para este formato.")

            if selected_ds_id == "__new__":
                # Determinar si primera fila es header
                first_row_header = getattr(active_format, "first_row_header", True)

                uploaded_file = st.file_uploader(
                    "Subir archivo",
                    type=["xlsx", "xls", "csv"],
                    help="Excel (.xlsx) o CSV (.csv)",
                )

                if not first_row_header:
                    st.caption("⚠ Este formato espera que la primera fila NO sea encabezado.")

                dataset_name_input = st.text_input(
                    "Nombre del dataset",
                    placeholder="Ej: Citas Mayo 2026",
                )
                config["source"] = "upload_new"
                config["uploaded_file"] = uploaded_file
                config["dataset_name"] = dataset_name_input
                config["first_row_header"] = first_row_header
            else:
                config["source"] = "local"
                config["dataset_id"] = selected_ds_id

                ds_meta = data_manager.get_dataset(selected_ds_id)
                if ds_meta:
                    st.caption(
                        f"Filas: {ds_meta['row_count']}  ·  "
                        f"Actualizado: {ds_meta['updated_at'][:10]}"
                    )

                with st.expander("Actualizar dataset"):
                    update_file = st.file_uploader(
                        "Nuevo archivo",
                        type=["xlsx", "xls", "csv"],
                        key="update_uploader",
                    )
                    config["update_file"] = update_file

                if st.button("Eliminar dataset", type="secondary"):
                    data_manager.delete_dataset(selected_ds_id)
                    st.rerun()

        st.markdown("---")

        # ── Agrupación ──────────────────────────────────────────
        st.markdown("### Agrupacion")
        grouping = st.selectbox(
            "Agrupar por",
            options=active_format.grouping_options,
        )

        st.markdown("---")

        # ── Rango de fechas ─────────────────────────────────────
        st.markdown("### Rango de Fechas")
        today = datetime.date.today()
        first_of_month = today.replace(day=1)
        date_start = st.date_input("Fecha de Inicio", value=first_of_month)
        date_end = st.date_input("Fecha de Fin", value=today)

        if date_start > date_end:
            st.error(
                "La Fecha de Inicio no puede ser posterior a la Fecha de Fin."
            )

    # ── Consolidar config ───────────────────────────────────────
    config["mode"] = "dashboard"
    config["format_id"] = format_id
    config["active_format"] = active_format
    config["grouping"] = grouping
    config["date_start"] = date_start
    config["date_end"] = date_end

    return config
