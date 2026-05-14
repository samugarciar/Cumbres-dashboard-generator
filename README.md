# Cumbres Dashboard Generator

Dashboard interactivo para la visualizacion y seguimiento de citas (appointments) con datos obtenidos en tiempo real desde Google Sheets o archivos locales (Excel / CSV).

---

## Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Sistema de Formatos](#sistema-de-formatos)
- [Prerrequisitos](#prerrequisitos)
- [Instalacion](#instalacion)
- [Configuracion de Credenciales](#configuracion-de-credenciales)
- [Ejecucion](#ejecucion)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Agregar un Formato Nuevo](#agregar-un-formato-nuevo)
- [Seguridad](#seguridad)

---

## Arquitectura

El proyecto sigue una arquitectura modular con un sistema de formatos tipo plugin:

```
Origenes de datos
├── Google Sheets (API via gspread)
└── Archivo local (Excel/CSV → Parquet)
        |
        v
  Sistema de Formatos (formats/)
  ├── Validacion de columnas
  ├── KPIs personalizados
  └── Graficos personalizados
        |
        v
     app.py  ── Streamlit + Pandas + Plotly
        |
        v
  Navegador web (interfaz de usuario)
```

- **formats/**: Paquete de formatos. Cada formato define su esquema, KPIs y graficos. Se descubren automaticamente al iniciar la app.
- **data_loader.py**: Acceso a Google Sheets via Service Account con cache de 10 minutos.
- **data_manager.py**: Persistencia local de datasets en formato Parquet con un registro JSON central.
- **components/**: Componentes UI reutilizables (KPI cards, graficos, sidebar).
- **app.py**: Orquestador principal que conecta todo.

---

## Sistema de Formatos

Cada formato es una clase Python en `formats/` que hereda de `BaseFormat` y define:

- **Columnas esperadas** con tipos y requisitos
- **KPIs** a calcular sobre los datos filtrados
- **Graficos** a renderizar (con posicionamiento left/right)
- **Opciones de agrupacion** para el sidebar

Para agregar un formato nuevo, solo se necesita crear un archivo Python en `formats/`. El sistema lo descubre automaticamente al reiniciar la app.

---

## Prerrequisitos

1. **Python 3.9 o superior** instalado en tu sistema.
2. **Una cuenta de Google Cloud** con un proyecto activo (solo si usas Google Sheets como origen).
3. **Una Service Account** con acceso a la API de Google Sheets:
   - Ve a Google Cloud Console, seccion "IAM & Admin" y luego "Service Accounts".
   - Crea una nueva Service Account (o utiliza una existente).
   - Genera una clave en formato JSON y descargala.
   - Habilita la API de Google Sheets y la API de Google Drive en tu proyecto de GCP.
4. **El Google Sheet** debe estar compartido con el correo electronico de la Service Account (campo `client_email` del JSON) con permisos de **Lector**.

Si solo vas a usar archivos locales (Excel/CSV), los pasos 2-4 no son necesarios.

---

## Instalacion

1. Clona el repositorio:

```bash
git clone https://github.com/samugarciar/Cumbres-dashboard-generator.git
cd Cumbres-dashboard-generator
```

2. Crea y activa un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

---

## Configuracion de Credenciales

Este paso solo es necesario si vas a usar Google Sheets como origen de datos.

1. Crea el directorio `.streamlit` si no existe:

```bash
mkdir -p .streamlit
```

2. Crea el archivo `.streamlit/secrets.toml` tomando como referencia la plantilla incluida.

3. Abre el archivo JSON de tu Service Account y copia cada campo dentro de la seccion `[gcp_service_account]` del archivo `secrets.toml`.

---

## Ejecucion

Con el entorno virtual activo:

```bash
streamlit run app.py
```

La aplicacion se abrira automaticamente en tu navegador en `http://localhost:8501`.

Desde la barra lateral podras:

- Seleccionar el origen de datos (Archivo Local o Google Sheets).
- Elegir el formato de datos (cada formato define sus columnas y graficos).
- Subir archivos Excel o CSV y guardarlos como datasets persistentes.
- Seleccionar datasets guardados previamente.
- Actualizar o eliminar datasets existentes.
- Configurar la agrupacion y el rango de fechas.

---

## Estructura del Proyecto

```
Cumbres-dashboard-generator/
├── .gitignore
├── .streamlit/
│   └── secrets.toml               # Credenciales (NO subir a repositorios)
├── app.py                          # Orquestador principal
├── data_loader.py                  # Carga desde Google Sheets
├── data_manager.py                 # Persistencia local (Parquet + JSON)
├── requirements.txt                # Dependencias de Python
├── README.md                       # Documentacion del proyecto
│
├── formats/                        # Sistema de formatos (plugins)
│   ├── __init__.py                 # Auto-descubrimiento
│   ├── base_format.py              # Clase abstracta BaseFormat
│   └── citas_inmobiliarias.py      # Formato: Citas Inmobiliarias
│
├── components/                     # Componentes UI reutilizables
│   ├── __init__.py
│   ├── kpi_cards.py                # Tarjetas KPI glassmorphism
│   ├── charts.py                   # Renderizado de graficos Plotly
│   └── sidebar.py                  # Logica del sidebar
│
└── data/                           # Datasets persistidos (gitignored)
    ├── registry.json               # Indice de datasets
    └── datasets/                   # Archivos Parquet
```

---

## Agregar un Formato Nuevo

1. Crea un archivo en `formats/`, por ejemplo `formats/seguimiento_leads.py`.

2. Define una clase que herede de `BaseFormat`:

```python
from .base_format import BaseFormat, ColumnSpec, KPI

class SeguimientoLeads(BaseFormat):
    id = "seguimiento_leads"
    name = "Seguimiento de Leads"
    description = "Tracking de leads por fuente y estado"
    icon = "📋"
    date_column = "Fecha"
    grouping_options = ["Fuente", "Estado"]

    columns = {
        "Fecha":  ColumnSpec(type="datetime", required=True),
        "Lead":   ColumnSpec(type="string",   required=True),
        "Fuente": ColumnSpec(type="string",   required=True),
        "Estado": ColumnSpec(type="string",   required=True),
    }

    def compute_kpis(self, df):
        return [
            KPI(label="Total Leads", value=len(df)),
            KPI(label="Fuentes",     value=df["Fuente"].nunique()),
        ]

    def build_charts(self, df, grouping):
        # ... retornar lista de (posicion, figura_plotly)
        ...
```

3. Reinicia la app. El formato aparecera automaticamente en el sidebar.

---

## Seguridad

**Advertencia**: El archivo `.streamlit/secrets.toml` contiene credenciales sensibles de tu Service Account de Google Cloud. **Nunca subas este archivo a un repositorio publico.**

El archivo `.gitignore` incluido ya excluye:
- `.streamlit/` — credenciales de la Service Account.
- `data/` — datasets locales con datos potencialmente sensibles.

Siempre verifica antes de hacer un commit:

```bash
git status
```

Si necesitas compartir el proyecto con otros colaboradores, cada persona debera crear su propio archivo `secrets.toml` con sus credenciales.
