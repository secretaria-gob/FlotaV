import os
import json
import pickle
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from functools import wraps
from logger import get_logger

# Configurar logger
logger = get_logger('cache_manager')

# Directorio para almacenar el caché
CACHE_DIR = os.path.join(os.getcwd(), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Archivo para guardar el estado del caché
CACHE_STATE_FILE = os.path.join(CACHE_DIR, 'cache_state.json')

# Valores por defecto
DEFAULT_CACHE_TTL = 3600  # 1 hora en segundos
DEFAULT_CACHE_SIZE = 100  # Número máximo de elementos en caché
DEFAULT_CACHE_ENABLED = True

class CacheItem:
    """Clase para manejar un elemento en caché con metadatos"""
    
    def __init__(self, key, data, ttl=DEFAULT_CACHE_TTL):
        self.key = key
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.last_accessed = self.created_at
        self.access_count = 0
    
    def is_expired(self):
        """Verifica si el elemento ha expirado"""
        return datetime.now() > self.expires_at
    
    def to_dict(self):
        """Convierte el objeto a un diccionario para serialización"""
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'ttl': (self.expires_at - self.created_at).total_seconds()
        }
    
    @classmethod
    def from_dict(cls, data_dict):
        """Crea un objeto CacheItem desde un diccionario"""
        item = cls(data_dict['key'], None)
        item.created_at = datetime.fromisoformat(data_dict['created_at'])
        item.expires_at = datetime.fromisoformat(data_dict['expires_at'])
        item.last_accessed = datetime.fromisoformat(data_dict['last_accessed'])
        item.access_count = data_dict['access_count']
        return item

class CacheManager:
    """Gestor de caché en memoria con respaldo en disco"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Singleton pattern - inicializar sólo una vez
        if self._initialized:
            return
        
        self.cache = {}
        self.max_size = DEFAULT_CACHE_SIZE
        self.enabled = DEFAULT_CACHE_ENABLED
        self._initialized = True
        
        # Cargar caché existente
        self.load_cache_from_disk()
        
        # Limpiar caché al inicializar (eliminar items expirados)
        self.cleanup_expired()
    
    def generate_key(self, base_key, params=None):
        """
        Genera una clave única para el caché basada en la consulta y sus parámetros.
        
        Args:
            base_key: Clave base (generalmente el nombre de la función o consulta)
            params: Diccionario de parámetros o cualquier objeto serializable
        
        Returns:
            str: Clave única para el caché
        """
        key = str(base_key)
        
        if params:
            # Si params es un diccionario, ordenarlo para consistencia
            if isinstance(params, dict):
                # Convertir a string ordenado
                params_str = json.dumps(params, sort_keys=True)
            else:
                # Intentar serializar directamente
                try:
                    params_str = str(params)
                except:
                    params_str = str(hash(params))
            
            # Generar hash para los parámetros
            params_hash = hashlib.md5(params_str.encode()).hexdigest()
            key = f"{key}_{params_hash}"
        
        return key
    
    def get(self, key):
        """
        Obtiene un valor del caché.
        
        Args:
            key: Clave del elemento a obtener
        
        Returns:
            objeto o None: El valor almacenado o None si no existe o expiró
        """
        if not self.enabled:
            return None
        
        # Verificar si la clave existe
        if key not in self.cache:
            return None
        
        # Obtener el item y verificar si expiró
        item = self.cache[key]
        if item.is_expired():
            self.delete(key)
            return None
        
        # Actualizar metadatos de acceso
        item.last_accessed = datetime.now()
        item.access_count += 1
        
        return item.data
    
    def set(self, key, data, ttl=DEFAULT_CACHE_TTL):
        """
        Almacena un valor en el caché.
        
        Args:
            key: Clave para identificar el valor
            data: Datos a almacenar (deben ser serializables)
            ttl: Tiempo de vida en segundos (por defecto 1 hora)
        
        Returns:
            bool: True si se almacenó correctamente
        """
        if not self.enabled:
            return False
        
        # Verificar si estamos en el límite de tamaño
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.evict_oldest()
        
        # Almacenar el elemento
        self.cache[key] = CacheItem(key, data, ttl)
        
        # Guardar estado actual en disco
        self.save_cache_to_disk()
        
        return True
    
    def delete(self, key):
        """
        Elimina un elemento del caché.
        
        Args:
            key: Clave del elemento a eliminar
        
        Returns:
            bool: True si se eliminó correctamente
        """
        if key in self.cache:
            del self.cache[key]
            
            # Eliminar también el archivo de datos si existe
            data_file = os.path.join(CACHE_DIR, f"{key}.pkl")
            if os.path.exists(data_file):
                os.remove(data_file)
            
            # Guardar estado actual
            self.save_cache_to_disk()
            
            return True
        
        return False
    
    def clear(self):
        """Limpia completamente el caché"""
        # Eliminar todos los archivos de datos
        for key in self.cache.keys():
            data_file = os.path.join(CACHE_DIR, f"{key}.pkl")
            if os.path.exists(data_file):
                os.remove(data_file)
        
        # Limpiar el diccionario de caché
        self.cache.clear()
        
        # Guardar estado vacío
        self.save_cache_to_disk()
    
    def cleanup_expired(self):
        """Elimina elementos expirados del caché"""
        keys_to_delete = [key for key, item in self.cache.items() if item.is_expired()]
        
        for key in keys_to_delete:
            self.delete(key)
        
        return len(keys_to_delete)
    
    def evict_oldest(self):
        """Elimina el elemento más antiguo del caché"""
        if not self.cache:
            return
        
        # Ordenar por último acceso (más antiguo primero)
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        
        self.delete(oldest_key)
    
    def save_cache_to_disk(self):
        """Guarda el estado del caché en disco"""
        try:
            # Guardar metadatos en JSON
            cache_state = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'count': len(self.cache),
                    'max_size': self.max_size
                },
                'items': {
                    key: item.to_dict() for key, item in self.cache.items()
                }
            }
            
            with open(CACHE_STATE_FILE, 'w') as f:
                json.dump(cache_state, f, indent=2)
            
            # Guardar datos en archivos individuales (para evitar un único archivo grande)
            for key, item in self.cache.items():
                # Evitar guardar si no hay datos o si ya existe el archivo
                if item.data is None:
                    continue
                
                data_file = os.path.join(CACHE_DIR, f"{key}.pkl")
                if not os.path.exists(data_file):
                    try:
                        with open(data_file, 'wb') as f:
                            pickle.dump(item.data, f)
                    except Exception as e:
                        logger.error(f"Error al guardar datos de caché para {key}: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error al guardar caché en disco: {str(e)}")
            return False
    
    def load_cache_from_disk(self):
        """Carga el estado del caché desde disco"""
        try:
            # Verificar si existe el archivo de estado
            if not os.path.exists(CACHE_STATE_FILE):
                return False
            
            # Cargar metadatos desde JSON
            with open(CACHE_STATE_FILE, 'r') as f:
                cache_state = json.load(f)
            
            # Configurar tamaño máximo
            if 'metadata' in cache_state and 'max_size' in cache_state['metadata']:
                self.max_size = cache_state['metadata']['max_size']
            
            # Cargar elementos
            if 'items' in cache_state:
                for key, item_dict in cache_state['items'].items():
                    # Recrear el objeto CacheItem
                    item = CacheItem.from_dict(item_dict)
                    
                    # Verificar si ha expirado
                    if item.is_expired():
                        continue
                    
                    # Cargar datos desde archivo individual
                    data_file = os.path.join(CACHE_DIR, f"{key}.pkl")
                    if os.path.exists(data_file):
                        try:
                            with open(data_file, 'rb') as f:
                                item.data = pickle.load(f)
                                self.cache[key] = item
                        except Exception as e:
                            logger.error(f"Error al cargar datos de caché para {key}: {str(e)}")
            
            logger.info(f"Caché cargado desde disco: {len(self.cache)} elementos")
            return True
        except Exception as e:
            logger.error(f"Error al cargar caché desde disco: {str(e)}")
            return False

# Crear singleton del caché
cache_manager = CacheManager()

def cached(ttl=DEFAULT_CACHE_TTL):
    """
    Decorador para cachear el resultado de una función.
    
    Args:
        ttl: Tiempo de vida en segundos (por defecto 1 hora)
    
    Returns:
        decorator: Decorador para aplicar a funciones
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única para esta función y sus argumentos
            base_key = f"{func.__module__}.{func.__name__}"
            params = {'args': args, 'kwargs': kwargs}
            cache_key = cache_manager.generate_key(base_key, params)
            
            # Intentar obtener del caché
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar la función
            result = func(*args, **kwargs)
            
            # Guardar en caché
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator