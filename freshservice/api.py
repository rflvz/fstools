from functools import lru_cache
import json
import requests
import time
from colorama import Fore, Style, init
import os
from dotenv import load_dotenv
from .cache_manager import CacheManager
from .config import CACHE_CONFIG
import logging

class FreshServiceAPI:
    def __init__(self):
        init(autoreset=True)
        load_dotenv()
        self.subdomain = os.getenv('FRESHSERVICE_SUBDOMAIN')
        self.api_key = os.getenv('FRESHSERVICE_API_KEY')
        self.base_url = f'https://{self.subdomain}.freshservice.com/api/v2/'
        self.request_counter = 0
        self.cache = CacheManager()
        self.logger = logging.getLogger(__name__)

    def handle_rate_limit(self, response):
        """Handle API rate limiting"""
        if response.status_code == 429:
            wait_time = int(response.headers.get('Retry-After', 60))
            print(f"{Fore.YELLOW}Rate limit reached. Waiting {wait_time} seconds...{Style.RESET_ALL}")
            time.sleep(wait_time)
            self.request_counter = 0
            return True
        return False

    def get_cached_request(self, endpoint):
        """Get cached request or make new one"""
        try:
            # Determinar el tipo de caché basado en el endpoint
            endpoint_parts = endpoint.split('/')
            cache_type = endpoint_parts[0] if endpoint_parts else 'general'
            
            logging.debug(f"Checking cache for endpoint: {endpoint} (type: {cache_type})")
            
            # Verificar si el endpoint está en la lista de excluidos
            if cache_type in CACHE_CONFIG.get('excluded_endpoints', []):
                logging.debug(f"Endpoint {endpoint} excluded from cache")
                return self.make_request(endpoint)
            
            # Intentar obtener de la caché
            cached_data = self.cache.get(endpoint, cache_type=cache_type)
            if cached_data is not None:
                logging.info(f"Cache hit for {endpoint}")
                return cached_data
            
            # Si no está en caché, hacer la petición
            logging.debug(f"Cache miss for {endpoint}, making request")
            data = self.make_request(endpoint)
            
            # Guardar en caché si la petición fue exitosa
            if data is not None:
                logging.debug(f"Caching response for {endpoint}")
                self.cache.set(endpoint, data, cache_type=cache_type)
            
            return data
            
        except Exception as e:
            logging.error(f"Error in cached request for {endpoint}: {e}")
            return self.make_request(endpoint)

    def make_request(self, endpoint, method='GET', params=None, data=None):
        """Make API request with simplified logging"""
        endpoint = endpoint.lstrip('/')
        url = f'{self.base_url}{endpoint}'
        
        logger = logging.getLogger(__name__)
        logger.info(f"API Request: {method} {url}")
        
        try:
            response = requests.request(
                method,
                url,
                auth=(self.api_key, ''),
                params=params,
                json=data,
                timeout=30
            )
            
            logger.info(f"Response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")
                return None
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None

    def fetch_all_pages(self, endpoint, key):
        page = 1
        all_data = []
        while True:
            data = self.make_request(f"{endpoint}?page={page}")
            if not data or key not in data or not data[key]:
                break
            all_data.extend(data[key])
            page += 1
        return all_data

    def fetch_paginated_data(self, endpoint, query=''):
        """Fetch all paginated data from an endpoint"""
        all_data = []
        page = 1
        while True:
            separator = '&' if '?' in query else '?'
            data = self.make_request(f'{endpoint}{query}{separator}page={page}')
            if not data:
                break
                
            # Extract data based on endpoint type
            key = endpoint.split('/')[0]  # assets, departments, locations, etc.
            if key in data and data[key]:
                all_data.extend(data[key])
                page += 1
            else:
                break
        return all_data

    def get_cached_data(self, url):
        """Get cached data from API"""
        return self.get_cached_request(url)
