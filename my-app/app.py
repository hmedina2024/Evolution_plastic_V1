import os
import logging
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import datetime
from dotenv import load_dotenv

# Carga las variables de entorno desde un archivo .env (opcional, útil para desarrollo)
# Asegúrate de tener python-dotenv instalado: pip install python-dotenv
# Crea un archivo .env en la raíz de my-app/
load_dotenv()

# Configura logging antes de inicializar la app
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# Inicializa la aplicación Flask
app = Flask(__name__)
CORS(app)

# --- VARIABLES DE ENTORNO ---
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError("SECRET_KEY no definida en variables de entorno")

db_user     = os.environ.get('DB_USER', 'root')
db_password = os.environ.get('DB_PASSWORD', '')
db_host     = os.environ.get('DB_HOST', 'localhost')
db_name     = os.environ.get('DB_NAME', 'evolution_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
# --- FIN VARIABLES DE ENTORNO ---

# Límite de tamaño de archivos: 10 MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Sesiones permanentes expiran en 8 horas
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# CSRF
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
csrf = CSRFProtect(app)

# Rate limiting — máx 10 intentos de login por minuto por IP
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True
}

# Inicializa SQLAlchemy
# db = SQLAlchemy(app)
# Importamos la db vacía desde el nuevo archivo
from conexion.database import db

# La conectamos con la app
db.init_app(app)

# Vincula el logger de Flask al logger personalizado
app.logger.handlers = logger.handlers
app.logger.setLevel(logging.DEBUG)

# Prueba el logging
app.logger.debug("Aplicación iniciada - Logging de prueba")

if not app.debug:
    if __name__ != '__main__':
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

# Importa modelos DESPUÉS de inicializar db
# Asegúrate de que la ruta de importación sea correcta según tu estructura
# Si models.py está en my-app/conexion/
from conexion.models import Operaciones, Empleados, Tipo_Empleado, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users
# Si models.py estuviera directamente en my-app/
# from models import Operaciones, Empleados, ...

# El bloque if __name__ == '__main__': para app.run() y db.create_all()
# debería estar idealmente solo en run.py (para desarrollo)
# y db.create_all() comentado/eliminado para producción.
# Si ejecutas con `gunicorn app:app`, este bloque no se ejecutará de todas formas.
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all() # Comentar/Eliminar en producción
#     app.run(host="0.0.0.0", port=8000, debug=True) # Solo para desarrollo