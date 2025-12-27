import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import datetime
# Importa la librería dotenv si decides usarla para desarrollo
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

# --- USO DE VARIABLES DE ENTORNO ---
# Obtiene la SECRET_KEY desde las variables de entorno
# Proporciona un valor predeterminado SOLO para desarrollo si la variable no está definida
app.secret_key = os.environ.get('SECRET_KEY', 'secretEvolutioControllocalhost')

# Obtiene las credenciales de la base de datos desde las variables de entorno
db_user = os.environ.get('DB_USER', 'root') # Valor predeterminado para desarrollo
db_password = os.environ.get('DB_PASSWORD', 'Yamasaqui2024*') # ¡CAMBIA ESTO para desarrollo!
db_host = os.environ.get('DB_HOST', 'localhost') # Valor predeterminado para desarrollo
db_name = os.environ.get('DB_NAME', 'evolution_db') # Valor predeterminado para desarrollo

# Configura SQLAlchemy usando las variables obtenidas
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
# --- FIN USO DE VARIABLES DE ENTORNO ---

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