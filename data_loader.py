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
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(creds_info, scopes=_SCOPES)
        client = gspread.authorize(credentials)
    except Exception as e:
        raise ValueError(
            f"No se pudieron cargar las credenciales de Google Cloud desde secrets.toml. "
            f"Detalle técnico: {e}"
        )

    # ── Apertura de la hoja ──
    try:
        if sheet_url_or_id.startswith("http"):
            spreadsheet = client.open_by_url(sheet_url_or_id)
        else:
            spreadsheet = client.open_by_key(sheet_url_or_id)
    except gspread.exceptions.SpreadsheetNotFound:
        client_email = creds_info.get("client_email", "tu-cuenta-de-servicio")
        raise ValueError(
            "No se encontró el Google Sheet. Por favor verifica:\n\n"
            "1. Que la URL o ID del Google Sheet sea correcta.\n"
            f"2. Que hayas compartido el Google Sheet con el correo:\n"
            f"   👉 **{client_email}**\n"
            "   con permisos de **Lector** (Viewer)."
        )
    except gspread.exceptions.APIError as e:
        client_email = creds_info.get("client_email", "tu-cuenta-de-servicio")
        raise ValueError(
            f"Error de API de Google (permisos o cuota). Detalle: {e}\n\n"
            f"Verifica que hayas compartido el Google Sheet con: **{client_email}**"
        )
    except Exception as e:
        raise ValueError(f"Error al abrir la hoja de cálculo: {e}")

    # ── Apertura de la pestaña ──
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # Intentar obtener pestañas disponibles para ayudar al usuario
        try:
            available_sheets = [w.title for w in spreadsheet.worksheets()]
            sheets_str = ", ".join([f"'{s}'" for s in available_sheets])
            helper_msg = f"\n\nPestañas disponibles encontradas en este archivo: {sheets_str}"
        except Exception:
            helper_msg = ""
        raise ValueError(
            f"No se encontró la pestaña llamada '{worksheet_name}' en el Google Sheet.{helper_msg}\n\n"
            "Verifica que el nombre coincida exactamente (mayúsculas, minúsculas, espacios)."
        )
    except Exception as e:
        raise ValueError(f"Error al acceder a la pestaña: {e}")

    # ── Conversión a DataFrame ──
    try:
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
    except Exception as e:
        raise ValueError(
            f"Error al leer los datos de la pestaña. "
            f"Verifica que no contenga celdas combinadas ni filas vacías al inicio. Detalle: {e}"
        )

    return df

