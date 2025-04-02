# Freshservice Asset Management Tool

Una herramienta para gestionar y obtener información de activos desde Freshservice.

## Características

- Obtener información detallada de activos
- Buscar activos por usuario, departamento o ubicación
- Listar departamentos y ubicaciones
- Importar IDs de activos desde Excel
- Exportar resultados a Excel o txt
- Interfaz web para fácil gestión

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/freshservice-tools.git
cd freshservice-tools
```

2. Crear y activar un entorno virtual (recomendado):
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar credenciales:
   - Crear archivo .env con:
     ```
     FRESHSERVICE_SUBDOMAIN=tu-subdominio
     FRESHSERVICE_API_KEY=tu-api-key
     SECRET_KEY=una-clave-secreta-para-flask
     ```

## Uso

### Interfaz Web

Iniciar la aplicación web:

```bash
python run.py
```

Acceder a la aplicación en: http://localhost:8080

La interfaz web ofrece:
- Búsqueda de activos por ID
- Búsqueda por criterios (usuario, departamento, ubicación)
- Subida de archivos para procesar múltiples IDs

### Línea de Comandos

#### Obtener información de activos
```bash
python fstools.py -i 143-150 -a -o output.xlsx
```

#### Obtener componentes específicos
```bash
python fstools.py -i 143-150 -c cpu ram -o output.xlsx
```

#### Buscar por usuario
```bash
python fstools.py -su "John Doe" -o user_assets.xlsx
```

#### Listar ubicaciones
```bash
python fstools.py -ll
```

#### Importar IDs desde Excel
```bash
python fstools.py -ie assets.xlsx
```

## Opciones de línea de comandos

### Información
- `-d`: Nombres de departamentos
- `-t`: Tipo de activo
- `-l`: Ubicación
- `-u`: Información de usuario
- `-s`: Sistema operativo
- `-n`: IP de máquina
- `-m`: Dirección MAC
- `-sn`: Número de serie
- `-desc`: Descripción del activo
- `-a`: Todos los datos del activo

### Búsqueda
- `-su`: Buscar por nombre de usuario
- `-sd`: Buscar por departamento
- `-sl`: Buscar por ubicación
- `-ld`: Listar departamentos
- `-ll`: Listar ubicaciones

### Componentes
- `-c`: Especificar tipos de componentes
- `-dj`: Deshabilitar unión de RAM
- `-jc`: Combinar CPU y RAM

### Archivos
- `-ie`: Importar IDs desde Excel
- `-o`: Exportar resultados
- `-v`: Mostrar resultados en consola

## Despliegue

Para desplegar en un servidor de producción:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 'web:app'
```

## Contribuir

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está licenciado bajo la licencia MIT.
