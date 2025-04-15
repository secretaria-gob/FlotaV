import streamlit as st
from auth.authentication import check_authentication
from pages.home import home_page
from pages.vehicles import view_vehicles_page, add_vehicle_page, edit_vehicle_page
from pages.services import add_service_page, service_history_page
from pages.incidents import add_incident_page, view_incidents_page
from pages.analytics import fleet_stats_page
from pages.admin import admin_settings_page

# Configuración de la página principal
st.set_page_config(
    page_title="Sistema de Gestión de Flota Vehicular",
    page_icon="🚗",
    layout="wide"
)

# Autenticación
auth_status, user_name, username = check_authentication()
if not auth_status:
    st.stop()

# Configuración de la navegación entre páginas
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Sidebar para navegación
with st.sidebar:
    st.title("Menú")
    if st.button("Inicio", use_container_width=True):
        st.session_state.page = 'home'

    st.subheader("Vehículos")
    if st.button("Ver Vehículos", use_container_width=True):
        st.session_state.page = 'view_vehicles'
    if st.button("Agregar Vehículo", use_container_width=True):
        st.session_state.page = 'add_vehicle'
    if st.button("Editar Vehículo", use_container_width=True):
        st.session_state.page = 'edit_vehicle'

    st.subheader("Mantenimiento")
    if st.button("Registrar Service", use_container_width=True):
        st.session_state.page = 'add_service'
    if st.button("Historial de Service", use_container_width=True):
        st.session_state.page = 'service_history'

    st.subheader("Incidentes")
    if st.button("Registrar Incidente", use_container_width=True):
        st.session_state.page = 'add_incident'
    if st.button("Ver Incidentes", use_container_width=True):
        st.session_state.page = 'view_incidents'

    st.subheader("Reportes y Analíticas")
    if st.button("Estadísticas de Flota", use_container_width=True):
        st.session_state.page = 'fleet_stats'

    if st.button("Configuración Administrativa", use_container_width=True):
        st.session_state.page = 'admin_settings'

# Ruteo de las páginas principales
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
else:
    home_page()