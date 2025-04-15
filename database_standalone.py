import os
import json
import base64
import sqlite3
import pandas as pd
import numpy as np
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
    """Initialize the database and create tables if they don't exist."""
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
        fecha_alta TEXT DEFAULT CURRENT_DATE,
        rori TEXT,
        id_vehiculo INTEGER,
        vtv_vencimiento TEXT
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
    """Get a database connection."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    return conn

def get_sqlalchemy_engine():
    """Get a SQLAlchemy engine."""
    db_path = get_database_path()
    return create_engine(f'sqlite:///{db_path}')

def load_vehicles(search_term=None):
    """Load all vehicles from the database with optional search filter."""
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

def add_vehicle(patente, area, tipo, marca, modelo, año, estado, km=0, fecha_service=None, taller=None, observaciones=None, pdf_files=None, rori=None, id_vehiculo=None, vtv_vencimiento=None):
    """Add a new vehicle to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO vehiculos (
            patente, area, tipo, marca, modelo, año, estado, km, 
            fecha_service, taller, observaciones, pdf_files,
            rori, id_vehiculo, vtv_vencimiento
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patente, area, tipo, marca, modelo, año, estado, km, 
            fecha_service, taller, observaciones, pdf_files,
            rori, id_vehiculo, vtv_vencimiento
        ))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        st.error(f"Error al agregar vehículo: {e}")
        return False
    finally:
        conn.close()

def update_vehicle(patente, **kwargs):
    """Update vehicle information."""
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
    """Delete a vehicle from the database."""
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
    """Get a vehicle by its license plate number."""
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

def add_service_record(patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files=None):
    """Add a new service record for a vehicle."""
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
    """Add a new incident record."""
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
    """Get service history for a specific vehicle or all vehicles."""
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
    """Get incidents for a specific vehicle or all vehicles, optionally filtered by status."""
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
    """Get fleet statistics for reports."""
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
    """Process an uploaded CSV file into a pandas DataFrame."""
    try:
        if uploaded_file.name.endswith('.csv'):
            # Try UTF-8 first
            try:
                df = pd.read_csv(uploaded_file, sep=',', encoding='utf-8')
            except UnicodeDecodeError:
                # Try Latin-1 encoding if UTF-8 fails
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=',', encoding='latin1')
            
            # Clean the DataFrame: remove empty rows and columns
            df = df.dropna(how='all').reset_index(drop=True)  # Drop rows where all values are NaN
            df = df.dropna(axis=1, how='all')  # Drop columns where all values are NaN
            
            # Detección específica para formato SEC DE GOBIERNO con estructura especial
            # Buscar la fila que contiene "patente" como encabezado
            header_row = None
            for i, row in df.iterrows():
                row_values = [str(x).lower().strip() for x in row.values if pd.notna(x)]
                if 'patente' in row_values:
                    header_row = i
                    break
            
            if header_row is not None:
                # Usar esta fila como encabezados y usar solo los datos posteriores
                headers = [str(x).strip() if pd.notna(x) else f"col_{i}" for i, x in enumerate(df.iloc[header_row])]
                df = pd.DataFrame(df.iloc[header_row+1:].values, columns=headers)
                
                # Filtrar filas vacías o que solo tienen formato 
                df = df[df.iloc[:, 0].notna() & (df.iloc[:, 0].astype(str).str.strip() != '')]
            
            # Clean and standardize column names
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Map expected columns with expanded options, específicamente para SEC DE GOBIERNO
            column_map = {
                'patente': ['patente', 'dominio', 'placa', 'matricula', 'pt', 'chapa patente'],
                'area': ['area', 'dependencia', 'seccion', 'departamento', 'ubicacion'],
                'tipo': ['tipo', 'tipo de vehiculo', 'clase', 'tipo vehiculo', 'tipo vehículo'],
                'marca': ['marca'],
                'modelo': ['modelo'],
                'año': ['año', 'ano', 'year', 'modelo año', 'a? - fecha alta', 'a? - fecha alta'],
                'estado': ['estado', 'condicion', 'status'],
                'km': ['km', 'kilometraje', 'kilometros', 'kms'],
                'rori': ['rori', 'ro-ri'],          # Columna 7 en SEC DE GOBIERNO
                'id_vehiculo': ['id', 'id vehiculo'], # Columna 8 en SEC DE GOBIERNO
                'vtv_vencimiento': ['vtv'],         # Columna 15 en SEC DE GOBIERNO
                'taller': ['taller']                # Columna 13 en SEC DE GOBIERNO
            }
            
            # Create standardized dataframe
            std_df = pd.DataFrame()
            
            # Map columns based on the standard names
            for std_col, possible_cols in column_map.items():
                for col in possible_cols:
                    if col in df.columns:
                        std_df[std_col] = df[col]
                        break
                if std_col not in std_df.columns:
                    # Add empty column if not found
                    if std_col == 'estado':
                        std_df[std_col] = 'SERVICIO'  # Default value
                    else:
                        std_df[std_col] = ''
            
            # Para el archivo SEC DE GOBIERNO, manejar columnas por posición si no las encontramos por nombre
            if len(std_df) > 0 and 'patente' in std_df.columns and std_df['patente'].notna().any():
                # Si tenemos al menos una patente pero faltan las columnas específicas, intentamos por posición
                if 'rori' not in std_df.columns or std_df['rori'].isna().all():
                    try:
                        # RO-RI es la columna 7
                        std_df['rori'] = df.iloc[:, 7] if df.shape[1] > 7 else ''
                    except:
                        std_df['rori'] = ''
                        
                if 'id_vehiculo' not in std_df.columns or std_df['id_vehiculo'].isna().all():
                    try:
                        # ID es la columna 8
                        std_df['id_vehiculo'] = df.iloc[:, 8] if df.shape[1] > 8 else ''
                    except:
                        std_df['id_vehiculo'] = ''
                        
                if 'taller' not in std_df.columns or std_df['taller'].isna().all():
                    try:
                        # TALLER es la columna 13
                        std_df['taller'] = df.iloc[:, 13] if df.shape[1] > 13 else ''
                    except:
                        std_df['taller'] = ''
                        
                if 'vtv_vencimiento' not in std_df.columns or std_df['vtv_vencimiento'].isna().all():
                    try:
                        # VTV es la columna 15
                        std_df['vtv_vencimiento'] = df.iloc[:, 15] if df.shape[1] > 15 else ''
                    except:
                        std_df['vtv_vencimiento'] = ''
            
            # Ensure numeric columns
            if 'año' in std_df.columns:
                # Limpiar valores no numéricos y reemplazar valores como '-' con NaN
                std_df['año'] = std_df['año'].astype(str).replace(['-', 'nan', 'null', ''], np.nan)
                # Extraer solo dígitos si hay texto mixto
                std_df['año'] = std_df['año'].str.extract('(\d+)').fillna(np.nan)
                # Convertir a numérico con manejo de errores
                std_df['año'] = pd.to_numeric(std_df['año'], errors='coerce').fillna(0).astype(int)
                
            if 'km' in std_df.columns:
                # Limpiar y manejar valores no numéricos
                std_df['km'] = std_df['km'].astype(str).replace(['-', 'nan', 'null', ''], np.nan)
                std_df['km'] = pd.to_numeric(std_df['km'], errors='coerce').fillna(0).astype(int)
                
            # Manejar id_vehiculo que es donde el error ocurre principalmente
            if 'id_vehiculo' in std_df.columns:
                # Reemplazar cualquier valor no numérico con NaN
                std_df['id_vehiculo'] = std_df['id_vehiculo'].astype(str).replace(['-', 'nan', 'null', ''], np.nan)
                # Intentar extraer solo la parte numérica si hay texto mixto
                std_df['id_vehiculo'] = std_df['id_vehiculo'].str.extract('(\d+)').fillna(np.nan)
                # Convertir a numérico con manejo de errores
                std_df['id_vehiculo'] = pd.to_numeric(std_df['id_vehiculo'], errors='coerce').fillna(0).astype(int)
                
            # Remove duplicate vehicles
            std_df = std_df.drop_duplicates(subset=['patente'])
            
            # Remove rows where patente is empty or just whitespace
            std_df = std_df[std_df['patente'].astype(str).str.strip() != '']
            
            # Validate estado
            valid_states = ['SERVICIO', 'RECUPERAR', 'RADIADO']
            std_df['estado'] = std_df['estado'].astype(str).str.strip().str.upper()
            std_df.loc[~std_df['estado'].isin(valid_states), 'estado'] = 'SERVICIO'
            
            return std_df
        else:
            st.error("El archivo debe ser un CSV.")
            return None
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        import traceback
        st.write(traceback.format_exc())
        return None

def import_vehicles_from_df(df):
    """Import vehicles from a DataFrame into the database."""
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
                
                for col, db_col in [
                    ('area', 'area'), ('tipo', 'tipo'), ('marca', 'marca'), ('modelo', 'modelo'),
                    ('año', 'año'), ('estado', 'estado'), ('km', 'km'), ('taller', 'taller'),
                    ('rori', 'rori'), ('id_vehiculo', 'id_vehiculo'), ('vtv_vencimiento', 'vtv_vencimiento')
                ]:
                    if col in row and not pd.isna(row[col]):
                        fields.append(f"{db_col} = ?")
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
                INSERT INTO vehiculos (
                    patente, area, tipo, marca, modelo, año, estado, km,
                    taller, rori, id_vehiculo, vtv_vencimiento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['patente'],
                    row.get('area', ''),
                    row.get('tipo', ''),
                    row.get('marca', ''),
                    row.get('modelo', ''),
                    row.get('año', 0),
                    row.get('estado', 'SERVICIO'),
                    row.get('km', 0),
                    row.get('taller', ''),
                    row.get('rori', ''),
                    row.get('id_vehiculo', 0),
                    row.get('vtv_vencimiento', '')
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
    """Process uploaded PDF files and return a JSON string with the file data."""
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
    """Generate HTML download links for PDF files stored in the database."""
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