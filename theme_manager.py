import os
import json
import streamlit as st
from logger import get_logger

# Configurar logger
logger = get_logger('theme_manager')

# Directorio para almacenar configuraciones
CONFIG_DIR = os.path.join(os.getcwd(), 'config')
os.makedirs(CONFIG_DIR, exist_ok=True)

# Archivo de configuración de temas
THEME_CONFIG_FILE = os.path.join(CONFIG_DIR, 'theme_config.json')

# Temas disponibles
THEMES = {
    'default': {
        'name': 'Tema Predeterminado',
        'primary_color': '#3872E0',
        'background_color': '#FFFFFF',
        'secondary_background_color': '#F0F2F6',
        'text_color': '#262730',
        'font': 'sans serif',
        'font_size': 'normal',
        'border_radius': '4px',
        'shadow': 'medium'
    },
    'dark': {
        'name': 'Tema Oscuro',
        'primary_color': '#4F8BF9',
        'background_color': '#0E1117',
        'secondary_background_color': '#262730',
        'text_color': '#FAFAFA',
        'font': 'sans serif',
        'font_size': 'normal',
        'border_radius': '4px',
        'shadow': 'medium'
    },
    'high_contrast': {
        'name': 'Alto Contraste',
        'primary_color': '#FFFF00',
        'background_color': '#000000',
        'secondary_background_color': '#333333',
        'text_color': '#FFFFFF',
        'font': 'sans serif',
        'font_size': 'large',
        'border_radius': '2px',
        'shadow': 'high'
    },
    'pastel': {
        'name': 'Pastel',
        'primary_color': '#FF9AA2',
        'background_color': '#FFDAC1',
        'secondary_background_color': '#E2F0CB',
        'text_color': '#555555',
        'font': 'serif',
        'font_size': 'normal',
        'border_radius': '8px',
        'shadow': 'low'
    },
    'institutional': {
        'name': 'Institucional',
        'primary_color': '#003366',
        'background_color': '#FFFFFF',
        'secondary_background_color': '#EEEEEE',
        'text_color': '#333333',
        'font': 'sans serif',
        'font_size': 'normal',
        'border_radius': '0px',
        'shadow': 'medium'
    }
}

def load_theme_config():
    """
    Carga la configuración de tema actual.
    
    Returns:
        dict: Configuración de tema
    """
    try:
        if os.path.exists(THEME_CONFIG_FILE):
            with open(THEME_CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Configuración por defecto
            return THEMES['default']
    except Exception as e:
        logger.error(f"Error al cargar configuración de tema: {str(e)}")
        return THEMES['default']

def save_theme_config(theme_config):
    """
    Guarda la configuración de tema.
    
    Args:
        theme_config: Configuración de tema a guardar
    
    Returns:
        bool: True si se guardó correctamente
    """
    try:
        with open(THEME_CONFIG_FILE, 'w') as f:
            json.dump(theme_config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error al guardar configuración de tema: {str(e)}")
        return False

def apply_custom_css():
    """
    Aplica estilos CSS personalizados basados en el tema seleccionado.
    """
    # Obtener configuración actual
    theme = get_current_theme()
    
    # Aplicar estilos CSS
    st.markdown(f"""
    <style>
        /* Estilos generales */
        body {{
            color: {theme['text_color']};
            font-family: {theme['font']};
            background-color: {theme['background_color']};
        }}
        
        /* Tamaño de fuente */
        html {{
            font-size: {
                '16px' if theme['font_size'] == 'normal' else
                '18px' if theme['font_size'] == 'large' else
                '14px' if theme['font_size'] == 'small' else
                '16px'
            };
        }}
        
        /* Tarjetas y contenedores */
        div.stButton > button {{
            border-radius: {theme['border_radius']};
            background-color: {theme['primary_color']};
            color: white;
            border: none;
            box-shadow: {
                '0 2px 5px rgba(0, 0, 0, 0.1)' if theme['shadow'] == 'low' else
                '0 4px 8px rgba(0, 0, 0, 0.2)' if theme['shadow'] == 'medium' else
                '0 6px 12px rgba(0, 0, 0, 0.3)' if theme['shadow'] == 'high' else
                'none'
            };
        }}
        
        div.stButton > button:hover {{
            filter: brightness(1.1);
        }}
        
        /* Enlaces */
        a {{
            color: {theme['primary_color']};
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        /* Tooltips personalizados */
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
            margin-left: 5px;
        }}
        
        .tooltip .tooltip-text {{
            visibility: hidden;
            background-color: {theme['secondary_background_color']};
            color: {theme['text_color']};
            text-align: center;
            border-radius: {theme['border_radius']};
            padding: 5px 10px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: {
                '0 2px 5px rgba(0, 0, 0, 0.1)' if theme['shadow'] == 'low' else
                '0 4px 8px rgba(0, 0, 0, 0.2)' if theme['shadow'] == 'medium' else
                '0 6px 12px rgba(0, 0, 0, 0.3)' if theme['shadow'] == 'high' else
                'none'
            };
            width: 200px;
        }}
        
        .tooltip:hover .tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}
        
        /* Encabezados con estilo */
        h3 {{
            color: {theme['primary_color']};
            padding-bottom: 5px;
            border-bottom: 1px solid {theme['primary_color'] + '50'};
            margin-bottom: 15px;
        }}
    </style>
    """, unsafe_allow_html=True)

def create_tooltip(icon, tooltip_text):
    """
    Crea HTML para un tooltip personalizado.
    
    Args:
        icon: Ícono o texto del tooltip
        tooltip_text: Texto a mostrar en el tooltip
    
    Returns:
        str: HTML del tooltip
    """
    return f"""
    <span class="tooltip">{icon}
        <span class="tooltip-text">{tooltip_text}</span>
    </span>
    """

def get_current_theme():
    """
    Obtiene el tema actual, primero de la sesión, luego del archivo.
    
    Returns:
        dict: Tema actual
    """
    if 'current_theme' in st.session_state:
        return st.session_state.current_theme
    
    # Cargar tema desde archivo
    theme_config = load_theme_config()
    st.session_state.current_theme = theme_config
    return theme_config

def theme_selector():
    """
    Componente para seleccionar y personalizar el tema.
    """
    # Inicializar tema actual si no existe
    if 'current_theme' not in st.session_state:
        st.session_state.current_theme = load_theme_config()
    
    st.subheader("Seleccionar Tema")
    
    # Lista de temas predefinidos
    theme_names = list(THEMES.keys())
    theme_labels = [THEMES[t]['name'] for t in theme_names]
    
    # Encontrar índice del tema actual (o usar 0 para el predeterminado)
    current_theme_config = st.session_state.current_theme
    current_theme_name = 'default'
    
    for theme_name, theme_config in THEMES.items():
        if all(current_theme_config.get(k) == v for k, v in theme_config.items() if k != 'name'):
            current_theme_name = theme_name
            break
    
    try:
        selected_index = theme_names.index(current_theme_name)
    except ValueError:
        selected_index = 0
    
    # Selector de tema
    selected_theme = st.selectbox(
        "Tema:",
        theme_labels,
        index=selected_index
    )
    
    # Obtener nombre del tema seleccionado
    selected_theme_name = theme_names[theme_labels.index(selected_theme)]
    
    # Mostrar la configuración del tema seleccionado
    st.session_state.current_theme = THEMES[selected_theme_name].copy()
    
    # Opciones avanzadas
    with st.expander("Opciones avanzadas"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.current_theme['font_size'] = st.selectbox(
                "Tamaño de fuente:",
                ["small", "normal", "large"],
                index=["small", "normal", "large"].index(
                    st.session_state.current_theme.get('font_size', 'normal')
                )
            )
            
            st.session_state.current_theme['shadow'] = st.selectbox(
                "Sombras:",
                ["none", "low", "medium", "high"],
                index=["none", "low", "medium", "high"].index(
                    st.session_state.current_theme.get('shadow', 'medium')
                )
            )
        
        with col2:
            st.session_state.current_theme['border_radius'] = st.selectbox(
                "Bordes redondeados:",
                ["0px", "2px", "4px", "8px", "12px"],
                index=["0px", "2px", "4px", "8px", "12px"].index(
                    st.session_state.current_theme.get('border_radius', '4px')
                )
            )
            
            st.session_state.current_theme['font'] = st.selectbox(
                "Tipografía:",
                ["sans serif", "serif", "monospace"],
                index=["sans serif", "serif", "monospace"].index(
                    st.session_state.current_theme.get('font', 'sans serif')
                )
            )
    
    # Guardar configuración
    if st.button("Aplicar tema"):
        # Guardar en archivo
        success = save_theme_config(st.session_state.current_theme)
        
        if success:
            st.success("Tema aplicado correctamente. Los cambios se verán reflejados al recargar la página.")
            
            # Aplicar inmediatamente
            apply_custom_css()
            
            # Mostrar botón para recargar
            if st.button("Recargar página"):
                st.rerun()
        else:
            st.error("Error al guardar la configuración del tema.")
    
    # Vista previa
    st.subheader("Vista previa")
    
    with st.container():
        st.markdown(f"""
        <div style="padding: 1em; background-color: {st.session_state.current_theme['secondary_background_color']}; border-radius: {st.session_state.current_theme['border_radius']}; margin-bottom: 1em;">
            <h4 style="color: {st.session_state.current_theme['primary_color']};">Ejemplo de encabezado</h4>
            <p style="color: {st.session_state.current_theme['text_color']}; font-family: {st.session_state.current_theme['font']};">
                Este es un ejemplo de texto con el tema seleccionado. La configuración de colores,
                tipografía y otros estilos se aplicará a toda la aplicación.
            </p>
            <a href="#" style="color: {st.session_state.current_theme['primary_color']};">Ejemplo de enlace</a>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar botón de ejemplo
        st.button("Botón de ejemplo", key="preview_button")
        
        # Ejemplo de tooltip
        st.markdown(
            f"Campo con tooltip {create_tooltip('❓', 'Este es un ejemplo de tooltip con el tema seleccionado.')}",
            unsafe_allow_html=True
        )