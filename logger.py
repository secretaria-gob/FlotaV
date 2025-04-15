import os
import logging
import traceback
from datetime import datetime

# Directorio para almacenar logs
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Formato de logs
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
ACCESS_LOG_FORMAT = '%(asctime)s - %(message)s'

# Configura un diccionario para almacenar los loggers y evitar duplicados
LOGGERS = {}

def get_logger(name, level=logging.INFO):
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo para el logger
        level: Nivel de logging (por defecto INFO)
    
    Returns:
        logging.Logger: Logger configurado
    """
    # Si ya existe el logger, devolverlo directamente
    if name in LOGGERS:
        return LOGGERS[name]
    
    # Crear y configurar el logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicación de handlers
    if not logger.handlers:
        # Handler para archivo
        log_file = os.path.join(LOG_DIR, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
        
        # Handler para consola (sólo para desarrollo)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
    
    # Almacenar en el diccionario
    LOGGERS[name] = logger
    
    return logger

def get_access_logger():
    """
    Obtiene un logger específico para registrar accesos y eventos de usuario.
    
    Returns:
        logging.Logger: Logger configurado para accesos
    """
    name = 'access'
    
    # Si ya existe el logger, devolverlo directamente
    if name in LOGGERS:
        return LOGGERS[name]
    
    # Crear y configurar el logger de acceso
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Evitar duplicación de handlers
    if not logger.handlers:
        # Handler para archivo
        log_file = os.path.join(LOG_DIR, "access.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(ACCESS_LOG_FORMAT))
        logger.addHandler(file_handler)
    
    # Almacenar en el diccionario
    LOGGERS[name] = logger
    
    return logger

def log_exception(logger, exception, message="Se produjo una excepción"):
    """
    Registra una excepción con el traceback completo.
    
    Args:
        logger: Logger a utilizar
        exception: Excepción a registrar
        message: Mensaje descriptivo opcional
    """
    error_msg = f"{message}: {str(exception)}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    
    return error_msg

def log_access(username, action, details=None):
    """
    Registra una acción de usuario en el log de acceso.
    
    Args:
        username: Nombre de usuario que realiza la acción
        action: Tipo de acción (login, logout, view, edit, delete, etc.)
        details: Detalles adicionales de la acción
    """
    access_logger = get_access_logger()
    
    if details:
        access_logger.info(f"USER: {username} | ACTION: {action} | DETAILS: {details}")
    else:
        access_logger.info(f"USER: {username} | ACTION: {action}")

# Crear logger principal de la aplicación
app_logger = get_logger('app')
app_logger.info(f"Logger inicializado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")