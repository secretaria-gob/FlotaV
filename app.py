import streamlit as st
import pandas as pd
from datetime import datetime
import os
import database as db
from auth import check_authentication, get_user_role
import plotly.express as px  # Para gráficos interactivos con valores numéricos

# Set page configuration
st.set_page_config(
    page_title="Sistema de Gestión de Flota Vehicular",
    page_icon="🚗",
    layout="wide"
)

# Initialize database
db.init_database()

# Check authentication
auth_status, user_name, username = check_authentication()
if not auth_status:
    # La nueva función de autenticación maneja todo el proceso de inicio de sesión
    st.stop()

# Get user role
user_role = get_user_role(username)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Sidebar navigation
with st.sidebar:
    st.title("Menú")
    
    # Home button
    if st.button("Inicio", use_container_width=True):
        st.session_state.page = 'home'
    
    # Vehicle section
    st.subheader("Vehículos")
    if st.button("Ver Vehículos", use_container_width=True):
        st.session_state.page = 'view_vehicles'
    
    if user_role in ['admin', 'manager']:
        if st.button("Agregar Vehículo", use_container_width=True):
            st.session_state.page = 'add_vehicle'
        
        if st.button("Editar Vehículo", use_container_width=True):
            st.session_state.page = 'edit_vehicle'
    
    # Service section
    st.subheader("Mantenimiento")
    if st.button("Registrar Service", use_container_width=True):
        st.session_state.page = 'add_service'
    
    if st.button("Historial de Service", use_container_width=True):
        st.session_state.page = 'service_history'
    
    if st.button("Registrar Incidente", use_container_width=True):
        st.session_state.page = 'add_incident'
    
    if st.button("Ver Incidentes", use_container_width=True):
        st.session_state.page = 'view_incidents'
        
    if st.button("Programar Mantenimiento", use_container_width=True):
        st.session_state.page = 'schedule_maintenance'
        
    if st.button("Ver Programación", use_container_width=True):
        st.session_state.page = 'view_schedules'
    
    # Reports section
    st.subheader("Reportes")
    if st.button("Estadísticas de Flota", use_container_width=True):
        st.session_state.page = 'fleet_stats'
    
    # Admin section
    if user_role == 'admin':
        st.subheader("Administración")
        if st.button("Configuración", use_container_width=True):
            st.session_state.page = 'admin_settings'

# Main content area
def home_page():
    st.title("Sistema de Gestión de Flota Vehicular 🚗")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Resumen de Flota")
        try:
            vehicles = db.load_vehicles()
            st.info(f"Total vehículos: {len(vehicles)}")
            
            # Count by status
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
            st.error(f"Error al cargar los datos: {str(e)}")
    
    with col2:
        st.subheader("Acciones Rápidas")
        if st.button("⭐ Ver todos los vehículos", use_container_width=True):
            st.session_state.page = 'view_vehicles'
        
        if user_role in ['admin', 'manager']:
            if st.button("➕ Agregar nuevo vehículo", use_container_width=True):
                st.session_state.page = 'add_vehicle'
        
        if st.button("🔧 Registrar service", use_container_width=True):
            st.session_state.page = 'add_service'
        
        if st.button("📊 Ver estadísticas", use_container_width=True):
            st.session_state.page = 'fleet_stats'
    
    # Recent incidents
    st.subheader("Incidentes Recientes")
    try:
        incidents = db.get_incidents(estado="PENDIENTE")
        if not incidents.empty:
            st.dataframe(incidents[['patente', 'marca', 'modelo', 'fecha', 'tipo', 'descripcion']], use_container_width=True)
        else:
            st.info("No hay incidentes pendientes registrados.")
    except Exception as e:
        st.error(f"Error al cargar incidentes: {str(e)}")
    
    # Mantenimientos programados próximos
    st.subheader("Mantenimientos Próximos")
    try:
        scheduled_maintenance = db.get_maintenance_schedules(estado="PENDIENTE", proximos_dias=30)
        if not scheduled_maintenance.empty:
            display_cols = ['patente', 'marca', 'modelo', 'fecha_programada', 'tipo_service']
            st.dataframe(scheduled_maintenance[display_cols], use_container_width=True)
            
            if st.button("Ver todos los mantenimientos programados"):
                st.session_state.page = 'view_schedules'
                st.rerun()
        else:
            st.info("No hay mantenimientos programados para los próximos 30 días.")
    except Exception as e:
        st.error(f"Error al cargar mantenimientos programados: {str(e)}")

def view_vehicles_page():
    st.title("Listado de Vehículos")
    
    # Search box
    search = st.text_input("Buscar por patente, área, marca o modelo:")
    
    # Load vehicles with optional search filter
    vehicles = db.load_vehicles(search)
    
    # Display vehicles
    if not vehicles.empty:
        # Filter columns for display
        display_columns = ['patente', 'area', 'tipo', 'marca', 'modelo', 'año', 'estado', 'km', 'fecha_service']
        st.dataframe(vehicles[display_columns], use_container_width=True)
        
        # Select vehicle for detailed view
        patentes = vehicles['patente'].tolist()
        selected_patente = st.selectbox("Seleccionar vehículo para ver detalles:", [""] + patentes)
        
        if selected_patente:
            vehicle = db.get_vehicle_by_patente(selected_patente)
            if vehicle:
                st.subheader(f"Detalles del Vehículo: {vehicle['patente']}")
                
                col1, col2 = st.columns(2)
                with col1:
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
                
                # Additional actions
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("Ver historial de service"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'service_history'
                
                with col2:
                    if st.button("Registrar service"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'add_service'
                
                with col3:
                    if st.button("Programar mantenimiento"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'schedule_maintenance'
                
                with col4:
                    if user_role in ['admin', 'manager'] and st.button("Editar vehículo"):
                        st.session_state.selected_vehicle = selected_patente
                        st.session_state.page = 'edit_vehicle'
    else:
        st.info("No se encontraron vehículos.")

def add_vehicle_page():
    st.title("Agregar Nuevo Vehículo")
    
    if user_role not in ['admin', 'manager']:
        st.error("No tiene permisos para agregar vehículos.")
        st.button("Volver", on_click=lambda: setattr(st.session_state, 'page', 'home'))
        return
    
    # Opción para importar vehículos desde CSV
    tabs = st.tabs(["Agregar vehículo", "Importar desde CSV"])
    
    with tabs[0]:  # Pestaña de agregar vehículo individual
        with st.form("add_vehicle_form"):
            patente = st.text_input("Patente*").upper()
            area = st.text_input("Área*")
            tipo = st.selectbox("Tipo*", ["AUTO", "CAMIONETA", "MOTO", "FURGON", "CAMION", "OTRO"])
            marca = st.text_input("Marca*")
            modelo = st.text_input("Modelo*")
            
            # Datos principales del vehículo
            col1, col2, col3 = st.columns(3)
            with col1:
                año = st.number_input("Año*", min_value=1950, max_value=datetime.now().year, value=2020)
                id_vehiculo = st.number_input("ID Vehículo", min_value=0, value=0)
            with col2:
                estado = st.selectbox("Estado*", ["SERVICIO", "RECUPERAR", "RADIADO"])
                rori = st.text_input("RORI")
            with col3:
                km = st.number_input("Kilometraje inicial", min_value=0, value=0)
                vtv_vencimiento = st.date_input("Vencimiento VTV", value=None)
                vtv_vencimiento_str = vtv_vencimiento.strftime("%Y-%m-%d") if vtv_vencimiento else None
            
            # Datos de servicio
            fecha_service = st.date_input("Fecha último service", value=None)
            fecha_service_str = fecha_service.strftime("%Y-%m-%d") if fecha_service else None
            taller = st.text_input("Taller")
            observaciones = st.text_area("Observaciones")
            
            # Agregar campo para subir archivos PDF
            uploaded_files = st.file_uploader("Adjuntar documentación (PDF)", type=['pdf'], accept_multiple_files=True)
            
            st.markdown("*Campos obligatorios")
            submitted = st.form_submit_button("Guardar")
            
            if submitted:
                if not all([patente, area, tipo, marca, modelo, año, estado]):
                    st.error("Por favor, complete todos los campos obligatorios.")
                else:
                    # Procesar archivos PDF si los hay
                    pdf_files_json = db.process_pdf_files(uploaded_files) if uploaded_files else None
                    
                    result = db.add_vehicle(
                        patente, area, tipo, marca, modelo, año, estado, 
                        km, fecha_service_str, taller, observaciones, pdf_files_json,
                        rori, id_vehiculo, vtv_vencimiento_str
                    )
                    
                    if result:
                        st.success("Vehículo agregado exitosamente.")
                        if st.button("Agregar otro vehículo"):
                            for key in st.session_state.keys():
                                if key != 'page' and key != 'authenticated' and key != 'username' and key != 'name':
                                    if key in st.session_state:
                                        del st.session_state[key]
                            st.rerun()
                        if st.button("Ver listado de vehículos"):
                            st.session_state.page = 'view_vehicles'
                            st.rerun()
                    else:
                        st.error("Error al agregar el vehículo. La patente ya podría estar registrada.")
    
    with tabs[1]:  # Pestaña de importación CSV
        st.subheader("Importar vehículos desde archivo CSV")
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
        
        uploaded_file = st.file_uploader("Seleccionar archivo CSV", type=['csv'])
        
        if uploaded_file:
            st.write("Vista previa del archivo:")
            
            df = db.process_uploaded_file(uploaded_file)
            if df is not None:
                st.dataframe(df.head())
                
                col1, col2 = st.columns(2)
                with col1:
                    confirm_import = st.button("Importar vehículos")
                with col2:
                    cancel_import = st.button("Cancelar")
                
                if confirm_import:
                    with st.spinner("Importando vehículos..."):
                        success_count, error_count, error_plates = db.import_vehicles_from_df(df)
                        st.success(f"Importación completada: {success_count} vehículos importados correctamente.")
                        if error_count > 0:
                            st.warning(f"{error_count} vehículos no pudieron ser importados.")
                            st.write("Patentes con error:", ", ".join(error_plates[:10]) + ("..." if len(error_plates) > 10 else ""))
                
                if cancel_import:
                    st.rerun()

def edit_vehicle_page():
    st.title("Editar Vehículo")
    
    if user_role not in ['admin', 'manager']:
        st.error("No tiene permisos para editar vehículos.")
        st.button("Volver", on_click=lambda: setattr(st.session_state, 'page', 'home'))
        return
    
    # If coming from the details page, use the selected vehicle
    if 'selected_vehicle' in st.session_state:
        patente = st.session_state.selected_vehicle
        del st.session_state.selected_vehicle
    else:
        # Otherwise, show a selection box
        vehicles = db.load_vehicles()
        patentes = vehicles['patente'].tolist()
        patente = st.selectbox("Seleccionar vehículo para editar:", [""] + patentes)
    
    if patente:
        vehicle = db.get_vehicle_by_patente(patente)
        if vehicle:
            with st.form("edit_vehicle_form"):
                st.subheader(f"Editando Vehículo: {patente}")
                
                area = st.text_input("Área", value=vehicle['area'])
                tipo = st.selectbox("Tipo", ["AUTO", "CAMIONETA", "MOTO", "FURGON", "CAMION", "OTRO"], index=["AUTO", "CAMIONETA", "MOTO", "FURGON", "CAMION", "OTRO"].index(vehicle['tipo']) if vehicle['tipo'] in ["AUTO", "CAMIONETA", "MOTO", "FURGON", "CAMION", "OTRO"] else 0)
                marca = st.text_input("Marca", value=vehicle['marca'])
                modelo = st.text_input("Modelo", value=vehicle['modelo'])

                # Datos principales del vehículo en columnas
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Asegurar que año sea un valor válido (mínimo 1950)
                    año_value = vehicle.get('año', 0) or 0
                    año_value = max(1950, año_value)  # Si es menor que 1950, usamos 1950
                    año = st.number_input("Año", min_value=1950, max_value=datetime.now().year, value=año_value)
                    id_vehiculo_value = vehicle.get('id_vehiculo', 0) or 0  # Valor predeterminado si no existe o es None
                    id_vehiculo = st.number_input("ID Vehículo", min_value=0, value=id_vehiculo_value)
                with col2:
                    estado = st.selectbox("Estado", ["SERVICIO", "RECUPERAR", "RADIADO"], index=["SERVICIO", "RECUPERAR", "RADIADO"].index(vehicle['estado']) if vehicle['estado'] in ["SERVICIO", "RECUPERAR", "RADIADO"] else 0)
                    rori = st.text_input("RORI", value=vehicle.get('rori', "") or "")
                with col3:
                    km = st.number_input("Kilometraje", min_value=0, value=vehicle['km'])
                    
                    # Procesamiento de fecha de VTV
                    vtv_value = None
                    if vehicle.get('vtv_vencimiento'):
                        try:
                            vtv_value = datetime.strptime(vehicle['vtv_vencimiento'], "%Y-%m-%d").date()
                        except:
                            # Manejo de posibles problemas de formato de fecha
                            pass
                    
                    vtv_vencimiento = st.date_input("Vencimiento VTV", value=vtv_value)
                    vtv_vencimiento_str = vtv_vencimiento.strftime("%Y-%m-%d") if vtv_vencimiento else None
                
                # Datos de servicio
                fecha_service_value = None
                if vehicle['fecha_service']:
                    try:
                        fecha_service_value = datetime.strptime(vehicle['fecha_service'], "%Y-%m-%d").date()
                    except:
                        # Handle potential date format issues
                        pass
                
                fecha_service = st.date_input("Fecha último service", value=fecha_service_value)
                fecha_service_str = fecha_service.strftime("%Y-%m-%d") if fecha_service else None
                
                taller = st.text_input("Taller", value=vehicle['taller'] or "")
                observaciones = st.text_area("Observaciones", value=vehicle['observaciones'] or "")
                
                # Mostrar los PDFs existentes
                if vehicle.get('pdf_files'):
                    st.write("**Documentación adjunta actualmente:**")
                    pdf_links = db.get_pdf_download_links(vehicle['pdf_files'])
                    if pdf_links:
                        st.markdown(pdf_links, unsafe_allow_html=True)
                
                # Agregar campo para subir archivos PDF
                st.write("**Adjuntar nueva documentación (PDF):**")
                uploaded_files = st.file_uploader("Seleccionar archivos", type=['pdf'], accept_multiple_files=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Actualizar")
                with col2:
                    delete = st.form_submit_button("Eliminar Vehículo", type="secondary")
                
                if submitted:
                    # Procesar archivos PDF si los hay
                    pdf_files_json = None
                    if uploaded_files:
                        pdf_files_json = db.process_pdf_files(uploaded_files)
                    
                    updated_fields = {
                        'area': area,
                        'tipo': tipo,
                        'marca': marca,
                        'modelo': modelo,
                        'año': año,
                        'estado': estado,
                        'km': km,
                        'fecha_service': fecha_service_str,
                        'taller': taller,
                        'observaciones': observaciones,
                        'rori': rori,
                        'id_vehiculo': id_vehiculo,
                        'vtv_vencimiento': vtv_vencimiento_str
                    }
                    
                    # Solo actualizar los PDF si se subieron nuevos archivos
                    if pdf_files_json:
                        updated_fields['pdf_files'] = pdf_files_json
                    
                    result = db.update_vehicle(patente, **updated_fields)
                    
                    if result:
                        st.success("Vehículo actualizado exitosamente.")
                        # Guardamos en la sesión que queremos ver el listado después
                        st.session_state.show_vehicle_list = True
                    else:
                        st.error("Error al actualizar el vehículo.")
                
                if delete:
                    confirm = st.checkbox("Confirmar eliminación")
                    if confirm:
                        result = db.delete_vehicle(patente)
                        if result:
                            st.success("Vehículo eliminado exitosamente.")
                            if st.button("Ver listado de vehículos"):
                                st.session_state.page = 'view_vehicles'
                                st.rerun()
                        else:
                            st.error("Error al eliminar el vehículo.")
        else:
            st.error("Vehículo no encontrado.")
    else:
        st.info("Seleccione un vehículo para editar.")
        
    # Botón para ver la lista de vehículos fuera del formulario
    if 'show_vehicle_list' in st.session_state and st.session_state.show_vehicle_list:
        if st.button("Ver listado de vehículos"):
            st.session_state.page = 'view_vehicles'
            st.session_state.show_vehicle_list = False
            st.rerun()

def add_service_page():
    st.title("Registrar Service")
    
    # If coming from the details page, use the selected vehicle
    if 'selected_vehicle' in st.session_state:
        patente = st.session_state.selected_vehicle
        del st.session_state.selected_vehicle
    else:
        # Otherwise, show a selection box
        vehicles = db.load_vehicles()
        patentes = vehicles['patente'].tolist()
        patente = st.selectbox("Seleccionar vehículo:", [""] + patentes)
    
    if patente:
        vehicle = db.get_vehicle_by_patente(patente)
        if vehicle:
            st.subheader(f"Registrando Service para: {patente}")
            st.write(f"**Vehículo:** {vehicle['marca']} {vehicle['modelo']} ({vehicle['año']})")
            st.write(f"**Kilometraje actual:** {vehicle['km']} km")
            
            with st.form("add_service_form"):
                fecha = st.date_input("Fecha de service", value=datetime.now().date())
                fecha_str = fecha.strftime("%Y-%m-%d")
                
                km = st.number_input("Kilometraje actual", min_value=vehicle['km'], value=vehicle['km'])
                
                tipo_service = st.selectbox(
                    "Tipo de service", 
                    ["Mantenimiento general", "Cambio de aceite", "Cambio de filtros", 
                     "Reparación mecánica", "Reparación eléctrica", "Cambio de neumáticos",
                     "Alineación y balanceo", "Otro"]
                )
                
                taller = st.text_input("Taller")
                costo = st.number_input("Costo", min_value=0.0, format="%.2f")
                descripcion = st.text_area("Descripción del service")
                
                # Agregar campo para subir archivos PDF
                uploaded_files = st.file_uploader("Adjuntar documentación (PDF)", type=['pdf'], accept_multiple_files=True)
                
                submitted = st.form_submit_button("Registrar")
                
                if submitted:
                    if not all([fecha_str, km, tipo_service, taller]):
                        st.error("Por favor, complete todos los campos obligatorios.")
                    else:
                        # Procesar archivos PDF si los hay
                        pdf_files_json = db.process_pdf_files(uploaded_files) if uploaded_files else None
                        
                        result = db.add_service_record(
                            patente, fecha_str, km, tipo_service, taller, costo, descripcion, pdf_files_json
                        )
                        
                        if result:
                            st.success("Service registrado exitosamente.")
                            # Guardar en session_state que queremos mostrar opciones después
                            st.session_state.show_service_options = True
                        else:
                            st.error("Error al registrar el service.")
        else:
            st.error("Vehículo no encontrado.")
    else:
        st.info("Seleccione un vehículo para registrar el service.")
        
    # Botones para navegar fuera del formulario
    if 'show_service_options' in st.session_state and st.session_state.show_service_options:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Registrar otro service"):
                for key in st.session_state.keys():
                    if key != 'page' and key != 'authenticated' and key != 'username' and key != 'name':
                        if key in st.session_state:
                            del st.session_state[key]
                st.session_state.show_service_options = False
                st.rerun()
        with col2:
            if st.button("Ver historial de service"):
                st.session_state.page = 'service_history'
                st.session_state.show_service_options = False
                st.rerun()

def service_history_page():
    st.title("Historial de Service")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        # If coming from the details page, use the selected vehicle
        if 'selected_vehicle' in st.session_state:
            selected_patente = st.session_state.selected_vehicle
            del st.session_state.selected_vehicle
            filter_by_vehicle = True
        else:
            filter_by_vehicle = st.checkbox("Filtrar por vehículo", value=False)
            selected_patente = None
            
            if filter_by_vehicle:
                vehicles = db.load_vehicles()
                patentes = vehicles['patente'].tolist()
                selected_patente = st.selectbox("Seleccionar vehículo:", patentes)
    
    # Load service history with optional filter
    service_history = db.get_service_history(selected_patente)
    
    if not service_history.empty:
        st.dataframe(service_history, use_container_width=True)
        
        # Mostrar detalles de un registro específico con sus adjuntos
        st.subheader("Ver detalles y archivos adjuntos")
        record_ids = service_history['id'].tolist()
        selected_id = st.selectbox("Seleccionar registro:", record_ids)
        
        if selected_id:
            # Filtrar el registro seleccionado
            record = service_history[service_history['id'] == selected_id].iloc[0]
            
            st.write(f"**Vehículo:** {record['patente']} - {record.get('marca', '')} {record.get('modelo', '')}")
            st.write(f"**Fecha:** {record['fecha']}")
            st.write(f"**Kilometraje:** {record['km']} km")
            st.write(f"**Tipo:** {record['tipo_service']}")
            st.write(f"**Taller:** {record['taller']}")
            st.write(f"**Costo:** ${record['costo']}")
            st.write(f"**Descripción:** {record['descripcion']}")
            
            # Mostrar archivos PDF si existen
            if record.get('pdf_files'):
                st.write("**Documentación adjunta:**")
                pdf_links = db.get_pdf_download_links(record['pdf_files'])
                if pdf_links:
                    st.markdown(pdf_links, unsafe_allow_html=True)
                else:
                    st.write("Error al cargar los archivos adjuntos.")
    else:
        if selected_patente:
            st.info(f"No hay registros de service para el vehículo {selected_patente}.")
        else:
            st.info("No hay registros de service.")

def add_incident_page():
    st.title("Registrar Incidente")
    
    vehicles = db.load_vehicles()
    patentes = vehicles['patente'].tolist()
    patente = st.selectbox("Seleccionar vehículo:", [""] + patentes)
    
    if patente:
        vehicle = db.get_vehicle_by_patente(patente)
        if vehicle:
            st.subheader(f"Registrando Incidente para: {patente}")
            st.write(f"**Vehículo:** {vehicle['marca']} {vehicle['modelo']} ({vehicle['año']})")
            
            with st.form("add_incident_form"):
                fecha = st.date_input("Fecha del incidente", value=datetime.now().date())
                fecha_str = fecha.strftime("%Y-%m-%d")
                
                tipo = st.selectbox(
                    "Tipo de incidente", 
                    ["Accidente", "Falla mecánica", "Falla eléctrica", "Problema con neumáticos",
                     "Problema de frenos", "Problema de motor", "Otro"]
                )
                
                descripcion = st.text_area("Descripción del incidente")
                estado = st.selectbox("Estado", ["PENDIENTE", "EN PROCESO", "RESUELTO"])
                
                # Agregar campo para subir archivos PDF
                uploaded_files = st.file_uploader("Adjuntar documentación (PDF)", type=['pdf'], accept_multiple_files=True)
                
                submitted = st.form_submit_button("Registrar")
                
                if submitted:
                    if not all([fecha_str, tipo, descripcion, estado]):
                        st.error("Por favor, complete todos los campos.")
                    else:
                        # Procesar archivos PDF si los hay
                        pdf_files_json = db.process_pdf_files(uploaded_files) if uploaded_files else None
                        
                        result = db.add_incident(
                            patente, fecha_str, tipo, descripcion, estado, pdf_files_json
                        )
                        
                        if result:
                            st.success("Incidente registrado exitosamente.")
                            # Guardar en session_state que queremos mostrar opciones después
                            st.session_state.show_incident_options = True
                        else:
                            st.error("Error al registrar el incidente.")
        else:
            st.error("Vehículo no encontrado.")
    else:
        st.info("Seleccione un vehículo para registrar un incidente.")
        
    # Botones para navegar fuera del formulario
    if 'show_incident_options' in st.session_state and st.session_state.show_incident_options:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Registrar otro incidente"):
                for key in st.session_state.keys():
                    if key != 'page' and key != 'authenticated' and key != 'username' and key != 'name':
                        if key in st.session_state:
                            del st.session_state[key]
                st.session_state.show_incident_options = False
                st.rerun()
        with col2:
            if st.button("Ver incidentes"):
                st.session_state.page = 'view_incidents'
                st.session_state.show_incident_options = False
                st.rerun()

def view_incidents_page():
    st.title("Listado de Incidentes")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        filter_by_vehicle = st.checkbox("Filtrar por vehículo", value=False)
        selected_patente = None
        
        if filter_by_vehicle:
            vehicles = db.load_vehicles()
            patentes = vehicles['patente'].tolist()
            selected_patente = st.selectbox("Seleccionar vehículo:", patentes)
    
    with col2:
        filter_by_status = st.checkbox("Filtrar por estado", value=False)
        selected_status = None
        
        if filter_by_status:
            selected_status = st.selectbox("Estado:", ["PENDIENTE", "EN PROCESO", "RESUELTO"])
    
    # Load incidents with optional filters
    incidents = db.get_incidents(selected_patente, selected_status)
    
    if not incidents.empty:
        st.dataframe(incidents, use_container_width=True)
        
        # Allow viewing details and updating incident status
        st.subheader("Ver detalles y archivos adjuntos")
        incident_ids = incidents['id'].tolist()
        selected_id = st.selectbox("Seleccionar incidente:", incident_ids)
        
        if selected_id:
            # Filtrar el incidente seleccionado
            incident = incidents[incidents['id'] == selected_id].iloc[0]
            
            st.write(f"**Vehículo:** {incident['patente']} - {incident.get('marca', '')} {incident.get('modelo', '')}")
            st.write(f"**Fecha:** {incident['fecha']}")
            st.write(f"**Tipo:** {incident['tipo']}")
            st.write(f"**Estado:** {incident['estado']}")
            st.write(f"**Descripción:** {incident['descripcion']}")
            
            # Mostrar archivos PDF si existen
            if incident.get('pdf_files'):
                st.write("**Documentación adjunta:**")
                pdf_links = db.get_pdf_download_links(incident['pdf_files'])
                if pdf_links:
                    st.markdown(pdf_links, unsafe_allow_html=True)
                else:
                    st.write("Error al cargar los archivos adjuntos.")
            
            # Allow updating incident status
            if user_role in ['admin', 'manager']:
                st.subheader("Actualizar Estado de Incidente")
                new_status = st.selectbox("Nuevo estado:", ["PENDIENTE", "EN PROCESO", "RESUELTO"])
                
                if st.button("Actualizar Estado"):
                    # In a real app, you would add a function to update the incident status
                    st.success(f"Estado del incidente {selected_id} actualizado a {new_status}.")
    else:
        if selected_patente or selected_status:
            st.info(f"No hay incidentes que coincidan con los filtros aplicados.")
        else:
            st.info("No hay incidentes registrados.")

def fleet_stats_page():
    st.title("Estadísticas de Flota")
    
    try:
        stats = db.get_stats()
        
        # Crear tabs para diferentes vistas de estadísticas
        tab1, tab2, tab3 = st.tabs(["Estadísticas Generales", "Reportes", "Alertas"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Vehículos por Estado")
                if not stats["status"].empty:
                    st.bar_chart(stats["status"].set_index("estado"))
                else:
                    st.info("No hay datos para mostrar.")
                
                st.subheader("Vehículos por Tipo")
                if not stats["type"].empty:
                    st.bar_chart(stats["type"].set_index("tipo"))
                else:
                    st.info("No hay datos para mostrar.")
            
            with col2:
                st.subheader("Vehículos por Marca")
                if not stats["make"].empty:
                    st.bar_chart(stats["make"].set_index("marca"))
                else:
                    st.info("No hay datos para mostrar.")
                
                st.subheader("Vehículos por Área")
                if not stats["area"].empty:
                    st.bar_chart(stats["area"].set_index("area"))
                else:
                    st.info("No hay datos para mostrar.")
            
            # Eliminado gráfico de distribución por año de fabricación por solicitud del usuario
        
        with tab2:
            st.subheader("Herramientas de Reporte")
            
            # Exportar datos
            export_data_expander = st.expander("Exportar Datos", expanded=True)
            with export_data_expander:
                col1, col2 = st.columns([3, 1])
                with col1:
                    tabla = st.selectbox(
                        "Seleccione tabla a exportar:", 
                        ["vehiculos", "historial_service", "incidentes", "programacion_mantenimiento"],
                        format_func=lambda x: {
                            "vehiculos": "Vehículos", 
                            "historial_service": "Historial de Service", 
                            "incidentes": "Incidentes", 
                            "programacion_mantenimiento": "Programación de Mantenimiento"
                        }.get(x, x)
                    )
                with col2:
                    formato = st.selectbox("Formato:", ["xlsx", "csv"])
                
                # Mostrar gráficos correspondientes a la tabla seleccionada
                st.write("#### Vista previa gráfica")
                engine = db.get_sqlalchemy_engine()
                
                if tabla == 'vehiculos':
                    # Mostrar gráficos de vehículos
                    col1, col2 = st.columns(2)
                    with col1:
                        # Vehículos por estado
                        if not stats["status"].empty:
                            fig = px.bar(stats["status"], x="estado", y="count", 
                                         title="Vehículos por Estado",
                                         labels={"estado": "Estado", "count": "Cantidad"},
                                         text_auto=True)  # Mostrar números en el gráfico
                            fig.update_traces(textposition='outside')
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Vehículos por tipo
                        if not stats["type"].empty:
                            fig = px.bar(stats["type"], x="tipo", y="count", 
                                         title="Vehículos por Tipo",
                                         labels={"tipo": "Tipo", "count": "Cantidad"},
                                         text_auto=True)
                            fig.update_traces(textposition='outside')
                            st.plotly_chart(fig, use_container_width=True)
                
                elif tabla == 'historial_service':
                    # Consulta para servicios por mes/año
                    try:
                        service_over_time = pd.read_sql("""
                            SELECT 
                                EXTRACT(YEAR FROM CAST(fecha AS DATE)) as año,
                                EXTRACT(MONTH FROM CAST(fecha AS DATE)) as mes,
                                COUNT(*) as cantidad,
                                SUM(costo) as costo_total
                            FROM historial_service
                            GROUP BY año, mes
                            ORDER BY año, mes
                        """, engine)
                        
                        if not service_over_time.empty:
                            # Crear etiquetas de fecha
                            service_over_time['fecha'] = service_over_time.apply(
                                lambda x: f"{int(x['mes'])}/{int(x['año'])}", axis=1)
                            
                            fig = px.line(service_over_time, x='fecha', y='cantidad', 
                                          title="Servicios realizados por mes",
                                          labels={"fecha": "Mes/Año", "cantidad": "Cantidad de servicios"},
                                          markers=True, text='cantidad')
                            fig.update_traces(textposition='top center')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            fig2 = px.bar(service_over_time, x='fecha', y='costo_total', 
                                          title="Costo total de servicios por mes",
                                          labels={"fecha": "Mes/Año", "costo_total": "Costo total ($)"},
                                          text_auto=True)
                            fig2.update_traces(textposition='outside')
                            st.plotly_chart(fig2, use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pueden mostrar gráficos de servicios: {e}")
                
                elif tabla == 'incidentes':
                    # Consulta para incidentes por tipo
                    try:
                        incidentes_por_tipo = pd.read_sql("""
                            SELECT tipo, COUNT(*) as cantidad
                            FROM incidentes
                            GROUP BY tipo
                            ORDER BY cantidad DESC
                        """, engine)
                        
                        incidentes_por_estado = pd.read_sql("""
                            SELECT estado, COUNT(*) as cantidad
                            FROM incidentes
                            GROUP BY estado
                            ORDER BY cantidad DESC
                        """, engine)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if not incidentes_por_tipo.empty:
                                fig = px.pie(incidentes_por_tipo, values='cantidad', names='tipo', 
                                             title="Incidentes por Tipo",
                                             hole=0.3)
                                fig.update_traces(textinfo='percent+label+value')
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            if not incidentes_por_estado.empty:
                                fig = px.bar(incidentes_por_estado, x='estado', y='cantidad', 
                                             title="Incidentes por Estado",
                                             labels={"estado": "Estado", "cantidad": "Cantidad"},
                                             text_auto=True)
                                fig.update_traces(textposition='outside')
                                st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pueden mostrar gráficos de incidentes: {e}")
                
                elif tabla == 'programacion_mantenimiento':
                    # Consulta para mantenimientos programados
                    try:
                        mantenimientos_por_estado = pd.read_sql("""
                            SELECT estado, COUNT(*) as cantidad
                            FROM programacion_mantenimiento
                            GROUP BY estado
                            ORDER BY cantidad DESC
                        """, engine)
                        
                        mantenimientos_por_mes = pd.read_sql("""
                            SELECT 
                                EXTRACT(YEAR FROM CAST(fecha_programada AS DATE)) as año,
                                EXTRACT(MONTH FROM CAST(fecha_programada AS DATE)) as mes,
                                COUNT(*) as cantidad
                            FROM programacion_mantenimiento
                            GROUP BY año, mes
                            ORDER BY año, mes
                        """, engine)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if not mantenimientos_por_estado.empty:
                                fig = px.pie(mantenimientos_por_estado, values='cantidad', names='estado', 
                                             title="Mantenimientos por Estado",
                                             hole=0.3)
                                fig.update_traces(textinfo='percent+label+value')
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            if not mantenimientos_por_mes.empty:
                                # Crear etiquetas de fecha
                                mantenimientos_por_mes['fecha'] = mantenimientos_por_mes.apply(
                                    lambda x: f"{int(x['mes'])}/{int(x['año'])}", axis=1)
                                
                                fig = px.line(mantenimientos_por_mes, x='fecha', y='cantidad', 
                                              title="Mantenimientos programados por mes",
                                              labels={"fecha": "Mes/Año", "cantidad": "Cantidad"},
                                              markers=True, text='cantidad')
                                fig.update_traces(textposition='top center')
                                st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pueden mostrar gráficos de mantenimientos: {e}")
                
                # Botón para generar reporte
                if st.button("Generar Reporte"):
                    data = db.exportar_datos(tabla, formato)
                    if data:
                        file_ext = "xlsx" if formato == "xlsx" else "csv"
                        file_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if formato == "xlsx" else "text/csv"
                        st.download_button(
                            label=f"Descargar reporte {tabla}.{file_ext}",
                            data=data,
                            file_name=f"{tabla}_{datetime.now().strftime('%Y%m%d')}.{file_ext}",
                            mime=file_mime
                        )
                    else:
                        st.error("No se pudo generar el reporte. Verifique que la tabla contenga datos.")
            
            # Enviar reporte por email
            if user_role == 'admin':
                email_expander = st.expander("Enviar Reportes por Email")
                with email_expander:
                    email_configured = all(key in os.environ for key in ["EMAIL_HOST", "EMAIL_PORT", "EMAIL_USER", "EMAIL_PASSWORD"])
                    if not email_configured:
                        st.warning("Para enviar reportes por email, debe configurar las variables de entorno EMAIL_HOST, EMAIL_PORT, EMAIL_USER y EMAIL_PASSWORD.")
                    else:
                        email_to = st.text_input("Email del destinatario:")
                        email_subject = st.text_input("Asunto:", value="Reporte de Flota Vehicular")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            tabla_email = st.selectbox(
                                "Tabla para el reporte:", 
                                ["vehiculos", "historial_service", "incidentes", "programacion_mantenimiento"],
                                format_func=lambda x: {
                                    "vehiculos": "Vehículos", 
                                    "historial_service": "Historial de Service", 
                                    "incidentes": "Incidentes", 
                                    "programacion_mantenimiento": "Programación de Mantenimiento"
                                }.get(x, x),
                                key="email_tabla"
                            )
                        with col2:
                            formato_email = st.selectbox("Formato:", ["xlsx", "csv"], key="email_formato")
                        
                        mensaje_html = st.text_area(
                            "Mensaje:",
                            value="""
                            <html>
                            <body>
                            <h2>Reporte de Flota Vehicular</h2>
                            <p>Adjunto encontrará el reporte solicitado.</p>
                            <p>Este es un mensaje automático del Sistema de Gestión de Flota Vehicular.</p>
                            </body>
                            </html>
                            """
                        )
                        
                        if st.button("Enviar Reporte por Email"):
                            if not email_to:
                                st.error("Debe ingresar un email de destinatario.")
                            else:
                                # Obtener los datos para el reporte
                                engine = db.get_sqlalchemy_engine()
                                
                                if tabla_email == 'vehiculos':
                                    df = pd.read_sql("SELECT * FROM vehiculos", engine)
                                    nombre_archivo = "Vehículos"
                                elif tabla_email == 'historial_service':
                                    df = pd.read_sql("""
                                        SELECT s.*, v.marca, v.modelo, v.tipo
                                        FROM historial_service s
                                        JOIN vehiculos v ON s.patente = v.patente
                                        ORDER BY s.fecha DESC
                                    """, engine)
                                    nombre_archivo = "Historial_Service"
                                elif tabla_email == 'incidentes':
                                    df = pd.read_sql("""
                                        SELECT i.*, v.marca, v.modelo, v.tipo
                                        FROM incidentes i
                                        JOIN vehiculos v ON i.patente = v.patente
                                        ORDER BY i.fecha DESC
                                    """, engine)
                                    nombre_archivo = "Incidentes"
                                else:  # programacion_mantenimiento
                                    df = pd.read_sql("""
                                        SELECT m.*, v.marca, v.modelo, v.tipo, v.km as km_actual
                                        FROM programacion_mantenimiento m
                                        JOIN vehiculos v ON m.patente = v.patente
                                        ORDER BY m.fecha_programada ASC
                                    """, engine)
                                    nombre_archivo = "Mantenimientos_Programados"
                                
                                if df.empty:
                                    st.error("No hay datos para crear el reporte.")
                                else:
                                    # Enviar el reporte
                                    success = db.enviar_reporte_por_email(
                                        email=email_to,
                                        titulo=email_subject,
                                        mensaje_html=mensaje_html,
                                        df=df,
                                        formato=formato_email,
                                        nombre_archivo=nombre_archivo
                                    )
                                    
                                    if success:
                                        st.success(f"Reporte enviado correctamente a {email_to}")
                                    else:
                                        st.error("Error al enviar el reporte. Verifique la configuración de correo.")
            
            # Resumen de Servicio
            st.subheader("Resumen de Servicio")
            if not stats["service"].empty:
                st.dataframe(stats["service"], use_container_width=True)
            else:
                st.info("No hay datos de servicio para mostrar.")
        
        with tab3:
            # Alertas de VTV
            st.subheader("VTV próximas a vencer")
            vtv_proximos = stats.get("vtv_proximos")
            if vtv_proximos is not None and not vtv_proximos.empty:
                # Formatear los datos para mejor visualización
                display_df = vtv_proximos[['patente', 'marca', 'modelo', 'area', 'vtv_vencimiento']].copy()
                display_df['días_restantes'] = (pd.to_datetime(display_df['vtv_vencimiento']) - pd.to_datetime('today')).dt.days
                display_df = display_df.sort_values('días_restantes')
                
                # Mostrar con colorización por cercanía a la fecha de vencimiento
                st.dataframe(
                    display_df.style.applymap(
                        lambda x: 'background-color: #ffcccc' if isinstance(x, int) and x < 7 else '',
                        subset=['días_restantes']
                    ),
                    use_container_width=True
                )
                
                # Botón para exportar
                if st.button("Exportar listado de VTV próximas a vencer"):
                    excel_data = db.exportar_datos('vehiculos', 'xlsx')
                    if excel_data:
                        st.download_button(
                            label="Descargar Excel de VTV proximas a vencer",
                            data=excel_data,
                            file_name=f"vtv_proximas_vencer_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.info("No hay vehículos con VTV próxima a vencer en los próximos 30 días.")
            
            # Alertas de mantenimientos pendientes
            st.subheader("Mantenimientos Pendientes")
            mantenimientos = stats.get("mantenimientos", {})
            if mantenimientos and "PENDIENTE" in mantenimientos:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pendientes", mantenimientos.get("PENDIENTE", 0))
                with col2:
                    st.metric("Completados", mantenimientos.get("COMPLETADO", 0))
                with col3:
                    st.metric("Cancelados", mantenimientos.get("CANCELADO", 0))
                
                # Mostrar los próximos mantenimientos
                prox_mant = db.get_maintenance_schedules(estado="PENDIENTE", proximos_dias=30)
                if not prox_mant.empty:
                    st.write("Próximos mantenimientos (30 días):")
                    display_mant = prox_mant[['patente', 'marca', 'modelo', 'fecha_programada', 'tipo_service']].copy()
                    st.dataframe(display_mant, use_container_width=True)
                    
                    if st.button("Ver todos los mantenimientos"):
                        st.session_state.page = 'view_schedules'
                        st.rerun()
            else:
                st.info("No hay mantenimientos pendientes.")
    
    except Exception as e:
        st.error(f"Error al cargar las estadísticas: {str(e)}")

def admin_settings_page():
    st.title("Configuración del Sistema")
    
    if user_role != 'admin':
        st.error("No tiene permisos para acceder a esta sección.")
        if st.button("Volver"):
            st.session_state.page = 'home'
            st.rerun()
        return
    
    # Crear pestañas para las diferentes secciones de administración
    tabs = st.tabs(["Base de Datos", "Importación de Datos", "Configuración", "Recordatorios"])
    
    with tabs[0]:
        st.subheader("Base de Datos")
        
        if st.button("Inicializar Base de Datos"):
            db.init_database()
            st.success("Base de datos inicializada correctamente.")
        
        st.write("Esta acción creará las tablas necesarias si no existen.")
    
    with tabs[1]:
        st.subheader("Importación de Datos")
        st.write("Desde aquí puede importar datos masivamente desde archivos CSV.")
        
        # Opción para importar vehículos
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
        
        uploaded_file = st.file_uploader("Seleccionar archivo CSV", type=['csv'], key="admin_csv_uploader")
        
        if uploaded_file:
            st.write("Vista previa del archivo:")
            
            df = db.process_uploaded_file(uploaded_file)
            if df is not None:
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
    
    with tabs[2]:
        st.subheader("Configuración General")
        
        # Otras configuraciones
        st.subheader("Configuraciones del Sistema")
        st.write("Aquí se pueden agregar opciones futuras como:")
        st.write("- Gestión de usuarios y permisos")
        st.write("- Configuración de copias de seguridad")
        st.write("- Personalización de la interfaz")
        st.write("- Configuración regional y horarios")
        
        st.info("Funcionalidades adicionales en desarrollo...")
    
    with tabs[3]:
        st.subheader("Configuración de Recordatorios")
        st.info("Configure direcciones de correo electrónico para recibir recordatorios de mantenimientos programados y vencimientos de VTV.")
        
        # Verificar si tenemos las credenciales de email configuradas
        import os
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
                new_email = st.text_input("Agregar correo electrónico:")
                submitted = st.form_submit_button("Agregar")
                
                if submitted and new_email:
                    if new_email in st.session_state.email_recipients:
                        st.warning(f"El correo {new_email} ya está en la lista.")
                    else:
                        st.session_state.email_recipients.append(new_email)
                        st.success(f"Correo {new_email} agregado correctamente.")
                        st.rerun()
            
            # Separador
            st.markdown("---")
            
            # Sección para procesar recordatorios
            st.subheader("Procesar Recordatorios Pendientes")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Recordatorios de Mantenimiento", use_container_width=True):
                    if not st.session_state.email_recipients:
                        st.warning("No ha configurado ningún correo electrónico para notificaciones.")
                    elif not email_configured:
                        st.error("No se pueden enviar correos sin configurar las credenciales SMTP primero.")
                    else:
                        # Obtener recordatorios pendientes
                        reminders_df = db.get_maintenance_reminders()
                        
                        if reminders_df.empty:
                            st.info("No hay recordatorios de mantenimiento pendientes para procesar.")
                        else:
                            total = len(reminders_df)
                            email_sent = 0
                            email_failed = 0
                            
                            for _, reminder in reminders_df.iterrows():
                                # Marcar el recordatorio como enviado
                                db.update_maintenance_schedule(
                                    reminder['id'],
                                    recordatorio_enviado=True
                                )
                                
                                patente = reminder['patente']
                                vehicle = db.get_vehicle_by_patente(patente)
                                
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
                                for email in st.session_state.email_recipients:
                                    if db.send_email_notification(email, asunto, mensaje):
                                        email_sent += 1
                                    else:
                                        email_failed += 1
                            
                            # Mostrar resultados
                            st.success(f"Se procesaron {total} recordatorios pendientes.")
                            
                            if email_sent > 0:
                                st.success(f"Se enviaron {email_sent} correos electrónicos correctamente.")
                            if email_failed > 0:
                                st.warning(f"No se pudieron enviar {email_failed} correos. Verifique la configuración.")
            
            with col2:
                if st.button("Verificar Vencimientos VTV", use_container_width=True):
                    if not st.session_state.email_recipients:
                        st.warning("No ha configurado ningún correo electrónico para notificaciones.")
                    elif not email_configured:
                        st.error("No se pueden enviar correos sin configurar las credenciales SMTP primero.")
                    else:
                        # Verificar vehículos con VTV próxima a vencer
                        vtv_df = db.get_vtv_proximos_vencer(dias=30)
                        
                        if vtv_df.empty:
                            st.info("No hay vehículos con VTV próxima a vencer en los próximos 30 días.")
                        else:
                            email_sent = 0
                            email_failed = 0
                            
                            # Construir asunto
                            asunto = f"ALERTA: Vehículos con VTV próxima a vencer"
                            
                            # Construir cuerpo del mensaje HTML
                            mensaje = f"""
                            <html>
                            <body>
                            <h2>Alerta de VTV próxima a vencer</h2>
                            <p>Los siguientes vehículos tienen la VTV próxima a vencer en los próximos 30 días:</p>
                            
                            <table border="1" cellpadding="5" cellspacing="0">
                                <tr style="background-color:#f0f0f0">
                                    <th>Patente</th>
                                    <th>Marca</th>
                                    <th>Modelo</th>
                                    <th>Área</th>
                                    <th>Vencimiento VTV</th>
                                </tr>
                            """
                            
                            vtv_display = vtv_df[['patente', 'marca', 'modelo', 'area', 'vtv_vencimiento']]
                            for _, row in vtv_display.iterrows():
                                # Calcular días restantes para colorizar
                                dias_restantes = (pd.to_datetime(row['vtv_vencimiento']) - pd.to_datetime('today')).days
                                bg_color = "#ffcccc" if dias_restantes < 7 else "#ffffff"
                                
                                mensaje += f"""
                                <tr style="background-color:{bg_color}">
                                    <td>{row['patente']}</td>
                                    <td>{row['marca']}</td>
                                    <td>{row['modelo']}</td>
                                    <td>{row['area']}</td>
                                    <td>{row['vtv_vencimiento']} ({dias_restantes} días)</td>
                                </tr>
                                """
                            
                            mensaje += """
                            </table>
                            <p>Este es un mensaje automático del Sistema de Gestión de Flota Vehicular.</p>
                            </body>
                            </html>
                            """
                            
                            # Enviar el correo a cada destinatario
                            for email in st.session_state.email_recipients:
                                if db.send_email_notification(email, asunto, mensaje):
                                    email_sent += 1
                                else:
                                    email_failed += 1
                            
                            # Mostrar resultados
                            if email_sent > 0:
                                st.success(f"Se enviaron {email_sent} alertas de VTV por correo electrónico.")
                            if email_failed > 0:
                                st.warning(f"No se pudieron enviar {email_failed} correos. Verifique la configuración.")
            
            # Separador
            st.markdown("---")
            
            # Sección para ver y configurar próximos recordatorios
            st.subheader("Próximos Recordatorios")
            
            # Mostrar próximos mantenimientos programados
            prox_mant = db.get_maintenance_schedules(estado="PENDIENTE", proximos_dias=30)
            if not prox_mant.empty:
                st.write("Mantenimientos programados para los próximos 30 días:")
                display_mant = prox_mant[['patente', 'marca', 'modelo', 'fecha_programada', 'tipo_service']].copy()
                st.dataframe(display_mant, use_container_width=True)
                
                if st.button("Ver todos los mantenimientos"):
                    st.session_state.page = 'view_schedules'
                    st.rerun()
            else:
                st.info("No hay mantenimientos programados para los próximos 30 días.")
            
            # Mostrar próximos vencimientos de VTV
            vtv_proximos = db.get_vtv_proximos_vencer(30)
            if not vtv_proximos.empty:
                st.write("Vehículos con VTV próxima a vencer:")
                display_vtv = vtv_proximos[['patente', 'marca', 'modelo', 'area', 'vtv_vencimiento']].copy()
                display_vtv['días_restantes'] = (pd.to_datetime(display_vtv['vtv_vencimiento']) - pd.to_datetime('today')).dt.days
                display_vtv = display_vtv.sort_values('días_restantes')
                
                st.dataframe(display_vtv, use_container_width=True)
            else:
                st.info("No hay vehículos con VTV próxima a vencer en los próximos 30 días.")
                
        except Exception as e:
            st.error(f"Error al cargar configuración de recordatorios: {e}")

def schedule_maintenance_page():
    st.title("Programar Mantenimiento")
    
    # Si hay un vehículo seleccionado, usar ese, de lo contrario mostrar selector
    if 'selected_vehicle' in st.session_state:
        patente = st.session_state.selected_vehicle
        vehicle = db.get_vehicle_by_patente(patente)
        st.subheader(f"Programar mantenimiento para: {patente} - {vehicle['marca']} {vehicle['modelo']}")
        del st.session_state.selected_vehicle
    else:
        # Mostrar selector de vehículos
        vehicles = db.load_vehicles()
        patentes = vehicles['patente'].tolist()
        patente = st.selectbox("Seleccionar vehículo:", [""] + patentes)
        
        if not patente:
            st.info("Por favor seleccione un vehículo para programar su mantenimiento.")
            return
        
        vehicle = db.get_vehicle_by_patente(patente)
        st.subheader(f"Programar mantenimiento para: {patente} - {vehicle['marca']} {vehicle['modelo']}")
    
    # Formulario para programar mantenimiento
    with st.form("schedule_maintenance_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_programada = st.date_input("Fecha programada", value=None)
            fecha_programada_str = fecha_programada.strftime("%Y-%m-%d") if fecha_programada else None
            
        with col2:
            km_actual = vehicle['km']
            km_programado = st.number_input("Kilometraje programado", min_value=km_actual, value=km_actual + 10000, step=1000)
        
        tipo_service = st.selectbox("Tipo de service", ["COMPLETO", "INTERMEDIO", "ACEITE", "FRENOS", "BATERÍA", "NEUMÁTICOS", "OTRO"])
        descripcion = st.text_area("Descripción y detalles")
        
        submitted = st.form_submit_button("Programar Mantenimiento")
        
        if submitted:
            if not fecha_programada_str and km_programado <= km_actual:
                st.error("Debe especificar una fecha futura o un kilometraje mayor al actual.")
            else:
                result = db.add_maintenance_schedule(
                    patente=patente,
                    fecha_programada=fecha_programada_str,
                    km_programado=km_programado,
                    tipo_service=tipo_service,
                    descripcion=descripcion
                )
                
                if result:
                    st.success("Mantenimiento programado correctamente.")
                    if st.button("Ver Programación"):
                        st.session_state.page = 'view_schedules'
                        st.rerun()
                else:
                    st.error("Error al programar el mantenimiento.")
    
    st.button("Volver", on_click=lambda: setattr(st.session_state, 'page', 'home'))

def view_schedules_page():
    st.title("Programación de Mantenimiento")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estado_filter = st.selectbox(
            "Filtrar por estado:", 
            ["TODOS", "PENDIENTE", "COMPLETADO", "CANCELADO"],
            index=0
        )
        estado = None if estado_filter == "TODOS" else estado_filter
    
    with col2:
        vehicles = db.load_vehicles()
        patentes = ["TODOS"] + vehicles['patente'].tolist()
        patente_filter = st.selectbox("Filtrar por vehículo:", patentes, index=0)
        patente = None if patente_filter == "TODOS" else patente_filter
    
    with col3:
        proximos_dias = st.number_input("Próximos días:", min_value=0, value=30)
        proximos_dias = proximos_dias if proximos_dias > 0 else None
    
    # Cargar datos
    schedules = db.get_maintenance_schedules(patente=patente, estado=estado, proximos_dias=proximos_dias)
    
    if schedules.empty:
        st.info("No hay mantenimientos programados que coincidan con los filtros seleccionados.")
    else:
        # Mostrar datos
        display_cols = ['patente', 'marca', 'modelo', 'fecha_programada', 'km_programado', 'km_actual', 'tipo_service', 'estado']
        st.dataframe(schedules[display_cols], use_container_width=True)
        
        # Selector para ver detalles y acciones
        selected_id = st.selectbox(
            "Seleccionar mantenimiento para ver detalles:", 
            [""] + schedules['id'].astype(str).tolist()
        )
        
        if selected_id:
            # Mostrar detalles del mantenimiento seleccionado
            selected_schedule = schedules[schedules['id'].astype(str) == selected_id].iloc[0]
            
            st.subheader("Detalles del Mantenimiento")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Vehículo:** {selected_schedule['patente']} - {selected_schedule['marca']} {selected_schedule['modelo']}")
                st.write(f"**Tipo de Service:** {selected_schedule['tipo_service']}")
                st.write(f"**Estado:** {selected_schedule['estado']}")
                
            with col2:
                st.write(f"**Fecha programada:** {selected_schedule['fecha_programada']}")
                st.write(f"**Km programado:** {selected_schedule['km_programado']}")
                st.write(f"**Km actual:** {selected_schedule['km_actual']}")
            
            st.write("**Descripción:**")
            st.write(selected_schedule['descripcion'] or "Sin descripción")
            
            # Acciones según el estado
            if selected_schedule['estado'] == 'PENDIENTE':
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Marcar como Completado"):
                        result = db.mark_maintenance_completed(int(selected_id), service_realizado=True)
                        if result:
                            st.success("Mantenimiento marcado como completado. Se ha registrado un service.")
                            st.rerun()
                        else:
                            st.error("Error al completar el mantenimiento.")
                
                with col2:
                    if st.button("Cancelar Programación"):
                        result = db.update_maintenance_schedule(
                            id_programacion=int(selected_id),
                            estado="CANCELADO"
                        )
                        if result:
                            st.success("Programación cancelada correctamente.")
                            st.rerun()
                        else:
                            st.error("Error al cancelar la programación.")
                
                with col3:
                    if st.button("Editar"):
                        st.warning("Funcionalidad de edición en desarrollo.")
                        
            elif selected_schedule['estado'] == 'COMPLETADO':
                if st.button("Ver Historial de Service"):
                    st.session_state.selected_vehicle = selected_schedule['patente']
                    st.session_state.page = 'service_history'
                    st.rerun()
    
    st.button("Programar Nuevo Mantenimiento", on_click=lambda: setattr(st.session_state, 'page', 'schedule_maintenance'))

# Page router
if st.session_state.page == 'home':
    home_page()
elif st.session_state.page == 'view_vehicles':
    view_vehicles_page()
elif st.session_state.page == 'add_vehicle':
    add_vehicle_page()
elif st.session_state.page == 'edit_vehicle':
    edit_vehicle_page()
elif st.session_state.page == 'add_service':
    add_service_page()
elif st.session_state.page == 'service_history':
    service_history_page()
elif st.session_state.page == 'add_incident':
    add_incident_page()
elif st.session_state.page == 'view_incidents':
    view_incidents_page()
elif st.session_state.page == 'fleet_stats':
    fleet_stats_page()
elif st.session_state.page == 'admin_settings':
    admin_settings_page()
elif st.session_state.page == 'schedule_maintenance':
    schedule_maintenance_page()
elif st.session_state.page == 'view_schedules':
    view_schedules_page()
else:
    home_page()
