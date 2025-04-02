import os
import sys
from pathlib import Path
import tempfile
from flask import render_template, request, send_file, flash
from web import app
from web.forms import AssetForm, SearchForm

# Agregar el directorio raíz al path de manera más robusta
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from freshservice import FreshServiceManager

manager = FreshServiceManager()

@app.route('/', methods=['GET', 'POST'])
def index():
    asset_form = AssetForm()
    search_form = SearchForm()
    
    if request.method == 'POST':
        if 'submit_assets' in request.form and asset_form.validate():
            # Obtener componentes seleccionados
            components = request.form.getlist('components')
            
            # Procesar búsqueda por IDs
            options = {
                'ids': asset_form.ids.data,
                'exclude': asset_form.exclude.data,
                'components': components if components else None,
                'disable_join': False,  # Opción para unir RAM
                'combine_cpu_ram': False,  # Opción para combinar CPU y RAM
                'asset_data': True,
                'include_departments': 'departments' in asset_form.include_info.data,
                'include_user': 'user' in asset_form.include_info.data,
                'include_location': 'location' in asset_form.include_info.data,
                'verbose': True
            }
            
            # Crear archivo temporal para la salida
            temp_dir = tempfile.mkdtemp()
            output_file = os.path.join(temp_dir, 'output.xlsx')
            options['output'] = output_file
            
            try:
                manager.run(options)
                
                if os.path.exists(output_file):
                    return send_file(output_file, as_attachment=True, download_name='assets.xlsx')
                else:
                    flash('No se encontraron resultados', 'warning')
            except Exception as e:
                flash(f'Error al procesar la solicitud: {str(e)}', 'error')
                
        elif 'submit_search' in request.form and search_form.validate():
            # Procesar búsqueda por criterios
            if search_form.search_type.data == 'user':
                manager.search_by_user(search_form.search_value.data)
            elif search_form.search_type.data == 'department':
                manager.search_by_department(search_form.search_value.data)
            elif search_form.search_type.data == 'location':
                manager.search_by_location(search_form.search_value.data)
    
    return render_template('index.html', asset_form=asset_form, search_form=search_form)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
