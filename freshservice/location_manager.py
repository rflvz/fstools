from colorama import Fore

class LocationManager:
    def __init__(self, api):
        self.api = api

    def get_all_locations(self):
        """Get all locations with complete data"""
        locations = self.api.fetch_paginated_data('locations')
        return sorted(locations, key=lambda x: x.get('name', '')) if locations else []

    def map_location_name_to_id(self, location_name):
        """Map location name to ID"""
        data = self.api.make_request(f'locations/?query="name:\'{location_name}\'"')
        if data and 'locations' in data and len(data['locations']) > 0:
            return data['locations'][0]['id']
        print(f"{Fore.YELLOW}Warning: No location found with name '{location_name}'.")
        return None

    def build_location_hierarchy(self):
        """Build location hierarchy tree"""
        locations = self.get_all_locations()
        hierarchy = {}
        
        # First pass: Create all nodes
        for loc in locations:
            loc_id = loc.get('id')
            hierarchy[loc_id] = {
                'name': loc.get('name', 'Unknown'),
                'children': [],
                'parent_id': loc.get('parent_location_id'),
                'data': loc
            }
        
        # Second pass: Build tree structure
        root_locations = []
        for loc_id, loc_data in hierarchy.items():
            parent_id = loc_data['parent_id']
            if parent_id and parent_id in hierarchy:
                hierarchy[parent_id]['children'].append(loc_data)
            else:
                root_locations.append(loc_data)
                
        return root_locations

    def format_location_tree(self, prefix=""):
        """Format location hierarchy as text tree"""
        root_locations = self.build_location_hierarchy()
        output = []
        
        def format_node(node, prefix="", is_last=True):
            # Add line for current location
            marker = "└── " if is_last else "├── "
            output.append(f"{prefix}{marker}{node['name']}")
            
            # Prepare prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            # Process children
            for i, child in enumerate(node['children']):
                is_last_child = i == len(node['children']) - 1
                format_node(child, child_prefix, is_last_child)
        
        # Process root locations
        for i, location in enumerate(root_locations):
            is_last = i == len(root_locations) - 1
            format_node(location, prefix, is_last)
            
        return output
