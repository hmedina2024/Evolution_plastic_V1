from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging
import datetime  # Añade esta importación si usas datetime en los modelos
from flask_cors import CORS  # Importa CORS


# Inicializa la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para toda la aplicación

app.secret_key = 'xxx'  # Mantén tu clave secreta actual

# Configura SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Evolution123#@217.15.171.201/evolution_DB'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Yamasaqui2024*@localhost/evolution_DB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desactiva notificaciones de modificaciones para ahorrar recursos
app.config['SQLALCHEMY_POOL_SIZE'] = 10  # Aumenta a 10 para manejar 10+ usuarios simultáneos
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20  # Máximo de conexiones adicionales (30 conexiones totales max)
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # Tiempo máximo en segundos para esperar una conexión
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True  # Verifica conexiones antes de usarlas
}

# Inicializa SQLAlchemy
db = SQLAlchemy(app)

# Configura logging para errores
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Importa los modelos después de inicializar SQLAlchemy
from conexion.models import Operaciones, Empleados, TipoEmpleado, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users  # Importa directamente los modelos

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen (solo para desarrollo, coméntalo en producción)
    app.run(host="0.0.0.0", port=8000, debug=True)