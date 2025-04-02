from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired, Optional, ValidationError
import os

def validate_txt_file(form, field):
    if field.data:
        filename = field.data.filename
        if not filename.endswith('.txt'):
            raise ValidationError('Solo se permiten archivos .txt')

class FileUploadForm(FlaskForm):
    file = FileField('Archivo de IDs', validators=[DataRequired(), validate_txt_file],
                    description='Seleccione un archivo .txt con IDs (uno por línea)')
    submit = SubmitField('Cargar IDs')

class AssetForm(FlaskForm):
    ids = StringField('IDs de Activos', validators=[DataRequired()],
                     description='Ejemplo: 143-150,155,160')
    exclude = StringField('IDs a Excluir',
                        description='Ejemplo: 145,147')
    components = SelectMultipleField('Componentes',
                                   choices=[
                                       ('cpu', 'Procesador (CPU)'),
                                       ('ram', 'Memoria (RAM)'),
                                       ('hdd', 'Disco Duro'),
                                       ('nic', 'Adaptador de Red')
                                   ])
    include_info = SelectMultipleField('Información a Incluir',
                                     choices=[
                                         ('departments', 'Departamentos'),
                                         ('location', 'Ubicación'),
                                         ('user', 'Usuario'),
                                         ('system', 'Sistema Operativo'),
                                         ('machine_ip', 'IP'),
                                         ('machine_mac', 'MAC'),
                                         ('serial_number', 'Número de Serie'),
                                         ('description', 'Descripción')
                                     ])
    disable_join = BooleanField('Desactivar unión de RAM')
    combine_cpu_ram = BooleanField('Combinar CPU y RAM')
    all_data = BooleanField('Incluir todos los datos')
    filename = StringField('Nombre del archivo', validators=[Optional()], 
                         description='Nombre para guardar el archivo (opcional)')
    submit = SubmitField('Buscar Activos')

class SearchForm(FlaskForm):
    search_type = SelectField('Tipo de Búsqueda',
                            choices=[
                                ('user', 'Usuario'),
                                ('department', 'Departamento'),
                                ('location', 'Ubicación'),
                                ('list_departments', 'Listar Departamentos'),
                                ('list_locations', 'Listar Ubicaciones')
                            ])
    search_value = StringField('Término de Búsqueda')  # Removido el validator ya que no siempre se necesita
    filename = StringField('Nombre del archivo', validators=[Optional()],
                         description='Nombre para guardar el archivo (opcional)')
    submit = SubmitField('Buscar')
