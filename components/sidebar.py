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
        # ── Formato ─────────────────────────────────────────────
        st.markdown("### Formato de Datos")

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

        # ── Explorador Unificado de Conexiones / Datasets ────────
        st.markdown("### Explorador de Datasets")
        
        # Listar datasets y conexiones existentes para este formato
        datasets = data_manager.list_datasets(format_id)
        
        ds_options = {}
        for d in datasets:
            if d.get("source") == "sheets":
                label = f"🏠 {d['name']} (Google Sheet)"
            else:
                label = f"📂 {d['name']} (Archivo Local)"
            ds_options[label] = d["id"]
            
        ds_options["＋ Conectar Google Sheet..."] = "__new_sheet__"
        ds_options["＋ Subir archivo local..."] = "__new_local__"
        
        # Clave en session state para persistir la selección del dataset
        sb_key = f"sb_dataset_{format_id}"
        
        # Encontrar el índice por defecto
        options_list = list(ds_options.keys())
        default_index = 0
        if sb_key in st.session_state and st.session_state[sb_key] in options_list:
            default_index = options_list.index(st.session_state[sb_key])
            
        selected_ds_label = st.selectbox(
            "Conexión o Dataset",
            options=options_list,
            index=default_index,
            key=sb_key,
            label_visibility="collapsed",
        )
        selected_ds_id = ds_options[selected_ds_label]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ── Renderizar opciones según selección ──────────────────
        if selected_ds_id == "__new_sheet__":
            st.markdown("#### 🔌 Conectar Google Sheet")
            sheet_url = st.text_input(
                "URL del Google Sheet",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                key="new_sheet_url"
            )
            worksheet_name = st.text_input(
                "Nombre de la pestaña",
                value="Hoja 1",
                key="new_worksheet_name"
            )
            connection_name = st.text_input(
                "Nombre de la conexión",
                placeholder="Ej: Citas Cumbres Activas",
                key="new_connection_name"
            )
            config["source"] = "sheets_new"
            config["sheet_url"] = sheet_url
            config["worksheet_name"] = worksheet_name
            config["connection_name"] = connection_name
            
        elif selected_ds_id == "__new_local__":
            st.markdown("#### 📂 Subir archivo local")
            first_row_header = getattr(active_format, "first_row_header", True)
            uploaded_file = st.file_uploader(
                "Subir archivo",
                type=["xlsx", "xls", "csv"],
                help="Excel (.xlsx) o CSV (.csv)",
                key="new_local_uploader"
            )
            if not first_row_header:
                st.caption("⚠ Este formato espera que la primera fila NO sea encabezado.")
                
            dataset_name_input = st.text_input(
                "Nombre del dataset",
                placeholder="Ej: Citas Mayo 2026",
                key="new_local_name"
            )
            config["source"] = "upload_new"
            config["uploaded_file"] = uploaded_file
            config["dataset_name"] = dataset_name_input
            config["first_row_header"] = first_row_header
            
        else:
            # Cargar metadata de la conexión/dataset existente
            ds_meta = data_manager.get_dataset(selected_ds_id)
            if ds_meta:
                if ds_meta.get("source") == "sheets":
                    config["source"] = "sheets_saved"
                    config["dataset_id"] = selected_ds_id
                    config["sheet_url"] = ds_meta["sheet_url"]
                    config["worksheet_name"] = ds_meta["worksheet_name"]
                    config["connection_name"] = ds_meta["name"]
                    
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                            <span style="color:#b388ff; font-weight:600; font-size: 0.85rem; display:block; margin-bottom:4px;">🔌 Google Sheet Conectado</span>
                            <span style="color:rgba(224,224,255,0.7); font-size:0.8rem; display:block;">Pestaña: <b>{ds_meta['worksheet_name']}</b></span>
                            <span style="color:rgba(224,224,255,0.7); font-size:0.8rem; display:block;">Filas: <b>{ds_meta['row_count']}</b></span>
                            <span style="color:rgba(224,224,255,0.4); font-size:0.75rem; display:block; margin-top:6px;">Última sinc: <br>{ds_meta['updated_at'].replace('T', ' ')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    if st.button("🗑 Eliminar conexión", type="secondary", use_container_width=True, key="del_sheet_conn"):
                        data_manager.delete_dataset(selected_ds_id)
                        # Limpiar session state para no mantener selección inexistente
                        if sb_key in st.session_state:
                            del st.session_state[sb_key]
                        st.rerun()
                else:
                    config["source"] = "local"
                    config["dataset_id"] = selected_ds_id
                    config["dataset_name"] = ds_meta["name"]
                    
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                            <span style="color:#82b1ff; font-weight:600; font-size: 0.85rem; display:block; margin-bottom:4px;">📂 Dataset Local</span>
                            <span style="color:rgba(224,224,255,0.7); font-size:0.8rem; display:block;">Filas: <b>{ds_meta['row_count']}</b></span>
                            <span style="color:rgba(224,224,255,0.4); font-size:0.75rem; display:block; margin-top:6px;">Actualizado: <br>{ds_meta['updated_at'].replace('T', ' ')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    with st.expander("Actualizar dataset"):
                        update_file = st.file_uploader(
                            "Subir nuevo archivo",
                            type=["xlsx", "xls", "csv"],
                            key="update_uploader",
                        )
                        config["update_file"] = update_file
                        
                    if st.button("🗑 Eliminar dataset", type="secondary", use_container_width=True, key="del_local_ds"):
                        data_manager.delete_dataset(selected_ds_id)
                        if sb_key in st.session_state:
                            del st.session_state[sb_key]
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
