import os
import pandas as pd
import numpy as np
import io
import streamlit as st
import json
import base64
from io import StringIO, BytesIO
import sqlite3
import importlib.util
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# Detectar automáticamente si debemos usar la versión PostgreSQL o SQLite (standalone)
USE_POSTGRES = "DATABASE_URL" in os.environ
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Importar psycopg2 solo si estamos usando PostgreSQL
if USE_POSTGRES:
    import psycopg2
else:
    # Si no hay PostgreSQL, usamos la versión SQLite (standalone)
    print("DATABASE_URL no encontrada, usando SQLite en modo standalone")

def get_database_path():
    """Get the path to the SQLite database file."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "flota_vehicular.db")

def init_database():
    """Initialize the database and create tables if they don't exist."""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
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
                estado TEXT,
                km INTEGER DEFAULT 0,
                fecha_service TEXT,
                taller TEXT,
                observaciones TEXT,
                pdf_files TEXT,
                rori TEXT,
                id_vehiculo INTEGER,
                vtv_vencimiento TEXT
            )
        ''')
        
        # Create service history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_service (
                id SERIAL PRIMARY KEY,
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
        
        # Create incident/maintenance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidentes (
                id SERIAL PRIMARY KEY,
                patente TEXT,
                fecha TEXT,
                tipo TEXT,
                descripcion TEXT,
                estado TEXT,
                pdf_files TEXT,
                FOREIGN KEY (patente) REFERENCES vehiculos (patente)
            )
        ''')
        
        # Create maintenance schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS programacion_mantenimiento (
                id SERIAL PRIMARY KEY,
                patente TEXT,
                fecha_programada TEXT,
                km_programado INTEGER,
                tipo_service TEXT,
                descripcion TEXT,
                recordatorio_enviado BOOLEAN DEFAULT FALSE,
                estado TEXT DEFAULT 'PENDIENTE',
                fecha_creacion TEXT DEFAULT CURRENT_DATE,
                FOREIGN KEY (patente) REFERENCES vehiculos (patente)
            )
        ''')
    else:
        # Usar SQLite en modo standalone
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
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
        
        # Create maintenance schedule table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS programacion_mantenimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patente TEXT,
            fecha_programada TEXT,
            km_programado INTEGER,
            tipo_service TEXT,
            descripcion TEXT,
            recordatorio_enviado BOOLEAN DEFAULT 0,
            estado TEXT DEFAULT 'PENDIENTE',
            fecha_creacion TEXT DEFAULT CURRENT_DATE,
            FOREIGN KEY (patente) REFERENCES vehiculos (patente)
        )
        ''')
    
    conn.commit()
    conn.close()

def get_connection():
    """Get a database connection."""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        db_path = get_database_path()
        return sqlite3.connect(db_path)

def get_sqlalchemy_engine():
    """Get a SQLAlchemy engine."""
    if USE_POSTGRES:
        return create_engine(DATABASE_URL)
    else:
        db_path = get_database_path()
        return create_engine(f'sqlite:///{db_path}')

def load_vehicles(search_term=None):
    """Load all vehicles from the database with optional search filter."""
    engine = get_sqlalchemy_engine()
    
    if search_term:
        search_pattern = f"%{search_term}%"
        if USE_POSTGRES:
            query = """
                SELECT * FROM vehiculos 
                WHERE patente LIKE %s OR area LIKE %s OR marca LIKE %s OR modelo LIKE %s
            """
            df = pd.read_sql(query, engine, params=(search_pattern, search_pattern, search_pattern, search_pattern))
        else:
            # SQLite usa ? en vez de %s
            query = """
                SELECT * FROM vehiculos 
                WHERE patente LIKE ? OR area LIKE ? OR marca LIKE ? OR modelo LIKE ?
            """
            df = pd.read_sql(query, engine, params=(search_pattern, search_pattern, search_pattern, search_pattern))
    else:
        df = pd.read_sql("SELECT * FROM vehiculos", engine)
    
    return df

def add_vehicle(patente, area, tipo, marca, modelo, año, estado, km=0, fecha_service=None, taller=None, observaciones=None, pdf_files=None, rori=None, id_vehiculo=None, vtv_vencimiento=None):
    """Add a new vehicle to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO vehiculos 
                (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento))
        else:
            # SQLite usa ? en vez de %s
            cursor.execute('''
                INSERT INTO vehiculos 
                (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento))
        
        conn.commit()
        result = True
    except Exception as e:
        # Manejar error de clave duplicada (patente debe ser única) para ambos tipos de base de datos
        if "UNIQUE constraint" in str(e) or "unique" in str(e).lower() or "duplicate" in str(e).lower():
            result = False
        else:
            st.error(f"Error al agregar vehículo: {e}")
            result = False
    finally:
        conn.close()
    
    return result

def update_vehicle(patente, **kwargs):
    """Update vehicle information."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            # Build the SET part of the SQL query dynamically
            set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(patente)  # Add the patente for the WHERE clause
            
            cursor.execute(f'''
                UPDATE vehiculos 
                SET {set_clause}
                WHERE patente = %s
            ''', values)
        else:
            # Para SQLite
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(patente)  # Add the patente for the WHERE clause
            
            cursor.execute(f'''
                UPDATE vehiculos 
                SET {set_clause}
                WHERE patente = ?
            ''', values)
        
        conn.commit()
        result = True  # En SQLite, cursor.rowcount puede no ser confiable
    except Exception as e:
        st.error(f"Error al actualizar vehículo: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def delete_vehicle(patente):
    """Delete a vehicle from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("DELETE FROM vehiculos WHERE patente = %s", (patente,))
        else:
            # SQLite usa ? en vez de %s
            cursor.execute("DELETE FROM vehiculos WHERE patente = ?", (patente,))
        
        conn.commit()
        result = True  # En SQLite, cursor.rowcount puede no ser confiable
    except Exception as e:
        st.error(f"Error al eliminar vehículo: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def get_vehicle_by_patente(patente):
    """Get a vehicle by its license plate number."""
    engine = get_sqlalchemy_engine()
    
    if USE_POSTGRES:
        query = "SELECT * FROM vehiculos WHERE patente = %s"
    else:
        query = "SELECT * FROM vehiculos WHERE patente = ?"
    
    df = pd.read_sql(query, engine, params=(patente,))
    
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def add_service_record(patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files=None):
    """Add a new service record for a vehicle."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO historial_service 
                (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files))
            
            # Update the vehicle's last service date and current km
            cursor.execute('''
                UPDATE vehiculos 
                SET fecha_service = %s, km = %s, taller = %s
                WHERE patente = %s
            ''', (fecha, km, taller, patente))
        else:
            # SQLite usa ? en vez de %s
            cursor.execute('''
                INSERT INTO historial_service 
                (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files))
            
            # Update the vehicle's last service date and current km
            cursor.execute('''
                UPDATE vehiculos 
                SET fecha_service = ?, km = ?, taller = ?
                WHERE patente = ?
            ''', (fecha, km, taller, patente))
        
        conn.commit()
        result = True
    except Exception as e:
        st.error(f"Error al agregar registro de servicio: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def add_incident(patente, fecha, tipo, descripcion, estado, pdf_files=None):
    """Add a new incident or maintenance record."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO incidentes 
                (patente, fecha, tipo, descripcion, estado, pdf_files)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (patente, fecha, tipo, descripcion, estado, pdf_files))
        else:
            # SQLite usa ? en vez de %s
            cursor.execute('''
                INSERT INTO incidentes 
                (patente, fecha, tipo, descripcion, estado, pdf_files)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (patente, fecha, tipo, descripcion, estado, pdf_files))
        
        conn.commit()
        result = True
    except Exception as e:
        st.error(f"Error al agregar incidente: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def get_service_history(patente=None):
    """Get service history for a specific vehicle or all vehicles."""
    engine = get_sqlalchemy_engine()
    
    if patente:
        if USE_POSTGRES:
            query = "SELECT * FROM historial_service WHERE patente = %s ORDER BY fecha DESC"
        else:
            query = "SELECT * FROM historial_service WHERE patente = ? ORDER BY fecha DESC"
        df = pd.read_sql(query, engine, params=(patente,))
    else:
        query = """
            SELECT h.*, v.marca, v.modelo 
            FROM historial_service h
            JOIN vehiculos v ON h.patente = v.patente
            ORDER BY h.fecha DESC
        """
        df = pd.read_sql(query, engine)
    
    return df

def get_incidents(patente=None, estado=None):
    """Get incidents for a specific vehicle or all vehicles, optionally filtered by status."""
    engine = get_sqlalchemy_engine()
    params = []
    
    base_query = "SELECT i.*, v.marca, v.modelo FROM incidentes i JOIN vehiculos v ON i.patente = v.patente WHERE 1=1"
    
    if patente:
        if USE_POSTGRES:
            base_query += " AND i.patente = %s"
        else:
            base_query += " AND i.patente = ?"
        params.append(patente)
    
    if estado:
        if USE_POSTGRES:
            base_query += " AND i.estado = %s"
        else:
            base_query += " AND i.estado = ?"
        params.append(estado)
    
    base_query += " ORDER BY i.fecha DESC"
    
    df = pd.read_sql(base_query, engine, params=tuple(params) if params else None)
    return df

def get_stats():
    """Get fleet statistics for reports."""
    engine = get_sqlalchemy_engine()
    
    # Vehicles by status
    status_df = pd.read_sql("SELECT estado, COUNT(*) as count FROM vehiculos GROUP BY estado", engine)
    
    # Vehicles by make
    make_df = pd.read_sql("SELECT marca, COUNT(*) as count FROM vehiculos GROUP BY marca", engine)
    
    # Vehicles by type
    type_df = pd.read_sql("SELECT tipo, COUNT(*) as count FROM vehiculos GROUP BY tipo", engine)
    
    # Vehicles by area
    area_df = pd.read_sql("SELECT area, COUNT(*) as count FROM vehiculos GROUP BY area", engine)
    
    # Vehicles by year (age distribution)
    year_df = pd.read_sql("SELECT año, COUNT(*) as count FROM vehiculos GROUP BY año ORDER BY año", engine)
    
    # Service history summary - este query debe funcionar en ambas bases de datos
    service_df = pd.read_sql("""
        SELECT v.patente, v.marca, v.modelo, v.km, v.fecha_service, COUNT(h.id) as num_services, 
        SUM(h.costo) as total_cost
        FROM vehiculos v
        LEFT JOIN historial_service h ON v.patente = h.patente
        GROUP BY v.patente
    """, engine)
    
    # Información de VTV próximos a vencer
    vtv_proximos = get_vtv_proximos_vencer(30)
    
    # Mantenimientos programados pendientes
    try:
        mantenimientos_df = pd.read_sql("""
            SELECT estado, COUNT(*) as count 
            FROM programacion_mantenimiento 
            GROUP BY estado
        """, engine)
        mantenimientos_dict = mantenimientos_df.set_index('estado')['count'].to_dict() if not mantenimientos_df.empty else {}
    except:
        mantenimientos_dict = {}
    
    return {
        "status": status_df,
        "make": make_df,
        "type": type_df,
        "area": area_df,
        "year": year_df,
        "service": service_df,
        "vtv_proximos": vtv_proximos,
        "mantenimientos": mantenimientos_dict
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
    success_count = 0
    error_count = 0
    error_plates = []
    
    for _, row in df.iterrows():
        try:
            patente = row['patente'].strip().upper() if isinstance(row['patente'], str) else str(row['patente']).upper()
            area = row['area'] if 'area' in row and not pd.isna(row['area']) else ''
            tipo = row['tipo'] if 'tipo' in row and not pd.isna(row['tipo']) else ''
            marca = row['marca'] if 'marca' in row and not pd.isna(row['marca']) else ''
            modelo = row['modelo'] if 'modelo' in row and not pd.isna(row['modelo']) else ''
            año = int(row['año']) if 'año' in row and not pd.isna(row['año']) else 0
            estado = row['estado'] if 'estado' in row and not pd.isna(row['estado']) else 'SERVICIO'
            km = int(row['km']) if 'km' in row and not pd.isna(row['km']) else 0
            
            # Check if the vehicle already exists
            if get_vehicle_by_patente(patente):
                error_count += 1
                error_plates.append(patente)
                continue  # Skip if already exists
            
            # Obtener campos adicionales para los nuevos valores
            rori = row['rori'] if 'rori' in row and not pd.isna(row['rori']) else None
            id_vehiculo = int(row['id_vehiculo']) if 'id_vehiculo' in row and not pd.isna(row['id_vehiculo']) else None
            vtv_vencimiento = row['vtv_vencimiento'] if 'vtv_vencimiento' in row and not pd.isna(row['vtv_vencimiento']) else None
            taller = row['taller'] if 'taller' in row and not pd.isna(row['taller']) else None
            
            # Add the vehicle with all fields
            result = add_vehicle(
                patente, area, tipo, marca, modelo, año, estado, km, 
                fecha_service=None, taller=taller, observaciones=None, pdf_files=None,
                rori=rori, id_vehiculo=id_vehiculo, vtv_vencimiento=vtv_vencimiento
            )
            
            if result:
                success_count += 1
            else:
                error_count += 1
                error_plates.append(patente)
                
        except Exception as e:
            st.error(f"Error al importar vehículo: {e}")
            error_count += 1
            if 'patente' in row and not pd.isna(row['patente']):
                error_plates.append(row['patente'])
    
    return success_count, error_count, error_plates

def process_pdf_files(uploaded_files):
    """Process uploaded PDF files and return a JSON string with the file data."""
    if not uploaded_files:
        return None
        
    files_data = []
    
    for pdf_file in uploaded_files:
        if pdf_file.type == 'application/pdf':
            # Read the file into memory
            file_bytes = pdf_file.read()
            file_b64 = base64.b64encode(file_bytes).decode('utf-8')
            
            files_data.append({
                'filename': pdf_file.name,
                'content_type': pdf_file.type,
                'data': file_b64
            })
    
    if files_data:
        return json.dumps(files_data)
    return None

def get_pdf_download_links(pdf_files_json):
    """Generate HTML download links for PDF files stored in the database."""
    if not pdf_files_json:
        return ""
    
    try:
        files_data = json.loads(pdf_files_json)
        links = []
        
        for idx, file_data in enumerate(files_data):
            filename = file_data.get('filename', f'document_{idx}.pdf')
            file_b64 = file_data.get('data', '')
            
            if file_b64:
                # Create a download link with the base64 data
                link = f"""
                <a href="data:application/pdf;base64,{file_b64}" 
                   download="{filename}" 
                   target="_blank"
                   style="color:#4CAF50; text-decoration:none;">
                    📄 {filename}
                </a>
                """
                links.append(link)
        
        return "".join(links) if links else ""
    except Exception as e:
        st.error(f"Error processing PDF links: {e}")
        return ""

# Funciones para programación de mantenimiento y recordatorios

def add_maintenance_schedule(patente, fecha_programada, km_programado, tipo_service, descripcion):
    """Programa un mantenimiento futuro para un vehículo."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO programacion_mantenimiento 
                (patente, fecha_programada, km_programado, tipo_service, descripcion)
                VALUES (%s, %s, %s, %s, %s)
            ''', (patente, fecha_programada, km_programado, tipo_service, descripcion))
        else:
            # SQLite usa ? en vez de %s
            cursor.execute('''
                INSERT INTO programacion_mantenimiento 
                (patente, fecha_programada, km_programado, tipo_service, descripcion)
                VALUES (?, ?, ?, ?, ?)
            ''', (patente, fecha_programada, km_programado, tipo_service, descripcion))
        
        conn.commit()
        result = True
    except Exception as e:
        st.error(f"Error al programar mantenimiento: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def get_maintenance_schedules(patente=None, estado=None, proximos_dias=None):
    """Obtiene los mantenimientos programados con opciones de filtrado.
    
    Args:
        patente: Opcional. Filtra por patente del vehículo.
        estado: Opcional. Filtra por estado ('PENDIENTE', 'COMPLETADO', 'CANCELADO').
        proximos_dias: Opcional. Muestra solo los mantenimientos programados para 
                      los próximos X días a partir de hoy.
    """
    engine = get_sqlalchemy_engine()
    params = []
    
    # Construir la consulta base con join a la tabla de vehículos para obtener info adicional
    base_query = """
        SELECT m.*, v.marca, v.modelo, v.km as km_actual 
        FROM programacion_mantenimiento m
        JOIN vehiculos v ON m.patente = v.patente
        WHERE 1=1
    """
    
    if patente:
        if USE_POSTGRES:
            base_query += " AND m.patente = %s"
        else:
            base_query += " AND m.patente = ?"
        params.append(patente)
    
    if estado:
        if USE_POSTGRES:
            base_query += " AND m.estado = %s"
        else:
            base_query += " AND m.estado = ?"
        params.append(estado)
    
    if proximos_dias and int(proximos_dias) > 0:
        if USE_POSTGRES:
            dias = int(proximos_dias)
            base_query += f" AND CAST(m.fecha_programada AS DATE) <= CURRENT_DATE + INTERVAL '{dias} days'"
            base_query += " AND CAST(m.fecha_programada AS DATE) >= CURRENT_DATE"
        else:
            base_query += f" AND m.fecha_programada <= date('now', '+{int(proximos_dias)} days')"
            base_query += " AND m.fecha_programada >= date('now')"
    
    # Ordenar por fecha programada (más cercanos primero)
    base_query += " ORDER BY m.fecha_programada ASC"
    
    df = pd.read_sql(base_query, engine, params=tuple(params) if params else None)
    return df

def update_maintenance_schedule(id_programacion, **kwargs):
    """Actualiza un registro de programación de mantenimiento."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            # Construir consulta dinámica
            set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(id_programacion)  # Añadir el id para el WHERE
            
            cursor.execute(f'''
                UPDATE programacion_mantenimiento 
                SET {set_clause}
                WHERE id = %s
            ''', values)
        else:
            # Para SQLite
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(id_programacion)  # Añadir el id para el WHERE
            
            cursor.execute(f'''
                UPDATE programacion_mantenimiento 
                SET {set_clause}
                WHERE id = ?
            ''', values)
        
        conn.commit()
        result = True
    except Exception as e:
        st.error(f"Error al actualizar programación: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def delete_maintenance_schedule(id_programacion):
    """Elimina una programación de mantenimiento."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("DELETE FROM programacion_mantenimiento WHERE id = %s", (id_programacion,))
        else:
            cursor.execute("DELETE FROM programacion_mantenimiento WHERE id = ?", (id_programacion,))
        
        conn.commit()
        result = True
    except Exception as e:
        st.error(f"Error al eliminar programación: {e}")
        result = False
    finally:
        conn.close()
    
    return result

def get_maintenance_reminders():
    """Obtiene mantenimientos que requieren recordatorio.
    
    Devuelve mantenimientos pendientes cuya fecha programada es hoy 
    o está próxima (dentro de 7 días) y el recordatorio no ha sido enviado aún.
    """
    engine = get_sqlalchemy_engine()
    
    # Consulta para obtener recordatorios pendientes
    if USE_POSTGRES:
        query = """
            SELECT m.*, v.marca, v.modelo, v.km as km_actual 
            FROM programacion_mantenimiento m
            JOIN vehiculos v ON m.patente = v.patente
            WHERE m.estado = 'PENDIENTE'
            AND m.recordatorio_enviado = FALSE
            AND (
                CAST(m.fecha_programada AS DATE) <= (CURRENT_DATE + INTERVAL '7 days')
                OR v.km >= (m.km_programado - 500)
            )
            ORDER BY m.fecha_programada ASC
        """
    else:
        # SQLite version
        query = """
            SELECT m.*, v.marca, v.modelo, v.km as km_actual 
            FROM programacion_mantenimiento m
            JOIN vehiculos v ON m.patente = v.patente
            WHERE m.estado = 'PENDIENTE'
            AND m.recordatorio_enviado = 0
            AND (
                m.fecha_programada <= date('now', '+7 days')
                OR v.km >= (m.km_programado - 500)
            )
            ORDER BY m.fecha_programada ASC
        """
    
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error al obtener recordatorios: {e}")
        return pd.DataFrame()

def get_vtv_proximos_vencer(dias=30):
    """Obtiene vehículos cuya VTV está próxima a vencer.
    
    Args:
        dias: Número de días hasta el vencimiento para considerar próximo
    
    Returns:
        DataFrame con los vehículos cuya VTV vence dentro de los próximos X días
    """
    engine = get_sqlalchemy_engine()
    
    # Consulta para obtener vehículos con VTV próxima a vencer
    # Usamos consulta más simple y menos restrictiva para asegurar que capturemos todas las VTVs próximas
    if USE_POSTGRES:
        query = f"""
            SELECT * FROM vehiculos
            WHERE vtv_vencimiento IS NOT NULL
            AND vtv_vencimiento != ''
            AND (TRY_CAST(vtv_vencimiento AS DATE) IS NOT NULL)
            AND CAST(vtv_vencimiento AS DATE) BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '{dias} days')
            ORDER BY vtv_vencimiento ASC
        """
    else:
        # SQLite version
        query = f"""
            SELECT * FROM vehiculos
            WHERE vtv_vencimiento IS NOT NULL
            AND vtv_vencimiento != ''
            AND date(vtv_vencimiento) <= date('now', '+{dias} days')
            AND date(vtv_vencimiento) >= date('now')
            ORDER BY vtv_vencimiento ASC
        """
    
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error al obtener vehículos con VTV próxima a vencer: {e}")
        return pd.DataFrame()

def send_email_notification(destinatario, asunto, mensaje):
    """Envía un correo electrónico para notificaciones.
    
    Args:
        destinatario: Dirección de correo electrónico del destinatario
        asunto: Asunto del correo
        mensaje: Texto del mensaje a enviar
    
    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Verificar si tenemos las credenciales de correo configuradas
        if not all(key in os.environ for key in ["EMAIL_HOST", "EMAIL_PORT", "EMAIL_USER", "EMAIL_PASSWORD"]):
            # No mostramos error en consola para no interrumpir el flujo si no está configurado
            return False
        
        # Configurar servidor de correo
        smtp_host = os.environ["EMAIL_HOST"]
        smtp_port = int(os.environ["EMAIL_PORT"])
        smtp_user = os.environ["EMAIL_USER"]
        smtp_password = os.environ["EMAIL_PASSWORD"]
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Agregar cuerpo del mensaje
        msg.attach(MIMEText(mensaje, 'html'))
        
        # Enviar correo
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        # Registramos el error pero no lo mostramos en la interfaz
        print(f"Error al enviar correo: {e}")
        return False

def process_maintenance_reminders(emails=None):
    """Procesa los recordatorios pendientes y envía correos electrónicos si es necesario.
    
    Args:
        emails: Lista opcional de direcciones de correo electrónico a notificar
                Si no se proporciona, no se enviarán correos pero se actualizará el estado de los recordatorios.
    
    Returns:
        tuple: (total_reminders, sent_email_count, failed_email_count)
    """
    # Obtener recordatorios pendientes
    reminders_df = get_maintenance_reminders()
    
    if reminders_df.empty:
        return 0, 0, 0  # No hay recordatorios pendientes
    
    sent_count = 0
    failed_count = 0
    
    for _, reminder in reminders_df.iterrows():
        # Marcar el recordatorio como enviado
        update_maintenance_schedule(
            reminder['id'],
            recordatorio_enviado=True
        )
        
        # Si tenemos emails configurados, enviar notificaciones
        if emails:
            patente = reminder['patente']
            vehicle = get_vehicle_by_patente(patente)
            
            # Construir asunto
            asunto = f"RECORDATORIO: Mantenimiento programado para vehículo {patente}"
            
            # Construir cuerpo del mensaje HTML
            mensaje = f"""
            <html>
            <body>
            <h2>Recordatorio de Mantenimiento</h2>
            <p>El vehículo <strong>{patente}</strong> ({reminder['marca']} {reminder['modelo']}) tiene mantenimiento programado.</p>
            
            <h3>Detalles:</h3>
            <ul>
            """
            
            # Agregar detalles según el tipo de recordatorio (fecha o km)
            if pd.notna(reminder['fecha_programada']):
                mensaje += f"<li>Tiene programado un service de tipo <strong>'{reminder['tipo_service']}'</strong> para el <strong>{reminder['fecha_programada']}</strong></li>"
            
            if pd.notna(reminder['km_programado']) and reminder['km_programado'] > 0:
                mensaje += f"<li>Debe realizarse un service al alcanzar <strong>{reminder['km_programado']} km</strong>. Actualmente: {reminder['km_actual']} km</li>"
            
            # Agregar área del vehículo si está disponible
            if vehicle and 'area' in vehicle and vehicle['area']:
                mensaje += f"<li>Área asignada: <strong>{vehicle['area']}</strong></li>"
                
            # Agregar descripción si existe
            if pd.notna(reminder['descripcion']) and reminder['descripcion']:
                mensaje += f"<li>Detalles adicionales: {reminder['descripcion']}</li>"
                
            mensaje += """
            </ul>
            <p>Este es un mensaje automático del Sistema de Gestión de Flota Vehicular.</p>
            </body>
            </html>
            """
                    
            # Enviar el correo a cada destinatario
            for email in emails:
                if send_email_notification(email, asunto, mensaje):
                    sent_count += 1
                else:
                    failed_count += 1
    
    return len(reminders_df), sent_count, failed_count

def mark_maintenance_completed(id_programacion, service_realizado=True):
    """Marca un mantenimiento programado como completado y opcionalmente crea un registro de servicio.
    
    Args:
        id_programacion: ID del mantenimiento programado
        service_realizado: Si es True, se registrará un servicio basado en la programación
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    # Obtener datos del mantenimiento programado
    engine = get_sqlalchemy_engine()
    
    if USE_POSTGRES:
        query = """
            SELECT m.*, v.km as km_actual 
            FROM programacion_mantenimiento m
            JOIN vehiculos v ON m.patente = v.patente
            WHERE m.id = %s
        """
        params = (id_programacion,)
    else:
        query = """
            SELECT m.*, v.km as km_actual 
            FROM programacion_mantenimiento m
            JOIN vehiculos v ON m.patente = v.patente
            WHERE m.id = ?
        """
        params = (id_programacion,)
    
    try:
        df = pd.read_sql(query, engine, params=params)
        if df.empty:
            st.error("No se encontró el mantenimiento programado")
            return False
        
        # Marcar como completado
        result = update_maintenance_schedule(
            id_programacion,
            estado="COMPLETADO"
        )
        
        # Si se solicita, crear registro de servicio
        if service_realizado and result:
            programacion = df.iloc[0]
            
            # Obtener fecha actual si la fecha programada es futura
            from datetime import datetime
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            
            fecha_service = fecha_actual if programacion['fecha_programada'] > fecha_actual else programacion['fecha_programada']
            
            # Agregar registro de servicio
            add_service_record(
                patente=programacion['patente'],
                fecha=fecha_service,
                km=programacion['km_actual'],
                tipo_service=programacion['tipo_service'],
                taller="",  # Por defecto vacío, se actualizará manualmente
                costo=0,    # Por defecto 0, se actualizará manualmente
                descripcion=programacion['descripcion']
            )
        
        return result
    except Exception as e:
        st.error(f"Error al completar mantenimiento: {e}")
        return False

def exportar_datos(tabla, formato='xlsx'):
    """Exporta datos de una tabla a un archivo.
    
    Args:
        tabla: Nombre de la tabla a exportar ('vehiculos', 'historial_service', 'incidentes', 'programacion_mantenimiento')
        formato: Formato de exportación ('xlsx', 'csv')
    
    Returns:
        bytes: Datos del archivo para descarga
    """
    engine = get_sqlalchemy_engine()
    
    try:
        # Determinar qué consulta ejecutar según la tabla solicitada
        if tabla == 'vehiculos':
            query = "SELECT * FROM vehiculos"
            filename = "vehiculos"
        elif tabla == 'historial_service':
            query = """
                SELECT s.*, v.marca, v.modelo, v.tipo
                FROM historial_service s
                JOIN vehiculos v ON s.patente = v.patente
                ORDER BY s.fecha DESC
            """
            filename = "historial_service"
        elif tabla == 'incidentes':
            query = """
                SELECT i.*, v.marca, v.modelo, v.tipo
                FROM incidentes i
                JOIN vehiculos v ON i.patente = v.patente
                ORDER BY i.fecha DESC
            """
            filename = "incidentes"
        elif tabla == 'programacion_mantenimiento':
            query = """
                SELECT m.*, v.marca, v.modelo, v.tipo, v.km as km_actual
                FROM programacion_mantenimiento m
                JOIN vehiculos v ON m.patente = v.patente
                ORDER BY m.fecha_programada ASC
            """
            filename = "mantenimientos_programados"
        else:
            raise ValueError(f"Tabla no reconocida: {tabla}")
        
        # Ejecutar consulta
        df = pd.read_sql(query, engine)
        
        # Exportar según formato solicitado
        if formato == 'xlsx':
            # Crear un buffer en memoria para el archivo Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=filename, index=False)
                # Ajustar ancho de columnas
                worksheet = writer.sheets[filename]
                for i, col in enumerate(df.columns):
                    max_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, max_width)
            
            output.seek(0)
            return output.getvalue()
            
        elif formato == 'csv':
            # Crear un buffer en memoria para el archivo CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            return output.getvalue().encode('utf-8')
        else:
            raise ValueError(f"Formato no soportado: {formato}")
    
    except Exception as e:
        st.error(f"Error al exportar datos: {str(e)}")
        return None

def enviar_reporte_por_email(email, titulo, mensaje_html, df=None, formato='xlsx', nombre_archivo=None):
    """Envía un reporte por correo electrónico, opcionalmente con un archivo adjunto.
    
    Args:
        email: Dirección de correo del destinatario
        titulo: Asunto del correo
        mensaje_html: Cuerpo del mensaje en formato HTML
        df: DataFrame opcional para adjuntar
        formato: Formato del archivo adjunto ('xlsx', 'csv')
        nombre_archivo: Nombre para el archivo adjunto
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        
        # Verificar si tenemos las credenciales de correo configuradas
        if not all(key in os.environ for key in ["EMAIL_HOST", "EMAIL_PORT", "EMAIL_USER", "EMAIL_PASSWORD"]):
            return False
            
        # Configurar servidor de correo
        smtp_host = os.environ["EMAIL_HOST"]
        smtp_port = int(os.environ["EMAIL_PORT"])
        smtp_user = os.environ["EMAIL_USER"]
        smtp_password = os.environ["EMAIL_PASSWORD"]
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = titulo
        
        # Agregar cuerpo del mensaje
        msg.attach(MIMEText(mensaje_html, 'html'))
        
        # Si hay un DataFrame para adjuntar
        if df is not None and not df.empty:
            if nombre_archivo is None:
                nombre_archivo = "reporte"
                
            # Preparar archivo según formato
            if formato == 'xlsx':
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name="Reporte", index=False)
                data = output.getvalue()
                filename = f"{nombre_archivo}.xlsx"
                mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:  # csv
                csv_data = df.to_csv(index=False)
                data = csv_data.encode('utf-8')
                filename = f"{nombre_archivo}.csv"
                mimetype = "text/csv"
                
            # Adjuntar archivo
            attachment = MIMEApplication(data)
            attachment["Content-Disposition"] = f'attachment; filename="{filename}"'
            attachment["Content-Type"] = f'{mimetype}; name="{filename}"'
            msg.attach(attachment)
        
        # Enviar correo
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        return True
    except Exception as e:
        print(f"Error al enviar reporte por email: {e}")
        return False