import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # Importa CORS
import datetime


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
CORS(app)  # Habilita CORS para toda la aplicación

app.secret_key = 'secretEvolutioControl'  # Mantén tu clave secreta actual

# Configura SQLAlchemy
##app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Yamasaqui2024*@localhost/evolution_plastic'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Evolution123#@217.15.171.201/evolution_DB'
##app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Yamasaqui2024*@localhost/evolution_DB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desactiva notificaciones de modificaciones para ahorrar recursos
app.config['SQLALCHEMY_POOL_SIZE'] = 10  # Aumenta a 10 para manejar 10+ usuarios simultáneos
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20  # Máximo de conexiones adicionales (30 conexiones totales max)
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # Tiempo máximo en segundos para esperar una conexión
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True  # Verifica conexiones antes de usarlas
}

# Inicializa SQLAlchemy
db = SQLAlchemy(app)

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

from conexion.models import Operaciones, Empleados, Tipo_Empleado, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)