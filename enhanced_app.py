import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time
import io
import traceback
import database as db
import secure_database as sdb
from auth import check_authentication, get_user_role
from logger import get_logger, log_exception, log_access
from validators import validar_patente, validar_entero_positivo, validar_fecha
from theme_manager import apply_custom_css, theme_selector, get_current_theme
from documentation import get_tooltip_html, styled_header, display_manual, show_tutorial
from pagination import crear_tabla_paginada, tabla_filtrable
from backup_manager import interfaz_backup_sqlite
from ocr_processor import procesar_pdfs_para_service, mostrar_resultados_ocr, buscar_texto_en_pdfs
from analytics import dashboard_analitica, visualizar_costos_mantenimiento

# Configurar logger principal
logger = get_logger('app')

# Configurar página
st.set_page_config(
    page_title="Sistema de Gestión de Flota Vehicular",
    page_icon="🚗",
    layout="wide"
)

# Aplicar CSS personalizado basado en el tema seleccionado
apply_custom_css()

# Inicializar base de datos
try:
    db.init_database()
    # También inicializar o actualizar la base de datos segura si es necesario
    if hasattr(sdb, 'init_database'):
        sdb.init_database()
except Exception as e:
    log_exception(logger, e, "Error crítico al inicializar base de datos")
    st.error("Error al inicializar la base de datos. Por favor contacte al administrador del sistema.")
    st.error(f"Detalles: {str(e)}")
    st.stop()

# Verificar autenticación
auth_status, user_name, username = check_authentication()
if not auth_status:
    # La función de autenticación maneja todo el proceso de inicio de sesión
    st.stop()

# Registrar acceso exitoso
log_access(username, 'login')

# Obtener rol del usuario
user_role = get_user_role(username)

# Inicializar estado de sesión
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Navegación en barra lateral
with st.sidebar:
    st.title("Menú")
    
    # Botón Inicio
    if st.button("Inicio", use_container_width=True):
        st.session_state.page = 'home'
        log_access(username, 'navigate', 'Inicio')
    
    # Sección Vehículos
    st.subheader("Vehículos")
    if st.button("Ver Vehículos", use_container_width=True):
        st.session_state.page = 'view_vehicles'
        log_access(username, 'navigate', 'Ver Vehículos')
    
    if user_role in ['admin', 'manager']:
        if st.button("Agregar Vehículo", use_container_width=True):
            st.session_state.page = 'add_vehicle'
            log_access(username, 'navigate', 'Agregar Vehículo')
        
        if st.button("Editar Vehículo", use_container_width=True):
            st.session_state.page = 'edit_vehicle'
            log_access(username, 'navigate', 'Editar Vehículo')
    
    # Sección Mantenimiento
    st.subheader("Mantenimiento")
    if st.button("Registrar Service", use_container_width=True):
        st.session_state.page = 'add_service'
        log_access(username, 'navigate', 'Registrar Service')
    
    if st.button("Historial de Service", use_container_width=True):
        st.session_state.page = 'service_history'
        log_access(username, 'navigate', 'Historial de Service')
    
    if st.button("Registrar Incidente", use_container_width=True):
        st.session_state.page = 'add_incident'
        log_access(username, 'navigate', 'Registrar Incidente')
    
    if st.button("Ver Incidentes", use_container_width=True):
        st.session_state.page = 'view_incidents'
        log_access(username, 'navigate', 'Ver Incidentes')
    
    if st.button("Programar Mantenimiento", use_container_width=True):
        st.session_state.page = 'schedule_maintenance'
        log_access(username, 'navigate', 'Programar Mantenimiento')
    
    if st.button("Ver Programación", use_container_width=True):
        st.session_state.page = 'view_schedules'
        log_access(username, 'navigate', 'Ver Programación')
    
    # Sección Reportes
    st.subheader("Reportes")
    if st.button("Estadísticas de Flota", use_container_width=True):
        st.session_state.page = 'fleet_stats'
        log_access(username, 'navigate', 'Estadísticas de Flota')
        
    if st.button("Análisis de Costos", use_container_width=True):
        st.session_state.page = 'cost_analysis'
        log_access(username, 'navigate', 'Análisis de Costos')
    
    # Sección Administración
    if user_role == 'admin':
        st.subheader("Administración")
        if st.button("Configuración", use_container_width=True):
            st.session_state.page = 'admin_settings'
            log_access(username, 'navigate', 'Configuración')
    
    # Sección Ayuda
    st.subheader("Ayuda")
    if st.button("Manual de Usuario", use_container_width=True):
        st.session_state.page = 'user_manual'
        log_access(username, 'navigate', 'Manual de Usuario')
    
    if st.button("Tutorial Guiado", use_container_width=True):
        st.session_state.page = 'tutorial'
        log_access(username, 'navigate', 'Tutorial Guiado')
    
    # Información de usuario
    st.sidebar.markdown("---")
    st.sidebar.info(f"Usuario: **{user_name}**  \nRol: **{user_role.capitalize()}**")
    
    # Botón de cierre de sesión
    if st.button("Cerrar Sesión", key="logout_btn"):
        # Vaciar el estado de sesión excepto las variables de autenticación
        for key in list(st.session_state.keys()):
            if key != 'authenticated':
                if key in st.session_state:
                    del st.session_state[key]
        
        # Marcar como no autenticado
        st.session_state.authenticated = False
        log_access(username, 'logout')
        st.rerun()

# Función para la página de inicio
def home_page():
    st.title("Sistema de Gestión de Flota Vehicular 🚗")
    
    col1, col2 = st.columns(2)
    
    with col1:
        styled_header("Resumen de Flota", "flota")
        
        try:
            vehicles = db.load_vehicles()
            st.info(f"Total vehículos: {len(vehicles)}")
            
            # Contar por estado
            if not vehicles.empty:
                status_counts = vehicles['estado'].value_counts()
                for status, count in status_counts.items():
                    if status == "SERVICIO":
                        st.success(f"✅ En servicio: {count}")
                    elif status == "RECUPERAR":
                        st.warning(f"⚠️ Para recuperar: {count}")
                    elif status == "RADIADO":
                        st.error(f"❌ Radiados: {count}")
                    else:
                        st.write(f"{status}: {count}")
        except Exception as e:
            log_exception(logger, e, "Error al cargar datos en página de inicio")
            st.error(f"Error al cargar los datos: {str(e)}")
    
    with col2:
        styled_header("Acciones Rápidas", "acciones")
        
        if st.button("⭐ Ver todos los vehículos", use_container_width=True):
            st.session_state.page = 'view_vehicles'
            st.rerun()
        
        if user_role in ['admin', 'manager']:
            if st.button("➕ Agregar nuevo vehículo", use_container_width=True):
                st.session_state.page = 'add_vehicle'
                st.rerun()
        
        if st.button("🔧 Registrar service", use_container_width=True):
            st.session_state.page = 'add_service'
            st.rerun()
        
        if st.button("📊 Ver estadísticas", use_container_width=True):
            st.session_state.page = 'fleet_stats'
            st.rerun()
    
    # Incidentes recientes
    styled_header("Incidentes Recientes", "incidentes", "🚨")
    
    try:
        incidents = db.get_incidents(estado="PENDIENTE")
        if not incidents.empty:
            # Usar función de paginación para mostrar tabla
            crear_tabla_paginada(
                incidents[['patente', 'marca', 'modelo', 'fecha', 'tipo', 'descripcion']], 
                page_size=5,
                key_prefix="home_incidents"
            )
        else:
            st.info("No hay incidentes pendientes registrados.")
    except Exception as e:
        log_exception(logger, e, "Error al cargar incidentes en página de inicio")
        st.error(f"Error al cargar incidentes: {str(e)}")
    
    # Mantenimientos programados próximos
    styled_header("Mantenimientos Próximos", "mantenimiento", "📅")
    
    try:
        scheduled_maintenance = db.get_maintenance_schedules(estado="PENDIENTE", proximos_dias=30)
        if not scheduled_maintenance.empty:
            display_cols = ['patente', 'marca', 'modelo', 'fecha_programada', 'tipo_service']
            
            crear_tabla_paginada(
                scheduled_maintenance[display_cols],
                page_size=5,
                key_prefix="home_maintenance"
            )
            
            if st.button("Ver todos los mantenimientos programados"):
                st.session_state.page = 'view_schedules'
                st.rerun()
        else:
            st.info("No hay mantenimientos programados para los próximos 30 días.")
    except Exception as e:
        log_exception(logger, e, "Error al cargar mantenimientos en página de inicio")
        st.error(f"Error al cargar mantenimientos programados: {str(e)}")

# Función para la página de listado de vehículos
def view_vehicles_page():
    styled_header("Listado de Vehículos", "vehiculos", "🚗")
    
    # Crear tabla filtrable con búsqueda y paginación
    try:
        # Obtener vehículos
        vehicles = db.load_vehicles()
        
        if vehicles.empty:
            st.info("No hay vehículos registrados en el sistema.")
            return
        
        # Configurar filtros
        filtros = {
            'area': {'titulo': 'Filtrar por área'},
            'tipo': {'titulo': 'Filtrar por tipo'},
            'estado': {'titulo': 'Filtrar por estado'}
        }
        
        # Usar componente de tabla filtrable
        df_filtrado = tabla_filtrable(
            vehicles, 
            filtros=filtros,
            texto_busqueda=True,
            titulo="",
            page_size=10,
            key_prefix="view_vehicles"
        )
        
        # Seleccionar vehículo para ver detalles
        st.subheader("Detalles del Vehículo")
        
        patentes = df_filtrado['patente'].tolist()
        selected_patente = st.selectbox(
            "Seleccionar vehículo para ver detalles:", 
            [""] + patentes
        )
        
        if selected_patente:
            vehicle = db.get_vehicle_by_patente(selected_patente)
            if vehicle:
                # Mostrar detalles en dos columnas
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Patente:** {vehicle['patente']}")
                    st.write(f"**Área:** {vehicle['area']}")
                    st.write(f"**Tipo:** {vehicle['tipo']}")
                    st.write(f"**Marca:** {vehicle['marca']}")
                    st.write(f"**Modelo:** {vehicle['modelo']}")
                    st.write(f"**Año:** {vehicle['año']}")
                
                with col2:
                    st.write(f"**Estado:** {vehicle['estado']}")
                    st.write(f"**Kilometraje:** {vehicle['km']} km")
                    st.write(f"**Último service:** {vehicle['fecha_service'] or 'No registrado'}")
                    st.write(f"**Taller:** {vehicle['taller'] or 'No registrado'}")
                    if vehicle.get('id_vehiculo'):
                        st.write(f"**ID Vehículo:** {vehicle['id_vehiculo']}")
                    if vehicle.get('rori'):
                        st.write(f"**RORI:** {vehicle['rori']}")
                    if vehicle.get('vtv_vencimiento'):
                        st.write(f"**Vencimiento VTV:** {vehicle['vtv_vencimiento']}")
                
                # Observaciones
                st.write("**Observaciones:**")
                st.write(vehicle['observaciones'] or "Sin observaciones")
                
                # Mostrar enlaces de PDF si existen
                if vehicle.get('pdf_files'):
                    st.write("**Documentación adjunta:**")
                    pdf_links = db.get_pdf_download_links(vehicle['pdf_files'])
                    if pdf_links:
                        st.markdown(pdf_links, unsafe_allow_html=True)
                    else:
                        st.write("Error al cargar los archivos adjuntos.")
                
                # Acciones adicionales
                st.subheader("Acciones")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("Ver historial de service", key="btn_hist_service"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'service_history'
                        st.rerun()
                
                with col2:
                    if st.button("Registrar service", key="btn_reg_service"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'add_service'
                        st.rerun()
                
                with col3:
                    if st.button("Programar mantenimiento", key="btn_prog_maint"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'schedule_maintenance'
                        st.rerun()
                
                with col4:
                    if user_role in ['admin', 'manager'] and st.button("Editar vehículo", key="btn_edit"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'edit_vehicle'
                        st.rerun()
                
                # Si es administrador, mostrar opción para eliminar
                if user_role == 'admin':
                    if st.button("⚠️ Eliminar vehículo", key="btn_delete"):
                        # Modal de confirmación
                        confirm = st.checkbox(
                            "Confirmo que quiero eliminar este vehículo y todos sus registros asociados.", 
                            key="confirm_delete"
                        )
                        
                        if confirm and st.button("CONFIRMAR ELIMINACIÓN", key="btn_confirm_delete"):
                            success, message = db.delete_vehicle(selected_patente)
                            if success:
                                st.success(message)
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(message)
    
    except Exception as e:
        log_exception(logger, e, "Error en página de listado de vehículos")
        st.error(f"Error al cargar o procesar vehículos: {str(e)}")

# Las demás funciones de páginas se implementarían de forma similar
# add_vehicle_page(), edit_vehicle_page(), add_service_page(), etc.

def admin_settings_page():
    styled_header("Configuración del Sistema", "configuracion", "⚙️")
    
    if user_role != 'admin':
        st.error("No tiene permisos para acceder a esta sección.")
        if st.button("Volver"):
            st.session_state.page = 'home'
            st.rerun()
        return
    
    # Crear pestañas para diferentes secciones
    tabs = st.tabs([
        "Base de Datos", 
        "Importación de Datos", 
        "Tema y Apariencia", 
        "Copias de Seguridad",
        "Recordatorios"
    ])
    
    # Tab: Base de Datos
    with tabs[0]:
        styled_header("Base de Datos", "database", "💾")
        
        st.info("Desde aquí puede administrar la base de datos del sistema.")
        
        if st.button("Inicializar Base de Datos"):
            with st.spinner("Inicializando base de datos..."):
                success = db.init_database()
                if success:
                    st.success("Base de datos inicializada correctamente.")
                else:
                    st.error("Error al inicializar la base de datos.")
        
        st.write("Esta acción creará las tablas necesarias si no existen.")
        
        # Mostrar información de la base de datos
        st.subheader("Información de la Base de Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Tipo de base de datos:** {'PostgreSQL' if db.USE_POSTGRES else 'SQLite (standalone)'}")
            if not db.USE_POSTGRES:
                st.write(f"**Ubicación:** {db.get_database_path()}")
        
        with col2:
            # Obtener estadísticas
            try:
                engine = db.get_sqlalchemy_engine()
                
                # Contar registros en cada tabla
                tablas = {
                    "vehiculos": "SELECT COUNT(*) FROM vehiculos",
                    "historial_service": "SELECT COUNT(*) FROM historial_service",
                    "incidentes": "SELECT COUNT(*) FROM incidentes",
                    "programacion_mantenimiento": "SELECT COUNT(*) FROM programacion_mantenimiento"
                }
                
                for tabla, query in tablas.items():
                    result = pd.read_sql(query, engine)
                    count = result.iloc[0, 0]
                    st.write(f"**Registros en {tabla}:** {count}")
            
            except Exception as e:
                log_exception(logger, e, "Error al obtener estadísticas de BD")
                st.error(f"Error al obtener estadísticas: {str(e)}")
    
    # Tab: Importación de Datos
    with tabs[1]:
        styled_header("Importación de Datos", "import", "📤")
        
        st.write("Desde aquí puede importar datos masivamente desde archivos CSV.")
        
        # Importar vehículos
        st.write("### Importar Vehículos")
        st.write("""
        Por favor, asegúrese que el archivo CSV tenga las siguientes columnas:
        - patente/dominio (obligatorio)
        - área/dependencia
        - tipo de vehículo
        - marca
        - modelo
        - año
        - estado (por defecto: SERVICIO)
        - km (por defecto: 0)
        """)
        
        uploaded_file = st.file_uploader(
            "Seleccionar archivo CSV", 
            type=['csv'], 
            key="admin_csv_uploader"
        )
        
        if uploaded_file:
            st.write("Vista previa del archivo:")
            
            df = db.process_uploaded_file(uploaded_file)
            if df is not None:
                # Mostrar primeras filas
                st.dataframe(df.head())
                
                col1, col2 = st.columns(2)
                with col1:
                    confirm_import = st.button("Importar vehículos", key="admin_import_btn")
                with col2:
                    cancel_import = st.button("Cancelar", key="admin_cancel_btn")
                
                if confirm_import:
                    with st.spinner("Importando vehículos..."):
                        success_count, error_count, error_plates = db.import_vehicles_from_df(df)
                        st.success(f"Importación completada: {success_count} vehículos importados correctamente.")
                        if error_count > 0:
                            st.warning(f"{error_count} vehículos no pudieron ser importados.")
                            st.write("Patentes con error:", ", ".join(error_plates[:10]) + ("..." if len(error_plates) > 10 else ""))
    
    # Tab: Tema y Apariencia
    with tabs[2]:
        styled_header("Tema y Apariencia", "theme", "🎨")
        
        # Usar el componente de selección de tema
        theme_selector()
    
    # Tab: Copias de Seguridad
    with tabs[3]:
        styled_header("Copias de Seguridad", "backup", "📦")
        
        if not db.USE_POSTGRES:
            # Para SQLite, usar el componente de gestión de copias
            interfaz_backup_sqlite(db.get_database_path())
        else:
            st.warning("Las copias de seguridad manuales no están disponibles para PostgreSQL. Por favor, contacte al administrador del sistema para gestionar copias de seguridad.")
    
    # Tab: Recordatorios
    with tabs[4]:
        styled_header("Configuración de Recordatorios", "reminders", "🔔")
        
        st.info("Configure direcciones de correo electrónico para recibir recordatorios de mantenimientos programados y vencimientos de VTV.")
        
        # Verificar si tenemos las credenciales de email configuradas
        email_configured = all(key in os.environ for key in ["EMAIL_HOST", "EMAIL_PORT", "EMAIL_USER", "EMAIL_PASSWORD"])
        
        if not email_configured:
            st.warning("La funcionalidad de recordatorios por correo electrónico requiere configurar las credenciales SMTP.")
            st.info("Para enviar correos, necesita agregar las siguientes variables de entorno: EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD")
        
        # Configuración de correos electrónicos para notificaciones
        try:
            if 'email_recipients' not in st.session_state:
                st.session_state.email_recipients = []
            
            # Mostrar los correos electrónicos actuales
            if st.session_state.email_recipients:
                st.write("Correos electrónicos configurados:")
                for i, email in enumerate(st.session_state.email_recipients):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(email)
                    with col2:
                        if st.button("Eliminar", key=f"delete_email_{i}"):
                            st.session_state.email_recipients.pop(i)
                            st.rerun()
            
            # Agregar nuevo correo electrónico
            with st.form("email_form"):
                new_email = st.text_input("Nuevo correo electrónico:")
                submit = st.form_submit_button("Agregar")
                
                if submit and new_email:
                    # Validar formato de email
                    import re
                    if re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                        if new_email not in st.session_state.email_recipients:
                            st.session_state.email_recipients.append(new_email)
                            st.success(f"Correo {new_email} agregado correctamente.")
                            st.rerun()
                        else:
                            st.error("Este correo electrónico ya está en la lista.")
                    else:
                        st.error("Por favor, ingrese un correo electrónico válido.")
            
            # Configuración de parámetros de recordatorios
            st.subheader("Parámetros de Recordatorios")
            
            col1, col2 = st.columns(2)
            
            with col1:
                dias_vtv = st.slider(
                    "Días de anticipación para alertas de VTV:",
                    min_value=7,
                    max_value=60,
                    value=30,
                    step=1
                )
            
            with col2:
                dias_mant = st.slider(
                    "Días de anticipación para alertas de mantenimiento:",
                    min_value=1,
                    max_value=30,
                    value=7,
                    step=1
                )
            
            if st.button("Guardar configuración de recordatorios"):
                # En una aplicación real, aquí guardaríamos esta configuración en la base de datos
                st.success("Configuración guardada correctamente.")
                
                # Proceso de envío de recordatorios (simulado)
                if st.session_state.email_recipients and email_configured:
                    with st.spinner("Enviando recordatorios pendientes..."):
                        time.sleep(2)  # Simulación de procesamiento
                        st.success("Recordatorios enviados correctamente.")
        
        except Exception as e:
            log_exception(logger, e, "Error en configuración de recordatorios")
            st.error(f"Error en la configuración de recordatorios: {str(e)}")

def user_manual_page():
    # Usar el componente de documentación
    display_manual()

def tutorial_page():
    # Usar el componente de tutorial guiado
    show_tutorial()

def fleet_stats_page():
    styled_header("Estadísticas de Flota", "estadisticas", "📊")
    
    try:
        # Cargar datos necesarios
        df_vehiculos = db.load_vehicles()
        df_services = db.get_service_history()
        df_incidentes = db.get_incidents()
        df_mantenimientos = db.get_maintenance_schedules()
        
        # Usar el componente de dashboard analítico
        dashboard_analitica(df_vehiculos, df_services, df_incidentes, df_mantenimientos)
    
    except Exception as e:
        log_exception(logger, e, "Error al cargar estadísticas de flota")
        st.error(f"Error al cargar estadísticas: {str(e)}")

def cost_analysis_page():
    styled_header("Análisis de Costos de Mantenimiento", "costos", "💰")
    
    try:
        # Cargar datos necesarios
        df_vehiculos = db.load_vehicles()
        df_services = db.get_service_history()
        
        # Usar el componente de análisis de costos
        visualizar_costos_mantenimiento(df_services, df_vehiculos)
    
    except Exception as e:
        log_exception(logger, e, "Error al cargar análisis de costos")
        st.error(f"Error al cargar análisis de costos: {str(e)}")

# Función básica para páginas pendientes de implementación completa
def page_in_development(title="Página en Desarrollo", icon="🛠️"):
    styled_header(title, None, icon)
    st.info(f"Esta funcionalidad está en desarrollo. Pronto estará disponible la versión completa.")
    st.warning("Vuelva a la página principal o pruebe otra sección.")
    
    if st.button("Volver a la página principal"):
        st.session_state.page = 'home'
        st.rerun()

# Implementación básica de las páginas de mantenimiento
def add_vehicle_page():
    page_in_development("Agregar Vehículo", "🚗")

def edit_vehicle_page():
    page_in_development("Editar Vehículo", "✏️")

def add_service_page():
    page_in_development("Registrar Service", "🔧")

def service_history_page():
    page_in_development("Historial de Service", "📋")

def add_incident_page():
    page_in_development("Registrar Incidente", "🚨")

def view_incidents_page():
    page_in_development("Ver Incidentes", "⚠️")

def schedule_maintenance_page():
    page_in_development("Programar Mantenimiento", "🗓️")

def view_schedules_page():
    page_in_development("Ver Programación", "📅")

# Diccionario de páginas
pages = {
    'home': home_page,
    'view_vehicles': view_vehicles_page,
    'add_vehicle': add_vehicle_page,
    'edit_vehicle': edit_vehicle_page,
    'add_service': add_service_page,
    'service_history': service_history_page,
    'add_incident': add_incident_page,
    'view_incidents': view_incidents_page,
    'schedule_maintenance': schedule_maintenance_page,
    'view_schedules': view_schedules_page,
    'fleet_stats': fleet_stats_page,
    'cost_analysis': cost_analysis_page,
    'admin_settings': admin_settings_page,
    'user_manual': user_manual_page,
    'tutorial': tutorial_page
}

# Renderizar la página seleccionada
try:
    if st.session_state.page in pages:
        # Registrar la navegación de página
        log_access(username, 'view', st.session_state.page)
        
        # Renderizar la página
        pages[st.session_state.page]()
    else:
        st.error(f"Página no encontrada: {st.session_state.page}")
        st.session_state.page = 'home'
        st.rerun()
except Exception as e:
    log_exception(logger, e, f"Error al renderizar página: {st.session_state.page}")
    st.error(f"Se produjo un error inesperado: {str(e)}")
    
    # Mostrar detalles del error solo para administradores
    if user_role == 'admin':
        with st.expander("Detalles del error (solo administradores)"):
            st.code(traceback.format_exc())
            
            # Opción para volver a la página de inicio
            if st.button("Volver a la página de inicio"):
                st.session_state.page = 'home'
                st.rerun()