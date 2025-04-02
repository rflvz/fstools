import pandas as pd
from colorama import Fore

class SearchManager:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager

    def display_user_assets(self, user, assets):
        """Display user information and associated assets"""
        print(f"{Fore.GREEN}Usuario encontrado:")
        print(f"  Nombre: {user.get('first_name', 'Unknown')}")
        print(f"  Apellido: {user.get('last_name', 'Unknown')}")
        print(f"  ID: {user.get('id', 'Unknown')}")

        if assets:
            print(f"{Fore.CYAN}Activos:")
            for asset in assets:
                print(f"  {asset.get('display_id')}: {asset.get('name', 'Unknown')}")

    def display_department_assets(self, department_name, assets):
        """Display department assets"""
        if assets:
            print(f"{Fore.CYAN}Activos en departamento '{department_name}':")
            for asset in assets:
                print(f"  {asset.get('display_id')}: {asset.get('name', 'Unknown')}")

    def display_location_assets(self, location_name, assets):
        """Display location assets"""
        if assets:
            print(f"{Fore.CYAN}Activos en ubicación '{location_name}':")
            for asset in assets:
                print(f"  {asset.get('display_id')}: {asset.get('name', 'Unknown')}")

    def display_locations_hierarchy(self, locations):
        """Display locations in hierarchical format"""
        # Construir jerarquía
        hierarchy = {}
        location_details = {}

        # Almacenar detalles de cada localización
        for location in locations:
            location_id = location['id']
            location_name = location['name']
            parent_id = location.get('parent_location_id')
            location_details[location_id] = {
                'name': location_name,
                'parent_id': parent_id,
                'children': []
            }

        # Construir árbol jerárquico
        for location_id, details in location_details.items():
            parent_id = details['parent_id']
            if parent_id:
                if parent_id in location_details:
                    location_details[parent_id]['children'].append(details)
            else:
                hierarchy[location_id] = details

        # Colores para diferentes niveles
        colors = [Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTWHITE_EX, Fore.LIGHTGREEN_EX]

        def print_hierarchy(location, level=0):
            color = colors[level % len(colors)]
            indent = "    " * level
            print(f"{color}{indent}{location['name']}")
            for child in sorted(location['children'], key=lambda x: x['name']):
                print_hierarchy(child, level + 1)

        # Imprimir jerarquía ordenada
        for _, root_location in sorted(hierarchy.items(), key=lambda x: x[1]['name']):
            print_hierarchy(root_location)

    def export_results(self, assets, output_file):
        """Export search results to file"""
        if not output_file:
            return

        if output_file.endswith('.xlsx'):
            df = pd.DataFrame(assets)
            # Seleccionar solo las columnas que existen
            columns_to_show = []
            available_columns = ["display_id", "name", "asset_tag", "department_id", "user_id", "state"]
            
            for col in available_columns:
                if col in df.columns:
                    columns_to_show.append(col)
            
            df = df[columns_to_show]
            
            # Mapear nombres de columnas a español
            column_mapping = {
                "display_id": "ID",
                "name": "Nombre",
                "asset_tag": "Tag",
                "department_id": "Departamento ID",
                "user_id": "Usuario ID",
                "state": "Estado"
            }
            
            df.columns = [column_mapping.get(col, col) for col in df.columns]
            self.asset_manager.excel_manager.export_to_excel(df, output_file)
            print(f"{Fore.GREEN}Resultados exportados a {output_file}")
        elif output_file.endswith('.txt'):
            with open(output_file, 'w') as f:
                f.write(','.join(str(asset['display_id']) for asset in assets))
            print(f"{Fore.GREEN}IDs exportados a {output_file}")
