class DataExporter:
    def __init__(self, excel_manager):
        self.excel_manager = excel_manager
        
    def export_data(self, df, options):
        if options.get('output'):
            self.excel_manager.export_to_excel(df, options['output'])
        
        if options.get('verbose'):
            print(df)
