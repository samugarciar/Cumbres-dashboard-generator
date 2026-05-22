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
import datetime


@st.dialog("Confirmar Citas")
def show_confirm_dialog(full_df):
    st.markdown(
        """
        <style>
        .confirm-subtitle {
            color: rgba(224, 224, 255, 0.6);
            font-size: 0.88rem;
            margin-bottom: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<p class="confirm-subtitle">Selecciona el día de las citas que deseas verificar y confirmar para enviar al workflow de n8n.</p>', unsafe_allow_html=True)
    
    # Intentar extraer las fechas de las citas
    if "Fecha" in full_df.columns:
        try:
            fechas_disponibles = pd.to_datetime(full_df["Fecha"]).dt.date.unique()
            fechas_disponibles = sorted(list(fechas_disponibles))
            min_val = fechas_disponibles[0] if fechas_disponibles else datetime.date.today()
            max_val = fechas_disponibles[-1] if fechas_disponibles else datetime.date.today()
        except Exception:
            min_val = datetime.date.today() - datetime.timedelta(days=365)
            max_val = datetime.date.today() + datetime.timedelta(days=365)
    else:
        min_val = datetime.date.today()
        max_val = datetime.date.today()
        
    selected_date = st.date_input(
        "Fecha de citas a confirmar",
        value=datetime.date.today(),
        min_value=min_val,
        max_value=max_val,
        key="confirm_date_picker"
    )
    
    # Filtrar citas de esa fecha
    citas_dia = pd.DataFrame()
    if "Fecha" in full_df.columns:
        citas_dia = full_df[pd.to_datetime(full_df["Fecha"]).dt.date == selected_date]
        
    if not citas_dia.empty:
        st.success(f"🔍 Encontradas **{len(citas_dia)}** citas para el **{selected_date.strftime('%d/%m/%Y')}**.")
        # Mostrar resumen interactivo y limpio
        cols_to_show = [c for c in ["Hora", "Inmueble", "Asesor", "Tercero", "Telefono"] if c in citas_dia.columns]
        resumen_df = citas_dia[cols_to_show].copy()
        if "Tercero" in resumen_df.columns:
            resumen_df = resumen_df.rename(columns={"Tercero": "Cliente"})
        if "Telefono" in resumen_df.columns:
            resumen_df = resumen_df.rename(columns={"Telefono": "Teléfono"})
            
        st.dataframe(resumen_df.fillna(""), use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ No hay citas registradas en los datos para el **{selected_date.strftime('%d/%m/%Y')}**.")
        
    st.markdown("---")
    
    # Obtener el webhook de los secretos o de un input fallback
    webhook_url = st.secrets.get("n8n_webhook_url", "")
    if not webhook_url:
        st.info("ℹ️ Define `n8n_webhook_url` en tus secretos de Streamlit para automatizar esto en producción. Mientras tanto, puedes ingresarlo aquí:")
        webhook_url = st.text_input("URL del Webhook de n8n", placeholder="https://tu-n8n.com/webhook/...", key="confirm_webhook_fallback")
        
    # Deshabilitar si no hay citas en la fecha elegida
    btn_disabled = citas_dia.empty or not webhook_url
    
    if st.button("🚀 Confirmar y Enviar a n8n", type="primary", use_container_width=True, disabled=btn_disabled):
        if not webhook_url:
            st.error("Por favor proporciona una URL de webhook válida.")
            return
            
        with st.spinner("⏳ Enviando confirmación al workflow de n8n..."):
            try:
                import requests
                # Convertir fechas/horas a strings para el JSON
                citas_json = citas_dia.copy()
                for col in citas_json.columns:
                    if pd.api.types.is_datetime64_any_dtype(citas_json[col]):
                        citas_json[col] = citas_json[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                payload = {
                    "fecha_confirmacion": selected_date.isoformat(),
                    "total_citas": len(citas_dia),
                    "citas": citas_json.fillna("").to_dict(orient="records")
                }
                
                response = requests.post(webhook_url, json=payload, timeout=15)
                if response.status_code in [200, 201]:
                    st.toast("✅ Citas enviadas a n8n con éxito.")
                    st.success("🎉 ¡El webhook de confirmación se envió correctamente!")
                    st.rerun()
                else:
                    st.error(f"❌ Error de n8n (Código {response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"❌ Error de conexión al enviar el webhook: {e}")


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
    active_ds_key = f"active_ds_id_{config['format_id']}"
    st.session_state[active_ds_key] = entry["id"]
    
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
            active_ds_key = f"active_ds_id_{config['format_id']}"
            st.session_state[active_ds_key] = entry["id"]
            
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

# ── Panel de Acciones Rápidas (Solo para Citas Inmobiliarias) ──────
if fmt.id == "citas_inmobiliarias":
    col_text, col_btn = st.columns([3, 1])
    with col_text:
        st.markdown(
            """
            <div style="background: rgba(24, 255, 255, 0.05); border: 1px solid rgba(24, 255, 255, 0.15); padding: 14px 20px; border-radius: 12px; height: 100%; display: flex; align-items: center;">
                <div>
                    <span style="color:#18ffff; font-weight:700; font-size: 1.05rem; display:block;">⚡ Acciones de Gestión</span>
                    <span style="color:rgba(224, 224, 255, 0.65); font-size:0.85rem; margin-top: 4px; display: block;">
                        Verifica y confirma el estado de las citas programadas para cualquier día enviándolas directamente a n8n.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_btn:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("🔔 Confirmar Citas", type="primary", use_container_width=True, key="btn_confirmar_citas_trigger"):
            show_confirm_dialog(df)
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

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
