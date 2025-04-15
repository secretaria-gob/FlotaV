import os
import shutil
import subprocess
import sys

def build_executable():
    print("Iniciando empaquetado de la aplicación para distribución...")
    
    # Asegurarse de que los directorios del build existan
    if os.path.exists("dist"):
        print("Limpiando directorio dist previo...")
        shutil.rmtree("dist")
    if os.path.exists("build"):
        print("Limpiando directorio build previo...")
        shutil.rmtree("build")
    
    # Crear directorio para archivos adicionales
    os.makedirs("standalone_assets", exist_ok=True)
    
    # Crear un archivo config.yaml con usuarios de ejemplo para standalone
    with open("standalone_assets/config.yaml", "w") as f:
        f.write("""credentials:
  usernames:
    admin:
      name: Administrador
      password: $2b$12$Pb0ZxrCHNTPQoLsdBR1UGe6O.3n7ECVIcqiPXHH7qn.zpb2NnLoGK  # admin123
      role: admin
    user:
      name: Usuario Regular
      password: $2b$12$lQOXx1.mfQz5GD9DJM.8SeWP1tCJ.2F/hPrtrrm85w7e6ATUlwglu  # user123
      role: user
cookie:
  expiry_days: 30
  key: flota_vehicular_app
  name: flota_cookie
""")
    
    # Crear script launcher.py para la aplicación standalone
    with open("launcher.py", "w") as f:
        f.write("""import os
import sys
import sqlite3
import streamlit.web.cli as stcli
from pathlib import Path

def main():
    # Configurar el entorno para modo standalone
    os.environ['STREAMLIT_SERVER_PORT'] = "8501"
    os.environ['STREAMLIT_SERVER_HEADLESS'] = "false"
    os.environ['STREAMLIT_SERVER_ADDRESS'] = "localhost"
    
    # Crear directorio de datos si no existe
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Ruta a la base de datos SQLite
    db_path = os.path.join(data_dir, "flota_vehicular.db")
    os.environ['DATABASE_FILE'] = db_path
    
    # Copiar config.yaml si no existe
    config_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(config_dir, "config.yaml")
    
    if not os.path.exists(config_path):
        assets_config = os.path.join(config_dir, "standalone_assets", "config.yaml")
        if os.path.exists(assets_config):
            import shutil
            shutil.copy(assets_config, config_path)
    
    # Obtener la ruta al script app.py
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    # Iniciar Streamlit
    sys.argv = ["streamlit", "run", app_path]
    stcli.main()

if __name__ == "__main__":
    main()
""")
    
    # Modificar database.py para modo standalone usando SQLite
    create_standalone_database_module()
    
    # Crear el spec file para PyInstaller
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('database_standalone.py', '.'),
        ('auth.py', '.'),
        ('send_message.py', '.'),
        ('config.yaml', '.'),
        ('standalone_assets/config.yaml', 'standalone_assets'),
        ('.streamlit', '.streamlit')
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'sqlite3',
        'yaml',
        'sqlalchemy',
        'streamlit_authenticator'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Gestion_Flota_Vehicular',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Gestion_Flota_Vehicular',
)
"""
    
    with open("gestflota.spec", "w") as f:
        f.write(spec_content)
    
    # Ejecutar PyInstaller
    print("Ejecutando PyInstaller...")
    result = subprocess.call(["pyinstaller", "gestflota.spec", "--noconfirm"])
    
    if result == 0:
        print("¡Empaquetado completado con éxito!")
        print("El ejecutable se encuentra en la carpeta 'dist/Gestion_Flota_Vehicular'")
        print("Para distribuir la aplicación, copie toda la carpeta 'Gestion_Flota_Vehicular'.")
    else:
        print("Error durante el empaquetado. Revise los mensajes de error.")

def create_standalone_database_module():
    """Crea una versión standalone del módulo database.py usando SQLite"""
    
    standalone_db_content = """import os
import json
import base64
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from sqlalchemy import create_engine

# Función para obtener la ruta de la base de datos SQLite
def get_database_path():
    if 'DATABASE_FILE' in os.environ:
        return os.environ['DATABASE_FILE']
    # Fallback al directorio actual
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "flota_vehicular.db")

def init_database():
    """"Initialize the database and create tables if they don't exist.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create vehicles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehiculos (
        patente TEXT PRIMARY KEY,
        area TEXT,
        tipo TEXT,
        marca TEXT,
        modelo TEXT,
        año INTEGER,
        estado TEXT DEFAULT 'SERVICIO',
        km INTEGER DEFAULT 0,
        fecha_service TEXT,
        taller TEXT,
        observaciones TEXT,
        pdf_files TEXT,
        fecha_alta TEXT DEFAULT CURRENT_DATE
    )
    ''')
    
    # Create service history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historial_service (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patente TEXT,
        fecha TEXT,
        km INTEGER,
        tipo_service TEXT,
        taller TEXT,
        costo REAL,
        descripcion TEXT,
        pdf_files TEXT,
        FOREIGN KEY (patente) REFERENCES vehiculos (patente)
    )
    ''')
    
    # Create incidents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS incidentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patente TEXT,
        fecha TEXT,
        tipo TEXT,
        descripcion TEXT,
        estado TEXT DEFAULT 'PENDIENTE',
        pdf_files TEXT,
        FOREIGN KEY (patente) REFERENCES vehiculos (patente)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    """"Get a database connection.""""""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    return conn

def get_sqlalchemy_engine():
    """"Get a SQLAlchemy engine.""""
    db_path = get_database_path()
    return create_engine(f'sqlite:///{db_path}')

def load_vehicles(search_term=None):
    """"Load all vehicles from the database with optional search filter.""""""
    engine = get_sqlalchemy_engine()
    
    if search_term:
        query = f'''
        SELECT * FROM vehiculos
        WHERE patente LIKE '%{search_term}%'
        OR area LIKE '%{search_term}%'
        OR tipo LIKE '%{search_term}%'
        OR marca LIKE '%{search_term}%'
        OR modelo LIKE '%{search_term}%'
        OR estado LIKE '%{search_term}%'
        ORDER BY patente
        '''
    else:
        query = 'SELECT * FROM vehiculos ORDER BY patente'
    
    df = pd.read_sql(query, engine)
    return df

def add_vehicle(patente, area, tipo, marca, modelo, año, estado, km=0, fecha_service=None, taller=None, observaciones=None, pdf_files=None):
    """"Add a new vehicle to the database.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO vehiculos (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, observaciones, pdf_files)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, observaciones, pdf_files))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def update_vehicle(patente, **kwargs):
    """"Update vehicle information.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build update query dynamically based on provided fields
    fields = []
    values = []
    
    for key, value in kwargs.items():
        fields.append(f"{key} = ?")
        values.append(value)
    
    # Add patente to values for WHERE clause
    values.append(patente)
    
    try:
        query = f"UPDATE vehiculos SET {', '.join(fields)} WHERE patente = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def delete_vehicle(patente):
    """"Delete a vehicle from the database.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # First check if the vehicle has any related records
        cursor.execute("SELECT COUNT(*) FROM historial_service WHERE patente = ?", (patente,))
        has_service = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM incidentes WHERE patente = ?", (patente,))
        has_incidents = cursor.fetchone()[0] > 0
        
        if has_service or has_incidents:
            return False
        
        cursor.execute("DELETE FROM vehiculos WHERE patente = ?", (patente,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_vehicle_by_patente(patente):
    """"Get a vehicle by its license plate number.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM vehiculos WHERE patente = ?", (patente,))
        row = cursor.fetchone()
        
        if row:
            columns = [col[0] for col in cursor.description]
            vehicle = dict(zip(columns, row))
            return vehicle
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def a"dd_service_record(patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files=None):
    """"Add a new service record for a vehicle.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Add service record
        cursor.execute('''
        INSERT INTO historial_service (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files))
        
        # Update vehicle's current km and last service date
        cursor.execute('''
        UPDATE vehiculos 
        SET km = ?, fecha_service = ?, taller = ?
        WHERE patente = ?
        ''', (km, fecha, taller, patente))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def add_incident(patente, fecha, tipo, descripcion, estado, pdf_files=None):
    """"Add a new incident record.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO incidentes (patente, fecha, tipo, descripcion, estado, pdf_files)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (patente, fecha, tipo, descripcion, estado, pdf_files))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def get_service_history(patente=None):
    """"Get service history for a specific vehicle or all vehicles.""""
    engine = get_sqlalchemy_engine()
    
    if patente:
        query = f'''
        SELECT h.*, v.marca, v.modelo
        FROM historial_service h
        JOIN vehiculos v ON h.patente = v.patente
        WHERE h.patente = '{patente}'
        ORDER BY h.fecha DESC, h.id DESC
        '''
    else:
        query = '''
        SELECT h.*, v.marca, v.modelo
        FROM historial_service h
        JOIN vehiculos v ON h.patente = v.patente
        ORDER BY h.fecha DESC, h.id DESC
        '''
    
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Error loading service history: {e}")
        return pd.DataFrame()

def get_incidents(patente=None, estado=None):
    """"Get incidents for a specific vehicle or all vehicles, optionally filtered by status.""""""
    engine = get_sqlalchemy_engine()
    
    conditions = []
    if patente:
        conditions.append(f"i.patente = '{patente}'")
    if estado:
        conditions.append(f"i.estado = '{estado}'")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = f'''
    SELECT i.*, v.marca, v.modelo
    FROM incidentes i
    JOIN vehiculos v ON i.patente = v.patente
    {where_clause}
    ORDER BY i.fecha DESC, i.id DESC
    '''
    
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Error loading incidents: {e}")
        return pd.DataFrame()

def get_stats():
    """"Get fleet statistics for reports.""""""
    engine = get_sqlalchemy_engine()
    
    try:
        # Vehicles by status
        status_query = '''
        SELECT estado, COUNT(*) as cantidad
        FROM vehiculos
        GROUP BY estado
        '''
        status_df = pd.read_sql(status_query, engine)
        
        # Vehicles by type
        type_query = '''
        SELECT tipo, COUNT(*) as cantidad
        FROM vehiculos
        GROUP BY tipo
        '''
        type_df = pd.read_sql(type_query, engine)
        
        # Vehicles by area
        area_query = '''
        SELECT area, COUNT(*) as cantidad
        FROM vehiculos
        GROUP BY area
        '''
        area_df = pd.read_sql(area_query, engine)
        
        # Service by month (last 12 months)
        service_query = '''
        SELECT strftime('%Y-%m', fecha) as mes, COUNT(*) as cantidad, SUM(costo) as costo_total
        FROM historial_service
        WHERE fecha >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', fecha)
        ORDER BY mes
        '''
        service_df = pd.read_sql(service_query, engine)
        
        # Incidents by status
        incidents_query = '''
        SELECT estado, COUNT(*) as cantidad
        FROM incidentes
        GROUP BY estado
        '''
        incidents_df = pd.read_sql(incidents_query, engine)
        
        return {
            "status": status_df,
            "type": type_df,
            "area": area_df,
            "service_by_month": service_df,
            "incidents": incidents_df
        }
    except Exception as e:
        print(f"Error loading stats: {e}")
        return {
            "status": pd.DataFrame(),
            "type": pd.DataFrame(),
            "area": pd.DataFrame(),
            "service_by_month": pd.DataFrame(),
            "incidents": pd.DataFrame()
        }

def process_uploaded_file(uploaded_file):
    """"Process an uploaded CSV file into a pandas DataFrame.""""""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Convert column names to lowercase and strip spaces
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Map expected column names
        column_mappings = {
            'patente': ['patente', 'dominio', 'patente/dominio', 'dominio/patente'],
            'area': ['area', 'dependencia', 'área', 'área/dependencia', 'area/dependencia'],
            'tipo': ['tipo', 'tipo de vehículo', 'tipo de vehiculo', 'tipo vehiculo', 'tipo vehículo'],
            'marca': ['marca'],
            'modelo': ['modelo'],
            'año': ['año', 'ano', 'modelo año', 'año modelo'],
            'estado': ['estado'],
            'km': ['km', 'kilometraje', 'kilómetros', 'kilometros']
        }
        
        # Create standard column names
        for std_col, possible_cols in column_mappings.items():
            for col in possible_cols:
                if col in df.columns:
                    df.rename(columns={col: std_col}, inplace=True)
                    break
        
        # Check if required column exists
        if 'patente' not in df.columns:
            st.error("El archivo CSV debe contener una columna con el nombre 'patente' o 'dominio'.")
            return None
        
        # Set default values for missing columns
        default_values = {
            'area': '',
            'tipo': '',
            'marca': '',
            'modelo': '',
            'año': 0,
            'estado': 'SERVICIO',
            'km': 0
        }
        
        for col, default in default_values.items():
            if col not in df.columns:
                df[col] = default
        
        # Clean and convert data types
        df['patente'] = df['patente'].astype(str).str.strip().str.upper()
        if 'año' in df.columns:
            df['año'] = pd.to_numeric(df['año'], errors='coerce').fillna(0).astype(int)
        if 'km' in df.columns:
            df['km'] = pd.to_numeric(df['km'], errors='coerce').fillna(0).astype(int)
        if 'estado' in df.columns:
            df['estado'] = df['estado'].astype(str).str.strip().str.upper()
            # Set default state if not valid
            valid_states = ['SERVICIO', 'RECUPERAR', 'RADIADO']
            df.loc[~df['estado'].isin(valid_states), 'estado'] = 'SERVICIO'
        
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        return None

def import_vehicles_from_df(df):
    """"Import vehicles from a DataFrame into the database.""""""
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    error_plates = []
    
    for _, row in df.iterrows():
        try:
            # Check if the vehicle already exists
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = ?", (row['patente'],))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing vehicle
                fields = []
                values = []
                
                for col in ['area', 'tipo', 'marca', 'modelo', 'año', 'estado', 'km']:
                    if col in row and not pd.isna(row[col]):
                        fields.append(f"{col} = ?")
                        values.append(row[col])
                
                if fields:
                    # Add patente to values for WHERE clause
                    values.append(row['patente'])
                    
                    query = f"UPDATE vehiculos SET {', '.join(fields)} WHERE patente = ?"
                    cursor.execute(query, values)
                    success_count += 1
                else:
                    error_count += 1
                    error_plates.append(row['patente'])
            else:
                # Insert new vehicle
                cursor.execute('''
                INSERT INTO vehiculos (patente, area, tipo, marca, modelo, año, estado, km)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['patente'],
                    row.get('area', ''),
                    row.get('tipo', ''),
                    row.get('marca', ''),
                    row.get('modelo', ''),
                    row.get('año', 0),
                    row.get('estado', 'SERVICIO'),
                    row.get('km', 0)
                ))
                success_count += 1
        except Exception as e:
            print(f"Error importing vehicle {row.get('patente', 'unknown')}: {e}")
            error_count += 1
            error_plates.append(row.get('patente', 'unknown'))
    
    conn.commit()
    conn.close()
    
    return success_count, error_count, error_plates

def process_pdf_files(uploaded_files):
    """"Process uploaded PDF files and return a JSON string with the file data.""""""
    if not uploaded_files:
        return None
    
    pdf_data = []
    
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        encoded = base64.b64encode(file_bytes).decode()
        
        pdf_data.append({
            "name": uploaded_file.name,
            "content": encoded,
            "type": "application/pdf",
            "size": len(file_bytes)
        })
    
    return json.dumps(pdf_data)

def get_pdf_download_links(pdf_files_json):
    """"Generate HTML download links for PDF files stored in the database."""""
    if not pdf_files_json:
        return None
    
    try:
        pdf_files = json.loads(pdf_files_json)
        html_links = ""
        
        for i, pdf in enumerate(pdf_files):
            # Create a download link with base64 data
            file_name = pdf.get("name", f"documento_{i+1}.pdf")
            b64_content = pdf.get("content", "")
            
            if b64_content:
                html_links += f'<p><a href="data:application/pdf;base64,{b64_content}" download="{file_name}" target="_blank">{file_name}</a></p>'
        
        return html_links
    except Exception as e:
        print(f"Error generating PDF links: {e}")
        return None

            """"Extract file names from the JSON string of PDF files."""

                        
    with open("database_standalone.py", "w") as f:
        f.write(standalone_db_content)

if __name__ == "__main__":
    build_executable()