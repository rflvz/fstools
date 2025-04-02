import logging
from datetime import datetime
from venv import logger
from colorama import Fore, init
import pandas as pd
from .asset_manager import AssetManager
from .excel_manager import ExcelManager
from .data_processor import DataProcessor
from .data_exporter import DataExporter
from .search_manager import SearchManager
from .location_manager import LocationManager
import os

class FreshServiceManager:
    def __init__(self):
        init(autoreset=True)
        self.asset_manager = AssetManager()
        self.excel_manager = ExcelManager()
        self.data_processor = DataProcessor()
        self.data_exporter = DataExporter(self.excel_manager)
        self.search_manager = SearchManager(self.asset_manager)
        self.location_manager = LocationManager(self.asset_manager)  # Add this line
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging"""
        from . import LOGS_DIR
        
        log_filename = os.path.join(LOGS_DIR, f'freshservice_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            filename=log_filename,
            level=logging.DEBUG,  # Cambiar a DEBUG para ver logs detallados
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("Logging initialized with cache tracking")

    def run(self, options):
        """Main execution logic with logging"""
        logging.info(f"Starting execution with options: {options}")
        asset_ids = self.asset_manager.process_asset_ids(options['ids'], options['exclude'])
        if not asset_ids:
            print(f"{Fore.RED}Error: No valid IDs found in provided input.")
            return

        data = []
        for asset_id in asset_ids:
            # Usar el método público process_asset en lugar del privado
            asset_data = self.asset_manager.process_asset(asset_id, options)
            if asset_data:
                data.append(asset_data)

        if data:
            print(f"{Fore.GREEN}Successfully processed {len(data)} entries")
            logging.info(f"Successfully processed {len(data)} entries")
            self._export_data(data, options)
        else:
            print(f"{Fore.YELLOW}No data obtained")
            logging.warning("No data obtained")

    def _export_data(self, data, options):
        """Export processed data"""
        df = self.data_processor.process_dataframe(data)
        if df is not None:
            self.data_exporter.export_data(df, options)

    def list_departments(self):
        """List all departments"""
        logger.info("Requesting department list")
        departments = self.asset_manager.get_departments()
        
        if departments:
            sorted_depts = sorted(departments.values())
            logger.info(f"Found {len(sorted_depts)} departments")
            logger.debug(f"Department list: {sorted_depts}")
            return sorted_depts
            
        logger.warning("No departments found")
        return None

    def list_locations(self):
        """List all locations in a hierarchical tree structure"""
        return self.location_manager.format_location_tree()

    def search_by_user(self, full_name, output_file=None):
        """Search assets by user name"""
        try:
            first_name, last_name = full_name.split(' ', 1)
        except ValueError:
            return None, "Error: Full name must include first and last name"

        user = self.asset_manager.get_user_by_name(first_name, last_name)
        if not user:
            return None, "User not found"

        assets = self.asset_manager.get_assets_by_user(user['id'])
        if not assets:
            return None, "No assets found for this user"
            
        processed_data = []
        for asset in assets:
            processed_data.append({
                'Asset ID': asset.get('display_id'),
                'Name': asset.get('name'),
                'Department': self.asset_manager._get_department_name(asset),
                'Location': self.asset_manager._get_location_name(asset),
                'Type': self.asset_manager._get_asset_type(asset),
                'State': asset.get('asset_state')
            })

        if output_file:
            self.search_manager.export_results(assets, output_file)
            
        return processed_data, f"Assets found for {first_name} {last_name}"

    def search_by_department(self, department_name, output_file=None):
        """Search assets by department"""
        logger.info(f"Searching assets in department: {department_name}")
        
        dept_id = self.asset_manager.map_department_name_to_id(department_name)
        if not dept_id:
            logger.warning(f"Department not found: {department_name}")
            return None, "Department not found"
            
        logger.info(f"Found department ID: {dept_id}")
        assets = self.asset_manager.get_assets_by_department(dept_id)
        
        if not assets:
            logger.info(f"No assets found in department {department_name}")
            return None, "No assets found in this department"
            
        logger.info(f"Found {len(assets)} assets in department {department_name}")
        
        processed_data = []
        for asset in assets:
            asset_info = {
                'Asset ID': asset.get('display_id'),
                'Name': asset.get('name'),
                'Location': self.asset_manager._get_location_name(asset),
                'Type': self.asset_manager._get_asset_type(asset),
                'State': asset.get('asset_state')
            }
            logger.debug(f"Processed asset: {asset_info}")
            processed_data.append(asset_info)

        if output_file:
            logger.info(f"Exporting results to {output_file}")
            self.search_manager.export_results(assets, output_file)
            
        return processed_data, f"Assets found in department: {department_name}"

    def search_by_location(self, location_name, output_file=None):
        """Search assets by location"""
        loc_id = self.asset_manager.map_location_name_to_id(location_name)
        if not loc_id:
            return None, "Location not found"
            
        assets = self.asset_manager.get_assets_by_location(loc_id)
        if not assets:
            return None, "No assets found in this location"
            
        processed_data = []
        for asset in assets:
            processed_data.append({
                'Asset ID': asset.get('display_id'),
                'Name': asset.get('name'),
                'Department': self.asset_manager._get_department_name(asset),
                'Type': self.asset_manager._get_asset_type(asset),
                'State': asset.get('asset_state')
            })

        if output_file:
            self.search_manager.export_results(assets, output_file)
            
        return processed_data, f"Assets found in location: {location_name}"

    def import_excel_ids(self, excel_file):
        """Import IDs from Excel and export to txt"""
        if not excel_file.endswith(('.xlsx', '.xls')):
            print(f"{Fore.RED}Error: File must be an Excel file (.xlsx or .xls)")
            return

        try:
            # Process IDs using existing method
            ids = self.asset_manager.process_asset_ids(excel_file)
            if not ids:
                print(f"{Fore.RED}No valid IDs found in the Excel file")
                return

            # Create output filename
            output_file = os.path.splitext(excel_file)[0] + '_ids.txt'
            
            # Export IDs to txt file
            with open(output_file, 'w') as f:
                f.write(','.join(map(str, ids)))

            print(f"{Fore.GREEN}Successfully exported {len(ids)} IDs to {output_file}")
            print(f"{Fore.CYAN}IDs: {','.join(map(str, ids[:5])) + ('...' if len(ids) > 5 else '')}")

        except Exception as e:
            print(f"{Fore.RED}Error processing Excel file: {str(e)}")

    def process_assets(self, asset_ids, options):
        """Process assets based on options"""
        try:
            data = []
            for asset_id in asset_ids:
                # Primero obtener los datos básicos del asset
                asset_data = self.api.get_cached_request(f'assets/{asset_id}')
                if not asset_data or 'asset' not in asset_data:
                    continue
                
                # Si se solicitan componentes, obtenerlos y procesarlos
                if options.get('components'):
                    components_data = self.api.get_cached_request(f'assets/{asset_id}/components')
                    if components_data and 'components' in components_data:
                        data.append({
                            'asset_id': asset_id,
                            'components': self.process_components(components_data['components'], options)
                        })
                else:
                    data.append(self.process_asset_data(asset_data['asset'], options))
                    
            return data
        except Exception as e:
            logger.error(f"Error processing assets: {e}")
            return None

    def run_and_get_results(self, options):
        """Execute and return results without saving to file"""
        logging.info(f"Starting execution with options: {options}")
        
        asset_ids = self.asset_manager.process_asset_ids(options['ids'], options['exclude'])
        if not asset_ids:
            return None

        data = []
        for asset_id in asset_ids:
            asset_data = self.asset_manager.process_asset(asset_id, options)
            if asset_data:
                data.append(asset_data)

        return data if data else None

    def export_to_excel(self, data, output_file):
        """Export data to Excel file"""
        try:
            if not data:
                return False
                
            # Si los datos son una lista de departamentos, formatear adecuadamente
            if isinstance(data, list) and all('Departamento' in d for d in data):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data)
                
            # Verificar si el directorio existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Exportar
            self.data_exporter.export_data(df, {'output': output_file})
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
