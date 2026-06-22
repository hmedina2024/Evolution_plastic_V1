"""Sistema de Roles y Permisos administrable desde la UI.

Diseño de seguridad:
- El rol 'Administrador' SIEMPRE tiene todos los permisos (bypass) → nunca se
  puede autobloquear ni perder acceso al módulo de permisos.
- Si el sistema aún no está sembrado o las tablas no existen, se usa un FALLBACK
  con el mismo mapa que la semilla (DEFAULT_ROLES), de modo que el comportamiento
  es idéntico antes y después de sembrar (no hay regresión al desplegar).
- Los permisos del usuario se cargan una sola vez por request (cache en flask.g).
"""
from functools import wraps
from datetime import datetime

from flask import session, g, redirect, url_for, flash, request, jsonify

from app import app
from conexion.models import db, Rol, Permiso, RolPermiso

ROL_ADMIN = 'Administrador'

# Catálogo: (modulo, etiqueta, [acciones])
CATALOGO_MODULOS = [
    ('dashboard',   'Dashboard',                    ['ver']),
    ('op',          'Órdenes de Producción',        ['ver', 'crear', 'editar', 'eliminar']),
    ('odi',         'Órdenes de Diseño Industrial', ['ver', 'crear', 'editar', 'eliminar']),
    ('operaciones', 'Operaciones',                  ['ver', 'crear', 'editar', 'eliminar']),
    ('jornadas',    'Novedades / Jornadas',         ['ver', 'crear', 'editar', 'eliminar']),
    ('empleados',   'Empleados',                    ['ver', 'crear', 'editar', 'eliminar']),
    ('clientes',    'Clientes',                     ['ver', 'crear', 'editar', 'eliminar']),
    ('procesos',    'Procesos',                     ['ver', 'crear', 'editar', 'eliminar']),
    ('actividades', 'Actividades',                  ['ver', 'crear', 'editar', 'eliminar']),
    ('empresas',    'Empresas',                     ['ver', 'crear', 'editar', 'eliminar']),
    ('usuarios',    'Usuarios',                     ['ver', 'crear', 'editar', 'eliminar']),
    ('reportes',    'Reportes',                     ['ver']),
    ('auditoria',   'Auditoría (Logs de acceso)',   ['ver']),
    ('permisos',    'Roles y Permisos',             ['ver', 'editar']),
]

ACCION_LABELS = {'ver': 'Ver', 'crear': 'Crear', 'editar': 'Editar', 'eliminar': 'Eliminar'}


def _claves(modulo, acciones):
    return {f'{modulo}.{a}' for a in acciones}


# Permisos por defecto que REPLICAN el comportamiento actual del sistema.
DEFAULT_SUPERVISOR = (
    _claves('dashboard', ['ver'])
    | _claves('op', ['ver', 'crear', 'editar'])
    | _claves('odi', ['ver', 'crear', 'editar'])
    | _claves('operaciones', ['ver', 'crear', 'editar', 'eliminar'])
    | _claves('jornadas', ['ver', 'crear', 'editar', 'eliminar'])
    | _claves('empleados', ['ver'])
    | _claves('clientes', ['ver'])
    | _claves('procesos', ['ver'])
    | _claves('actividades', ['ver'])
    | _claves('empresas', ['ver'])
    | _claves('usuarios', ['ver'])
    | _claves('reportes', ['ver'])
)

DEFAULT_OPERARIO = (
    _claves('dashboard', ['ver'])
    | _claves('operaciones', ['ver', 'crear', 'editar'])
    | _claves('jornadas', ['ver', 'crear', 'editar'])
)

# Mapa de fallback (mismo que la semilla) para roles no-admin.
DEFAULT_ROLES = {
    'Supervisor': DEFAULT_SUPERVISOR,
    'Operativo': DEFAULT_OPERARIO,
}


def todas_las_claves():
    claves = set()
    for modulo, _label, acciones in CATALOGO_MODULOS:
        claves |= _claves(modulo, acciones)
    return claves


# ---------------------------------------------------------------------------
# Semilla (idempotente)
# ---------------------------------------------------------------------------
def seed_permisos_y_roles():
    """Crea el catálogo de permisos y los roles base si no existen.

    Idempotente: se puede llamar muchas veces sin duplicar. Asegura además que
    'Administrador' tenga TODOS los permisos (incluidos los nuevos que se agreguen).
    """
    try:
        existentes = {p.clave for p in db.session.query(Permiso).all()}
        for modulo, label, acciones in CATALOGO_MODULOS:
            for accion in acciones:
                clave = f'{modulo}.{accion}'
                if clave not in existentes:
                    db.session.add(Permiso(
                        modulo=modulo, accion=accion, clave=clave,
                        descripcion=f'{ACCION_LABELS.get(accion, accion)} — {label}'
                    ))
        db.session.flush()
        perm_por_clave = {p.clave: p for p in db.session.query(Permiso).all()}

        roles_base = [
            ('Administrador', 'Acceso total al sistema', 'all'),
            ('Supervisor', 'Gestión de producción y diseño', DEFAULT_SUPERVISOR),
            ('Operativo', 'Registro de operaciones y novedades', DEFAULT_OPERARIO),
        ]
        for nombre, desc, claves in roles_base:
            rol = db.session.query(Rol).filter_by(nombre_rol=nombre).first()
            if not rol:
                rol = Rol(nombre_rol=nombre, descripcion=desc, es_sistema=True)
                db.session.add(rol)
                db.session.flush()
                claves_asignar = set(perm_por_clave.keys()) if claves == 'all' else claves
                for clave in claves_asignar:
                    p = perm_por_clave.get(clave)
                    if p:
                        db.session.add(RolPermiso(id_rol=rol.id_rol, id_permiso=p.id_permiso))
            elif nombre == ROL_ADMIN:
                # Garantizar que Administrador siempre tenga todos los permisos
                asignados = {rp.id_permiso for rp in rol.permisos}
                for p in perm_por_clave.values():
                    if p.id_permiso not in asignados:
                        db.session.add(RolPermiso(id_rol=rol.id_rol, id_permiso=p.id_permiso))
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"seed_permisos_y_roles falló (¿migración pendiente?): {e}")
        return False


# ---------------------------------------------------------------------------
# Resolución de permisos
# ---------------------------------------------------------------------------
def _cargar_permisos_desde_db(nombre_rol):
    """Devuelve el set de claves del rol, o None si no se puede resolver (usar fallback)."""
    try:
        rol = db.session.query(Rol).filter_by(nombre_rol=nombre_rol, fecha_borrado=None).first()
        if not rol:
            return None  # rol no gestionado en BD → usar fallback legacy
        return {rp.permiso.clave for rp in rol.permisos if rp.permiso}
    except Exception as e:
        app.logger.warning(f"No se pudieron cargar permisos de '{nombre_rol}': {e}")
        return None


def _permisos_actuales(nombre_rol):
    """Carga (y cachea en g por request) el set de permisos del rol."""
    if not hasattr(g, '_permisos_cache'):
        g._permisos_cache = {}
    if nombre_rol not in g._permisos_cache:
        g._permisos_cache[nombre_rol] = _cargar_permisos_desde_db(nombre_rol)
    return g._permisos_cache[nombre_rol]


def tiene_permiso(clave):
    """True si el usuario en sesión tiene el permiso indicado (ej. 'op.crear')."""
    rol = session.get('rol')
    if not rol:
        return False
    if rol == ROL_ADMIN:
        return True
    permisos = _permisos_actuales(rol)
    if permisos is None:
        # Sistema no sembrado o error → comportamiento legacy equivalente
        return clave in DEFAULT_ROLES.get(rol, set())
    return clave in permisos


def requiere_permiso(clave):
    """Decorador de ruta: exige sesión + permiso. Si falla, 403 (AJAX) o redirect."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'conectado' not in session:
                flash('Primero debes iniciar sesión.', 'error')
                return redirect(url_for('inicio'))
            if not tiene_permiso(clave):
                es_ajax = (request.path.startswith('/api/')
                           or request.path.startswith('/buscando-')
                           or request.headers.get('X-Requested-With') == 'XMLHttpRequest')
                if es_ajax:
                    return jsonify({'status': 'error', 'message': 'No tienes permisos para esta acción.'}), 403
                flash('No tienes permisos para acceder a esta sección.', 'error')
                return redirect(url_for('inicio'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# CRUD de roles y matriz de permisos (para el módulo de administración)
# ---------------------------------------------------------------------------
def listar_roles():
    roles = db.session.query(Rol).filter(Rol.fecha_borrado.is_(None)).order_by(Rol.id_rol.asc()).all()
    data = []
    for r in roles:
        data.append({
            'id_rol': r.id_rol,
            'nombre_rol': r.nombre_rol,
            'descripcion': r.descripcion or '',
            'es_sistema': r.es_sistema,
            'num_permisos': len(r.permisos),
        })
    return data


def nombres_roles_disponibles():
    """Lista los nombres de roles activos (para poblar dropdowns de usuario).

    Defensivo: si las tablas aún no existen o no hay roles, devuelve los roles
    base por defecto para no dejar el formulario sin opciones.
    """
    try:
        roles = db.session.query(Rol).filter(Rol.fecha_borrado.is_(None)).order_by(Rol.id_rol.asc()).all()
        nombres = [r.nombre_rol for r in roles]
        if nombres:
            return nombres
    except Exception as e:
        app.logger.warning(f"nombres_roles_disponibles: {e}")
    return ['Administrador', 'Supervisor', 'Operativo']


def crear_rol(nombre, descripcion=''):
    nombre = (nombre or '').strip()
    if not nombre:
        return False, 'El nombre del rol es obligatorio.'
    existe = db.session.query(Rol).filter(func_lower_eq(Rol.nombre_rol, nombre)).first()
    if existe:
        return False, f"Ya existe un rol llamado '{nombre}'."
    try:
        rol = Rol(nombre_rol=nombre, descripcion=(descripcion or '').strip() or None, es_sistema=False)
        db.session.add(rol)
        db.session.commit()
        return True, rol.id_rol
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creando rol: {e}")
        return False, 'Error al crear el rol.'


def actualizar_rol(id_rol, nombre, descripcion=''):
    rol = db.session.query(Rol).filter_by(id_rol=id_rol, fecha_borrado=None).first()
    if not rol:
        return False, 'Rol no encontrado.'
    nombre = (nombre or '').strip()
    if not nombre:
        return False, 'El nombre del rol es obligatorio.'
    # No permitir renombrar el rol Administrador (clave del sistema)
    if rol.nombre_rol == ROL_ADMIN and nombre != ROL_ADMIN:
        return False, 'El rol Administrador no se puede renombrar.'
    duplicado = db.session.query(Rol).filter(
        func_lower_eq(Rol.nombre_rol, nombre), Rol.id_rol != id_rol
    ).first()
    if duplicado:
        return False, f"Ya existe otro rol llamado '{nombre}'."
    try:
        nombre_anterior = rol.nombre_rol
        rol.nombre_rol = nombre
        rol.descripcion = (descripcion or '').strip() or None
        # Mantener consistencia: usuarios con el nombre anterior pasan al nuevo
        if nombre_anterior != nombre:
            from conexion.models import Users
            db.session.query(Users).filter_by(rol=nombre_anterior).update({'rol': nombre})
        db.session.commit()
        return True, 'Rol actualizado.'
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error actualizando rol: {e}")
        return False, 'Error al actualizar el rol.'


def eliminar_rol(id_rol):
    rol = db.session.query(Rol).filter_by(id_rol=id_rol, fecha_borrado=None).first()
    if not rol:
        return False, 'Rol no encontrado.'
    if rol.es_sistema:
        return False, 'Los roles del sistema no se pueden eliminar.'
    # No eliminar si hay usuarios usando el rol
    from conexion.models import Users
    en_uso = db.session.query(Users).filter_by(rol=rol.nombre_rol, fecha_borrado=None).count()
    if en_uso > 0:
        return False, f'No se puede eliminar: {en_uso} usuario(s) tienen este rol asignado.'
    try:
        rol.fecha_borrado = datetime.now()
        db.session.commit()
        return True, 'Rol eliminado.'
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error eliminando rol: {e}")
        return False, 'Error al eliminar el rol.'


def obtener_matriz_rol(id_rol):
    """Devuelve el catálogo agrupado por módulo + las claves que el rol tiene marcadas."""
    rol = db.session.query(Rol).filter_by(id_rol=id_rol, fecha_borrado=None).first()
    if not rol:
        return None
    claves_rol = {rp.permiso.clave for rp in rol.permisos if rp.permiso}
    columnas = ['ver', 'crear', 'editar', 'eliminar']
    modulos = []
    for modulo, label, acciones in CATALOGO_MODULOS:
        cols = {}
        for accion in columnas:
            if accion in acciones:
                clave = f'{modulo}.{accion}'
                cols[accion] = {'clave': clave, 'activo': clave in claves_rol}
            else:
                cols[accion] = None  # el módulo no tiene esta acción
        modulos.append({'modulo': modulo, 'label': label, 'cols': cols})
    return {
        'id_rol': rol.id_rol,
        'nombre_rol': rol.nombre_rol,
        'descripcion': rol.descripcion or '',
        'es_admin': rol.nombre_rol == ROL_ADMIN,
        'modulos': modulos,
    }


def guardar_permisos_rol(id_rol, claves_seleccionadas):
    """Reemplaza el conjunto de permisos del rol por las claves indicadas."""
    rol = db.session.query(Rol).filter_by(id_rol=id_rol, fecha_borrado=None).first()
    if not rol:
        return False, 'Rol no encontrado.'
    # El Administrador siempre conserva todos los permisos
    if rol.nombre_rol == ROL_ADMIN:
        return False, 'El rol Administrador siempre tiene todos los permisos (no editable).'
    try:
        validas = todas_las_claves()
        claves = {c for c in (claves_seleccionadas or []) if c in validas}
        perm_por_clave = {p.clave: p for p in db.session.query(Permiso).all()}

        # Limpiar permisos actuales y hacer flush para que los DELETE se
        # ejecuten ANTES de los INSERT (evita violar uq_rol_permiso).
        rol.permisos.clear()
        db.session.flush()

        for c in claves:
            if c in perm_por_clave:
                rol.permisos.append(RolPermiso(id_permiso=perm_por_clave[c].id_permiso))
        db.session.commit()
        return True, 'Permisos actualizados correctamente.'
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error guardando permisos del rol {id_rol}: {e}")
        return False, 'Error al guardar los permisos.'


def func_lower_eq(columna, valor):
    """Comparación case-insensitive para nombres de rol."""
    from sqlalchemy import func
    return func.lower(columna) == func.lower(valor)


# Registrar tiene_permiso como global de Jinja para usarlo en las plantillas.
app.jinja_env.globals['tiene_permiso'] = tiene_permiso
