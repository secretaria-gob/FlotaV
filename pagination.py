import streamlit as st
import pandas as pd
from logger import get_logger

# Configurar logger
logger = get_logger('pagination')

def crear_tabla_paginada(df, page_size=10, key_prefix="table", show_index=False):
    """
    Crea una tabla paginada a partir de un DataFrame.
    
    Args:
        df: DataFrame a mostrar
        page_size: Número de filas por página
        key_prefix: Prefijo para las claves de sesión
        show_index: Si se debe mostrar la columna de índice
    
    Returns:
        None
    """
    if df.empty:
        st.info("No hay datos para mostrar.")
        return
    
    # Inicializar estado de página si no existe
    page_key = f"{key_prefix}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    
    # Calcular número total de páginas
    n_pages = len(df) // page_size
    if len(df) % page_size != 0:
        n_pages += 1
    
    # Asegurar que la página actual es válida
    if st.session_state[page_key] >= n_pages:
        st.session_state[page_key] = n_pages - 1
    if st.session_state[page_key] < 0:
        st.session_state[page_key] = 0
    
    # Extraer página actual
    start_idx = st.session_state[page_key] * page_size
    end_idx = min(start_idx + page_size, len(df))
    page_df = df.iloc[start_idx:end_idx]
    
    # Mostrar tabla
    st.dataframe(page_df, use_container_width=True, hide_index=not show_index)
    
    # Controles de paginación
    col1, col2, col3, col4, col5 = st.columns([1, 1, 3, 1, 1])
    
    # Función para cambiar página
    def set_page(page):
        st.session_state[page_key] = page
    
    # Botones de navegación
    with col1:
        if st.button("⏮️ Inicio", key=f"{key_prefix}_first", disabled=st.session_state[page_key] == 0):
            set_page(0)
    
    with col2:
        if st.button("◀️ Anterior", key=f"{key_prefix}_prev", disabled=st.session_state[page_key] <= 0):
            set_page(st.session_state[page_key] - 1)
    
    with col3:
        st.write(f"Página {st.session_state[page_key] + 1} de {n_pages} ({len(df)} registros)")
    
    with col4:
        if st.button("▶️ Siguiente", key=f"{key_prefix}_next", disabled=st.session_state[page_key] >= n_pages - 1):
            set_page(st.session_state[page_key] + 1)
    
    with col5:
        if st.button("⏭️ Final", key=f"{key_prefix}_last", disabled=st.session_state[page_key] == n_pages - 1):
            set_page(n_pages - 1)
    
    # Selector de página
    page_options = [f"Ir a página {i+1}" for i in range(n_pages)]
    selected_page = st.selectbox(
        "Seleccionar página:", 
        page_options,
        index=st.session_state[page_key],
        key=f"{key_prefix}_page_select"
    )
    
    # Actualizar página seleccionada
    page_idx = page_options.index(selected_page)
    if page_idx != st.session_state[page_key]:
        set_page(page_idx)
        st.rerun()
    
    # Devolver rango de índices mostrados (para referencia)
    return start_idx, end_idx

def tabla_filtrable(df, filtros=None, texto_busqueda=False, titulo=None, page_size=10, key_prefix="filtrable"):
    """
    Crea una tabla filtrable y paginada.
    
    Args:
        df: DataFrame a mostrar
        filtros: Diccionario con columnas a filtrar y sus opciones
        texto_busqueda: Si se debe incluir campo de búsqueda de texto
        titulo: Título opcional para la sección
        page_size: Número de filas por página
        key_prefix: Prefijo para las claves de sesión
    
    Returns:
        DataFrame: DataFrame filtrado según selecciones
    """
    if df.empty:
        st.info("No hay datos para mostrar.")
        return df
    
    # Inicializar
    if titulo:
        st.subheader(titulo)
    
    df_filtrado = df.copy()
    
    # Contenedor para filtros
    with st.container():
        # Filtros de columnas
        if filtros:
            # Crear un acordeón para los filtros
            with st.expander("Filtros", expanded=False):
                # Organizar filtros en columnas
                n_cols = min(3, len(filtros))
                cols = st.columns(n_cols)
                
                # Inicializar estado para cada filtro si no existe
                for i, (col_name, options) in enumerate(filtros.items()):
                    filter_key = f"{key_prefix}_filter_{col_name}"
                    if filter_key not in st.session_state:
                        st.session_state[filter_key] = []
                    
                    # Asignar cada filtro a una columna
                    col_idx = i % n_cols
                    with cols[col_idx]:
                        # Si se proporciona un título personalizado para el filtro
                        titulo_filtro = options.get('titulo', f"Filtrar por {col_name}")
                        
                        # Obtener valores únicos de la columna
                        valores_unicos = df[col_name].dropna().unique().tolist()
                        valores_unicos.sort()
                        
                        # Multiselect para filtro
                        selected_values = st.multiselect(
                            titulo_filtro,
                            valores_unicos,
                            default=st.session_state[filter_key],
                            key=filter_key
                        )
                        
                        # Aplicar filtro si hay valores seleccionados
                        if selected_values:
                            df_filtrado = df_filtrado[df_filtrado[col_name].isin(selected_values)]
        
        # Campo de búsqueda por texto
        if texto_busqueda:
            search_key = f"{key_prefix}_search_text"
            if search_key not in st.session_state:
                st.session_state[search_key] = ""
            
            search_text = st.text_input(
                "Buscar:", 
                value=st.session_state[search_key],
                key=search_key
            )
            
            if search_text:
                # Buscar en todas las columnas de texto
                mask = False
                for col in df_filtrado.columns:
                    if df_filtrado[col].dtype == 'object':
                        # Convertir a string y buscar (case insensitive)
                        col_mask = df_filtrado[col].astype(str).str.contains(search_text, case=False, na=False)
                        mask = mask | col_mask
                
                df_filtrado = df_filtrado[mask]
    
    # Mostrar resultados
    st.write(f"Mostrando {len(df_filtrado)} de {len(df)} registros")
    
    # Tabla paginada con los resultados filtrados
    crear_tabla_paginada(df_filtrado, page_size=page_size, key_prefix=key_prefix)
    
    # Opciones adicionales
    with st.expander("Opciones de tabla", expanded=False):
        cols = st.columns(2)
        
        with cols[0]:
            # Selector de columnas a mostrar
            view_key = f"{key_prefix}_columns_view"
            if view_key not in st.session_state:
                st.session_state[view_key] = list(df.columns)
            
            selected_columns = st.multiselect(
                "Columnas a mostrar:",
                list(df.columns),
                default=st.session_state[view_key],
                key=view_key
            )
            
            if selected_columns:
                df_filtrado = df_filtrado[selected_columns]
        
        with cols[1]:
            # Botón para exportar
            if st.button("Exportar a Excel", key=f"{key_prefix}_export"):
                # Preparar Excel para descarga
                output = pd.ExcelWriter(f"{key_prefix}_export.xlsx")
                df_filtrado.to_excel(output)
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_filtrado.to_excel(writer, sheet_name='Datos', index=False)
                    writer.save()
                
                buffer.seek(0)
                
                # Botón de descarga
                st.download_button(
                    label="Descargar Excel",
                    data=buffer,
                    file_name=f"{key_prefix}_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    return df_filtrado