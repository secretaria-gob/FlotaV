import os
import re
import json
import io
import tempfile
import pytesseract
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image
import streamlit as st
from logger import get_logger

# Configurar logger
logger = get_logger('ocr')

# Patrones regex para extraer información
PATRONES = {
    'fecha': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+de\s+[a-zA-ZáéíóúÁÉÍÓÚ]+\s+de\s+\d{2,4})',
    'monto': r'(?:total|importe|monto|valor)[\s:]*[$\s]*([0-9.,]+)',
    'patente': r'(?:patente|dominio)[:\s]*([A-Z0-9]{6,7})',
    'km': r'(?:km|kilom[eé]tr[oa][js]?)[:\s]*([0-9.,]+)',
    'factura_numero': r'(?:factura|fact)[:\s]*(?:n[°º]|numero|nro)[:\s]*([A-Z0-9\-]+)'
}

def procesar_ocr(archivo, idioma='spa'):
    """
    Procesa un archivo PDF utilizando OCR para extraer texto.
    
    Args:
        archivo: Bytes del archivo PDF o ruta al archivo
        idioma: Código del idioma para OCR (por defecto español)
    
    Returns:
        dict: Diccionario con el texto extraído y metadatos
    """
    try:
        # Detectar si es bytes o ruta
        if isinstance(archivo, bytes):
            # Convertir PDF a imágenes
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(archivo)
                temp_pdf_path = temp_pdf.name
            
            try:
                images = convert_from_bytes(archivo)
            except Exception as e:
                logger.error(f"Error al convertir PDF a imágenes desde bytes: {str(e)}")
                # Intentar con la ruta temporal
                images = convert_from_path(temp_pdf_path)
                
            # Eliminar archivo temporal
            os.unlink(temp_pdf_path)
        else:
            # Convertir PDF a imágenes desde ruta
            images = convert_from_path(archivo)
        
        # Procesar cada página con OCR
        text_completo = ""
        paginas = []
        
        for i, img in enumerate(images):
            # Realizar OCR
            texto_pagina = pytesseract.image_to_string(img, lang=idioma)
            text_completo += texto_pagina + "\n\n"
            paginas.append(texto_pagina)
        
        # Extraer información relevante
        info_extraida = extraer_informacion(text_completo)
        
        return {
            'texto_completo': text_completo,
            'paginas': paginas,
            'num_paginas': len(paginas),
            'informacion_extraida': info_extraida
        }
        
    except Exception as e:
        logger.error(f"Error en procesamiento OCR: {str(e)}")
        return {
            'texto_completo': "",
            'paginas': [],
            'num_paginas': 0,
            'informacion_extraida': {},
            'error': str(e)
        }

def extraer_informacion(texto):
    """
    Extrae información relevante del texto procesado.
    
    Args:
        texto: Texto completo extraído por OCR
    
    Returns:
        dict: Información extraída según patrones
    """
    resultado = {}
    
    # Normalizar texto (convertir a minúsculas y quitar múltiples espacios)
    texto_norm = re.sub(r'\s+', ' ', texto.lower())
    
    # Aplicar patrones
    for campo, patron in PATRONES.items():
        matches = re.findall(patron, texto_norm, re.IGNORECASE)
        if matches:
            # Para algunos campos, queremos el primer match
            if campo in ['patente', 'factura_numero']:
                # Limpiar caracteres no deseados y espacios
                valor = re.sub(r'[^\w\-]', '', matches[0]).strip()
                resultado[campo] = valor
            # Para montos y km, queremos convertir a números
            elif campo in ['monto', 'km']:
                # Limpiar caracteres no numéricos excepto punto y coma
                valor = re.sub(r'[^\d.,]', '', matches[0]).strip()
                # Convertir a formato numérico (reemplazar coma por punto)
                valor = valor.replace(',', '.')
                try:
                    resultado[campo] = float(valor)
                except:
                    resultado[campo] = valor
            # Para fechas, mantener formato original
            else:
                resultado[campo] = matches[0].strip()
    
    return resultado

def procesar_pdfs_para_service(archivos_pdf):
    """
    Procesa archivos PDF para extraer información relevante para registros de servicio.
    
    Args:
        archivos_pdf: Lista de archivos PDF subidos por el usuario
    
    Returns:
        tuple: (texto_extraido, informacion_extraida, pdf_files_json)
    """
    try:
        if not archivos_pdf:
            return "", {}, None
        
        texto_extraido = []
        informacion_extraida = {
            'fecha': None,
            'monto': None,
            'km': None,
            'taller': None,
            'factura_numero': None
        }
        
        # Procesar cada PDF
        for archivo in archivos_pdf:
            # Procesar con OCR
            resultado_ocr = procesar_ocr(archivo.read())
            texto_extraido.append(f"--- {archivo.name} ---\n{resultado_ocr['texto_completo']}\n")
            
            # Actualizar información extraída
            for campo, valor in resultado_ocr['informacion_extraida'].items():
                if campo in informacion_extraida and not informacion_extraida[campo]:
                    informacion_extraida[campo] = valor
        
        # También procesar los PDFs para guardarlos en la base de datos
        import database as db  # Importar aquí para evitar dependencias circulares
        pdf_files_json = db.process_pdf_files(archivos_pdf)
        
        return "\n".join(texto_extraido), informacion_extraida, pdf_files_json
    
    except Exception as e:
        logger.error(f"Error al procesar PDFs para service: {str(e)}")
        return f"Error al procesar PDFs: {str(e)}", {}, None

def mostrar_resultados_ocr(texto, informacion):
    """
    Muestra resultados de OCR en la interfaz de Streamlit.
    
    Args:
        texto: Texto completo extraído
        informacion: Información estructurada extraída
    """
    # Mostrar información extraída
    st.subheader("Información extraída automáticamente")
    
    if not informacion:
        st.info("No se pudo extraer información automáticamente.")
        return
    
    # Crear columnas para mostrar datos
    cols = st.columns(3)
    
    # Mostrar cada campo extraído
    campos = [
        ("Fecha", informacion.get('fecha')),
        ("Monto", f"${informacion.get('monto')}" if informacion.get('monto') else None),
        ("Kilometraje", f"{informacion.get('km')} km" if informacion.get('km') else None),
        ("Factura", informacion.get('factura_numero')),
        ("Patente", informacion.get('patente')),
        ("Taller", informacion.get('taller'))
    ]
    
    for i, (label, valor) in enumerate(campos):
        with cols[i % 3]:
            if valor:
                st.info(f"**{label}:** {valor}")
    
    # Mostrar texto completo extraído
    with st.expander("Ver texto completo extraído"):
        st.text_area("Texto extraído por OCR", texto, height=300)

def buscar_texto_en_pdfs(texto_busqueda, json_pdfs):
    """
    Busca texto en PDFs previamente procesados.
    
    Args:
        texto_busqueda: Texto a buscar
        json_pdfs: JSON con datos de PDFs almacenados
    
    Returns:
        list: Lista de coincidencias encontradas
    """
    try:
        if not json_pdfs or not texto_busqueda:
            return []
        
        # Convertir JSON a objeto Python
        pdf_data = json.loads(json_pdfs)
        resultados = []
        
        for pdf in pdf_data:
            # Si el PDF ya tiene texto extraído por OCR
            if 'texto_ocr' in pdf and pdf['texto_ocr']:
                if texto_busqueda.lower() in pdf['texto_ocr'].lower():
                    resultados.append({
                        'nombre': pdf['nombre'],
                        'fecha': pdf.get('fecha', 'Desconocida'),
                        'url': pdf['url'] if 'url' in pdf else None
                    })
            else:
                # Si no tiene texto extraído, procesar el PDF
                # Esto requeriría acceso al archivo, lo cual no es viable aquí
                # ya que solo tenemos el JSON con las referencias
                pass
        
        return resultados
    
    except Exception as e:
        logger.error(f"Error al buscar texto en PDFs: {str(e)}")
        return []

def interfaz_busqueda_pdf():
    """
    Crea una interfaz para buscar texto en PDFs almacenados.
    """
    st.subheader("Búsqueda en documentos")
    
    # Campo de búsqueda
    texto_busqueda = st.text_input("Buscar texto en documentos PDF almacenados:")
    
    # Opciones de búsqueda
    col1, col2 = st.columns(2)
    with col1:
        tipo_doc = st.selectbox(
            "Tipo de documento:",
            ["Todos", "Servicios", "Incidentes", "Vehículos"]
        )
    
    with col2:
        fecha_desde = st.date_input("Desde fecha:", value=None)
    
    # Ejecutar búsqueda
    if st.button("Buscar") and texto_busqueda:
        with st.spinner("Buscando en documentos..."):
            # Aquí se necesitaría consultar la base de datos para obtener los PDFs
            # según los criterios seleccionados
            st.info("Esta función requiere conexión a la base de datos.")
            st.error("Característica en desarrollo - la búsqueda aún no está implementada en la base de datos.")