"""Configuration settings for the Freshservice tools"""

# API retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
RATE_LIMIT_DELAY = 60  # seconds

# Export settings
EXCEL_SETTINGS = {
    'header_color': '003366',
    'row_color': 'D9E1F2',
    'max_column_width': 50
}

# Default column order for exports
DEFAULT_COLUMNS = [
    'asset_id',
    'name',
    'display_id',
    'asset_tag',
    'department_name',
    'location_name',
    'user_first_name',
    'user_last_name',
    'user_email'
]

# Component type mappings
COMPONENT_TYPES = {
    'cpu': 'Processor',
    'ram': 'Memory',
    'hdd': 'Logical Drive',
    'nic': 'Network Adapter'
}

# Cache settings
CACHE_CONFIG = {
    'enabled': True,
    'max_age_hours': 24,
    'excluded_endpoints': ['assets']  # endpoints that shouldn't be cached
}

# Export settings
EXPORT_CONFIG = {
    'default_format': 'xlsx',
    'allowed_formats': ['xlsx', 'csv', 'json'],
    'excel': {
        'date_format': 'DD/MM/YYYY',
        'freeze_panes': True,
        'auto_filter': True
    }
}
