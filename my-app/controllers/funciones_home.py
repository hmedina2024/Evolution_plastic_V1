# Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename
import uuid  # Módulo de Python para crear un string
import json
import magic
import os
from os import remove, path  # Módulos para manejar archivos
from app import app  # Importa la instancia de Flask desde app.py
# Importa modelos desde models.py
from conexion.models import db, OrdenPiezasProcesos, OrdenPiezas, RendersOP, DocumentosOP, Operaciones, Empleados, Tipo_Empleado, Piezas, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users
import datetime
import pytz
import re
import openpyxl  # Para generar el Excel
from flask import send_file, session, Flask, url_for,jsonify,flash
from conexion.models import db, Empleados, Procesos, Actividades, OrdenProduccion, Empresa, Tipo_Empleado
from sqlalchemy import or_, func, desc, asc
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Message
import smtplib
import ssl
from email.message import EmailMessage
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

magic.Magic(mime=True)

# Define la zona horaria local (ajusta según tu ubicación)
LOCAL_TIMEZONE = pytz.timezone('America/Bogota')


# Empleados
def procesar_form_empleado(dataForm, foto_perfil):
    try:
        # Formateando documento
        documento_sin_puntos = re.sub('[^0-9]+', '', dataForm['documento'])
        documento = int(documento_sin_puntos)

        # Obtener id_empresa y validar que esté presente
        if 'id_empresa' not in dataForm or not dataForm['id_empresa']:
            return False, "Debe seleccionar una empresa."

        id_empresa = int(dataForm['id_empresa'])  # Convertir a entero

        # Obtener id_tipo_empleado como ID directamente del formulario
        if 'tipo_empleado' not in dataForm or not dataForm['tipo_empleado']:
            return False, "Debe seleccionar un tipo de empleado."

        id_tipo_empleado = int(dataForm['tipo_empleado'])  # Convertir a entero

        # Procesar la foto del empleado
        result_foto_perfil = procesar_imagen_perfil(foto_perfil)

        # Crear el nuevo empleado con id_empresa e id_tipo_empleado
        empleado = Empleados(
            documento=documento,
            id_empresa=id_empresa,
            # Usar id_tipo_empleado en lugar de tipo_empleado
            id_tipo_empleado=id_tipo_empleado,
            nombre_empleado=dataForm['nombre_empleado'],
            apellido_empleado=dataForm['apellido_empleado'],
            telefono_empleado=dataForm['telefono_empleado'] if dataForm['telefono_empleado'] else None,
            email_empleado=dataForm['email_empleado'] if dataForm['email_empleado'] else None,
            cargo=dataForm['cargo'] if dataForm['cargo'] else None,
            foto_empleado=result_foto_perfil
        )
        db.session.add(empleado)
        db.session.commit()
        return True, "El empleado fue registrado con éxito."
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f'Se produjo un error en procesar_form_empleado: {str(e)}')
        return False, f'Se produjo un error al registrar el empleado: {str(e)}'


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
        tipos = Tipo_Empleado.query.filter_by(fecha_borrado=None).order_by(
            Tipo_Empleado.id_tipo_empleado.asc()).all()
        app.logger.debug(
            f"Tipos de empleado obtenidos: {[(t.id_tipo_empleado, t.tipo_empleado) for t in tipos]}")
        return tipos
    except Exception as e:
        app.logger.error(f"Error en la función obtener_tipo_empleado: {e}")
        return None

# Lista de Empleados con paginación


def sql_lista_empleadosBD():
    try:
        empleados = db.session.query(Empleados, Empresa).\
            join(Empresa, Empleados.id_empresa == Empresa.id_empresa).\
            filter(Empleados.fecha_borrado.is_(None)).\
            order_by(Empleados.nombre_empleado.asc()).\
            all()
        return empleados
    except Exception as e:
        app.logger.error(f"Error al listar empleados: {str(e)}")
        return []


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
        empleado = db.session.query(Empleados, Empresa).\
            join(Empresa, Empleados.id_empresa == Empresa.id_empresa).\
            filter(Empleados.id_empleado == id_empleado).first()
        if empleado:
            e, empresa = empleado
            return {
                'id_empleado': e.id_empleado,
                'documento': e.documento,
                'nombre_empleado': e.nombre_empleado,
                'apellido_empleado': e.apellido_empleado,
                # Usamos tipo_empresa de Empresa
                'tipo_empleado': empresa.tipo_empresa if empresa else None,
                # Usamos nombre_empresa de Empresa
                'nombre_empresa': empresa.nombre_empresa if empresa else None,
                'telefono_empleado': e.telefono_empleado,
                'email_empleado': e.email_empleado,
                'cargo': e.cargo,
                'foto_empleado': e.foto_empleado,
                'fecha_registro': e.fecha_registro.strftime('%Y-%m-%d %I:%M %p')
            }
        return None
    except Exception as e:
        app.logger.error(
            f"Error en la función sql_detalles_empleadosBD: {str(e)}")
        return None

# Funcion Empleados Informe (Reporte)


def empleados_reporte():
    try:
        empleados = db.session.query(Empleados).order_by(
            Empleados.id_empleado.desc()).all()
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
def generar_codigo_op():
    try:
        # Obtener el último código de OP registrado
        ultima_op = db.session.query(OrdenProduccion).order_by(OrdenProduccion.codigo_op.desc()).first()
        if ultima_op and ultima_op.codigo_op:
            # Si existe un último código, incrementar en 1
            ultimo_codigo = int(ultima_op.codigo_op)
            nuevo_codigo = ultimo_codigo + 1
        else:
            # Si no hay códigos registrados, empezar en 1
            nuevo_codigo = 1
        return str(nuevo_codigo)
    except Exception as e:
        app.logger.error(f"Error al generar código de OP: {e}")
        return None


def generar_reporte_excel():
    data_empleados = empleados_reporte()
    wb = openpyxl.Workbook()
    hoja = wb.active

    # Agregar la fila de encabezado con los títulos
    cabecera_excel = ("Documento", "Nombre", "Apellido", "Tipo Empleado",
                      "Telefono", "Email", "Profesión", "Fecha de Ingreso")
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
    ruta_descarga = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), carpeta_descarga)

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
        empleado = db.session.query(Empleados).filter_by(
            documento=documento, fecha_borrado=None).first()
        return empleado is not None
    except Exception as e:
        app.logger.error(f"Error en validate_document: {e}")
        return False


def buscar_empleado_unico(id):
    try:
        empleado = db.session.query(Empleados, Empresa).\
            join(Empresa, Empleados.id_empresa == Empresa.id_empresa).\
            filter(Empleados.id_empleado == id, Empleados.fecha_borrado.is_(None)).\
            first()
        if empleado:
            e, empresa = empleado
            return {
                'id_empleado': e.id_empleado,
                'documento': e.documento,
                'id_empresa': e.id_empresa,
                'nombre_empresa': empresa.nombre_empresa if empresa else None,
                'nombre_empleado': e.nombre_empleado,
                'apellido_empleado': e.apellido_empleado,
                'tipo_empleado': empresa.tipo_empresa if empresa else None,
                'telefono_empleado': e.telefono_empleado,
                'email_empleado': e.email_empleado,
                'cargo': e.cargo,
                'foto_empleado': e.foto_empleado,
                'fecha_registro': e.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if e.fecha_registro else None
            }
        return None
    except Exception as e:
        app.logger.error(f"Error al buscar empleado: {str(e)}")
        return None


def procesar_actualizacion_form(data):
    try:
        empleado = db.session.query(Empleados).filter_by(
            id_empleado=data.form['id_empleado']).first()
        if empleado:
            # Formatear documento
            documento_sin_puntos = re.sub(
                '[^0-9]+', '', data.form['documento'])
            documento = int(documento_sin_puntos)

            # Obtener id_empresa y validar que esté presente
            if 'id_empresa' not in data.form or not data.form['id_empresa']:
                return False, "Debe seleccionar una empresa."

            id_empresa = int(data.form['id_empresa'])

            # Obtener tipo_empresa y mapearlo a tipo_empleado
            if 'tipo_empleado' not in data.form or not data.form['tipo_empleado']:
                return False, "El tipo de empleado no puede estar vacío."

            tipo_empresa = data.form['tipo_empleado']
            tipo_empleado_map = {
                "Directo": 1,
                "Temporal": 2
                # Agrega más mapeos si es necesario
            }

            if tipo_empresa not in tipo_empleado_map:
                return False, f"Tipo de empresa '{tipo_empresa}' no válido."

            tipo_empleado = tipo_empleado_map[tipo_empresa]

            empleado.documento = documento
            empleado.id_empresa = id_empresa
            empleado.nombre_empleado = data.form['nombre_empleado']
            empleado.apellido_empleado = data.form['apellido_empleado']
            empleado.tipo_empleado = tipo_empleado
            empleado.telefono_empleado = data.form['telefono_empleado'] if data.form['telefono_empleado'] else None
            empleado.email_empleado = data.form['email_empleado'] if data.form['email_empleado'] else None
            empleado.cargo = data.form['cargo'] if data.form['cargo'] else None

            # Actualizar la foto si se proporciona una nueva
            if 'foto_empleado' in data.files and data.files['foto_empleado']:
                file = data.files['foto_empleado']
                foto_form = procesar_imagen_perfil(file)
                empleado.foto_empleado = foto_form

            db.session.commit()
            return True, "Empleado actualizado con éxito."
        return False, "El empleado no existe."
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Ocurrió un error en procesar_actualizacion_form: {str(e)}")
        return False, f"Error al actualizar el empleado: {str(e)}"

# Eliminar Empleado


def eliminar_empleado(id_empleado, foto_empleado):
    try:
        empleado = db.session.query(Empleados).filter_by(
            id_empleado=id_empleado).first()
        if empleado:
            # Usar datetime.now() en lugar de datetime.datetime.now()
            empleado.fecha_borrado = datetime.now()
            db.session.commit()

            # Eliminando foto_empleado desde el directorio
            if foto_empleado:  # Verificar que foto_empleado no sea None o vacío
                basepath = path.dirname(__file__)
                url_file = path.join(
                    basepath, '../static/fotos_empleados', foto_empleado)

                if path.exists(url_file):
                    remove(url_file)  # Borrar foto desde la carpeta

            return 1  # Indica éxito (rowcount)
        return 0  # Empleado no encontrado
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_empleado: {e}")
        return 0

# Usuarios
# Lista de Usuarios con paginación


def sql_lista_usuarios_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Users).filter(Users.email_user != 'admin@admin.com', Users.fecha_borrado.is_(
            None)).order_by(Users.created_user.desc()).limit(per_page).offset(offset)
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
            usuario.fecha_borrado = datetime.now()
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_usuario: {e}")
        return 0

# Procesos


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
        app.logger.error(
            f'Se produjo un error en procesar_form_proceso: {str(e)}')
        return None

# Lista de Procesos con paginación


def sql_lista_procesos_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Procesos).order_by(
            Procesos.id_proceso.desc()).limit(per_page).offset(offset)
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
        proceso = db.session.query(Procesos).filter_by(
            codigo_proceso=id_proceso).first()
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
        proceso = db.session.query(Procesos).filter_by(
            id_proceso=data.form['id_proceso']).first()
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
        proceso = db.session.query(Procesos).filter_by(
            id_proceso=id_proceso).first()
        if proceso:
            db.session.delete(proceso)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_proceso: {e}")
        return 0

# Clientes


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
        app.logger.error(
            f'Se produjo un error en procesar_form_cliente: {str(e)}')
        return None


def validar_documento_cliente(documento):
    try:
        cliente = db.session.query(Clientes).filter_by(
            documento=documento, fecha_borrado=None).first()
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


def buscar_cliente_bd(search='', start=0, length=10):
    try:
        # Consulta base
        query = db.session.query(Clientes)

        # Filtros
        if search:
            # Buscar en múltiples columnas
            query = query.filter(
                db.or_(
                    Clientes.nombre_cliente.ilike(f'%{search}%'),
                    Clientes.documento.ilike(f'%{search}%'),
                    Clientes.email_cliente.ilike(f'%{search}%'),
                    # Para búsqueda exacta de fecha
                    db.func.date(Clientes.fecha_registro) == search
                )
            )

        # Total de registros sin filtrar
        total = db.session.query(Clientes).count()
        app.logger.debug(f"Total de registros sin filtrar: {total}")

        # Total de registros filtrados
        total_filtered = query.count()
        app.logger.debug(f"Total de registros filtrados: {total_filtered}")

        # Aplicar paginación
        clientes = query.order_by(Clientes.id_cliente.desc()).offset(
            start).limit(length).all()
        app.logger.debug(f"Clientes obtenidos: {len(clientes)} registros")

        # Formatear los datos
        data = [{
            'id_cliente': c.id_cliente,
            'tipo_documento': c.tipo_documento,
            'documento': c.documento,
            'nombre_cliente': c.nombre_cliente,
            'email_cliente': c.email_cliente,
            'fecha_registro': c.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
            'foto_cliente': c.foto_cliente,
            'url_editar': url_for('viewEditarCliente', id=c.id_cliente)
        } for c in clientes]
        app.logger.debug(f"Datos formateados: {data}")

        return data, total, total_filtered

    except Exception as e:
        app.logger.error(
            f"Ocurrió un error en def buscar_cliente_bd: {str(e)}")
        return [], 0, 0

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
        cliente = db.session.query(Clientes).filter_by(
            id_cliente=id_cliente).first()
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


def buscar_cliente_bd(search='', search_date='', start=0, length=10, order=[{'column': 0, 'dir': 'desc'}]):
    try:
        query = db.session.query(Clientes)

        # Aplicar filtros
        if search:
            query = query.filter(Clientes.nombre_cliente.ilike(f'%{search}%'))
        if search_date:
            query = query.filter(db.func.date(
                Clientes.fecha_registro) == search_date)

        # Total de registros sin filtrar
        total = db.session.query(Clientes).count()
        app.logger.debug(f"Total de registros sin filtrar: {total}")

        # Total de registros filtrados
        total_filtered = query.count()
        app.logger.debug(f"Total de registros filtrados: {total_filtered}")

        # Mapear columnas de DataTables a campos de la tabla
        column_map = {
            0: Clientes.id_cliente,          # #
            1: Clientes.tipo_documento,      # Tipo Documento
            2: Clientes.documento,           # Documento
            3: Clientes.nombre_cliente,      # Nombre
            4: Clientes.email_cliente,       # Correo
            5: Clientes.fecha_registro       # Fecha Registro
        }

        # Aplicar ordenamiento basado en el parámetro 'order' de DataTables
        if order and len(order) > 0:
            order_col = order[0]['column']
            order_dir = order[0]['dir']
            if order_col in column_map:
                if order_dir == 'asc':
                    query = query.order_by(column_map[order_col].asc())
                else:
                    query = query.order_by(column_map[order_col].desc())

        # Aplicar paginación
        clientes = query.offset(start).limit(length).all()
        app.logger.debug(f"Clientes obtenidos: {len(clientes)} registros")

        # Formatear los datos
        data = [{
            'id_cliente': c.id_cliente,
            'tipo_documento': c.tipo_documento,
            'documento': c.documento,
            'nombre_cliente': c.nombre_cliente,
            'email_cliente': c.email_cliente,
            'fecha_registro': c.fecha_registro.strftime('%Y-%m-%d') if c.fecha_registro else None,
            'foto_cliente': c.foto_cliente,
            'url_editar': url_for('viewEditarCliente', id=c.id_cliente)
        } for c in clientes]
        app.logger.debug(f"Datos formateados: {data}")

        return data, total, total_filtered

    except Exception as e:
        app.logger.error(
            f"Ocurrió un error en def buscar_cliente_bd: {str(e)}")
        return [], 0, 0


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
        cliente = db.session.query(Clientes).filter_by(
            id_cliente=data.form['id_cliente']).first()
        if cliente:
            documento_sin_puntos = re.sub(
                '[^0-9]+', '', data.form['documento'])
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
        app.logger.error(
            f"Ocurrió un error en procesar_actualizacion_cliente: {e}")
        return None

# Eliminar Cliente


def eliminar_cliente(id_cliente, foto_cliente):
    try:
        cliente = db.session.query(Clientes).filter_by(
            id_cliente=id_cliente).first()
        if cliente:
            cliente.fecha_borrado = datetime.now()
            db.session.commit()

            # Eliminando foto_cliente desde el directorio
            basepath = path.dirname(__file__)
            url_file = path.join(
                basepath, '../static/fotos_clientes', foto_cliente)

            if path.exists(url_file):
                remove(url_file)  # Borrar foto desde la carpeta

            return 1  # Indica éxito (rowcount)
        return 0  # Cliente no encontrado
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_cliente: {e}")
        return 0

# Actividades


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
        app.logger.error(
            f'Se produjo un error en procesar_form_actividad: {str(e)}')
        return None

# Lista de Actividades con paginación


def sql_lista_actividades_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Actividades).order_by(
            Actividades.id_actividad.desc()).limit(per_page).offset(offset)
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
        actividad = db.session.query(Actividades).filter_by(
            codigo_actividad=id_actividad).first()
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
        app.logger.error(
            f"Error en la función sql_detalles_actividades_bd: {e}")
        return None


def buscar_actividad_unico(id):
    try:
        actividad = db.session.query(
            Actividades).filter_by(id_actividad=id).first()
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
        app.logger.error(
            f"Ocurrió un error en def buscar_actividad_unico: {e}")
        return None


def procesar_actualizar_actividad(data):
    try:
        actividad = db.session.query(Actividades).filter_by(
            id_actividad=data.form['id_actividad']).first()
        if actividad:
            actividad.codigo_actividad = data.form['codigo_actividad']
            actividad.nombre_actividad = data.form['nombre_actividad']
            actividad.descripcion_actividad = data.form['descripcion_actividad']
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Ocurrió un error en procesar_actualizar_actividad: {e}")
        return None

# Eliminar Actividades


def eliminar_actividad(id_actividad):
    try:
        actividad = db.session.query(Actividades).filter_by(
            id_actividad=id_actividad).first()
        if actividad:
            db.session.delete(actividad)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_actividad: {e}")
        return 0

# Operación Diaria


def obtener_id_empleados():
    try:
        empleados = db.session.query(Empleados).filter(
            Empleados.fecha_borrado.is_(None)).order_by(Empleados.id_empleado.asc()).all()
        return [f"{e.nombre_empleado} {e.apellido_empleado}" for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en la función obtener_id_empleados: {e}")
        return None


def obtener_nombre_empleado(id_empleado):
    try:
        empleado = db.session.query(Empleados).filter_by(
            id_empleado=id_empleado).first()
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
    app.logger.debug(
        "Entrando a procesar_form_operacion con datos: %s", dataForm)
    try:
        # Obtener los campos enviados por el formulario
        id_empleado = dataForm.get('id_empleado')
        id_proceso = dataForm.get('id_proceso')
        id_actividad = dataForm.get('id_actividad')
        id_op = dataForm.get('id_op')
        cantidad = dataForm.get('cantidad')
        pieza_realizada = dataForm.get('pieza_realizada')
        novedad = dataForm.get('novedad')
        fecha_hora_inicio = dataForm.get('fecha_hora_inicio')
        fecha_hora_fin = dataForm.get('fecha_hora_fin')
        action = dataForm.get('action')

        app.logger.debug(f"Valor de action recibido: {action}")

        # Validar campos obligatorios
        if not all([id_empleado, id_proceso, id_actividad, id_op, cantidad, fecha_hora_inicio, fecha_hora_fin]):
            app.logger.error("Faltan campos requeridos en el formulario")
            return "Faltan campos requeridos en el formulario"

        # Convertir cantidad a entero
        try:
            cantidad = int(cantidad)
        except (ValueError, TypeError):
            app.logger.error("Cantidad no es un número válido")
            return "Cantidad no es un número válido"

        # Verificar que el empleado existe
        empleado = db.session.query(Empleados).filter_by(
            id_empleado=id_empleado).first()
        if not empleado:
            app.logger.error(
                "No se encontró el empleado con el ID especificado")
            return "No se encontró el empleado con el ID especificado"

        # Convertir id_op a entero
        try:
            id_op = int(id_op)
        except (ValueError, TypeError):
            app.logger.error(
                "El código de la orden de producción no es válido")
            return "El código de la orden de producción no es válido"

        # Obtener el ID del usuario desde la sesión (ajusta según cómo almacenes el ID)
        # Ajusta 'user_id' al nombre correcto de la clave en tu sesión
        usuario_registro_id = session.get('user_id')
        if not usuario_registro_id:
            app.logger.error("No se encontró el ID del usuario en la sesión")
            return "No se encontró el ID del usuario en la sesión"

        # Crear instancia de Operaciones
        operacion = Operaciones(
            id_empleado=id_empleado,
            id_proceso=id_proceso,
            id_actividad=id_actividad,
            id_op=id_op,
            cantidad=cantidad,
            pieza_realizada=pieza_realizada,
            novedad=novedad,
            fecha_hora_inicio=datetime.strptime(
                fecha_hora_inicio, '%Y-%m-%dT%H:%M'),
            fecha_hora_fin=datetime.strptime(fecha_hora_fin, '%Y-%m-%dT%H:%M'),
            # Usa el campo correcto y el ID del usuario
            id_usuario_registro=usuario_registro_id
        )

        db.session.add(operacion)
        db.session.commit()

        if action == 'save_and_notify':
            app.logger.debug("Entrando al bloque de envío de correo...")
            try:
                admins = db.session.query(Users).filter_by(
                    rol='administrador').all()
                if not admins:
                    app.logger.warning(
                        'No se encontraron usuarios con rol administrador.')
                else:
                    app.logger.debug(
                        f"Se encontraron {len(admins)} administradores: {[admin.email_user for admin in admins]}")
                    email_sender = 'evolutioncontrolweb@gmail.com'
                    email_password = 'qsmr ccyb yzjd gzkm'
                    subject = 'Confirmación: Finalización de Actividad'

                    for admin in admins:
                        email_receiver = admin.email_user
                        body = f"""
                        Se ha registrado una nueva operación diaria:

                        - Empleado: {empleado.nombre_empleado} {empleado.apellido_empleado or ''}
                        - Proceso: {id_proceso}  # Ajusta según el modelo
                        - Actividad: {id_actividad}  # Ajusta según el modelo
                        - Orden de Producción: {id_op}
                        - Cantidad Realizada: {cantidad}
                        - Fecha y Hora Inicio: {fecha_hora_inicio}
                        - Fecha y Hora Fin: {fecha_hora_fin}
                        - Pieza Realizada: {pieza_realizada if pieza_realizada else 'No especificada'}
                        - Novedades: {novedad if novedad else 'Sin novedades'}
                        - Registrado por: {session.get('name_surname', 'Usuario desconocido')}

                        Este es un mensaje automático. Por favor, no respondas a este correo.
                        """

                        em = EmailMessage()
                        em['From'] = email_sender
                        em['To'] = email_receiver
                        em['Subject'] = subject
                        em.set_content(body)

                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                            smtp.login(email_sender, email_password)
                            smtp.sendmail(
                                email_sender, email_receiver, em.as_string())
                            app.logger.info(
                                f'Correo enviado a {email_receiver}')
            except Exception as e:
                app.logger.error(
                    f'Error al enviar correo de notificación: {str(e)}')
        else:
            app.logger.debug(
                "No se solicitó enviar correo (action != 'save_and_notify')")

        return 1
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f'Se produjo un error en procesar_form_operacion: {str(e)}')
        return f"Se produjo un error: {str(e)}"

# Lista de Operaciones con paginación


def sql_lista_operaciones_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Operaciones).order_by(
            Operaciones.fecha_registro.desc()).limit(per_page).offset(offset)
        operaciones_bd = query.all()
        return [{
            'id_operacion': o.id_operacion,
            'nombre_empleado': o.nombre_empleado,
            'proceso': o.proceso,
            'actividad': o.actividad,
            'codigo_op': o.codigo_op,
            'cantidad': o.cantidad,
            'fecha_registro': o.fecha_registro
        } for o in operaciones_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_operaciones_bd: {e}")
        return None


def buscar_operaciones_bd(empleado_filter, fecha_filter, hora_filter, start, length, order_info):
    """
    Busca operaciones en la base de datos con filtros, paginación y ordenamiento
    para DataTables, usando las relaciones del modelo.

    Args:
        empleado_filter (str): Texto para filtrar por nombre de empleado.
        fecha_filter (str): Fecha en formato 'YYYY-MM-DD' para filtrar.
        hora_filter (str): Hora para filtrar (actualmente no implementado).
        start (int): Registro inicial para paginación.
        length (int): Número de registros por página.
        order_info (list): Información de ordenamiento de DataTables. ej [{'column': 1, 'dir': 'desc'}]

    Returns:
        tuple: (list_de_diccionarios_operaciones, total_registros, total_registros_filtrados)
    """
    try:
        # --- Mapeo de columnas para Ordenamiento ---
        # El índice (key) debe coincidir con el índice de la columna en DataTables JS
        # El valor (value) es la columna SQLAlchemy por la cual ordenar
        column_map = {
            # 0: # Índice (no ordenable directamente aquí)
            1: Operaciones.id_operacion,
            2: Empleados.nombre_empleado,    # Ordenar por nombre empleado
            3: Procesos.nombre_proceso,      # Ordenar por nombre proceso
            4: Actividades.nombre_actividad,  # Ordenar por nombre actividad
            5: OrdenProduccion.codigo_op,    # Ordenar por código OP
            6: Operaciones.cantidad,
            7: Operaciones.fecha_registro,
            # 8: # Acciones (no ordenable)
        }

        # --- Query Base con Joins ---
        # Usamos outerjoin por si alguna relación es opcional (nullable=True en el modelo)
        query = db.session.query(
            Operaciones.id_operacion,
            # Usa label para que puedas acceder fácilmente por nombre después
            Empleados.nombre_empleado.label('empleado_nombre'),
            Procesos.nombre_proceso.label('proceso_nombre'),
            Actividades.nombre_actividad.label('actividad_nombre'),
            OrdenProduccion.codigo_op.label('orden_codigo_op'),
            Operaciones.cantidad,
            Operaciones.fecha_registro
            # Añade aquí otros campos de Operaciones si los necesitas devolver en el JSON
            # Operaciones.pieza_realizada.label('pieza_realizada'),
            # Operaciones.novedad.label('novedad'),
            # Operaciones.fecha_hora_inicio.label('fecha_hora_inicio'),
            # Operaciones.fecha_hora_fin.label('fecha_hora_fin'),
            # Users.name_surname.label('usuario_registro_nombre') # Ejemplo si necesitaras el nombre del usuario que registró
        ).select_from(Operaciones) \
            .outerjoin(Empleados, Operaciones.id_empleado == Empleados.id_empleado) \
            .outerjoin(Procesos, Operaciones.id_proceso == Procesos.id_proceso) \
            .outerjoin(Actividades, Operaciones.id_actividad == Actividades.id_actividad) \
            .outerjoin(OrdenProduccion, Operaciones.id_op == OrdenProduccion.id_op)
        # .outerjoin(Users, Operaciones.id_usuario_registro == Users.id) # Ejemplo de join adicional

        # --- Total de Registros (sin filtros) ---
        # Es más eficiente contar solo el ID
        total_records = db.session.query(
            func.count(Operaciones.id_operacion)).scalar()

        # --- Aplicar Filtros ---
        if empleado_filter:
            # Busca de forma insensible a mayúsculas/minúsculas
            query = query.filter(
                Empleados.nombre_empleado.ilike(f'%{empleado_filter}%'))
            # Si quieres buscar también en apellido:
            # query = query.filter(func.concat(Empleados.nombre_empleado, ' ', Empleados.apellido_empleado).ilike(f'%{empleado_filter}%'))

        if fecha_filter:
            try:
                # Compara solo la parte de la fecha
                fecha_obj = datetime.strptime(fecha_filter, '%Y-%m-%d').date()
                query = query.filter(
                    func.date(Operaciones.fecha_registro) == fecha_obj)
            except ValueError:
                app.logger.warning(
                    f"Filtro de fecha inválido ignorado: {fecha_filter}")
                # Decide si quieres devolver un error o simplemente ignorar el filtro inválido

        # TODO: Implementar filtro por hora si es necesario, usando hora_filter
        # if hora_filter:
        #     try:
        #         # Extraer la hora y comparar
        #         hora_obj = datetime.strptime(hora_filter, '%H:%M').time() # Asumiendo formato HH:MM
        #         query = query.filter(func.time(Operaciones.fecha_registro) == hora_obj) # O comparar fecha_hora_inicio/fin
        #     except ValueError:
        #          app.logger.warning(f"Filtro de hora inválido ignorado: {hora_filter}")

        # --- Total de Registros Filtrados ---
        # Cuenta DESPUÉS de aplicar filtros
        filtered_records = query.count()

        # --- Ordenamiento ---
        # Columna índice 1 (ID) por defecto
        order_column_index = order_info[0]['column'] if order_info else 1
        # Dirección 'desc' por defecto
        order_dir = order_info[0]['dir'] if order_info else 'desc'

        order_column = column_map.get(order_column_index)

        if order_column is not None:
            # Necesitamos asegurarnos de que estamos ordenando por la expresión
            # correcta de la consulta, especialmente si usamos labels.
            # Buscamos la expresión en la descripción de columnas de la query
            # que coincide con la columna seleccionada del map.
            effective_order_column = None
            if hasattr(order_column, 'key'):  # Si es una columna con label (como empleado_nombre)
                col_label = order_column.key
                for col_desc in query.column_descriptions:
                    # Comparar la clave de la columna del map con el nombre asignado en la query
                    if col_desc['expr'] is order_column or (hasattr(col_desc['expr'], 'key') and col_desc['expr'].key == col_label):
                        effective_order_column = col_desc['expr']
                        break
            # Si es una columna directa del modelo (como Operaciones.id_operacion)
            else:
                effective_order_column = order_column

            if effective_order_column is not None:
                if order_dir == 'asc':
                    query = query.order_by(asc(effective_order_column))
                else:
                    query = query.order_by(desc(effective_order_column))
            else:
                # Fallback si no se encontró la columna (raro)
                app.logger.warning(
                    f"No se pudo mapear la columna de ordenamiento índice {order_column_index}")
                query = query.order_by(desc(Operaciones.id_operacion))
        else:
            # Orden por defecto si el índice no está en el map
            query = query.order_by(desc(Operaciones.id_operacion))

        # --- Paginación ---
        query = query.offset(start).limit(length)

        # --- Ejecutar y Formatear Resultados ---
        results = query.all()
        data_list = []
        for row in results:
            # Accede a los datos usando los labels definidos en la query
            data_list.append({
                'id_operacion': row.id_operacion,
                'empleado_nombre': row.empleado_nombre,
                'proceso_nombre': row.proceso_nombre or 'N/A',  # Devuelve 'N/A' si es None
                'actividad_nombre': row.actividad_nombre or 'N/A',
                'orden_codigo_op': row.orden_codigo_op or 'N/A',
                'cantidad': row.cantidad,
                'fecha_registro': row.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if row.fecha_registro else '',
                # Añade otros campos si los incluiste en la query y los necesitas
                # 'pieza_realizada': row.pieza_realizada,
                # 'novedad': row.novedad,
                # 'fecha_hora_inicio': row.fecha_hora_inicio.strftime('%Y-%m-%d %H:%M:%S') if row.fecha_hora_inicio else '',
                # 'fecha_hora_fin': row.fecha_hora_fin.strftime('%Y-%m-%d %H:%M:%S') if row.fecha_hora_fin else '',
                # 'usuario_registro_nombre': row.usuario_registro_nombre or '',
            })

        # --- Retornar los 3 valores esperados por la ruta ---
        return data_list, total_records, filtered_records

    except Exception as e:
        # Log completo
        app.logger.error(f"Error en buscar_operaciones_bd: {e}", exc_info=True)
        # Devuelve valores que indican error para que la ruta los maneje
        return [], 0, 0


def get_total_operaciones():
    try:
        return db.session.query(Operaciones).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_operaciones: {e}")
        return 0

# Detalles de la Operación


def sql_detalles_operaciones_bd(id_operacion):
    try:
        operacion = db.session.query(Operaciones).filter_by(
            id_operacion=id_operacion).first(),
        Users.name_surname.label('nombre_usuario_registro')
        if operacion:
            # Obtener datos relacionados
            empleado = operacion.empleado
            proceso = operacion.proceso_rel
            actividad = operacion.actividad_rel
            orden = operacion.orden_produccion
            usuario = Users.name_surname

            return {
                'id_operacion': operacion.id_operacion,
                'id_empleado': operacion.id_empleado,
                'nombre_empleado': f"{empleado.nombre_empleado} {empleado.apellido_empleado or ''}".strip() if empleado else 'Desconocido',
                'proceso': proceso.nombre_proceso if proceso else 'Desconocido',
                'actividad': actividad.nombre_actividad if actividad else 'Desconocido',
                'codigo_op': orden.codigo_op if orden else 'Desconocido',
                'cantidad': operacion.cantidad,
                'pieza_realizada': operacion.pieza_realizada,
                'novedad': operacion.novedad,
                'fecha_hora_inicio': operacion.fecha_hora_inicio.strftime('%Y-%m-%d %H:%M') if operacion.fecha_hora_inicio else 'Sin registro',
                'fecha_hora_fin': operacion.fecha_hora_fin.strftime('%Y-%m-%d %H:%M') if operacion.fecha_hora_fin else 'Sin registro',
                'fecha_registro': operacion.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if operacion.fecha_registro else 'Sin registro',
                'usuario_registro': usuario.name_surname if usuario else 'Desconocido'
            }
        return None
    except Exception as e:
        app.logger.error(
            f"Error en la función sql_detalles_operaciones_bd: {e}")
        return None


def buscar_operacion_unico(id):
    try:
        operacion = db.session.query(
            Operaciones).filter_by(id_operacion=id).first()
        if operacion:
            # Obtener datos relacionados
            empleado = operacion.empleado
            proceso = operacion.proceso_rel
            actividad = operacion.actividad_rel
            orden = operacion.orden_produccion

            return {
                'id_operacion': operacion.id_operacion,
                'id_empleado': operacion.id_empleado,
                'nombre_empleado': f"{empleado.nombre_empleado} {empleado.apellido_empleado or ''}".strip() if empleado else 'Desconocido',
                'proceso': proceso.nombre_proceso if proceso else 'Desconocido',
                'actividad': actividad.nombre_actividad if actividad else 'Desconocido',
                'codigo_op': orden.codigo_op if orden else 'Desconocido',
                'cantidad': operacion.cantidad,
                'pieza': operacion.pieza_realizada,
                'novedad': operacion.novedad,
                'fecha_hora_inicio': operacion.fecha_hora_inicio.strftime('%Y-%m-%d %H:%M') if operacion.fecha_hora_inicio else 'Sin registro',
                'fecha_hora_fin': operacion.fecha_hora_fin.strftime('%Y-%m-%d %H:%M') if operacion.fecha_hora_fin else 'Sin registro',
                'fecha_registro': operacion.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if operacion.fecha_registro else 'Sin registro',
            }
        return None
    except Exception as e:
        app.logger.error(
            f"Ocurrió un error en def buscar_operacion_unico: {e}")
        return None


def buscar_operacion_unico(id):
    try:
        operacion = db.session.query(
            Operaciones).filter_by(id_operacion=id).first()
        if operacion:
            # Obtener datos relacionados
            empleado = operacion.empleado
            proceso = operacion.proceso_rel
            actividad = operacion.actividad_rel
            orden = operacion.orden_produccion

            return {
                'id_operacion': operacion.id_operacion,
                'id_empleado': operacion.id_empleado,
                'nombre_empleado': f"{empleado.nombre_empleado} {empleado.apellido_empleado or ''}".strip() if empleado else 'Desconocido',
                'id_proceso': operacion.id_proceso,
                'proceso': proceso.nombre_proceso if proceso else 'Desconocido',
                'id_actividad': operacion.id_actividad,
                'actividad': actividad.nombre_actividad if actividad else 'Desconocido',
                'id_op': operacion.id_op,
                'codigo_op': orden.codigo_op if orden else 'Desconocido',
                'cantidad': operacion.cantidad,
                'pieza': operacion.pieza_realizada,
                'novedad': operacion.novedad,
                'fecha_hora_inicio': operacion.fecha_hora_inicio.strftime('%Y-%m-%dT%H:%M') if operacion.fecha_hora_inicio else '',
                'fecha_hora_fin': operacion.fecha_hora_fin.strftime('%Y-%m-%dT%H:%M') if operacion.fecha_hora_fin else '',
                'fecha_registro': operacion.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if operacion.fecha_registro else 'Sin registro',
            }
        return None
    except Exception as e:
        app.logger.error(
            f"Ocurrió un error en def buscar_operacion_unico: {e}")
        return None


def procesar_actualizacion_operacion(data):
    try:
        id_operacion = data.form.get('id_operacion')
        operacion = db.session.query(Operaciones).filter_by(
            id_operacion=id_operacion).first()
        if operacion:
            # Obtener y validar IDs, usando valores por defecto si son None
            operacion.id_proceso = int(data.form.get('id_proceso')) if data.form.get(
                'id_proceso') else operacion.id_proceso
            operacion.id_actividad = int(data.form.get('id_actividad')) if data.form.get(
                'id_actividad') else operacion.id_actividad
            operacion.id_op = int(data.form.get('id_op')) if data.form.get(
                'id_op') else operacion.id_op
            operacion.cantidad = int(data.form.get('cantidad')) if data.form.get(
                'cantidad') else operacion.cantidad
            operacion.pieza_realizada = data.form.get('pieza') if data.form.get(
                'pieza') else operacion.pieza_realizada
            operacion.novedad = data.form.get('novedad') if data.form.get(
                'novedad') else operacion.novedad

            # Validar y convertir fechas
            fecha_hora_inicio_str = data.form.get('fecha_hora_inicio')
            fecha_hora_fin_str = data.form.get('fecha_hora_fin')
            if not fecha_hora_inicio_str or not fecha_hora_fin_str:
                raise ValueError("Las fechas no pueden estar vacías")

            operacion.fecha_hora_inicio = datetime.strptime(
                fecha_hora_inicio_str, '%Y-%m-%dT%H:%M')
            operacion.fecha_hora_fin = datetime.strptime(
                fecha_hora_fin_str, '%Y-%m-%dT%H:%M')

            db.session.commit()
            return 1
        return None
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Ocurrió un error en procesar_actualizar_actividad: {e}")
        return None

# Eliminar Operación


def eliminar_operacion(id_operacion):
    try:
        operacion = db.session.query(Operaciones).filter_by(
            id_operacion=id_operacion).first()
        if operacion:
            db.session.delete(operacion)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_operacion: {e}")
        return 0

# Orden de Producción

# Constantes de configuración
ALLOWED_RENDER_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_DOC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/zip'  # Solo permitido para .xlsx mediante la lógica especial
}

def validate_file(file, allowed_extensions):
    """Valida archivo considerando casos especiales como .xlsx"""
    try:
        filename = secure_filename(file.filename)
        if not filename:
            return False, "Nombre de archivo inválido"

        # Obtener extensión
        extension = os.path.splitext(filename)[1][1:].lower()
        
        # Validar extensión permitida
        if not extension or extension not in allowed_extensions:
            return False, f"Extensión .{extension} no permitida"

        # Leer MIME type real
        file.seek(0)
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file.read(2048))  # Lee más bytes para mejor detección
        file.seek(0)

        # Caso especial para .xlsx
        if extension == "xlsx" and detected_mime == "application/zip":
            return True, filename  # Permitir como excepción

        # Validar MIME type
        if detected_mime not in ALLOWED_MIME_TYPES:
            return False, f"Tipo de archivo no permitido: {detected_mime}"

        return True, filename

    except Exception as e:
        return False, f"Error validando archivo: {str(e)}"

def procesar_form_op(dataForm, files):
    """Procesa el formulario de orden de producción con transacciones atómicas"""
    errores = []
    orden = None
    id_usuario_registro = session.get('user_id')

    try:
        # ========== VALIDACIONES INICIALES ==========
        if not id_usuario_registro:
            raise ValueError("Usuario no autenticado")

        # Validar campos requeridos básicos
        required_fields = {
            'cod_op': dataForm.get('cod_op'),
            'id_cliente': dataForm.get('id_cliente'),
            'cantidad': dataForm.get('cantidad'),
            'id_empleado': dataForm.get('id_empleado'),
            'fecha': dataForm.get('fecha'),
            'fecha_entrega': dataForm.get('fecha_entrega'),
            'odi': dataForm.get('odi'),
            'estado': dataForm.get('estado'),
            'descripcion_general': dataForm.get('descripcion_general'),
            'materiales': dataForm.get('materiales')
        }
        
        for field, value in required_fields.items():
            if not value:
                errores.append(f"Campo requerido faltante: {field.replace('_', ' ').title()}")

        # ========== CONVERSIONES Y VALIDACIONES DE TIPOS ==========
        conversions = []
        try:
            conversions.append(('codigo_op', int(dataForm['cod_op'])))
        except (ValueError, KeyError):
            errores.append("Código OP debe ser un número entero válido")            
        try:
            conversions.append(('id_cliente', int(dataForm['id_cliente'])))
        except (ValueError, KeyError):
            errores.append("ID Cliente debe ser un número entero")
        try:
            conversions.append(('cantidad', int(dataForm['cantidad'])))
        except (ValueError, KeyError):
            errores.append("Cantidad debe ser un número entero")   
        try:
            conversions.append(('id_empleado', int(dataForm['id_empleado'])))
        except (ValueError, KeyError):
            errores.append("ID Empleado debe ser un número entero") 
            
        try:
            conversions.append(('id_supervisor', int(dataForm['id_supervisor'])))
        except (ValueError, KeyError):
            errores.append("ID supervisor debe ser un número entero")    

        id_usuario_registro = session.get('user_id')

        # Convertir fechas
        try:
            fecha = datetime.strptime(dataForm['fecha'], '%Y-%m-%d').date()
            fecha_entrega = datetime.strptime(dataForm['fecha_entrega'], '%Y-%m-%d').date()
            if fecha_entrega < fecha:
                errores.append("La fecha de entrega no puede ser anterior a la fecha de registro")
        except (ValueError, KeyError):
            errores.append("Formato de fecha inválido (Use YYYY-MM-DD)")
            
        # Definir las rutas base para los archivos
        basepath = os.path.abspath(os.path.dirname(__file__))
        render_dir = os.path.normpath(os.path.join(basepath, '../static/render_op'))
        documentos_dir = os.path.normpath(os.path.join(basepath, '../static/documentos_op'))

        # Crear las carpetas si no existen
        for upload_dir in [render_dir, documentos_dir]:
            os.makedirs(upload_dir, exist_ok=True)

        # ========== VALIDACIÓN DE ARCHIVOS ==========
        # Validar Render
        if 'render' in files and files['render'].filename:
            render_file = files['render']
            is_valid, msg = validate_file(render_file, ALLOWED_RENDER_EXTENSIONS)
            if not is_valid:
                errores.append(f"Render: {msg}")

        # Validar Documentos
        if 'documentos' in files:
            for doc in files.getlist('documentos'):
                if doc and doc.filename:
                    is_valid, msg = validate_file(doc, ALLOWED_DOC_EXTENSIONS)
                    if not is_valid:
                        errores.append(f"Documento: {msg}")

        # ========== VALIDACIÓN DE PIEZAS DINÁMICAS ==========
        piezas_data = []
        if 'piezas' in dataForm:
            try:
                piezas = json.loads(dataForm['piezas'])
                for idx, pieza in enumerate(piezas, 1):
                    if 'id_pieza' not in pieza:
                        errores.append(f"Pieza {idx}: Falta ID de pieza")
                        continue
                    
                    try:
                        pieza_id = int(pieza['id_pieza'])
                        if not Piezas.query.get(pieza_id):
                            errores.append(f"Pieza {idx}: ID {pieza_id} no existe")
                    except ValueError:
                        errores.append(f"Pieza {idx}: ID inválido")
                    
                    # Validar campos numéricos
                    if not str(pieza.get('cabezoteCantidad', '')).isdigit():
                        errores.append(f"Pieza {idx}: Cantidad inválida")
                    
                    piezas_data.append(pieza)
            except json.JSONDecodeError:
                errores.append("Formato inválido en datos de piezas")

        # ========== MANEJO DE ERRORES TEMPRANOS ==========
        if errores:
            for error in errores:
                flash(error, 'error')
            return None

        # ========== INICIAR TRANSACCIÓN ATÓMICA ==========
        with db.session.begin_nested():
            # ========== CREAR ORDEN ==========
            orden = OrdenProduccion(
                codigo_op=conversions['codigo_op'],
                id_cliente=conversions['id_cliente'],
                version="1",  # Establecer la versión inicial a "1"
                # ... otros campos ...
                id_usuario_registro=id_usuario_registro
            )
            db.session.add(orden)
            db.session.flush()

            # ========== PROCESAR ARCHIVOS ==========
            # Guardar Render
            if 'render' in files and files['render'].filename:
                render_file = files['render']
                filename = secure_filename(render_file.filename)
                unique_name = f"render_{uuid.uuid4().hex}.{filename.split('.')[-1]}"
                render_path = os.path.join(render_dir, unique_name)
                render_file.save(render_path)
                
                orden.render.append(RendersOP(
                    render_path=os.path.join('static/render_op', unique_name)
                ))

            # Guardar Documentos
            if 'documentos' in files:
                for doc in files.getlist('documentos'):
                    if doc and doc.filename:
                        filename = secure_filename(doc.filename)
                        unique_name = f"doc_{uuid.uuid4().hex}.{filename.split('.')[-1]}"
                        doc_path = os.path.join(documentos_dir, unique_name)
                        doc.save(doc_path)
                        
                        orden.documentos.append(DocumentosOP(
                            documento_path=os.path.join('static/documentos_op', unique_name),
                            documento_nombre_original=filename
                        ))

            # ========== PROCESAR PIEZAS ==========
            for pieza in piezas_data:
                nueva_pieza = OrdenPiezas(
                    id_pieza=pieza['id_pieza'],
                    cantidad=pieza.get('cabezoteCantidad'),
                    # ... otros campos ...
                )
                db.session.add(nueva_pieza)
                db.session.flush()

                # Procesos asociados
                if 'id_proceso' in pieza:
                    for proceso_id in pieza['id_proceso']:
                        db.session.add(OrdenPiezasProcesos(
                            id_orden_pieza=nueva_pieza.id_orden_pieza,
                            id_proceso=proceso_id
                        ))

        # ========== CONFIRMAR TRANSACCIÓN PRINCIPAL ==========
        db.session.commit()
        flash("Orden registrada exitosamente", 'success')
        return orden.id_op

    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Error de base de datos: {str(e)}")
        flash("Error al guardar en la base de datos", 'error')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error inesperado: {str(e)}")
        flash("Ocurrió un error inesperado al procesar la orden", 'error')
    finally:
        if 'render_file' in locals():
            render_file.close()
    
    return None

def validar_cod_op(codigo_op):
    try:
        codigo_op = int(codigo_op) if codigo_op else None
        if not codigo_op:
            return False
        orden = db.session.query(OrdenProduccion).filter_by(
            codigo_op=codigo_op, fecha_borrado=None).first()
        return orden is not None
    except Exception as e:
        app.logger.error(f"Error en validar_cod_op: {e}")
        return False

def sql_lista_op_bd(draw=1, start=0, length=10, search_codigo_op=None, search_fecha=None):
    try:
        # Construir la consulta base
        query = db.session.query(OrdenProduccion).filter(
            OrdenProduccion.fecha_borrado.is_(None))

        # Filtrar por código de OP si se proporciona
        if search_codigo_op:
            query = query.filter(
                OrdenProduccion.codigo_op.ilike(f"%{search_codigo_op}%"))

        # Filtrar por fecha de registro si se proporciona
        if search_fecha:
            query = query.filter(db.func.date(
                OrdenProduccion.fecha_registro) == search_fecha)

        # Contar el total de registros (sin paginación, pero con filtros)
        records_filtered = query.count()

        # Aplicar paginación y ordenamiento
        query = query.order_by(OrdenProduccion.codigo_op.desc()).offset(
            start).limit(length)

        # Ejecutar la consulta
        op_bd = query.all()

        # Obtener el total de registros sin filtros
        records_total = db.session.query(OrdenProduccion).filter(
            OrdenProduccion.fecha_borrado.is_(None)).count()

        # Formatear los datos para DataTables
        data = []
        for o in op_bd:
            cliente = o.cliente
            supervisor = o.supervisor
            data.append({
                'id_op': o.id_op,
                'codigo_op': o.codigo_op,
                'nombre_cliente': cliente.nombre_cliente if cliente else 'Desconocido',
                'producto': o.producto,
                'estado': o.estado,
                'cantidad': o.cantidad,
                'fecha_registro': o.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if o.fecha_registro else 'Sin registro',
                'nombre_supervisor': f"{supervisor.nombre_empleado} {supervisor.apellido_empleado or ''}".strip() if supervisor else 'Sin supervisor',
            })

        # Retornar en el formato que espera DataTables
        return {
            "draw": int(draw),
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_op_bd: {e}")
        return {
            "draw": int(draw),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }


def sql_detalles_op_bd(id_op):
    try:
        # Crear alias para las dos instancias de Empleados
        empleado_vendedor = aliased(Empleados)
        empleado_supervisor = aliased(Empleados)

        # Consulta con JOINs para obtener los nombres relacionados
        result = db.session.query(
            OrdenProduccion,
            Clientes.nombre_cliente.label('nombre_cliente'),
            empleado_vendedor.nombre_empleado.label('nombre_empleado_vendedor'),
            db.func.concat(empleado_supervisor.nombre_empleado, ' ',
                            empleado_supervisor.apellido_empleado).label('nombre_supervisor'),
            Users.name_surname.label('nombre_usuario_registro')
        ).outerjoin(
            Clientes, OrdenProduccion.id_cliente == Clientes.id_cliente
        ).outerjoin(
            empleado_vendedor, OrdenProduccion.id_empleado == empleado_vendedor.id_empleado
        ).outerjoin(
            empleado_supervisor, OrdenProduccion.id_supervisor == empleado_supervisor.id_empleado
        ).outerjoin(
            Users, OrdenProduccion.id_usuario_registro == Users.id
        ).filter(
            OrdenProduccion.id_op == id_op,
            OrdenProduccion.fecha_borrado.is_(None)
        ).first()

        if not result:
            return None

        orden, nombre_cliente, nombre_empleado_vendedor, nombre_supervisor, nombre_usuario_registro = result

        # Obtener las piezas asociadas y sus procesos
        piezas = []
        for pieza in orden.orden_piezas:
            # Obtener el nombre de la pieza
            pieza_info = db.session.query(Piezas.nombre_pieza.label('nombre_pieza')).filter(
                Piezas.id_pieza == pieza.id_pieza,
                Piezas.fecha_borrado.is_(None)
            ).first()

            # Obtener los procesos asociados a la pieza
            procesos = db.session.query(
                Procesos.nombre_proceso.label('nombre_proceso')
            ).join(
                OrdenPiezasProcesos, Procesos.id_proceso == OrdenPiezasProcesos.id_proceso
            ).filter(
                OrdenPiezasProcesos.id_orden_pieza == pieza.id_orden_pieza,
                OrdenPiezasProcesos.fecha_borrado.is_(None)
            ).all()

            procesos_nombres = [proceso.nombre_proceso for proceso in procesos]

            piezas.append({
                'id_orden_pieza': pieza.id_orden_pieza,
                'nombre_pieza': pieza_info.nombre_pieza if pieza_info else 'Desconocido',
                'cantidad': pieza.cantidad if pieza.cantidad else 'No especificado',
                'tamano': pieza.tamano if pieza.tamano else 'No especificado',
                'montaje': pieza.montaje if pieza.montaje else 'No especificado',
                'montaje_tamano': pieza.montaje_tamano if pieza.montaje_tamano else 'No especificado',
                'material': pieza.material if pieza.material else 'No especificado',
                'cantidad_material': pieza.cantidad_material if pieza.cantidad_material else 'No especificado',
                'otros_procesos': pieza.otros_procesos if pieza.otros_procesos else 'No especificado',
                'descripcion_general': pieza.descripcion_general if pieza.descripcion_general else 'No especificado',
                'procesos': procesos_nombres if procesos_nombres else ['No especificado']
            })

        # Obtener solo el nombre del archivo para los renders
        renders = [render.render_path.split('/')[-1] for render in orden.renders if render.fecha_borrado is None]
        app.logger.debug(f"Nombres de archivo de renders: {renders}")

        # Depurar las rutas y nombres de los documentos
        documentos = [
            {
                'id_documento': doc.id_documento,
                'documento_path': doc.documento_path,
                'documento_nombre_original': doc.documento_nombre_original
            }
            for doc in orden.documentos if doc.fecha_borrado is None
        ]
        app.logger.debug(f"Documentos: {documentos}")

        # Formatear los datos de la orden
        detalle = {
            'id_op': orden.id_op,
            'codigo_op': orden.codigo_op,
            'id_cliente': orden.id_cliente,
            'nombre_cliente': nombre_cliente if nombre_cliente else 'Desconocido',
            'producto': orden.producto if orden.producto else 'Sin descripción',
            'version': orden.version if orden.version else 'No especificado',
            'cotizacion': orden.cotizacion if orden.cotizacion else 'No especificado',
            'estado': orden.estado if orden.estado else 'Sin estado',
            'cantidad': orden.cantidad if orden.cantidad else 0,
            'medida': orden.medida if orden.medida else 'No especificado',
            'referencia': orden.referencia if orden.referencia else 'No especificado',
            'odi': orden.odi if orden.odi else 'Sin ODI',
            'id_empleado': orden.id_empleado,
            'empleado': nombre_empleado_vendedor if nombre_empleado_vendedor else 'Sin vendedor',
            'id_supervisor': orden.id_supervisor,
            'nombre_supervisor': nombre_supervisor if nombre_supervisor else 'Sin supervisor',
            'fecha': orden.fecha.strftime('%Y-%m-%d') if orden.fecha else 'No especificado',
            'fecha_entrega': orden.fecha_entrega.strftime('%Y-%m-%d') if orden.fecha_entrega else 'No especificado',
            'descripcion_general': orden.descripcion_general if orden.descripcion_general else 'No especificado',
            'empaque': orden.empaque if orden.empaque else 'No especificado',
            'materiales': orden.materiales if orden.materiales else 'No especificado',
            'fecha_registro': orden.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if orden.fecha_registro else 'Sin registro',
            'id_usuario_registro': orden.id_usuario_registro,
            'usuario_registro': nombre_usuario_registro if nombre_usuario_registro else 'Desconocido',
            'fecha_borrado': orden.fecha_borrado,
            # Renders y documentos asociados
            'renders': renders,
            'documentos': documentos,
            'piezas': piezas
        }
        app.logger.debug(f"Detalles de la orden: {detalle}")
        return detalle

    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_op_bd: {str(e)}")
        return None

# Eliminar buscar_op_unico ya que sql_detalles_op_bd lo reemplaza
# def buscar_op_unico(id):  # Comentar o eliminar esta función


# def buscar_op_unico(id):
#     try:
#         # Crear alias para las dos instancias de Empleados
#         empleado_vendedor = aliased(Empleados)
#         empleado_supervisor = aliased(Empleados)

#         # Consulta principal con JOINs para obtener los nombres relacionados
#         result = db.session.query(
#             OrdenProduccion,
#             Clientes.id_cliente.label('id_cliente'),
#             Clientes.nombre_cliente.label('nombre_cliente'),
#             empleado_vendedor.id_empleado.label('id_empleado'),
#             empleado_vendedor.nombre_empleado.label('nombre_empleado_vendedor'),
#             empleado_supervisor.id_empleado.label('id_supervisor'),
#             db.func.concat(empleado_supervisor.nombre_empleado, ' ',
#             empleado_supervisor.apellido_empleado).label('nombre_supervisor'),
#             Users.name_surname.label('nombre_usuario_registro')
#         ).outerjoin(
#             Clientes, OrdenProduccion.id_cliente == Clientes.id_cliente
#         ).outerjoin(
#             empleado_vendedor, OrdenProduccion.id_empleado == empleado_vendedor.id_empleado
#         ).outerjoin(
#             empleado_supervisor, OrdenProduccion.id_supervisor == empleado_supervisor.id_empleado
#         ).outerjoin(
#             Users, OrdenProduccion.id_usuario_registro == Users.id
#         ).filter(
#             OrdenProduccion.id_op == id,
#             OrdenProduccion.fecha_borrado.is_(None)
#         ).first()

#         if not result:
#             return None

#         orden, id_cliente, nombre_cliente, id_empleado, nombre_empleado_vendedor, id_supervisor, nombre_supervisor, nombre_usuario_registro = result

#         # Consulta para renders
#         renders = db.session.query(RendersOP.render_path).filter(
#             RendersOP.id_op == id,
#             RendersOP.fecha_borrado.is_(None)
#         ).all()
#         renders_list = [render.render_path for render in renders]

#         # Consulta para documentos
#         documentos = db.session.query(
#             DocumentosOP.id_documento,
#             DocumentosOP.documento_path,
#             DocumentosOP.documento_nombre_original
#         ).filter(
#             DocumentosOP.id_op == id,
#             DocumentosOP.fecha_borrado.is_(None)
#         ).all()
#         documentos_list = [{
#             'id_documento': doc.id_documento,
#             'documento_path': doc.documento_path,
#             'documento_nombre_original': doc.documento_nombre_original
#         } for doc in documentos]

#         # Consulta para piezas
#         piezas = db.session.query(
#             OrdenPiezas,
#             Piezas.nombre_pieza.label('nombre_pieza')
#         ).join(
#             Piezas, OrdenPiezas.id_pieza == Piezas.id_pieza
#         ).filter(
#             OrdenPiezas.id_op == id,
#             OrdenPiezas.fecha_borrado.is_(None)
#         ).all()

#         piezas_list = []
#         for pieza, nombre_pieza in piezas:
#             # Consulta para procesos asociados a la pieza
#             procesos = db.session.query(
#                 Procesos.nombre_proceso
#             ).join(
#                 OrdenPiezasProcesos, Procesos.id_proceso == OrdenPiezasProcesos.id_proceso
#             ).filter(
#                 OrdenPiezasProcesos.id_orden_pieza == pieza.id_orden_pieza,
#                 OrdenPiezasProcesos.fecha_borrado.is_(None)
#             ).all()
#             procesos_list = [proceso.nombre_proceso for proceso in procesos]

#             piezas_list.append({
#                 'id_orden_pieza': pieza.id_orden_pieza,
#                 'id_pieza': pieza.id_pieza,
#                 'nombre_pieza': nombre_pieza if nombre_pieza else 'Sin nombre',
#                 'cantidad': pieza.cantidad if pieza.cantidad else 0,
#                 'tamano': pieza.tamano if pieza.tamano else '',
#                 'montaje': pieza.montaje if pieza.montaje else '',
#                 'montaje_tamano': pieza.montaje_tamano if pieza.montaje_tamano else '',
#                 'material': pieza.material if pieza.material else '',
#                 'cantidad_material': pieza.cantidad_material if pieza.cantidad_material else '',
#                 'otros_procesos': pieza.otros_procesos if pieza.otros_procesos else '',
#                 'procesos': procesos_list,
#                 'descripcion_general': pieza.descripcion_general if pieza.descripcion_general else ''
#             })

#         return {
#             'id_op': orden.id_op,
#             'codigo_op': orden.codigo_op,
#             'id_cliente': id_cliente if id_cliente else None,
#             'nombre_cliente': nombre_cliente if nombre_cliente else 'Desconocido',
#             'producto': orden.producto if orden.producto else 'Sin descripción',
#             'version': orden.version if orden.version else '',
#             'cotizacion': orden.cotizacion if orden.cotizacion else '',
#             'estado': orden.estado if orden.estado else 'Sin estado',
#             'cantidad': orden.cantidad if orden.cantidad else 0,
#             'medida': orden.medida if orden.medida else '',
#             'referencia': orden.referencia if orden.referencia else '',
#             'odi': orden.odi if orden.odi else 'Sin ODI',
#             'id_empleado': id_empleado if id_empleado else None,
#             'empleado': nombre_empleado_vendedor if nombre_empleado_vendedor else 'Sin vendedor',
#             'id_supervisor': id_supervisor if id_supervisor else None,
#             'nombre_supervisor': nombre_supervisor if nombre_supervisor else 'Sin supervisor',
#             'fecha': orden.fecha.strftime('%Y-%m-%d') if orden.fecha else '',
#             'fecha_entrega': orden.fecha_entrega.strftime('%Y-%m-%d') if orden.fecha_entrega else '',
#             'descripcion_general': orden.descripcion_general if orden.descripcion_general else '',
#             'empaque': orden.empaque if orden.empaque else '',
#             'materiales': orden.materiales if orden.materiales else '',
#             'fecha_registro': orden.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if orden.fecha_registro else 'Sin registro',
#             'usuario_registro': nombre_usuario_registro if nombre_usuario_registro else 'Desconocido',
#             'renders': renders_list,
#             'documentos': documentos_list,
#             'piezas': piezas_list
#         }
#     except Exception as e:
#         app.logger.error(f"Ocurrió un error en def buscar_op_unico: {e}")
#         return None


def procesar_actualizar_form_op(data, files):
    try:
        app.logger.debug(f"Datos recibidos del formulario: {data.form}")
        app.logger.debug(f"Archivos recibidos: {files}")

        # Obtener la orden existente
        id_op = data.form.get('id_op')
        if not id_op:
            app.logger.error("ID de la orden no proporcionado")
            return jsonify({'success': False, 'message': 'ID de la orden no proporcionado'})

        orden = db.session.query(OrdenProduccion).filter_by(id_op=id_op).first()
        if not orden:
            app.logger.error(f"Orden con id_op {id_op} no encontrada")
            return jsonify({'success': False, 'message': 'Orden no encontrada'})

        # Convertir campos numéricos y validar
        codigo_op = int(data.form['cod_op']) if data.form['cod_op'] else orden.codigo_op
        id_cliente = int(data.form['id_cliente']) if data.form['id_cliente'] else orden.id_cliente
        cantidad = int(data.form['cantidad']) if data.form['cantidad'] else orden.cantidad
        id_empleado = int(data.form['id_empleado']) if data.form['id_empleado'] else orden.id_empleado
        id_supervisor = int(data.form['id_supervisor']) if data.form.get('id_supervisor') and data.form['id_supervisor'].strip() else orden.id_supervisor

        # Convertir fechas
        fecha = datetime.strptime(data.form['fecha'], '%Y-%m-%d').date() if data.form['fecha'] else orden.fecha
        fecha_entrega = datetime.strptime(data.form['fecha_entrega'], '%Y-%m-%d').date() if data.form['fecha_entrega'] else orden.fecha_entrega

        # Validar campos requeridos
        required_fields = {
            'codigo_op': codigo_op,
            'id_cliente': id_cliente,
            'cantidad': cantidad,
            'id_empleado': id_empleado,
            'fecha': fecha,
            'fecha_entrega': fecha_entrega,
            'odi': data.form.get('odi'),
            'estado': data.form.get('estado'),
            'descripcion_general': data.form.get('descripcion_general'),
            'materiales': data.form.get('materiales')
        }
        for field_name, field_value in required_fields.items():
            if not field_value:
                app.logger.error(f"Campo requerido faltante: {field_name}")
                return jsonify({'success': False, 'message': f"Campo requerido faltante: {field_name}"})

        # Actualizar el objeto OrdenProduccion
        orden.codigo_op = codigo_op
        orden.id_cliente = id_cliente
        orden.producto = data.form.get('producto') or orden.producto
        # Incrementar la versión
        current_version = orden.version or "0"  # Obtener la versión actual, por defecto "0" si es None o vacío
        try:
            next_version = int(current_version) + 1
            orden.version = str(next_version)
        except ValueError:
            # Si la versión actual no es un número, establecer la próxima versión a "1"
            orden.version = "1"
            app.logger.warning(f"La versión actual de la OP {orden.id_op} no es un número válido: {current_version}. Estableciendo la próxima versión a 1.")

        orden.cotizacion = data.form.get('cotizacion') or orden.cotizacion
        orden.estado = data.form['estado']
        orden.cantidad = cantidad
        orden.medida = data.form.get('medida') or orden.medida
        orden.referencia = data.form.get('referencia') or orden.referencia
        orden.odi = data.form['odi']
        orden.id_empleado = id_empleado
        orden.id_supervisor = id_supervisor
        orden.fecha = fecha
        orden.fecha_entrega = fecha_entrega
        orden.descripcion_general = data.form['descripcion_general']
        orden.empaque = data.form.get('empaque') or orden.empaque
        orden.materiales = data.form['materiales']

        # Procesar eliminación de renders
        if 'delete_renders[]' in data.form and data.form.getlist('delete_renders[]'):
            old_renders = db.session.query(RendersOP).filter_by(id_op=id_op).all()
            for render in old_renders:
                file_path = os.path.join('static', render.render_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(render)
                app.logger.debug(f"Render eliminado: {file_path}")

        # Procesar nuevo render
        if 'render' in files and files['render'].filename:
            render_file = files['render']
            filename = secure_filename(render_file.filename)
            extension = os.path.splitext(filename)[1]
            nuevo_name = (uuid.uuid4().hex + uuid.uuid4().hex)[:100]
            render_filename = f"render_{nuevo_name}{extension}"
            render_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../static/render_op'))
            os.makedirs(render_dir, exist_ok=True)
            render_path = os.path.normpath(os.path.join(render_dir, render_filename))
            render_file.save(render_path)
            render_path_relative = os.path.join('static/render_op', render_filename).replace('\\', '/')
            nuevo_render = RendersOP(id_op=id_op, render_path=render_path_relative)
            db.session.add(nuevo_render)
            app.logger.debug(f"Archivo render guardado en: {render_path} (ruta relativa: {render_path_relative})")

        # Procesar eliminación de documentos
        if 'delete_docs[]' in data.form:
            docs_to_delete = data.form.getlist('delete_docs[]')
            for doc_id in docs_to_delete:
                doc = db.session.query(DocumentosOP).filter_by(id_documento=doc_id).first()
                if doc:
                    file_path = os.path.join('static', doc.documento_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    db.session.delete(doc)
                    app.logger.debug(f"Documento eliminado: {file_path}")

        # Procesar nuevos documentos
        if 'documentos' in files:
            documentos_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../static/documentos_op'))
            os.makedirs(documentos_dir, exist_ok=True)
            for doc in files.getlist('documentos'):
                if doc and doc.filename:
                    filename = secure_filename(doc.filename)
                    extension = os.path.splitext(filename)[1]
                    nuevo_name = (uuid.uuid4().hex + uuid.uuid4().hex)[:100]
                    doc_filename = f"doc_{nuevo_name}{extension}"
                    doc_path = os.path.normpath(os.path.join(documentos_dir, doc_filename))
                    doc.save(doc_path)
                    doc_path_relative = os.path.join('static/documentos_op', doc_filename).replace('\\', '/')
                    nuevo_doc = DocumentosOP(
                        id_op=id_op,
                        documento_path=doc_path_relative,
                        documento_nombre_original=filename
                    )
                    db.session.add(nuevo_doc)
                    app.logger.debug(f"Documento guardado en: {doc_path} (ruta relativa: {doc_path_relative})")

        # Procesar piezas
        piezas_json = data.form.get('piezas')
        if piezas_json:
            piezas = json.loads(piezas_json)
            # Eliminar todas las piezas existentes primero
            db.session.query(OrdenPiezas).filter_by(id_op=id_op).delete()
            for pieza_data in piezas:
                if not pieza_data.get('id_pieza'):
                    app.logger.error(f"Pieza inválida, falta id_pieza: {pieza_data}")
                    continue
                id_pieza = int(pieza_data['id_pieza'])
                orden_pieza = OrdenPiezas(
                    id_op=id_op,
                    id_pieza=id_pieza,
                    cantidad=int(pieza_data['cabezoteCantidad']) if pieza_data.get('cabezoteCantidad') and pieza_data['cabezoteCantidad'].isdigit() else None,
                    tamano=pieza_data.get('cabezoteTamaño'),
                    montaje=pieza_data.get('cabezoteMontaje'),
                    montaje_tamano=pieza_data.get('cabezoteMontajeTamaño'),
                    material=pieza_data.get('cabezoteMaterial'),
                    cantidad_material=pieza_data.get('cabezoteCantidadMaterial'),
                    otros_procesos=pieza_data.get('cabezoteOtrosProcesos'),
                    descripcion_general=pieza_data.get('cabezoteDescGeneral')
                )
                db.session.add(orden_pieza)
                db.session.flush()

                if 'id_proceso' in pieza_data and pieza_data['id_proceso']:
                    for id_proceso in pieza_data['id_proceso']:
                        orden_pieza_proceso = OrdenPiezasProcesos(
                            id_orden_pieza=orden_pieza.id_orden_pieza,
                            id_proceso=int(id_proceso)
                        )
                        db.session.add(orden_pieza_proceso)

        # Confirmar la transacción
        db.session.commit()
        app.logger.debug(f"Orden con id_op {id_op} actualizada correctamente")
        return jsonify({'success': True, 'message': 'Orden actualizada con éxito'})

    except ValueError as ve:
        db.session.rollback()
        app.logger.error(f"Error de conversión en procesar_actualizar_form_op: {str(ve)}")
        return jsonify({'success': False, 'message': str(ve)})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Se produjo un error en procesar_actualizar_form_op: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# Eliminar Orden de Producción


def eliminar_op(id_op):
    try:
        # Buscar la orden
        orden = db.session.query(OrdenProduccion).filter_by(id_op=id_op).first()
        if not orden:
            app.logger.warning(f"No se encontró la orden con id_op: {id_op}")
            return 0

        # Calcular la ruta base para los archivos
        basepath = os.path.abspath(os.path.dirname(__file__))

        # Eliminar archivos de renders asociados
        for render in orden.renders:
            render_full_path = os.path.normpath(os.path.join(basepath, '../', render.render_path))
            if os.path.exists(render_full_path):
                os.remove(render_full_path)
                app.logger.debug(f"Archivo render eliminado: {render_full_path}")
            else:
                app.logger.warning(f"Archivo render no encontrado en: {render_full_path}")

        # Eliminar documentos asociados
        for doc in orden.documentos:
            doc_full_path = os.path.normpath(os.path.join(basepath, '../', doc.documento_path))
            if os.path.exists(doc_full_path):
                os.remove(doc_full_path)
                app.logger.debug(f"Documento eliminado: {doc_full_path}")
            else:
                app.logger.warning(f"Documento no encontrado en: {doc_full_path}")

        # Eliminar la orden (esto también elimina registros relacionados por CASCADE)
        db.session.delete(orden)
        db.session.commit()
        app.logger.debug(f"Orden de producción con id_op {id_op} eliminada correctamente.")
        return 1  # Indica éxito (rowcount)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_op: {e}")
        return 0


def buscar_ordenes_produccion_bd(codigo_op='', fecha='', start=0, length=10, order=None):
    try:
        # Consulta base con JOIN para obtener el nombre del supervisor
        query = db.session.query(
            OrdenProduccion,
            db.func.concat(Empleados.nombre_empleado, ' ',
                           Empleados.apellido_empleado).label('nombre_supervisor')
        ).outerjoin(
            Empleados, OrdenProduccion.id_supervisor == Empleados.id_empleado
        )

        # Filtro por código de orden de producción
        if codigo_op:
            query = query.filter(
                OrdenProduccion.codigo_op.ilike(f'%{codigo_op}%'))

        # Filtro por fecha de registro
        if fecha:
            try:
                # Convertir la fecha del input (YYYY-MM-DD) a un objeto datetime
                fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
                # Filtrar por la parte de la fecha de fecha_registro
                query = query.filter(
                    func.date(OrdenProduccion.fecha_registro) == fecha_dt)
            except ValueError as e:
                app.logger.error(
                    f"Error al parsear la fecha: {fecha}, error: {e}")
                # Si la fecha no es válida, no aplicamos el filtro

        # Total de registros sin filtrar
        total = db.session.query(OrdenProduccion).count()
        app.logger.debug(f"Total de registros sin filtrar: {total}")

        # Total de registros filtrados
        total_filtered = query.count()
        app.logger.debug(f"Total de registros filtrados: {total_filtered}")

        # Mapear índices de columnas a campos del modelo
        column_mapping = {
            0: OrdenProduccion.id_op,        # Columna '#'
            1: OrdenProduccion.codigo_op,    # Columna 'Cod. OP'
            2: OrdenProduccion.nombre_cliente,  # Columna 'Cliente'
            3: OrdenProduccion.producto,     # Columna 'Producto'
            4: OrdenProduccion.cantidad,     # Columna 'Cantidad'
            5: OrdenProduccion.estado,       # Columna 'Estado'
            6: OrdenProduccion.fecha_registro,  # Columna 'Fecha Registro'
            # Columna 'Supervisor' (no ordenable por ahora)
            7: None,
            8: None                          # Columna 'Acción' no es ordenable
        }

        # Aplicar ordenamiento dinámico
        if order:
            for ord in order:
                column_index = ord.get('column', 0)
                direction = ord.get('dir', 'asc')
                column = column_mapping.get(column_index)
                if column:  # Solo ordenar si la columna está mapeada
                    if direction == 'desc':
                        query = query.order_by(column.desc())
                    else:
                        query = query.order_by(column.asc())

        # Aplicar paginación
        results = query.offset(start).limit(length).all()
        app.logger.debug(f"Órdenes obtenidas: {len(results)} registros")

        # Formatear los datos
        data = [{
            'id_op': op.id_op,
            'codigo_op': op.codigo_op,
            'nombre_cliente': op.nombre_cliente,
            'producto': op.producto,
            'cantidad': op.cantidad,
            'estado': op.estado,
            'fecha_registro': op.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
            # Mostrar el nombre del supervisor
            'nombre_supervisor': nombre_supervisor if nombre_supervisor else 'Sin supervisor'
        } for op, nombre_supervisor in results]
        app.logger.debug(f"Datos formateados: {data}")

        return data, total, total_filtered

    except Exception as e:
        app.logger.error(f"Error en buscar_ordenes_produccion_bd: {str(e)}")
        return [], 0, 0


def obtener_vendedor():
    try:
        empleados = db.session.query(Empleados).filter(Empleados.fecha_borrado.is_(
            None)).order_by(Empleados.nombre_empleado.asc()).all()
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

# Jornada Diaria


def procesar_form_jornada(dataForm):
    try:
        id_empleado = dataForm['id_empleado']
        fecha_hora_llegada_programada = dataForm['fecha_hora_llegada_programada']
        fecha_hora_salida_programada = dataForm['fecha_hora_salida_programada']
        novedad_jornada_programada = dataForm['novedad_jornada_programada']
        fecha_hora_llegada = dataForm['fecha_hora_llegada']
        fecha_hora_salida = dataForm['fecha_hora_salida']
        novedad_jornada = dataForm['novedad_jornada']

        jornada = Jornadas(
            id_empleado=id_empleado,
            novedad_jornada_programada=novedad_jornada_programada,
            novedad_jornada=novedad_jornada,
            fecha_hora_llegada_programada=fecha_hora_llegada_programada,
            fecha_hora_salida_programada=fecha_hora_salida_programada,
            fecha_hora_llegada=fecha_hora_llegada,
            fecha_hora_salida=fecha_hora_salida,
            id_usuario_registro=session['user_id']
        )
        db.session.add(jornada)
        db.session.commit()
        return 1  # Indica éxito (rowcount)
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f'Se produjo un error en procesar_form_jornada: {str(e)}')
        return None

# Lista de Jornadas con paginación


def sql_lista_jornadas_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Jornadas, Empleados.nombre_empleado, Empleados.apellido_empleado).join(Empleados, Jornadas.id_empleado == Empleados.id_empleado).order_by(
            Jornadas.fecha_registro.desc()).limit(per_page).offset(offset)
        jornadas_bd = query.all()
        return [{
            'id_jornada': j.Jornadas.id_jornada,
            'id_empleado': j.Jornadas.id_empleado,
            'nombre_empleado': f"{j.nombre_empleado} {j.apellido_empleado or ''}".strip(),
            'novedad_jornada_programada': j.Jornadas.novedad_jornada_programada,
            'novedad_jornada': j.Jornadas.novedad_jornada,
            'fecha_hora_llegada_programada': j.Jornadas.fecha_hora_llegada_programada,
            'fecha_hora_salida_programada': j.Jornadas.fecha_hora_salida_programada,
            'fecha_hora_llegada': j.Jornadas.fecha_hora_llegada,
            'fecha_hora_salida': j.Jornadas.fecha_hora_salida,
            'fecha_registro': j.Jornadas.fecha_registro
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
        jornada = db.session.query(Jornadas).filter_by(
            id_jornada=id_jornada).first()
        if jornada:
            empleado = Empleados.query.get(jornada.id_empleado)
            usuario = Users.query.get(jornada.id_usuario_registro)
            if not empleado:
                raise ValueError(f"No se encontró el empleado con ID: {jornada.id_empleado}")

            return {
                'id_jornada': jornada.id_jornada,
                'id_empleado': jornada.id_empleado,
                'nombre_empleado': f"{empleado.nombre_empleado} {empleado.apellido_empleado or ''}".strip(),
                'novedad_jornada_programada': jornada.novedad_jornada_programada,
                'novedad_jornada': jornada.novedad_jornada,
                'fecha_hora_llegada_programada': jornada.fecha_hora_llegada_programada,
                'fecha_hora_salida_programada': jornada.fecha_hora_salida_programada,
                'fecha_hora_llegada': jornada.fecha_hora_llegada,
                'fecha_hora_salida': jornada.fecha_hora_salida,
                'fecha_registro': jornada.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
                'usuario_registro': usuario.name_surname if usuario else 'Desconocido'
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_jornadas_bd: {e}")
        return None


def buscar_jornada_unico(id):
    try:
        app.logger.debug(f"Buscando jornada con ID: {id}, tipo: {type(id)}")
        jornada = db.session.query(Jornadas).filter_by(id_jornada=id).first()
        app.logger.debug(f"Jornada encontrada: {jornada}")
        if jornada:
            app.logger.debug(f"ID Empleado de la jornada: {jornada.id_empleado}")
            empleado = Empleados.query.get(jornada.id_empleado)
            app.logger.debug(f"Empleado encontrado: {empleado}")
            nombre_completo_empleado = "Desconocido"
            if empleado:
                nombre_completo_empleado = f"{empleado.nombre_empleado} {empleado.apellido_empleado or ''}".strip()
            
            # Convertir datetimes a string si no son None, de lo contrario None o string vacío
            fecha_hora_llegada_programada_str = jornada.fecha_hora_llegada_programada.strftime('%Y-%m-%dT%H:%M') if jornada.fecha_hora_llegada_programada else None
            fecha_hora_salida_programada_str = jornada.fecha_hora_salida_programada.strftime('%Y-%m-%dT%H:%M') if jornada.fecha_hora_salida_programada else None
            fecha_hora_llegada_str = jornada.fecha_hora_llegada.strftime('%Y-%m-%dT%H:%M') if jornada.fecha_hora_llegada else None
            fecha_hora_salida_str = jornada.fecha_hora_salida.strftime('%Y-%m-%dT%H:%M') if jornada.fecha_hora_salida else None
            fecha_registro_str = jornada.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if jornada.fecha_registro else None

            return {
                'id_jornada': jornada.id_jornada,
                'id_empleado': jornada.id_empleado,
                'nombre_empleado': nombre_completo_empleado,
                'novedad_jornada_programada': jornada.novedad_jornada_programada,
                'novedad_jornada': jornada.novedad_jornada,
                'fecha_hora_llegada_programada': fecha_hora_llegada_programada_str,
                'fecha_hora_salida_programada': fecha_hora_salida_programada_str,
                'fecha_hora_llegada': fecha_hora_llegada_str,
                'fecha_hora_salida': fecha_hora_salida_str,
                'fecha_registro': fecha_registro_str
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_jornada_unico: {e}")
        return None


def procesar_actualizacion_jornada(id_jornada, dataForm):
    try:
        jornada = db.session.query(Jornadas).filter_by(id_jornada=id_jornada).first()
        if jornada:
            jornada.id_empleado = dataForm.get('id_empleado')
            
            fh_llegada_prog_str = dataForm.get('fecha_hora_llegada_programada')
            if fh_llegada_prog_str:
                jornada.fecha_hora_llegada_programada = datetime.strptime(fh_llegada_prog_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_llegada_programada = None

            fh_salida_prog_str = dataForm.get('fecha_hora_salida_programada')
            if fh_salida_prog_str:
                jornada.fecha_hora_salida_programada = datetime.strptime(fh_salida_prog_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_salida_programada = None

            fh_llegada_real_str = dataForm.get('fecha_hora_llegada')
            if fh_llegada_real_str:
                jornada.fecha_hora_llegada = datetime.strptime(fh_llegada_real_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_llegada = None

            fh_salida_real_str = dataForm.get('fecha_hora_salida')
            if fh_salida_real_str:
                jornada.fecha_hora_salida = datetime.strptime(fh_salida_real_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_salida = None
                
            jornada.novedad_jornada_programada = dataForm.get('novedad_jornada_programada')
            jornada.novedad_jornada = dataForm.get('novedad_jornada')
            
            # Considera si necesitas actualizar el usuario que modifica el registro
            # jornada.id_usuario_modificacion = session.get('user_id')
            # jornada.fecha_modificacion = datetime.now()

            db.session.commit()
            return True, "Jornada actualizada correctamente."
        return False, "Jornada no encontrada."
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en procesar_actualizacion_jornada: {str(e)}")
        return False, f"Error al actualizar la jornada: {str(e)}"

# Eliminar Jornada


def eliminar_jornada(id_jornada):
    try:
        jornada = db.session.query(Jornadas).filter_by(
            id_jornada=id_jornada).first()
        if jornada:
            db.session.delete(jornada)
            db.session.commit()
            return 1  # Indica éxito (rowcount)
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_jornada: {e}")
        return 0

def get_jornadas_serverside(draw, start, length, search_empleado, search_fecha, order_info):
    """
    Obtiene las jornadas para DataTables con procesamiento del lado del servidor.
    """
    try:
        # Query base uniendo Jornadas y Empleados
        query = db.session.query(Jornadas, Empleados.nombre_empleado, Empleados.apellido_empleado).\
            join(Empleados, Jornadas.id_empleado == Empleados.id_empleado)

        # Conteo total de registros ANTES de cualquier filtro específico de la búsqueda
        # Esto es para 'recordsTotal'
        # Si tienes un filtro general como "fecha_borrado IS NULL" para Jornadas, aplícalo aquí.
        # query_total = db.session.query(func.count(Jornadas.id_jornada))
        # if un filtro general existe: query_total = query_total.filter(...)
        # total_records = query_total.scalar()
        # Por ahora, un conteo simple, ajustar si es necesario.
        total_records = db.session.query(func.count(Jornadas.id_jornada)).scalar()


        # Aplicar filtros de búsqueda
        if search_empleado:
            search_term_empleado = f"%{search_empleado}%"
            query = query.filter(or_(Empleados.nombre_empleado.ilike(search_term_empleado), Empleados.apellido_empleado.ilike(search_term_empleado)))

        if search_fecha:
            try:
                fecha_obj = datetime.strptime(search_fecha, '%Y-%m-%d').date()
                query = query.filter(func.date(Jornadas.fecha_registro) == fecha_obj)
            except ValueError:
                app.logger.warning(f"Formato de fecha inválido para búsqueda: {search_fecha}")
                # Considerar no aplicar el filtro de fecha o devolver un error/lista vacía

        # Conteo de registros DESPUÉS de aplicar los filtros de búsqueda
        # Esto es para 'recordsFiltered'
        filtered_records = query.count()

        # Mapeo de columnas para ordenamiento (el índice debe coincidir con el orden en el frontend)
        column_map = {
            0: Jornadas.id_jornada, # O un campo no visible si la primera col es contador
            1: Empleados.nombre_empleado, # Asumiendo que esta es la columna por la que se ordena
            2: Jornadas.fecha_hora_llegada,
            3: Jornadas.fecha_hora_salida,
            4: Jornadas.novedad_jornada,
        }

        order_column_index = order_info.get('column')
        order_direction = order_info.get('dir', 'asc')
        order_column_name = column_map.get(order_column_index)

        if order_column_name is not None:
            # Si se ordena por nombre_empleado, también considerar apellido para un orden más completo
            if order_column_name == Empleados.nombre_empleado:
                if order_direction == 'desc':
                    query = query.order_by(desc(Empleados.nombre_empleado), desc(Empleados.apellido_empleado))
                else:
                    query = query.order_by(asc(Empleados.nombre_empleado), asc(Empleados.apellido_empleado))
            else:
                if order_direction == 'desc':
                    query = query.order_by(desc(order_column_name))
                else:
                    query = query.order_by(asc(order_column_name))
        else:
            # Orden por defecto si no se especifica o la columna no es válida
            query = query.order_by(desc(Jornadas.fecha_registro))

        # Aplicar paginación
        jornadas_paginadas = query.offset(start).limit(length).all()

        data_list = []
        for jornada_obj, nombre_emp, apellido_emp in jornadas_paginadas:
            data_list.append({
                'id_jornada': jornada_obj.id_jornada,
                'nombre_empleado': f"{nombre_emp} {apellido_emp or ''}".strip(),
                'fecha_hora_llegada': jornada_obj.fecha_hora_llegada.strftime('%Y-%m-%d %I:%M %p') if jornada_obj.fecha_hora_llegada else '-',
                'fecha_hora_salida': jornada_obj.fecha_hora_salida.strftime('%Y-%m-%d %I:%M %p') if jornada_obj.fecha_hora_salida else '-',
                'novedad_jornada': jornada_obj.novedad_jornada if jornada_obj.novedad_jornada else '-'
            })
        
        return data_list, total_records, filtered_records

    except Exception as e:
        app.logger.error(f"Error en get_jornadas_serverside: {str(e)}")
        return [], 0, 0 # Devuelve valores por defecto en caso de error


# Funciones paginados filtros
def get_empleados_paginados(page, per_page, search):
    """
    Obtiene una lista paginada de empleados, opcionalmente filtrada por un término de búsqueda.
    La búsqueda se realiza en nombre_empleado y apellido_empleado.
    """
    try:
        offset = (page - 1) * per_page
        
        # Query base, incluyendo las cargas anticipadas (joinedload)
        # y el filtro para no mostrar empleados con fecha_borrado
        query = db.session.query(Empleados).options(
            db.joinedload(Empleados.empresa),
            # Asegúrate que 'tipo_empleado_ref' esté correctamente definido como una relación 
            # en tu modelo Empleados si quieres usar joinedload con él.
            # Si no, puedes remover la siguiente línea o ajustarla.
            db.joinedload(Empleados.tipo_empleado_ref) 
        ).filter(Empleados.fecha_borrado.is_(None))

        # Aplicar filtro de búsqueda si 'search' no está vacío
        if search and search.strip(): # También verifica que search no sea solo espacios
            search_term = f"%{search.strip()}%" # Preparar el término para LIKE (quita espacios al inicio/fin)
            query = query.filter(
                or_(
                    Empleados.nombre_empleado.ilike(search_term),
                    Empleados.apellido_empleado.ilike(search_term)
                    # Opcional: buscar también por documento si es relevante
                    # Empleados.documento.ilike(search_term) 
                )
            )
        
        # Aplicar orden (más natural para resultados de búsqueda) y paginación
        empleados_bd = query.order_by(
            Empleados.nombre_empleado, 
            Empleados.apellido_empleado
        ).limit(per_page).offset(offset).all()
        
        return empleados_bd
        
    except Exception as e:
        # Usar app.logger si está configurado, sino un print o logging estándar
        # Asegúrate que 'app' esté disponible en este contexto si usas app.logger
        if hasattr(app, 'logger'):
            app.logger.error(f"Error en la función get_empleados_paginados: {e}")
        else:
            print(f"Error en la función get_empleados_paginados: {e}") # Fallback si app.logger no existe
        return None


def get_supervisores_paginados(page, per_page, search=None):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Empleados).options(db.joinedload(Empleados.empresa), db.joinedload(Empleados.tipo_empleado_ref)).filter(
            Empleados.fecha_borrado.is_(None),
            # Filtrar por cargo
            Empleados.cargo.in_(['supervisor', 'supervisora'])
        ).order_by(Empleados.id_empleado.desc())
        if search:
            search = f"%{search}%"
            query = query.filter(
                db.or_(
                    Empleados.nombre_empleado.like(search),
                    Empleados.apellido_empleado.like(search),
                    db.text("CONCAT(nombre_empleado, ' ', apellido_empleado) LIKE :search").params(
                        search=search)
                )
            )
        empleados = query.paginate(page=page, per_page=per_page, error_out=False).items
        return [{'id_empleado': e.id_empleado, 'nombre_empleado': f"{e.nombre_empleado} {e.apellido_empleado}"} for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en get_supervisores_paginados: {e}")
        return []


def get_procesos_paginados(page, per_page, search):
    query = Procesos.query.filter(Procesos.fecha_borrado.is_(None))

    if search:
        search_term = f"%{search}%"
        query = query.filter(Procesos.nombre_proceso.ilike(search_term))

    return query.paginate(page=page, per_page=per_page, error_out=False).items


def get_piezas_paginados(page, per_page, search):
    query = Piezas.query.filter(Piezas.fecha_borrado.is_(None))

    if search:
        search_term = f"%{search}%"
        query = query.filter(Piezas.nombre_proceso.ilike(search_term))

    return query.paginate(page=page, per_page=per_page, error_out=False).items


def get_actividades_paginados(page, per_page, search):
    query = Actividades.query.filter(Actividades.fecha_borrado.is_(None))

    if search:
        search_term = f"%{search}%"
        query = query.filter(Actividades.nombre_actividad.ilike(search_term))

    return query.paginate(page=page, per_page=per_page, error_out=False).items


def get_ordenes_paginadas(page, per_page, search):
    query = OrdenProduccion.query.filter(
        OrdenProduccion.fecha_borrado.is_(None),  # Excluye órdenes eliminadas
        (OrdenProduccion.estado != 'TER') | (
            OrdenProduccion.estado.is_(None))  # Excluye "TER" y maneja NULL
    ).order_by(desc(OrdenProduccion.id_op))  # Ordena por id_op descendente

    if search:
        search_term = f"%{search}%"
        query = query.join(Clientes, isouter=True).filter(
            db.or_(
                OrdenProduccion.codigo_op.ilike(search_term),
                Clientes.nombre_cliente.ilike(search_term)
            )
        )

    # Depuración para verificar la consulta
    app.logger.debug(f"Query generada: {query}")
    return query.paginate(page=page, per_page=per_page, error_out=False).items


def get_clientes_paginados(page=1, per_page=10, search=''):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Clientes).filter(
            Clientes.fecha_borrado.is_(None))

        # Filtrar por búsqueda si existe
        if search:
            query = query.filter(
                Clientes.nombre_cliente.ilike(f'%{search}%')
            )

        # Paginación
        total = query.count()
        clientes = query.offset(offset).limit(per_page).all()

        # Formatear los resultados
        return [{
            'id_cliente': c.id_cliente,
            'nombre_cliente': c.nombre_cliente
        } for c in clientes]
    except Exception as e:
        app.logger.error(f"Error en get_clientes_paginados: {e}")
        return []


# EMPRESAS

def procesar_form_empresa(dataForm):
    try:
        # Obtener y validar los datos del formulario
        nit = dataForm.get('nit')
        nombre_empresa = dataForm.get('nombre_empresa')
        tipo_empresa = dataForm.get('tipo_empresa')
        direccion = dataForm.get('direccion')
        telefono = dataForm.get('telefono')
        email = dataForm.get('email')

        # Validar campos requeridos
        if not all([nit, nombre_empresa, tipo_empresa]):
            return None  # Indica error si falta algún campo obligatorio

        # Validar que el NIT no exista
        if db.session.query(Empresa).filter_by(nit=nit, fecha_borrado=None).first():
            return 'El NIT ya está registrado.'

        # Validar tipo_empresa
        if tipo_empresa not in ['Directo', 'Temporal']:
            return 'El tipo de empresa no es válido.'

        # Crear nueva empresa
        empresa = Empresa(
            nit=nit,
            nombre_empresa=nombre_empresa,
            tipo_empresa=tipo_empresa,
            direccion=direccion,
            telefono=telefono,
            email=email,
            usuario_registro=session.get(
                'name_surname', 'Usuario desconocido'),
            fecha_registro=datetime.now()
        )

        # Guardar en la base de datos
        db.session.add(empresa)
        db.session.commit()
        return 1  # Indica éxito

    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f'Se produjo un error en procesar_form_empresa: {str(e)}')
        return None


def sql_lista_empresasBD(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        # Obtener las empresas paginadas
        empresas = (db.session.query(Empresa)
                    .filter(Empresa.fecha_borrado.is_(None))
                    .order_by(Empresa.id_empresa.desc())
                    .limit(per_page)
                    .offset(offset)
                    .all())

        # Obtener el total de empresas
        total = db.session.query(Empresa).filter(
            Empresa.fecha_borrado.is_(None)).count()

        # Devolver una tupla con los registros y el total
        return (empresas, total)
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_empresasBD: {str(e)}")
        return None


def sql_detalles_empresaBD(id_empresa):
    try:
        empresa = db.session.query(Empresa).filter_by(
            id_empresa=id_empresa, fecha_borrado=None).first()
        if empresa:
            return empresa
        return None
    except Exception as e:
        app.logger.error(
            f"Error en la función sql_detalles_empresaBD: {str(e)}")
        return None


def buscar_empresa_unica(id_empresa):
    try:
        empresa = db.session.query(Empresa).filter_by(
            id_empresa=id_empresa, fecha_borrado=None).first()
        if empresa:
            return empresa
        return None
    except Exception as e:
        app.logger.error(f"Error en la función buscar_empresa_unica: {str(e)}")
        return None


def eliminar_empresa(id_empresa):
    try:
        empresa = db.session.query(Empresa).filter_by(
            id_empresa=id_empresa, fecha_borrado=None).first()
        if empresa:
            empresa.fecha_borrado = datetime.now()
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en la función eliminar_empresa: {str(e)}")
        return False


def procesar_actualizar_empresa(request):
    try:
        id_empresa = request.form.get('id_empresa')
        nit = request.form.get('nit')
        nombre_empresa = request.form.get('nombre_empresa')
        tipo_empresa = request.form.get('tipo_empresa')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        email = request.form.get('email')

        # Validar campos requeridos
        if not all([id_empresa, nit, nombre_empresa, tipo_empresa]):
            return "Todos los campos requeridos deben estar completos."

        # Buscar la empresa
        empresa = db.session.query(Empresa).filter_by(
            id_empresa=id_empresa, fecha_borrado=None).first()
        if not empresa:
            return "La empresa no existe."

        # Actualizar los datos
        empresa.nit = nit
        empresa.nombre_empresa = nombre_empresa
        empresa.tipo_empresa = tipo_empresa
        empresa.direccion = direccion if direccion else None
        empresa.telefono = telefono if telefono else None
        empresa.email = email if email else None
        empresa.fecha_modificacion = datetime.now()
        # Asumiendo que el usuario está en la sesión
        empresa.usuario_modificacion = session.get('usuario')

        db.session.commit()
        return 1  # Éxito
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al actualizar la empresa: {str(e)}")
        return f"Error al actualizar la empresa: {str(e)}"


def buscando_empresas(draw, start, length, search_value, order_column, order_direction, filter_empresa):
    try:
        # Obtener el total de registros sin filtrar
        total_records = db.session.query(func.count(Empresa.id_empresa)).filter(
            Empresa.fecha_borrado.is_(None)).scalar()

        # Construir la consulta base
        query = db.session.query(Empresa).filter(
            Empresa.fecha_borrado.is_(None))

        # Aplicar el filtro personalizado por empresa (nombre_empresa o nit)
        if filter_empresa:
            filter_empresa = f"%{filter_empresa}%"
            query = query.filter(
                (Empresa.nit.ilike(filter_empresa)) |
                (Empresa.nombre_empresa.ilike(filter_empresa))
            )

        # Obtener el total de registros filtrados
        filtered_records = query.count()

        # Aplicar ordenamiento
        order_columns = {
            1: Empresa.nit,
            2: Empresa.nombre_empresa,
            3: Empresa.tipo_empresa,
            4: Empresa.telefono,
            5: Empresa.email
        }
        if order_column in order_columns:
            column = order_columns[order_column]
            if order_direction == "desc":
                column = column.desc()
            query = query.order_by(column)

        # Aplicar paginación
        query = query.offset(start).limit(length)

        # Obtener los registros
        empresas = query.all()

        # Formatear los datos para DataTables
        data = []
        for empresa in empresas:
            data.append({
                "id_empresa": empresa.id_empresa,
                "nit": empresa.nit,
                "nombre_empresa": empresa.nombre_empresa,
                "tipo_empresa": empresa.tipo_empresa,
                "telefono": empresa.telefono if empresa.telefono else "N/A",
                "email": empresa.email if empresa.email else "N/A"
            })

        return {
            "draw": int(draw),
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data,
            "fin": 1
        }
    except Exception as e:
        app.logger.error(f"Error en la función buscando_empresas: {str(e)}")
        return {
            "draw": int(draw),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "fin": 0,
            "error": str(e)
        }


def get_empresas_paginadas(page, per_page, search, id=None):
    try:
        query = Empresa.query.filter(Empresa.fecha_borrado.is_(None))
        if id:
            query = query.filter(Empresa.id_empresa == id)
        if search:
            search = f"%{search}%"
            query = query.filter(
                (Empresa.nit.ilike(search)) |
                (Empresa.nombre_empresa.ilike(search))
            )
        query = query.order_by(Empresa.nombre_empresa.asc())
        empresas = query.paginate(
            page=page, per_page=per_page, error_out=False).items
        return [{"id_empresa": e.id_empresa, "nombre_empresa": e.nombre_empresa, "tipo_empresa": e.tipo_empresa} for e in empresas]
    except Exception as e:
        app.logger.error(f"Error en get_empresas_paginadas: {str(e)}")
        return []


def get_tipos_empleado_paginados(page, per_page, search, id_empresa):
    try:
        query = Tipo_Empleado.query
        if id_empresa:
            # Filtrar tipos de empleado según la empresa (ajusta según tu lógica)
            # Por ejemplo, si tienes una relación entre Tipo_Empleado y Empresa
            query = query.filter(Tipo_Empleado.id_empresa == id_empresa)
        if search:
            search = f"%{search}%"
            query = query.filter(Tipo_Empleado.tipo_empleado.ilike(search))
        query = query.order_by(Tipo_Empleado.tipo_empleado.asc())
        tipos = query.paginate(
            page=page, per_page=per_page, error_out=False).items
        return [{"id_tipo_empleado": t.id_tipo_empleado, "tipo_empleado": t.tipo_empleado} for t in tipos]
    except Exception as e:
        app.logger.error(f"Error en get_tipos_empleado_paginados: {str(e)}")
        return []
