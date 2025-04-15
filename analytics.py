import io
import os
import pickle
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from logger import get_logger

# Configurar logger
logger = get_logger('analytics')

# Directorio para guardar modelos
MODELS_DIR = os.path.join(os.getcwd(), 'modelos')
os.makedirs(MODELS_DIR, exist_ok=True)

def analizar_km_por_tiempo(df_vehiculos, df_services):
    """
    Analiza el incremento de kilometraje por tiempo para cada vehículo.
    
    Args:
        df_vehiculos: DataFrame con datos de vehículos
        df_services: DataFrame con historial de servicios
    
    Returns:
        DataFrame: Análisis de incremento de kilometraje
    """
    try:
        # Verificar si hay datos suficientes
        if df_vehiculos.empty or df_services.empty:
            return pd.DataFrame()
        
        # Preparar DataFrame
        df_km = df_services[['patente', 'fecha', 'km']].copy()
        df_km['fecha'] = pd.to_datetime(df_km['fecha'])
        
        # Ordenar por patente y fecha
        df_km = df_km.sort_values(['patente', 'fecha'])
        
        # Añadir km actual de cada vehículo
        km_actuales = df_vehiculos[['patente', 'km']].copy()
        km_actuales['fecha'] = pd.to_datetime('today')
        km_actuales = km_actuales[['patente', 'fecha', 'km']]
        
        # Combinar con historial
        df_km = pd.concat([df_km, km_actuales])
        df_km = df_km.sort_values(['patente', 'fecha'])
        
        # Calcular incremento de kilometraje
        df_km['km_previo'] = df_km.groupby('patente')['km'].shift(1)
        df_km['fecha_previa'] = df_km.groupby('patente')['fecha'].shift(1)
        
        # Calcular días entre registros y km recorridos
        df_km['dias'] = (df_km['fecha'] - df_km['fecha_previa']).dt.days
        df_km['km_recorridos'] = df_km['km'] - df_km['km_previo']
        
        # Filtrar registros con valores válidos
        df_km = df_km.dropna()
        df_km = df_km[df_km['dias'] > 0]  # Evitar división por cero
        
        # Calcular km por día
        df_km['km_por_dia'] = df_km['km_recorridos'] / df_km['dias']
        
        # Añadir información del vehículo
        df_km = df_km.merge(
            df_vehiculos[['patente', 'marca', 'modelo', 'tipo', 'area']], 
            on='patente', 
            how='left'
        )
        
        # Calcular estadísticas por vehículo
        stats = df_km.groupby('patente').agg({
            'km_por_dia': ['mean', 'min', 'max', 'count'],
            'marca': 'first',
            'modelo': 'first',
            'area': 'first',
            'tipo': 'first',
            'km': 'last',
            'fecha': 'last'
        })
        
        # Aplanar columnas multi-índice
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        stats = stats.reset_index()
        
        # Estimar kilometraje anual
        stats['km_anual_estimado'] = stats['km_por_dia_mean'] * 365
        
        # Ordenar por km por día promedio (de mayor a menor)
        stats = stats.sort_values('km_por_dia_mean', ascending=False)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error en análisis de kilometraje: {str(e)}")
        return pd.DataFrame()

def predecir_proximos_mantenimientos(df_vehiculos, df_services, umbral_km=5000, umbral_dias=180):
    """
    Predice cuándo los vehículos necesitarán el próximo servicio basado en patrones históricos.
    
    Args:
        df_vehiculos: DataFrame con datos de vehículos
        df_services: DataFrame con historial de servicios
        umbral_km: Kilometraje después del cual se recomienda servicio
        umbral_dias: Días después de los cuales se recomienda servicio
    
    Returns:
        DataFrame: Predicciones de próximo mantenimiento
    """
    try:
        # Obtener análisis de kilometraje
        stats_km = analizar_km_por_tiempo(df_vehiculos, df_services)
        
        if stats_km.empty:
            return pd.DataFrame()
        
        # Preparar DataFrame para predicciones
        predicciones = stats_km[['patente', 'marca_first', 'modelo_first', 'tipo_first', 
                                'area_first', 'km_last', 'fecha_last', 'km_por_dia_mean']].copy()
        
        # Renombrar columnas
        predicciones.columns = ['patente', 'marca', 'modelo', 'tipo', 'area', 'km_actual', 
                              'ultima_fecha', 'km_por_dia']
        
        # Obtener fecha del último servicio para cada vehículo
        ultimo_service = df_services.sort_values('fecha', ascending=False).drop_duplicates('patente')
        ultimo_service = ultimo_service[['patente', 'fecha', 'km']]
        ultimo_service.columns = ['patente', 'fecha_ultimo_service', 'km_ultimo_service']
        
        # Unir con predicciones
        predicciones = predicciones.merge(ultimo_service, on='patente', how='left')
        
        # Convertir fechas
        predicciones['ultima_fecha'] = pd.to_datetime(predicciones['ultima_fecha'])
        predicciones['fecha_ultimo_service'] = pd.to_datetime(predicciones['fecha_ultimo_service'])
        
        # Si no hay fecha de último servicio, usar la fecha actual
        predicciones['fecha_ultimo_service'] = predicciones['fecha_ultimo_service'].fillna(pd.to_datetime('today'))
        predicciones['km_ultimo_service'] = predicciones['km_ultimo_service'].fillna(predicciones['km_actual'])
        
        # Cálculos para predicción
        hoy = pd.to_datetime('today')
        predicciones['dias_desde_ultimo_service'] = (hoy - predicciones['fecha_ultimo_service']).dt.days
        predicciones['km_desde_ultimo_service'] = predicciones['km_actual'] - predicciones['km_ultimo_service']
        
        # Predecir días hasta alcanzar umbral de km
        predicciones['dias_hasta_umbral_km'] = np.ceil((umbral_km - predicciones['km_desde_ultimo_service']) / 
                                                  predicciones['km_por_dia']).astype(int)
        
        # Filtrar valores negativos (ya pasaron el umbral)
        predicciones.loc[predicciones['dias_hasta_umbral_km'] < 0, 'dias_hasta_umbral_km'] = 0
        
        # Calcular fecha estimada para próximo servicio por km
        predicciones['fecha_estimada_km'] = hoy + pd.to_timedelta(predicciones['dias_hasta_umbral_km'], unit='d')
        
        # Calcular fecha estimada para próximo servicio por tiempo
        predicciones['fecha_estimada_tiempo'] = predicciones['fecha_ultimo_service'] + timedelta(days=umbral_dias)
        
        # Determinar cuál umbral se alcanzará primero
        predicciones['fecha_proximo_service'] = predicciones[['fecha_estimada_km', 'fecha_estimada_tiempo']].min(axis=1)
        predicciones['dias_hasta_service'] = (predicciones['fecha_proximo_service'] - hoy).dt.days
        
        # Clasificar urgencia
        condiciones = [
            (predicciones['dias_hasta_service'] < 0),
            (predicciones['dias_hasta_service'] <= 15),
            (predicciones['dias_hasta_service'] <= 30),
            (predicciones['dias_hasta_service'] > 30)
        ]
        valores = ['ATRASADO', 'URGENTE', 'PRÓXIMO', 'PLANIFICADO']
        predicciones['estado'] = np.select(condiciones, valores, default='DESCONOCIDO')
        
        # Ordenar por urgencia y días hasta service
        predicciones = predicciones.sort_values(['estado', 'dias_hasta_service'])
        
        return predicciones
        
    except Exception as e:
        logger.error(f"Error en predicción de mantenimientos: {str(e)}")
        return pd.DataFrame()

def crear_modelo_prediccion_costos(df_services, df_vehiculos):
    """
    Crea un modelo de regresión para predecir costos de servicio.
    
    Args:
        df_services: DataFrame con historial de servicios
        df_vehiculos: DataFrame con datos de vehículos
    
    Returns:
        tuple: (modelo, preprocesador, r2_score, error)
    """
    try:
        if df_services.empty or df_vehiculos.empty:
            return None, None, 0, "Datos insuficientes"
        
        # Preparar datos
        df = df_services.merge(
            df_vehiculos[['patente', 'marca', 'modelo', 'tipo', 'año']], 
            on='patente'
        )
        
        # Eliminar filas con costo = 0 o nulo
        df = df[df['costo'] > 0]
        df = df.dropna(subset=['costo', 'km'])
        
        if len(df) < 10:
            return None, None, 0, "Datos insuficientes (mínimo 10 registros)"
        
        # Convertir fecha a antigüedad en días
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['antiguedad_dias'] = (datetime.now() - df['fecha']).dt.days
        
        # Variables categóricas y numéricas
        categorical_features = ['marca', 'tipo', 'tipo_service']
        numeric_features = ['km', 'año', 'antiguedad_dias']
        
        # Preprocesamiento
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])
        
        # Crear pipeline con Ridge (regularización)
        model = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', Ridge(alpha=1.0))
        ])
        
        # Separar características y variable objetivo
        X = df[numeric_features + categorical_features]
        y = df['costo']
        
        # Entrenar modelo
        model.fit(X, y)
        
        # Evaluar modelo
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        
        # Guardar modelo
        modelo_path = os.path.join(MODELS_DIR, 'modelo_costos.pkl')
        with open(modelo_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Guardar columnas para referencia
        columnas = {
            'categorical_features': categorical_features,
            'numeric_features': numeric_features
        }
        columnas_path = os.path.join(MODELS_DIR, 'columnas_modelo_costos.pkl')
        with open(columnas_path, 'wb') as f:
            pickle.dump(columnas, f)
        
        logger.info(f"Modelo de predicción de costos creado. R²: {r2:.2f}, MAE: {mae:.2f}")
        
        return model, preprocessor, r2, f"R²: {r2:.2f}, Error medio: ${mae:.2f}"
        
    except Exception as e:
        logger.error(f"Error al crear modelo de predicción: {str(e)}")
        return None, None, 0, f"Error: {str(e)}"

def predecir_costo_service(vehiculo, km, tipo_service):
    """
    Predice el costo de un servicio para un vehículo específico.
    
    Args:
        vehiculo: Diccionario con datos del vehículo
        km: Kilometraje actual
        tipo_service: Tipo de servicio
    
    Returns:
        float: Costo estimado
    """
    try:
        # Cargar modelo
        modelo_path = os.path.join(MODELS_DIR, 'modelo_costos.pkl')
        columnas_path = os.path.join(MODELS_DIR, 'columnas_modelo_costos.pkl')
        
        if not os.path.exists(modelo_path) or not os.path.exists(columnas_path):
            logger.warning("No existe modelo de predicción de costos")
            return None
        
        with open(modelo_path, 'rb') as f:
            model = pickle.load(f)
        
        with open(columnas_path, 'rb') as f:
            columnas = pickle.load(f)
        
        # Crear DataFrame con datos para predicción
        data = {
            'km': km,
            'año': vehiculo.get('año', 2020),
            'antiguedad_dias': 0,  # Servicio actual
            'marca': vehiculo.get('marca', ''),
            'tipo': vehiculo.get('tipo', ''),
            'tipo_service': tipo_service
        }
        
        df_pred = pd.DataFrame([data])
        
        # Realizar predicción
        costo_estimado = model.predict(df_pred)[0]
        
        # Limitar a valores positivos y redondear
        costo_estimado = max(0, round(costo_estimado, 2))
        
        return costo_estimado
        
    except Exception as e:
        logger.error(f"Error al predecir costo de servicio: {str(e)}")
        return None

def grafico_mantenimientos_previstos(predicciones_df):
    """
    Crea un gráfico de mantenimientos previstos.
    
    Args:
        predicciones_df: DataFrame con predicciones de mantenimientos
    
    Returns:
        figura de plotly
    """
    try:
        if predicciones_df.empty:
            return None
        
        # Crear copia para no modificar el original
        df = predicciones_df.copy()
        
        # Calcular mes de cada mantenimiento previsto
        df['mes'] = df['fecha_proximo_service'].dt.strftime('%Y-%m')
        
        # Contar mantenimientos por mes
        conteo_meses = df.groupby(['mes', 'estado']).size().reset_index(name='count')
        
        # Ordenar por mes
        conteo_meses = conteo_meses.sort_values('mes')
        
        # Crear gráfico
        fig = px.bar(
            conteo_meses,
            x='mes',
            y='count',
            color='estado',
            title='Mantenimientos Previstos por Mes',
            labels={'mes': 'Mes', 'count': 'Número de Mantenimientos', 'estado': 'Urgencia'},
            color_discrete_map={
                'ATRASADO': 'red',
                'URGENTE': 'orange',
                'PRÓXIMO': 'yellow',
                'PLANIFICADO': 'green'
            }
        )
        
        # Personalizar diseño
        fig.update_layout(
            xaxis_title='Mes',
            yaxis_title='Cantidad de Mantenimientos',
            legend_title='Estado',
            template='plotly_white'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error al crear gráfico de mantenimientos: {str(e)}")
        return None

def grafico_comparativa_costos(df_services, df_vehiculos, n_last_months=12):
    """
    Crea un gráfico comparativo de costos de mantenimiento.
    
    Args:
        df_services: DataFrame con historial de servicios
        df_vehiculos: DataFrame con datos de vehículos
        n_last_months: Número de meses a considerar
    
    Returns:
        figura de plotly
    """
    try:
        if df_services.empty:
            return None
        
        # Convertir fecha a datetime
        df_services['fecha'] = pd.to_datetime(df_services['fecha'])
        
        # Filtrar por últimos N meses
        fecha_inicio = pd.to_datetime('today') - pd.DateOffset(months=n_last_months)
        df = df_services[df_services['fecha'] >= fecha_inicio].copy()
        
        if df.empty:
            return None
        
        # Añadir información del vehículo
        df = df.merge(
            df_vehiculos[['patente', 'marca', 'modelo', 'tipo', 'area']],
            on='patente',
            how='left'
        )
        
        # Crear columna de año-mes
        df['mes'] = df['fecha'].dt.strftime('%Y-%m')
        
        # Calcular costo total por vehículo y mes
        costos_vehiculo_mes = df.groupby(['patente', 'marca', 'modelo', 'mes'])['costo'].sum().reset_index()
        
        # Calcular costo promedio por área
        costos_area = df.groupby(['area', 'mes'])['costo'].mean().reset_index()
        costos_area['area'] = 'Promedio: ' + costos_area['area']
        
        # Crear gráfico
        fig = px.line(
            costos_vehiculo_mes,
            x='mes',
            y='costo',
            color='patente',
            hover_data=['marca', 'modelo'],
            title='Costos de Mantenimiento por Vehículo',
            labels={'mes': 'Mes', 'costo': 'Costo ($)', 'patente': 'Vehículo'}
        )
        
        # Agregar líneas de promedio por área
        for area in costos_area['area'].unique():
            area_data = costos_area[costos_area['area'] == area]
            fig.add_trace(
                go.Scatter(
                    x=area_data['mes'],
                    y=area_data['costo'],
                    mode='lines+markers',
                    name=area,
                    line=dict(width=3, dash='dash'),
                    marker=dict(size=8, symbol='diamond')
                )
            )
        
        # Personalizar diseño
        fig.update_layout(
            xaxis_title='Mes',
            yaxis_title='Costo de mantenimiento ($)',
            template='plotly_white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.5,
                xanchor="center",
                x=0.5
            ),
            height=600
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error al crear gráfico comparativo de costos: {str(e)}")
        return None

def dashboard_analitica(df_vehiculos, df_services, df_incidentes, df_mantenimientos):
    """
    Crea un dashboard con análisis y visualizaciones para la flota.
    
    Args:
        df_vehiculos: DataFrame con datos de vehículos
        df_services: DataFrame con historial de servicios
        df_incidentes: DataFrame con incidentes
        df_mantenimientos: DataFrame con mantenimientos programados
    """
    st.title("Dashboard Analítico de Flota")
    
    if df_vehiculos.empty:
        st.warning("No hay datos de vehículos disponibles para análisis.")
        return
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3, tab4 = st.tabs([
        "Resumen y KPIs", 
        "Predicciones", 
        "Costos y Comparativas",
        "Modelos Predictivos"
    ])
    
    with tab1:
        st.subheader("Indicadores Clave de Desempeño (KPIs)")
        
        # KPIs en tarjetas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Vehículos", 
                len(df_vehiculos),
                f"+{len(df_vehiculos[df_vehiculos['estado'] == 'SERVICIO'])} en servicio"
            )
        
        with col2:
            if not df_services.empty:
                costo_total = df_services['costo'].sum()
                costo_prom = df_services['costo'].mean()
                st.metric(
                    "Costo Total Mantenimiento", 
                    f"${costo_total:,.2f}",
                    f"${costo_prom:,.2f} promedio"
                )
            else:
                st.metric("Costo Mantenimiento", "Sin datos", "")
        
        with col3:
            if not df_incidentes.empty:
                incidentes_pendientes = len(df_incidentes[df_incidentes['estado'] == 'PENDIENTE'])
                st.metric(
                    "Incidentes Pendientes", 
                    incidentes_pendientes,
                    f"{len(df_incidentes)} totales"
                )
            else:
                st.metric("Incidentes", "Sin datos", "")
        
        with col4:
            if not df_mantenimientos.empty:
                mant_prox_30 = len(df_mantenimientos[
                    (df_mantenimientos['estado'] == 'PENDIENTE') & 
                    (pd.to_datetime(df_mantenimientos['fecha_programada']) <= pd.to_datetime('today') + timedelta(days=30))
                ])
                st.metric(
                    "Mantenimientos (30 días)", 
                    mant_prox_30,
                    f"{len(df_mantenimientos[df_mantenimientos['estado'] == 'PENDIENTE'])} pendientes"
                )
            else:
                st.metric("Mantenimientos", "Sin datos", "")
        
        # Análisis de uso por vehículo
        st.subheader("Análisis de Uso por Vehículo")
        
        if not df_services.empty:
            analisis_km = analizar_km_por_tiempo(df_vehiculos, df_services)
            
            if not analisis_km.empty:
                # Mostrar tabla con datos principales
                cols_mostrar = ['patente', 'marca_first', 'modelo_first', 'area_first',
                               'km_last', 'km_por_dia_mean', 'km_anual_estimado']
                
                df_mostrar = analisis_km[cols_mostrar].copy()
                df_mostrar.columns = ['Patente', 'Marca', 'Modelo', 'Área', 
                                     'Km Actual', 'Km/día (prom)', 'Km Anual Est.']
                
                # Formatear valores numéricos
                df_mostrar['Km/día (prom)'] = df_mostrar['Km/día (prom)'].round(1)
                df_mostrar['Km Anual Est.'] = df_mostrar['Km Anual Est.'].astype(int)
                
                st.dataframe(df_mostrar)
                
                # Gráfico de uso anual estimado
                fig_uso = px.bar(
                    analisis_km.head(10),  # Top 10 vehículos
                    x='patente',
                    y='km_anual_estimado',
                    color='area_first',
                    hover_data=['marca_first', 'modelo_first', 'km_por_dia_mean'],
                    title='Top 10 Vehículos por Uso Anual Estimado',
                    labels={
                        'patente': 'Vehículo',
                        'km_anual_estimado': 'Kilómetros Anuales Estimados',
                        'area_first': 'Área'
                    }
                )
                
                fig_uso.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_uso, use_container_width=True)
            else:
                st.info("No hay suficientes datos para el análisis de uso.")
        else:
            st.info("No hay datos de servicios para analizar el uso.")
    
    with tab2:
        st.subheader("Predicciones de Mantenimiento")
        
        if not df_services.empty:
            # Configuración para predicciones
            umbral_km = st.slider("Umbral de Km para mantenimiento", 1000, 15000, 5000, 1000)
            umbral_dias = st.slider("Umbral de días para mantenimiento", 30, 365, 180, 30)
            
            # Calcular predicciones
            predicciones = predecir_proximos_mantenimientos(
                df_vehiculos, df_services, umbral_km, umbral_dias
            )
            
            if not predicciones.empty:
                # Gráfico de mantenimientos previstos
                fig_mant = grafico_mantenimientos_previstos(predicciones)
                if fig_mant:
                    st.plotly_chart(fig_mant, use_container_width=True)
                
                # Mostrar tabla de predicciones
                st.subheader("Próximos Mantenimientos Previstos")
                
                # Formatear para visualización
                df_pred_mostrar = predicciones[[
                    'patente', 'marca', 'modelo', 'area', 'estado', 
                    'dias_hasta_service', 'fecha_proximo_service', 'km_actual'
                ]].copy()
                
                df_pred_mostrar.columns = [
                    'Patente', 'Marca', 'Modelo', 'Área', 'Urgencia',
                    'Días Restantes', 'Fecha Estimada', 'Km Actual'
                ]
                
                # Colorear por estado
                def color_estado(val):
                    if val == 'ATRASADO':
                        return 'background-color: #FFCCCC'
                    elif val == 'URGENTE':
                        return 'background-color: #FFECD9'
                    elif val == 'PRÓXIMO':
                        return 'background-color: #FFFFCC'
                    else:
                        return ''
                
                # Aplicar estilo y mostrar
                st.dataframe(
                    df_pred_mostrar.style.applymap(color_estado, subset=['Urgencia']),
                    use_container_width=True
                )
            else:
                st.info("No hay suficientes datos para realizar predicciones.")
        else:
            st.info("Se necesitan datos de servicio para generar predicciones.")
    
    with tab3:
        st.subheader("Análisis de Costos")
        
        if not df_services.empty:
            # Periodo para análisis
            meses_analisis = st.slider(
                "Meses a considerar en el análisis", 
                3, 36, 12, 3
            )
            
            # Gráfico comparativo de costos
            fig_costos = grafico_comparativa_costos(
                df_services, df_vehiculos, meses_analisis
            )
            
            if fig_costos:
                st.plotly_chart(fig_costos, use_container_width=True)
            
            # Análisis por tipo de vehículo y área
            st.subheader("Costo Promedio por Tipo de Vehículo")
            
            # Preparar datos
            df_analisis = df_services.merge(
                df_vehiculos[['patente', 'tipo', 'area', 'año']], 
                on='patente'
            )
            
            if not df_analisis.empty:
                # Costos por tipo de vehículo
                costo_tipo = df_analisis.groupby('tipo')['costo'].agg(
                    ['mean', 'median', 'sum', 'count']
                ).reset_index()
                
                costo_tipo.columns = ['Tipo', 'Promedio', 'Mediana', 'Total', 'Servicios']
                costo_tipo = costo_tipo.sort_values('Promedio', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de costo promedio por tipo
                    fig_tipo = px.bar(
                        costo_tipo,
                        x='Tipo',
                        y='Promedio',
                        color='Tipo',
                        title='Costo Promedio por Tipo de Vehículo',
                        text='Promedio'
                    )
                    fig_tipo.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
                    st.plotly_chart(fig_tipo, use_container_width=True)
                
                with col2:
                    # Tabla de costos por tipo
                    for col in ['Promedio', 'Mediana', 'Total']:
                        costo_tipo[col] = costo_tipo[col].apply(lambda x: f"${x:,.2f}")
                    
                    st.dataframe(costo_tipo, use_container_width=True)
                
                # Análisis por área
                st.subheader("Costo Total por Área")
                
                costo_area = df_analisis.groupby('area')['costo'].agg(
                    ['mean', 'sum', 'count']
                ).reset_index()
                
                costo_area.columns = ['Área', 'Promedio', 'Total', 'Servicios']
                costo_area = costo_area.sort_values('Total', ascending=False)
                
                # Gráfico de costo total por área
                fig_area = px.pie(
                    costo_area,
                    names='Área',
                    values='Total',
                    title='Distribución de Costos por Área',
                    hover_data=['Promedio', 'Servicios']
                )
                
                fig_area.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_area, use_container_width=True)
            else:
                st.info("No hay suficientes datos para el análisis de costos.")
        else:
            st.info("Se necesitan datos de servicio para analizar costos.")
    
    with tab4:
        st.subheader("Modelos Predictivos")
        
        if not df_services.empty and len(df_services) >= 10:
            # Modelo de predicción de costos
            st.write("### Modelo de Predicción de Costos de Servicio")
            
            if st.button("Entrenar Modelo de Predicción"):
                with st.spinner("Entrenando modelo..."):
                    modelo, preprocesador, r2, mensaje = crear_modelo_prediccion_costos(
                        df_services, df_vehiculos
                    )
                    
                    if modelo:
                        st.success(f"Modelo creado exitosamente. {mensaje}")
                        
                        # Mostrar ejemplo de predicción
                        st.write("### Ejemplo de Predicción")
                        
                        # Seleccionar vehículo
                        patentes = df_vehiculos['patente'].tolist()
                        patente_sel = st.selectbox("Seleccionar vehículo:", patentes)
                        
                        if patente_sel:
                            vehiculo = df_vehiculos[df_vehiculos['patente'] == patente_sel].iloc[0].to_dict()
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                km_pred = st.number_input(
                                    "Kilometraje:", 
                                    min_value=0, 
                                    value=int(vehiculo.get('km', 0))
                                )
                            
                            with col2:
                                # Obtener tipos de service únicos
                                tipos_service = df_services['tipo_service'].unique().tolist()
                                if not tipos_service:
                                    tipos_service = ['MANTENIMIENTO', 'CAMBIO ACEITE', 'REPARACIÓN']
                                
                                tipo_pred = st.selectbox(
                                    "Tipo de servicio:", 
                                    tipos_service
                                )
                            
                            if st.button("Predecir Costo"):
                                costo_pred = predecir_costo_service(
                                    vehiculo, km_pred, tipo_pred
                                )
                                
                                if costo_pred is not None:
                                    st.info(f"Costo estimado: ${costo_pred:,.2f}")
                                else:
                                    st.warning("No se pudo realizar la predicción.")
                    else:
                        st.error(f"No se pudo crear el modelo. {mensaje}")
            
            # Verificar si existe modelo guardado
            modelo_path = os.path.join(MODELS_DIR, 'modelo_costos.pkl')
            if os.path.exists(modelo_path):
                st.info("✅ Existe un modelo de predicción de costos guardado.")
            else:
                st.warning("⚠️ No hay modelo de predicción guardado. Presione 'Entrenar Modelo' para crear uno.")
        else:
            st.warning("Se necesitan al menos 10 registros de servicio para crear modelos predictivos.")
            st.info(f"Registros actuales: {0 if df_services.empty else len(df_services)}/10")

def visualizar_costos_mantenimiento(df_services, df_vehiculos):
    """
    Crea visualizaciones específicas para costos de mantenimiento.
    
    Args:
        df_services: DataFrame con historial de servicios
        df_vehiculos: DataFrame con datos de vehículos
    """
    st.title("Análisis de Costos de Mantenimiento")
    
    if df_services.empty:
        st.warning("No hay datos de servicio disponibles para análisis.")
        return
    
    # Combinar datos
    df = df_services.merge(
        df_vehiculos[['patente', 'marca', 'modelo', 'tipo', 'area', 'año']],
        on='patente',
        how='left'
    )
    
    # Convertir fecha a datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['año_service'] = df['fecha'].dt.year
    df['mes_service'] = df['fecha'].dt.month
    
    # Calcular edad del vehículo al momento del servicio
    df['edad_vehiculo'] = df['año_service'] - df['año']
    
    # Filtros en sidebar
    st.sidebar.subheader("Filtros")
    
    # Filtro por fecha
    min_fecha = df['fecha'].min()
    max_fecha = df['fecha'].max()
    
    fecha_inicio, fecha_fin = st.sidebar.date_input(
        "Rango de fechas:",
        [min_fecha, max_fecha],
        min_value=min_fecha,
        max_value=max_fecha
    )
    
    # Filtros adicionales
    areas = ['Todas'] + df['area'].unique().tolist()
    area_sel = st.sidebar.selectbox("Área:", areas)
    
    tipos = ['Todos'] + df['tipo'].unique().tolist()
    tipo_sel = st.sidebar.selectbox("Tipo de vehículo:", tipos)
    
    # Aplicar filtros
    mask = (df['fecha'] >= pd.Timestamp(fecha_inicio)) & (df['fecha'] <= pd.Timestamp(fecha_fin))
    
    if area_sel != 'Todas':
        mask &= (df['area'] == area_sel)
    
    if tipo_sel != 'Todos':
        mask &= (df['tipo'] == tipo_sel)
    
    df_filtrado = df[mask]
    
    if df_filtrado.empty:
        st.warning("No hay datos que cumplan con los filtros seleccionados.")
        return
    
    # Métricas principales
    st.subheader("Métricas de Costos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Servicios", 
            len(df_filtrado),
            f"{len(df_filtrado)/len(df)*100:.1f}% del total"
        )
    
    with col2:
        costo_total = df_filtrado['costo'].sum()
        st.metric(
            "Costo Total", 
            f"${costo_total:,.2f}",
            f"${df_filtrado['costo'].mean():,.2f} promedio"
        )
    
    with col3:
        st.metric(
            "Costo Mínimo", 
            f"${df_filtrado['costo'].min():,.2f}",
            f"${df_filtrado['costo'].median():,.2f} mediana"
        )
    
    with col4:
        st.metric(
            "Costo Máximo", 
            f"${df_filtrado['costo'].max():,.2f}"
        )
    
    # Visualizaciones
    tab1, tab2, tab3 = st.tabs(["Evolución Temporal", "Análisis por Categorías", "Detalles"])
    
    with tab1:
        # Agrupar por año-mes
        df_tiempo = df_filtrado.groupby(df_filtrado['fecha'].dt.strftime('%Y-%m'))['costo'].agg(
            ['sum', 'mean', 'count']
        ).reset_index()
        df_tiempo.columns = ['mes', 'total', 'promedio', 'servicios']
        
        # Gráfico de evolución temporal
        fig = px.line(
            df_tiempo,
            x='mes',
            y=['total', 'promedio'],
            title='Evolución de Costos por Mes',
            labels={'value': 'Costo ($)', 'mes': 'Mes', 'variable': 'Métrica'},
            line_shape='linear',
            markers=True
        )
        
        # Renombrar series
        fig.data[0].name = 'Costo Total'
        fig.data[1].name = 'Costo Promedio'
        
        # Añadir cantidad de servicios como barras
        fig2 = px.bar(
            df_tiempo,
            x='mes',
            y='servicios',
            opacity=0.3
        )
        
        # Combinar gráficos
        for trace in fig2.data:
            trace.name = 'Cantidad de Servicios'
            trace.yaxis = 'y2'
            fig.add_trace(trace)
        
        # Configurar eje Y secundario
        fig.update_layout(
            yaxis2=dict(
                title='Cantidad de Servicios',
                title_font=dict(color='gray'),
                tickfont=dict(color='gray'),
                anchor='x',
                overlaying='y',
                side='right'
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5
            ),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tendencia de costos por km
        if 'km' in df_filtrado.columns:
            st.subheader("Relación entre Kilometraje y Costos")
            
            # Gráfico de dispersión
            fig_km = px.scatter(
                df_filtrado,
                x='km',
                y='costo',
                color='tipo_service',
                size='costo',
                hover_data=['patente', 'marca', 'modelo', 'fecha'],
                title='Costos vs Kilometraje',
                trendline='ols',
                trendline_color_override='darkblue'
            )
            
            st.plotly_chart(fig_km, use_container_width=True)
    
    with tab2:
        # Análisis por tipo de servicio
        st.subheader("Costos por Tipo de Servicio")
        
        # Agrupar por tipo de servicio
        costos_tipo_service = df_filtrado.groupby('tipo_service')['costo'].agg(
            ['sum', 'mean', 'count']
        ).reset_index()
        
        costos_tipo_service.columns = ['Tipo de Servicio', 'Total', 'Promedio', 'Cantidad']
        costos_tipo_service = costos_tipo_service.sort_values('Total', ascending=False)
        
        # Gráfico de barras apiladas horizontales
        fig_tipo = px.bar(
            costos_tipo_service,
            y='Tipo de Servicio',
            x='Total',
            color='Tipo de Servicio',
            text='Total',
            orientation='h',
            title='Costo Total por Tipo de Servicio'
        )
        
        fig_tipo.update_traces(
            texttemplate='$%{text:.2f}',
            textposition='outside'
        )
        
        st.plotly_chart(fig_tipo, use_container_width=True)
        
        # Mostrar tabla con datos
        costos_tipo_service['Total'] = costos_tipo_service['Total'].apply(lambda x: f"${x:,.2f}")
        costos_tipo_service['Promedio'] = costos_tipo_service['Promedio'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(costos_tipo_service, use_container_width=True)
        
        # Análisis por marca y modelo
        st.subheader("Costos por Marca y Modelo")
        
        # Agrupar por marca y modelo
        costos_modelo = df_filtrado.groupby(['marca', 'modelo'])['costo'].agg(
            ['sum', 'mean', 'count']
        ).reset_index()
        
        costos_modelo.columns = ['Marca', 'Modelo', 'Total', 'Promedio', 'Servicios']
        costos_modelo = costos_modelo.sort_values('Total', ascending=False)
        
        # Gráfico de treemap
        fig_modelo = px.treemap(
            costos_modelo,
            path=['Marca', 'Modelo'],
            values='Total',
            color='Promedio',
            hover_data=['Servicios'],
            title='Distribución de Costos por Marca y Modelo',
            color_continuous_scale='Viridis'
        )
        
        fig_modelo.update_traces(
            texttemplate='%{label}<br>$%{value:,.2f}'
        )
        
        st.plotly_chart(fig_modelo, use_container_width=True)
    
    with tab3:
        # Tabla detallada de servicios
        st.subheader("Detalle de Servicios")
        
        # Opciones de agrupación
        grupo_options = ['Ninguna', 'Mensual', 'Por vehículo', 'Por tipo de servicio', 'Por área']
        agrupacion = st.selectbox("Agrupar por:", grupo_options)
        
        if agrupacion == 'Ninguna':
            # Mostrar todos los servicios
            cols_mostrar = ['fecha', 'patente', 'marca', 'modelo', 'km', 
                           'tipo_service', 'costo', 'descripcion']
            
            df_mostrar = df_filtrado[cols_mostrar].copy()
            df_mostrar.columns = ['Fecha', 'Patente', 'Marca', 'Modelo', 'Kilometraje', 
                                  'Tipo', 'Costo', 'Descripción']
            
            # Formatear costo
            df_mostrar['Costo'] = df_mostrar['Costo'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_mostrar, use_container_width=True)
            
        elif agrupacion == 'Mensual':
            # Agrupar por mes
            df_mensual = df_filtrado.groupby(df_filtrado['fecha'].dt.strftime('%Y-%m'))['costo'].agg(
                ['sum', 'mean', 'count']
            ).reset_index()
            
            df_mensual.columns = ['Mes', 'Total', 'Promedio', 'Servicios']
            
            # Formatear valores
            df_mensual['Total'] = df_mensual['Total'].apply(lambda x: f"${x:,.2f}")
            df_mensual['Promedio'] = df_mensual['Promedio'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_mensual, use_container_width=True)
            
        elif agrupacion == 'Por vehículo':
            # Agrupar por vehículo
            df_vehiculo = df_filtrado.groupby(['patente', 'marca', 'modelo'])['costo'].agg(
                ['sum', 'mean', 'count']
            ).reset_index()
            
            df_vehiculo.columns = ['Patente', 'Marca', 'Modelo', 'Total', 'Promedio', 'Servicios']
            df_vehiculo = df_vehiculo.sort_values('Total', ascending=False)
            
            # Formatear valores
            df_vehiculo['Total'] = df_vehiculo['Total'].apply(lambda x: f"${x:,.2f}")
            df_vehiculo['Promedio'] = df_vehiculo['Promedio'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_vehiculo, use_container_width=True)
            
        elif agrupacion == 'Por tipo de servicio':
            # Ya calculado arriba, usar esos datos
            st.dataframe(costos_tipo_service, use_container_width=True)
            
        elif agrupacion == 'Por área':
            # Agrupar por área
            df_area = df_filtrado.groupby('area')['costo'].agg(
                ['sum', 'mean', 'count']
            ).reset_index()
            
            df_area.columns = ['Área', 'Total', 'Promedio', 'Servicios']
            df_area = df_area.sort_values('Total', ascending=False)
            
            # Formatear valores
            df_area['Total'] = df_area['Total'].apply(lambda x: f"${x:,.2f}")
            df_area['Promedio'] = df_area['Promedio'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_area, use_container_width=True)
        
        # Exportar datos
        if st.button("Exportar datos a Excel"):
            # Preparar datos para exportar
            df_export = df_filtrado.copy()
            
            # Crear buffer en memoria
            buffer = io.BytesIO()
            
            # Escribir a Excel
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, sheet_name='Datos', index=False)
                
                # Acceder al objeto workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Datos']
                
                # Formato para moneda
                formato_moneda = workbook.add_format({'num_format': '$#,##0.00'})
                
                # Aplicar formato a columna de costo
                col_idx = df_export.columns.get_loc('costo')
                worksheet.set_column(col_idx, col_idx, 15, formato_moneda)
                
                # Ajustar ancho de columnas
                for i, col in enumerate(df_export.columns):
                    column_width = max(len(str(col)), df_export[col].astype(str).map(len).max())
                    worksheet.set_column(i, i, column_width + 2)
            
            # Descargar Excel
            buffer.seek(0)
            fecha_actual = datetime.now().strftime('%Y%m%d')
            
            st.download_button(
                label="Descargar Excel",
                data=buffer,
                file_name=f"costos_mantenimiento_{fecha_actual}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )