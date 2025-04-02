from colorama import Fore

class UserManager:
    def __init__(self, api):
        self.api = api

    def get_user_by_name(self, first_name, last_name):
        """Get user by first and last name with full details"""
        query = f'requesters?query="first_name:\'{first_name}\'"&query="last_name:\'{last_name}\'"'
        response = self.api.make_request(query)
        if response and 'requesters' in response and response['requesters']:
            return response['requesters'][0]
        print(f"{Fore.YELLOW}No se encontró ningún usuario con nombre: {first_name} {last_name}")
        return None

    def get_extended_user_info(self, user_id):
        """Get complete user information"""
        if not user_id:
            return None
            
        response = self.api.get_cached_request(f'requesters/{user_id}')
        if response and 'requester' in response:
            user = response['requester']
            return {
                'first_name': user.get('first_name', 'Unknown'),
                'last_name': user.get('last_name', 'Unknown'),
                'primary_email': user.get('primary_email', 'Unknown'),
                'mobile_phone_number': user.get('mobile_phone_number', 'Unknown'),
                'job_title': user.get('job_title', 'Unknown'),
            }
        return None
