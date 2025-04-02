import json
import os
import logging
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self):
        from . import CACHE_DIR
        self.cache_dir = CACHE_DIR
        
        try:
            # Crear directorio principal
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Definir y crear subdirectorios
            self.subdirs = {
                'locations': 'locations',
                'departments': 'departments',
                'assets': 'assets',
                'general': 'general',
                'requesters': 'requesters'  # Agregar subdirectorio para requesters
            }
            
            # Crear todos los subdirectorios
            for subdir in self.subdirs.values():
                subdir_path = os.path.join(self.cache_dir, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                
            logging.info(f"Cache directories created at {self.cache_dir}")
        except Exception as e:
            logging.error(f"Error creating cache directories: {e}")
            raise
    
    def get(self, key, cache_type='general', max_age_hours=24):
        """Get cached data if not expired"""
        try:
            cache_dir = self._get_cache_dir(cache_type)
            # Sanitizar la key
            key = str(key).replace('/', '_').replace('\\', '_')
            cache_file = os.path.join(cache_dir, f"{key}.json")
            
            if not os.path.exists(cache_file):
                logging.debug(f"Cache miss for {key} in {cache_type}")
                return None
                
            # Check cache age
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_age > timedelta(hours=max_age_hours):
                logging.info(f"Cache expired for {key} in {cache_type}")
                os.remove(cache_file)
                return None
                
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    logging.debug(f"Cache hit for {key} in {cache_type}")
                    return data
            except json.JSONDecodeError:
                logging.warning(f"Corrupted cache file for {key} in {cache_type}")
                os.remove(cache_file)
                return None
        except Exception as e:
            logging.error(f"Error reading cache: {e}")
            return None
    
    def set(self, key, data, cache_type='general'):
        """Save data to cache"""
        try:
            cache_dir = self._get_cache_dir(cache_type)
            os.makedirs(cache_dir, exist_ok=True)
            
            # Sanitizar la key
            key = str(key).replace('/', '_').replace('\\', '_')
            cache_file = os.path.join(cache_dir, f"{key}.json")
            
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            logging.debug(f"Cache set for {key} in {cache_type}")
        except Exception as e:
            logging.error(f"Error writing cache for {key} in {cache_type}: {e}")
    
    def _get_cache_dir(self, cache_type):
        """Get appropriate cache directory based on type"""
        if cache_type in self.subdirs:
            return os.path.join(self.cache_dir, self.subdirs[cache_type])
        return self.cache_dir
    
    def clear_cache(self, cache_type=None):
        """Clear all cache or specific cache type"""
        if cache_type:
            cache_dir = self._get_cache_dir(cache_type)
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))
        else:
            for directory in [os.path.join(self.cache_dir, 'locations'), os.path.join(self.cache_dir, 'departments'), os.path.join(self.cache_dir, 'assets'), self.cache_dir]:
                if os.path.exists(directory):
                    for file in os.listdir(directory):
                        os.remove(os.path.join(directory, file))
