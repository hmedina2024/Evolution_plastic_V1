# Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename
import uuid  # Módulo de Python para crear un string
import os
from os import remove, path  # Módulos para manejar archivos
from app import app # Importa la instancia de Flask desde app.py
from conexion.models import db, Operaciones, Empleados, Tipo_Empleado, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users  # Importa modelos desde models.py
import datetime
import pytz
import re
import openpyxl  # Para generar el Excel
from flask import send_file, session, Flask,url_for
from conexion.models import db, Empleados, Procesos, Actividades, OrdenProduccion,Empresa,Tipo_Empleado
from sqlalchemy import or_,func
from datetime import datetime,timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Message
import smtplib
import ssl
from email.message import EmailMessage

# Define la zona horaria local (ajusta según tu ubicación)
LOCAL_TIMEZONE = pytz.timezone('America/Bogota')


### Empleados
def procesar_form_empleado(dataForm, foto_perfil):
    try:
        # Formateando documento
        documento_sin_puntos = re.sub('[^0-9]+', '', dataForm['documento'])
        documento = int(documento_sin_puntos)

        # Obtener id_empresa y validar que esté presente
        if 'id_empresa' not in dataForm or not dataForm['id_empresa']:
            return False, "Debe seleccionar una empresa."

        id_empresa = int(dataForm['id_empresa'])  # Convertir a entero

        # Obtener tipo_empresa y mapearlo a tipo_empleado
        if 'tipo_empleado' not in dataForm or not dataForm['tipo_empleado']:
            return False, "El tipo de empleado no puede estar vacío."

        tipo_empresa = dataForm['tipo_empleado']  # Este es el valor de tipo_empresa de la empresa seleccionada

        # Mapear tipo_empresa a tipo_empleado (ajusta según tus valores)
        tipo_empleado_map = {
            "Directo": 1,
            "Temporal": 2
            # Agrega más mapeos si es necesario
        }

        if tipo_empresa not in tipo_empleado_map:
            return False, f"Tipo de empresa '{tipo_empresa}' no válido."

        tipo_empleado = tipo_empleado_map[tipo_empresa]

        # Procesar la foto del empleado
        result_foto_perfil = procesar_imagen_perfil(foto_perfil)

        # Crear el nuevo empleado con id_empresa y tipo_empleado
        empleado = Empleados(
            documento=documento,
            id_empresa=id_empresa,
            tipo_empleado=tipo_empleado,  # Usar el valor mapeado
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
        app.logger.error(f'Se produjo un error en procesar_form_empleado: {str(e)}')
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
        return Tipo_Empleado.query.distinct(Tipo_Empleado.id_tipo_empleado, Tipo_Empleado.tipo_empleado).order_by(Tipo_Empleado.id_tipo_empleado.asc()).all()
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
                'tipo_empleado': empresa.tipo_empresa if empresa else None,  # Usamos tipo_empresa de Empresa
                'nombre_empresa': empresa.nombre_empresa if empresa else None,  # Usamos nombre_empresa de Empresa
                'telefono_empleado': e.telefono_empleado,
                'email_empleado': e.email_empleado,
                'cargo': e.cargo,
                'foto_empleado': e.foto_empleado,
                'fecha_registro': e.fecha_registro.strftime('%Y-%m-%d %I:%M %p')
            }
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_empleadosBD: {str(e)}")
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
        empleado = db.session.query(Empleados).filter_by(id_empleado=data.form['id_empleado']).first()
        if empleado:
            # Formatear documento
            documento_sin_puntos = re.sub('[^0-9]+', '', data.form['documento'])
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

            # Actualizar los campos del empleado
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
        app.logger.error(f"Ocurrió un error en procesar_actualizacion_form: {str(e)}")
        return False, f"Error al actualizar el empleado: {str(e)}"

# Eliminar Empleado
def eliminar_empleado(id_empleado, foto_empleado):
    try:
        empleado = db.session.query(Empleados).filter_by(id_empleado=id_empleado).first()
        if empleado:
            empleado.fecha_borrado = datetime.now()  # Usar datetime.now() en lugar de datetime.datetime.now()
            db.session.commit()

            # Eliminando foto_empleado desde el directorio
            if foto_empleado:  # Verificar que foto_empleado no sea None o vacío
                basepath = path.dirname(__file__)
                url_file = path.join(basepath, '../static/fotos_empleados', foto_empleado)

                if path.exists(url_file):
                    remove(url_file)  # Borrar foto desde la carpeta

            return 1  # Indica éxito (rowcount)
        return 0  # Empleado no encontrado
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
                    db.func.date(Clientes.fecha_registro) == search  # Para búsqueda exacta de fecha
                )
            )

        # Total de registros sin filtrar
        total = db.session.query(Clientes).count()
        app.logger.debug(f"Total de registros sin filtrar: {total}")

        # Total de registros filtrados
        total_filtered = query.count()
        app.logger.debug(f"Total de registros filtrados: {total_filtered}")

        # Aplicar paginación
        clientes = query.order_by(Clientes.id_cliente.desc()).offset(start).limit(length).all()
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
        app.logger.error(f"Ocurrió un error en def buscar_cliente_bd: {str(e)}")
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

def buscar_cliente_bd(search='', search_date='', start=0, length=10, order=[{'column': 0, 'dir': 'desc'}]):
    try:
        query = db.session.query(Clientes)

        # Aplicar filtros
        if search:
            query = query.filter(Clientes.nombre_cliente.ilike(f'%{search}%'))
        if search_date:
            query = query.filter(db.func.date(Clientes.fecha_registro) == search_date)

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
        app.logger.error(f"Ocurrió un error en def buscar_cliente_bd: {str(e)}")
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
            cliente.fecha_borrado = datetime.now()
            db.session.commit()

            # Eliminando foto_cliente desde el directorio
            basepath = path.dirname(__file__)
            url_file = path.join(basepath, '../static/fotos_clientes', foto_cliente)

            if path.exists(url_file):
                remove(url_file)  # Borrar foto desde la carpeta

            return 1  # Indica éxito (rowcount)
        return 0  # Cliente no encontrado
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
    app.logger.debug("Entrando a procesar_form_operacion con datos: %s", dataForm)
    try:
        nombre_empleado = dataForm.get('nombre_empleado')
        nombre_proceso = dataForm.get('nombre_proceso')
        nombre_actividad = dataForm.get('nombre_actividad')
        cod_op = dataForm.get('cod_op')
        cantidad = dataForm.get('cantidad')
        pieza = dataForm.get('pieza')
        novedades = dataForm.get('novedades')
        hora_inicio = dataForm.get('hora_inicio')
        hora_fin = dataForm.get('hora_fin')
        action = dataForm.get('action')

        app.logger.debug(f"Valor de action recibido: {action}")

        if not all([nombre_empleado, nombre_proceso, nombre_actividad, cod_op, cantidad, hora_inicio, hora_fin]):
            app.logger.error("Faltan campos requeridos en el formulario")
            return None

        try:
            cantidad = int(cantidad)
        except (ValueError, TypeError):
            app.logger.error("Cantidad no es un número válido")
            return None

        empleado = db.session.query(Empleados).filter(
            db.text("CONCAT(nombre_empleado, ' ', apellido_empleado) = :nombre_completo")
        ).params(nombre_completo=nombre_empleado).first()

        if not empleado:
            app.logger.error("No se encontró el empleado con el nombre especificado")
            return 'No se encontró el empleado con el nombre especificado.'

        try:
            codigo_op = int(cod_op)
        except (ValueError, TypeError):
            app.logger.error("El código de la orden de producción no es válido")
            return 'El código de la orden de producción no es válido.'

        operacion = Operaciones(
            id_empleado=empleado.id_empleado,
            nombre_empleado=nombre_empleado,
            proceso=nombre_proceso,
            actividad=nombre_actividad,
            codigo_op=codigo_op,
            cantidad=cantidad,
            pieza_realizada=pieza,
            novedad=novedades,
            fecha_hora_inicio=datetime.strptime(hora_inicio, '%Y-%m-%dT%H:%M'),
            fecha_hora_fin=datetime.strptime(hora_fin, '%Y-%m-%dT%H:%M'),
            usuario_registro=session.get('name_surname', 'Usuario desconocido')
        )

        db.session.add(operacion)
        db.session.commit()

        if action == 'save_and_notify':
            app.logger.debug("Entrando al bloque de envío de correo...")
            try:
                admins = db.session.query(Users).filter_by(rol='administrador').all()
                if not admins:
                    app.logger.warning('No se encontraron usuarios con rol administrador.')
                else:
                    app.logger.debug(f"Se encontraron {len(admins)} administradores: {[admin.email_user for admin in admins]}")
                    email_sender = 'evolutioncontrolweb@gmail.com'
                    email_password = 'qsmr ccyb yzjd gzkm'  # Usa la contraseña de aplicación que configuraste
                    subject = 'Confirmación: Finalización de Actividad'

                    for admin in admins:
                        email_receiver = admin.email_user
                        body = f"""
                        Se ha registrado una nueva operación diaria:

                        - Empleado: {nombre_empleado}
                        - Proceso: {nombre_proceso}
                        - Actividad: {nombre_actividad}
                        - Orden de Producción: {cod_op}
                        - Cantidad Realizada: {cantidad}
                        - Fecha y Hora Inicio: {hora_inicio}
                        - Fecha y Hora Fin: {hora_fin}
                        - Pieza Realizada: {pieza if pieza else 'No especificada'}
                        - Novedades: {novedades if novedades else 'Sin novedades'}
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
                            smtp.sendmail(email_sender, email_receiver, em.as_string())
                            app.logger.info(f'Correo enviado a {email_receiver}')
            except Exception as e:
                app.logger.error(f'Error al enviar correo de notificación: {str(e)}')
        else:
            app.logger.debug("No se solicitó enviar correo (action != 'save_and_notify')")

        return 1
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
            'cantidad': o.cantidad,
            'fecha_registro': o.fecha_registro
        } for o in operaciones_bd]
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_operaciones_bd: {e}")
        return None
    
def buscar_operaciones_bd(empleado='', fecha='', hora='', start=0, length=10, order=[{'column': 0, 'dir': 'desc'}]):
    try:
        query = db.session.query(Operaciones)

        # Aplicar filtros
        if empleado:
            query = query.filter(
                db.or_(
                    Operaciones.nombre_empleado.ilike(f'%{empleado}%')
                )
            )
        if fecha:
            # No necesitamos convertir a UTC, ya que fecha_registro está en America/Bogota
            try:
                local_date = datetime.strptime(fecha, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Operaciones.fecha_registro) == local_date)
            except ValueError:
                app.logger.error(f"Formato de fecha inválido: {fecha}")
        if hora:
            # Filtrar por hora (asegúrate de que 'hora' esté en formato HH:MM:SS)
            query = query.filter(db.func.time(Operaciones.fecha_registro) == hora)

        # Total de registros sin filtrar
        total = db.session.query(Operaciones).count()
        app.logger.debug(f"Total de registros sin filtrar: {total}")

        # Total de registros filtrados
        total_filtered = query.count()
        app.logger.debug(f"Total de registros filtrados: {total_filtered}")

        # Mapear columnas de DataTables a campos de la tabla
        column_map = {
            0: Operaciones.id_operacion,      # #
            1: Operaciones.id_operacion,      # ID
            2: Operaciones.nombre_empleado,   # Empleado
            3: Operaciones.proceso,           # Proceso
            4: Operaciones.actividad,         # Actividad
            5: Operaciones.codigo_op,         # Cod. OP
            6: Operaciones.cantidad,          # Cantidad
            7: Operaciones.fecha_registro     # fecha_registro
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
        operaciones = query.offset(start).limit(length).all()
        app.logger.debug(f"Operaciones obtenidas: {len(operaciones)} registros")

        # Formatear los datos
        data = []
        for o in operaciones:
            data.append({
                'id_operacion': o.id_operacion,
                'nombre_empleado': o.nombre_empleado,
                'proceso': o.proceso,
                'actividad': o.actividad,
                'codigo_op': o.codigo_op,
                'cantidad': o.cantidad,
                'fecha_registro': o.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if o.fecha_registro else None
            })
        app.logger.debug(f"Datos formateados: {data}")

        return data, total, total_filtered

    except Exception as e:
        app.logger.error(f"Ocurrió un error en buscar_operaciones_bd: {str(e)}")
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
                'pieza': operacion.pieza_realizada,
                'novedad': operacion.novedad,
                'fecha_hora_inicio': operacion.fecha_hora_inicio,
                'fecha_hora_fin': operacion.fecha_hora_fin,
                'fecha_registro': operacion.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_operacion_unico: {e}")
        return None

def procesar_actualizacion_operacion(data):
    try:        
        operacion = db.session.query(Operaciones).filter_by(id_operacion=data.form['id_operacion']).first()
        if operacion:
            operacion.proceso = data.form['nombre_proceso']
            operacion.actividad = data.form['nombre_actividad']
            operacion.cantidad = int(data.form['cantidad'])  # Convertir a entero
            operacion.novedad = data.form['novedad']
            operacion.pieza_realizada = data.form['pieza'] if data.form['pieza'] else None
            
            # Validar y convertir fechas
            fecha_hora_inicio_str = data.form['fecha_hora_inicio']
            fecha_hora_fin_str = data.form['fecha_hora_fin']
            if not fecha_hora_inicio_str or not fecha_hora_fin_str:
                raise ValueError("Las fechas no pueden estar vacías")
            
            operacion.fecha_hora_inicio = datetime.strptime(fecha_hora_inicio_str, '%Y-%m-%dT%H:%M')
            operacion.fecha_hora_fin = datetime.strptime(fecha_hora_fin_str, '%Y-%m-%dT%H:%M')
            
            db.session.commit()
            return 1
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
        # Depurar los datos recibidos
        app.logger.debug(f"Datos recibidos del formulario: {dataForm}")

        # Convertir campos numéricos a enteros
        codigo_op = int(dataForm['cod_op']) if dataForm['cod_op'] else None
        cantidad = int(dataForm['cantidad']) if dataForm['cantidad'] else None
        supervisor = int(dataForm['supervisor']) if dataForm.get('supervisor') and dataForm['supervisor'].strip() else None

        # Crear el objeto OrdenProduccion
        orden = OrdenProduccion(
            codigo_op=codigo_op,
            nombre_cliente=dataForm['nombre_cliente'],
            producto=dataForm['producto'],
            estado=dataForm['estado'],
            cantidad=cantidad,
            odi=dataForm['odi'],
            empleado=dataForm['vendedor'],
            id_supervisor=supervisor,  # Ya manejamos el caso de None
            usuario_registro=session['name_surname']
        )
        db.session.add(orden)
        db.session.commit()
        app.logger.debug("Orden de producción guardada correctamente.")
        return 1  # Indica éxito (rowcount)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Se produjo un error en procesar_form_op: {str(e)}")
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
        # Consulta con JOIN para obtener el nombre del supervisor
        result = db.session.query(
            OrdenProduccion,
            db.func.concat(Empleados.nombre_empleado, ' ', Empleados.apellido_empleado).label('nombre_supervisor')
        ).outerjoin(
            Empleados, OrdenProduccion.id_supervisor == Empleados.id_empleado
        ).filter(
            OrdenProduccion.id_op == id_op
        ).first()

        if not result:
            return None

        orden, nombre_supervisor = result

        # Formatear los datos
        detalle = {
            'id_op': orden.id_op,
            'codigo_op': orden.codigo_op,
            'nombre_cliente': orden.nombre_cliente,
            'producto': orden.producto,
            'estado': orden.estado,
            'cantidad': orden.cantidad,
            'odi': orden.odi,
            'empleado': orden.empleado,
            'fecha_registro': orden.fecha_registro.strftime('%Y-%m-%d %I:%M %p'),
            'usuario_registro': orden.usuario_registro,
            'nombre_supervisor': nombre_supervisor if nombre_supervisor else 'Sin supervisor'  # Nuevo campo
        }
        app.logger.debug(f"Detalles de la orden: {detalle}")
        return detalle

    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_op_bd: {str(e)}")
        return None

def buscar_op_unico(id):
    try:
        # Consulta con JOIN para obtener el nombre y el ID del supervisor
        result = db.session.query(
            OrdenProduccion,
            Empleados.id_empleado.label('id_supervisor'),
            db.func.concat(Empleados.nombre_empleado, ' ', Empleados.apellido_empleado).label('nombre_supervisor')
        ).outerjoin(
            Empleados, OrdenProduccion.id_supervisor == Empleados.id_empleado
        ).filter(
            OrdenProduccion.id_op == id
        ).first()

        if not result:
            return None

        orden, id_supervisor, nombre_supervisor = result

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
                'id_supervisor': id_supervisor if id_supervisor else '',  # Se agrega el ID del supervisor
                'nombre_supervisor': nombre_supervisor if nombre_supervisor else 'Sin supervisor'
            }
        return None
    except Exception as e:
        app.logger.error(f"Ocurrió un error en def buscar_op_unico: {e}")
        return None

def procesar_actualizar_form_op(data):
    try:
        id_op = data.form.get('id_op')
        if not id_op:
            app.logger.error("ID de la orden no proporcionado")
            return None

        orden = db.session.query(OrdenProduccion).filter_by(id_op=id_op).first()
        if orden:
            # Solo actualizamos los campos que vienen en el formulario
            if 'producto' in data.form:
                orden.producto = data.form['producto']
            if 'estado' in data.form:
                orden.estado = data.form['estado']
            if 'cantidad' in data.form:
                orden.cantidad = data.form['cantidad']
            if 'odi' in data.form:
                orden.odi = data.form['odi']
            if 'supervisor' in data.form:
                orden.id_supervisor = int(data.form['supervisor']) if data.form['supervisor'] else None  # Nuevo campo
            # No actualizamos codigo_op, nombre_cliente, empleado porque no se envían
            db.session.commit()
            app.logger.debug(f"Orden con id_op {id_op} actualizada correctamente")
            return 1  # Éxito
        else:
            app.logger.error(f"Orden con id_op {id_op} no encontrada")
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
    
def buscar_ordenes_produccion_bd(codigo_op='', fecha='', start=0, length=10, order=None):
    try:
        # Consulta base con JOIN para obtener el nombre del supervisor
        query = db.session.query(
            OrdenProduccion,
            db.func.concat(Empleados.nombre_empleado, ' ', Empleados.apellido_empleado).label('nombre_supervisor')
        ).outerjoin(
            Empleados, OrdenProduccion.id_supervisor == Empleados.id_empleado
        )

        # Filtro por código de orden de producción
        if codigo_op:
            query = query.filter(OrdenProduccion.codigo_op.ilike(f'%{codigo_op}%'))

        # Filtro por fecha de registro
        if fecha:
            try:
                # Convertir la fecha del input (YYYY-MM-DD) a un objeto datetime
                fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
                # Filtrar por la parte de la fecha de fecha_registro
                query = query.filter(func.date(OrdenProduccion.fecha_registro) == fecha_dt)
            except ValueError as e:
                app.logger.error(f"Error al parsear la fecha: {fecha}, error: {e}")
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
            7: None,                         # Columna 'Supervisor' (no ordenable por ahora)
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
            'nombre_supervisor': nombre_supervisor if nombre_supervisor else 'Sin supervisor'  # Mostrar el nombre del supervisor
        } for op, nombre_supervisor in results]
        app.logger.debug(f"Datos formateados: {data}")

        return data, total, total_filtered

    except Exception as e:
        app.logger.error(f"Error en buscar_ordenes_produccion_bd: {str(e)}")
        return [], 0, 0

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
        query = db.session.query(Empleados).order_by(Empleados.id_empleado.desc()).filter(Empleados.fecha_borrado.is_(None))
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
            empleados = query.all()
        return [{'nombre_empleado': f"{e.nombre_empleado} {e.apellido_empleado}"} for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en get_empleados_paginados: {e}")
        return []

def get_supervisores_paginados(page, per_page, search=None):
    try:
        query = db.session.query(Empleados).filter(
            Empleados.fecha_borrado.is_(None),
            Empleados.cargo.in_(['supervisor', 'supervisora'])  # Filtrar por cargo
        ).order_by(Empleados.id_empleado.desc())
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
            empleados = query.all()
        return [{'id_empleado': e.id_empleado, 'nombre_empleado': f"{e.nombre_empleado} {e.apellido_empleado}"} for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en get_supervisores_paginados: {e}")
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
    

def get_clientes_paginados(page, per_page, search=None):
    try:
        query = db.session.query(Clientes).order_by(Clientes.id_cliente.desc())
        if search:
            search = f"%{search}%"
            query = query.filter(Clientes.nombre_cliente.like(search))
        if page and per_page:
            offset = (page - 1) * per_page
            clientes = query.limit(per_page).offset(offset).all()
        else:
            clientes = query.all()
        return [{'nombre_cliente': c.nombre_cliente} for c in clientes]
    except Exception as e:
        app.logger.error(f"Error en get_clientes_paginados: {e}")
        return []
    
    

## EMPRESAS

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
            usuario_registro=session.get('name_surname', 'Usuario desconocido'),
            fecha_registro=datetime.now()
        )

        # Guardar en la base de datos
        db.session.add(empresa)
        db.session.commit()
        return 1  # Indica éxito

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Se produjo un error en procesar_form_empresa: {str(e)}')
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
        total = db.session.query(Empresa).filter(Empresa.fecha_borrado.is_(None)).count()

        # Devolver una tupla con los registros y el total
        return (empresas, total)
    except Exception as e:
        app.logger.error(f"Error en la función sql_lista_empresasBD: {str(e)}")
        return None
    
    
def sql_detalles_empresaBD(id_empresa):
    try:
        empresa = db.session.query(Empresa).filter_by(id_empresa=id_empresa, fecha_borrado=None).first()
        if empresa:
            return empresa
        return None
    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_empresaBD: {str(e)}")
        return None

def buscar_empresa_unica(id_empresa):
    try:
        empresa = db.session.query(Empresa).filter_by(id_empresa=id_empresa, fecha_borrado=None).first()
        if empresa:
            return empresa
        return None
    except Exception as e:
        app.logger.error(f"Error en la función buscar_empresa_unica: {str(e)}")
        return None
    
    
def eliminar_empresa(id_empresa):
    try:
        empresa = db.session.query(Empresa).filter_by(id_empresa=id_empresa, fecha_borrado=None).first()
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
        empresa = db.session.query(Empresa).filter_by(id_empresa=id_empresa, fecha_borrado=None).first()
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
        empresa.usuario_modificacion = session.get('usuario')  # Asumiendo que el usuario está en la sesión

        db.session.commit()
        return 1  # Éxito
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al actualizar la empresa: {str(e)}")
        return f"Error al actualizar la empresa: {str(e)}"
    
    
def buscando_empresas(draw, start, length, search_value, order_column, order_direction, filter_empresa):
    try:
        # Obtener el total de registros sin filtrar
        total_records = db.session.query(func.count(Empresa.id_empresa)).filter(Empresa.fecha_borrado.is_(None)).scalar()

        # Construir la consulta base
        query = db.session.query(Empresa).filter(Empresa.fecha_borrado.is_(None))

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
        empresas = query.paginate(page=page, per_page=per_page, error_out=False).items
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
        tipos = query.paginate(page=page, per_page=per_page, error_out=False).items
        return [{"id_tipo_empleado": t.id_tipo_empleado, "tipo_empleado": t.tipo_empleado} for t in tipos]
    except Exception as e:
        app.logger.error(f"Error en get_tipos_empleado_paginados: {str(e)}")
        return []