import os
from turtle import st
import pandas as pd
import numpy as np
import io
import json
import base64
import re
import sqlite3
import traceback
from io import StringIO, BytesIO
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from logger import get_logger, log_exception
from validators import sanitizar_input, validar_patente, validar_entero_positivo, validar_fecha
from cache_manager import cached

# Configurar logger para este módulo
logger = get_logger('database')

# Detectar automáticamente si debemos usar la versión PostgreSQL o SQLite (standalone)
USE_POSTGRES = "DATABASE_URL" in os.environ
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Importar psycopg2 solo si estamos usando PostgreSQL
if USE_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        logger.info("Usando PostgreSQL como base de datos")
    except ImportError:
        logger.error("Error al importar psycopg2, revise que esté instalado correctamente")
else:
    # Si no hay PostgreSQL, usamos la versión SQLite (standalone)
    logger.info("DATABASE_URL no encontrada, usando SQLite en modo standalone")

def get_database_path():
    """Get the path to the SQLite database file."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "flota_vehicular.db")

def init_database():
    """Initialize the database and create tables if they don't exist."""
    try:
        if USE_POSTGRES:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Crear tabla de vehículos
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
            
            # Crear tabla de historial de service
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_service (
                    id SERIAL PRIMARY KEY,
                    patente TEXT REFERENCES vehiculos(patente),
                    fecha TEXT,
                    km INTEGER,
                    tipo_service TEXT,
                    taller TEXT,
                    costo REAL,
                    descripcion TEXT,
                    pdf_files TEXT
                )
            ''')
            
            # Crear tabla de incidentes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS incidentes (
                    id SERIAL PRIMARY KEY,
                    patente TEXT REFERENCES vehiculos(patente),
                    fecha TEXT,
                    tipo TEXT,
                    descripcion TEXT,
                    estado TEXT,
                    pdf_files TEXT
                )
            ''')
            
            # Crear tabla de programación de mantenimiento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS programacion_mantenimiento (
                    id SERIAL PRIMARY KEY,
                    patente TEXT REFERENCES vehiculos(patente),
                    fecha_programada TEXT,
                    km_programado INTEGER,
                    tipo_service TEXT,
                    descripcion TEXT,
                    estado TEXT DEFAULT 'PENDIENTE',
                    recordatorio_enviado BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Base de datos PostgreSQL inicializada correctamente")
            
        else:
            # Usar SQLite para la versión standalone
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Crear tabla de vehículos
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
            
            # Crear tabla de historial de service
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_service (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patente TEXT REFERENCES vehiculos(patente),
                    fecha TEXT,
                    km INTEGER,
                    tipo_service TEXT,
                    taller TEXT,
                    costo REAL,
                    descripcion TEXT,
                    pdf_files TEXT
                )
            ''')
            
            # Crear tabla de incidentes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS incidentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patente TEXT REFERENCES vehiculos(patente),
                    fecha TEXT,
                    tipo TEXT,
                    descripcion TEXT,
                    estado TEXT,
                    pdf_files TEXT
                )
            ''')
            
            # Crear tabla de programación de mantenimiento
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS programacion_mantenimiento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patente TEXT REFERENCES vehiculos(patente),
                    fecha_programada TEXT,
                    km_programado INTEGER,
                    tipo_service TEXT,
                    descripcion TEXT,
                    estado TEXT DEFAULT 'PENDIENTE',
                    recordatorio_enviado BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Base de datos SQLite inicializada correctamente en {db_path}")
        
        return True
    except Exception as e:
        log_exception(logger, e, "Error al inicializar la base de datos")
        return False

def get_connection():
    """Get a database connection."""
    try:
        if USE_POSTGRES:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        else:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            # Configurar SQLite para devolver filas como diccionarios
            conn.row_factory = sqlite3.Row
            return conn
    except Exception as e:
        log_exception(logger, e, "Error al obtener conexión a la base de datos")
        raise

def get_sqlalchemy_engine():
    """Get a SQLAlchemy engine."""
    try:
        if USE_POSTGRES:
            return create_engine(DATABASE_URL)
        else:
            db_path = get_database_path()
            return create_engine(f"sqlite:///{db_path}")
    except Exception as e:
        log_exception(logger, e, "Error al crear engine de SQLAlchemy")
        raise

@cached(ttl=300)  # Caché de 5 minutos
def load_vehicles(search_term=None):
    """
    Load all vehicles from the database with optional search filter.
    
    Args:
        search_term: Optional search term to filter vehicles
    
    Returns:
        DataFrame: Vehicles data
    """
    try:
        # Sanitizar término de búsqueda para prevenir inyección SQL
        if search_term:
            search_term = sanitizar_input(search_term)
        
        engine = get_sqlalchemy_engine()
        
        # Consulta base
        query = "SELECT * FROM vehiculos"
        
        # Añadir filtro de búsqueda si se proporciona
        if search_term and search_term.strip():
            # Usando parámetros con SQLAlchemy para prevenir inyección SQL
            like_term = f"%{search_term}%"
            if USE_POSTGRES:
                query += " WHERE patente ILIKE :term OR area ILIKE :term OR marca ILIKE :term OR modelo ILIKE :term"
                vehicles = pd.read_sql(text(query), engine, params={"term": like_term})
            else:
                query += " WHERE patente LIKE :term OR area LIKE :term OR marca LIKE :term OR modelo LIKE :term"
                vehicles = pd.read_sql(text(query), engine, params={"term": like_term})
        else:
            vehicles = pd.read_sql(query, engine)
        
        return vehicles
    except Exception as e:
        log_exception(logger, e, "Error al cargar vehículos")
        return pd.DataFrame()

def add_vehicle(patente, area, tipo, marca, modelo, año, estado, km=0, fecha_service=None, taller=None, 
               observaciones=None, pdf_files=None, rori=None, id_vehiculo=None, vtv_vencimiento=None):
    """
    Add a new vehicle to the database.
    
    Args:
        patente: License plate (primary key)
        area: Department or area
        tipo: Vehicle type
        marca: Vehicle brand
        modelo: Vehicle model
        año: Manufacturing year
        estado: Current status
        km: Current mileage
        fecha_service: Last service date
        taller: Last service workshop
        observaciones: Notes
        pdf_files: JSON string with attached PDF files
        rori: RORI identification number
        id_vehiculo: Vehicle ID
        vtv_vencimiento: VTV expiration date
    
    Returns:
        bool: True if vehicle was added successfully
    """
    try:
        # Validar datos críticos
        valido, mensaje = validar_patente(patente)
        if not valido:
            logger.warning(f"Patente inválida: {patente} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validar año
        valido, mensaje = validar_entero_positivo(año, 1950, datetime.now().year)
        if not valido:
            logger.warning(f"Año inválido: {año} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validar km
        valido, mensaje = validar_entero_positivo(km, 0, None, False)
        if not valido:
            logger.warning(f"Kilometraje inválido: {km} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validar id_vehiculo si está presente
        if id_vehiculo:
            valido, mensaje = validar_entero_positivo(id_vehiculo, 0, None, False)
            if not valido:
                logger.warning(f"ID de vehículo inválido: {id_vehiculo} - {mensaje}")
                st.error(mensaje)
                return False
        
        # Sanitizar campos de texto
        area = sanitizar_input(area)
        tipo = sanitizar_input(tipo)
        marca = sanitizar_input(marca)
        modelo = sanitizar_input(modelo)
        estado = sanitizar_input(estado)
        taller = sanitizar_input(taller) if taller else None
        observaciones = sanitizar_input(observaciones) if observaciones else None
        rori = sanitizar_input(rori) if rori else None
        
        # Validar fechas
        if fecha_service:
            valido, mensaje = validar_fecha(fecha_service, False)
            if not valido:
                logger.warning(f"Fecha de service inválida: {fecha_service} - {mensaje}")
                st.error(mensaje)
                return False
        
        if vtv_vencimiento:
            valido, mensaje = validar_fecha(vtv_vencimiento, False)
            if not valido:
                logger.warning(f"Fecha de vencimiento VTV inválida: {vtv_vencimiento} - {mensaje}")
                st.error(mensaje)
                return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existe un vehículo con la misma patente
        if USE_POSTGRES:
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = %s", (patente,))
        else:
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = ?", (patente,))
        
        if cursor.fetchone():
            conn.close()
            logger.warning(f"Intento de agregar vehículo con patente duplicada: {patente}")
            st.error(f"Ya existe un vehículo con la patente {patente}")
            return False
        
        # Preparar la consulta usando la forma segura con parámetros
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO vehiculos (patente, area, tipo, marca, modelo, año, estado, km, 
                                     fecha_service, taller, observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, 
                observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento))
        else:
            cursor.execute('''
                INSERT INTO vehiculos (patente, area, tipo, marca, modelo, año, estado, km, 
                                     fecha_service, taller, observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patente, area, tipo, marca, modelo, año, estado, km, fecha_service, taller, 
                observaciones, pdf_files, rori, id_vehiculo, vtv_vencimiento))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Vehículo agregado correctamente: {patente}")
        return True
        
    except Exception as e:
        log_exception(logger, e, "Error al agregar vehículo")
        st.error(f"Error al agregar vehículo: {str(e)}")
        return False

def update_vehicle(patente, **kwargs):
    """
    Update vehicle information.
    
    Args:
        patente: License plate of the vehicle to update
        **kwargs: Fields to update with their new values
    
    Returns:
        bool: True if vehicle was updated successfully
    """
    try:
        # Validar patente
        valido, mensaje = validar_patente(patente)
        if not valido:
            logger.warning(f"Patente inválida en actualización: {patente} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validaciones específicas para campos críticos
        if 'año' in kwargs:
            valido, mensaje = validar_entero_positivo(kwargs['año'], 1950, datetime.now().year)
            if not valido:
                logger.warning(f"Año inválido en actualización: {kwargs['año']} - {mensaje}")
                st.error(mensaje)
                return False
        
        if 'km' in kwargs:
            valido, mensaje = validar_entero_positivo(kwargs['km'], 0, None, False)
            if not valido:
                logger.warning(f"Kilometraje inválido en actualización: {kwargs['km']} - {mensaje}")
                st.error(mensaje)
                return False
        
        if 'id_vehiculo' in kwargs and kwargs['id_vehiculo']:
            valido, mensaje = validar_entero_positivo(kwargs['id_vehiculo'], 0, None, False)
            if not valido:
                logger.warning(f"ID de vehículo inválido en actualización: {kwargs['id_vehiculo']} - {mensaje}")
                st.error(mensaje)
                return False
        
        # Validar fechas
        if 'fecha_service' in kwargs and kwargs['fecha_service']:
            valido, mensaje = validar_fecha(kwargs['fecha_service'], False)
            if not valido:
                logger.warning(f"Fecha de service inválida en actualización: {kwargs['fecha_service']} - {mensaje}")
                st.error(mensaje)
                return False
        
        if 'vtv_vencimiento' in kwargs and kwargs['vtv_vencimiento']:
            valido, mensaje = validar_fecha(kwargs['vtv_vencimiento'], False)
            if not valido:
                logger.warning(f"Fecha de vencimiento VTV inválida en actualización: {kwargs['vtv_vencimiento']} - {mensaje}")
                st.error(mensaje)
                return False
        
        # Sanitizar todos los valores de texto
        for key, value in list(kwargs.items()):
            if isinstance(value, str) and key not in ['pdf_files']:  # No sanitizar JSON de PDFs
                kwargs[key] = sanitizar_input(value)
        
        # Preparar la consulta de actualización
        fields = []
        values = []
        
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        # Añadir patente al final de los valores para la condición WHERE
        values.append(patente)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si existe el vehículo
        if USE_POSTGRES:
            # Adaptar campos para PostgreSQL
            fields = [f.replace('?', '%s') for f in fields]
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = %s", (patente,))
        else:
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = ?", (patente,))
        
        if not cursor.fetchone():
            conn.close()
            logger.warning(f"Intento de actualizar vehículo inexistente: {patente}")
            st.error(f"No existe un vehículo con la patente {patente}")
            return False
        
        # Ejecutar la actualización
        query = f"UPDATE vehiculos SET {', '.join(fields)} WHERE patente = ?"
        
        if USE_POSTGRES:
            query = query.replace('?', '%s')
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        logger.info(f"Vehículo actualizado correctamente: {patente}")
        return True
        
    except Exception as e:
        log_exception(logger, e, "Error al actualizar vehículo")
        st.error(f"Error al actualizar vehículo: {str(e)}")
        return False

def delete_vehicle(patente):
    """
    Delete a vehicle from the database.
    
    Args:
        patente: License plate of the vehicle to delete
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Validar patente
        valido, mensaje = validar_patente(patente)
        if not valido:
            logger.warning(f"Patente inválida en eliminación: {patente} - {mensaje}")
            return False, mensaje
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si hay registros relacionados
        related_records = {}
        
        # Verificar historial de service
        if USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM historial_service WHERE patente = %s", (patente,))
        else:
            cursor.execute("SELECT COUNT(*) FROM historial_service WHERE patente = ?", (patente,))
        
        service_count = cursor.fetchone()[0]
        if service_count > 0:
            related_records['historial_service'] = service_count
        
        # Verificar incidentes
        if USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM incidentes WHERE patente = %s", (patente,))
        else:
            cursor.execute("SELECT COUNT(*) FROM incidentes WHERE patente = ?", (patente,))
        
        incidentes_count = cursor.fetchone()[0]
        if incidentes_count > 0:
            related_records['incidentes'] = incidentes_count
        
        # Verificar programación de mantenimiento
        if USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM programacion_mantenimiento WHERE patente = %s", (patente,))
        else:
            cursor.execute("SELECT COUNT(*) FROM programacion_mantenimiento WHERE patente = ?", (patente,))
        
        mant_count = cursor.fetchone()[0]
        if mant_count > 0:
            related_records['programacion_mantenimiento'] = mant_count
        
        # Si hay registros relacionados, mostrar error detallado
        if related_records:
            conn.close()
            
            mensaje = f"No se puede eliminar el vehículo {patente} porque tiene registros relacionados:\n"
            if 'historial_service' in related_records:
                mensaje += f"- {related_records['historial_service']} registros de servicio\n"
            if 'incidentes' in related_records:
                mensaje += f"- {related_records['incidentes']} incidentes\n"
            if 'programacion_mantenimiento' in related_records:
                mensaje += f"- {related_records['programacion_mantenimiento']} mantenimientos programados\n"
            
            mensaje += "\nDebe eliminar estos registros antes de eliminar el vehículo."
            logger.warning(f"Eliminación rechazada - vehículo con registros relacionados: {patente}")
            
            return False, mensaje
        
        # Eliminar el vehículo
        if USE_POSTGRES:
            cursor.execute("DELETE FROM vehiculos WHERE patente = %s", (patente,))
        else:
            cursor.execute("DELETE FROM vehiculos WHERE patente = ?", (patente,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Vehículo eliminado correctamente: {patente}")
        return True, f"Vehículo {patente} eliminado correctamente."
        
    except Exception as e:
        log_exception(logger, e, "Error al eliminar vehículo")
        return False, f"Error al eliminar vehículo: {str(e)}"

@cached(ttl=300)  # Caché de 5 minutos
def get_vehicle_by_patente(patente):
    """
    Get a vehicle by its license plate number.
    
    Args:
        patente: License plate number
    
    Returns:
        dict: Vehicle data or None if not found
    """
    try:
        # Validar patente
        valido, mensaje = validar_patente(patente)
        if not valido:
            logger.warning(f"Patente inválida en consulta: {patente} - {mensaje}")
            return None
        
        conn = get_connection()
        
        if USE_POSTGRES:
            # Usar cursor con diccionario para PostgreSQL
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM vehiculos WHERE patente = %s", (patente,))
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehiculos WHERE patente = ?", (patente,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Para SQLite con Row factory
            if not USE_POSTGRES:
                # Convertir Row a diccionario
                result = dict(result)
            
            return result
        return None
        
    except Exception as e:
        log_exception(logger, e, f"Error al obtener vehículo por patente: {patente}")
        return None

def add_service_record(patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files=None):
    """
    Add a new service record for a vehicle.
    
    Args:
        patente: License plate of the vehicle
        fecha: Service date
        km: Current mileage
        tipo_service: Type of service
        taller: Workshop name
        costo: Service cost
        descripcion: Service description
        pdf_files: JSON string with attached PDF files
    
    Returns:
        bool: True if record was added successfully
    """
    try:
        # Validar patente
        valido, mensaje = validar_patente(patente)
        if not valido:
            logger.warning(f"Patente inválida en registro de servicio: {patente} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validar fecha
        valido, mensaje = validar_fecha(fecha)
        if not valido:
            logger.warning(f"Fecha inválida en registro de servicio: {fecha} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validar km
        valido, mensaje = validar_entero_positivo(km, 0)
        if not valido:
            logger.warning(f"Kilometraje inválido en registro de servicio: {km} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validar costo
        try:
            costo = float(costo)
            if costo < 0:
                logger.warning(f"Costo negativo en registro de servicio: {costo}")
                st.error("El costo no puede ser negativo")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Costo inválido en registro de servicio: {costo}")
            st.error("El costo debe ser un número válido")
            return False
        
        # Sanitizar campos de texto
        tipo_service = sanitizar_input(tipo_service)
        taller = sanitizar_input(taller)
        descripcion = sanitizar_input(descripcion)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si existe el vehículo
        if USE_POSTGRES:
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = %s", (patente,))
        else:
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = ?", (patente,))
        
        if not cursor.fetchone():
            conn.close()
            logger.warning(f"Intento de agregar servicio a vehículo inexistente: {patente}")
            st.error(f"No existe un vehículo con la patente {patente}")
            return False
        
        # Insertar registro de servicio
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO historial_service (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files))
        else:
            cursor.execute('''
                INSERT INTO historial_service (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patente, fecha, km, tipo_service, taller, costo, descripcion, pdf_files))
        
        # Actualizar km y fecha último service del vehículo
        if USE_POSTGRES:
            cursor.execute('''
                UPDATE vehiculos SET km = %s, fecha_service = %s, taller = %s
                WHERE patente = %s
            ''', (km, fecha, taller, patente))
        else:
            cursor.execute('''
                UPDATE vehiculos SET km = ?, fecha_service = ?, taller = ?
                WHERE patente = ?
            ''', (km, fecha, taller, patente))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Registro de servicio agregado correctamente para: {patente}")
        return True
        
    except Exception as e:
        log_exception(logger, e, "Error al agregar registro de servicio")
        st.error(f"Error al agregar registro de servicio: {str(e)}")
        return False

def add_incident(patente, fecha, tipo, descripcion, estado, pdf_files=None):
    """
    Add a new incident record.
    
    Args:
        patente: License plate of the vehicle
        fecha: Incident date
        tipo: Type of incident
        descripcion: Incident description
        estado: Current status of the incident
        pdf_files: JSON string with attached PDF files
    
    Returns:
        bool: True if record was added successfully
    """
    try:
        # Validar patente
        valido, mensaje = validar_patente(patente)
        if not valido:
            logger.warning(f"Patente inválida en registro de incidente: {patente} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Validar fecha
        valido, mensaje = validar_fecha(fecha)
        if not valido:
            logger.warning(f"Fecha inválida en registro de incidente: {fecha} - {mensaje}")
            st.error(mensaje)
            return False
        
        # Sanitizar campos de texto
        tipo = sanitizar_input(tipo)
        descripcion = sanitizar_input(descripcion)
        estado = sanitizar_input(estado)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si existe el vehículo
        if USE_POSTGRES:
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = %s", (patente,))
        else:
            cursor.execute("SELECT patente FROM vehiculos WHERE patente = ?", (patente,))
        
        if not cursor.fetchone():
            conn.close()
            logger.warning(f"Intento de agregar incidente a vehículo inexistente: {patente}")
            st.error(f"No existe un vehículo con la patente {patente}")
            return False
        
        # Insertar registro de incidente
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO incidentes (patente, fecha, tipo, descripcion, estado, pdf_files)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (patente, fecha, tipo, descripcion, estado, pdf_files))
        else:
            cursor.execute('''
                INSERT INTO incidentes (patente, fecha, tipo, descripcion, estado, pdf_files)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (patente, fecha, tipo, descripcion, estado, pdf_files))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Incidente registrado correctamente para: {patente}")
        return True
        
    except Exception as e:
        log_exception(logger, e, "Error al agregar incidente")
        st.error(f"Error al agregar incidente: {str(e)}")
        return False

@cached(ttl=300)  # Caché de 5 minutos
def get_service_history(patente=None):
    """
    Get service history for a specific vehicle or all vehicles.
    
    Args:
        patente: Optional license plate to filter by vehicle
    
    Returns:
        DataFrame: Service history records
    """
    try:
        engine = get_sqlalchemy_engine()
        
        # Consulta base con join para obtener datos del vehículo
        query = """
            SELECT s.*, v.marca, v.modelo, v.tipo, v.area
            FROM historial_service s
            JOIN vehiculos v ON s.patente = v.patente
        """
        
        # Añadir filtro por patente si se proporciona
        if patente:
            # Validar patente
            valido, mensaje = validar_patente(patente)
            if not valido:
                logger.warning(f"Patente inválida en consulta de historial: {patente} - {mensaje}")
                return pd.DataFrame()
            
            # Usar parámetros con SQLAlchemy para prevenir inyección SQL
            query += " WHERE s.patente = :patente"
            params = {"patente": patente}
            history = pd.read_sql(text(query), engine, params=params)
        else:
            history = pd.read_sql(query, engine)
        
        # Ordenar por fecha descendente
        if not history.empty:
            history['fecha'] = pd.to_datetime(history['fecha'], errors='coerce')
            history = history.sort_values('fecha', ascending=False)
        
        return history
        
    except Exception as e:
        log_exception(logger, e, "Error al obtener historial de servicio")
        return pd.DataFrame()

@cached(ttl=300)  # Caché de 5 minutos
def get_incidents(patente=None, estado=None):
    """
    Get incidents for a specific vehicle or all vehicles, optionally filtered by status.
    
    Args:
        patente: Optional license plate to filter by vehicle
        estado: Optional status to filter incidents
    
    Returns:
        DataFrame: Incident records
    """
    try:
        engine = get_sqlalchemy_engine()
        
        # Consulta base con join para obtener datos del vehículo
        query = """
            SELECT i.*, v.marca, v.modelo, v.tipo, v.area
            FROM incidentes i
            JOIN vehiculos v ON i.patente = v.patente
        """
        
        params = {}
        where_clauses = []
        
        # Añadir filtro por patente si se proporciona
        if patente:
            # Validar patente
            valido, mensaje = validar_patente(patente)
            if not valido:
                logger.warning(f"Patente inválida en consulta de incidentes: {patente} - {mensaje}")
                return pd.DataFrame()
            
            where_clauses.append("i.patente = :patente")
            params["patente"] = patente
        
        # Añadir filtro por estado si se proporciona
        if estado:
            estado = sanitizar_input(estado)
            where_clauses.append("i.estado = :estado")
            params["estado"] = estado
        
        # Completar la consulta con WHERE si hay filtros
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Ejecutar consulta con o sin parámetros
        if params:
            incidents = pd.read_sql(text(query), engine, params=params)
        else:
            incidents = pd.read_sql(query, engine)
        
        # Ordenar por fecha descendente
        if not incidents.empty:
            incidents['fecha'] = pd.to_datetime(incidents['fecha'], errors='coerce')
            incidents = incidents.sort_values('fecha', ascending=False)
        
        return incidents
        
    except Exception as e:
        log_exception(logger, e, "Error al obtener incidentes")
        return pd.DataFrame()

# Resto de funciones de database.py con mejoras similares...

# Las funciones restantes se implementarían siguiendo el mismo patrón de
# validación, sanitización y uso de parámetros seguros para prevenir inyección SQL.