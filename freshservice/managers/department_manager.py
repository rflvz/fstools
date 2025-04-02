from colorama import Fore
import logging

logger = logging.getLogger(__name__)

class DepartmentManager:
    def __init__(self, api):
        self.api = api
        logger.info("DepartmentManager initialized")

    def get_departments(self):
        """Get all departments"""
        try:
            logger.info("Fetching all departments")
            data = self.api.make_request('departments')
            
            if data and 'departments' in data:
                departments = {dept['id']: dept['name'] for dept in data['departments']}
                logger.info(f"Found {len(departments)} departments")
                logger.debug(f"Department data: {departments}")
                return departments
                
            logger.warning("No departments found in response")
            return {}
            
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
            print(f"{Fore.RED}Error getting departments: {e}")
            return {}

    def map_department_name_to_id(self, department_name):
        """Map department name to ID"""
        logger.info(f"Mapping department name: {department_name}")
        
        query = f'departments/?query="name:\'{department_name}\'"'
        logger.debug(f"Department search query: {query}")
        
        data = self.api.make_request(query)
        
        if data and 'departments' in data and len(data['departments']) > 0:
            dept_id = data['departments'][0]['id']
            logger.info(f"Found department ID {dept_id} for name '{department_name}'")
            return dept_id
            
        logger.warning(f"No department found with name '{department_name}'")
        print(f"{Fore.YELLOW}Warning: No department found with name '{department_name}'")
        return None
