"""
format_builder.py
-----------------
Constructor visual de formatos personalizados.
Permite al usuario definir columnas, tipos, KPIs y agrupaciones
directamente desde la interfaz de Streamlit.
"""

from typing import Dict, List, Optional

import streamlit as st

import format_manager

# ── Tipos disponibles ───────────────────────────────────────────
COLUMN_TYPES = ["Texto", "Fecha", "Numero"]

KPI_TYPES = {
    "Conteo (total de filas)": "count",
    "Valores unicos de una columna": "unique",
    "Suma de una columna numerica": "sum",
    "Promedio de una columna numerica": "avg",
}

ICON_OPTIONS = ["📊", "🏠", "📋", "💰", "📦", "👥", "📈", "🔧", "📞", "🗂️"]


def _init_builder_state(existing: Optional[Dict] = None) -> None:
    """Inicializa el session_state para el builder."""

    if "builder_initialized" in st.session_state:
        return

    if existing:
        st.session_state.builder_name = existing.get("name", "")
        st.session_state.builder_icon = existing.get("icon", "📊")
        st.session_state.builder_first_row = existing.get("first_row_header", True)
        st.session_state.builder_columns = existing.get("columns", [])
        st.session_state.builder_kpis = existing.get("kpis", [])
        st.session_state.builder_id = existing.get("id", "")
    else:
        st.session_state.builder_name = ""
        st.session_state.builder_icon = "📊"
        st.session_state.builder_first_row = True
        st.session_state.builder_columns = []
        st.session_state.builder_kpis = []
        st.session_state.builder_id = ""

    st.session_state.builder_initialized = True


def _clear_builder_state() -> None:
    """Limpia el estado del builder."""

    for key in list(st.session_state.keys()):
        if key.startswith("builder_"):
            del st.session_state[key]


def render_format_builder(existing: Optional[Dict] = None) -> bool:
    """Renderiza el constructor de formatos en el área principal.

    Returns
    -------
    bool
        ``True`` si el usuario guardó el formato (se hizo rerun).
    """

    _init_builder_state(existing)

    is_edit = bool(st.session_state.builder_id)
    title = "Editar Formato" if is_edit else "Crear Nuevo Formato"

    st.markdown(
        f'<p class="main-title">{title}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="main-subtitle">Define las columnas, tipos de datos y metricas para tu formato</p>',
        unsafe_allow_html=True,
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INFORMACIÓN GENERAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown("### Informacion General")

    col_name, col_icon = st.columns([3, 1])
    with col_name:
        st.session_state.builder_name = st.text_input(
            "Nombre del formato",
            value=st.session_state.builder_name,
            placeholder="Ej: Seguimiento de Leads",
        )
    with col_icon:
        icon_idx = (
            ICON_OPTIONS.index(st.session_state.builder_icon)
            if st.session_state.builder_icon in ICON_OPTIONS
            else 0
        )
        st.session_state.builder_icon = st.selectbox(
            "Icono", options=ICON_OPTIONS, index=icon_idx
        )

    st.session_state.builder_first_row = st.checkbox(
        "La primera fila del archivo contiene los encabezados (nombres de columna)",
        value=st.session_state.builder_first_row,
    )

    st.markdown("---")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # COLUMNAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown("### Columnas Esperadas")
    st.caption("Define las columnas que debe tener el archivo para este formato.")

    columns: List[Dict] = st.session_state.builder_columns

    # Renderizar columnas existentes
    to_remove = None
    for i, col in enumerate(columns):
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        with c1:
            columns[i]["name"] = st.text_input(
                "Nombre", value=col["name"], key=f"col_name_{i}",
                label_visibility="collapsed",
                placeholder="Nombre de la columna",
            )
        with c2:
            type_idx = COLUMN_TYPES.index(col["type"]) if col["type"] in COLUMN_TYPES else 0
            columns[i]["type"] = st.selectbox(
                "Tipo", options=COLUMN_TYPES, index=type_idx, key=f"col_type_{i}",
                label_visibility="collapsed",
            )
        with c3:
            columns[i]["required"] = st.checkbox(
                "Req.", value=col.get("required", True), key=f"col_req_{i}",
            )
        with c4:
            if st.button("✕", key=f"col_del_{i}", help="Eliminar columna"):
                to_remove = i

    if to_remove is not None:
        columns.pop(to_remove)
        st.session_state.builder_columns = columns
        st.rerun()

    if st.button("＋ Agregar columna", type="secondary"):
        columns.append({"name": "", "type": "Texto", "required": True})
        st.session_state.builder_columns = columns
        st.rerun()

    st.markdown("---")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CONFIGURACIÓN DE ANÁLISIS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Solo mostrar si hay columnas definidas
    col_names = [c["name"] for c in columns if c["name"].strip()]

    if col_names:
        st.markdown("### Configuracion de Analisis")

        date_cols = [c["name"] for c in columns if c["type"] == "Fecha" and c["name"].strip()]
        text_cols = [c["name"] for c in columns if c["type"] == "Texto" and c["name"].strip()]

        col_date, col_group = st.columns(2)
        with col_date:
            date_col_options = ["(ninguna)"] + date_cols
            selected_date = st.selectbox(
                "Columna de fecha (para filtros)",
                options=date_col_options,
            )
        with col_group:
            grouping_cols = st.multiselect(
                "Columnas de agrupacion (para graficos)",
                options=text_cols,
                default=[],
                help="Selecciona las columnas por las que el usuario podra agrupar los datos.",
            )

        st.markdown("---")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # KPIs
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        st.markdown("### Indicadores (KPIs)")
        st.caption("Define las metricas que se mostraran en la parte superior del dashboard.")

        kpis: List[Dict] = st.session_state.builder_kpis
        kpi_to_remove = None

        for i, kpi in enumerate(kpis):
            k1, k2, k3, k4 = st.columns([3, 2, 2, 1])
            with k1:
                kpis[i]["label"] = st.text_input(
                    "Etiqueta", value=kpi.get("label", ""), key=f"kpi_label_{i}",
                    label_visibility="collapsed",
                    placeholder="Ej: Total Registros",
                )
            with k2:
                kpi_type_labels = list(KPI_TYPES.keys())
                current_type = kpi.get("type", "count")
                # Reverse lookup
                current_label_idx = 0
                for j, (lbl, val) in enumerate(KPI_TYPES.items()):
                    if val == current_type:
                        current_label_idx = j
                        break
                selected_kpi_label = st.selectbox(
                    "Tipo", options=kpi_type_labels, index=current_label_idx,
                    key=f"kpi_type_{i}", label_visibility="collapsed",
                )
                kpis[i]["type"] = KPI_TYPES[selected_kpi_label]
            with k3:
                needs_col = kpis[i]["type"] in ("unique", "sum", "avg")
                if needs_col:
                    kpis[i]["column"] = st.selectbox(
                        "Columna", options=col_names, key=f"kpi_col_{i}",
                        label_visibility="collapsed",
                    )
                else:
                    kpis[i].pop("column", None)
                    st.write("")  # Placeholder
            with k4:
                if st.button("✕", key=f"kpi_del_{i}", help="Eliminar KPI"):
                    kpi_to_remove = i

        if kpi_to_remove is not None:
            kpis.pop(kpi_to_remove)
            st.session_state.builder_kpis = kpis
            st.rerun()

        if st.button("＋ Agregar KPI", type="secondary"):
            kpis.append({"label": "", "type": "count"})
            st.session_state.builder_kpis = kpis
            st.rerun()

        st.markdown("---")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # GUARDAR
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        st.markdown("")
        col_save, col_cancel = st.columns([1, 1])

        with col_save:
            if st.button("Guardar formato", type="primary", use_container_width=True):
                # Validaciones
                if not st.session_state.builder_name.strip():
                    st.error("El nombre del formato es obligatorio.")
                    return False
                valid_cols = [c for c in columns if c["name"].strip()]
                if len(valid_cols) < 1:
                    st.error("Agrega al menos una columna.")
                    return False
                if not grouping_cols:
                    st.error("Selecciona al menos una columna de agrupacion.")
                    return False

                definition = {
                    "id": st.session_state.builder_id or "",
                    "name": st.session_state.builder_name.strip(),
                    "icon": st.session_state.builder_icon,
                    "first_row_header": st.session_state.builder_first_row,
                    "columns": valid_cols,
                    "date_column": selected_date if selected_date != "(ninguna)" else "",
                    "grouping_options": grouping_cols,
                    "kpis": [k for k in kpis if k.get("label", "").strip()],
                }

                format_manager.save_custom_format(definition)
                _clear_builder_state()
                st.success(f"Formato '{definition['name']}' guardado correctamente.")
                st.rerun()

        with col_cancel:
            if st.button("Cancelar", use_container_width=True):
                _clear_builder_state()
                st.rerun()

    else:
        st.info("Agrega al menos una columna para continuar con la configuracion.")

    return False
