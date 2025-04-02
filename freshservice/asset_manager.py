import requests
from .api import FreshServiceAPI
from .component_manager import ComponentManager
from .managers.location_manager import LocationManager
from .managers.user_manager import UserManager
from .managers.department_manager import DepartmentManager
from .excel_manager import ExcelManager
import pandas as pd
from tqdm import tqdm
import os
from colorama import Fore, Style, init
import logging
import time

logger = logging.getLogger(__name__)

class AssetManager(FreshServiceAPI):
    def __init__(self):
        super().__init__()
        init(autoreset=True)  # Inicializar colorama
        self.component_manager = ComponentManager(self)
        self.location_manager = LocationManager(self)
        self.user_manager = UserManager(self)
        self.department_manager = DepartmentManager(self)
        self.excel_manager = ExcelManager()

    def get_asset(self, asset_id):
        """Get asset data by ID"""
        response = self.make_request(f'assets/{asset_id}')
        return response.get('asset') if response else None

    def get_departments(self):
        """Get all departments using correct API URL and handling"""
        try:
            data = self.make_request('departments')
            if data and 'departments' in data:
                return {dept['id']: dept['name'] for dept in data['departments']}
            return {}
        except Exception as e:
            print(f"{Fore.RED}Error getting departments: {e}")
            return {}

    def get_locations(self):
        """Get all locations with proper API URL"""
        url = f'https://{self.subdomain}.freshservice.com/api/v2/locations/'
        data = self.fetch_paginated_data('locations')
        return {loc['id']: loc['name'] for loc in data} if data else {}

    def get_all_locations(self):
        """Get all locations with complete data"""
        locations = self.fetch_paginated_data('locations')
        return sorted(locations, key=lambda x: x.get('name', '')) if locations else []

    def process_asset_ids(self, ids_input, exclude_input=None):
        """Process asset IDs from input"""
        ids = []
        if os.path.isfile(ids_input):
            if ids_input.endswith('.xlsx') or ids_input.endswith('.xls'):
                # Leer Excel y tomar primera columna
                try:
                    df = pd.read_excel(ids_input)
                    if not df.empty:
                        # Convertir primera columna a números y eliminar duplicados
                        numbers = pd.to_numeric(df.iloc[:, 0], errors='coerce')
                        ids = sorted(set([int(x) for x in numbers.dropna()]))
                except Exception as e:
                    print(f"{Fore.RED}Error reading Excel file: {e}")
                    return []
            else:
                # Mantener lógica existente para archivos txt
                with open(ids_input, 'r') as file:
                    ids = file.read().strip().split(',')
        else:
            ids = ids_input.split(',')

        expanded_ids = []
        for id_part in ids:
            id_part = str(id_part).strip()
            if '-' in id_part:
                try:
                    start, end = map(int, id_part.split('-'))
                    expanded_ids.extend(range(start, end + 1))
                except ValueError:
                    print(f"{Fore.RED}Error: Invalid range '{id_part}'. Skipping.")
            elif str(id_part).replace('.0', '').isdigit():  # Manejar números con .0 desde Excel
                expanded_ids.append(int(float(id_part)))
            elif id_part.isdigit():
                expanded_ids.append(int(id_part))
            else:
                print(f"{Fore.RED}Error: Invalid ID '{id_part}'. Skipping.")

        # Eliminar duplicados y ordenar
        expanded_ids = sorted(set(expanded_ids))

        if exclude_input:
            exclude_ids = self.process_asset_ids(exclude_input)
            expanded_ids = [id_ for id_ in expanded_ids if id_ not in exclude_ids]

        return expanded_ids

    def process_assets(self, asset_ids, options):
        """Process multiple assets with options"""
        total = len(asset_ids)
        start_time = time.time()

        # Configurar barra de progreso más visible y descriptiva
        progress_bar = tqdm(
            asset_ids,
            desc=f"{Fore.CYAN}Processing assets{Style.RESET_ALL}",
            total=total,
            unit="asset",
            leave=True,
            ncols=100,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        )

        times_per_asset = []
        all_data = []

        for asset_id in progress_bar:
            asset_start = time.time()
            
            try:
                asset_data = self._process_single_asset(asset_id, options)
                if asset_data:
                    all_data.extend(asset_data if isinstance(asset_data, list) else [asset_data])
                
                # Actualizar estadísticas
                asset_time = time.time() - asset_start
                times_per_asset.append(asset_time)
                avg_time = sum(times_per_asset) / len(times_per_asset)
                
                # Actualizar descripción de la barra con más detalles
                progress_bar.set_description(
                    f"{Fore.CYAN}Processing assets{Style.RESET_ALL} "
                    f"(avg: {avg_time:.1f}s/asset)"
                )
            
            except Exception as e:
                logger.error(f"Error processing asset {asset_id}: {str(e)}")
                continue

        total_time = time.time() - start_time
        print(f"\n{Fore.GREEN}✓ Completed processing {total} assets in {total_time:.1f}s")
        
        if times_per_asset:
            print(f"{Fore.CYAN}Statistics:")
            print(f"  Average time per asset: {sum(times_per_asset)/len(times_per_asset):.1f}s")
            print(f"  Fastest asset: {min(times_per_asset):.1f}s")
            print(f"  Slowest asset: {max(times_per_asset):.1f}s")

        return all_data

    def process_asset(self, asset_id, options):
        """Public method to process a single asset"""
        return self._process_single_asset(asset_id, options)

    def _process_single_asset(self, asset_id, options):
        """Process single asset with all possible options"""
        try:
            # Obtener datos básicos del asset
            asset_data = self.get_asset(asset_id)
            if not asset_data:
                logger.warning(f"Asset {asset_id} not found")
                return None

            # Crear diccionario base con display_id y name
            result = {
                'display_id': asset_data.get('display_id'),
                'name': asset_data.get('name', 'Unknown')
            }

            # Procesar componentes si se solicitan
            if options.get('components'):
                logger.debug("Processing components")
                components = self.component_manager.get_components(
                    asset_id,
                    join=not options.get('disable_join', False),
                    combine_cpu_ram=options.get('combine_cpu_ram', False),
                    specified_components=options['components']
                )
                if components and len(components) > 0:
                    result.update(components[0])
                    logger.debug(f"Updated result with components: {result}")

            # Procesar opciones adicionales
            if options.get('include_departments'):
                dept_name = self._get_department_name(asset_data)
                result['department'] = dept_name
                logger.debug(f"Added department: {dept_name}")

            if options.get('include_user'):
                user_info = self._get_user_info(asset_data)
                if user_info:
                    result['user'] = user_info
                    logger.debug(f"Added user info: {user_info}")

            if options.get('include_location'):
                location = self._get_location_name(asset_data)
                result['location'] = location
                logger.debug(f"Added location: {location}")

            if options.get('include_system_os'):
                os_info = self._get_system_os(asset_id)
                result['system_os'] = os_info
                logger.debug(f"Added OS info: {os_info}")

            if options.get('include_machine_ip'):
                ip = self._get_machine_ip(asset_id)
                result['machine_ip'] = ip
                logger.debug(f"Added IP: {ip}")

            if options.get('include_machine_mac'):
                mac = self._get_machine_mac(asset_id)
                result['machine_mac'] = mac
                logger.debug(f"Added MAC: {mac}")

            if options.get('include_serial_number'):
                serial = self._get_serial_number(asset_id)
                result['serial_number'] = serial
                logger.debug(f"Added serial number: {serial}")

            if options.get('include_description'):
                desc = self._get_asset_description(asset_id)
                result['description'] = desc
                logger.debug(f"Added description")

            logger.info(f"Completed processing asset {asset_id}")
            logger.debug(f"Final result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error processing asset {asset_id}: {str(e)}")
            return None

    def _create_asset_info_dict(self, asset_id, asset_info, system_info):
        """Create dictionary with asset information"""
        info = {'asset_id': asset_id}
        if asset_info:
            if asset_info.get('department_name'):
                info['department_name'] = asset_info['department_name']
            if asset_info.get('asset_type'):
                info['asset_type'] = asset_info['asset_type']
            if asset_info.get('location_name'):
                info['location_name'] = asset_info['location_name']
            if asset_info.get('user_info'):
                info.update({
                    'user_first_name': asset_info['user_info'].get('first_name'),
                    'user_last_name': asset_info['user_info'].get('last_name'),
                    'user_email': asset_info['user_info'].get('primary_email')
                })
            if asset_info.get('description'):
                info['description'] = asset_info['description']

        # Agregar información del sistema
        for key, value in system_info.items():
            if value is not None:
                info[key] = value

        return info

    def _gather_asset_info(self, asset_id, options):
        """Gather all required information for an asset"""
        asset_data = self.get_asset(asset_id) if options.get('include_asset_data') else None
        
        info = {
            "asset_data": asset_data,
            "department_name": self._get_department_name(asset_data) if options.get('include_departments') else None,
            "asset_type": self._get_asset_type(asset_data) if options.get('include_asset_type') else None,
            "location_name": self._get_location_name(asset_data) if options.get('include_location') else None,
            "user_info": self._get_user_info(asset_data) if options.get('include_user') else None,
            "system_os": self._get_system_os(asset_id) if options.get('include_system_os') else None,
            "machine_ip": self._get_machine_ip(asset_id) if options.get('include_machine_ip') else None,
            "machine_mac": self._get_machine_mac(asset_id) if options.get('include_machine_mac') else None,
            "serial_number": self._get_serial_number(asset_id) if options.get('include_serial_number') else None
        }
        
        return info

    def _get_system_os(self, asset_id):
        """Get system OS information"""
        response = self.make_request(f'assets/{asset_id}?include=type_fields')
        if response and 'asset' in response:
            type_fields = response['asset'].get('type_fields', {})
            return type_fields.get('os_23001176139', 'Unknown')
        return 'Unknown'

    def _get_machine_ip(self, asset_id):
        """Get machine IP information"""
        response = self.make_request(f'assets/{asset_id}?include=type_fields')
        if response and 'asset' in response:
            type_fields = response['asset'].get('type_fields', {})
            return type_fields.get('computer_ip_address_23001176139', 'Unknown')
        return 'Unknown'

    def _get_machine_mac(self, asset_id):
        """Get machine MAC information"""
        response = self.make_request(f'assets/{asset_id}?include=type_fields')
        if response and 'asset' in response:
            type_fields = response['asset'].get('type_fields', {})
            return type_fields.get('mac_address_23001176139', 'Unknown')
        return 'Unknown'

    def _get_serial_number(self, asset_id):
        """Get machine serial number"""
        response = self.make_request(f'assets/{asset_id}?include=type_fields')
        if response and 'asset' in response:
            type_fields = response['asset'].get('type_fields', {})
            return type_fields.get('serial_number_23001176134', 'Unknown')
        return 'Unknown'

    def export_data(self, data, output_file=None, verbose=True):
        """Export data to Excel and/or console"""
        if not data:
            print("No data obtained.")
            return

        df = pd.DataFrame(data)
        
        # Reorder columns
        column_order = ["asset_id", "department_name", "user_first_name", "user_last_name", "user_email"]
        existing_columns = [col for col in column_order if col in df.columns]
        remaining_columns = [col for col in df.columns if col not in column_order]
        df = df[existing_columns + remaining_columns]
        
        # Remove columns with all "Unknown" values
        df = df.loc[:, ~(df == "Unknown").all()]

        if output_file:
            self.excel_manager.export_to_excel(df, output_file)
        
        if verbose:
            print(df)

    def map_department_name_to_id(self, department_name):
        """Map department name to ID with improved error handling"""
        try:
            query = f'departments/?query="name:\'{department_name}\'"'
            data = self.make_request(query)
            if data and 'departments' in data and len(data['departments']) > 0:
                return data['departments'][0]['id']
            print(f"{Fore.YELLOW}Warning: No department found with name '{department_name}'")
            return None
        except Exception as e:
            print(f"{Fore.RED}Error mapping department name: {e}")
            return None

    def map_location_name_to_id(self, location_name):
        """Map location name to ID"""
        data = self.make_request(f'locations/?query="name:\'{location_name}\'"')
        if data and 'locations' in data and len(data['locations']) > 0:
            return data['locations'][0]['id']
        print(f"{Fore.YELLOW}Warning: No location found with name '{location_name}'.")
        return None

    def _get_department_name(self, asset_data):
        """Get department name with proper handling"""
        if not asset_data or 'department_id' not in asset_data:
            return 'Unknown'
        
        departments = self.get_departments()
        return departments.get(asset_data['department_id'], 'Unknown')

    def get_location_name(self, location_id):
        """Get location name with improved error handling"""
        if not location_id:
            return 'Unknown'
            
        try:
            # Try direct API call first
            response = self.get_cached_request(f'locations/{location_id}')
            if response and 'location' in response:
                return response['location'].get('name', 'Unknown')

            # Fallback to cached locations list
            locations = self.get_locations()
            location_name = locations.get(location_id, 'Unknown')
            
            if location_name == 'Unknown':
                print(f"{Fore.YELLOW}Warning: Location ID {location_id} not found")
            
            return location_name
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not get location name: {e}")
            return 'Unknown'

    def _get_location_name(self, asset_data):
        """Get location name from asset data"""
        if not asset_data or 'location_id' not in asset_data:
            return 'Unknown'
        return self.get_location_name(asset_data['location_id'])

    def _get_asset_type(self, asset_data):
        """Get asset type name"""
        if not asset_data or 'asset_type_id' not in asset_data:
            return 'Unknown'
            
        type_id = asset_data['asset_type_id']
        return self.get_asset_type(type_id)

    def get_asset_type(self, type_id):
        """Get asset type name directly"""
        if not type_id:
            return 'Unknown'
            
        response = self.get_cached_request(f'asset_types/{type_id}')
        if response and 'asset_type' in response:
            return response['asset_type']['name']
        return 'Unknown'

    def _get_user_info(self, asset_data):
        """Get detailed user information"""
        if not asset_data or 'user_id' not in asset_data:
            return None
        response = self.get_cached_request(f'requesters/{asset_data["user_id"]}')
        if response and 'requester' in response:
            user = response['requester']
            return {
                'first_name': user.get('first_name', 'Unknown'),
                'last_name': user.get('last_name', 'Unknown'),
                'primary_email': user.get('primary_email', 'Unknown'),
                'work_phone_number': user.get('work_phone_number', 'Unknown'),
                'mobile_phone_number': user.get('mobile_phone_number', 'Unknown'),
                'department_names': ', '.join(user.get('department_names', [])),  # Convertir array a string
                'job_title': user.get('job_title', 'Unknown')
            }
        return None

    def get_asset_types(self):
        """Get all asset types"""
        url = 'asset_types'
        data = self.get_cached_request(url)
        if data and 'asset_types' in data:
            return {asset_type['id']: asset_type['name'] for asset_type in data['asset_types']}
        return {}

    def get_asset_with_type_fields(self, asset_id):
        """Get asset with type fields included"""
        url = f'assets?include=type_fields&filter="name:\'ASSET-{asset_id}\'"'
        data = self.make_request(url)
        if data and 'assets' in data and len(data['assets']) > 0:
            return data['assets'][0]
        return None

    def get_extended_user_info(self, user_id):
        """Get complete user information"""
        if not user_id:
            return None
            
        response = self.get_cached_request(f'requesters/{user_id}')
        if response and 'requester' in response:
            user = response['requester']
            return {
                'first_name': user.get('first_name', 'Unknown'),
                'last_name': user.get('last_name', 'Unknown'),
                'primary_email': user.get('primary_email', 'Unknown'),
                #'work_phone_number': user.get('work_phone_number', 'Unknown'),# descomentar linea si se desea incluir
                'mobile_phone_number': user.get('mobile_phone_number', 'Unknown'),
                # 'department_names': user.get('department_names', []), # descomentar linea si se desea incluir
                'job_title': user.get('job_title', 'Unknown'),
 
            }
        return None

    def _get_asset_description(self, asset_id):
        """Get asset description"""
        if asset_data := self.get_asset(asset_id):
            return asset_data.get('description', 'Unknown')
        return 'Unknown'

    def find_user_by_name(self, first_name, last_name):
        """Find user by first and last name"""
        query = f'requesters?query="first_name:\'{first_name}\'"&query="last_name:\'{last_name}\'"'
        response = self.make_request(query)
        if response and 'requesters' in response and response['requesters']:
            return response['requesters'][0]['id']
        print(f"{Fore.YELLOW}No user found with name: {first_name} {last_name}")
        return None

    def get_user_by_name(self, first_name, last_name):
        """Get user by first and last name with full details"""
        query = f'requesters?query="first_name:\'{first_name}\'"&query="last_name:\'{last_name}\'"'
        response = self.make_request(query)
        if response and 'requesters' in response and response['requesters']:
            return response['requesters'][0]
        print(f"{Fore.YELLOW}No se encontró ningún usuario con nombre: {first_name} {last_name}")
        return None

    def get_assets_by_user(self, user_id):
        """Get all assets associated with a user"""
        query = f'assets?query="user_id:{user_id}"'
        assets = []
        page = 1
        
        while True:
            response = self.make_request(f"{query}&page={page}")
            if not response or 'assets' not in response or not response['assets']:
                break
            assets.extend(response['assets'])
            page += 1
            
        return sorted(assets, key=lambda x: int(x.get('display_id', 0)))

    def get_assets_by_department(self, department_id):
        """Get all assets in a department"""
        query = f'assets?query="department_id:{department_id}"'
        return self._get_assets_with_query(query)

    def get_assets_by_location(self, location_id):
        """Get all assets in a location"""
        query = f'assets?query="location_id:{location_id}"'
        return self._get_assets_with_query(query)

    def _get_assets_with_query(self, query):
        """Get assets using a query with pagination"""
        assets = []
        page = 1
        while True:
            response = self.make_request(f"{query}&page={page}")
            if not response or 'assets' not in response or not response['assets']:
                break
            assets.extend(response['assets'])
            page += 1
        return sorted(assets, key=lambda x: int(x['display_id']))