from pathlib import Path
import logging
import logging.handlers
import os

# Definir rutas importantes
ROOT_DIR = Path(__file__).parent.parent
CACHE_DIR = ROOT_DIR / '.cache'
LOGS_DIR = ROOT_DIR / 'logs'

# Configurar rutas en __init__
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Configurar logging global
def setup_logging():
    log_file = LOGS_DIR / f'freshservice.log'
    
    # Formato detallado para incluir timestamps y niveles
    file_formatter = logging.Formatter(
        '\n%(asctime)s - %(name)s - %(levelname)s\n%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar manejador de archivo con rotación
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5MB 
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Configurar manejador de consola minimalista
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.WARNING)  # Solo mostrar advertencias y errores en consola
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log inicial con información del sistema
    import sys
    import platform
    
    root_logger.info("=== Freshservice Tool Started ===")
    root_logger.debug(f"Python version: {sys.version}")
    root_logger.debug(f"Platform: {platform.platform()}")
    root_logger.debug(f"Working directory: {os.getcwd()}")
    root_logger.debug(f"Log file: {log_file}")
    root_logger.debug(f"Cache directory: {CACHE_DIR}")

setup_logging()

from .managers.location_manager import LocationManager
from .managers.user_manager import UserManager
from .managers.department_manager import DepartmentManager
from .freshservice_manager import FreshServiceManager
from .config import *

__all__ = [
    'LocationManager',
    'UserManager',
    'DepartmentManager',
    'FreshServiceManager',
    'ROOT_DIR',
    'CACHE_DIR',
    'LOGS_DIR'
]
