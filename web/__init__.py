import os
from flask import Flask 
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect

# Definir rutas absolutas
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Asegurarse que los directorios static/img y static/css existen
img_dir = os.path.join(STATIC_DIR, 'img')
css_dir = os.path.join(STATIC_DIR, 'css')
os.makedirs(img_dir, exist_ok=True)
os.makedirs(css_dir, exist_ok=True)

# Crear app con las rutas correctas
app = Flask(__name__, 
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR)

app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)
csrf = CSRFProtect(app)

# Importar rutas después de crear la aplicación
from web import routes
