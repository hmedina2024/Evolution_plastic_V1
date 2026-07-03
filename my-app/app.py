import os
import time as _time
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

# Sesiones permanentes expiran en 24 horas
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Cache-busting: token único generado al arrancar el servidor.
# Cada reinicio (nuevo despliegue) cambia el valor y los navegadores
# descartan el caché de CSS/JS propios sin que el usuario haga nada.
app.jinja_env.globals['STATIC_V'] = str(int(_time.time()))

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

# --- CABECERAS DE SEGURIDAD (Flask-Talisman) ---
# Import protegido: si el paquete no está instalado, la app sigue funcionando.
try:
    from flask_talisman import Talisman

    # CSP permisiva: la app usa scripts/estilos inline y varios CDNs.
    # Declara una política sin romper la funcionalidad existente.
    _csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'", "'unsafe-inline'", "'unsafe-eval'",
            'https://cdn.jsdelivr.net',
            'https://code.jquery.com',
            'https://cdn.datatables.net',
            'https://cdnjs.cloudflare.com',
        ],
        'style-src': [
            "'self'", "'unsafe-inline'",
            'https://cdn.jsdelivr.net',
            'https://cdn.datatables.net',
            'https://cdnjs.cloudflare.com',
            'https://fonts.googleapis.com',
        ],
        'img-src': ["'self'", 'data:', 'https:'],
        'font-src': [
            "'self'", 'data:',
            'https://cdn.jsdelivr.net',
            'https://fonts.gstatic.com',
            'https://cdnjs.cloudflare.com',
        ],
        'connect-src': ["'self'"],
        # Reportes Power BI embebidos vía iframe
        'frame-src': ["'self'", 'https://app.powerbi.com'],
    }

    # En local (HTTP) no forzar HTTPS ni cookies seguras para no romper el dev.
    # En producción definir TALISMAN_FORCE_HTTPS=true.
    _force_https = os.environ.get('TALISMAN_FORCE_HTTPS', 'false').lower() == 'true'

    Talisman(
        app,
        force_https=_force_https,
        strict_transport_security=_force_https,
        session_cookie_secure=_force_https,
        content_security_policy=_csp,
        frame_options='SAMEORIGIN',
        referrer_policy='strict-origin-when-cross-origin',
    )
    app.logger.info(f"Flask-Talisman activo (force_https={_force_https}).")
except ImportError:
    app.logger.warning(
        "Flask-Talisman no está instalado; cabeceras de seguridad deshabilitadas. "
        "Ejecute 'pip install flask-talisman' para activarlas."
    )
# --- FIN CABECERAS DE SEGURIDAD ---

# --- CACHÉ DE ENDPOINTS /api/* (Flask-Caching) ---
# TTL configurable con API_CACHE_TIMEOUT (segundos). 0 = caché desactivada.
# Import protegido: si la librería no está, se usa un no-op y la app sigue igual.
try:
    from flask_caching import Cache
    _api_cache_ttl = int(os.environ.get('API_CACHE_TIMEOUT', '60'))
    if _api_cache_ttl > 0:
        cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache',
                                   'CACHE_DEFAULT_TIMEOUT': _api_cache_ttl})
        app.logger.info(f"Flask-Caching activo (SimpleCache, TTL={_api_cache_ttl}s).")
    else:
        cache = Cache(app, config={'CACHE_TYPE': 'NullCache'})
        app.logger.info("Flask-Caching: caché desactivada (API_CACHE_TIMEOUT=0).")
except ImportError:
    class _NoCache:
        """Sustituto no-op si Flask-Caching no está instalado."""
        def cached(self, *args, **kwargs):
            def _decorador(f):
                return f
            return _decorador
        def clear(self):
            pass
    cache = _NoCache()
    app.logger.warning("Flask-Caching no instalado; caché de API deshabilitada (no-op).")
# --- FIN CACHÉ ---

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

# --- Invalidación automática de la caché de /api/* ---
# Cuando cambia (alta/edición/baja) una entidad de referencia usada en los
# dropdowns cacheados, se limpia la caché para no servir datos obsoletos.
from sqlalchemy import event as _sa_event

_NOMBRES_MODELOS_REF = {
    'Clientes', 'Empleados', 'Procesos', 'Empresa', 'Actividades', 'Piezas', 'Tipo_Empleado'
}

@_sa_event.listens_for(db.session, 'after_flush')
def _marcar_cambio_referencia(session, flush_context):
    objetos = list(session.new) + list(session.dirty) + list(session.deleted)
    if any(type(o).__name__ in _NOMBRES_MODELOS_REF for o in objetos):
        session.info['_limpiar_cache_api'] = True

@_sa_event.listens_for(db.session, 'after_commit')
def _limpiar_cache_referencia(session):
    if session.info.pop('_limpiar_cache_api', False):
        try:
            cache.clear()
            app.logger.debug("Caché de /api/* invalidada por cambio en entidad de referencia.")
        except Exception as _e:
            app.logger.warning(f"No se pudo invalidar la caché de API: {_e}")

# --- Inicialización del sistema de Roles y Permisos ---
# Importa el módulo (registra el global de Jinja 'tiene_permiso') y siembra los
# datos base de forma idempotente. Todo va protegido para no afectar el arranque.
try:
    with app.app_context():
        from controllers.funciones_permisos import seed_permisos_y_roles
        seed_permisos_y_roles()
except Exception as _e_perm:
    app.logger.warning(f"No se pudo inicializar el sistema de permisos al arranque: {_e_perm}")

# El bloque if __name__ == '__main__': para app.run() y db.create_all()
# debería estar idealmente solo en run.py (para desarrollo)
# y db.create_all() comentado/eliminado para producción.
# Si ejecutas con `gunicorn app:app`, este bloque no se ejecutará de todas formas.
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all() # Comentar/Eliminar en producción
#     app.run(host="0.0.0.0", port=8000, debug=True) # Solo para desarrollo