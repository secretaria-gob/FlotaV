import os
import sqlite3
import shutil
import zipfile
import datetime
import uuid
import pandas as pd
import streamlit as st
from logger import get_logger

# Configurar logger
logger = get_logger('backup_manager')

# Directorio para backups
BACKUP_DIR = os.path.join(os.getcwd(), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

def crear_backup_sqlite(db_path):
    """
    Crea un backup completo de la base de datos SQLite.
    
    Args:
        db_path: Ruta al archivo de base de datos SQLite
    
    Returns:
        tuple: (éxito, ruta_backup o mensaje_error)
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(db_path):
            return False, f"No se encontró el archivo de base de datos en {db_path}"
        
        # Generar nombre de archivo único para el backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Hacer una copia completa del archivo
        shutil.copy2(db_path, backup_path)
        
        # Crear archivo de metadatos
        metadata = {
            'timestamp': timestamp,
            'source_db': db_path,
            'backup_path': backup_path,
            'description': f"Backup completo creado el {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # Guardar metadatos
        metadata_path = backup_path + '.meta'
        with open(metadata_path, 'w') as f:
            for key, value in metadata.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"Backup creado exitosamente en {backup_path}")
        return True, backup_path
    
    except Exception as e:
        logger.error(f"Error al crear backup: {str(e)}")
        return False, f"Error al crear backup: {str(e)}"

def restaurar_backup_sqlite(backup_path, db_path):
    """
    Restaura un backup de la base de datos SQLite.
    
    Args:
        backup_path: Ruta al archivo de backup
        db_path: Ruta al archivo de base de datos a restaurar
    
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        # Verificar que el backup existe
        if not os.path.exists(backup_path):
            return False, f"No se encontró el archivo de backup en {backup_path}"
        
        # Crear copia de seguridad antes de restaurar (por si acaso)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safety_backup = os.path.join(BACKUP_DIR, f"pre_restore_{timestamp}.db")
        
        # Si existe la base de datos actual, hacer backup de seguridad
        if os.path.exists(db_path):
            shutil.copy2(db_path, safety_backup)
        
        # Detener conexiones activas (no podemos hacerlo programáticamente en Python)
        # En una aplicación real, esto requeriría detener servicios o cerrar conexiones
        
        # Restaurar el backup
        shutil.copy2(backup_path, db_path)
        
        logger.info(f"Backup restaurado exitosamente desde {backup_path}")
        return True, f"Backup restaurado exitosamente. Se creó una copia de seguridad en {safety_backup}"
    
    except Exception as e:
        logger.error(f"Error al restaurar backup: {str(e)}")
        return False, f"Error al restaurar backup: {str(e)}"

def listar_backups():
    """
    Lista todos los backups disponibles.
    
    Returns:
        list: Lista de diccionarios con información de cada backup
    """
    backups = []
    
    try:
        # Buscar archivos de backup
        for file in os.listdir(BACKUP_DIR):
            if file.startswith("backup_") and file.endswith(".db"):
                backup_path = os.path.join(BACKUP_DIR, file)
                metadata_path = backup_path + '.meta'
                
                # Extraer timestamp del nombre
                timestamp = file.replace("backup_", "").replace(".db", "")
                
                # Formatear fecha para mostrar
                try:
                    fecha = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    fecha_str = fecha.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    fecha_str = "Desconocida"
                    fecha = datetime.datetime.fromtimestamp(0)
                
                # Obtener tamaño
                size_bytes = os.path.getsize(backup_path)
                size_mb = size_bytes / (1024 * 1024)
                
                # Obtener descripción si existe
                description = ""
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        for line in f:
                            if line.startswith("description="):
                                description = line.replace("description=", "").strip()
                                break
                
                # Contar tablas y registros
                tablas = {}
                try:
                    conn = sqlite3.connect(backup_path)
                    cursor = conn.cursor()
                    
                    # Obtener lista de tablas
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    table_names = cursor.fetchall()
                    
                    for table in table_names:
                        table_name = table[0]
                        if table_name.startswith("sqlite_"):
                            continue
                        
                        # Contar registros
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        tablas[table_name] = count
                    
                    conn.close()
                except:
                    pass
                
                # Añadir información del backup
                backups.append({
                    'filename': file,
                    'path': backup_path,
                    'timestamp': timestamp,
                    'fecha': fecha,
                    'fecha_str': fecha_str,
                    'size_bytes': size_bytes,
                    'size_mb': size_mb,
                    'description': description,
                    'tablas': tablas
                })
        
        # Ordenar por fecha (más reciente primero)
        backups.sort(key=lambda x: x['fecha'], reverse=True)
        
        return backups
    
    except Exception as e:
        logger.error(f"Error al listar backups: {str(e)}")
        return []

def exportar_tablas_csv(db_path, directorio_destino=None):
    """
    Exporta todas las tablas de la base de datos a archivos CSV.
    
    Args:
        db_path: Ruta al archivo de base de datos SQLite
        directorio_destino: Directorio donde se guardarán los CSV (opcional)
    
    Returns:
        tuple: (éxito, ruta_zip o mensaje_error)
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(db_path):
            return False, f"No se encontró el archivo de base de datos en {db_path}"
        
        # Crear directorio temporal
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = os.path.join(BACKUP_DIR, f"temp_export_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        
        # Obtener lista de tablas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cursor.fetchall()
        
        # Exportar cada tabla
        for table in table_names:
            table_name = table[0]
            if table_name.startswith("sqlite_"):
                continue
            
            # Leer tabla como DataFrame
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            
            # Guardar como CSV
            csv_path = os.path.join(temp_dir, f"{table_name}.csv")
            df.to_csv(csv_path, index=False)
        
        conn.close()
        
        # Crear archivo ZIP con todos los CSV
        zip_name = f"export_{timestamp}.zip"
        zip_path = os.path.join(BACKUP_DIR, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir)
        
        logger.info(f"Exportación a CSV completada en {zip_path}")
        return True, zip_path
    
    except Exception as e:
        logger.error(f"Error al exportar tablas a CSV: {str(e)}")
        
        # Limpiar directorio temporal si existe
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        return False, f"Error al exportar tablas: {str(e)}"

def importar_desde_zip(zip_path, db_path):
    """
    Importa datos desde un archivo ZIP que contiene CSVs de tablas.
    
    Args:
        zip_path: Ruta al archivo ZIP con los CSVs
        db_path: Ruta al archivo de base de datos SQLite
    
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        # Verificar que el archivo ZIP existe
        if not os.path.exists(zip_path):
            return False, f"No se encontró el archivo ZIP en {zip_path}"
        
        # Crear directorio temporal para extraer
        temp_dir = os.path.join(BACKUP_DIR, f"temp_import_{uuid.uuid4().hex}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extraer ZIP
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Crear backup antes de importar
        success, backup_result = crear_backup_sqlite(db_path)
        if not success:
            return False, f"Error al crear backup antes de importar: {backup_result}"
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista para registrar resultados
        importados = []
        errores = []
        
        # Procesar cada CSV
        for file in os.listdir(temp_dir):
            if file.endswith(".csv"):
                table_name = os.path.splitext(file)[0]
                csv_path = os.path.join(temp_dir, file)
                
                try:
                    # Leer CSV
                    df = pd.read_csv(csv_path)
                    
                    # Verificar si la tabla existe
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                    table_exists = cursor.fetchone() is not None
                    
                    if table_exists:
                        # Verificar si hay datos en la tabla
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        
                        if count > 0:
                            # Si hay datos, truncar la tabla
                            cursor.execute(f"DELETE FROM {table_name}")
                    else:
                        # La tabla no existe, ignorar este CSV
                        errores.append(f"La tabla {table_name} no existe en la base de datos")
                        continue
                    
                    # Insertar datos
                    df.to_sql(table_name, conn, if_exists='append', index=False)
                    
                    importados.append(f"Tabla {table_name}: {len(df)} registros importados")
                    
                except Exception as e:
                    errores.append(f"Error al importar tabla {table_name}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir)
        
        # Generar mensaje de resultado
        resultado = f"Importación completada:\n- {len(importados)} tablas importadas\n"
        if errores:
            resultado += f"- {len(errores)} errores\n"
        
        logger.info(f"Importación completada desde {zip_path}")
        return True, resultado
    
    except Exception as e:
        logger.error(f"Error al importar desde ZIP: {str(e)}")
        
        # Limpiar directorio temporal si existe
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        return False, f"Error al importar desde ZIP: {str(e)}"

def interfaz_backup_sqlite(db_path):
    """
    Crea una interfaz de usuario para gestionar backups de la base de datos.
    Para ser usado en una sección de la aplicación Streamlit.
    
    Args:
        db_path: Ruta al archivo de base de datos SQLite
    """
    st.write("### Gestión de Copias de Seguridad")
    
    # Tabs para diferentes acciones
    tabs = st.tabs(["Crear Backup", "Restaurar Backup", "Exportar/Importar"])
    
    # Tab: Crear Backup
    with tabs[0]:
        st.write("Crea una copia de seguridad completa de la base de datos.")
        
        descripcion = st.text_area(
            "Descripción (opcional):",
            placeholder="Ej: Backup antes de importación masiva de vehículos",
            key="backup_description"
        )
        
        if st.button("Crear copia de seguridad", key="btn_crear_backup"):
            with st.spinner("Creando backup..."):
                success, result = crear_backup_sqlite(db_path)
                
                if success:
                    # Añadir descripción personalizada si se proporcionó
                    if descripcion:
                        metadata_path = result + '.meta'
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                lines = f.readlines()
                            
                            with open(metadata_path, 'w') as f:
                                for line in lines:
                                    if line.startswith("description="):
                                        f.write(f"description={descripcion}\n")
                                    else:
                                        f.write(line)
                    
                    st.success(f"Backup creado exitosamente en:\n{result}")
                else:
                    st.error(result)
        
        # Espacio adicional
        st.write("")
        
        # Lista de backups disponibles
        st.write("### Backups disponibles")
        backups = listar_backups()
        
        if not backups:
            st.info("No hay backups disponibles.")
        else:
            # Crear tabla con backups
            data = []
            for backup in backups:
                # Contar registros totales
                total_registros = sum(backup['tablas'].values())
                
                data.append({
                    "Fecha": backup['fecha_str'],
                    "Tamaño": f"{backup['size_mb']:.2f} MB",
                    "Tablas": len(backup['tablas']),
                    "Registros": total_registros,
                    "Descripción": backup['description']
                })
            
            # Mostrar como dataframe
            st.dataframe(pd.DataFrame(data), use_container_width=True)
    
    # Tab: Restaurar Backup
    with tabs[1]:
        st.write("Restaura la base de datos desde una copia de seguridad previa.")
        st.warning("⚠️ Esta acción sobrescribirá los datos actuales. Asegúrese de tener una copia de seguridad reciente.")
        
        backups = listar_backups()
        if not backups:
            st.info("No hay backups disponibles para restaurar.")
        else:
            # Opciones de backup para seleccionar
            opciones = [f"{b['fecha_str']} - {b['size_mb']:.2f} MB - {b['description'][:50]}..." for b in backups]
            seleccion = st.selectbox("Seleccione backup a restaurar:", [""] + opciones)
            
            if seleccion:
                idx = opciones.index(seleccion)
                backup = backups[idx]
                
                # Mostrar detalles del backup seleccionado
                st.write("### Detalles del backup seleccionado")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Fecha:** {backup['fecha_str']}")
                    st.write(f"**Tamaño:** {backup['size_mb']:.2f} MB")
                
                with col2:
                    st.write(f"**Tablas:** {len(backup['tablas'])}")
                    st.write(f"**Registros totales:** {sum(backup['tablas'].values())}")
                
                st.write(f"**Descripción:** {backup['description']}")
                
                # Mostrar contenido de tablas
                with st.expander("Ver contenido de tablas"):
                    for tabla, count in backup['tablas'].items():
                        st.write(f"- **{tabla}:** {count} registros")
                
                # Confirmación adicional
                confirmar = st.checkbox("Confirmo que quiero restaurar este backup y sobrescribir los datos actuales", key="confirm_restore")
                
                if confirmar and st.button("Restaurar backup", key="btn_restore_backup"):
                    with st.spinner("Restaurando backup..."):
                        success, message = restaurar_backup_sqlite(backup['path'], db_path)
                        
                        if success:
                            st.success(message)
                            st.info("Es necesario reiniciar la aplicación para ver los cambios.")
                            
                            if st.button("Reiniciar aplicación", key="btn_restart_after_restore"):
                                st.rerun()
                        else:
                            st.error(message)
    
    # Tab: Exportar/Importar
    with tabs[2]:
        st.write("### Exportar datos a CSV")
        st.write("Exporta todas las tablas a archivos CSV comprimidos en un ZIP.")
        
        if st.button("Exportar datos a CSV", key="btn_export_csv"):
            with st.spinner("Exportando datos..."):
                success, result = exportar_tablas_csv(db_path)
                
                if success:
                    # Ofrecer descarga
                    with open(result, "rb") as f:
                        data = f.read()
                    
                    st.success("Exportación completada.")
                    st.download_button(
                        label="Descargar archivo ZIP",
                        data=data,
                        file_name=os.path.basename(result),
                        mime="application/zip"
                    )
                else:
                    st.error(result)
        
        st.write("### Importar datos desde CSV")
        st.write("Importa datos desde un archivo ZIP que contiene CSVs de tablas.")
        st.warning("⚠️ Esta acción sobrescribirá los datos actuales en las tablas importadas.")
        
        uploaded_file = st.file_uploader("Seleccionar archivo ZIP", type="zip", key="upload_zip_import")
        
        if uploaded_file:
            # Guardar archivo temporal
            temp_zip = os.path.join(BACKUP_DIR, f"temp_import_{uuid.uuid4().hex}.zip")
            with open(temp_zip, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Verificar y mostrar contenido
            try:
                with zipfile.ZipFile(temp_zip, 'r') as zipf:
                    csv_files = [f for f in zipf.namelist() if f.endswith('.csv')]
                
                if not csv_files:
                    st.error("El archivo ZIP no contiene archivos CSV.")
                else:
                    st.write(f"El archivo contiene {len(csv_files)} tablas:")
                    for csv in csv_files:
                        st.write(f"- {os.path.basename(csv)}")
                    
                    # Confirmar importación
                    confirmar = st.checkbox("Confirmo que quiero importar estos datos y sobrescribir los actuales", key="confirm_import")
                    
                    if confirmar and st.button("Importar datos", key="btn_import_csv"):
                        with st.spinner("Importando datos..."):
                            success, message = importar_desde_zip(temp_zip, db_path)
                            
                            if success:
                                st.success(message)
                                st.info("Es necesario reiniciar la aplicación para ver los cambios.")
                                
                                if st.button("Reiniciar aplicación", key="btn_restart_after_import"):
                                    st.rerun()
                            else:
                                st.error(message)
            
            except Exception as e:
                st.error(f"Error al procesar el archivo ZIP: {str(e)}")
                
                # Limpiar archivo temporal
                if os.path.exists(temp_zip):
                    os.remove(temp_zip)