import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def process_dataframe(self, data):
        """Convert data to DataFrame"""
        if not data:
            return None
            
        try:
            # Procesar datos combinados de asset y componentes
            if isinstance(data, list) and 'components' in data[0]:
                logger.info("Processing combined asset and components data")
                processed_data = []
                
                for item in data:
                    base_info = {k: v for k, v in item.items() if k != 'components'}
                    
                    # Procesar cada componente y agregar la info base
                    for component in item.get('components', []):
                        row = base_info.copy()
                        row.update(component)
                        processed_data.append(row)
                        
                df = pd.DataFrame(processed_data)
            else:
                logger.info("Processing regular asset data")
                df = pd.DataFrame(data)
            
            return self._reorder_columns(df)
                
        except Exception as e:
            logger.error(f"Error processing DataFrame: {e}")
            logger.exception(e)
            return None

    def _reorder_columns(self, df):
        """Reorder columns to desired order"""
        if df is None or df.empty:
            return df

        # Define priority columns
        priority_columns = ['asset_id', 'department_name', 'location_name']
        
        # Get existing columns
        existing_columns = df.columns.tolist()
        
        # Filter priority columns that exist in the dataframe
        priority_exists = [col for col in priority_columns if col in existing_columns]
        
        # Get remaining columns
        other_columns = [col for col in existing_columns if col not in priority_exists]
        
        # Reorder columns
        new_column_order = priority_exists + other_columns
        
        return df[new_column_order]
