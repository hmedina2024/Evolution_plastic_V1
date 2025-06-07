from flask_sqlalchemy import SQLAlchemy
from app import db  # Importa db desde app.py, donde se inicializa
# Quitamos import datetime ya que no se usa directamente aquí
from sqlalchemy.sql import func  # Importa func para usar func.now()
from sqlalchemy import Enum # Para el Enum de Empresa
from datetime import datetime

# --- Modelo Empresa ---
# Definido antes porque otros modelos dependen de él
class Empresa(db.Model):
    __tablename__ = 'tbl_empresas'

    id_empresa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_empresa = db.Column(db.String(100), nullable=False)
    # Usamos Enum nativo de SQLAlchemy
    tipo_empresa = db.Column(Enum('Directo', 'Temporal', name='tipo_empresa_enum'), nullable=False)
    nit = db.Column(db.String(20), nullable=False, unique=True)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, nullable=False, default=func.now())
    # FK a Users
    id_usuario_registro = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fecha_borrado = db.Column(db.DateTime)

    # Relación con Users (quién registró)
    usuario_reg = db.relationship('Users', backref='empresas_registradas')
    # La relación inversa 'empleados' se define en Empleados
    # La relación inversa 'tipos_empleado' se define en Tipo_Empleado

# --- Modelo Tipo_Empleado ---
# Relacionado con Empresa y Empleados
class Tipo_Empleado(db.Model):
    __tablename__ = 'tbl_tipo_empleado'
    id_tipo_empleado = db.Column(db.Integer, primary_key=True)
    tipo_empleado = db.Column(db.String(50), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relación con Empleados (usamos un backref diferente para evitar conflictos)
    empleados = db.relationship('Empleados', backref='tipo_empleado_ref')

# --- Modelo TipoDocumento ---
# Usado por Clientes y potencialmente Empleados
class TipoDocumento(db.Model):
    __tablename__ = 'tbl_tipo_documento'
    id_tipo_documento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    td_abreviacion = db.Column(db.String(45), nullable=False, unique=True) # Ej. CC, NIT, CE
    tipo_documento = db.Column(db.String(45), nullable=False) # Ej. Cédula de Ciudadanía, NIT, Cédula Extranjería
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    # La relación inversa 'clientes' se define en Clientes

# --- Modelo Users ---
# Usuarios del sistema
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name_surname = db.Column(db.String(100), nullable=False)
    email_user = db.Column(db.String(50), nullable=False, unique=True)
    pass_user = db.Column(db.Text, nullable=False)  # Almacena el hash
    rol = db.Column(db.String(45), nullable=False) # Ej. 'Admin', 'Supervisor', 'Operario'
    created_user = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime)
    # Relaciones inversas definidas en otros modelos:
    # operaciones_registradas, ordenes_produccion_registradas, jornadas_registradas, empresas_registradas

# --- Modelo Empleados ---
class Empleados(db.Model):
    __tablename__ = 'tbl_empleados'
    id_empleado = db.Column(db.Integer, primary_key=True)
    documento = db.Column(db.String(50), nullable=False, unique=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('tbl_empresas.id_empresa'), nullable=False)
    nombre_empleado = db.Column(db.String(50), nullable=True)
    apellido_empleado = db.Column(db.String(50), nullable=True)
    id_tipo_empleado = db.Column(db.Integer, db.ForeignKey('tbl_tipo_empleado.id_tipo_empleado'), nullable=True)
    telefono_empleado = db.Column(db.String(50), nullable=True)
    email_empleado = db.Column(db.String(50), nullable=True, unique=True)
    cargo = db.Column(db.String(50), nullable=True)
    foto_empleado = db.Column(db.Text, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relaciones
    empresa = db.relationship('Empresa', backref='empleados')

# --- Modelo Procesos ---
class Procesos(db.Model):
    __tablename__ = 'tbl_procesos'
    id_proceso = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_proceso = db.Column(db.String(50), nullable=False, unique=True)
    nombre_proceso = db.Column(db.String(50), nullable=True) # Ajustado a nullable=True como en tu SQL
    descripcion_proceso = db.Column(db.String(200), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False) # Considera usar default=func.now() para consistencia
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relaciones
    orden_piezas_procesos = db.relationship('OrdenPiezasProcesos', backref='proceso', lazy=True)
    # Asegúrate de que las relaciones inversas ('operaciones') estén definidas si las necesitas
    operaciones = db.relationship('Operaciones', lazy=True) # Ejemplo


# --- Modelo Piezas ---
class Piezas(db.Model):
    __tablename__ = 'tbl_piezas'
    id_pieza = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_pieza = db.Column(db.String(50), nullable=True)
    descripcion_pieza = db.Column(db.String(200), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relaciones
    orden_piezas = db.relationship('OrdenPiezas', backref='pieza', lazy=True)


# --- Modelo Actividades ---
class Actividades(db.Model):
    __tablename__ = 'tbl_actividades'
    id_actividad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_actividad = db.Column(db.String(50), nullable=False, unique=True)
    nombre_actividad = db.Column(db.String(50), nullable=True)
    descripcion_actividad = db.Column(db.String(200), nullable=True)
    id_proceso = db.Column(db.Integer, db.ForeignKey('tbl_procesos.id_proceso'), nullable=False) # Nueva FK
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)
    
    # Relación con Procesos (Una Actividad pertenece a Un Proceso)
    proceso = db.relationship('Procesos', backref=db.backref('actividades', lazy='dynamic'))
    # Relación inversa 'operaciones' definida en Operaciones (si aún es relevante directamente con actividad)

# --- Modelo Clientes ---
class Clientes(db.Model):
    __tablename__ = 'tbl_clientes'
    id_cliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # FK a TipoDocumento
    id_tipo_documento = db.Column(db.Integer, db.ForeignKey('tbl_tipo_documento.id_tipo_documento'), nullable=True)
    # Ajuste: String y unique
    documento = db.Column(db.String(50), nullable=False, unique=True)
    nombre_cliente = db.Column(db.String(50), nullable=True)
    telefono_cliente = db.Column(db.String(50), nullable=True)
    email_cliente = db.Column(db.String(50), nullable=True)
    foto_cliente = db.Column(db.Text, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relación con TipoDocumento
    tipo_documento_rel = db.relationship('TipoDocumento', backref='clientes')
    # Relación inversa 'ordenes_produccion' definida en OrdenProduccion

# --- Modelo Operaciones ---
# (Registro de trabajo diario)
class Operaciones(db.Model):
    __tablename__ = 'tbl_operaciones'
    id_operacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # FK a Empleados (ya estaba)
    id_empleado = db.Column(db.Integer, db.ForeignKey('tbl_empleados.id_empleado'), nullable=False)
    # FK a Procesos
    id_proceso = db.Column(db.Integer, db.ForeignKey('tbl_procesos.id_proceso'), nullable=True)
    # FK a Actividades
    id_actividad = db.Column(db.Integer, db.ForeignKey('tbl_actividades.id_actividad'), nullable=True)
    # FK a OrdenProduccion
    id_op = db.Column(db.Integer, db.ForeignKey('tbl_ordenproduccion.id_op'), nullable=True)
    cantidad = db.Column(db.Integer, nullable=True)
    pieza_realizada = db.Column(db.String(100), nullable=True)
    novedad = db.Column(db.Text, nullable=True)
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False)
    fecha_hora_fin = db.Column(db.DateTime, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    # FK a Users (quién registra)
    id_usuario_registro = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relaciones
    empleado = db.relationship('Empleados', backref='operaciones') # foreign_keys no es necesario si solo hay una FK a Empleados
    proceso_rel = db.relationship('Procesos')
    actividad_rel = db.relationship('Actividades', backref='operaciones')
    orden_produccion = db.relationship('OrdenProduccion', backref='operaciones')
    usuario_reg = db.relationship('Users', backref='operaciones_registradas')

# --- Modelo Jornadas ---
# (Control de asistencia/turnos)
class Jornadas(db.Model):
    __tablename__ = 'tbl_jornadas'
    id_jornada = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # FK a Empleados (ya estaba)
    id_empleado = db.Column(db.Integer, db.ForeignKey('tbl_empleados.id_empleado'), nullable=False)
    novedad_jornada_programada = db.Column(db.String(200), nullable=True)
    novedad_jornada = db.Column(db.String(50), nullable=True) # Ej. 'Llegada Tarde', 'Ausencia Justificada'
    fecha_hora_llegada_programada = db.Column(db.DateTime, nullable=True) # Puede ser nullable si no siempre se programa
    fecha_hora_salida_programada = db.Column(db.DateTime, nullable=True) # Puede ser nullable
    fecha_hora_llegada = db.Column(db.DateTime, nullable=True) # Puede ser nullable si aún no ha llegado
    fecha_hora_salida = db.Column(db.DateTime, nullable=True) # Puede ser nullable si aún no ha salido
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    # FK a Users (quién registra)
    id_usuario_registro = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relaciones
    empleado = db.relationship('Empleados', backref='jornadas') # foreign_keys no es necesario
    usuario_reg = db.relationship('Users', backref='jornadas_registradas')


class OrdenProduccion(db.Model):
    __tablename__ = 'tbl_ordenproduccion'
    id_op = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_op = db.Column(db.Integer, nullable=False, unique=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('tbl_clientes.id_cliente'), nullable=True)
    producto = db.Column(db.String(200), nullable=True)
    version = db.Column(db.String(50), nullable=True)
    cotizacion = db.Column(db.String(50), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    cantidad = db.Column(db.Integer, nullable=True)
    medida = db.Column(db.String(50), nullable=True)
    referencia = db.Column(db.String(100), nullable=True)
    odi = db.Column(db.String(50), nullable=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('tbl_empleados.id_empleado'), nullable=True)
    id_supervisor = db.Column(db.Integer, db.ForeignKey('tbl_empleados.id_empleado'), nullable=True)
    fecha = db.Column(db.Date, nullable=True)
    fecha_entrega = db.Column(db.Date, nullable=True)
    descripcion_general = db.Column(db.Text, nullable=True)
    empaque = db.Column(db.String(100), nullable=True)
    materiales = db.Column(db.Text, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    id_usuario_registro = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relaciones con cascade para eliminación automática
    cliente = db.relationship('Clientes', backref='ordenes', lazy=True)
    empleado = db.relationship('Empleados', foreign_keys=[id_empleado], backref='ordenes_empleado', lazy=True)
    supervisor = db.relationship('Empleados', foreign_keys=[id_supervisor], backref='ordenes_supervisor', lazy=True)
    usuario_registro = db.relationship('Users', backref='ordenes_registradas', lazy=True)
    documentos = db.relationship('DocumentosOP', backref='orden', lazy=True, cascade="all, delete-orphan")
    renders = db.relationship('RendersOP', backref='orden', lazy=True, cascade="all, delete-orphan")
    orden_piezas = db.relationship('OrdenPiezas', backref='orden', lazy=True, cascade="all, delete-orphan")

class DocumentosOP(db.Model):
    __tablename__ = 'tbl_documentos_op'
    id_documento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_op = db.Column(db.Integer, db.ForeignKey('tbl_ordenproduccion.id_op', ondelete='CASCADE'), nullable=False)
    documento_path = db.Column(db.String(255), nullable=False)
    documento_nombre_original = db.Column(db.String(255), nullable=False)  # Nuevo campo
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

class RendersOP(db.Model):
    __tablename__ = 'tbl_renders_op'
    id_render = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_op = db.Column(db.Integer, db.ForeignKey('tbl_ordenproduccion.id_op', ondelete='CASCADE'), nullable=False)
    render_path = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

class OrdenPiezas(db.Model):
    __tablename__ = 'tbl_orden_piezas'
    id_orden_pieza = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_op = db.Column(db.Integer, db.ForeignKey('tbl_ordenproduccion.id_op', ondelete='CASCADE'), nullable=False)
    # id_pieza ya no será una FK obligatoria a tbl_piezas si los detalles se guardan aquí.
    # Considerar hacerlo nullable o eliminarlo si tbl_piezas no se usa como maestro para este flujo.
    id_pieza = db.Column(db.Integer, db.ForeignKey('tbl_piezas.id_pieza'), nullable=True) # Renombrado para claridad, y nullable
    nombre_pieza_op = db.Column(db.String(100), nullable=False) # Nuevo campo para el nombre específico de la pieza en esta OP
    cantidad = db.Column(db.Integer, nullable=False) # Hacerlo no nullable si siempre se requiere
    tamano = db.Column(db.String(100), nullable=True)
    montaje = db.Column(db.String(100), nullable=True)
    montaje_tamano = db.Column(db.String(100), nullable=True)
    material = db.Column(db.String(100), nullable=True)
    cantidad_material = db.Column(db.String(100), nullable=True) # Ajustado a String si es más apropiado que Text
    # 'otros_procesos' se manejará creando un registro en tbl_procesos y vinculándolo. Este campo puede eliminarse de OrdenPiezas.
    # otros_procesos_texto = db.Column(db.String(255), nullable=True) # Si se quiere mantener un campo de texto adicional para notas de proceso
    descripcion_pieza = db.Column(db.Text, nullable=True) # Renombrado para claridad (era descripcion_general)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relaciones
    procesos = db.relationship('OrdenPiezasProcesos', backref='orden_pieza', lazy=True, cascade="all, delete-orphan")

class OrdenPiezasProcesos(db.Model):
    __tablename__ = 'tbl_orden_piezas_procesos'
    id_orden_pieza_proceso = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_orden_pieza = db.Column(db.Integer, db.ForeignKey('tbl_orden_piezas.id_orden_pieza', ondelete='CASCADE'), nullable=False)
    id_proceso = db.Column(db.Integer, db.ForeignKey('tbl_procesos.id_proceso'), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)
    
class OrdenPiezasActividades(db.Model):
    __tablename__ = 'tbl_orden_piezas_actividades'
    id_orden_pieza_actividad = db.Column(db.Integer, primary_key=True)
    id_orden_pieza = db.Column(db.Integer, db.ForeignKey('tbl_orden_piezas.id_orden_pieza'), nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('tbl_actividades.id_actividad'), nullable=False)