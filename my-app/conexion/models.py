from flask_sqlalchemy import SQLAlchemy
from app import db  # Importa db desde app.py, donde se inicializa
import datetime
from sqlalchemy.sql import func  # Importa func para usar func.now()

# Definición de modelos usando db desde app.py
class Operaciones(db.Model):
    __tablename__ = 'tbl_operaciones'
    id_operacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('tbl_empleados.id_empleado'), nullable=False)
    nombre_empleado = db.Column(db.String(50), nullable=True)  # Opcional según la tabla
    proceso = db.Column(db.String(50), nullable=True)  # Opcional según la tabla
    actividad = db.Column(db.String(50), nullable=True)  # Opcional según la tabla
    codigo_op = db.Column(db.Integer, nullable=True)  # FK a tbl_ordenproduccion.id_op, opcional según la tabla
    cantidad = db.Column(db.Integer, nullable=True)  # Opcional según la tabla
    pieza_realizada = db.Column(db.String(100), nullable=True)
    novedad = db.Column(db.Text, nullable=True)  # Usamos Text para mediumtext
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False)
    fecha_hora_fin = db.Column(db.DateTime, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    usuario_registro = db.Column(db.String(50), nullable=True)  # Opcional según la tabla

    # Relación con Empleados (opcional, para validación)
    empleado = db.relationship('Empleados', backref='operaciones', foreign_keys=[id_empleado])

class Empleados(db.Model):
    __tablename__ = 'tbl_empleados'
    id_empleado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documento = db.Column(db.Integer, nullable=False)
    nombre_empleado = db.Column(db.String(50), nullable=True)
    apellido_empleado = db.Column(db.String(50), nullable=True)
    tipo_empleado = db.Column(db.Integer, db.ForeignKey('tbl_tipo_empleado.id_tipo_empleado'), nullable=True)
    telefono_empleado = db.Column(db.String(50), nullable=True)
    email_empleado = db.Column(db.String(50), nullable=True)
    cargo = db.Column(db.String(50), nullable=True)
    foto_empleado = db.Column(db.Text, nullable=True)  # Usamos Text para mediumtext
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

    # Relación con TipoEmpleado
    tipo = db.relationship('TipoEmpleado', backref='empleados', foreign_keys=[tipo_empleado])

class TipoEmpleado(db.Model):
    __tablename__ = 'tbl_tipo_empleado'
    id_tipo_empleado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_empleado = db.Column(db.String(45), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)

class Procesos(db.Model):
    __tablename__ = 'tbl_procesos'
    id_proceso = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_proceso = db.Column(db.String(50), nullable=False, unique=True)
    nombre_proceso = db.Column(db.String(50), nullable=True)
    descripcion_proceso = db.Column(db.String(200), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)

class Actividades(db.Model):
    __tablename__ = 'tbl_actividades'
    id_actividad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_actividad = db.Column(db.String(50), nullable=False, unique=True)
    nombre_actividad = db.Column(db.String(50), nullable=True)
    descripcion_actividad = db.Column(db.String(200), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)

class Clientes(db.Model):
    __tablename__ = 'tbl_clientes'
    id_cliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_documento = db.Column(db.String(50), nullable=True)  # Ajusta si hay FK a tbl_tipo_documento
    documento = db.Column(db.Integer, nullable=False)
    nombre_cliente = db.Column(db.String(50), nullable=True)
    telefono_cliente = db.Column(db.String(50), nullable=True)
    email_cliente = db.Column(db.String(50), nullable=True)
    foto_cliente = db.Column(db.Text, nullable=True)  # Usamos Text para mediumtext
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

class TipoDocumento(db.Model):
    __tablename__ = 'tbl_tipo_documento'
    id_tipo_documento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    td_abreviacion = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(db.String(45), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)

class OrdenProduccion(db.Model):
    __tablename__ = 'tbl_ordenproduccion'
    id_op = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_op = db.Column(db.Integer, nullable=False)
    nombre_cliente = db.Column(db.String(50), nullable=True)
    producto = db.Column(db.String(200), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    cantidad = db.Column(db.Integer, nullable=True)
    odi = db.Column(db.String(50), nullable=True)
    empleado = db.Column(db.String(50), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    usuario_registro = db.Column(db.String(50), nullable=True)
    fecha_borrado = db.Column(db.DateTime, nullable=True)

class Jornadas(db.Model):
    __tablename__ = 'tbl_jornadas'
    id_jornada = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('tbl_empleados.id_empleado'), nullable=False)
    nombre_empleado = db.Column(db.String(50), nullable=True)
    novedad_jornada_programada = db.Column(db.String(200), nullable=True)
    novedad_jornada = db.Column(db.String(50), nullable=True)
    fecha_hora_llegada_programada = db.Column(db.DateTime, nullable=False)
    fecha_hora_salida_programada = db.Column(db.DateTime, nullable=False)
    fecha_hora_llegada = db.Column(db.DateTime, nullable=False)
    fecha_hora_salida = db.Column(db.DateTime, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=func.now(), nullable=False)
    usuario_registro = db.Column(db.String(50), nullable=True)

    # Relación con Empleados
    empleado = db.relationship('Empleados', backref='jornadas', foreign_keys=[id_empleado])

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name_surname = db.Column(db.String(100), nullable=False)
    email_user = db.Column(db.String(50), nullable=False, unique=True)
    pass_user = db.Column(db.Text, nullable=False)  # Usamos Text para text
    rol = db.Column(db.String(45), nullable=False)
    created_user = db.Column(db.DateTime, default=func.now(), nullable=False)