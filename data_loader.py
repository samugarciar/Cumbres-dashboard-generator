"""
data_loader.py
--------------
Módulo de carga de datos desde Google Sheets.
Utiliza gspread con autenticación via Service Account para
descargar la hoja de cálculo y convertirla en un DataFrame de Pandas.
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st


# Scopes requeridos para lectura de Google Sheets
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


@st.cache_data(ttl=600, show_spinner="Cargando datos desde Google Sheets…")
def load_data(sheet_url_or_id: str, worksheet_name: str = "Hoja 1") -> pd.DataFrame:
    """Descarga los datos de una hoja de Google Sheets y los retorna
    como un DataFrame con la columna ``Fecha`` en formato datetime.

    Parameters
    ----------
    sheet_url_or_id : str
        URL completa del Google Sheet **o** su ID.
    worksheet_name : str
        Nombre exacto de la pestaña dentro del libro.

    Returns
    -------
    pd.DataFrame
        DataFrame con todas las filas de la hoja.
    """

    # ── Autenticación ──
    creds_info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_info, scopes=_SCOPES)
    client = gspread.authorize(credentials)

    # ── Apertura de la hoja ──
    # Soporta tanto URL completa como ID directo
    if sheet_url_or_id.startswith("http"):
        spreadsheet = client.open_by_url(sheet_url_or_id)
    else:
        spreadsheet = client.open_by_key(sheet_url_or_id)

    worksheet = spreadsheet.worksheet(worksheet_name)

    # ── Conversión a DataFrame ──
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    # ── Parseo de fechas ──
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True)

    return df
