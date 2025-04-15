import os
import streamlit as st
from theme_manager import create_tooltip
from PIL import Image
from logger import get_logger

# Configurar logger
logger = get_logger('documentation')

# Directorio para imágenes y recursos
DOCS_DIR = os.path.join(os.getcwd(), 'docs')
os.makedirs(DOCS_DIR, exist_ok=True)

# Imágenes estáticas para la documentación
IMAGES = {
    'main_screen': os.path.join(DOCS_DIR, 'main_screen.png'),
    'vehicle_form': os.path.join(DOCS_DIR, 'vehicle_form.png'),
    'service_history': os.path.join(DOCS_DIR, 'service_history.png'),
    'stats_dashboard': os.path.join(DOCS_DIR, 'stats_dashboard.png'),
    'maintenance_schedule': os.path.join(DOCS_DIR, 'maintenance_schedule.png')
}

# Diccionario de tooltips para cada formulario
TOOLTIPS = {
    # Vehículos
    'patente': 'Formato de patente Mercosur: AA123BB, o formato antiguo: ABC123',
    'area': 'Departamento o área a la que está asignado el vehículo',
    'tipo': 'Categoría del vehículo según su tipo y uso',
    'marca': 'Marca del fabricante del vehículo',
    'modelo': 'Modelo específico del vehículo',
    'año': 'Año de fabricación del vehículo, entre 1950 y el año actual',
    'km': 'Kilometraje actual del vehículo',
    'estado': 'Estado operativo actual del vehículo',
    'rori': 'Número de identificación RORI (si aplica)',
    'id_vehiculo': 'Número de identificación interno del vehículo',
    'vtv_vencimiento': 'Fecha de vencimiento de la Verificación Técnica Vehicular',
    
    # Servicios
    'fecha_service': 'Fecha en que se realizó el servicio',
    'tipo_service': 'Categoría del servicio realizado',
    'taller': 'Nombre del taller o lugar donde se realizó el servicio',
    'costo': 'Costo total del servicio en pesos',
    'descripcion': 'Detalle de las tareas realizadas y repuestos utilizados',
    
    # Incidentes
    'tipo_incidente': 'Categoría del incidente (Accidente, Avería, etc.)',
    'estado_incidente': 'Estado actual del incidente (Pendiente, Resuelto, etc.)',
    
    # Mantenimiento programado
    'fecha_programada': 'Fecha planificada para realizar el mantenimiento',
    'km_programado': 'Kilometraje al que se debe realizar el mantenimiento',
    'descripcion_mant': 'Detalles de las tareas a realizar',
    
    # Otros
    'pdf_files': 'Archivos PDF con documentación relacionada (facturas, informes, etc.)'
}

def get_tooltip_html(field_name):
    """
    Genera el HTML para un tooltip.
    
    Args:
        field_name: Nombre del campo para el que se genera el tooltip
    
    Returns:
        str: HTML con el tooltip o texto vacío si no existe
    """
    if field_name in TOOLTIPS:
        return create_tooltip(
            '❓', 
            TOOLTIPS[field_name]
        )
    return ''

def styled_header(title, tooltip=None, icon=None):
    """
    Crea un encabezado con estilo y tooltip opcional.
    
    Args:
        title: Título del encabezado
        tooltip: Texto del tooltip (opcional)
        icon: Icono a mostrar (opcional)
    """
    icon_html = f"{icon} " if icon else ""
    tooltip_html = f" {get_tooltip_html(tooltip)}" if tooltip else ""
    
    st.markdown(
        f"<h3 style='color: #3872E0; margin-bottom: 10px;'>{icon_html}{title}{tooltip_html}</h3>",
        unsafe_allow_html=True
    )

def display_manual():
    """
    Muestra el manual de usuario en la interfaz.
    """
    st.title("Manual de Usuario - Sistema de Gestión de Flota Vehicular")
    
    # Tabla de contenidos
    st.sidebar.title("Contenido")
    sections = [
        "Introducción",
        "Gestión de Vehículos",
        "Registros de Servicio",
        "Incidentes",
        "Programación de Mantenimiento",
        "Estadísticas y Reportes",
        "Administración",
        "Resolución de Problemas"
    ]
    
    selected_section = st.sidebar.radio("Ir a:", sections)
    
    # Sección de introducción
    if selected_section == "Introducción":
        st.header("Introducción")
        
        st.write("""
        El Sistema de Gestión de Flota Vehicular es una herramienta integral diseñada para optimizar la administración
        de flotas de vehículos. Este sistema permite el seguimiento detallado de vehículos, mantenimientos,
        incidentes y proporaciona análisis estadísticos para la toma de decisiones.
        """)
        
        st.subheader("Características principales")
        features = {
            "🚗 Gestión de vehículos": "Registro completo de datos de cada vehículo, incluyendo kilometraje, estado y documentación.",
            "🔧 Mantenimientos": "Seguimiento de historial de servicios y programación de mantenimientos futuros.",
            "⚠️ Incidentes": "Registro y seguimiento de incidentes y averías.",
            "📊 Estadísticas": "Análisis y reportes sobre costos, uso y estado de la flota.",
            "📱 Alertas": "Notificaciones por email para mantenimientos programados y vencimientos de VTV.",
            "📁 Documentación": "Almacenamiento digital de facturas y documentos relacionados."
        }
        
        for key, value in features.items():
            st.markdown(f"**{key}:** {value}")
        
        st.subheader("Acceso al sistema")
        st.write("""
        Para acceder al sistema, ingrese con su nombre de usuario y contraseña en la pantalla de inicio.
        El sistema ofrece diferentes niveles de acceso:
        
        - **Administrador**: Acceso completo a todas las funcionalidades.
        - **Gestor**: Puede administrar vehículos y mantenimientos, pero no tiene acceso a configuraciones avanzadas.
        - **Usuario**: Puede visualizar información y generar reportes, pero no puede realizar modificaciones.
        """)
        
        # Mostrar imagen si existe
        if os.path.exists(IMAGES.get('main_screen', '')):
            try:
                image = Image.open(IMAGES['main_screen'])
                st.image(image, caption="Pantalla principal del sistema", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        else:
            st.info("La imagen de la pantalla principal no está disponible.")
    
    # Sección de gestión de vehículos
    elif selected_section == "Gestión de Vehículos":
        st.header("Gestión de Vehículos")
        
        st.write("""
        La gestión de vehículos es una funcionalidad central del sistema que permite registrar,
        actualizar y consultar toda la información relevante sobre cada unidad de la flota.
        """)
        
        st.subheader("Agregar un nuevo vehículo")
        st.write("""
        Para agregar un nuevo vehículo al sistema:
        
        1. Seleccione "Agregar Vehículo" en el menú lateral.
        2. Complete el formulario con todos los datos del vehículo.
        3. Los campos marcados con * son obligatorios.
        4. Puede adjuntar documentación en formato PDF (opcional).
        5. Haga clic en "Guardar" para registrar el vehículo.
        """)
        
        # Información sobre campos
        st.subheader("Descripción de campos")
        
        campos = {
            "Patente*": "Identificador único del vehículo. " + TOOLTIPS.get('patente', ''),
            "Área*": "Departamento o área a la que está asignado el vehículo.",
            "Tipo*": "Categoría del vehículo (AUTO, CAMIONETA, MOTO, etc.).",
            "Marca*": "Marca del fabricante.",
            "Modelo*": "Modelo específico del vehículo.",
            "Año*": "Año de fabricación, debe ser entre 1950 y el año actual.",
            "Estado*": "Estado operativo (SERVICIO, RECUPERAR, RADIADO).",
            "Kilometraje": "Odómetro actual del vehículo.",
            "ID Vehículo": "Número de identificación interno asignado al vehículo.",
            "RORI": "Número de identificación RORI si aplica.",
            "Vencimiento VTV": "Fecha de vencimiento de la Verificación Técnica Vehicular.",
            "Fecha último service": "Fecha en que se realizó el último mantenimiento.",
            "Taller": "Nombre del taller donde se realizó el último service.",
            "Observaciones": "Notas adicionales sobre el vehículo."
        }
        
        # Mostrar campos en dos columnas
        col1, col2 = st.columns(2)
        
        items = list(campos.items())
        mid = len(items) // 2
        
        with col1:
            for key, value in items[:mid]:
                st.markdown(f"**{key}:** {value}")
        
        with col2:
            for key, value in items[mid:]:
                st.markdown(f"**{key}:** {value}")
        
        # Importación desde CSV
        st.subheader("Importación masiva de vehículos")
        st.write("""
        El sistema permite la importación masiva de vehículos desde archivos CSV:
        
        1. Prepare un archivo CSV con las columnas necesarias (patente, área, tipo, marca, modelo, año, estado, km).
        2. Vaya a la pestaña "Importar desde CSV" en la pantalla de Agregar Vehículo.
        3. Seleccione el archivo y haga clic en "Importar vehículos".
        4. El sistema validará los datos y mostrará resultados de la importación.
        """)
        
        st.subheader("Editar vehículo")
        st.write("""
        Para modificar los datos de un vehículo existente:
        
        1. Seleccione "Editar Vehículo" en el menú lateral.
        2. Seleccione el vehículo a editar de la lista desplegable.
        3. Actualice los campos necesarios.
        4. Haga clic en "Guardar cambios".
        """)
        
        # Mostrar imagen si existe
        if os.path.exists(IMAGES.get('vehicle_form', '')):
            try:
                image = Image.open(IMAGES['vehicle_form'])
                st.image(image, caption="Formulario de vehículo", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        st.info("ℹ️ Todos los cambios quedan registrados en el historial del sistema para auditoría.")
    
    # Sección de registros de servicio
    elif selected_section == "Registros de Servicio":
        st.header("Registros de Servicio")
        
        st.write("""
        El módulo de registros de servicio permite documentar todos los mantenimientos, reparaciones
        y servicios realizados a los vehículos de la flota.
        """)
        
        st.subheader("Agregar un nuevo registro de servicio")
        st.write("""
        Para agregar un nuevo registro de servicio:
        
        1. Seleccione "Registrar Service" en el menú lateral.
        2. Seleccione el vehículo para el que desea registrar el servicio.
        3. Complete el formulario con los detalles del servicio.
        4. Adjunte documentación de respaldo si es necesario (facturas, informes).
        5. Haga clic en "Guardar" para registrar el servicio.
        """)
        
        # Descripción de campos
        st.subheader("Descripción de campos")
        
        campos_service = {
            "Fecha*": "Fecha en que se realizó el servicio.",
            "Kilometraje*": "Lectura del odómetro al momento del servicio.",
            "Tipo de servicio*": "Categoría del servicio (ej. Cambio de aceite, Service completo).",
            "Taller*": "Nombre del taller o proveedor que realizó el servicio.",
            "Costo*": "Costo total del servicio en pesos.",
            "Descripción*": "Detalle de las tareas realizadas y repuestos utilizados.",
            "Documentación adjunta": "Archivos PDF con facturas u otros documentos relacionados."
        }
        
        for key, value in campos_service.items():
            st.markdown(f"**{key}:** {value}")
        
        st.subheader("Consultar historial de servicios")
        st.write("""
        Para consultar el historial de servicios:
        
        1. Seleccione "Historial de Service" en el menú lateral.
        2. Puede filtrar por vehículo específico o ver todos los registros.
        3. Los registros se muestran ordenados por fecha (más recientes primero).
        4. Puede descargar el historial completo en formato Excel o CSV.
        """)
        
        # Mostrar imagen si existe
        if os.path.exists(IMAGES.get('service_history', '')):
            try:
                image = Image.open(IMAGES['service_history'])
                st.image(image, caption="Historial de servicios", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        st.subheader("Extracción automática de datos de facturas")
        st.write("""
        El sistema cuenta con OCR (Reconocimiento Óptico de Caracteres) para extraer automáticamente
        información de facturas y documentos PDF:
        
        1. Al adjuntar un documento PDF, el sistema intentará extraer:
           - Fecha del servicio
           - Monto
           - Kilometraje
           - Número de factura
           - Patente del vehículo
        
        2. Los datos extraídos se sugieren automáticamente en el formulario.
        3. Siempre verifique la información extraída antes de guardar.
        """)
        
        st.info("ℹ️ Los servicios registrados actualizan automáticamente el kilometraje y la fecha del último service del vehículo.")
    
    # Sección de incidentes
    elif selected_section == "Incidentes":
        st.header("Gestión de Incidentes")
        
        st.write("""
        El módulo de incidentes permite registrar y dar seguimiento a eventos como accidentes,
        averías, robos u otras situaciones que afecten a los vehículos de la flota.
        """)
        
        st.subheader("Registrar un nuevo incidente")
        st.write("""
        Para registrar un nuevo incidente:
        
        1. Seleccione "Registrar Incidente" en el menú lateral.
        2. Seleccione el vehículo involucrado en el incidente.
        3. Complete el formulario con los detalles del incidente.
        4. Adjunte documentación relevante (fotos, denuncias, informes).
        5. Haga clic en "Guardar" para registrar el incidente.
        """)
        
        # Descripción de campos
        st.subheader("Descripción de campos")
        
        campos_incidente = {
            "Fecha*": "Fecha en que ocurrió el incidente.",
            "Tipo*": "Categoría del incidente (Accidente, Avería, Robo, Otro).",
            "Descripción*": "Detalle completo del incidente, incluyendo circunstancias y consecuencias.",
            "Estado*": "Estado actual del incidente (PENDIENTE, EN PROCESO, RESUELTO, CERRADO).",
            "Documentación adjunta": "Archivos PDF con informes, denuncias, presupuestos u otros documentos."
        }
        
        for key, value in campos_incidente.items():
            st.markdown(f"**{key}:** {value}")
        
        st.subheader("Consultar y gestionar incidentes")
        st.write("""
        Para consultar y gestionar incidentes:
        
        1. Seleccione "Ver Incidentes" en el menú lateral.
        2. Los incidentes se muestran ordenados por fecha (más recientes primero).
        3. Puede filtrar por vehículo o por estado del incidente.
        4. Para actualizar el estado de un incidente, selecciónelo y use la opción "Actualizar estado".
        5. Los incidentes pendientes se muestran en el panel de inicio para seguimiento.
        """)
        
        st.warning("⚠️ Los incidentes no resueltos por más de 30 días se destacan automáticamente para seguimiento prioritario.")
        
        st.subheader("Indicadores de gestión de incidentes")
        st.write("""
        El sistema proporciona indicadores para evaluar la gestión de incidentes:
        
        - **Tiempo medio de resolución**: Promedio de días entre el registro y la resolución de incidentes.
        - **Distribución por tipo**: Cantidad de incidentes por categoría.
        - **Vehículos con mayor incidencia**: Ranking de vehículos por cantidad de incidentes.
        - **Tendencia temporal**: Evolución de incidentes a lo largo del tiempo.
        """)
        
        st.info("ℹ️ Estos indicadores se pueden consultar en la sección 'Estadísticas de Flota'.")
    
    # Sección de programación de mantenimiento
    elif selected_section == "Programación de Mantenimiento":
        st.header("Programación de Mantenimiento")
        
        st.write("""
        Este módulo permite planificar y dar seguimiento a los mantenimientos futuros de los vehículos,
        estableciendo recordatorios basados en fechas o kilometraje.
        """)
        
        st.subheader("Programar un nuevo mantenimiento")
        st.write("""
        Para programar un nuevo mantenimiento:
        
        1. Seleccione "Programar Mantenimiento" en el menú lateral.
        2. Seleccione el vehículo para el que desea programar mantenimiento.
        3. Complete el formulario definiendo si el mantenimiento se basa en:
           - Una fecha específica
           - Un kilometraje específico
           - Ambos criterios
        4. Especifique el tipo de servicio a realizar.
        5. Haga clic en "Guardar" para programar el mantenimiento.
        """)
        
        # Descripción de campos
        st.subheader("Descripción de campos")
        
        campos_programacion = {
            "Fecha programada": "Fecha en que debe realizarse el mantenimiento.",
            "Kilometraje programado": "Lectura del odómetro a la que debe realizarse el mantenimiento.",
            "Tipo de servicio*": "Categoría del servicio a realizar.",
            "Descripción*": "Detalle de las tareas a realizar.",
            "Generar recordatorio": "Si debe enviarse una notificación cuando se aproxime la fecha."
        }
        
        for key, value in campos_programacion.items():
            st.markdown(f"**{key}:** {value}")
        
        # Mostrar imagen si existe
        if os.path.exists(IMAGES.get('maintenance_schedule', '')):
            try:
                image = Image.open(IMAGES['maintenance_schedule'])
                st.image(image, caption="Programación de mantenimiento", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        st.subheader("Consultar mantenimientos programados")
        st.write("""
        Para consultar los mantenimientos programados:
        
        1. Seleccione "Ver Programación" en el menú lateral.
        2. Los mantenimientos se muestran ordenados por fecha/kilometraje.
        3. Puede filtrar por vehículo o por estado.
        4. Para marcar un mantenimiento como completado, selecciónelo y use la opción "Marcar como completado".
        5. Al marcar como completado, se puede registrar automáticamente un nuevo servicio basado en la programación.
        """)
        
        st.subheader("Sistema de recordatorios")
        st.write("""
        El sistema envía recordatorios automáticos para mantenimientos programados:
        
        - Por **fecha**: Se envían recordatorios 7 días antes de la fecha programada.
        - Por **kilometraje**: Se envían recordatorios cuando el vehículo está a 500 km del umbral programado.
        - Los recordatorios se envían por email a las direcciones configuradas.
        - En la página principal se muestra un resumen de mantenimientos próximos.
        """)
        
        st.info("ℹ️ Configure los destinatarios de recordatorios en la sección 'Configuración > Recordatorios'.")
    
    # Sección de estadísticas y reportes
    elif selected_section == "Estadísticas y Reportes":
        st.header("Estadísticas y Reportes")
        
        st.write("""
        El módulo de estadísticas y reportes proporciona análisis detallados sobre la flota
        y herramientas para generar informes personalizados.
        """)
        
        st.subheader("Dashboard de estadísticas")
        st.write("""
        Para acceder al dashboard de estadísticas:
        
        1. Seleccione "Estadísticas de Flota" en el menú lateral.
        2. El dashboard muestra:
           - Resumen general de la flota
           - Distribución por tipo, área y estado
           - Análisis de costos de mantenimiento
           - Vehículos con mayor kilometraje
           - Alertas de VTV próximas a vencer
        """)
        
        # Mostrar imagen si existe
        if os.path.exists(IMAGES.get('stats_dashboard', '')):
            try:
                image = Image.open(IMAGES['stats_dashboard'])
                st.image(image, caption="Dashboard de estadísticas", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        st.subheader("Herramientas de reporte")
        st.write("""
        El sistema ofrece diversas herramientas para generar reportes:
        
        1. **Exportación de datos**: Permite exportar cualquier tabla a formato Excel o CSV.
        2. **Envío por email**: Envía reportes directamente por correo electrónico.
        3. **Gráficos interactivos**: Visualizaciones que pueden personalizarse y descargarse.
        4. **Filtros avanzados**: Permite filtrar datos por múltiples criterios.
        """)
        
        st.subheader("Análisis predictivo")
        st.write("""
        El sistema incluye capacidades de análisis predictivo:
        
        - **Predicción de costos**: Estima costos futuros de mantenimiento basados en histórico.
        - **Previsión de mantenimientos**: Calcula cuándo se requerirán próximos servicios.
        - **Alertas predictivas**: Identifica vehículos con mayor probabilidad de incidencias.
        - **Comparativas**: Permite comparar rendimiento entre vehículos similares.
        """)
        
        st.subheader("Reportes personalizados")
        st.write("""
        Para crear reportes personalizados:
        
        1. Seleccione la tabla base para el reporte.
        2. Aplique filtros según necesite.
        3. Seleccione las columnas a incluir.
        4. Elija el formato de salida (Excel, CSV, PDF).
        5. Descargue el reporte o envíelo por email.
        """)
        
        st.info("ℹ️ Todos los reportes incluyen fecha y hora de generación y pueden incluir el logo institucional si está configurado.")
    
    # Sección de administración
    elif selected_section == "Administración":
        st.header("Administración del Sistema")
        
        st.write("""
        El módulo de administración permite configurar diversos aspectos del sistema
        y está disponible sólo para usuarios con rol de administrador.
        """)
        
        st.subheader("Configuración de la base de datos")
        st.write("""
        Para gestionar la base de datos:
        
        1. Acceda a "Configuración > Base de Datos" en el menú.
        2. Desde allí puede:
           - Inicializar o reiniciar la base de datos
           - Crear copias de seguridad
           - Restaurar desde copias previas
           - Exportar/importar datos
        
        Se recomienda crear copias de seguridad regulares para prevenir pérdida de datos.
        """)
        
        st.subheader("Importación de datos")
        st.write("""
        El sistema permite importar datos masivamente:
        
        1. Acceda a "Configuración > Importación de Datos".
        2. Seleccione el archivo CSV con los datos a importar.
        3. Verifique la vista previa para asegurar que los datos son correctos.
        4. Confirme la importación.
        
        El sistema validará los datos antes de importarlos y mostrará un resumen del resultado.
        """)
        
        st.subheader("Configuración de recordatorios")
        st.write("""
        Para configurar el sistema de recordatorios:
        
        1. Acceda a "Configuración > Recordatorios".
        2. Configure las direcciones de correo electrónico que recibirán notificaciones.
        3. Establezca los parámetros para alertas:
           - Días de anticipación para mantenimientos programados
           - Días de anticipación para vencimientos de VTV
           - Frecuencia de envío de recordatorios
        """)
        
        st.subheader("Personalización de la interfaz")
        st.write("""
        El sistema permite personalizar la interfaz:
        
        1. Acceda a "Configuración > Personalización".
        2. Seleccione el tema visual (claro, oscuro o alto contraste).
        3. Ajuste el tamaño de texto y elementos visuales.
        4. La configuración se guarda por usuario.
        """)
        
        st.subheader("Copias de seguridad")
        st.write("""
        Para gestionar copias de seguridad:
        
        1. Acceda a "Configuración > Base de Datos > Gestión de Copias".
        2. Desde allí puede:
           - Crear nuevas copias de seguridad
           - Ver copias existentes con sus fechas y contenido
           - Restaurar desde una copia
           - Exportar copias para almacenamiento externo
        
        El sistema también crea automáticamente copias de seguridad periódicas.
        """)
        
        st.warning("⚠️ La restauración de copias de seguridad sobrescribe los datos actuales. Use esta función con precaución.")
    
    # Sección de resolución de problemas
    elif selected_section == "Resolución de Problemas":
        st.header("Resolución de Problemas")
        
        st.write("""
        Esta sección proporciona soluciones a problemas comunes que pueden surgir durante el uso del sistema.
        """)
        
        st.subheader("Problemas de inicio de sesión")
        
        problemas_login = [
            ("**No puedo iniciar sesión**", """
            - Verifique que está ingresando el usuario y contraseña correctos.
            - Las credenciales distinguen entre mayúsculas y minúsculas.
            - Si olvidó su contraseña, contacte al administrador del sistema.
            """),
            
            ("**La sesión expira muy rápido**", """
            - El tiempo de inactividad para cierre automático de sesión es de 30 minutos.
            - Este valor puede ser modificado por el administrador del sistema.
            """)
        ]
        
        for titulo, solucion in problemas_login:
            st.markdown(titulo)
            st.markdown(solucion)
        
        st.subheader("Problemas con vehículos")
        
        problemas_vehiculos = [
            ("**No puedo agregar un vehículo con una patente existente**", """
            - Las patentes son identificadores únicos en el sistema.
            - Si necesita registrar un vehículo con una patente ya existente, primero debe eliminar o modificar el registro anterior.
            """),
            
            ("**Los datos de kilometraje no se actualizan**", """
            - El kilometraje se actualiza automáticamente al registrar un servicio.
            - También puede actualizarlo manualmente desde "Editar Vehículo".
            - Verifique que está ingresando un valor válido (numérico y mayor al kilometraje actual).
            """),
            
            ("**No aparecen todas las columnas en la tabla de vehículos**", """
            - Use la opción "Opciones de tabla" para seleccionar qué columnas mostrar.
            - También puede ajustar el número de registros por página.
            """)
        ]
        
        for titulo, solucion in problemas_vehiculos:
            st.markdown(titulo)
            st.markdown(solucion)
        
        st.subheader("Problemas con servicios y mantenimientos")
        
        problemas_servicios = [
            ("**No puedo marcar un mantenimiento como completado**", """
            - Verifique que tiene los permisos necesarios (rol gestor o administrador).
            - Asegúrese de que el mantenimiento no está ya marcado como completado o cancelado.
            """),
            
            ("**No se envían recordatorios de mantenimiento**", """
            - Verifique que hay direcciones de correo configuradas en "Configuración > Recordatorios".
            - Confirme que las credenciales de correo del sistema están configuradas correctamente.
            - Compruebe que los mantenimientos tienen la opción "Generar recordatorio" activada.
            """),
            
            ("**La extracción OCR no funciona correctamente**", """
            - El OCR funciona mejor con facturas escaneadas de forma clara y en formato PDF.
            - Algunas facturas pueden no ser reconocidas correctamente debido a su formato.
            - Siempre verifique manualmente la información extraída antes de guardar.
            """)
        ]
        
        for titulo, solucion in problemas_servicios:
            st.markdown(titulo)
            st.markdown(solucion)
        
        st.subheader("Problemas con reportes y estadísticas")
        
        problemas_reportes = [
            ("**Los gráficos no muestran datos**", """
            - Verifique que hay suficientes datos para generar estadísticas.
            - Algunas visualizaciones requieren un mínimo de registros para ser significativas.
            - Compruebe los filtros aplicados, pueden estar excluyendo todos los datos.
            """),
            
            ("**No puedo exportar reportes**", """
            - Verifique que hay datos disponibles para exportar.
            - Asegúrese de que tiene permisos para exportar datos.
            - Compruebe que el formato seleccionado (Excel, CSV) es compatible con su sistema.
            """),
            
            ("**Los reportes enviados por email no llegan**", """
            - Verifique que la dirección de correo es correcta.
            - Compruebe la carpeta de spam o correo no deseado.
            - Confirme que las credenciales de correo del sistema están configuradas correctamente.
            """)
        ]
        
        for titulo, solucion in problemas_reportes:
            st.markdown(titulo)
            st.markdown(solucion)
        
        st.subheader("Problemas técnicos")
        
        problemas_tecnicos = [
            ("**El sistema está lento**", """
            - El rendimiento puede verse afectado si hay muchos usuarios simultáneos.
            - Las operaciones con grandes volúmenes de datos pueden tardar más tiempo.
            - Considere reducir el rango de datos en consultas y reportes.
            """),
            
            ("**Error al restaurar copia de seguridad**", """
            - Verifique que la copia de seguridad no está corrupta.
            - Asegúrese de que no hay operaciones en curso durante la restauración.
            - Contacte con soporte técnico si el problema persiste.
            """),
            
            ("**Archivo PDF no se puede adjuntar**", """
            - El tamaño máximo para archivos PDF es de 10MB.
            - Verifique que el archivo es un PDF válido.
            - Intente optimizar el PDF para reducir su tamaño.
            """)
        ]
        
        for titulo, solucion in problemas_tecnicos:
            st.markdown(titulo)
            st.markdown(solucion)
        
        st.subheader("Contacto de soporte")
        
        st.write("""
        Si encuentra problemas que no puede resolver con esta guía, contacte con el soporte técnico:
        
        - **Email**: soporte@flota-vehicular.gob.ar
        - **Teléfono**: (0XXX) 123-4567
        - **Horario de atención**: Lunes a viernes de 8:00 a 16:00
        """)

def add_documentation_tooltips():
    """
    Función para añadir documentación en forma de tooltips a toda la aplicación.
    Esta función debe llamarse desde app.py para habilitar los tooltips.
    """
    # Aplicar tooltips a los elementos de la interfaz
    # Este código se ejecutará cuando se importe este módulo
    # y nos permitirá referenciar los tooltips desde cualquier parte de la app
    
    st.write("""
    <style>
    /* Estilos para tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted blue;
        cursor: help;
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #f0f0f0;
        color: #333;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        border: 1px solid #ccc;
        font-size: 0.8em;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)


# Función para crear un tutorial guiado
def show_tutorial():
    """
    Muestra un tutorial paso a paso para nuevos usuarios.
    """
    st.title("Tutorial Guiado - Sistema de Gestión de Flota Vehicular")
    
    # Estado actual del tutorial
    if 'tutorial_step' not in st.session_state:
        st.session_state.tutorial_step = 1
    
    # Función para avanzar al siguiente paso
    def next_step():
        st.session_state.tutorial_step += 1
    
    # Función para volver al paso anterior
    def prev_step():
        st.session_state.tutorial_step -= 1
    
    # Pasos del tutorial
    total_steps = 5
    
    # Barra de progreso
    st.progress(st.session_state.tutorial_step / total_steps)
    
    # Contenido según el paso actual
    if st.session_state.tutorial_step == 1:
        st.header("Paso 1: Introducción al Sistema")
        
        st.write("""
        Bienvenido al Sistema de Gestión de Flota Vehicular. Este tutorial le guiará a través
        de las principales funcionalidades del sistema.
        
        El sistema le permite:
        - Gestionar información completa de vehículos
        - Registrar y programar mantenimientos
        - Documentar incidentes
        - Generar reportes y estadísticas
        - Recibir alertas sobre mantenimientos y documentación
        """)
        
        # Mostrar imagen de la pantalla principal si existe
        if os.path.exists(IMAGES.get('main_screen', '')):
            try:
                image = Image.open(IMAGES['main_screen'])
                st.image(image, caption="Pantalla principal del sistema", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        st.button("Siguiente →", on_click=next_step)
    
    elif st.session_state.tutorial_step == 2:
        st.header("Paso 2: Gestión de Vehículos")
        
        st.write("""
        La gestión de vehículos es la base del sistema. Desde aquí puede:
        
        1. **Ver vehículos**: Consultar el listado completo de vehículos y sus detalles.
        2. **Agregar vehículos**: Registrar nuevas unidades en el sistema.
        3. **Editar vehículos**: Modificar datos de unidades existentes.
        
        Para agregar un vehículo:
        - Seleccione "Agregar Vehículo" en el menú lateral.
        - Complete el formulario con los datos del vehículo.
        - Haga clic en "Guardar".
        """)
        
        # Mostrar imagen del formulario si existe
        if os.path.exists(IMAGES.get('vehicle_form', '')):
            try:
                image = Image.open(IMAGES['vehicle_form'])
                st.image(image, caption="Formulario de vehículo", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("← Anterior", on_click=prev_step)
        with col2:
            st.button("Siguiente →", key="next2", on_click=next_step)
    
    elif st.session_state.tutorial_step == 3:
        st.header("Paso 3: Mantenimientos y Servicios")
        
        st.write("""
        El sistema permite gestionar el mantenimiento de los vehículos:
        
        1. **Registrar service**: Documentar mantenimientos realizados.
        2. **Historial de service**: Consultar todo el historial de servicios.
        3. **Programar mantenimiento**: Planificar futuros mantenimientos.
        
        Para registrar un servicio:
        - Seleccione "Registrar Service" en el menú lateral.
        - Seleccione el vehículo y complete los detalles del servicio.
        - Puede adjuntar facturas u otros documentos PDF.
        - El sistema puede extraer automáticamente datos de las facturas.
        """)
        
        # Mostrar imagen del historial de servicios si existe
        if os.path.exists(IMAGES.get('service_history', '')):
            try:
                image = Image.open(IMAGES['service_history'])
                st.image(image, caption="Historial de servicios", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("← Anterior", key="prev3", on_click=prev_step)
        with col2:
            st.button("Siguiente →", key="next3", on_click=next_step)
    
    elif st.session_state.tutorial_step == 4:
        st.header("Paso 4: Reportes y Estadísticas")
        
        st.write("""
        El sistema ofrece herramientas de análisis y reportes:
        
        1. **Estadísticas de flota**: Dashboard con indicadores clave.
        2. **Herramientas de reporte**: Exportación de datos y envío por email.
        3. **Gráficos interactivos**: Visualizaciones para análisis de datos.
        
        Para acceder a las estadísticas:
        - Seleccione "Estadísticas de Flota" en el menú lateral.
        - Explore las diferentes pestañas con información.
        - Use los filtros para personalizar las visualizaciones.
        - Puede exportar datos o enviar reportes por email.
        """)
        
        # Mostrar imagen del dashboard si existe
        if os.path.exists(IMAGES.get('stats_dashboard', '')):
            try:
                image = Image.open(IMAGES['stats_dashboard'])
                st.image(image, caption="Dashboard de estadísticas", use_column_width=True)
            except Exception as e:
                logger.error(f"Error al cargar imagen: {str(e)}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("← Anterior", key="prev4", on_click=prev_step)
        with col2:
            st.button("Siguiente →", key="next4", on_click=next_step)
    
    elif st.session_state.tutorial_step == 5:
        st.header("Paso 5: Configuración y Personalización")
        
        st.write("""
        Para finalizar, explore las opciones de configuración:
        
        1. **Configuración del sistema**: Accesible desde "Configuración" en el menú.
        2. **Respaldo de datos**: Cree copias de seguridad regularmente.
        3. **Personalización**: Ajuste el tema y preferencias visuales.
        
        Recuerde:
        - La configuración del sistema requiere permisos de administrador.
        - El sistema de recordatorios debe configurarse para recibir alertas.
        - Puede consultar el manual de usuario para información detallada.
        """)
        
        st.success("""
        ¡Felicidades! Ha completado el tutorial básico del Sistema de Gestión de Flota Vehicular.
        
        Para obtener más información, consulte el manual de usuario completo o contacte con soporte.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("← Anterior", key="prev5", on_click=prev_step)
        with col2:
            # Botón para reiniciar el tutorial o ir a la aplicación
            if st.button("Ir a la aplicación"):
                st.session_state.tutorial_step = 1
                st.session_state.page = 'home'
                st.rerun()

# Esta variable almacena los tooltips para poder accederlos desde cualquier parte de la app
tooltips = TOOLTIPS