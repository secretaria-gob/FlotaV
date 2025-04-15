import re
from datetime import datetime
from logger import get_logger

# Configurar logger
logger = get_logger('validators')

def validar_patente(patente):
    """
    Valida que la patente tenga un formato válido (formato Mercosur o antiguo argentino).
    
    Args:
        patente: Patente/dominio a validar
    
    Returns:
        tuple: (es_valida, mensaje)
    """
    if not patente:
        return False, "La patente no puede estar vacía"
    
    # Convertir a mayúsculas y eliminar espacios
    patente = patente.upper().strip()
    
    # Validar según formato:
    # - Formato antiguo: ABC123 o ABC-123
    # - Formato Mercosur: AA123BB o AA123CD
    patron_antiguo = r'^[A-Z]{3}[\s-]?[0-9]{3}$'
    patron_mercosur = r'^[A-Z]{2}[\s-]?[0-9]{3}[\s-]?[A-Z]{2}$'
    
    if re.match(patron_antiguo, patente) or re.match(patron_mercosur, patente):
        # Remover guiones o espacios para almacenamiento
        patente_limpia = re.sub(r'[\s-]', '', patente)
        return True, patente_limpia
    
    return False, "Formato de patente inválido. Use formato argentino (ABC123) o Mercosur (AB123CD)"

def validar_entero_positivo(valor, minimo=None, maximo=None, obligatorio=True):
    """
    Valida que un valor sea un entero positivo dentro de un rango.
    
    Args:
        valor: Valor a validar
        minimo: Valor mínimo aceptable (opcional)
        maximo: Valor máximo aceptable (opcional)
        obligatorio: Si es False, permite valores nulos
    
    Returns:
        tuple: (es_valido, mensaje)
    """
    # Permitir valores vacíos si no es obligatorio
    if not obligatorio and (valor is None or valor == ''):
        return True, None
    
    # Validar que sea un número
    try:
        valor_int = int(valor)
    except (ValueError, TypeError):
        return False, "Debe ser un número entero válido"
    
    # Validar que sea positivo
    if valor_int < 0:
        return False, "Debe ser un número positivo"
    
    # Validar mínimo si se especifica
    if minimo is not None and valor_int < minimo:
        return False, f"Debe ser mayor o igual a {minimo}"
    
    # Validar máximo si se especifica
    if maximo is not None and valor_int > maximo:
        return False, f"Debe ser menor o igual a {maximo}"
    
    return True, None

def validar_decimal_positivo(valor, decimales=2, minimo=None, maximo=None, obligatorio=True):
    """
    Valida que un valor sea un número decimal positivo.
    
    Args:
        valor: Valor a validar
        decimales: Cantidad de decimales a permitir
        minimo: Valor mínimo aceptable (opcional)
        maximo: Valor máximo aceptable (opcional)
        obligatorio: Si es False, permite valores nulos
    
    Returns:
        tuple: (es_valido, mensaje)
    """
    # Permitir valores vacíos si no es obligatorio
    if not obligatorio and (valor is None or valor == ''):
        return True, None
    
    # Validar que sea un número
    try:
        valor_float = float(valor)
    except (ValueError, TypeError):
        return False, "Debe ser un número válido"
    
    # Validar que sea positivo
    if valor_float < 0:
        return False, "Debe ser un número positivo"
    
    # Validar mínimo si se especifica
    if minimo is not None and valor_float < minimo:
        return False, f"Debe ser mayor o igual a {minimo}"
    
    # Validar máximo si se especifica
    if maximo is not None and valor_float > maximo:
        return False, f"Debe ser menor o igual a {maximo}"
    
    # Validar decimales
    str_valor = str(valor_float)
    if '.' in str_valor:
        if len(str_valor.split('.')[1]) > decimales:
            return False, f"Debe tener máximo {decimales} decimales"
    
    return True, None

def validar_texto(texto, min_longitud=1, max_longitud=None, obligatorio=True, patron=None):
    """
    Valida que un texto cumpla con ciertos criterios.
    
    Args:
        texto: Texto a validar
        min_longitud: Longitud mínima (por defecto 1)
        max_longitud: Longitud máxima (opcional)
        obligatorio: Si es False, permite valores vacíos
        patron: Patrón regex para validar formato (opcional)
    
    Returns:
        tuple: (es_valido, mensaje)
    """
    # Permitir valores vacíos si no es obligatorio
    if not obligatorio and (texto is None or texto == ''):
        return True, None
    
    # Validar que no sea None
    if texto is None:
        return False, "El texto no puede ser nulo"
    
    # Convertir a string si no lo es
    if not isinstance(texto, str):
        texto = str(texto)
    
    # Validar longitud mínima
    if len(texto) < min_longitud:
        return False, f"Debe tener al menos {min_longitud} caracteres"
    
    # Validar longitud máxima si se especifica
    if max_longitud is not None and len(texto) > max_longitud:
        return False, f"Debe tener máximo {max_longitud} caracteres"
    
    # Validar patrón si se especifica
    if patron is not None and not re.match(patron, texto):
        return False, "Formato de texto inválido"
    
    return True, None

def validar_fecha(fecha, obligatorio=True, formato="%Y-%m-%d"):
    """
    Valida que una fecha tenga un formato válido.
    
    Args:
        fecha: Fecha a validar (string)
        obligatorio: Si es False, permite valores vacíos
        formato: Formato esperado para la fecha
    
    Returns:
        tuple: (es_valido, mensaje)
    """
    # Permitir valores vacíos si no es obligatorio
    if not obligatorio and (fecha is None or fecha == ''):
        return True, None
    
    if fecha is None or fecha == '':
        return False, "La fecha no puede estar vacía"
    
    # Intentar convertir la fecha al formato especificado
    try:
        if isinstance(fecha, str):
            datetime.strptime(fecha, formato)
        else:
            # Si es un objeto datetime, ya es válido
            if not isinstance(fecha, datetime):
                raise ValueError("Formato de fecha inválido")
        
        return True, None
    except ValueError as e:
        return False, f"Formato de fecha inválido. Use {formato}"

def sanitizar_input(texto):
    """
    Sanitiza un texto para prevenir inyección SQL.
    
    Args:
        texto: Texto a sanitizar
    
    Returns:
        str: Texto sanitizado
    """
    if texto is None:
        return None
    
    # Convertir a string si no lo es
    if not isinstance(texto, str):
        texto = str(texto)
    
    # Eliminar caracteres peligrosos para SQL
    # Esta es una sanitización básica, en producción se recomienda usar
    # consultas parametrizadas (lo cual ya implementamos)
    texto = texto.replace("'", "''")  # Escapar comillas simples
    texto = texto.replace(";", "")   # Eliminar punto y coma
    texto = texto.replace("--", "")  # Eliminar comentarios SQL
    texto = texto.replace("/*", "").replace("*/", "")  # Eliminar comentarios multi-línea
    texto = texto.replace("xp_", "")  # Eliminar procedimientos extendidos (SQL Server)
    
    return texto

def validar_email(email):
    """
    Valida que un email tenga un formato válido.
    
    Args:
        email: Email a validar
    
    Returns:
        tuple: (es_valido, mensaje)
    """
    if not email:
        return False, "El email no puede estar vacío"
    
    # Patrón para validar emails
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(patron, email):
        return True, None
    
    return False, "Formato de email inválido"