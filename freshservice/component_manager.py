import logging
import json
from colorama import Fore, Style, init

logger = logging.getLogger(__name__)

class ComponentManager:
    def __init__(self, api):
        self.api = api
        self.component_types = {
            "cpu": "Processor",
            "ram": "Memory",
            "hdd": "Logical Drive",
            "nic": "Network Adapter"
        }
        logger.info("ComponentManager initialized with types: %s", self.component_types)

    def get_components(self, asset_id, join=True, combine_cpu_ram=False, specified_components=None):
        """Get and process components for an asset"""
        logger.info(f"Getting components for asset {asset_id}")
        
        # Traducir los tipos de componentes especificados
        if specified_components:
            specified_components = [self.component_types[comp] for comp in specified_components]
            logger.debug(f"Looking for component types: {specified_components}")
        
        try:
            # Obtener componentes de la API
            components = self.api.make_request(f'assets/{asset_id}/components')
            
            if not components or 'components' not in components:
                logger.warning(f"No components found for asset {asset_id}")
                return []

            # Filtrar componentes
            filtered_components = [
                c for c in components['components']
                if specified_components is None or c.get('component_type') in specified_components
            ]
            
            logger.info(f"Found {len(filtered_components)} matching components")
            logger.debug(f"Component types found: {[c.get('component_type') for c in filtered_components]}")

            # Separar por tipo
            ram_components = [c for c in filtered_components if c.get('component_type') == 'Memory']
            cpu_components = [c for c in filtered_components if c.get('component_type') == 'Processor']

            # Si se solicita combinar CPU y RAM y tenemos ambos componentes
            if combine_cpu_ram and cpu_components and ram_components:
                logger.info("Combining CPU and RAM components")
                return self.combine_cpu_and_ram(cpu_components, ram_components, join)

            # Si no se combinan, procesar por separado como antes
            # Procesar RAM
            ram_processed = None
            if ram_components:
                if len(ram_components) > 0:
                    ram_data = ram_components[0].get('component_data', [{}])[0]
                    ram_processed = {
                        'memory_capacity': ram_data.get('capacity', 'Unknown'),
                        'memory_speed': ram_data.get('speed', 'Unknown'),
                        'memory_type': ram_data.get('memory_type', 'Unknown')
                    }
                    logger.debug(f"Processed RAM data: {ram_processed}")

            # Procesar CPU 
            cpu_processed = None
            if cpu_components:
                if len(cpu_components) > 0:
                    cpu_data = cpu_components[0].get('component_data', [{}])[0]
                    cpu_processed = {
                        'cpu_model': cpu_data.get('model', 'Unknown'),
                        'cpu_speed': cpu_data.get('cpu_speed', 'Unknown'),
                        'cpu_cores': cpu_data.get('no_of_cores', 'Unknown')
                    }
                    logger.debug(f"Processed CPU data: {cpu_processed}")

            # Combinar resultados
            result = {}
            if ram_processed:
                result.update(ram_processed)
            if cpu_processed:
                result.update(cpu_processed)

            logger.info(f"Final processed data: {result}")
            return [result] if result else []

        except Exception as e:
            logger.error(f"Error processing components for asset {asset_id}: {str(e)}")
            return []

    def combine_ram_components(self, ram_components):
        """Combine RAM components into a single entry"""
        if not ram_components:
            return []

        combined_ram = {
            "component_type": "Memory",
            "capacity": "",
            "speed": "",
            "socket": "",
            "memory_type": "",
            "total_capacity": 0
        }

        speeds = set()
        capacities = []
        sockets = []
        memory_type = None

        for component in ram_components:
            component_data = component.get('component_data', [])
            for data in component_data:
                capacity = data.get('capacity', 0)
                if isinstance(capacity, str) and capacity.isdigit():
                    capacity = int(capacity)
                speed = data.get('speed', 'Unknown')
                socket = data.get('socket', 'Unknown')
                memory_type = data.get('memory_type', memory_type)

                combined_ram["total_capacity"] += capacity
                capacities.append(capacity)
                speeds.add(speed)
                sockets.append(socket)

        if len(set(capacities)) == 1 and capacities[0] > 0:
            combined_ram["capacity"] = f"{capacities[0]}x{len(capacities)}"
        else:
            combined_ram["capacity"] = "+".join(map(str, capacities))

        if len(speeds) == 1:
            combined_ram["speed"] = speeds.pop()
        else:
            combined_ram["speed"] = "+".join(speeds)

        combined_ram["socket"] = ", ".join(sockets)
        combined_ram["memory_type"] = memory_type

        return [combined_ram]

    def combine_cpu_and_ram(self, cpu_components, ram_components, join_ram=True):
        """Combine CPU and RAM components into a single entry"""
        logger.info(f"Starting combine_cpu_and_ram with {len(cpu_components)} CPU and {len(ram_components)} RAM components")
        
        if not cpu_components or not ram_components:
            logger.warning("Missing components - CPU: %s, RAM: %s", bool(cpu_components), bool(ram_components))
            return []

        # Procesar RAM primero
        try:
            if join_ram:
                logger.debug("Combining RAM components")
                ram_data = self.combine_ram_components(ram_components)[0]
            else:
                logger.debug("Using first RAM component")
                ram_data = ram_components[0]
            logger.info(f"Processed RAM data: {ram_data}")
        except Exception as e:
            logger.error(f"Error processing RAM: {str(e)}")
            return []
        
        combined_data = []
        try:
            for cpu in cpu_components:
                # Procesar CPU
                logger.debug(f"Processing CPU component: {cpu}")
                cpu_data = cpu.get('component_data', [{}])[0]
                
                combined_row = {
                    "component_type": "CPU + RAM",
                    "cpu_model": cpu_data.get('model', 'Unknown'),
                    "cpu_cores": cpu_data.get('no_of_cores', 'Unknown'), 
                    "cpu_speed": cpu_data.get('cpu_speed', 'Unknown'),
                    "ram_capacity": ram_data.get('capacity', 'Unknown'),
                    "ram_speed": ram_data.get('speed', 'Unknown'),
                    "ram_socket": ram_data.get('socket', 'Unknown'),
                    "ram_memory_type": ram_data.get('memory_type', 'Unknown'),
                    "ram_total_capacity": ram_data.get('total_capacity', 'Unknown') if join_ram else 'N/A'
                }
                logger.info(f"Created combined row: {combined_row}")
                combined_data.append(combined_row)
        except Exception as e:
            logger.error(f"Error combining CPU and RAM: {str(e)}")
            return []

        logger.info(f"Successfully combined {len(combined_data)} CPU+RAM entries")
        return combined_data

    def _get_cpu_data(self, cpu):
        """Extract CPU data from component"""
        try:
            data = cpu.get('component_data', [{}])[0]
            return {
                'model': data.get('model', 'Unknown'),
                'cores': data.get('no_of_cores', 'Unknown'),
                'speed': data.get('cpu_speed', 'Unknown') 
            }
        except (IndexError, KeyError):
            return {
                'model': 'Unknown',
                'cores': 'Unknown',
                'speed': 'Unknown'
            }

    def _get_ram_data(self, ram):
        """Extract RAM data from component"""
        try:
            data = ram.get('component_data', [{}])[0]
            return {
                'capacity': data.get('capacity', 'Unknown'),
                'speed': data.get('speed', 'Unknown'),
                'socket': data.get('socket', 'Unknown'),
                'memory_type': data.get('memory_type', 'Unknown')
            }
        except (IndexError, KeyError):
            return {
                'capacity': 'Unknown',
                'speed': 'Unknown',
                'socket': 'Unknown',
                'memory_type': 'Unknown'
            }

    def translate_component_types(self, components):
        """Translate component abbreviations to full names"""
        if not components:
            return None
        return [self.component_types.get(c.lower(), c) for c in components]

    def process_component_data(self, components, join=True):
        """Process component data with detailed info"""
        if not components:
            return []
            
        processed = []
        for component in components:
            component_data = component.get('component_data', [{}])[0]
            if component['component_type'] == 'Memory':
                # Special handling for RAM
                if join:
                    return self.combine_ram_components([component])
            elif component['component_type'] == 'Processor':
                processed.append({
                    "component_type": "Processor",
                    "model": component_data.get('model', 'Unknown'),
                    "cores": component_data.get('no_of_cores', 'Unknown'),
                    "speed": component_data.get('cpu_speed', 'Unknown'),
                    "manufacturer": component_data.get('manufacturer', 'Unknown'),
                    "serial_number": component_data.get('serial_number', 'Unknown')
                })
        return processed

    def _process_cpu_component(self, cpu):
        """Process CPU component with detailed logging"""
        cpu_data = cpu.get('component_data', [{}])[0]
        processed = {
            "component_type": "Processor",
            "cpu_model": cpu_data.get('model', 'Unknown'),
            "cpu_cores": cpu_data.get('no_of_cores', 'Unknown'),
            "cpu_speed": cpu_data.get('cpu_speed', 'Unknown'),
            "cpu_manufacturer": cpu_data.get('manufacturer', 'Unknown')
        }
        logger.debug(f"Processed CPU component: {processed}")
        return processed

    def _process_ram_component(self, ram):
        """Process RAM component with all fields"""
        ram_data = ram.get('component_data', [{}])[0]
        processed = {
            'capacity': ram_data.get('capacity', 'Unknown'),
            'speed': ram_data.get('speed', 'Unknown'),
            'socket': ram_data.get('socket', 'Unknown'),
            'memory_type': ram_data.get('memory_type', 'Unknown')
        }
        return processed