from colorama import Fore
import logging

class LocationManager:
    def __init__(self, api):
        self.api = api
        self.logger = logging.getLogger(__name__)
        self.logger.info("LocationManager initialized")

    def get_all_locations(self):
        """Get all locations with complete data"""
        self.logger.info("Fetching all locations from API")
        locations = self.api.fetch_paginated_data('locations')
        
        if not locations:
            self.logger.error("No locations returned from API")
            return []
            
        self.logger.info(f"Retrieved {len(locations)} locations")
        self.logger.debug(f"Raw locations data: {locations}")
        
        sorted_locations = sorted(locations, key=lambda x: x.get('name', ''))
        self.logger.info("Locations sorted alphabetically")
        return sorted_locations

    def map_location_name_to_id(self, location_name):
        """Map location name to ID"""
        data = self.api.make_request(f'locations/?query="name:\'{location_name}\'"')
        if data and 'locations' in data and len(data['locations']) > 0:
            return data['locations'][0]['id']
        print(f"{Fore.YELLOW}Warning: No location found with name '{location_name}'.")
        return None

    def build_location_hierarchy(self):
        """Build location hierarchy tree"""
        self.logger.info("Building location hierarchy")
        locations = self.get_all_locations()
        
        if not locations:
            self.logger.error("No locations available to build hierarchy")
            return []
            
        hierarchy = {}
        self.logger.info("Creating node dictionary")
        
        # First pass: Create all nodes
        for loc in locations:
            loc_id = loc.get('id')
            self.logger.debug(f"Processing location: ID={loc_id}, Name={loc.get('name')}")
            
            hierarchy[loc_id] = {
                'name': loc.get('name', 'Unknown'),
                'children': [],
                'parent_id': loc.get('parent_location_id'),
                'data': loc
            }
        
        # Second pass: Build tree structure
        self.logger.info("Building tree relationships")
        root_locations = []
        for loc_id, loc_data in hierarchy.items():
            parent_id = loc_data['parent_id']
            self.logger.debug(f"Processing relationships for {loc_data['name']} (ID: {loc_id}, Parent: {parent_id})")
            
            if parent_id and parent_id in hierarchy:
                self.logger.debug(f"Adding {loc_data['name']} as child to {hierarchy[parent_id]['name']}")
                hierarchy[parent_id]['children'].append(loc_data)
            else:
                self.logger.debug(f"Adding {loc_data['name']} as root location")
                root_locations.append(loc_data)
        
        self.logger.info(f"Hierarchy built with {len(root_locations)} root locations")
        return root_locations

    def format_location_tree(self, prefix=""):
        """Format location hierarchy as text tree"""
        self.logger.info("Starting location tree formatting")
        root_locations = self.build_location_hierarchy()
        output = []

        def format_node(node, level=0, prefix="", is_last=True):
            marker = "└── " if is_last else "├── "
            text = f"{prefix}{marker}{node['name']}"
            output.append(text)
            
            if node['children']:
                child_prefix = prefix + ("    " if is_last else "│   ")
                sorted_children = sorted(node['children'], key=lambda x: x['name'])
                
                for i, child in enumerate(sorted_children):
                    is_last_child = i == len(sorted_children) - 1
                    format_node(child, level + 1, child_prefix, is_last_child)

        sorted_roots = sorted(root_locations, key=lambda x: x['name'])
        for i, location in enumerate(sorted_roots):
            is_last = i == len(sorted_roots) - 1
            format_node(location, 0, prefix, is_last)

        return output
