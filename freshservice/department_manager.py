from colorama import Fore

class DepartmentManager:
    def __init__(self, api):
        self.api = api

    def get_departments(self):
        """Get all departments"""
        try:
            data = self.api.make_request('departments')
            if data and 'departments' in data:
                return {dept['id']: dept['name'] for dept in data['departments']}
            return {}
        except Exception as e:
            print(f"{Fore.RED}Error getting departments: {e}")
            return {}

    def map_department_name_to_id(self, department_name):
        """Map department name to ID"""
        query = f'departments/?query="name:\'{department_name}\'"'
        data = self.api.make_request(query)
        if data and 'departments' in data and len(data['departments']) > 0:
            return data['departments'][0]['id']
        print(f"{Fore.YELLOW}Warning: No department found with name '{department_name}'")
        return None
