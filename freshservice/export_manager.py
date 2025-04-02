import json
import pandas as pd
from .config import EXPORT_CONFIG

class ExportManager:
    def export_data(self, data, output_file, format=None):
        if not format:
            format = EXPORT_CONFIG['default_format']
            
        if format not in EXPORT_CONFIG['allowed_formats']:
            raise ValueError(f"Unsupported format: {format}")
            
        method_name = f"_export_to_{format}"
        export_method = getattr(self, method_name)
        return export_method(data, output_file)
        
    def _export_to_xlsx(self, data, output_file):
        df = pd.DataFrame(data)
        writer = pd.ExcelWriter(output_file, engine='openpyxl')
        
        df.to_excel(writer, index=False)
        
        if EXPORT_CONFIG['excel']['freeze_panes']:
            writer.sheets['Sheet1'].freeze_panes = 'A2'
            
        if EXPORT_CONFIG['excel']['auto_filter']:
            writer.sheets['Sheet1'].auto_filter.ref = writer.sheets['Sheet1'].dimensions
            
        writer.save()
        
    def _export_to_csv(self, data, output_file):
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        
    def _export_to_json(self, data, output_file):
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
