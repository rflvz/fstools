import os
import sys
from pathlib import Path
import tempfile
import logging
import shutil
from venv import logger
from werkzeug.utils import secure_filename
from flask import render_template, request, send_file, flash, jsonify, redirect, url_for, session
from web import app
from web.forms import AssetForm, SearchForm, FileUploadForm

# Agregar el directorio raíz al path de manera más robusta
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from freshservice import FreshServiceManager

manager = FreshServiceManager()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    # Esta ruta ahora redirige a search_id para mantener compatibilidad
    return redirect(url_for('search_id'))

@app.route('/search_id', methods=['GET', 'POST'])
def search_id():
    asset_form = AssetForm()
    results = None
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        if 'submit_assets' in request.form and asset_form.validate_on_submit():
            # Obtener componentes seleccionados
            components = request.form.getlist('components')
            
            # Procesar búsqueda por IDs
            options = {
                'ids': asset_form.ids.data,
                'exclude': asset_form.exclude.data,
                'components': components if components else None,
                'disable_join': asset_form.disable_join.data,
                'combine_cpu_ram': asset_form.combine_cpu_ram.data,
                'asset_data': True,  # Siempre True para obtener datos básicos
                'include_departments': 'departments' in asset_form.include_info.data,
                'include_user': 'user' in asset_form.include_info.data,
                'include_location': 'location' in asset_form.include_info.data,
                'include_system_os': 'system' in asset_form.include_info.data,
                'include_machine_ip': 'machine_ip' in asset_form.include_info.data,
                'include_machine_mac': 'machine_mac' in asset_form.include_info.data,
                'include_serial_number': 'serial_number' in asset_form.include_info.data,
                'include_description': 'description' in asset_form.include_info.data,
                'verbose': True,
                'all_data': asset_form.all_data.data
            }
            
            try:
                # Procesar los resultados primero
                results = manager.run_and_get_results(options)
                
                if not results:
                    flash('No se encontraron resultados', 'warning')
                    return render_template('search_id.html', asset_form=asset_form)
                
                # Para mostrar en la web, formatear los resultados
                formatted_results = []
                for result in results:
                    formatted_result = {
                        'ID': result.get('display_id'),
                        'Nombre': result.get('name'),
                    }
                    
                    # Información adicional
                    if 'department' in result:
                        formatted_result['Departamento'] = result['department']
                        
                    if 'user' in result:
                        formatted_result.update({
                            'Usuario': f"{result['user'].get('first_name', '')} {result['user'].get('last_name', '')}",
                            'Email': result['user'].get('primary_email', '')
                        })
                        
                    if 'location' in result:
                        formatted_result['Ubicación'] = result['location']
                        
                    if 'system_os' in result:
                        formatted_result['Sistema Operativo'] = result['system_os']
                        
                    if 'machine_ip' in result:
                        formatted_result['IP'] = result['machine_ip']
                        
                    if 'machine_mac' in result:
                        formatted_result['MAC'] = result['machine_mac']
                        
                    if 'serial_number' in result:
                        formatted_result['Número de Serie'] = result['serial_number']
                        
                    if 'description' in result:
                        formatted_result['Descripción'] = result['description']

                    # Componentes (CPU + RAM)
                    if result.get('component_type') == 'CPU + RAM':
                        formatted_result.update({
                            'CPU Modelo': result.get('cpu_model'),
                            'CPU Núcleos': result.get('cpu_cores'),
                            'CPU Velocidad': result.get('cpu_speed'),
                            'RAM Capacidad': result.get('ram_capacity'),
                            'RAM Velocidad': result.get('ram_speed'),
                            'RAM Tipo': result.get('ram_memory_type')
                        })
                    # Componentes separados
                    else:
                        if 'memory_capacity' in result:
                            formatted_result.update({
                                'Memoria RAM': f"{result.get('memory_capacity')}",
                                'Velocidad RAM': result.get('memory_speed'),
                                'Tipo RAM': result.get('memory_type')
                            })
                        if 'cpu_model' in result:
                            formatted_result.update({
                                'CPU Modelo': result.get('cpu_model'),
                                'CPU Núcleos': result.get('cpu_cores'),
                                'CPU Velocidad': result.get('cpu_speed')
                            })
                            
                    formatted_results.append(formatted_result)

                # Si se solicitó descarga
                if 'download' in request.form:
                    try:
                        temp_dir = tempfile.mkdtemp()
                        filename = secure_filename(asset_form.filename.data or 'output.xlsx')
                        if not filename.endswith('.xlsx'):
                            filename += '.xlsx'
                            
                        output_file = os.path.join(temp_dir, 'temp.xlsx')
                        options['output'] = output_file
                        
                        # Exportar datos y asegurarse de que el archivo se escriba completamente
                        manager.export_to_excel(results, output_file)
                        
                        # Verificar que el archivo existe y tiene tamaño
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                            response = send_file(
                                output_file,
                                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                download_name=filename
                            )
                            
                            @response.call_on_close
                            def cleanup():
                                try:
                                    shutil.rmtree(temp_dir)
                                except Exception as e:
                                    logger.error(f"Error cleaning up temp files: {e}")
                                    
                            return response
                        else:
                            flash('Error al generar el archivo Excel', 'error')
                            return redirect(url_for('search_id'))
                    except Exception as e:
                        logger.error(f"Error en la descarga: {e}")
                        flash(f'Error al generar el archivo: {str(e)}', 'error')
                    
                return render_template('search_id.html', 
                                    asset_form=asset_form,
                                    results=formatted_results)

            except Exception as e:
                logger.error(f"Error al procesar la solicitud: {e}")
                flash(f'Error al procesar la solicitud: {str(e)}', 'error')
                return render_template('search_id.html', asset_form=asset_form)
    
    return render_template('search_id.html', asset_form=asset_form)

@app.route('/search_criteria', methods=['GET', 'POST'])
def search_criteria():
    search_form = SearchForm()
    results = None
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        if 'submit_search' in request.form:
            search_type = request.form.get('search_type')
            search_value = request.form.get('search_value')
            download = 'download' in request.form
            
            if search_type == 'list_departments':
                departments = manager.list_departments()
                if departments:
                    # Crear lista de diccionarios para poder exportar
                    results = [{"Departamento": dept} for dept in departments]
                    
                    # Si se solicitó descarga
                    if 'download' in request.form:
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                                temp_path = tmp.name
                                
                            filename = secure_filename(search_form.filename.data or 'departamentos.xlsx')
                            if not filename.endswith('.xlsx'):
                                filename += '.xlsx'
                                
                            if manager.export_to_excel(results, temp_path):
                                response = send_file(
                                    temp_path,
                                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                )
                                response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
                                
                                @response.call_on_close
                                def cleanup():
                                    try:
                                        os.unlink(temp_path)
                                    except:
                                        pass
                                        
                                return response
                            else:
                                flash('Error al exportar los departamentos', 'error')
                        except Exception as e:
                            flash(f'Error al generar el archivo: {str(e)}', 'error')
                            logger.error(f"Error generating departments Excel: {e}")
            elif search_type == 'list_locations':
                logger.info("Requesting location tree")
                tree_data = manager.location_manager.format_location_tree()
                if tree_data:
                    logger.info(f"Found {len(tree_data)} location entries")
                    results = [{'text': line} for line in tree_data]
                    logger.debug(f"Location data: {results}")
                else:
                    logger.warning("No locations found")
                    flash('No se encontraron ubicaciones', 'warning')
            elif search_type == 'user' and search_value:
                results, message = manager.search_by_user(search_value)
                if not results:
                    flash(message, 'warning')
            elif search_type == 'department' and search_value:
                results, message = manager.search_by_department(search_value)
                if download and results:
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                            temp_path = tmp.name
                            
                        filename = secure_filename(search_form.filename.data or f'activos_{search_value}.xlsx')
                        if not filename.endswith('.xlsx'):
                            filename += '.xlsx'
                            
                        if manager.export_to_excel(results, temp_path):
                            response = send_file(
                                temp_path,
                                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )
                            response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
                            
                            @response.call_on_close
                            def cleanup():
                                try:
                                    os.unlink(temp_path)
                                except:
                                    pass
                                    
                            return response
                        else:
                            flash('Error al exportar los resultados', 'error')
                    except Exception as e:
                        flash(f'Error al generar el archivo: {str(e)}', 'error')
                        logger.error(f"Error generating department assets Excel: {e}")
            
            return render_template('search_criteria.html', 
                                search_form=search_form,
                                results=results)
    
    return render_template('search_criteria.html', search_form=search_form)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = FileUploadForm()
    
    if form.validate_on_submit():
        try:
            file = form.file.data
            if file and file.filename:
                # Leer el contenido del archivo
                content = file.read().decode('utf-8')
                
                # Procesar el contenido para extraer IDs
                ids = []
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        # Dividir por comas y agregar cada ID
                        ids.extend([id.strip() for id in line.split(',') if id.strip()])
                
                if ids:
                    # Guardar los IDs en la sesión
                    session['uploaded_ids'] = ','.join(ids)
                    flash(f'Se han cargado {len(ids)} IDs exitosamente', 'success')
                    return redirect(url_for('search'))
                else:
                    flash('No se encontraron IDs válidos en el archivo', 'warning')
            else:
                flash('Por favor seleccione un archivo', 'warning')
        except Exception as e:
            flash(f'Error al procesar el archivo: {str(e)}', 'error')
            logger.error(f"Error processing file: {e}")
    
    return render_template('upload.html', form=form)