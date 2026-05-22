"""
app.py
------
Dashboard interactivo de Citas — Cumbres.
Orquestador principal: carga CSS, renderiza sidebar, procesa datos
a través del sistema de formatos y muestra KPIs + gráficos.
Soporta modo "constructor de formatos" para crear formatos desde la UI.
"""

import streamlit as st
import pandas as pd
import csv

from components.sidebar import render_sidebar
from components.kpi_cards import render_kpi_row
from components.charts import render_charts
from components.format_builder import render_format_builder
from data_loader import load_data
import data_manager
import format_manager


def read_csv_smart(file_obj, header):
    file_obj.seek(0)
    sample = file_obj.read(4096)
    if isinstance(sample, bytes):
        sample_text = sample.decode("utf-8", errors="ignore")
    else:
        sample_text = sample

    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=";,|\t")
        sep = dialect.delimiter
    except Exception:
        sep = ","

    file_obj.seek(0)
    return pd.read_csv(file_obj, header=header, sep=sep)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CONFIGURACIÓN DE PÁGINA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Cumbres — Dashboard de Citas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. CSS PREMIUM — GLASSMORPHISM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a40 40%, #24243e 100%);
    }

    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.85);
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e0ff;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 28px 24px;
        text-align: center;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(124, 77, 255, 0.18);
    }
    .glass-card .kpi-value {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #7c4dff, #448aff, #18ffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
    }
    .glass-card .kpi-label {
        font-size: 0.88rem;
        font-weight: 500;
        color: rgba(224, 224, 255, 0.55);
        text-transform: uppercase;
        letter-spacing: 1.6px;
        margin-top: 8px;
    }

    .chart-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 20px;
        margin-top: 12px;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #b388ff, #82b1ff, #80d8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 4px;
    }
    .main-subtitle {
        font-size: 0.95rem;
        color: rgba(224, 224, 255, 0.45);
        font-weight: 400;
        margin-bottom: 28px;
    }

    .streamlit-expanderHeader {
        color: #b388ff !important;
        font-weight: 600;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
config = render_sidebar()
mode = config.get("mode", "dashboard")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. MODO: CONSTRUCTOR DE FORMATOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if mode == "create_format":
    render_format_builder()
    st.stop()

if mode == "edit_format":
    edit_id = config.get("edit_format_id", "")
    existing_def = format_manager.get_custom_format(edit_id)
    render_format_builder(existing=existing_def)
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. MODO: DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
fmt = config["active_format"]

# ── Encabezado ──────────────────────────────────────────────────
st.markdown('<p class="main-title">Dashboard de Citas</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="main-subtitle">{fmt.icon} {fmt.name} &mdash; Cumbres</p>',
    unsafe_allow_html=True,
)

# ── Carga de datos ──────────────────────────────────────────────
df: pd.DataFrame | None = None
first_row_header = config.get("first_row_header", True)

if config["source"] == "sheets_new":
    if not config.get("sheet_url"):
        st.info("🔌 Ingresa la URL del Google Sheet en la barra lateral para comenzar.")
        st.stop()
        
    conn_name = config.get("connection_name") or "Google Sheet"
    st.info(f"⏳ Conectando con Google Sheets para '{conn_name}'...")
    
    try:
        raw_df = load_data(config["sheet_url"], config["worksheet_name"])
    except Exception as exc:
        st.error(f"❌ Error al conectar con Google Sheets: {exc}")
        st.stop()
        
    valid, errors = fmt.validate(raw_df)
    if not valid:
        st.error("❌ Los datos de la hoja no coinciden con el formato esperado:")
        for e in errors:
            st.error(e)
        st.stop()
        
    df = fmt.prepare(raw_df.copy())
    
    # Guardar automáticamente la conexión persistente y su caché
    entry = data_manager.save_sheets_connection(
        df,
        conn_name,
        config["format_id"],
        config["sheet_url"],
        config["worksheet_name"]
    )
    
    # Seleccionar la nueva conexión en session state para el próximo renderizado
    sb_key = f"sb_dataset_{config['format_id']}"
    st.session_state[sb_key] = f"🏠 {entry['name']} (Google Sheet)"
    
    st.success(f"✅ Conexión **{entry['name']}** guardada y cargada exitosamente.")
    st.rerun()

elif config["source"] == "sheets_saved":
    # Carga súper veloz desde caché local Parquet
    df = data_manager.load_dataset_df(config["dataset_id"])
    if df is None:
        st.error("❌ La caché local del dataset no fue encontrada.")
        st.stop()
        
    # Banner premium con información de la conexión y botón de sincronización
    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.markdown(
            f"""
            <div style="background: rgba(124, 77, 255, 0.08); border: 1px solid rgba(124, 77, 255, 0.2); padding: 14px 20px; border-radius: 12px; margin-bottom: 20px; display: flex; flex-direction: column;">
                <span style="color:#b388ff; font-weight:700; font-size: 1.05rem; display:block;">🔌 Conectado a Google Sheets: {config.get('connection_name')}</span>
                <span style="color:rgba(224, 224, 255, 0.65); font-size:0.85rem; margin-top: 4px; display: block;">
                    Cargado desde caché instantánea · Pestaña: <b>{config.get('worksheet_name')}</b> · Registros: <b>{len(df)}</b>
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_btn:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Sincronizar datos", type="primary", use_container_width=True, key="sync_sheets"):
            with st.spinner("⏳ Sincronizando en vivo desde Google Sheets..."):
                try:
                    # Limpiar la caché de load_data para garantizar la descarga fresca
                    load_data.clear()
                    fresh_df = load_data(config["sheet_url"], config["worksheet_name"])
                except Exception as exc:
                    st.error(f"❌ Error al sincronizar: {exc}")
                    st.stop()
                
                valid, errors = fmt.validate(fresh_df)
                if not valid:
                    st.error("❌ Los datos de la hoja no coinciden con el formato esperado:")
                    for e in errors:
                        st.error(e)
                    st.stop()
                
                prepared_df = fmt.prepare(fresh_df.copy())
                # Actualizar caché persistente en disco
                data_manager.save_sheets_connection(
                    prepared_df,
                    config["connection_name"],
                    config["format_id"],
                    config["sheet_url"],
                    config["worksheet_name"],
                    dataset_id=config["dataset_id"]
                )
                st.toast("✅ Sincronización finalizada con éxito.")
                st.rerun()

elif config["source"] == "upload_new":
    uploaded_file = config.get("uploaded_file")
    if not uploaded_file:
        st.info("📂 Sube un archivo en la barra lateral para comenzar.")
        st.stop()

    try:
        if uploaded_file.name.endswith(".csv"):
            header_opt = 0 if first_row_header else None
            df = read_csv_smart(uploaded_file, header_opt)
        else:
            header_opt = 0 if first_row_header else None
            df = pd.read_excel(uploaded_file, header=header_opt)

        if not first_row_header:
            expected_cols = [c["name"] for c in getattr(fmt, "_def", {}).get("columns", [])]
            if expected_cols and len(expected_cols) == len(df.columns):
                df.columns = expected_cols
            else:
                df.columns = [f"Columna_{i+1}" for i in range(len(df.columns))]
    except Exception as exc:
        st.error(f"❌ Error al leer el archivo: {exc}")
        st.stop()

    valid, errors = fmt.validate(df)
    if not valid:
        for e in errors:
            st.error(e)
        st.stop()

    df = fmt.prepare(df.copy())
    dataset_name = config.get("dataset_name") or uploaded_file.name
    st.toast(f"✅ Archivo leído: {uploaded_file.name} ({len(df)} filas)")

    save_col_left, save_col_right = st.columns([3, 1])
    with save_col_left:
        st.info(f"📂 Archivo temporal cargado. Haz clic en '💾 Guardar dataset' para registrarlo de forma permanente.")
    with save_col_right:
        if st.button("💾 Guardar dataset", type="primary", use_container_width=True):
            entry = data_manager.save_dataset(
                df, dataset_name, config["format_id"], uploaded_file.name
            )
            sb_key = f"sb_dataset_{config['format_id']}"
            st.session_state[sb_key] = f"📂 {entry['name']} (Archivo Local)"
            
            st.success(f"✅ Dataset **{dataset_name}** guardado correctamente.")
            st.rerun()

elif config["source"] == "local":
    df = data_manager.load_dataset_df(config["dataset_id"])
    if df is None:
        st.error("❌ Dataset no encontrado.")
        st.stop()

    st.markdown(
        f"""
        <div style="background: rgba(68, 138, 255, 0.08); border: 1px solid rgba(68, 138, 255, 0.2); padding: 14px 20px; border-radius: 12px; margin-bottom: 20px;">
            <span style="color:#82b1ff; font-weight:700; font-size: 1.05rem; display:block;">📂 Dataset Local Activo: {config.get('dataset_name')}</span>
            <span style="color:rgba(224, 224, 255, 0.65); font-size:0.85rem; margin-top: 4px; display: block;">
                Cargado desde disco local · Registros: <b>{len(df)}</b>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    update_file = config.get("update_file")
    if update_file:
        try:
            if update_file.name.endswith(".csv"):
                df_new = read_csv_smart(update_file, 0)
            else:
                df_new = pd.read_excel(update_file)
        except Exception as exc:
            st.error(f"❌ Error al leer el archivo de actualización: {exc}")
            df_new = None

        if df_new is not None:
            valid, errors = fmt.validate(df_new)
            if not valid:
                for e in errors:
                    st.error(e)
            else:
                df_new = fmt.prepare(df_new.copy())
                if st.button("📥 Confirmar actualización", type="primary"):
                    data_manager.save_dataset(
                        df_new, config.get('dataset_name'), config["format_id"],
                        update_file.name, dataset_id=config["dataset_id"],
                    )
                    st.success("✅ Dataset actualizado correctamente.")
                    st.rerun()

# ── Validación y preparación ────────────────────────────────────
if df is None or df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

df = fmt.prepare(df.copy())

valid, errors = fmt.validate(df)
if not valid:
    for e in errors:
        st.error(e)
    st.stop()

# ── Filtrar por fechas ──────────────────────────────────────────
date_col = fmt.date_column
if date_col and date_col in df.columns:
    mask = (df[date_col].dt.date >= config["date_start"]) & (
        df[date_col].dt.date <= config["date_end"]
    )
    df_filtered = df.loc[mask].copy()
else:
    df_filtered = df.copy()

if df_filtered.empty:
    st.warning("No hay datos para el rango de fechas seleccionado.")
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. KPIs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
kpis = fmt.compute_kpis(df_filtered)
render_kpi_row(kpis)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. GRÁFICOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
charts = fmt.build_charts(df_filtered, config["grouping"])
render_charts(charts)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. DATOS CRUDOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.expander("Ver datos crudos"):
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    st.caption(f"{len(df_filtered)} registros encontrados en el rango seleccionado.")
