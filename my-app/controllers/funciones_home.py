# Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename
import uuid  # Módulo de Python para crear un string
import os
from os import remove, path  # Módulos para manejar archivos
from app import app  # Importa la instancia de Flask desde app.py
from conexion.models import db, Operaciones, Empleados, TipoEmpleado, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users  # Importa modelos desde models.py
import datetime
import re
import openpyxl  # Para generar el Excel
from flask import send_file, session, Flask
from conexion.models import db, Empleados, Procesos, Actividades, OrdenProduccion
from sqlalchemy import or_

### Empleados
def procesar_form_empleado(dataForm, foto_perfil):
    # Formateando documento
    documento_sin_puntos = re.sub('[^0-9]+', '', dataForm['documento'])
    documento = int(documento_sin_puntos)

    result_foto_perfil = procesar_imagen_perfil(foto_perfil)
    try:
        empleado = Empleados(
            documento=documento,
            nombre_empleado=dataForm['nombre_empleado'],
            apellido_empleado=dataForm['apellido_empleado'],
            tipo_empleado=dataForm['tipo_empleado'],
            telefono_empleado=dataForm['telefono_empleado'],
            email_empleado=dataForm['email_empleado'],
            cargo=dataForm['cargo'],
            foto_empleado=result_foto_perfil
        )
        db.session.add(empleado)
        db.session.commit()
        return True, "El empleado fue registrado con éxito."
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_empleado: {str(e)}')
        return False, f'Se produjo un error en procesar_form_empleado: {str(e)}'

def procesar_imagen_perfil(foto):
    try:
        # Nombre original del archivo
        filename = secure_filename(foto.filename)
        extension = os.path.splitext(filename)[1]

        # Creando un string de 50 caracteres
        nuevoNameFile = (uuid.uuid4().hex + uuid.uuid4().hex)[:100]
        nombreFile = nuevoNameFile + extension

        # Construir la ruta completa de subida del archivo
        basepath = os.path.abspath(os.path.dirname(__file__))
        upload_dir = os.path.join(basepath, f'../static/fotos_empleados/')

        # Validar si existe la ruta y crearla si no existe
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            # Dando permiso a la carpeta
            os.chmod(upload_dir, 0o755)

        # Construir la ruta completa de subida del archivo
        upload_path = os.path.join(upload_dir, nombreFile)
        foto.save(upload_path)

        return nombreFile

    except Exception as e:
        app.logger.error("Error al procesar archivo:", e)
        return []

def obtener_tipo_empleado():
    try:
        return TipoEmpleado.query.distinct(TipoEmpleado.id_tipo_empleado, TipoEmpleado.tipo_empleado).order_by(TipoEmpleado.id_tipo_empleado.asc()).all()
    except Exception as e:
        app.logger.error(f"Error en la función obtener_tipo_empleado: {e}")
        return None

# Lista de Empleados con paginación
def sql_lista_empleadosBD(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Empleados, TipoEmpleado).outerjoin(TipoEmpleado, Empleados.tipo_empleado == TipoEmpleado.id_tipo_empleado).filter(Empleados.fecha_borrado.is_(None)).order_by(Empleados.id_empleado.desc()).limit(per_page).offset(offset)
        empleadosBD = query.all()
        return [{'id_empleado': e.id_empleado, 'documento': e.documento, 'nombre_empleado': e.nombre_empleado, 'apellido_empleado': e.apellido_empleado, 'foto_empleado': e.foto_empleado, 'cargo': e.cargo, 'tipo_empleado': t.tipo_empleado if t else None} for e, t in empleadosBD]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_empleadosBD: {e}")
        return None
    
    
# Total empleados:
def get_total_empleados():
    try:
        return db.session.query(Empleados).filter(Empleados.fecha_borrado.is_(None)).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_empleados: {e}")
        return 0

# Detalles del Empleado
def sql_detalles_empleadosBD(id_empleado):
    try:
        empleado = db.session.query(Empleados, TipoEmpleado).outerjoin(TipoEmpleado, Empleados.tipo_empleado == TipoEmpleado.id_tipo_empleado).filter(Empleados.id_empleado == id_empleado).first()
        if empleado:
            e, t = empleado
            return {
                'id_empleado': e.id_empleado,
                'documento': e.documento,
                'nombre_empleado': e.nombre_empleado,
                'apellido_empleado': e.apellido_empleado,
                'tipo_empleado': t.tipo_empleado if t else None,
                'telefono_empleado': e.telefono_empleado,
                'email_empleado': e.email_empleado,
                'cargo': e.cargo,
                'foto_empleado': e.foto_empleado,
                'fecha_registro': e.fecha_registro.strftime('%Y-%m-%d %I:%M %p')
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_empleadosBD: {e}")
        return None

# Funcion Empleados Informe (Reporte)
def empleados_reporte():
    try:
        empleados = db.session.query(Empleados).order_by(Empleados.id_empleado.desc()).all()
        return [{
            'id_empleado': e.id_empleado,
            'documento': e.documento,
            'nombre_empleado': e.nombre_empleado,
            'apellido_empleado': e.apellido_empleado,
            'email_empleado': e.email_empleado,
            'telefono_empleado': e.telefono_empleado,
            'cargo': e.cargo,
            'fecha_registro': e.fecha_registro.strftime('%d de %b %Y %I:%M %p'),
            'tipo_empleado': 'Directo' if e.tipo_empleado == 1 else 'Temporal'
        } for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en la función empleados_reporte: {e}")
        return None

def generar_reporte_excel():
    data_empleados = empleados_reporte()
    wb = openpyxl.Workbook()
    hoja = wb.active

    # Agregar la fila de encabezado con los títulos
    cabecera_excel = ("Documento", "Nombre", "Apellido", "Tipo Empleado", "Telefono", "Email", "Profesión", "Fecha de Ingreso")
    hoja.append(cabecera_excel)

    # Formato para números en moneda colombiana y sin decimales
    formato_moneda_colombiana = '#,##0'

    # Agregar los registros a la hoja
    for registro in data_empleados:
        hoja.append((
            registro['documento'],
            registro['nombre_empleado'],
            registro['apellido_empleado'],
            registro['tipo_empleado'],
            registro['telefono_empleado'],
            registro['email_empleado'],
            registro['cargo'],
            registro['fecha_registro']
        ))

        # Itera a través de las filas y aplica el formato a la columna G (Profesión)
        for fila_num in range(2, hoja.max_row + 1):
            columna = 7  # Columna G (Profesión)
            celda = hoja.cell(row=fila_num, column=columna)
            celda.number_format = formato_moneda_colombiana

    fecha_actual = datetime.datetime.now()
    archivo_excel = f"Reporte_empleados_{fecha_actual.strftime('%Y_%m_%d')}.xlsx"
    carpeta_descarga = "../static/downloads-excel"
    ruta_descarga = os.path.join(os.path.dirname(os.path.abspath(__file__)), carpeta_descarga)

    if not os.path.exists(ruta_descarga):
        os.makedirs(ruta_descarga)
        # Dando permisos a la carpeta
        os.chmod(ruta_descarga, 0o755)

    ruta_archivo = os.path.join(ruta_descarga, archivo_excel)
    wb.save(ruta_archivo)

    # Enviar el archivo como respuesta HTTP
    return send_file(ruta_archivo, as_attachment=True)

def buscar_empleado_bd(search):
    try:
        query = db.session.query(Empleados).filter(
            db.or_(
                Empleados.nombre_empleado.ilike(f'%{search}%'),
                Empleados.apellido_empleado.ilike(f'%{search}%')
            ),
            Empleados.fecha_borrado.is_(None)
        ).order_by(Empleados.id_empleado.desc()).all()

        return [{
            'id_empleado': e.id_empleado,
            'documento': e.documento,
            'nombre_empleado': e.nombre_empleado,
            'apellido_empleado': e.apellido_empleado,
            'cargo': e.cargo,
            'tipo_empleado': 'Directo' if e.tipo_empleado == 1 else 'Temporal'
        } for e in query]
    except Exception as e:
        app.logger.error(f"Ocurrió un error en buscar_empleado_bd: {e}")
        return []


def validate_document(documento):
    try:
        empleado = db.session.query(Empleados).filter_by(documento=documento, fecha_borrado=None).first()
        return empleado is not None
    except Exception as e:
        app.logger.error(f"Error en validate_document: {e}")
        return False

def buscar_empleado_unico(id):
    try:
        empleado = db.session.query(Empleados, TipoEmpleado).outerjoin(TipoEmpleado, Empleados.tipo_empleado == TipoEmpleado.id_tipo_empleado).filter(Empleados.id_empleado == id).first()
        if empleado:
            e, t = empleado
            return {
                'id_empleado': e.id_empleado,
                'documento': e.documento,
                'nombre_empleado': e.nombre_empleado,
                'apellido_empleado': e.apellido_empleado,
                'tipo_empleado': t.tipo_empleado if t else None,
                'id_tipo_empleado': t.id_tipo_empleado if t else None,
                'telefono_empleado': e.telefono_empleado,
                'email_empleado': e.email_empleado,
                'cargo': e.cargo,
                'foto_empleado': e.foto_empleado
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_empleado_unico: {e}")
        return None

def procesar_actualizacion_form(data):
    try:
        empleado = db.session.query(Empleados).filter_by(id_empleado=data.form['id_empleado']).first()
        if empleado:
            documento_sin_puntos = re.sub('[^0-9]+', '', data.form['documento'])
            documento = int(documento_sin_puntos)

            empleado.documento = documento
            empleado.nombre_empleado = data.form['nombre_empleado']
            empleado.apellido_empleado = data.form['apellido_empleado']
            empleado.tipo_empleado = data.form['tipo_empleado']
            empleado.telefono_empleado = data.form['telefono_empleado']
            empleado.email_empleado = data.form['email_empleado']
            empleado.cargo = data.form['cargo']

            if 'foto_empleado' in data.files and data.files['foto_empleado']:
                file = data.files['foto_empleado']
                foto_form = procesar_imagen_perfil(file)
                empleado.foto_empleado = foto_form

            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ocurrió un error en procesar_actualizacion_form: {e}")
        return None

# Eliminar Empleado
def eliminar_empleado(id_empleado, foto_empleado):
    try:
        empleado = db.session.query(Empleados).filter_by(id_empleado=id_empleado).first()
        if empleado:
            empleado.fecha_borrado = datetime.datetime.now()
            db.session.commit()

            # Eliminando foto_empleado desde el directorio
            basepath = path.dirname(__file__)
            url_file = path.join(basepath, '../static/fotos_empleados', foto_empleado)

            if path.exists(url_file):
                remove(url_file)  # Borrar foto desde la carpeta

            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_empleado: {e}")
        return 0

### Usuarios
# Lista de Usuarios con paginación
def sql_lista_usuarios_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Users).filter(Users.email_user != 'admin@admin.com').order_by(Users.created_user.desc()).limit(per_page).offset(offset)
        usuarios_bd = query.all()
        return [{
            'id': u.id,
            'name_surname': u.name_surname,
            'email_user': u.email_user,
            'rol': u.rol,
            'created_user': u.created_user
        } for u in usuarios_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_usuarios_bd: {e}")
        return None

# Total Usuarios
def get_total_usuarios():
    try:
        return db.session.query(Users).filter(Users.email_user != 'admin@admin.com').count()
    except Exception as e:
        app.logger.error(f"Error en get_total_usuarios: {e}")
        return 0

# Eliminar usuario
def eliminar_usuario(id):
    try:
        usuario = db.session.query(Users).filter_by(id=id).first()
        if usuario:
            db.session.delete(usuario)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_usuario: {e}")
        return 0

### Procesos
def procesar_form_proceso(dataForm):
    try:
        proceso = Procesos(
            codigo_proceso=dataForm['cod_proceso'],
            nombre_proceso=dataForm['nombre_proceso'],
            descripcion_proceso=dataForm['descripcion_proceso']
        )
        db.session.add(proceso)
        db.session.commit()
        return 1  # Indica éxito (rowcount)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_proceso: {str(e)}')
        return None

# Lista de Procesos con paginación
def sql_lista_procesos_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Procesos).order_by(Procesos.id_proceso.desc()).limit(per_page).offset(offset)
        procesos_bd = query.all()
        return [{
            'id_proceso': p.id_proceso,
            'codigo_proceso': p.codigo_proceso,
            'nombre_proceso': p.nombre_proceso,
            'descripcion_proceso': p.descripcion_proceso,
            'fecha_registro': p.fecha_registro
        } for p in procesos_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_procesos_bd: {e}")
        return None

# Total procesos:
def get_total_procesos():
    try:
        return db.session.query(Procesos).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_procesos: {e}")
        return 0

# Detalles del Proceso
def sql_detalles_procesos_bd(id_proceso):
    try:
        proceso = db.session.query(Procesos).filter_by(codigo_proceso=id_proceso).first()
        if proceso:
            return {
                'id_proceso': proceso.id_proceso,
                'codigo_proceso': proceso.codigo_proceso,
                'nombre_proceso': proceso.nombre_proceso,
                'descripcion_proceso': proceso.descripcion_proceso,
                'fecha_registro': proceso.fecha_registro.strftime('%Y-%m-%d %I:%M %p')
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_procesos_bd: {e}")
        return None

def buscar_proceso_unico(id):
    try:
        proceso = db.session.query(Procesos).filter_by(id_proceso=id).first()
        print(proceso)
        if proceso:
            return {
                'id_proceso': proceso.id_proceso,
                'codigo_proceso': proceso.codigo_proceso,
                'nombre_proceso': proceso.nombre_proceso,
                'descripcion_proceso': proceso.descripcion_proceso,
                'fecha_registro': proceso.fecha_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_proceso_unico: {e}")
        return None

def procesar_actualizar_form(data):
    try:
        proceso = db.session.query(Procesos).filter_by(id_proceso=data.form['id_proceso']).first()
        if proceso:
            proceso.codigo_proceso = data.form['codigo_proceso']
            proceso.nombre_proceso = data.form['nombre_proceso']
            proceso.descripcion_proceso = data.form['descripcion_proceso']
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ocurrió un error en procesar_actualizar_form: {e}")
        return None

# Eliminar Procesos
def eliminar_proceso(id_proceso):
    try:
        proceso = db.session.query(Procesos).filter_by(id_proceso=id_proceso).first()
        if proceso:
            db.session.delete(proceso)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_proceso: {e}")
        return 0

### Clientes
def procesar_form_cliente(dataForm, foto_perfil_cliente):
    # Formateando documento
    documento_sin_puntos = re.sub('[^0-9]+', '', dataForm['documento'])
    documento = int(documento_sin_puntos)

    result_foto_cliente = procesar_imagen_cliente(foto_perfil_cliente)
    try:
        cliente = Clientes(
            tipo_documento=dataForm['tipo_documento'],
            documento=documento,
            nombre_cliente=dataForm['nombre_cliente'],
            telefono_cliente=dataForm['telefono_cliente'],
            email_cliente=dataForm['email_cliente'],
            foto_cliente=result_foto_cliente
        )
        db.session.add(cliente)
        db.session.commit()
        return 1  # Indica éxito (rowcount)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_cliente: {str(e)}')
        return None

def validar_documento_cliente(documento):
    try:
        cliente = db.session.query(Clientes).filter_by(documento=documento, fecha_borrado=None).first()
        return cliente is not None
    except Exception as e:
        app.logger.error(f"Error en validar_documento_cliente: {e}")
        return False

def obtener_tipo_documento():
    try:
        return TipoDocumento.query.distinct(TipoDocumento.id_tipo_documento, TipoDocumento.td_abreviacion).order_by(TipoDocumento.id_tipo_documento.asc()).all()
    except Exception as e:
        app.logger.error(f"Error en la función obtener_tipo_documento: {e}")
        return None

def procesar_imagen_cliente(foto):
    try:
        # Nombre original del archivo
        filename = secure_filename(foto.filename)
        extension = os.path.splitext(filename)[1]

        # Creando un string de 50 caracteres
        nuevoNameFile = (uuid.uuid4().hex + uuid.uuid4().hex)[:100]
        nombreFile = nuevoNameFile + extension

        # Construir la ruta completa de subida del archivo
        basepath = os.path.abspath(os.path.dirname(__file__))
        upload_dir = os.path.join(basepath, f'../static/fotos_clientes/')

        # Validar si existe la ruta y crearla si no existe
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            # Dando permiso a la carpeta
            os.chmod(upload_dir, 0o755)

        # Construir la ruta completa de subida del archivo
        upload_path = os.path.join(upload_dir, nombreFile)
        foto.save(upload_path)

        return nombreFile

    except Exception as e:
        app.logger.error("Error al procesar archivo:", e)
        return []

# Lista de Clientes con paginación
def sql_lista_clientes_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Clientes).filter(Clientes.fecha_borrado.is_(None)).order_by(Clientes.id_cliente.desc()).limit(per_page).offset(offset)
        clientes_bd = query.all()
        return [{
            'id_cliente': c.id_cliente,
            'tipo_documento': c.tipo_documento,
            'documento': c.documento,
            'nombre_cliente': c.nombre_cliente,
            'telefono_cliente': c.telefono_cliente,
            'foto_cliente': c.foto_cliente,
            'email_cliente': c.email_cliente
        } for c in clientes_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_clientes_bd: {e}")
        return None

# Total clientes:
def get_total_clientes():
    try:
        return db.session.query(Clientes).filter(Clientes.fecha_borrado.is_(None)).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_clientes: {e}")
        return 0


# Detalles del Cliente
def sql_detalles_clientes_bd(id_cliente):
    try:
        cliente = db.session.query(Clientes).filter_by(id_cliente=id_cliente).first()
        if cliente:
            return {
                'id_cliente': cliente.id_cliente,
                'tipo_documento': cliente.tipo_documento,
                'documento': cliente.documento,
                'nombre_cliente': cliente.nombre_cliente,
                'telefono_cliente': cliente.telefono_cliente,
                'email_cliente': cliente.email_cliente,
                'foto_cliente': cliente.foto_cliente,
                'fecha_registro': cliente.fecha_registro.strftime('%Y-%m-%d %I:%M %p')
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_clientes_bd: {e}")
        return None

def buscar_cliente_bd(search):
    try:
        query = db.session.query(Clientes).filter(Clientes.nombre_cliente.ilike(f'%{search}%')).order_by(Clientes.id_cliente.desc()).all()
        return [{
            'id_cliente': c.id_cliente,
            'tipo_documento': c.tipo_documento,
            'documento': c.documento,
            'nombre_cliente': c.nombre_cliente,
            'email_cliente': c.email_cliente
        } for c in query]
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_cliente_bd: {e}")
        return []

def buscar_cliente_unico(id):
    try:
        cliente = db.session.query(Clientes).filter_by(id_cliente=id).first()
        if cliente:
            return {
                'id_cliente': cliente.id_cliente,
                'documento': cliente.documento,
                'nombre_cliente': cliente.nombre_cliente,
                'tipo_documento': cliente.tipo_documento,
                'telefono_cliente': cliente.telefono_cliente,
                'email_cliente': cliente.email_cliente,
                'foto_cliente': cliente.foto_cliente
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_cliente_unico: {e}")
        return None

def procesar_actualizacion_cliente(data):
    try:
        cliente = db.session.query(Clientes).filter_by(id_cliente=data.form['id_cliente']).first()
        if cliente:
            documento_sin_puntos = re.sub('[^0-9]+', '', data.form['documento'])
            documento = int(documento_sin_puntos)

            cliente.tipo_documento = data.form['tipo_documento']
            cliente.nombre_cliente = data.form['nombre_cliente']
            cliente.telefono_cliente = data.form['telefono_cliente']
            cliente.email_cliente = data.form['email_cliente']
            cliente.documento = documento

            if 'foto_cliente' in data.files and data.files['foto_cliente']:
                file = data.files['foto_cliente']
                foto_form = procesar_imagen_cliente(file)
                cliente.foto_cliente = foto_form

            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ocurrió un error en procesar_actualizacion_cliente: {e}")
        return None

# Eliminar Cliente
def eliminar_cliente(id_cliente, foto_cliente):
    try:
        cliente = db.session.query(Clientes).filter_by(id_cliente=id_cliente).first()
        if cliente:
            cliente.fecha_borrado = datetime.datetime.now()
            db.session.commit()

            # Eliminando foto_cliente desde el directorio
            basepath = path.dirname(__file__)
            url_file = path.join(basepath, '../static/fotos_clientes', foto_cliente)

            if path.exists(url_file):
                remove(url_file)  # Borrar foto desde la carpeta

            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_cliente: {e}")
        return 0

### Actividades
def procesar_form_actividad(dataForm):
    try:
        actividad = Actividades(
            codigo_actividad=dataForm['cod_actividad'],
            nombre_actividad=dataForm['nombre_actividad'],
            descripcion_actividad=dataForm['descripcion_actividad']
        )
        db.session.add(actividad)
        db.session.commit()
        return 1  # Indica éxito (rowcount)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_actividad: {str(e)}')
        return None

# Lista de Actividades con paginación
def sql_lista_actividades_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Actividades).order_by(Actividades.id_actividad.desc()).limit(per_page).offset(offset)
        actividades_bd = query.all()
        return [{
            'id_actividad': a.id_actividad,
            'codigo_actividad': a.codigo_actividad,
            'nombre_actividad': a.nombre_actividad,
            'descripcion_actividad': a.descripcion_actividad,
            'fecha_registro': a.fecha_registro
        } for a in actividades_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_actividades_bd: {e}")
        return None

# Total actividades:
def get_total_actividades():
    try:
        return db.session.query(Actividades).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_actividades: {e}")
        return 0


# Detalles de la actividad
def sql_detalles_actividades_bd(id_actividad):
    try:
        actividad = db.session.query(Actividades).filter_by(codigo_actividad=id_actividad).first()
        if actividad:
            return {
                'id_actividad': actividad.id_actividad,
                'codigo_actividad': actividad.codigo_actividad,
                'nombre_actividad': actividad.nombre_actividad,
                'descripcion_actividad': actividad.descripcion_actividad,
                'fecha_registro': actividad.fecha_registro.strftime('%Y-%m-%d %I:%M %p')
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_actividades_bd: {e}")
        return None

def buscar_actividad_unico(id):
    try:
        actividad = db.session.query(Actividades).filter_by(id_actividad=id).first()
        if actividad:
            return {
                'id_actividad': actividad.id_actividad,
                'codigo_actividad': actividad.codigo_actividad,
                'nombre_actividad': actividad.nombre_actividad,
                'descripcion_actividad': actividad.descripcion_actividad,
                'fecha_registro': actividad.fecha_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_actividad_unico: {e}")
        return None

def procesar_actualizar_actividad(data):
    try:
        actividad = db.session.query(Actividades).filter_by(id_actividad=data.form['id_actividad']).first()
        if actividad:
            actividad.codigo_actividad = data.form['codigo_actividad']
            actividad.nombre_actividad = data.form['nombre_actividad']
            actividad.descripcion_actividad = data.form['descripcion_actividad']
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ocurrió un error en procesar_actualizar_actividad: {e}")
        return None

# Eliminar Actividades
def eliminar_actividad(id_actividad):
    try:
        actividad = db.session.query(Actividades).filter_by(id_actividad=id_actividad).first()
        if actividad:
            db.session.delete(actividad)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_actividad: {e}")
        return 0

### Operación Diaria
def obtener_id_empleados():
    try:
        empleados = db.session.query(Empleados).filter(Empleados.fecha_borrado.is_(None)).order_by(Empleados.id_empleado.asc()).all()
        return [f"{e.nombre_empleado} {e.apellido_empleado}" for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en la función obtener_id_empleados: {e}")
        return None

def obtener_nombre_empleado(id_empleado):
    try:
        empleado = db.session.query(Empleados).filter_by(id_empleado=id_empleado).first()
        if empleado:
            return {'nombre_empleado': f"{empleado.nombre_empleado} {empleado.apellido_empleado}"}
        return {'nombre_empleado': None}
    except Exception as e:
        app.logger.error(f"Error en obtener_nombre_empleado: {e}")
        return {'nombre_empleado': None}

def obtener_proceso():
    try:
        procesos = db.session.query(Procesos.nombre_proceso).all()
        return [p[0] for p in procesos]
    except Exception as e:
        app.logger.error(f"Error en obtener_proceso: {e}")
        return []

def obtener_actividad():
    try:
        actividades = db.session.query(Actividades.nombre_actividad).all()
        return [a[0] for a in actividades]
    except Exception as e:
        app.logger.error(f"Error en obtener_actividad: {e}")
        return []

def procesar_form_operacion(dataForm):
    try:
        # Obtener y validar los datos del formulario
        nombre_empleado = dataForm.get('nombre_empleado')
        nombre_proceso = dataForm.get('nombre_proceso')
        nombre_actividad = dataForm.get('nombre_actividad')
        cod_op = dataForm.get('cod_op')  # Corregimos el nombre del campo enviado desde el formulario
        cantidad = dataForm.get('cantidad')
        pieza = dataForm.get('pieza')
        novedades = dataForm.get('novedades')
        hora_inicio = dataForm.get('hora_inicio')
        hora_fin = dataForm.get('hora_fin')

        # Validar que todos los campos requeridos estén presentes
        if not all([nombre_empleado, nombre_proceso, nombre_actividad, cod_op, cantidad, hora_inicio, hora_fin]):
            return None  # Indica error si falta algún campo obligatorio

        # Convertir cantidad a entero si es necesario
        try:
            cantidad = int(cantidad)
        except (ValueError, TypeError):
            return None  # Indica error si cantidad no es un número válido

        # Buscar el empleado por nombre completo
        empleado = db.session.query(Empleados).filter(
            db.text("CONCAT(nombre_empleado, ' ', apellido_empleado) = :nombre_completo")
        ).params(nombre_completo=nombre_empleado).first()

        if not empleado:
            return 'No se encontró el empleado con el nombre especificado.'

        # Convertir cod_op a entero si es necesario (asumiendo que es un ID de OrdenProduccion)
        try:
            codigo_op = int(cod_op)
        except (ValueError, TypeError):
            return 'El código de la orden de producción no es válido.'

        # Crear nueva operación
        operacion = Operaciones(
            id_empleado=empleado.id_empleado,
            nombre_empleado=nombre_empleado,
            proceso=nombre_proceso,
            actividad=nombre_actividad,
            codigo_op=codigo_op,  # Usamos el nombre correcto del campo en el modelo
            cantidad=cantidad,
            pieza_realizada=pieza,
            novedad=novedades,
            fecha_hora_inicio=datetime.datetime.strptime(hora_inicio, '%Y-%m-%dT%H:%M'),
            fecha_hora_fin=datetime.datetime.strptime(hora_fin, '%Y-%m-%dT%H:%M'),
            usuario_registro=session.get('name_surname', 'Usuario desconocido')  # Asegura que siempre haya un valor
        )

        # Guardar en la base de datos
        db.session.add(operacion)
        db.session.commit()
        return 1  # Indica éxito (rowcount)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_operacion: {str(e)}')
        return None

# Lista de Operaciones con paginación
def sql_lista_operaciones_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Operaciones).order_by(Operaciones.fecha_registro.desc()).limit(per_page).offset(offset)
        operaciones_bd = query.all()
        return [{
            'id_operacion': o.id_operacion,
            'nombre_empleado': o.nombre_empleado,
            'proceso': o.proceso,
            'actividad': o.actividad,
            'codigo_op': o.codigo_op,
            'cantidad': o.cantidad
        } for o in operaciones_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_operaciones_bd: {e}")
        return None
    
    
def get_total_operaciones():
    try:
        return db.session.query(Operaciones).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_operaciones: {e}")
        return 0

# Detalles de la Operación
def sql_detalles_operaciones_bd(id_operacion):
    try:
        operacion = db.session.query(Operaciones).filter_by(id_operacion=id_operacion).first()
        if operacion:
            return {
                'id_operacion': operacion.id_operacion,
                'id_empleado': operacion.id_empleado,
                'nombre_empleado': operacion.nombre_empleado,
                'proceso': operacion.proceso,
                'actividad': operacion.actividad,
                'codigo_op': operacion.codigo_op,
                'cantidad': operacion.cantidad,
                'pieza_realizada': operacion.pieza_realizada,
                'novedad': operacion.novedad,
                'fecha_hora_inicio': operacion.fecha_hora_inicio,
                'fecha_hora_fin': operacion.fecha_hora_fin,
                'fecha_registro': operacion.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
                'usuario_registro': operacion.usuario_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_operaciones_bd: {e}")
        return None

def buscar_operacion_unico(id):
    try:
        operacion = db.session.query(Operaciones).filter_by(id_operacion=id).first()
        if operacion:
            return {
                'id_operacion': operacion.id_operacion,
                'id_empleado': operacion.id_empleado,
                'nombre_empleado': operacion.nombre_empleado,
                'proceso': operacion.proceso,
                'actividad': operacion.actividad,
                'codigo_op': operacion.codigo_op,
                'cantidad': operacion.cantidad,
                'novedad': operacion.novedad,
                'fecha_hora_inicio': operacion.fecha_hora_inicio,
                'fecha_hora_fin': operacion.fecha_hora_fin,
                'fecha_registro': operacion.fecha_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_operacion_unico: {e}")
        return None

def procesar_actualizacion_operacion(data):
    try:
        operacion = db.session.query(Operaciones).filter_by(id_operacion=data.form['id_operacion']).first()
        if operacion:
            operacion.proceso = data.form['proceso']
            operacion.actividad = data.form['actividad']
            operacion.cantidad = data.form['cantidad']
            operacion.novedad = data.form['novedad']
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ocurrió un error en procesar_actualizar_actividad: {e}")
        return None

# Eliminar Operación
def eliminar_operacion(id_operacion):
    try:
        operacion = db.session.query(Operaciones).filter_by(id_operacion=id_operacion).first()
        if operacion:
            db.session.delete(operacion)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_operacion: {e}")
        return 0

### Orden de Producción
def procesar_form_op(dataForm):
    try:
        orden = OrdenProduccion(
            codigo_op=dataForm['cod_op'],
            nombre_cliente=dataForm['nombre_cliente'],
            producto=dataForm['producto'],
            estado=dataForm['estado'],
            cantidad=dataForm['cantidad'],
            odi=dataForm['odi'],
            empleado=dataForm['vendedor'],
            usuario_registro=session['name_surname']
        )
        db.session.add(orden)
        db.session.commit()
        return 1  # Indica éxito (rowcount)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_op: {str(e)}')
        return None

def validar_cod_op(codigo_op):
    try:
        orden = db.session.query(OrdenProduccion).filter_by(codigo_op=codigo_op, fecha_borrado=None).first()
        return orden is not None
    except Exception as e:
        app.logger.error(f"Error en validar_cod_op: {e}")
        return False

# Lista de Orden de Producción con paginación
def sql_lista_op_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(OrdenProduccion).order_by(OrdenProduccion.codigo_op.desc()).limit(per_page).offset(offset)
        op_bd = query.all()
        return [{
            'id_op': o.id_op,
            'codigo_op': o.codigo_op,
            'nombre_cliente': o.nombre_cliente,
            'producto': o.producto,
            'estado': o.estado,
            'cantidad': o.cantidad,
            'odi': o.odi,
            'empleado': o.empleado,
            'fecha_registro': o.fecha_registro
        } for o in op_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_op_bd: {e}")
        return None
    
def get_total_op():
    try:
        return db.session.query(OrdenProduccion).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_op: {e}")
        return 0

# Detalles del Orden de Producción
def sql_detalles_op_bd(id_op):
    try:
        orden = db.session.query(OrdenProduccion).filter_by(id_op=id_op).first()
        if orden:
            return {
                'id_op': orden.id_op,
                'codigo_op': orden.codigo_op,
                'nombre_cliente': orden.nombre_cliente,
                'producto': orden.producto,
                'estado': orden.estado,
                'cantidad': orden.cantidad,
                'odi': orden.odi,
                'empleado': orden.empleado,
                'fecha_registro': orden.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
                'usuario_registro': orden.usuario_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_op_bd: {e}")
        return None

def buscar_op_unico(id):
    try:
        orden = db.session.query(OrdenProduccion).filter_by(id_op=id).first()
        if orden:
            return {
                'id_op': orden.id_op,
                'codigo_op': orden.codigo_op,
                'nombre_cliente': orden.nombre_cliente,
                'producto': orden.producto,
                'estado': orden.estado,
                'cantidad': orden.cantidad,
                'odi': orden.odi,
                'empleado': orden.empleado,
                'fecha_registro': orden.fecha_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_op_unico: {e}")
        return None

def procesar_actualizar_form_op(data):
    try:
        orden = db.session.query(OrdenProduccion).filter_by(id_op=data.form['id_op']).first()
        if orden:
            orden.codigo_op = data.form['codigo_op']
            orden.nombre_cliente = data.form['nombre_cliente']
            orden.producto = data.form['producto']
            orden.estado = data.form['estado']
            orden.cantidad = data.form['cantidad']
            orden.odi = data.form['odi']
            orden.empleado = data.form['empleado']
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ocurrió un error en procesar_actualizar_form_op: {e}")
        return None

# Eliminar Orden de Producción
def eliminar_op(id_op):
    try:
        orden = db.session.query(OrdenProduccion).filter_by(id_op=id_op).first()
        if orden:
            db.session.delete(orden)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_op: {e}")
        return 0

def obtener_vendedor():
    try:
        empleados = db.session.query(Empleados).filter(Empleados.fecha_borrado.is_(None)).order_by(Empleados.nombre_empleado.asc()).all()
        return [f"{e.nombre_empleado} {e.apellido_empleado}" for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en la función obtener_nombre_empleado: {e}")
        return None

def obtener_op():
    try:
        ops = db.session.query(OrdenProduccion.codigo_op).all()
        return [o[0] for o in ops]
    except Exception as e:
        app.logger.error(f"Error en obtener_op: {e}")
        return []

### Jornada Diaria
def procesar_form_jornada(dataForm):
    try:
        nombre_completo = dataForm['nombre_empleado']
        empleado = db.session.query(Empleados).filter(db.text("CONCAT(nombre_empleado, ' ', apellido_empleado) = :nombre_completo")).params(nombre_completo=nombre_completo).first()
        
        if empleado:
            jornada = Jornadas(
                id_empleado=empleado.id_empleado,
                nombre_empleado=nombre_completo,
                novedad_jornada_programada=dataForm['novedad_jornada_programada'],
                novedad_jornada=dataForm['novedad_jornada'],
                fecha_hora_llegada_programada=dataForm['fecha_hora_llegada_programada'],
                fecha_hora_salida_programada=dataForm['fecha_hora_salida_programada'],
                fecha_hora_llegada=dataForm['fecha_hora_llegada'],
                fecha_hora_salida=dataForm['fecha_hora_salida'],
                usuario_registro=session['name_surname']
            )
            db.session.add(jornada)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        else:
            return 'No se encontró el empleado con el nombre especificado.'
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_jornada: {str(e)}')
        return None

# Lista de Jornadas con paginación
def sql_lista_jornadas_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Jornadas).order_by(Jornadas.fecha_registro.desc()).limit(per_page).offset(offset)
        jornadas_bd = query.all()
        return [{
            'id_jornada': j.id_jornada,
            'id_empleado': j.id_empleado,
            'nombre_empleado': j.nombre_empleado,
            'novedad_jornada_programada': j.novedad_jornada_programada,
            'novedad_jornada': j.novedad_jornada,
            'fecha_hora_llegada_programada': j.fecha_hora_llegada_programada,
            'fecha_hora_salida_programada': j.fecha_hora_salida_programada,
            'fecha_hora_llegada': j.fecha_hora_llegada,
            'fecha_hora_salida': j.fecha_hora_salida,
            'fecha_registro': j.fecha_registro
        } for j in jornadas_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_jornadas_bd: {e}")
        return None


# Total Jornadas:
def get_total_jornadas():
    try:
        return db.session.query(Jornadas).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_jornadas: {e}")
        return 0

# Detalles de la Jornada
def sql_detalles_jornadas_bd(id_jornada):
    try:
        jornada = db.session.query(Jornadas).filter_by(id_jornada=id_jornada).first()
        if jornada:
            return {
                'id_jornada': jornada.id_jornada,
                'id_empleado': jornada.id_empleado,
                'nombre_empleado': jornada.nombre_empleado,
                'novedad_jornada_programada': jornada.novedad_jornada_programada,
                'novedad_jornada': jornada.novedad_jornada,
                'fecha_hora_llegada_programada': jornada.fecha_hora_llegada_programada,
                'fecha_hora_salida_programada': jornada.fecha_hora_salida_programada,
                'fecha_hora_llegada': jornada.fecha_hora_llegada,
                'fecha_hora_salida': jornada.fecha_hora_salida,
                'fecha_registro': jornada.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
                'usuario_registro': jornada.usuario_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_jornadas_bd: {e}")
        return None

def buscar_jornada_unico(id):
    try:
        jornada = db.session.query(Jornadas).filter_by(id_jornada=id).first()
        if jornada:
            return {
                'id_jornada': jornada.id_jornada,
                'id_empleado': jornada.id_empleado,
                'nombre_empleado': jornada.nombre_empleado,
                'novedad_jornada_programada': jornada.novedad_jornada_programada,
                'novedad_jornada': jornada.novedad_jornada,
                'fecha_hora_llegada_programada': jornada.fecha_hora_llegada_programada,
                'fecha_hora_salida_programada': jornada.fecha_hora_salida_programada,
                'fecha_hora_llegada': jornada.fecha_hora_llegada,
                'fecha_hora_salida': jornada.fecha_hora_salida,
                'fecha_registro': jornada.fecha_registro
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_jornada_unico: {e}")
        return None

def procesar_actualizacion_jornada(data):
    try:
        jornada = db.session.query(Jornadas).filter_by(id_jornada=data.form['id_jornada']).first()
        if jornada:
            jornada.id_empleado = data.form['id_empleado']
            jornada.nombre_empleado = data.form['nombre_empleado']
            jornada.novedad_jornada_programada = data.form['novedad_jornada_programada']
            jornada.novedad_jornada = data.form['novedad_jornada']
            jornada.fecha_hora_llegada_programada = data.form['fecha_hora_llegada_programada']
            jornada.fecha_hora_salida_programada = data.form['fecha_hora_salida_programada']
            jornada.fecha_hora_llegada = data.form['fecha_hora_llegada']
            jornada.fecha_hora_salida = data.form['fecha_hora_salida']
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ocurrió un error en procesar_actualizar_jornada: {e}")
        return None

# Eliminar Jornada
def eliminar_jornada(id_jornada):
    try:
        jornada = db.session.query(Jornadas).filter_by(id_jornada=id_jornada).first()
        if jornada:
            db.session.delete(jornada)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_jornada: {e}")
        return 0
    




## Funciones paginados filtros
def get_empleados_paginados(page, per_page, search=None):
    try:
        query = db.session.query(Empleados).order_by(Empleados.id_empleado.desc())
        if search:
            search = f"%{search}%"
            query = query.filter(
                db.or_(
                    Empleados.nombre_empleado.like(search),
                    Empleados.apellido_empleado.like(search),
                    db.text("CONCAT(nombre_empleado, ' ', apellido_empleado) LIKE :search").params(search=search)
                )
            )
        if page and per_page:
            offset = (page - 1) * per_page
            empleados = query.limit(per_page).offset(offset).all()
        else:
            empleados = query.all()  # Devolver todos los registros si no hay paginación
        return [{'nombre_empleado': f"{e.nombre_empleado} {e.apellido_empleado}"} for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en get_empleados_paginados: {e}")
        return []

def get_procesos_paginados(page, per_page, search=None):
    try:
        query = db.session.query(Procesos).order_by(Procesos.id_proceso.desc())
        if search:
            search = f"%{search}%"
            query = query.filter(
                db.or_(
                    Procesos.codigo_proceso.like(search),
                    Procesos.nombre_proceso.like(search)
                )
            )
        if page and per_page:
            offset = (page - 1) * per_page
            procesos = query.limit(per_page).offset(offset).all()
        else:
            procesos = query.all()  # Devolver todos los registros si no hay paginación
        return [{'nombre_proceso': p.nombre_proceso} for p in procesos]
    except Exception as e:
        app.logger.error(f"Error en get_procesos_paginados: {e}")
        return []

def get_actividades_paginados(page, per_page, search=None):
    try:
        query = db.session.query(Actividades).order_by(Actividades.id_actividad.desc())
        if search:
            search = f"%{search}%"
            query = query.filter(
                db.or_(
                    Actividades.codigo_actividad.like(search),
                    Actividades.nombre_actividad.like(search)
                )
            )
        if page and per_page:
            offset = (page - 1) * per_page
            actividades = query.limit(per_page).offset(offset).all()
        else:
            actividades = query.all()  # Devolver todos los registros si no hay paginación
        return [{'nombre_actividad': a.nombre_actividad} for a in actividades]
    except Exception as e:
        app.logger.error(f"Error en get_actividades_paginados: {e}")
        return []

def get_ordenes_paginadas(page, per_page, search=None):
    try:
        query = db.session.query(OrdenProduccion).order_by(OrdenProduccion.codigo_op.desc())
        if search:
            search = f"%{search}%"
            query = query.filter(
                db.or_(
                    OrdenProduccion.codigo_op.cast(db.String).like(search),
                    OrdenProduccion.nombre_cliente.like(search)
                )
            )
        if page and per_page:
            offset = (page - 1) * per_page
            ordenes = query.limit(per_page).offset(offset).all()
        else:
            ordenes = query.all()  # Devolver todos los registros si no hay paginación
        return [{'cod_op': o.codigo_op} for o in ordenes]
    except Exception as e:
        app.logger.error(f"Error en get_ordenes_paginadas: {e}")
        return []