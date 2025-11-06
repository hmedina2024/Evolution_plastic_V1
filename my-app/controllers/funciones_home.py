# Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename
import uuid  # Módulo de Python para crear un string
import json
import magic
from sqlalchemy.orm import joinedload
import os
from os import remove, path  # Módulos para manejar archivos
from app import app  # Importa la instancia de Flask desde app.py
# Importa modelos desde models.py
from conexion.models import db, OPLog, OrdenPiezasActividades, OrdenPiezasProcesos, OrdenPiezas, RendersOP, DocumentosOP, Operaciones, Empleados, Tipo_Empleado, Piezas, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users, Empresa, OrdenProduccionProcesos, DetallesPiezaMaestra, OrdenPiezaValoresDetalle, OrdenProduccionURLs, OrdenPiezaEspecificaciones # Añadido OrdenProduccionURLs y OrdenPiezaEspecificaciones
# import datetime # datetime ya se importa desde datetime
import pytz
import re
import openpyxl  # Para generar el Excel
from flask import send_file, session, Flask, url_for, jsonify, flash
# from conexion.models import db, Empleados, Procesos, Actividades, OrdenProduccion, Empresa, Tipo_Empleado # Ya importado arriba
from sqlalchemy import or_, func, desc, asc
from datetime import datetime, timedelta  # datetime ya importado arriba
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Message
import smtplib
import ssl
from email.message import EmailMessage
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import text

magic.Magic(mime=True)

# Define la zona horaria local (ajusta según tu ubicación)
LOCAL_TIMEZONE = pytz.timezone('America/Bogota')

# Definiciones de extensiones permitidas
ALLOWED_RENDER_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_DOC_EXTENSIONS = {'pdf', 'doc', 'docx',
                          'xls', 'xlsx', 'txt', 'ppt', 'pptx', 'csv'}


# --- Funciones de Empleados ---
def procesar_form_empleado(dataForm, foto_perfil):
    try:
        documento_sin_puntos = re.sub(
            '[^0-9]+', '', dataForm.get('documento', ''))
        if not documento_sin_puntos:
            raise ValueError("Documento es requerido.")
        documento = int(documento_sin_puntos)

        id_empresa_str = dataForm.get('id_empresa')
        if not id_empresa_str or not id_empresa_str.isdigit():
            raise ValueError("Debe seleccionar una empresa válida.")
        id_empresa = int(id_empresa_str)

        id_tipo_empleado_str = dataForm.get('tipo_empleado')
        if not id_tipo_empleado_str or not id_tipo_empleado_str.isdigit():
            raise ValueError("Debe seleccionar un tipo de empleado válido.")
        id_tipo_empleado = int(id_tipo_empleado_str)

        nombre_empleado = dataForm.get('nombre_empleado')
        if not nombre_empleado:
            raise ValueError("Nombre del empleado es requerido.")

        result_foto_perfil = None
        if foto_perfil and foto_perfil.filename:
            valido, nombre_foto_o_msg = procesar_imagen_perfil(
                foto_perfil, 'fotos_empleados', ALLOWED_RENDER_EXTENSIONS)
            if not valido:
                raise ValueError(f"Foto empleado: {nombre_foto_o_msg}")
            result_foto_perfil = nombre_foto_o_msg

        empleado = Empleados(
            documento=documento,
            id_empresa=id_empresa,
            id_tipo_empleado=id_tipo_empleado,
            nombre_empleado=nombre_empleado,
            apellido_empleado=dataForm.get('apellido_empleado'),
            telefono_empleado=dataForm.get('telefono_empleado'),
            email_empleado=dataForm.get('email_empleado'),
            cargo=dataForm.get('cargo'),
            foto_empleado=result_foto_perfil
        )
        db.session.add(empleado)
        db.session.commit()
        return True, "El empleado fue registrado con éxito."
    except ValueError as ve:
        app.logger.warning(
            f"Error de validación en procesar_form_empleado: {str(ve)}")
        return False, str(ve)
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f'Se produjo un error en procesar_form_empleado: {str(e)}', exc_info=True)
        return False, f'Se produjo un error interno al registrar el empleado.'


def procesar_imagen_perfil(foto_storage, subfolder, allowed_extensions_set):
    try:
        if foto_storage and foto_storage.filename:
            filename = secure_filename(foto_storage.filename)
            extension = os.path.splitext(filename)[1].lower().strip('.')
            if extension not in allowed_extensions_set:
                app.logger.warning(
                    f"Extensión de archivo no permitida: .{extension} para {subfolder}. Permitidas: {', '.join(allowed_extensions_set)}")
                return False, f"Extensión .{extension} no permitida. Permitidas: {', '.join(allowed_extensions_set)}"

            nuevoNameFile = (uuid.uuid4().hex + uuid.uuid4().hex)[:100]
            nombreFile = f"{nuevoNameFile}.{extension}"

            basepath = os.path.abspath(os.path.dirname(__file__))
            upload_dir = os.path.normpath(
                os.path.join(basepath, f'../static/{subfolder}'))
            os.makedirs(upload_dir, exist_ok=True)

            upload_path = os.path.join(upload_dir, nombreFile)
            foto_storage.save(upload_path)
            return True, nombreFile
        return True, None  # No hay archivo, pero no es un error de validación de la función en sí
    except Exception as e:
        app.logger.error(
            f"Error al procesar imagen en '{subfolder}': {e}", exc_info=True)
        return False, "Error interno al guardar la imagen."


def obtener_tipo_empleado():
    try:
        return Tipo_Empleado.query.filter_by(fecha_borrado=None).order_by(Tipo_Empleado.id_tipo_empleado.asc()).all()
    except Exception as e:
        app.logger.error(
            f"Error en la función obtener_tipo_empleado: {e}", exc_info=True)
        return []


def sql_lista_empleadosBD():
    try:
        return db.session.query(Empleados, Empresa).join(Empresa, Empleados.id_empresa == Empresa.id_empresa).filter(Empleados.fecha_borrado.is_(None)).order_by(Empleados.fecha_registro.desc()).all()
    except Exception as e:
        app.logger.error(f"Error al listar empleados: {str(e)}", exc_info=True)
        return []


def get_total_empleados():
    try:
        return db.session.query(func.count(Empleados.id_empleado)).filter(Empleados.fecha_borrado.is_(None)).scalar() or 0
    except Exception as e:
        app.logger.error(f"Error en get_total_empleados: {e}", exc_info=True)
        return 0


def sql_detalles_empleadosBD(id_empleado):
    try:
        empleado_tupla = db.session.query(Empleados, Empresa, Tipo_Empleado).\
            join(Empresa, Empleados.id_empresa == Empresa.id_empresa).\
            join(Tipo_Empleado, Empleados.id_tipo_empleado == Tipo_Empleado.id_tipo_empleado).\
            filter(Empleados.id_empleado == id_empleado, Empleados.fecha_borrado.is_(None)).\
            first()
        if empleado_tupla:
            e, empresa, tipo_emp = empleado_tupla
            return {
                'id_empleado': e.id_empleado, 'documento': e.documento,
                'nombre_empleado': e.nombre_empleado, 'apellido_empleado': e.apellido_empleado,
                'tipo_empleado': tipo_emp.tipo_empleado if tipo_emp else None,
                'id_tipo_empleado': e.id_tipo_empleado,
                'id_empresa': e.id_empresa,
                'nombre_empresa': empresa.nombre_empresa if empresa else None,
                'telefono_empleado': e.telefono_empleado, 'email_empleado': e.email_empleado,
                'cargo': e.cargo, 'foto_empleado': e.foto_empleado,
                'fecha_registro': e.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if e.fecha_registro else None
            }
        return None
    except Exception as e:
        app.logger.error(
            f"Error en sql_detalles_empleadosBD: {str(e)}", exc_info=True)
        return None


def empleados_reporte():
    try:
        empleados = db.session.query(Empleados).join(Tipo_Empleado, Empleados.id_tipo_empleado == Tipo_Empleado.id_tipo_empleado, isouter=True).filter(
            Empleados.fecha_borrado.is_(None)).order_by(Empleados.id_empleado.desc()).all()
        return [{
            'id_empleado': e.id_empleado, 'documento': e.documento,
            'nombre_empleado': e.nombre_empleado, 'apellido_empleado': e.apellido_empleado,
            'email_empleado': e.email_empleado, 'telefono_empleado': e.telefono_empleado,
            'cargo': e.cargo, 'fecha_registro': e.fecha_registro.strftime('%d de %b %Y %I:%M %p') if e.fecha_registro else 'N/A',
            'tipo_empleado': e.tipo_empleado_ref.tipo_empleado if e.tipo_empleado_ref else 'N/A'
        } for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en empleados_reporte: {e}", exc_info=True)
        return []


def generar_codigo_op():
    try:
        ultima_op = db.session.query(OrdenProduccion.codigo_op).order_by(
            OrdenProduccion.codigo_op.desc()).first()
        if ultima_op and ultima_op[0] and str(ultima_op[0]).isdigit():
            nuevo_codigo = int(ultima_op[0]) + 1
        else:
            max_codigo_op = db.session.query(
                func.max(OrdenProduccion.codigo_op)).scalar()
            nuevo_codigo = (
                int(max_codigo_op) + 1) if max_codigo_op and str(max_codigo_op).isdigit() else 1
        return str(nuevo_codigo)
    except Exception as e:
        app.logger.error(f"Error al generar código de OP: {e}", exc_info=True)
        return "1"


def generar_reporte_excel():
    try:
        data_empleados = empleados_reporte()
        if not data_empleados:
            flash("No hay datos de empleados para generar el reporte.", "warning")
            return redirect(url_for('lista_empleados'))

        wb = openpyxl.Workbook()
        hoja = wb.active
        cabecera_excel = ("Documento", "Nombre", "Apellido", "Tipo Empleado",
                          "Telefono", "Email", "Profesión", "Fecha de Ingreso")
        hoja.append(cabecera_excel)

        for registro in data_empleados:
            hoja.append((
                registro.get('documento'), registro.get(
                    'nombre_empleado'), registro.get('apellido_empleado'),
                registro.get('tipo_empleado'), registro.get(
                    'telefono_empleado'), registro.get('email_empleado'),
                registro.get('cargo'), registro.get('fecha_registro')
            ))

        fecha_actual = datetime.now()
        archivo_excel = f"Reporte_empleados_{fecha_actual.strftime('%Y_%m_%d_%H%M%S')}.xlsx"
        carpeta_descarga = os.path.join(
            app.root_path, 'static', 'downloads-excel')
        os.makedirs(carpeta_descarga, exist_ok=True)
        ruta_archivo = os.path.join(carpeta_descarga, archivo_excel)
        wb.save(ruta_archivo)
        return send_file(ruta_archivo, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error al generar reporte Excel: {e}", exc_info=True)
        flash("Error al generar el reporte Excel.", "error")
        return redirect(url_for('lista_empleados'))


def buscar_empleado_bd(search):
    try:
        if not search or not search.strip():
            return []
        search_term = f"%{search.strip()}%"
        empleados = db.session.query(Empleados).join(Tipo_Empleado, Empleados.id_tipo_empleado == Tipo_Empleado.id_tipo_empleado, isouter=True)\
            .filter(Empleados.fecha_borrado.is_(None))\
            .filter(or_(Empleados.nombre_empleado.ilike(search_term), Empleados.apellido_empleado.ilike(search_term), Empleados.documento.ilike(search_term)))\
            .order_by(Empleados.nombre_empleado.asc()).limit(20).all()

        return [{
            'id_empleado': e.id_empleado, 'documento': e.documento,
            'nombre_empleado': e.nombre_empleado, 'apellido_empleado': e.apellido_empleado,
            'cargo': e.cargo,
            'tipo_empleado': e.tipo_empleado_ref.tipo_empleado if e.tipo_empleado_ref else 'N/A'
        } for e in empleados]
    except Exception as e:
        app.logger.error(
            f"Ocurrió un error en buscar_empleado_bd: {e}", exc_info=True)
        return []


def validate_document(documento):
    try:
        documento_limpio = re.sub('[^0-9]+', '', str(documento))
        if not documento_limpio:
            return False
        empleado = db.session.query(Empleados.id_empleado).filter_by(
            documento=documento_limpio, fecha_borrado=None).first()
        return empleado is not None
    except Exception as e:
        app.logger.error(f"Error en validate_document: {e}", exc_info=True)
        return False


def buscar_empleado_unico(id_empleado_param):
    try:
        if not id_empleado_param:
            return None
        empleado_tupla = db.session.query(Empleados, Empresa, Tipo_Empleado).\
            join(Empresa, Empleados.id_empresa == Empresa.id_empresa).\
            join(Tipo_Empleado, Empleados.id_tipo_empleado == Tipo_Empleado.id_tipo_empleado).\
            filter(Empleados.id_empleado == id_empleado_param, Empleados.fecha_borrado.is_(None)).\
            first()
        if empleado_tupla:
            e, empresa, tipo_emp = empleado_tupla
            return {
                'id_empleado': e.id_empleado, 'documento': e.documento,
                'id_empresa': e.id_empresa, 'nombre_empresa': empresa.nombre_empresa,
                'nombre_empleado': e.nombre_empleado, 'apellido_empleado': e.apellido_empleado,
                'id_tipo_empleado': e.id_tipo_empleado, 'tipo_empleado': tipo_emp.tipo_empleado,
                'telefono_empleado': e.telefono_empleado, 'email_empleado': e.email_empleado,
                'cargo': e.cargo, 'foto_empleado': e.foto_empleado,
                'fecha_registro': e.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if e.fecha_registro else None
            }
        return None
    except Exception as e:
        app.logger.error(
            f"Error al buscar empleado único (ID: {id_empleado_param}): {str(e)}", exc_info=True)
        return None


def procesar_actualizacion_form(data_request):
    try:
        id_empleado_str = data_request.form.get('id_empleado')
        if not id_empleado_str or not id_empleado_str.isdigit():
            return False, "ID de empleado inválido o faltante."

        empleado = db.session.query(Empleados).filter_by(
            id_empleado=int(id_empleado_str)).first()
        if not empleado or empleado.fecha_borrado is not None:
            return False, "El empleado no existe o ha sido eliminado."

        documento_str = data_request.form.get('documento', '')
        documento_sin_puntos = re.sub('[^0-9]+', '', documento_str)
        if not documento_sin_puntos:
            return False, "Documento es requerido."
        documento = int(documento_sin_puntos)

        if str(empleado.documento) != str(documento):
            otro_empleado_con_mismo_doc = db.session.query(Empleados.id_empleado).filter(
                Empleados.documento == documento, Empleados.id_empleado != empleado.id_empleado, Empleados.fecha_borrado.is_(None)).first()
            if otro_empleado_con_mismo_doc:
                return False, f"El documento '{documento}' ya está registrado para otro empleado."

        id_empresa_str = data_request.form.get('id_empresa')
        if not id_empresa_str or not id_empresa_str.isdigit():
            return False, "Debe seleccionar una empresa."

        id_tipo_empleado_str = data_request.form.get('id_tipo_empleado')
        app.logger.debug(f"Valor de id_tipo_empleado_str: {id_tipo_empleado_str}")
        print('tipo empleado', id_tipo_empleado_str)
        if not id_tipo_empleado_str or not id_tipo_empleado_str.isdigit():
            return False, "Debe seleccionar un tipo de empleado."

        empleado.documento = documento
        empleado.id_empresa = int(id_empresa_str)
        empleado.nombre_empleado = data_request.form.get('nombre_empleado')
        if not empleado.nombre_empleado:
            return False, "Nombre del empleado es requerido."
        empleado.apellido_empleado = data_request.form.get('apellido_empleado')
        empleado.id_tipo_empleado = int(id_tipo_empleado_str)
        empleado.telefono_empleado = data_request.form.get('telefono_empleado')
        empleado.email_empleado = data_request.form.get('email_empleado')
        empleado.cargo = data_request.form.get('cargo')

        foto_empleado_file = data_request.files.get('foto_empleado')
        if foto_empleado_file and foto_empleado_file.filename:
            valido, nombre_foto_o_msg = procesar_imagen_perfil(
                foto_empleado_file, 'fotos_empleados', ALLOWED_RENDER_EXTENSIONS)
            if not valido:
                return False, f"Foto empleado: {nombre_foto_o_msg}"
            if nombre_foto_o_msg:
                if empleado.foto_empleado and empleado.foto_empleado != nombre_foto_o_msg:
                    try:
                        path_foto_anterior = os.path.join(
                            app.root_path, 'static', 'fotos_empleados', empleado.foto_empleado)
                        if os.path.exists(path_foto_anterior):
                            os.remove(path_foto_anterior)
                    except Exception as e_remove:
                        app.logger.error(
                            f"Error eliminando foto anterior del empleado: {e_remove}")
                empleado.foto_empleado = nombre_foto_o_msg

        db.session.commit()
        return True, "Empleado actualizado con éxito."
    except ValueError as ve:
        db.session.rollback()
        app.logger.warning(
            f"Error de validación en procesar_actualizacion_form: {str(ve)}")
        return False, str(ve)
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Ocurrió un error en procesar_actualizacion_form: {str(e)}", exc_info=True)
        return False, f"Error interno al actualizar el empleado."


def eliminar_empleado(id_empleado, foto_empleado_nombre):
    try:
        empleado = db.session.query(Empleados).filter_by(
            id_empleado=id_empleado).first()
        if empleado:
            empleado.fecha_borrado = datetime.now()
            db.session.commit()
            if foto_empleado_nombre:
                try:
                    basepath = os.path.abspath(os.path.dirname(__file__))
                    url_file = os.path.join(
                        basepath, '../static/fotos_empleados', foto_empleado_nombre)
                    if os.path.exists(url_file):
                        os.remove(url_file)
                except Exception as e_remove_foto:
                    app.logger.error(
                        f"Error eliminando foto del empleado al borrar: {e_remove_foto}")
            return True
        return False
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_empleado: {e}", exc_info=True)
        return False

# --- Funciones de Usuarios ---


def sql_lista_usuarios_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = Users.query.filter(Users.email_user != 'admin@admin.com', Users.fecha_borrado.is_(None))\
                           .order_by(Users.created_user.desc())\
                           .limit(per_page).offset(offset)
        usuarios_bd = query.all()
        return [{
            'id': u.id, 'name_surname': u.name_surname, 'email_user': u.email_user,
            'rol': u.rol, 'created_user': u.created_user.strftime('%Y-%m-%d %I:%M %p') if u.created_user else 'N/A'
        } for u in usuarios_bd]
    except Exception as e:
        app.logger.error(f"Error en sql_lista_usuarios_bd: {e}", exc_info=True)
        return []


def get_total_usuarios():
    try:
        return Users.query.filter(Users.email_user != 'admin@admin.com', Users.fecha_borrado.is_(None)).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_usuarios: {e}", exc_info=True)
        return 0


def eliminar_usuario(user_id):
    try:
        usuario = Users.query.get(user_id)
        if usuario and usuario.email_user != 'admin@admin.com':
            usuario.fecha_borrado = datetime.now()
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_usuario: {e}", exc_info=True)
        return False

# --- Funciones de Procesos ---


def procesar_form_proceso(dataForm):
    try:
        codigo_proceso = dataForm.get('codigo_proceso')
        nombre_proceso = dataForm.get('nombre_proceso')
        if not codigo_proceso or not nombre_proceso:
            raise ValueError("Código y Nombre del proceso son requeridos.")

        existente = Procesos.query.filter_by(
            codigo_proceso=codigo_proceso, fecha_borrado=None).first()
        if existente:
            raise ValueError(
                f"El código de proceso '{codigo_proceso}' ya existe.")

        proceso = Procesos(
            codigo_proceso=codigo_proceso,
            nombre_proceso=nombre_proceso,
            descripcion_proceso=dataForm.get('descripcion_proceso'),
        )
        db.session.add(proceso)
        db.session.commit()
        return True, "Proceso registrado correctamente."
    except ValueError as ve:
        app.logger.warning(
            f"Error de validación en procesar_form_proceso: {str(ve)}")
        return False, str(ve)
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f'Se produjo un error en procesar_form_proceso: {str(e)}', exc_info=True)
        return False, "Error interno al registrar el proceso."


def sql_lista_procesos_bd(page=1, per_page=10):
    try:
        offset = (page - 1) * per_page
        query = Procesos.query.filter(Procesos.fecha_borrado.is_(None))\
                              .order_by(Procesos.id_proceso.desc())\
                              .limit(per_page).offset(offset)
        procesos_bd = query.all()
        return [{
            'id_proceso': p.id_proceso,
            'codigo_proceso': p.codigo_proceso,
            'nombre_proceso': p.nombre_proceso,
            'descripcion_proceso': p.descripcion_proceso,
            'fecha_registro': p.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if p.fecha_registro else 'N/A'
        } for p in procesos_bd]
    except Exception as e:
        app.logger.error(f"Error en sql_lista_procesos_bd: {e}", exc_info=True)
        return []


def get_total_procesos():
    try:
        return Procesos.query.filter(Procesos.fecha_borrado.is_(None)).count()
    except Exception as e:
        app.logger.error(f"Error en get_total_procesos: {e}", exc_info=True)
        return 0


def sql_detalles_procesos_bd(id_proceso_param):
    try:
        proceso = Procesos.query.filter_by(
            id_proceso=id_proceso_param, fecha_borrado=None).first()
        if proceso:
            actividades_asociadas = [{'id_actividad': act.id_actividad, 'nombre_actividad': act.nombre_actividad,
                                      'codigo_actividad': act.codigo_actividad} for act in proceso.actividades if act.fecha_borrado is None]
            return {
                'id_proceso': proceso.id_proceso, 'codigo_proceso': proceso.codigo_proceso,
                'nombre_proceso': proceso.nombre_proceso, 'descripcion_proceso': proceso.descripcion_proceso,
                'fecha_registro': proceso.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if proceso.fecha_registro else 'N/A',
                'actividades': actividades_asociadas
            }
        return None
    except Exception as e:
        app.logger.error(
            f"Error en sql_detalles_procesos_bd: {e}", exc_info=True)
        return None


def buscar_proceso_unico(id_proceso_param):
    try:
        return Procesos.query.filter_by(id_proceso=id_proceso_param, fecha_borrado=None).first()
    except Exception as e:
        app.logger.error(
            f"Ocurrió un error en buscar_proceso_unico: {e}", exc_info=True)
        return None


def procesar_actualizar_proceso(id_proceso, dataForm):
    try:
        proceso = Procesos.query.get(id_proceso)
        if not proceso or proceso.fecha_borrado is not None:
            return False, "Proceso no encontrado o ya fue eliminado."

        codigo_proceso = dataForm.get('codigo_proceso')
        nombre_proceso = dataForm.get('nombre_proceso')
        if not codigo_proceso or not nombre_proceso:
            raise ValueError("Código y Nombre del proceso son requeridos.")

        if proceso.codigo_proceso != codigo_proceso:
            otro_proceso_con_codigo = Procesos.query.filter(
                Procesos.codigo_proceso == codigo_proceso, Procesos.id_proceso != id_proceso, Procesos.fecha_borrado.is_(None)).first()
            if otro_proceso_con_codigo:
                raise ValueError(
                    f"El código de proceso '{codigo_proceso}' ya está en uso.")

        proceso.codigo_proceso = codigo_proceso
        proceso.nombre_proceso = nombre_proceso
        proceso.descripcion_proceso = dataForm.get('descripcion_proceso')
        db.session.commit()
        return True, "Proceso actualizado correctamente."
    except ValueError as ve:
        db.session.rollback()
        app.logger.warning(
            f"Error de validación al actualizar proceso: {str(ve)}")
        return False, str(ve)
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Ocurrió un error en procesar_actualizar_proceso: {e}", exc_info=True)
        return False, "Error interno al actualizar el proceso."


def eliminar_proceso(id_proceso):
    try:
        proceso = Procesos.query.get(id_proceso)
        if proceso:
            if Actividades.query.filter_by(id_proceso=id_proceso, fecha_borrado=None).first() or \
                OrdenPiezasProcesos.query.filter_by(id_proceso=id_proceso).first():
                proceso.fecha_borrado = datetime.now()
                db.session.commit()
                return True, "Proceso marcado como eliminado (está en uso)."

            proceso.fecha_borrado = datetime.now()
            db.session.commit()
            return True, "Proceso eliminado (o marcado como eliminado) correctamente."
        return False, "Proceso no encontrado."
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_proceso: {e}", exc_info=True)
        return False, "Error interno al eliminar el proceso."

# --- Funciones de Clientes ---

# Clientes

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



def procesar_form_cliente(dataForm, foto_perfil_cliente):
    # Formateando documento
    documento_sin_puntos = re.sub('[^0-9]+', '', dataForm['documento'])
    documento = int(documento_sin_puntos)

    result_foto_cliente = procesar_imagen_cliente(foto_perfil_cliente)
    try:
        cliente = Clientes(
            id_tipo_documento=dataForm['id_tipo_documento'],
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
        query = db.session.query(Clientes).join(
            Clientes.tipo_documento_rel, isouter=True)  # Unir con TipoDocumento

        # Aplicar filtro de borrado lógico si existe en el modelo Clientes
        if hasattr(Clientes, 'fecha_borrado'):
            query = query.filter(Clientes.fecha_borrado.is_(None))

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
            'tipo_documento': c.tipo_documento_rel.td_abreviacion if c.tipo_documento_rel else 'N/A',
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
                'id_tipo_documento': cliente.id_tipo_documento,  # Para el form de update
                # Nombre completo para detalles
                'tipo_documento': cliente.tipo_documento_rel.tipo_documento if cliente.tipo_documento_rel else 'N/A',
                # Abreviación si se necesita
                'td_abreviacion': cliente.tipo_documento_rel.td_abreviacion if cliente.tipo_documento_rel else 'N/A',
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
            1: Clientes.id_tipo_documento,      # Tipo Documento
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
                'id_tipo_documento': cliente.id_tipo_documento, # Devolver el ID para el select
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

            cliente.id_tipo_documento = data.form['id_tipo_documento'] # Corregido
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
            id_proceso=dataForm['id_proceso'],
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
        query = Actividades.query.filter(Actividades.fecha_borrado.is_(None))\
                            .order_by(Actividades.id_actividad.desc())\
                            .limit(per_page).offset(offset)
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
            proceso = actividad.proceso
            return {
                'id_actividad': actividad.id_actividad,
                'codigo_actividad': actividad.codigo_actividad,
                'nombre_actividad': actividad.nombre_actividad,
                'id_proceso': actividad.id_proceso,
                'proceso': proceso.nombre_proceso if proceso else 'Desconocido',
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
            actividad.id_proceso = data.form['id_proceso']
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
        actividad = Actividades.query.get(id_actividad)
        if actividad:
            if Actividades.query.filter_by(id_actividad=id_actividad, fecha_borrado=None).first() or \
                OrdenPiezasProcesos.query.filter_by(id_actividad=id_actividad).first():
                actividad.fecha_borrado = datetime.now()
                db.session.commit()
                return True, "Proceso marcado como eliminado (está en uso)."

            actividad.fecha_borrado = datetime.now()
            db.session.commit()
            return True, "Actividad eliminado (o marcado como eliminado) correctamente."
        return False, "Actividad no encontrado."
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_actividad: {e}", exc_info=True)
        return False, "Error interno al eliminar el proceso."

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
        mensaje_personalizado = dataForm.get('mensaje_personalizado')

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
                destinatarios_ids_str = dataForm.get('destinatarios')
                if not destinatarios_ids_str:
                    app.logger.warning('No se seleccionaron destinatarios.')
                else:
                    destinatarios_ids = [int(id) for id in destinatarios_ids_str.split(',')]
                    destinatarios = db.session.query(Users).filter(Users.id.in_(destinatarios_ids)).all()
                    
                    app.logger.debug(
                        f"Se encontraron {len(destinatarios)} destinatarios.")
                    email_sender = 'evolutioncontrolweb@gmail.com'
                    email_password = 'qsmr ccyb yzjd gzkm'
                    subject = 'Confirmación: Finalización de Actividad'
                    
                    # Obtener los nombres del proceso y actividad
                    proceso = db.session.query(Procesos).filter_by(id_proceso=id_proceso).first()
                    actividad = db.session.query(Actividades).filter_by(id_actividad=id_actividad).first()
                    nombre_proceso = proceso.nombre_proceso if proceso else f"ID Proceso no encontrado ({id_proceso})"
                    nombre_actividad = actividad.nombre_actividad if actividad else f"ID Actividad no encontrado ({id_actividad})"

                    orden_produccion = OrdenProduccion.query.get(id_op)
                    codigo_op_a_mostrar = orden_produccion.codigo_op if orden_produccion else id_op

                    for destinatario in destinatarios:
                        if destinatario.email_user:
                            email_receiver = destinatario.email_user
                            body = f"""
                            Se ha registrado una nueva operación diaria:

                            - Empleado: {empleado.nombre_empleado} {empleado.apellido_empleado or ''}
                            - Proceso: {nombre_proceso} 
                            - Actividad: {nombre_actividad} 
                            - Orden de Producción: {codigo_op_a_mostrar}
                            - Cantidad Realizada: {cantidad}
                            - Fecha y Hora Inicio: {fecha_hora_inicio}
                            - Fecha y Hora Fin: {fecha_hora_fin}
                            - Pieza Realizada: {pieza_realizada if pieza_realizada else 'No especificada'}
                            - Novedades: {novedad if novedad else 'Sin novedades'}
                            - Registrado por: {session.get('name_surname', 'Usuario desconocido')}
    
                            Descripción:
                            {mensaje_personalizado if mensaje_personalizado else 'No se ha incluido un mensaje adicional.'}
    
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
                        else:
                            app.logger.warning(f"El empleado {destinatario.nombre_empleado} no tiene un correo electrónico registrado.")
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
            func.concat(Empleados.nombre_empleado, ' ', Empleados.apellido_empleado).label('empleado_nombre'),
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
                func.concat(Empleados.nombre_empleado, ' ', Empleados.apellido_empleado).ilike(f'%{empleado_filter}%'))

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
        # Corregido: operacion_obj ahora es el objeto Operaciones, no una tupla.
        operacion_obj = db.session.query(Operaciones).filter_by(id_operacion=id_operacion).first()

        if operacion_obj:
            # Obtener datos relacionados directamente del objeto operacion_obj
            empleado = operacion_obj.empleado
            proceso = operacion_obj.proceso_rel
            actividad = operacion_obj.actividad_rel
            orden = operacion_obj.orden_produccion
            
            # Obtener el usuario que registró la operación a través de la relación 'usuario_reg'
            usuario_que_registro = operacion_obj.usuario_reg
            nombre_usuario_registro = usuario_que_registro.name_surname if usuario_que_registro else 'Desconocido'

            return {
                'id_operacion': operacion_obj.id_operacion,
                'id_empleado': operacion_obj.id_empleado,
                'nombre_empleado': f"{empleado.nombre_empleado} {empleado.apellido_empleado or ''}".strip() if empleado else 'Desconocido',
                'proceso': proceso.nombre_proceso if proceso else 'Desconocido',
                'actividad': actividad.nombre_actividad if actividad else 'Desconocido',
                'codigo_op': orden.codigo_op if orden else 'Desconocido',
                'cantidad': operacion_obj.cantidad,
                'pieza_realizada': operacion_obj.pieza_realizada,
                'novedad': operacion_obj.novedad,
                'fecha_hora_inicio': operacion_obj.fecha_hora_inicio.strftime('%Y-%m-%d %H:%M') if operacion_obj.fecha_hora_inicio else 'Sin registro',
                'fecha_hora_fin': operacion_obj.fecha_hora_fin.strftime('%Y-%m-%d %H:%M') if operacion_obj.fecha_hora_fin else 'Sin registro',
                'fecha_registro': operacion_obj.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if operacion_obj.fecha_registro else 'Sin registro',
                'usuario_registro': nombre_usuario_registro
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
            operacion.id_empleado = int(data.form.get('id_empleado')) if data.form.get(
                'id_empleado') else operacion.id_empleado
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
ALLOWED_DOC_EXTENSIONS = {'png', 'jpg', 'jpeg','pdf', 'doc', 'docx', 'xls', 'xlsx'}
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
        # Lee más bytes para mejor detección
        detected_mime = mime.from_buffer(file.read(2048))
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
    errores = []
    id_usuario_registro = session.get('user_id')

    if not id_usuario_registro:
        app.logger.warning("Intento de procesar OP sin usuario autenticado.")
        return jsonify({'status': 'error', 'message': "Usuario no autenticado. Por favor, inicie sesión."}), 401

    # --- 1. Obtener y Validar Campos Principales de la OP ---
    # codigo_op_str = dataForm.get('cod_op') # Se generará automáticamente
    id_cliente_str = dataForm.get('id_cliente')
    cantidad_op_str = dataForm.get('cantidad')
    id_empleado_str = dataForm.get('id_empleado')
    id_supervisor_str = dataForm.get('id_supervisor')
    fecha_str = dataForm.get('fecha')
    fecha_entrega_str = dataForm.get('fecha_entrega')
    producto_val = dataForm.get('producto')
    version_val = dataForm.get('version', "1")
    cotizacion_val = dataForm.get('cotizacion')
    estado_val = dataForm.get('estado')
    medida_val = dataForm.get('medida')
    referencia_val = dataForm.get('referencia')
    odi_val = dataForm.get('odi')
    descripcion_general_op_val = dataForm.get('descripcion_general_op')
    empaque_val = dataForm.get('empaque')
    logistica_val = dataForm.get('logistica') # Obtener logística
    instructivo_val = dataForm.get('instructivo') 
    estado_proyecto_val = dataForm.get('estado_proyecto')
    urls_list = dataForm.getlist('urls[]') # Obtener lista de URLs
    
    # --- Obtener campos para la notificación ---
    action = dataForm.get('submit_action', 'save') # Por defecto es 'save'
    destinatarios_ids_str = dataForm.get('destinatarios')
    mensaje_personalizado = dataForm.get('mensaje_personalizado', '')

    if not id_cliente_str or not id_cliente_str.strip():
        errores.append("El Cliente es requerido.")
        id_cliente_val = None
    else:
        try:
            id_cliente_val = int(id_cliente_str)
            if not Clientes.query.filter_by(id_cliente=id_cliente_val, fecha_borrado=None).first():
                errores.append(f"Cliente con ID '{id_cliente_val}' no encontrado o fue eliminado.")
        except ValueError:
            errores.append("ID Cliente debe ser un número entero válido.")
            id_cliente_val = None

    if not cantidad_op_str or not cantidad_op_str.strip():
        errores.append("La Cantidad para la OP es requerida.")
        cantidad_op_val = None
    else:
        try:
            cantidad_op_val = int(cantidad_op_str)
            if cantidad_op_val <= 0:
                errores.append("La Cantidad para la OP debe ser un número positivo.")
        except ValueError:
            errores.append("Cantidad para la OP debe ser un número entero válido.")
            cantidad_op_val = None

    if not id_empleado_str or not id_empleado_str.strip():
        errores.append("El Empleado (vendedor/responsable) es requerido.")
        id_empleado_val = None
    else:
        try:
            id_empleado_val = int(id_empleado_str)
            if not Empleados.query.filter_by(id_empleado=id_empleado_val, fecha_borrado=None).first():
                errores.append(f"Empleado con ID '{id_empleado_val}' no encontrado o fue eliminado.")
        except ValueError:
            errores.append("ID Empleado debe ser un número entero válido.")
            id_empleado_val = None

    id_supervisor_val = None
    if id_supervisor_str and id_supervisor_str.strip():
        try:
            id_supervisor_val = int(id_supervisor_str)
            if not Empleados.query.filter_by(id_empleado=id_supervisor_val, fecha_borrado=None).first():
                errores.append(f"Supervisor con ID '{id_supervisor_val}' no encontrado o fue eliminado.")
        except ValueError:
            errores.append("ID Supervisor debe ser un número entero válido.")

    fecha_val = None
    if not fecha_str or not fecha_str.strip():
        errores.append("La Fecha de la OP es requerida.")
    else:
        try:
            fecha_val = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            errores.append("Formato de Fecha inválido (Use YYYY-MM-DD).")

    fecha_entrega_val = None
    if not fecha_entrega_str or not fecha_entrega_str.strip():
        errores.append("La Fecha de Entrega es requerida.")
    else:
        try:
            fecha_entrega_val = datetime.strptime(fecha_entrega_str, '%Y-%m-%d').date()
        except ValueError:
            errores.append("Formato de Fecha de Entrega inválido (Use YYYY-MM-DD).")

    if fecha_val and fecha_entrega_val and fecha_entrega_val < fecha_val:
        errores.append("La fecha de entrega no puede ser anterior a la fecha de la OP.")

    if not estado_val or not estado_val.strip():
        errores.append("El Estado de la OP es requerido.")
    if not odi_val or not odi_val.strip():
        errores.append("El ODI es requerido.")
    if not descripcion_general_op_val or not descripcion_general_op_val.strip():
        errores.append("La Descripción General de la OP es requerida.")
    
    if not producto_val or not producto_val.strip(): # Nueva validación para producto
        errores.append("El Producto es requerido.")

    # if not materiales_op_val or not materiales_op_val.strip(): # Eliminado
    #     errores.append("Los Materiales de la OP son requeridos.") # Eliminado

    # --- 2. Validación de Archivos ---
    basepath = os.path.abspath(os.path.dirname(__file__))
    static_base_path = os.path.normpath(os.path.join(basepath, '../static'))
    render_dir_abs = os.path.join(static_base_path, 'render_op')
    documentos_dir_abs = os.path.join(static_base_path, 'documentos_op')
    os.makedirs(render_dir_abs, exist_ok=True)
    os.makedirs(documentos_dir_abs, exist_ok=True)

    render_file_storage = files.get('render')
    path_render_a_guardar = None
    if render_file_storage and render_file_storage.filename:
        valido, nombre_archivo_o_msg = procesar_imagen_perfil(render_file_storage, 'render_op', ALLOWED_RENDER_EXTENSIONS)
        if not valido:
            errores.append(f"Render: {nombre_archivo_o_msg}")
        elif nombre_archivo_o_msg:
            path_render_a_guardar = nombre_archivo_o_msg

    documentos_a_guardar = []
    documentos_adjuntos_files = files.getlist('documentos')
    for doc_file_storage in documentos_adjuntos_files:
        if doc_file_storage and doc_file_storage.filename:
            valido, nombre_archivo_o_msg = procesar_imagen_perfil(doc_file_storage, 'documentos_op', ALLOWED_DOC_EXTENSIONS)
            if not valido:
                errores.append(f"Documento '{secure_filename(doc_file_storage.filename)}': {nombre_archivo_o_msg}")
            elif nombre_archivo_o_msg:
                documentos_a_guardar.append({
                    "path": os.path.basename(nombre_archivo_o_msg),
                    "nombre_original": secure_filename(doc_file_storage.filename)
                })

    # --- 3. Validación de Piezas Dinámicas ---
    piezas_lista_form = []
    piezas_json_str = dataForm.get('piezas')
    app.logger.debug(f"Contenido del campo 'piezas' (datos de piezas) recibido del formulario: '{piezas_json_str}'")

    if piezas_json_str and piezas_json_str.strip() and piezas_json_str.lower() != 'undefined' and piezas_json_str.lower() != 'null':
        try:
            parsed_data = json.loads(piezas_json_str)
            if isinstance(parsed_data, list):
                piezas_lista_form = parsed_data
                if not piezas_lista_form:
                    app.logger.info("piezas se parseó a una lista vacía. OP se creará sin piezas si otras validaciones pasan.")
                    # errores.append("Debe agregar al menos una pieza a la Orden de Producción.")  # Descomentar si es obligatorio
            else:
                errores.append("El formato de los datos de piezas no es una lista como se esperaba.")
                app.logger.warning(f"piezas ('{piezas_json_str}') se parseó a un tipo no esperado: {type(parsed_data)}")
        except json.JSONDecodeError:
            errores.append("Error al decodificar los datos de las piezas (formato JSON inválido).")
            app.logger.warning(f"JSONDecodeError al parsear piezas: '{piezas_json_str}'")
    else:
        app.logger.info("No se proporcionaron datos en piezas o estaba vacío/nulo/undefined. OP se creará sin piezas si otras validaciones pasan.")
        # errores.append("Debe agregar al menos una pieza a la Orden de Producción.")  # Descomentar si es obligatorio

    if not errores and piezas_lista_form:
        for idx, pieza_data_form in enumerate(piezas_lista_form, 1):
            id_pieza_maestra = pieza_data_form.get('id_pieza_maestra')
            cantidad_pieza_str = str(pieza_data_form.get('cantidad', ''))
            id_actividades = pieza_data_form.get('id_actividad', [])
            nombre_pieza_val = pieza_data_form.get('nombre_pieza', 'N/A')

            if not id_pieza_maestra or not str(id_pieza_maestra).strip():
                errores.append(f"Pieza #{idx}: El ID de la pieza maestra es requerido.")
            else:
                try:
                    id_pieza_maestra = int(id_pieza_maestra)
                    pieza_db = Piezas.query.filter_by(id_pieza=id_pieza_maestra, fecha_borrado=None).first()
                    if not pieza_db:
                        errores.append(f"Pieza #{idx}: ID de pieza maestra '{id_pieza_maestra}' no encontrado.")
                    else:
                        nombre_pieza_val = pieza_db.nombre_pieza
                except ValueError:
                    errores.append(f"Pieza #{idx}: ID de pieza maestra inválido.")
                    id_pieza_maestra = None

            if not cantidad_pieza_str.isdigit() or int(cantidad_pieza_str) <= 0:
                errores.append(f"Pieza #{idx} ('{nombre_pieza_val}'): Cantidad es requerida y debe ser un número positivo.")

    # --- 4. Manejo de Errores Tempranos ---
    if errores:
        app.logger.warning(f"Errores de validación en procesar_form_op: {', '.join(errores)}")
        return jsonify({'status': 'error', 'message': ". ".join(errores) + "."}), 400

    # --- 4.5 Validación de Procesos Globales de la OP ---
    op_ids_procesos_form = dataForm.getlist('op_ids_procesos') # Usar getlist para campos multiple
    op_otro_proceso_val = dataForm.get('op_otro_proceso', '').strip()
    ids_procesos_a_asociar = []

    if not op_ids_procesos_form and not op_otro_proceso_val:
        errores.append("Debe seleccionar al menos un proceso global para la OP o especificar uno nuevo.")
    else:
        for id_proc_str in op_ids_procesos_form:
            if id_proc_str == 'otro_proceso_custom_op':
                if not op_otro_proceso_val:
                    errores.append("Seleccionó 'Otro Proceso' pero no especificó el nombre del nuevo proceso global.")
                else:
                    # Intentar encontrar o crear el "otro proceso"
                    proceso_existente = Procesos.query.filter(func.lower(Procesos.nombre_proceso) == func.lower(op_otro_proceso_val), Procesos.fecha_borrado.is_(None)).first()
                    if proceso_existente:
                        ids_procesos_a_asociar.append(proceso_existente.id_proceso)
                    else:
                        # Crear nuevo proceso si no existe
                        try:
                            # Generar un código único si es necesario, o pedirlo en el form
                            # Aquí asumimos que el nombre es suficiente para buscar/crear y el código se puede autogenerar o manejar de otra forma
                            # Para este ejemplo, si no hay un sistema de codificación claro para "otros", lo dejamos simple.
                            # Considerar una lógica más robusta para códigos de procesos creados dinámicamente.
                            # Por ahora, si el nombre es único, el código podría ser similar o requerir un manejo especial.
                            # Para simplificar, vamos a asumir que el nombre del proceso es lo principal aquí.
                            # Y que el código podría ser algo como "OTRO_" + nombre normalizado.
                            # Esta parte puede necesitar ajustes según las reglas de negocio para códigos de proceso.
                            
                            # Verificamos si ya existe un proceso con ese nombre (insensible a mayúsculas/minúsculas)
                            proceso_check_nombre = Procesos.query.filter(func.lower(Procesos.nombre_proceso) == func.lower(op_otro_proceso_val)).first()
                            if proceso_check_nombre:
                                ids_procesos_a_asociar.append(proceso_check_nombre.id_proceso)
                            else:
                                # Crear un código simple para el nuevo proceso "otro"
                                # Esto es una simplificación, idealmente el sistema de códigos debería ser más robusto
                                codigo_nuevo_proceso_otro = f"OTRO_{uuid.uuid4().hex[:8].upper()}"
                                nuevo_proceso_otro = Procesos(
                                    codigo_proceso=codigo_nuevo_proceso_otro, # Asegurar que sea único
                                    nombre_proceso=op_otro_proceso_val,
                                    descripcion_proceso=f"Proceso '{op_otro_proceso_val}' creado desde OP."
                                )
                                db.session.add(nuevo_proceso_otro)
                                db.session.flush() # Para obtener el ID del nuevo proceso
                                ids_procesos_a_asociar.append(nuevo_proceso_otro.id_proceso)
                                app.logger.info(f"Nuevo proceso global '{op_otro_proceso_val}' (ID: {nuevo_proceso_otro.id_proceso}) creado y añadido a la OP.")
                        except IntegrityError: # Podría ocurrir si el código generado no es único
                            db.session.rollback()
                            errores.append(f"Error al intentar crear el nuevo proceso global '{op_otro_proceso_val}'. Intente con un nombre o código diferente si el problema persiste.")
                            app.logger.error(f"IntegrityError al crear nuevo proceso global '{op_otro_proceso_val}'.")
                        except Exception as e_proc_otro:
                            db.session.rollback()
                            errores.append(f"Error inesperado al procesar 'Otro Proceso Global': {str(e_proc_otro)}")
                            app.logger.error(f"Error al procesar 'Otro Proceso Global': {str(e_proc_otro)}")
            else:
                try:
                    id_proc = int(id_proc_str)
                    proceso_db = Procesos.query.filter_by(id_proceso=id_proc, fecha_borrado=None).first()
                    if proceso_db:
                        if id_proc not in ids_procesos_a_asociar: # Evitar duplicados si se seleccionó y también se escribió como "otro"
                           ids_procesos_a_asociar.append(id_proc)
                    else:
                        errores.append(f"Proceso global con ID '{id_proc_str}' no encontrado o fue eliminado.")
                except ValueError:
                    errores.append(f"ID de proceso global inválido: '{id_proc_str}'.")
        
        if not ids_procesos_a_asociar and not errores: # Si después de procesar 'otro' no hay IDs y no hubo errores antes
             if 'otro_proceso_custom_op' in op_ids_procesos_form and not op_otro_proceso_val:
                # Este caso ya está cubierto arriba, pero por si acaso.
                pass # El error ya fue agregado
             elif not op_ids_procesos_form or all(p == 'otro_proceso_custom_op' for p in op_ids_procesos_form) and not op_otro_proceso_val:
                 errores.append("Debe seleccionar procesos válidos o especificar un nuevo proceso global.")


    # --- RE-CHEQUEO DE ERRORES DESPUÉS DE PROCESOS GLOBALES ---
    if errores:
        app.logger.warning(f"Errores de validación (incluyendo procesos globales) en procesar_form_op: {', '.join(errores)}")
        # Limpiar archivos subidos si hay errores para no dejarlos huérfanos
        if path_render_a_guardar and os.path.exists(os.path.join(static_base_path, path_render_a_guardar.replace('static/', ''))):
            os.remove(os.path.join(static_base_path, path_render_a_guardar.replace('static/', '')))
        for doc_info_err in documentos_a_guardar:
            if os.path.exists(os.path.join(static_base_path, doc_info_err["path"].replace('static/', ''))):
                os.remove(os.path.join(static_base_path, doc_info_err["path"].replace('static/', '')))
        return jsonify({'status': 'error', 'message': ". ".join(errores) + "."}), 400

    # --- 5. Iniciar Transacción y Crear Registros ---
    try:
        nuevo_codigo_op_generado = generar_codigo_op() # Generar el nuevo código OP
        app.logger.info(f"Nuevo Código OP generado: {nuevo_codigo_op_generado}")

        orden = OrdenProduccion(
            codigo_op=nuevo_codigo_op_generado,
            id_cliente=id_cliente_val,
            producto=producto_val,
            version=version_val,
            cotizacion=cotizacion_val,
            estado=estado_val,
            cantidad=cantidad_op_val,
            medida=medida_val,
            referencia=referencia_val,
            odi=odi_val,
            id_empleado=id_empleado_val,
            id_supervisor=id_supervisor_val,
            fecha=fecha_val,
            fecha_entrega=fecha_entrega_val,
            descripcion_general=descripcion_general_op_val, # Punto común de error, verificar este nombre
            empaque=empaque_val,
            logistica=logistica_val,
            instructivo=instructivo_val,
            estado_proyecto=estado_proyecto_val,
            id_usuario_registro=id_usuario_registro
        )
        db.session.add(orden)
        db.session.flush()

        if path_render_a_guardar:
            nuevo_render = RendersOP(id_op=orden.id_op, render_path=path_render_a_guardar)
            db.session.add(nuevo_render)

        for doc_info in documentos_a_guardar:
            nuevo_documento = DocumentosOP(
                id_op=orden.id_op,
                documento_path=doc_info["path"],
                documento_nombre_original=doc_info["nombre_original"]
            )
            db.session.add(nuevo_documento)

        # Guardar URLs asociadas a la OP
        for url_item in urls_list:
            if url_item and url_item.strip(): # Solo guardar URLs no vacías
                nueva_url_op = OrdenProduccionURLs(id_op=orden.id_op, url=url_item.strip())
                db.session.add(nueva_url_op)
 
        for pieza_data_form in piezas_lista_form:
            id_pieza_maestra = int(pieza_data_form.get('id_pieza_maestra'))
            nombre_pieza_val = pieza_data_form.get('nombre_pieza', 'N/A')
            cantidad_pieza_val = int(pieza_data_form.get('cantidad'))
            id_actividades = pieza_data_form.get('id_actividad', [])
            valores_configuracion_pieza = pieza_data_form.get('valores_configuracion', []) # Obtener los detalles del modal
            especificaciones_pieza_data = pieza_data_form.get('especificaciones_pieza', []) # Obtener los datos de especificaciones

            orden_pieza_obj = OrdenPiezas(
                id_op=orden.id_op,
                id_pieza=id_pieza_maestra, # Este es el ID de la pieza maestra de tbl_piezas
                nombre_pieza_op=nombre_pieza_val, # Nombre específico para esta OP
                cantidad=cantidad_pieza_val,
                tamano=pieza_data_form.get('tamano'),
                montaje=pieza_data_form.get('montaje'),
                montaje_tamano=pieza_data_form.get('tamano_montaje'), # Este campo ya existía en OrdenPiezas
                material=pieza_data_form.get('material'),
                cantidad_material=pieza_data_form.get('cantidad_material'),
                ancho=float(pieza_data_form.get('ancho')) if pieza_data_form.get('ancho') else None,
                alto=float(pieza_data_form.get('alto')) if pieza_data_form.get('alto') else None,
                fondo=float(pieza_data_form.get('fondo')) if pieza_data_form.get('fondo') else None,
                proveedor_externo=pieza_data_form.get('proveedor_externo'),
                descripcion_pieza=pieza_data_form.get('descripcion_pieza'),
                tipo_molde=pieza_data_form.get('tipo_molde')
            )
            db.session.add(orden_pieza_obj)
            db.session.flush() # Para obtener el id_orden_pieza para las tablas relacionadas

            # Guardar actividades de la pieza
            for id_actividad in id_actividades:
                try:
                    id_actividad_int = int(id_actividad)
                    db.session.add(OrdenPiezasActividades(
                        id_orden_pieza=orden_pieza_obj.id_orden_pieza,
                        id_actividad=id_actividad_int
                    ))
                except ValueError:
                    app.logger.warning(f"ID de actividad no válido '{id_actividad}' ignorado para pieza con nombre '{nombre_pieza_val}'.")

            # Guardar los valores de configuración adicionales del modal para esta pieza
            if isinstance(valores_configuracion_pieza, list):
                for config_item in valores_configuracion_pieza:
                    grupo = config_item.get('grupo_configuracion')
                    valor = config_item.get('valor_configuracion')
                    if grupo and valor is not None: # Permitir valores vacíos si es intencional, pero el grupo debe existir
                        detalle_obj = OrdenPiezaValoresDetalle(
                            id_orden_pieza=orden_pieza_obj.id_orden_pieza,
                            grupo_configuracion=grupo,
                            valor_configuracion=str(valor) # Asegurar que sea string
                        )
                        db.session.add(detalle_obj)
            else:
                app.logger.warning(f"El formato de 'valores_configuracion' para la pieza '{nombre_pieza_val}' no es una lista. Datos: {valores_configuracion_pieza}")

            # Guardar las especificaciones de la pieza
            if isinstance(especificaciones_pieza_data, list):
                for esp_item in especificaciones_pieza_data:
                    # Convertir valores numéricos, manejando None o strings vacíos
                    largo_val = float(esp_item.get('largo')) if esp_item.get('largo') else None
                    ancho_val = float(esp_item.get('ancho')) if esp_item.get('ancho') else None
                    cantidad_esp_val = int(esp_item.get('cantidad')) if esp_item.get('cantidad') else None
                    kg_val = float(esp_item.get('kg')) if esp_item.get('kg') else None
                    retal_kg_val = float(esp_item.get('retal_kg')) if esp_item.get('retal_kg') else None
                    
                    especificacion_obj = OrdenPiezaEspecificaciones(
                        id_orden_pieza=orden_pieza_obj.id_orden_pieza,
                        item=esp_item.get('item'),
                        calibre=esp_item.get('calibre'),
                        largo=largo_val,
                        ancho=ancho_val,                        
                        unidad=esp_item.get('unidad'),
                        cantidad_especificacion=cantidad_esp_val,
                        kg=kg_val,
                        retal_kg=retal_kg_val,
                        reproceso=esp_item.get('reproceso')
                    )
                    db.session.add(especificacion_obj)
            else:
                app.logger.warning(f"El formato de 'especificaciones_pieza' para la pieza '{nombre_pieza_val}' no es una lista. Datos: {especificaciones_pieza_data}")

        # Asociar Procesos Globales a la Orden de Producción
        for id_proc_asoc in ids_procesos_a_asociar:
            # Verificar si la asociación ya existe para evitar duplicados por si acaso
            # (aunque la lógica anterior debería prevenirlo, es una salvaguarda)
            existe_asociacion = db.session.query(OrdenProduccionProcesos).filter_by(id_op=orden.id_op, id_proceso=id_proc_asoc).first()
            if not existe_asociacion:
                nueva_asociacion_op_proceso = OrdenProduccionProcesos(id_op=orden.id_op, id_proceso=id_proc_asoc)
                db.session.add(nueva_asociacion_op_proceso)
            else:
                app.logger.info(f"Asociación OP-Proceso (ID_OP: {orden.id_op}, ID_Proceso: {id_proc_asoc}) ya existía. No se duplicó.")
        
        db.session.commit()
        app.logger.info(f"Orden de Producción {orden.codigo_op} (ID: {orden.id_op}) registrada exitosamente, incluyendo procesos globales y piezas.")
        
        
        # --- INICIO: LÓGICA DE NOTIFICACIÓN (SIN CAMBIOS) ---
        if action == 'save_and_notify':
            app.logger.info(f"Iniciando notificación por correo para OP {orden.codigo_op}.")
            if not destinatarios_ids_str:
                app.logger.warning('Acción "save_and_notify" pero no se proporcionaron destinatarios.')
            else:
                try:
                    destinatarios_ids = [int(id) for id in destinatarios_ids_str.split(',')]
                    destinatarios = db.session.query(Users).filter(Users.id.in_(destinatarios_ids)).all()
                    cliente = db.session.query(Clientes).get(id_cliente_val)
                    vendedor = db.session.query(Empleados).get(orden.id_empleado)
                    supervisor = db.session.query(Empleados).get(orden.id_supervisor) if orden.id_supervisor else None
                    email_sender = 'evolutioncontrolweb@gmail.com'
                    email_password = 'qsmr ccyb yzjd gzkm'

                    for destinatario in destinatarios:
                        # Usamos el campo 'email_user' de tu modelo Users
                        if destinatario.email_user: 
                            subject = f'Nueva Orden de Producción Registrada: {orden.codigo_op}'
                            body = f"""
                            Hola {destinatario.name_surname},

                            Se ha registrado una nueva Orden de Producción:

                            - Número de OP: {orden.codigo_op}
                            - Cliente: {cliente.nombre_cliente}
                            - Producto: {orden.producto}
                            - Fecha de Entrega: {orden.fecha_entrega.strftime('%d de %B de %Y')}
                            - ODI: {orden.odi}
                            - Cotización: {orden.cotizacion}
                            - Vendedor: {vendedor.nombre_empleado +' '+ vendedor.apellido_empleado if vendedor else 'N/A'}
                            - Supervisor: {supervisor.nombre_empleado if supervisor else 'No asignado'}
                            - Version : {orden.version}

                            Descripción:
                            {orden.descripcion_general}

                            ---
                            Mensaje Adicional:
                            {mensaje_personalizado if mensaje_personalizado else 'No se incluyó un mensaje adicional.'}
                            ---

                            Este es un mensaje automático.
                            """
                            em = EmailMessage()
                            em['From'] = email_sender
                            em['To'] = destinatario.email_user   # <-- CORREGIDO
                            em['Subject'] = subject
                            em.set_content(body)

                            context = ssl.create_default_context()
                            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                                smtp.login(email_sender, email_password)
                                smtp.send_message(em)
                            
                            # Logueamos el correo correcto al que se envió
                            app.logger.info(f'Correo de OP {orden.codigo_op} notificado a {destinatario.email_user}')
                except Exception as e:
                    app.logger.error(f"FALLO al enviar correos de notificación para OP {orden.codigo_op}: {str(e)}")
        # --- FIN: LÓGICA DE NOTIFICACIÓN ---
        
        
        mensaje_exito = f"Se creó el número de OP {orden.codigo_op} exitosamente."
        return jsonify({'status': 'success', 'message': mensaje_exito, 'id_op': orden.id_op, 'redirect_url': url_for('lista_op', id_op=orden.id_op)}), 200

    except IntegrityError as ie:
        db.session.rollback()
        app.logger.error(f"Error de Integridad de BD en procesar_form_op: {str(ie)}", exc_info=True)
        error_message = "Error de base de datos. Es posible que un valor único ya exista."
        return jsonify({'status': 'error', 'message': error_message}), 409

    except SQLAlchemyError as e_sql:
        db.session.rollback()
        app.logger.error(f"Error de SQLAlchemy en procesar_form_op: {str(e_sql)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Error al interactuar con la base de datos.'}), 500

    except Exception as e_inesperado:
        db.session.rollback()
        # MEJORA: Este log ahora te mostrará el error exacto en la consola de Flask
        app.logger.error(f"Error inesperado en procesar_form_op: {str(e_inesperado)}", exc_info=True)
        # MEJORA: Devolvemos el error específico para poder depurar mejor desde el frontend si es necesario
        return jsonify({'status': 'error', 'message': f'Ocurrió un error inesperado en el servidor: {str(e_inesperado)}'}), 500


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


def sql_lista_op_bd(draw=1, start=0, length=10, search_codigo_op=None, search_fecha=None, search_nombre_cliente=None):
    try:
        # Construir la consulta base
        query = db.session.query(OrdenProduccion).join(Clientes, OrdenProduccion.id_cliente == Clientes.id_cliente).filter(
            OrdenProduccion.fecha_borrado.is_(None))

        # Filtrar por código de OP si se proporciona
        if search_codigo_op:
            query = query.filter(
                OrdenProduccion.codigo_op.ilike(f"%{search_codigo_op}%"))
        
        # Filtrar por nombre de cliente si se proporciona
        if search_nombre_cliente:
            query = query.filter(
                Clientes.nombre_cliente.ilike(f"%{search_nombre_cliente}%"))

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


def sql_detalles_op_bd(codigo_op):
    try:
        # Crear alias para las dos instancias de Empleados
        empleado_vendedor = aliased(Empleados)
        empleado_supervisor = aliased(Empleados)

        # Consulta con JOINs para obtener los nombres relacionados
        result = db.session.query(
            OrdenProduccion,
            Clientes.nombre_cliente.label('nombre_cliente'),
            db.func.concat(empleado_vendedor.nombre_empleado, ' ', empleado_vendedor.apellido_empleado).label('nombre_completo_vendedor'),
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
            OrdenProduccion.codigo_op == codigo_op,
            OrdenProduccion.fecha_borrado.is_(None)
        ).first()

        if not result:
            app.logger.warning(f"No se encontró la orden de producción con id_op={id_op}")
            return None

        orden_obj, nombre_cliente, nombre_completo_vendedor, nombre_supervisor, nombre_usuario_registro = result

        # 1. Procesos Globales de la Orden
        procesos_globales_nombres = []
        if orden_obj.procesos_globales: # Accede a la relación directa
            procesos_globales_nombres = [p.nombre_proceso for p in orden_obj.procesos_globales]
        app.logger.debug(f"Procesos globales para OP {orden_obj.id_op}: {procesos_globales_nombres}")

        # 2. Piezas de la Orden
        # La consulta original para 'piezas' ya obtiene OrdenPiezas y el nombre de la pieza maestra.
        # Vamos a iterar sobre los objetos OrdenPiezas directamente.
        piezas_query_result = db.session.query(
            OrdenPiezas,
            Piezas.nombre_pieza.label('nombre_pieza_maestra') # Nombre de la pieza desde tbl_piezas
        ).outerjoin(
            Piezas, OrdenPiezas.id_pieza == Piezas.id_pieza # id_pieza es la FK a tbl_piezas
        ).filter(
            OrdenPiezas.id_op == orden_obj.id_op,
            OrdenPiezas.fecha_borrado.is_(None)
        ).all()

        piezas_list = []
        for pieza_orden_obj, nombre_pieza_maestra_val in piezas_query_result: # pieza_orden_obj es una instancia de OrdenPiezas
            # 2a. Actividades de la Pieza
            actividades_nombres = []
            # Asumiendo que OrdenPiezas tiene una relación 'actividades_asignadas' que lleva a OrdenPiezasActividades
            # y esta a su vez a Actividades. O una consulta directa:
            actividades_data = db.session.query(Actividades.nombre_actividad).\
                join(OrdenPiezasActividades, Actividades.id_actividad == OrdenPiezasActividades.id_actividad).\
                filter(OrdenPiezasActividades.id_orden_pieza == pieza_orden_obj.id_orden_pieza).all()
            if actividades_data:
                actividades_nombres = [a[0] for a in actividades_data]
            app.logger.debug(f"Actividades para pieza {pieza_orden_obj.id_orden_pieza}: {actividades_nombres}")

            # 2b. Detalles de Configuración Adicional de la Pieza
            detalles_config_list = []
            if pieza_orden_obj.valores_config_adicional: # Relación en OrdenPiezas
                for config_detalle in pieza_orden_obj.valores_config_adicional:
                    detalles_config_list.append({
                        'grupo': config_detalle.grupo_configuracion,
                        'valor': config_detalle.valor_configuracion
                    })
            app.logger.debug(f"Detalles config para pieza {pieza_orden_obj.id_orden_pieza}: {detalles_config_list}")

            # 2c. Especificaciones de la Pieza
            especificaciones_list = []
            if pieza_orden_obj.especificaciones: # Relación en OrdenPiezas
                for esp in pieza_orden_obj.especificaciones:
                    especificaciones_list.append({
                        'item': esp.item,
                        'calibre': esp.calibre,
                        'largo': str(esp.largo) if esp.largo is not None else None, # Convertir Decimal a str                        
                        'ancho': str(esp.ancho) if esp.ancho is not None else None, # Convertir Decimal a str
                        'unidad': esp.unidad,                        
                        'cantidad_especificacion': esp.cantidad_especificacion,
                        'kg': str(esp.kg) if esp.kg is not None else None, # Convertir Decimal a str
                        'retal_kg': str(esp.retal_kg) if esp.retal_kg is not None else None, # Convertir Decimal a str
                        'reproceso': esp.reproceso
                    })
            app.logger.debug(f"Especificaciones para pieza {pieza_orden_obj.id_orden_pieza}: {especificaciones_list}")
            
            # Determinar el nombre de la pieza a mostrar
            # Priorizar el nombre específico de la OP, luego el de la pieza maestra si existe.
            nombre_a_mostrar = pieza_orden_obj.nombre_pieza_op # Nombre específico guardado con la pieza de la OP
            if not nombre_a_mostrar and nombre_pieza_maestra_val:
                 nombre_a_mostrar = nombre_pieza_maestra_val
            elif not nombre_a_mostrar:
                 nombre_a_mostrar = "Pieza sin nombre específico"


            piezas_list.append({
                'id_orden_pieza': pieza_orden_obj.id_orden_pieza,
                'nombre_pieza': nombre_a_mostrar,
                'cantidad': pieza_orden_obj.cantidad if pieza_orden_obj.cantidad else '',
                'tamano': pieza_orden_obj.tamano if pieza_orden_obj.tamano else '',
                'montaje': pieza_orden_obj.montaje if pieza_orden_obj.montaje else '',
                'montaje_tamano': pieza_orden_obj.montaje_tamano if pieza_orden_obj.montaje_tamano else '',
                'material': pieza_orden_obj.material if pieza_orden_obj.material else '',
                'cantidad_material': pieza_orden_obj.cantidad_material if pieza_orden_obj.cantidad_material else '',
                'ancho_pieza': str(pieza_orden_obj.ancho) if pieza_orden_obj.ancho is not None else '', # Nuevo
                'alto_pieza': str(pieza_orden_obj.alto) if pieza_orden_obj.alto is not None else '',   # Nuevo
                'fondo_pieza': str(pieza_orden_obj.fondo) if pieza_orden_obj.fondo is not None else '', # Nuevo
                'proveedor_externo': pieza_orden_obj.proveedor_externo if pieza_orden_obj.proveedor_externo else '', # Nuevo
                'descripcion_general': pieza_orden_obj.descripcion_pieza if pieza_orden_obj.descripcion_pieza else '',
                'tipo_molde': pieza_orden_obj.tipo_molde if pieza_orden_obj.tipo_molde else '', # Nuevo
                'actividades': actividades_nombres if actividades_nombres else [''],
                'detalles_configuracion': detalles_config_list,
                'especificaciones': especificaciones_list # Nuevo
            })
 
        # Renders y Documentos
        renders = [render.render_path.split('/')[-1] for render in orden_obj.renders if render.fecha_borrado is None]
        documentos = [{
            'id_documento': doc.id_documento, # Añadido por si es útil en el template
            'documento_path': doc.documento_path,
            'documento_nombre_original': doc.documento_nombre_original
        } for doc in orden_obj.documentos if doc.fecha_borrado is None]
        
        # URLs de la OP
        urls_op_list = [url_obj.url for url_obj in orden_obj.urls_op]
 
        # Formatear los datos de la orden para el template
        detalle_op_data = {
            'id_op': orden_obj.id_op,
            'codigo_op': orden_obj.codigo_op,
            'id_cliente': orden_obj.id_cliente, # Añadido por si es útil
            'nombre_cliente': nombre_cliente if nombre_cliente else 'Desconocido',
            'producto': orden_obj.producto if orden_obj.producto else 'Sin descripción',
            'version': orden_obj.version if orden_obj.version else '',
            'cotizacion': orden_obj.cotizacion if orden_obj.cotizacion else '',
            'estado': orden_obj.estado if orden_obj.estado else 'Sin estado',
            'cantidad': orden_obj.cantidad if orden_obj.cantidad else 0,
            'medida': orden_obj.medida if orden_obj.medida else '',
            'referencia': orden_obj.referencia if orden_obj.referencia else '',
            'odi': orden_obj.odi if orden_obj.odi else 'Sin ODI',
            'id_empleado': orden_obj.id_empleado, # Añadido por si es útil (Vendedor)
            'empleado': nombre_completo_vendedor if nombre_completo_vendedor else 'Sin vendedor', # Nombre del Vendedor
            'id_supervisor': orden_obj.id_supervisor, # Añadido por si es útil
            'nombre_supervisor': nombre_supervisor if nombre_supervisor else 'Sin supervisor',
            'fecha': orden_obj.fecha.strftime('%Y-%m-%d') if orden_obj.fecha else '',
            'fecha_entrega': orden_obj.fecha_entrega.strftime('%Y-%m-%d') if orden_obj.fecha_entrega else '',
            'descripcion_general': orden_obj.descripcion_general if orden_obj.descripcion_general else '',
            'empaque': orden_obj.empaque if orden_obj.empaque else '',
            'logistica': orden_obj.logistica if orden_obj.logistica else '', # Nuevo
            'instructivo': orden_obj.instructivo if orden_obj.instructivo else '', # Nuevo
            'estado_proyecto': orden_obj.estado_proyecto if orden_obj.estado_proyecto else '', # Nuevo
            'materiales': orden_obj.materiales if orden_obj.materiales else '', # Materiales generales de la OP
            'fecha_registro': orden_obj.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if orden_obj.fecha_registro else 'Sin registro',
            'id_usuario_registro': orden_obj.id_usuario_registro, # Añadido por si es útil
            'usuario_registro': nombre_usuario_registro if nombre_usuario_registro else 'Desconocido',
            'fecha_borrado': orden_obj.fecha_borrado.strftime('%Y-%m-%d %I:%M %p') if orden_obj.fecha_borrado else None, # Formatear si existe
            'renders': renders,
            'documentos': documentos,
            'urls_op': urls_op_list, # Nuevo
            'procesos': procesos_globales_nombres if procesos_globales_nombres else ['s'], # Clave 'procesos' para el template
            'piezas': piezas_list
        }
        app.logger.debug(f"Detalles de la orden a retornar: {detalle_op_data}")
        return detalle_op_data

    except Exception as e:
        app.logger.error(f"Error en la función sql_detalles_op_bd para id_op={id_op}: {str(e)}", exc_info=True) # exc_info=True para traceback completo
        return None

def obtener_datos_op_para_edicion(codigo_op):
    try:
        # Obtener la OP con todas las relaciones necesarias
        orden = OrdenProduccion.query.options(
            joinedload(OrdenProduccion.cliente),
            joinedload(OrdenProduccion.empleado),
            joinedload(OrdenProduccion.supervisor),
            joinedload(OrdenProduccion.procesos_globales),
            joinedload(OrdenProduccion.renders),
            joinedload(OrdenProduccion.documentos),
            joinedload(OrdenProduccion.orden_piezas).options(
                joinedload(OrdenPiezas.pieza),
                joinedload(OrdenPiezas.valores_config_adicional),
                joinedload(OrdenPiezas.actividades),
                joinedload(OrdenPiezas.especificaciones) # Cargar especificaciones
            )
        ).filter_by(codigo_op=codigo_op, fecha_borrado=None).first()

        if not orden:
            app.logger.warning(f"Orden de Producción con código {codigo_op} no encontrada.")
            return {'status': 'error', 'message': 'Orden de Producción no encontrada.'}, 404

        # Formatear datos para la plantilla
        op_data = {
            'id_op': orden.id_op,
            'codigo_op': orden.codigo_op,
            'id_cliente': orden.id_cliente,
            'cliente': {
                'nombre_cliente': orden.cliente.nombre_cliente if orden.cliente else 'N/A'
            },
            'producto': orden.producto or '',
            'version': orden.version or '1',
            'cotizacion': orden.cotizacion or '',
            'estado': orden.estado or '',
            'cantidad': orden.cantidad or 0,
            'medida': orden.medida or '',
            'referencia': orden.referencia or '',
            'odi': orden.odi or '',
            'id_empleado': orden.id_empleado,
            'empleado': {
                'nombre_empleado': orden.empleado.nombre_empleado if orden.empleado else '',
                'apellido_empleado': orden.empleado.apellido_empleado if orden.empleado else ''
            },
            'id_supervisor': orden.id_supervisor,
            'supervisor': {
                'nombre_empleado': orden.supervisor.nombre_empleado if orden.supervisor else '',
                'apellido_empleado': orden.supervisor.apellido_empleado if orden.supervisor else ''
            },
            'fecha': orden.fecha.strftime('%Y-%m-%d') if orden.fecha else '',
            'fecha_entrega': orden.fecha_entrega.strftime('%Y-%m-%d') if orden.fecha_entrega else '',
            'descripcion_general': orden.descripcion_general or '',
            'empaque': orden.empaque or '',
            'logistica': orden.logistica or '', # Añadir logística
            'instructivo': orden.instructivo or '', # Añadir logística
            'materiales': orden.materiales or '',
            'estado_proyecto': orden.estado_proyecto or '',
            'procesos_globales': [
                {'id_proceso': p.id_proceso, 'nombre_proceso': p.nombre_proceso}
                for p in orden.procesos_globales
            ],
            'op_otro_proceso': next((p.nombre_proceso for p in orden.procesos_globales if 'OTRO_' in p.nombre_proceso), ''),
            'renders': [r.render_path.split('/')[-1] for r in orden.renders if r.fecha_borrado is None],
            'documentos': [
                {
                    'id_documento': d.id_documento,
                    'documento_path': d.documento_path,
                    'documento_nombre_original': d.documento_nombre_original
                }
                for d in orden.documentos
            ],
            'urls_op': [url.url for url in orden.urls_op if url.url], # Añadir URLs
            'orden_piezas': [
                {
                    'id_orden_pieza': p.id_orden_pieza,
                    'id_pieza': p.id_pieza,
                    'pieza': {'nombre_pieza': p.pieza.nombre_pieza if p.pieza else 'N/A'},
                    'nombre_pieza_op': p.nombre_pieza_op or 'N/A',
                    'cantidad': p.cantidad or 0,
                    'tamano': p.tamano or '',
                    'montaje': p.montaje or '',
                    'montaje_tamano': p.montaje_tamano or '',
                    'material': p.material or '',
                    'cantidad_material': p.cantidad_material or '',
                    'ancho_pieza': str(p.ancho) if p.ancho is not None else None,
                    'alto_pieza': str(p.alto) if p.alto is not None else None,
                    'fondo_pieza': str(p.fondo) if p.fondo is not None else None,
                    'proveedor_externo': p.proveedor_externo or '',
                    'descripcion_pieza': p.descripcion_pieza or '',
                    'tipo_molde': p.tipo_molde or '',
                    'actividades': [
                        {'id_actividad': a.id_actividad, 'nombre_actividad': a.nombre_actividad}
                        for a in p.actividades
                    ],
                    'valores_config_adicional': [
                        {'grupo_configuracion': v.grupo_configuracion, 'valor_configuracion': v.valor_configuracion}
                        for v in p.valores_config_adicional
                    ],
                    'especificaciones': [
                        {
                            'item': esp.item,
                            'calibre': esp.calibre,
                            'largo': str(esp.largo) if esp.largo is not None else None,                            
                            'ancho': str(esp.ancho) if esp.ancho is not None else None,
                            'unidad': esp.unidad,
                            'cantidad_especificacion': esp.cantidad_especificacion,
                            'kg': str(esp.kg) if esp.kg is not None else None,
                            'retal_kg': str(esp.retal_kg) if esp.retal_kg is not None else None,
                            'reproceso': esp.reproceso
                        }
                        for esp in p.especificaciones
                    ]
                }
                for p in orden.orden_piezas
            ]
        }

        app.logger.debug(f"Datos de OP {codigo_op} para edición: {op_data}")
        return op_data, 200

    except Exception as e:
        app.logger.error(f"Error al obtener datos de OP {codigo_op}: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': 'Error al cargar los datos de la orden.'}, 500


def procesar_actualizar_form_op(codigo_op, dataForm, files):
    app.logger.info(f"OP Código {codigo_op}: ENTRANDO A procesar_actualizar_form_op.")
    errores = []
    id_usuario_registro = session.get('user_id')
    app.logger.info(f"OP Código {codigo_op}: Valor de id_usuario_registro obtenido de la sesión: {id_usuario_registro}")
    app.logger.debug(f"Iniciando procesar_actualizar_form_op para OP Código: {codigo_op}")
    app.logger.debug(f"dataForm recibido: {dataForm}")
    app.logger.debug(f"files recibidos (Werkzeug MultiDict): {files}")

    if not id_usuario_registro:
        app.logger.warning("Intento de actualizar OP sin usuario autenticado.")
        return {'status': 'error', 'message': "Usuario no autenticado. Por favor, inicie sesión."}, 401

    if not codigo_op:
        app.logger.error("procesar_actualizar_form_op fue llamado sin un codigo_op.")
        return {'status': 'error', 'message': "Código de Orden de Producción no proporcionado."}, 400
        
    # Cargar la orden con sus relaciones de render y documentos para optimizar
    orden = db.session.query(OrdenProduccion).options(
        joinedload(OrdenProduccion.renders), # Corregido: usar el nombre de la relación del modelo 'renders'
        joinedload(OrdenProduccion.documentos) # Corregido: usar el nombre de la relación del modelo 'documentos'
    ).filter_by(codigo_op=codigo_op, fecha_borrado=None).first()
    
    if not orden:
        return {'status': 'error', 'message': f'Orden de Producción con Código {codigo_op} no encontrada o ya fue eliminada.'}, 404

    # --- Fase de Validación ---
    # Obtener todos los datos del formulario primero
    fecha_str = dataForm.get('fecha')
    fecha_entrega_str = dataForm.get('fecha_entrega')
    id_cliente_str = dataForm.get('id_cliente')
    producto_op_val = dataForm.get('producto') # Nombre directo, no ID
    cantidad_op_str = dataForm.get('cantidad')
    id_empleado_str = dataForm.get('id_empleado') # Vendedor
    id_supervisor_str = dataForm.get('id_supervisor')
    cotizacion_val = dataForm.get('cotizacion')
    odi_val = dataForm.get('odi')
    referencia_val = dataForm.get('referencia')
    descripcion_general_op_val = dataForm.get('descripcion_general_op')
    empaque_val = dataForm.get('empaque')
    estado_val = dataForm.get('estado')
    logistica_val = dataForm.get('logistica') # Nuevo campo
    instructivo_val = dataForm.get('instructivo') # Nuevo campo
    # medida_val = dataForm.get('medida') # Campo a revisar/eliminar, por ahora no se usa en la actualización

    # Validaciones de campos básicos
    if not fecha_str: errores.append("La Fecha es requerida.")
    else:
        try: datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError: errores.append("Formato de Fecha inválido. Use YYYY-MM-DD.")
    
    if not fecha_entrega_str: errores.append("La Fecha de Entrega es requerida.")
    else:
        try: datetime.strptime(fecha_entrega_str, '%Y-%m-%d')
        except ValueError: errores.append("Formato de Fecha de Entrega inválido. Use YYYY-MM-DD.")

    if fecha_str and fecha_entrega_str:
        try:
            if datetime.strptime(fecha_entrega_str, '%Y-%m-%d').date() < datetime.strptime(fecha_str, '%Y-%m-%d').date():
                errores.append("La Fecha de Entrega no puede ser anterior a la Fecha.")
        except ValueError: pass # Error de formato ya cubierto

    if not id_cliente_str or not id_cliente_str.isdigit():
        errores.append("Cliente es requerido y debe ser un ID válido.")
    else:
        id_cliente_val = int(id_cliente_str) # Guardar para uso posterior si es válido
        if not Clientes.query.filter_by(id_cliente=id_cliente_val, fecha_borrado=None).first():
            errores.append(f"Cliente con ID '{id_cliente_val}' no encontrado.")
    
    if not producto_op_val: errores.append("Producto es requerido.")
    
    if not cantidad_op_str or not cantidad_op_str.isdigit() or int(cantidad_op_str) <= 0:
        errores.append("Cantidad OP es requerida y debe ser un número entero positivo.")
    else:
        cantidad_op_val = int(cantidad_op_str) # Convertir para uso posterior
    
    if not id_empleado_str or not id_empleado_str.isdigit():
        errores.append("Vendedor es requerido y debe ser un ID válido.")
    else:
        id_empleado_val = int(id_empleado_str) # Guardar para uso posterior
        if not Empleados.query.filter_by(id_empleado=id_empleado_val, fecha_borrado=None).first():
            errores.append(f"Vendedor con ID '{id_empleado_val}' no encontrado.")

    id_supervisor_val = None # Es opcional
    if id_supervisor_str:
        if not id_supervisor_str.isdigit():
            errores.append("ID Supervisor inválido.")
        else:
            id_supervisor_val = int(id_supervisor_str) # Guardar para uso posterior
            if not Empleados.query.filter_by(id_empleado=id_supervisor_val, fecha_borrado=None).first():
                errores.append(f"Supervisor con ID '{id_supervisor_val}' no encontrado.")
    
    if not cotizacion_val: errores.append("Cotización es requerida.")
    if not odi_val: errores.append("ODI es requerido.")
    if not descripcion_general_op_val: errores.append("Descripción General es requerida.")
    if not estado_val: errores.append("Estado es requerido.")
    # Logística es opcional, no requiere validación de existencia aquí si puede ser nulo/vacío.

    # --- Procesos Globales de la OP (Validación) ---
    op_ids_procesos_form = dataForm.getlist('op_ids_procesos')
    op_otro_proceso_form = dataForm.get('op_otro_proceso', '').strip()
    ids_procesos_validados_global = []
    
    if not op_ids_procesos_form and not op_otro_proceso_form:
        # Si no se envía nada y la OP ya tiene procesos, no es un error. Si no tiene, sí.
        if not OrdenProduccionProcesos.query.filter_by(id_op=orden.id_op).first():
             errores.append("Debe seleccionar al menos un proceso para la OP o especificar uno nuevo.")
    else:
        for id_proc_str_form_g in op_ids_procesos_form:
            if id_proc_str_form_g == 'otro' and op_otro_proceso_form: # 'otro' es un valor especial del frontend
                proceso_existente_g = Procesos.query.filter(func.lower(Procesos.nombre_proceso) == func.lower(op_otro_proceso_form), Procesos.fecha_borrado.is_(None)).first()
                if proceso_existente_g:
                    ids_procesos_validados_global.append(proceso_existente_g.id_proceso)
                # Si no existe, se creará después si no hay otros errores.
            elif id_proc_str_form_g.isdigit():
                id_proc_g_int = int(id_proc_str_form_g)
                # CORRECCIÓN DEL SYNTAXERROR:
                if Procesos.query.filter(Procesos.id_proceso == id_proc_g_int, Procesos.fecha_borrado.is_(None)).first():
                    ids_procesos_validados_global.append(id_proc_g_int)
                else:
                    errores.append(f"Proceso global con ID '{id_proc_g_int}' no encontrado.")
            elif id_proc_str_form_g != 'otro': # Ignorar 'otro' si no hay texto para op_otro_proceso_form
                 errores.append(f"ID de proceso global inválido: '{id_proc_str_form_g}'.")

    # --- Render (Validación y preparación) ---
    render_file_storage = files.get('render')
    nombre_render_servidor_para_guardar = None
    nombre_render_original_para_guardar = None
    eliminar_render_actual = False

    if dataForm.get('existing_render_path') == '' and orden.renders: # Corregido: usar 'orden.renders'
        eliminar_render_actual = True
        # Acceder al primer render si es una lista, o directamente si es one-to-one y se espera un solo objeto.
        # Por el uso posterior de orden.render_op, parece que se espera una relación que devuelva un solo objeto o None.
        # Para simplificar y ser consistente con el modelo que define 'renders' como una lista:
        current_render_for_log = orden.renders[0] if orden.renders else None
        app.logger.debug(f"Render existente (ID: {current_render_for_log.id_render if current_render_for_log else 'N/A'}) marcado para eliminación por frontend.")

    if render_file_storage and render_file_storage.filename:
        valido_r, nombre_r_o_msg = procesar_imagen_perfil(render_file_storage, 'render_op', ALLOWED_RENDER_EXTENSIONS)
        if not valido_r:
            errores.append(f"Render: {nombre_r_o_msg}")
        else:
            nombre_render_servidor_para_guardar = nombre_r_o_msg
            nombre_render_original_para_guardar = secure_filename(render_file_storage.filename)
            eliminar_render_actual = True
            app.logger.debug(f"Nuevo render '{nombre_render_original_para_guardar}' validado. Servidor: '{nombre_render_servidor_para_guardar}'.")
    
    # --- Obtener campos para la notificación ---
    action = dataForm.get('submit_action', 'save')
    destinatarios_ids_str = dataForm.get('destinatarios')
    mensaje_personalizado = dataForm.get('mensaje_personalizado', '')
    
    
    # --- Documentos (Validación y preparación) ---
    app.logger.info(f"OP Código {codigo_op}: Iniciando validación de documentos a eliminar.") # NUEVO LOG
    ids_documentos_a_eliminar_validados = []
    for doc_id_del_str in dataForm.getlist('deleted_documentos[]'):  # Cambiado de 'documentos_a_eliminar_ids[]'
        if doc_id_del_str.isdigit():
            doc_id_int = int(doc_id_del_str)
            doc_obj_check = DocumentosOP.query.filter_by(id_documento=doc_id_int, id_op=orden.id_op).first()
            if doc_obj_check:
                ids_documentos_a_eliminar_validados.append(doc_id_int)
            else:
                app.logger.warning(f"Se intentó marcar para eliminar un DocumentoOP ID {doc_id_int} que no pertenece a OP {codigo_op} o no existe.")
        # No añadir error si el ID no es dígito, simplemente se ignora. El frontend debería enviar solo dígitos.

    nuevos_documentos_storage_list = files.getlist('documentos_nuevos[]')
    documentos_info_para_guardar = []
    
    for doc_file_s_item in nuevos_documentos_storage_list:
        if doc_file_s_item and doc_file_s_item.filename:
            filename_s_seguro_item = secure_filename(doc_file_s_item.filename)
            extension_s_item = os.path.splitext(filename_s_seguro_item)[1].lower().strip('.')
            if extension_s_item not in ALLOWED_DOC_EXTENSIONS:
                errores.append(f"Documento '{filename_s_seguro_item}': Extensión .{extension_s_item} no permitida.")
                continue
            
            valido_d_item, nombre_d_servidor_o_msg = procesar_imagen_perfil(doc_file_s_item, 'documentos_op', ALLOWED_DOC_EXTENSIONS)
            if not valido_d_item: # procesar_imagen_perfil ya guardó el archivo si es valido_d_item es True
                errores.append(f"Documento '{filename_s_seguro_item}': {nombre_d_servidor_o_msg}")
            else:
                documentos_info_para_guardar.append({
                    'nombre_servidor': nombre_d_servidor_o_msg,
                    'nombre_original': filename_s_seguro_item,
                    'tipo_archivo': extension_s_item
                })
                app.logger.debug(f"Nuevo documento '{filename_s_seguro_item}' validado y archivo físico guardado. Servidor: '{nombre_d_servidor_o_msg}'.")

    # --- Piezas (Validación) ---
    piezas_data_validadas = []
    piezas_json_str_form_val = dataForm.get('piezas')
    if piezas_json_str_form_val and piezas_json_str_form_val.strip().lower() not in ['undefined', 'null', '']:
        try:
            piezas_data_recibidas = json.loads(piezas_json_str_form_val)
            if not isinstance(piezas_data_recibidas, list):
                errores.append("El formato de los datos de piezas no es una lista.")
            else:
                for idx_p_val, pieza_item_val in enumerate(piezas_data_recibidas, 1):
                    current_pieza_errores = [] # Errores específicos para esta pieza
                    id_pieza_m_str_val = pieza_item_val.get('id_pieza_maestra')
                    cant_p_str_val = str(pieza_item_val.get('cantidad', '')) # Corregido: Usar 'cantidad' para coincidir con el JSON
                    
                    if id_pieza_m_str_val is None: # Primero chequear si es None
                        current_pieza_errores.append(f"ID de pieza maestra es requerido.")
                    elif not isinstance(id_pieza_m_str_val, (str, int)): # Debe ser string o int
                        current_pieza_errores.append(f"ID de pieza maestra debe ser un número o cadena numérica.")
                    elif isinstance(id_pieza_m_str_val, str) and not id_pieza_m_str_val.isdigit(): # Si es string, debe ser numérico
                        current_pieza_errores.append(f"ID de pieza maestra ('{id_pieza_m_str_val}') debe ser numérico.")
                    else: # Es un int o un string numérico
                        try:
                            id_pieza_int = int(id_pieza_m_str_val)
                            if not Piezas.query.filter_by(id_pieza=id_pieza_int, fecha_borrado=None).first():
                                current_pieza_errores.append(f"Pieza maestra con ID '{id_pieza_int}' no encontrada.")
                        except ValueError: # Por si acaso, aunque isdigit() debería cubrirlo para strings
                                current_pieza_errores.append(f"ID de pieza maestra ('{id_pieza_m_str_val}') no es un número válido.")
                    
                    if not cant_p_str_val.isdigit() or int(cant_p_str_val) <= 0:
                        current_pieza_errores.append(f"Cantidad es requerida y positiva.")
                    
                    for dim_key_p_val in ['ancho', 'alto', 'fondo']:
                        dim_val_str_p_val = pieza_item_val.get(dim_key_p_val)
                        if dim_val_str_p_val is not None and dim_val_str_p_val != '':
                            try: float(dim_val_str_p_val)
                            except ValueError: current_pieza_errores.append(f"Valor para '{dim_key_p_val}' ('{dim_val_str_p_val}') inválido.")
                    
                    especificaciones_p_val = pieza_item_val.get('especificaciones_pieza', [])
                    if not isinstance(especificaciones_p_val, list):
                        current_pieza_errores.append(f"Formato de especificaciones inválido.")
                    else:
                        for esp_idx_p_val, esp_data_p_val in enumerate(especificaciones_p_val, 1):
                            for num_fld_p_val in ['largo', 'ancho_especificacion', 'cantidad_especificacion', 'kg', 'retal_kg']: # 'ancho' cambiado a 'ancho_especificacion'
                                val_str_esp_val = esp_data_p_val.get(num_fld_p_val)
                                if val_str_esp_val is not None and val_str_esp_val != '':
                                    try: float(val_str_esp_val)
                                    except ValueError: current_pieza_errores.append(f"Esp. #{esp_idx_p_val}: Campo '{num_fld_p_val}' ('{val_str_esp_val}') inválido.")
                    
                    if current_pieza_errores:
                        errores.append(f"Pieza #{idx_p_val}: {'; '.join(current_pieza_errores)}")
                    else:
                        piezas_data_validadas.append(pieza_item_val)
        except json.JSONDecodeError:
            errores.append("Error al decodificar los datos de las piezas (JSON inválido).")

    # --- Si hay errores de validación, retornar y limpiar archivos subidos ---
    if errores:
        archivos_subidos_para_limpiar = []
        if nombre_render_servidor_para_guardar: # Si se validó y guardó un render
            archivos_subidos_para_limpiar.append(os.path.join(app.root_path, 'static', 'render_op', nombre_render_servidor_para_guardar))
        for doc_info_err_clean in documentos_info_para_guardar: # Si se validaron y guardaron documentos
            archivos_subidos_para_limpiar.append(os.path.join(app.root_path, 'static', 'documentos_op', doc_info_err_clean['nombre_servidor']))
        
        for path_archivo_err_clean in archivos_subidos_para_limpiar:
            if os.path.exists(path_archivo_err_clean):
                try:
                    os.remove(path_archivo_err_clean)
                    app.logger.info(f"Archivo subido '{path_archivo_err_clean}' eliminado debido a error de validación.")
                except Exception as e_clean_up:
                    app.logger.error(f"Error limpiando archivo subido '{path_archivo_err_clean}': {e_clean_up}")
            
        app.logger.warning(f"Errores de validación al actualizar OP {codigo_op}: {errores}")
        return {'status': 'error', 'message': "Errores de validación: " + "; ".join(errores)}, 400

    # --- Fase de Actualización en Base de Datos (si no hay errores de validación) ---
    try:
        # Calcular el siguiente número de versión
        last_version = db.session.query(func.max(OPLog.version_number)).filter_by(id_op=orden.id_op).scalar() or 0
        new_version_number = last_version + 1

        # Crear JSON de cambios
        cambios = {}
        if fecha_str and orden.fecha != datetime.strptime(fecha_str, '%Y-%m-%d').date():
            cambios['fecha'] = {'anterior': orden.fecha.strftime('%Y-%m-%d') if orden.fecha else None, 'nuevo': fecha_str}
        if fecha_entrega_str and orden.fecha_entrega != datetime.strptime(fecha_entrega_str, '%Y-%m-%d').date():
            cambios['fecha_entrega'] = {'anterior': orden.fecha_entrega.strftime('%Y-%m-%d') if orden.fecha_entrega else None, 'nuevo': fecha_entrega_str}
        if id_cliente_str and orden.id_cliente != int(id_cliente_str):
            cambios['id_cliente'] = {'anterior': orden.id_cliente, 'nuevo': int(id_cliente_str)}
        if producto_op_val and orden.producto != producto_op_val:
            cambios['producto'] = {'anterior': orden.producto, 'nuevo': producto_op_val}
        if cantidad_op_str and orden.cantidad != int(cantidad_op_str):
            cambios['cantidad'] = {'anterior': orden.cantidad, 'nuevo': int(cantidad_op_str)}
        if id_empleado_str and orden.id_empleado != int(id_empleado_str):
            cambios['id_empleado'] = {'anterior': orden.id_empleado, 'nuevo': int(id_empleado_str)}
        if id_supervisor_str and orden.id_supervisor != (int(id_supervisor_str) if id_supervisor_str else None):
            cambios['id_supervisor'] = {'anterior': orden.id_supervisor, 'nuevo': int(id_supervisor_str) if id_supervisor_str else None}
        if cotizacion_val and orden.cotizacion != cotizacion_val:
            cambios['cotizacion'] = {'anterior': orden.cotizacion, 'nuevo': cotizacion_val}
        if odi_val and orden.odi != odi_val:
            cambios['odi'] = {'anterior': orden.odi, 'nuevo': odi_val}
        if referencia_val != orden.referencia:
            cambios['referencia'] = {'anterior': orden.referencia, 'nuevo': referencia_val}
        if descripcion_general_op_val and orden.descripcion_general != descripcion_general_op_val:
            cambios['descripcion_general'] = {'anterior': orden.descripcion_general, 'nuevo': descripcion_general_op_val}
        if empaque_val != orden.empaque:
            cambios['empaque'] = {'anterior': orden.empaque, 'nuevo': empaque_val}
        if estado_val and orden.estado != estado_val:
            cambios['estado'] = {'anterior': orden.estado, 'nuevo': estado_val}
        if logistica_val != orden.logistica:
            cambios['logistica'] = {'anterior': orden.logistica, 'nuevo': logistica_val}
        if instructivo_val != orden.instructivo:
            cambios['instructivo'] = {'anterior': orden.instructivo, 'nuevo': instructivo_val}
        if dataForm.get('estado_proyecto') != orden.estado_proyecto:
            cambios['estado_proyecto'] = {'anterior': orden.estado_proyecto, 'nuevo': dataForm.get('estado_proyecto')}
            

        # Si hay cambios, insertar el log
        if cambios:
            db.session.execute(
                text("""
                    INSERT INTO tbl_op_logs (id_op, version_number, cambios, id_usuario_update)
                    VALUES (:id_op, :version_number, :cambios, :id_usuario_update)
                """),
                {
                    'id_op': orden.id_op,
                    'version_number': new_version_number,
                    'cambios': json.dumps(cambios),
                    'id_usuario_update': id_usuario_registro
                }
            )

        # Campos simples de OrdenProduccion
        orden.fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        orden.fecha_entrega = datetime.strptime(fecha_entrega_str, '%Y-%m-%d').date()
        orden.id_cliente = int(id_cliente_str)
        orden.producto = producto_op_val
        orden.cantidad = cantidad_op_val
        orden.id_empleado = int(id_empleado_str)
        orden.id_supervisor = id_supervisor_val
        orden.cotizacion = cotizacion_val
        orden.odi = odi_val
        orden.referencia = referencia_val
        orden.descripcion_general = descripcion_general_op_val
        orden.empaque = empaque_val
        orden.estado = estado_val
        orden.logistica = dataForm.get('logistica')
        orden.instructivo = dataForm.get('instructivo')
        orden.estado_proyecto = dataForm.get('estado_proyecto')
        
        try:
            current_version_ord_db_val = int(orden.version) if orden.version and orden.version.isdigit() else 0
            orden.version = str(current_version_ord_db_val + 1)
        except: orden.version = "1"  # Fallback
        
        orden.id_usuario_actualizacion = id_usuario_registro
        orden.fecha_actualizacion = datetime.now(LOCAL_TIMEZONE)

        # Render
        # Render: 'renders' es una lista en el modelo. Asumimos que solo puede haber uno o cero.
        current_render = orden.renders[0] if orden.renders else None

        if eliminar_render_actual and current_render:
            path_render_ant_fis_abs_db = os.path.join(app.root_path, 'static', 'render_op', os.path.basename(current_render.render_path))
            app.logger.info(f"Intentando eliminar render físico anterior: {path_render_ant_fis_abs_db}")
            if os.path.exists(path_render_ant_fis_abs_db):
                try:
                    os.remove(path_render_ant_fis_abs_db)
                    app.logger.info(f"Render físico anterior eliminado: {path_render_ant_fis_abs_db}")
                except Exception as e_rem_r_fis_db:
                    app.logger.error(f"Error eliminando render físico anterior {path_render_ant_fis_abs_db}: {e_rem_r_fis_db}")
            else:
                app.logger.warning(f"Render físico anterior no encontrado para eliminar: {path_render_ant_fis_abs_db}")
            db.session.delete(current_render)
            # orden.renders ya no contendrá este objeto después del delete y commit/flush.
            db.session.flush()

        if nombre_render_servidor_para_guardar:
            app.logger.info(f"Guardando nuevo render en BD. Path: {nombre_render_servidor_para_guardar}")
            nuevo_render_obj_db_val = RendersOP(
                id_op=orden.id_op,
                render_path=nombre_render_servidor_para_guardar
            )
            db.session.add(nuevo_render_obj_db_val)
            # Para asegurar que la relación orden.renders se actualice en memoria para esta transacción
            # si fuera necesario inmediatamente (aunque el commit y recarga en detalle_op es lo principal)
            if current_render in orden.renders: # Si el viejo estaba en la lista
                orden.renders.remove(current_render)
            orden.renders.append(nuevo_render_obj_db_val) # Añadir el nuevo a la lista en memoria

        # Obtener IDs de documentos a eliminar y validarlos como enteros
        app.logger.info(f"Contenido completo de dataForm ANTES de getlist('idsDocumentosAEliminar'): {dataForm}")
        documentos_a_eliminar_ids_str = dataForm.getlist('idsDocumentosAEliminar')
        app.logger.info(f"Resultado de dataForm.getlist('idsDocumentosAEliminar'): {documentos_a_eliminar_ids_str}")
        
        ids_documentos_a_eliminar_validados = []
        if documentos_a_eliminar_ids_str:
            for doc_id_str in documentos_a_eliminar_ids_str:
                try:
                    doc_id_int = int(doc_id_str)
                    ids_documentos_a_eliminar_validados.append(doc_id_int)
                except ValueError:
                    app.logger.warning(f"ID de documento no válido '{doc_id_str}' no se pudo convertir a entero.")
        else:
            app.logger.info("No se recibieron strings de IDs de documentos para eliminar desde dataForm.getlist.")

        # Documentos
        app.logger.info(f"IDs de documentos marcados para eliminar (validados): {ids_documentos_a_eliminar_validados}")
        if ids_documentos_a_eliminar_validados:
            for doc_id_del_val_db in ids_documentos_a_eliminar_validados:
                doc_obj_del_db_val = DocumentosOP.query.get(doc_id_del_val_db)
                if doc_obj_del_db_val:
                    app.logger.info(f"Procesando eliminación para Documento ID: {doc_obj_del_db_val.id_documento}, Path: {doc_obj_del_db_val.documento_path}")
                    if doc_obj_del_db_val.documento_path:
                        path_doc_fis_del_abs_db_val = os.path.join(app.root_path, 'static', 'documentos_op', os.path.basename(doc_obj_del_db_val.documento_path))
                        if os.path.exists(path_doc_fis_del_abs_db_val):
                            try:
                                os.remove(path_doc_fis_del_abs_db_val)
                                app.logger.info(f"Documento físico eliminado: {path_doc_fis_del_abs_db_val}")
                            except Exception as e_rem_d_fis_db_val:
                                app.logger.error(f"Error eliminando doc físico {path_doc_fis_del_abs_db_val}: {e_rem_d_fis_db_val}")
                        else:
                            app.logger.warning(f"Documento físico no encontrado para eliminar: {path_doc_fis_del_abs_db_val}")
                    db.session.delete(doc_obj_del_db_val)
                    app.logger.info(f"Documento ID: {doc_obj_del_db_val.id_documento} marcado para delete en sesión.")
                else:
                    app.logger.warning(f"Documento con ID {doc_id_del_val_db} no encontrado en BD para eliminar.")
        else:
            app.logger.info("No se enviaron IDs de documentos para eliminar o ninguno fue validado.")
        
        # 2. Añadir los nuevos (archivos físicos ya guardados por procesar_imagen_perfil)
        if documentos_info_para_guardar: # Solo iterar si hay nuevos documentos
            for doc_info_v_db_val in documentos_info_para_guardar:
                nuevo_doc_bd_obj_val = DocumentosOP(
                    id_op=orden.id_op,
                    documento_path=doc_info_v_db_val['nombre_servidor'], # Corregido
                    documento_nombre_original=doc_info_v_db_val['nombre_original'] # Corregido
                    # Corregido: Se eliminan tipo_archivo e id_usuario_registro
                )
                db.session.add(nuevo_doc_bd_obj_val)
            
        # URLs
        OrdenProduccionURLs.query.filter_by(id_op=orden.id_op).delete()
        urls_form_list_db_val = dataForm.getlist('urls[]')
        for url_item_form_db_val in urls_form_list_db_val:
            if url_item_form_db_val.strip():
                # Corregido: Se elimina id_usuario_registro ya que no existe en el modelo OrdenProduccionURLs
                db.session.add(OrdenProduccionURLs(id_op=orden.id_op, url=url_item_form_db_val.strip()))

        # Procesos Globales de la OP
        OrdenProduccionProcesos.query.filter_by(id_op=orden.id_op).delete()
        for id_proc_v_db_val in ids_procesos_validados_global:
            # Corregido: Se elimina id_usuario_registro para OrdenProduccionProcesos
            db.session.add(OrdenProduccionProcesos(id_op=orden.id_op, id_proceso=id_proc_v_db_val))
        
        if 'otro' in op_ids_procesos_form and op_otro_proceso_form: # Si se especificó "otro"
            proceso_otro_check_db_val = Procesos.query.filter(func.lower(Procesos.nombre_proceso) == func.lower(op_otro_proceso_form), Procesos.fecha_borrado.is_(None)).first()
            if not proceso_otro_check_db_val: # Y no existía previamente
                # Para el modelo Procesos, sí existe id_usuario_registro (asumiendo que se añadió o siempre estuvo)
                nuevo_proceso_otro_obj_db_val = Procesos(
                    codigo_proceso=f"OTRO-{uuid.uuid4().hex[:6].upper()}",
                    nombre_proceso=op_otro_proceso_form,
                    descripcion_proceso=f"Proceso '{op_otro_proceso_form}' creado desde OP.",
                    id_usuario_registro=id_usuario_registro # Asumiendo que Procesos sí lo tiene
                )
                db.session.add(nuevo_proceso_otro_obj_db_val)
                db.session.flush()
                if nuevo_proceso_otro_obj_db_val.id_proceso not in ids_procesos_validados_global:
                    # Corregido: Se elimina id_usuario_registro para OrdenProduccionProcesos
                    db.session.add(OrdenProduccionProcesos(id_op=orden.id_op, id_proceso=nuevo_proceso_otro_obj_db_val.id_proceso))
            elif proceso_otro_check_db_val and proceso_otro_check_db_val.id_proceso not in ids_procesos_validados_global:
                # Si existía pero no estaba en la lista (ej. se deselección y se volvió a escribir), añadirlo
                 # Corregido: Se elimina id_usuario_registro para OrdenProduccionProcesos
                 db.session.add(OrdenProduccionProcesos(id_op=orden.id_op, id_proceso=proceso_otro_check_db_val.id_proceso))


        # Piezas (Eliminar todas las existentes y sus detalles, luego recrear)
        piezas_existentes_ord_db_val = OrdenPiezas.query.filter_by(id_op=orden.id_op).all()
        for p_exist_ord_db_val in piezas_existentes_ord_db_val:
            OrdenPiezasActividades.query.filter_by(id_orden_pieza=p_exist_ord_db_val.id_orden_pieza).delete()
            OrdenPiezasProcesos.query.filter_by(id_orden_pieza=p_exist_ord_db_val.id_orden_pieza).delete()
            OrdenPiezaValoresDetalle.query.filter_by(id_orden_pieza=p_exist_ord_db_val.id_orden_pieza).delete()
            OrdenPiezaEspecificaciones.query.filter_by(id_orden_pieza=p_exist_ord_db_val.id_orden_pieza).delete()
            db.session.delete(p_exist_ord_db_val)
        db.session.flush()

        for pieza_d_form_db_val in piezas_data_validadas:
            nueva_op_pieza_obj_db_val = OrdenPiezas(
                id_op=orden.id_op,
                id_pieza=int(pieza_d_form_db_val['id_pieza_maestra']),
                cantidad=int(pieza_d_form_db_val['cantidad']),
                nombre_pieza_op=pieza_d_form_db_val.get('nombre_pieza'), # Añadido para el campo NOT NULL
                descripcion_pieza=pieza_d_form_db_val.get('descripcion_pieza'),
                ancho=float(pieza_d_form_db_val['ancho']) if pieza_d_form_db_val.get('ancho') else None,
                alto=float(pieza_d_form_db_val['alto']) if pieza_d_form_db_val.get('alto') else None,
                fondo=float(pieza_d_form_db_val['fondo']) if pieza_d_form_db_val.get('fondo') else None,
                proveedor_externo=pieza_d_form_db_val.get('proveedor_externo'),
                tipo_molde=pieza_d_form_db_val.get('tipo_molde'),
                montaje=pieza_d_form_db_val.get('montaje'),
                montaje_tamano=pieza_d_form_db_val.get('tamano_montaje'),
                cantidad_material=pieza_d_form_db_val.get('cantidad_material'),
                material=pieza_d_form_db_val.get('material')
                # Corregido: Se elimina id_usuario_registro ya que no existe en el modelo OrdenPiezas
            )
            db.session.add(nueva_op_pieza_obj_db_val)
            db.session.flush()

            for id_proc_p_form_str_db_val in pieza_d_form_db_val.get('procesos_pieza', []):
                if id_proc_p_form_str_db_val.isdigit():
                    db.session.add(OrdenPiezasProcesos(id_orden_pieza=nueva_op_pieza_obj_db_val.id_orden_pieza, id_proceso=int(id_proc_p_form_str_db_val), id_usuario_registro=id_usuario_registro))
            
            for id_act_p_form_str_db_val in pieza_d_form_db_val.get('actividades_pieza', []):
                if id_act_p_form_str_db_val.isdigit():
                    db.session.add(OrdenPiezasActividades(id_orden_pieza=nueva_op_pieza_obj_db_val.id_orden_pieza, id_actividad=int(id_act_p_form_str_db_val)))
            
            # Corregido: Usar 'valores_configuracion' para obtener la lista de detalles
            for config_item_from_json in pieza_d_form_db_val.get('valores_configuracion', []):
                grupo_conf = config_item_from_json.get('grupo_configuracion')
                valor_conf = config_item_from_json.get('valor_configuracion')
                
                # id_detalle_maestra no se usa directamente en el modelo OrdenPiezaValoresDetalle,
                # pero el grupo y valor sí. Asegurarse que el grupo exista.
                if grupo_conf and valor_conf is not None: # valor_conf puede ser una cadena vacía
                    db.session.add(OrdenPiezaValoresDetalle(
                        id_orden_pieza=nueva_op_pieza_obj_db_val.id_orden_pieza,
                        grupo_configuracion=str(grupo_conf),
                        valor_configuracion=str(valor_conf)
                        # Corregido: Se elimina id_usuario_registro y id_detalle_maestra ya que no existen en el modelo
                    ))
            
            for esp_item_p_form_db_val in pieza_d_form_db_val.get('especificaciones_pieza', []):
                db.session.add(OrdenPiezaEspecificaciones(
                    id_orden_pieza=nueva_op_pieza_obj_db_val.id_orden_pieza,
                    item=esp_item_p_form_db_val.get('item'), calibre=esp_item_p_form_db_val.get('calibre'),
                    largo=float(esp_item_p_form_db_val.get('largo')) if esp_item_p_form_db_val.get('largo') else None,                    
                    ancho=float(esp_item_p_form_db_val.get('ancho')) if esp_item_p_form_db_val.get('ancho') else None, # Corregido: argumento y fuente de datos                    
                    unidad=esp_item_p_form_db_val.get('unidad'),
                    cantidad_especificacion=int(esp_item_p_form_db_val.get('cantidad_especificacion')) if esp_item_p_form_db_val.get('cantidad_especificacion') else None,
                    kg=float(esp_item_p_form_db_val.get('kg')) if esp_item_p_form_db_val.get('kg') else None,
                    retal_kg=float(esp_item_p_form_db_val.get('retal_kg')) if esp_item_p_form_db_val.get('retal_kg') else None,
                    reproceso=esp_item_p_form_db_val.get('reproceso')
                    # Corregido: Se elimina id_usuario_registro ya que no existe en el modelo OrdenPiezaEspecificaciones
                ))
        
        db.session.commit()
        app.logger.info(f"Orden de Producción Código {codigo_op} (ID: {orden.id_op}) actualizada exitosamente por usuario ID {id_usuario_registro}.")
        
        # --- INICIO: LÓGICA DE NOTIFICACIÓN PARA ACTUALIZACIÓN ---
        if action == 'save_and_notify':
            app.logger.info(f"Iniciando notificación por correo para la ACTUALIZACIÓN de OP {orden.codigo_op}.")
            if not destinatarios_ids_str:
                app.logger.warning('Acción "save_and_notify" pero no se proporcionaron destinatarios.')
            else:
                try:
                    destinatarios_ids = [int(id) for id in destinatarios_ids_str.split(',')]
                    destinatarios = db.session.query(Users).filter(Users.id.in_(destinatarios_ids)).all()
                    cliente = db.session.query(Clientes).get(id_cliente_val)
                    vendedor = db.session.query(Empleados).get(orden.id_empleado)
                    supervisor = db.session.query(Empleados).get(orden.id_supervisor) if orden.id_supervisor else None
                    
                    email_sender = 'evolutioncontrolweb@gmail.com'
                    email_password = 'qsmr ccyb yzjd gzkm'

                    for destinatario in destinatarios:
                        if destinatario.email_user: 
                            subject = f'Actualización en Orden de Producción: {orden.codigo_op}'
                            body = f"""
                            Hola {destinatario.name_surname},

                            Se ha ACTUALIZADO la Orden de Producción con los siguientes detalles:

                            - Número de OP: {orden.codigo_op}
                            - Cliente: {cliente.nombre_cliente}
                            - Producto: {orden.producto}
                            - Fecha de Entrega: {orden.fecha_entrega.strftime('%d de %B de %Y')}
                            - ODI: {orden.odi}
                            - Cotización: {orden.cotizacion}
                            - Vendedor: {vendedor.nombre_empleado +' '+ vendedor.apellido_empleado if vendedor else 'N/A'}
                            - Supervisor: {supervisor.nombre_empleado if supervisor else 'No asignado'}
                            - Actualizado por: {session.get('name_surname', 'Usuario desconocido')}
                            - Version : {orden.version}

                            Descripción:
                            {orden.descripcion_general}

                            ---
                            Mensaje Adicional:
                            {mensaje_personalizado if mensaje_personalizado else 'No se incluyó un mensaje adicional.'}
                            ---

                            Este es un mensaje automático.
                            """
                            em = EmailMessage()
                            em['From'] = email_sender
                            em['To'] = destinatario.email_user
                            em['Subject'] = subject
                            em.set_content(body)

                            context = ssl.create_default_context()
                            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                                smtp.login(email_sender, email_password)
                                smtp.send_message(em)
                            
                            app.logger.info(f'Correo de actualización de OP {orden.codigo_op} notificado a {destinatario.email_user}')
                
                except Exception as e:
                    app.logger.error(f"FALLO al enviar correos de notificación para la ACTUALIZACIÓN de OP {orden.codigo_op}: {str(e)}", exc_info=True)
        # --- FIN: LÓGICA DE NOTIFICACIÓN ---
        
        return {'status': 'success', 'message': f'Orden de Producción {orden.codigo_op} actualizada correctamente.', 'codigo_op': orden.codigo_op, 'redirect_url': url_for('detalle_op', codigo_op=orden.codigo_op)} # Corregido: endpoint 'detalle_op'
    
    except IntegrityError as ie_db_val:
        db.session.rollback()
        app.logger.error(f"Error de integridad al actualizar OP Código {codigo_op}: {ie_db_val}", exc_info=True)
        return {'status': 'error', 'message': 'Error de integridad de datos. Verifique que no haya duplicados o datos incorrectos.'}, 409
    except SQLAlchemyError as sae_db_val:
        db.session.rollback()
        app.logger.error(f"Error de SQLAlchemy al actualizar OP Código {codigo_op}: {sae_db_val}", exc_info=True)
        return {'status': 'error', 'message': 'Error de base de datos al actualizar la orden.'}, 500
    except Exception as e_db_val:
        db.session.rollback()
        app.logger.error(f"Error inesperado al actualizar OP Código {codigo_op} en BD: {e_db_val}", exc_info=True)
        return {'status': 'error', 'message': f'Se produjo un error inesperado durante la actualización en BD: {str(e_db_val)}'}, 500


# Eliminar Orden de Producción
def eliminar_op(id_op):
    try:
        # Buscar la orden
        orden = db.session.query(
            OrdenProduccion).filter_by(id_op=id_op).first()
        if not orden:
            app.logger.warning(f"No se encontró la orden con id_op: {id_op}")
            return 0

        # Calcular la ruta base para los archivos
        basepath = os.path.abspath(os.path.dirname(__file__))

        # Eliminar archivos de renders asociados
        for render in orden.renders:
            render_full_path = os.path.normpath(
                os.path.join(basepath, '../', render.render_path))
            if os.path.exists(render_full_path):
                os.remove(render_full_path)
                app.logger.debug(
                    f"Archivo render eliminado: {render_full_path}")
            else:
                app.logger.warning(
                    f"Archivo render no encontrado en: {render_full_path}")

        # Eliminar documentos asociados
        for doc in orden.documentos:
            doc_full_path = os.path.normpath(
                os.path.join(basepath, '../', doc.documento_path))
            if os.path.exists(doc_full_path):
                os.remove(doc_full_path)
                app.logger.debug(f"Documento eliminado: {doc_full_path}")
            else:
                app.logger.warning(
                    f"Documento no encontrado en: {doc_full_path}")

        # Eliminar la orden (esto también elimina registros relacionados por CASCADE)
        db.session.delete(orden)
        db.session.commit()
        app.logger.debug(
            f"Orden de producción con id_op {id_op} eliminada correctamente.")
        return 1  # Indica éxito (rowcount)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en eliminar_op: {e}")
        return 0


def buscar_ordenes_produccion_bd(codigo_op='', fecha='', nombre_cliente='', start=0, length=10, order=None):
    try:
        # Consulta base con JOIN para obtener el nombre del supervisor y cliente
        query = db.session.query(
            OrdenProduccion,
            db.func.concat(Empleados.nombre_empleado, ' ',
                           Empleados.apellido_empleado).label('nombre_supervisor')
        ).outerjoin(
            Clientes, OrdenProduccion.id_cliente == Clientes.id_cliente
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
        
        # Filtro por nombre de cliente
        if nombre_cliente:
            query = query.filter(Clientes.nombre_cliente.ilike(f'%{nombre_cliente}%'))

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
            2: Clientes.nombre_cliente,  # Columna 'Cliente'
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
                raise ValueError(
                    f"No se encontró el empleado con ID: {jornada.id_empleado}")

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
            app.logger.debug(
                f"ID Empleado de la jornada: {jornada.id_empleado}")
            empleado = Empleados.query.get(jornada.id_empleado)
            app.logger.debug(f"Empleado encontrado: {empleado}")
            nombre_completo_empleado = "Desconocido"
            if empleado:
                nombre_completo_empleado = f"{empleado.nombre_empleado} {empleado.apellido_empleado or ''}".strip(
                )

            # Convertir datetimes a string si no son None, de lo contrario None o string vacío
            fecha_hora_llegada_programada_str = jornada.fecha_hora_llegada_programada.strftime(
                '%Y-%m-%dT%H:%M') if jornada.fecha_hora_llegada_programada else None
            fecha_hora_salida_programada_str = jornada.fecha_hora_salida_programada.strftime(
                '%Y-%m-%dT%H:%M') if jornada.fecha_hora_salida_programada else None
            fecha_hora_llegada_str = jornada.fecha_hora_llegada.strftime(
                '%Y-%m-%dT%H:%M') if jornada.fecha_hora_llegada else None
            fecha_hora_salida_str = jornada.fecha_hora_salida.strftime(
                '%Y-%m-%dT%H:%M') if jornada.fecha_hora_salida else None
            fecha_registro_str = jornada.fecha_registro.strftime(
                '%Y-%m-%d %I:%M %p') if jornada.fecha_registro else None

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
        jornada = db.session.query(Jornadas).filter_by(
            id_jornada=id_jornada).first()
        if jornada:
            jornada.id_empleado = dataForm.get('id_empleado')

            fh_llegada_prog_str = dataForm.get('fecha_hora_llegada_programada')
            if fh_llegada_prog_str:
                jornada.fecha_hora_llegada_programada = datetime.strptime(
                    fh_llegada_prog_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_llegada_programada = None

            fh_salida_prog_str = dataForm.get('fecha_hora_salida_programada')
            if fh_salida_prog_str:
                jornada.fecha_hora_salida_programada = datetime.strptime(
                    fh_salida_prog_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_salida_programada = None

            fh_llegada_real_str = dataForm.get('fecha_hora_llegada')
            if fh_llegada_real_str:
                jornada.fecha_hora_llegada = datetime.strptime(
                    fh_llegada_real_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_llegada = None

            fh_salida_real_str = dataForm.get('fecha_hora_salida')
            if fh_salida_real_str:
                jornada.fecha_hora_salida = datetime.strptime(
                    fh_salida_real_str, '%Y-%m-%dT%H:%M')
            else:
                jornada.fecha_hora_salida = None

            jornada.novedad_jornada_programada = dataForm.get(
                'novedad_jornada_programada')
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
        total_records = db.session.query(
            func.count(Jornadas.id_jornada)).scalar()

        # Aplicar filtros de búsqueda
        if search_empleado:
            search_term_empleado = f"%{search_empleado}%"
            query = query.filter(or_(Empleados.nombre_empleado.ilike(
                search_term_empleado), Empleados.apellido_empleado.ilike(search_term_empleado)))

        if search_fecha:
            try:
                fecha_obj = datetime.strptime(search_fecha, '%Y-%m-%d').date()
                query = query.filter(
                    func.date(Jornadas.fecha_registro) == fecha_obj)
            except ValueError:
                app.logger.warning(
                    f"Formato de fecha inválido para búsqueda: {search_fecha}")
                # Considerar no aplicar el filtro de fecha o devolver un error/lista vacía

        # Conteo de registros DESPUÉS de aplicar los filtros de búsqueda
        # Esto es para 'recordsFiltered'
        filtered_records = query.count()

        # Mapeo de columnas para ordenamiento (el índice debe coincidir con el orden en el frontend)
        column_map = {
            0: Jornadas.id_jornada,  # O un campo no visible si la primera col es contador
            # Asumiendo que esta es la columna por la que se ordena
            1: Empleados.nombre_empleado,
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
                    query = query.order_by(
                        desc(Empleados.nombre_empleado), desc(Empleados.apellido_empleado))
                else:
                    query = query.order_by(
                        asc(Empleados.nombre_empleado), asc(Empleados.apellido_empleado))
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
        return [], 0, 0  # Devuelve valores por defecto en caso de error


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
        if search and search.strip():  # También verifica que search no sea solo espacios
            # Preparar el término para LIKE (quita espacios al inicio/fin)
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Empleados.nombre_empleado.ilike(search_term),
                    Empleados.apellido_empleado.ilike(search_term)
                    # Opcional: buscar también por documento si es relevante
                    # Empleados.documento.ilike(search_term)
                )
            )

        # Aplicar orden (más natural para resultados de búsqueda) y paginación
        total = query.count()
        empleados_bd = query.order_by(
            Empleados.nombre_empleado,
            Empleados.apellido_empleado
        ).limit(per_page).offset(offset).all()

        return empleados_bd, total

    except Exception as e:
        # Usar app.logger si está configurado, sino un print o logging estándar
        # Asegúrate que 'app' esté disponible en este contexto si usas app.logger
        if hasattr(app, 'logger'):
            app.logger.error(
                f"Error en la función get_empleados_paginados: {e}")
        else:
            # Fallback si app.logger no existe
            print(f"Error en la función get_empleados_paginados: {e}")
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
        empleados = query.paginate(
            page=page, per_page=per_page, error_out=False).items
        return [{'id_empleado': e.id_empleado, 'nombre_empleado': f"{e.nombre_empleado} {e.apellido_empleado}"} for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en get_supervisores_paginados: {e}")
        return []


def get_procesos_paginados(page, per_page, search):
    query = Procesos.query.filter(Procesos.fecha_borrado.is_(None))

    if search:
        search_term = f"%{search}%"
        query = query.filter(Procesos.nombre_proceso.ilike(search_term))

    paginated_query = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated_query.items, paginated_query.total



def get_piezas_paginados(page, per_page, search):
    query = Piezas.query.filter(Piezas.fecha_borrado.is_(None))

    if search:
        search_term = f"%{search}%"
        query = query.filter(Piezas.nombre_proceso.ilike(search_term))

    return query.paginate(page=page, per_page=per_page, error_out=False).items


def get_actividades_paginados(page, per_page, search, id_proceso=None):
    query = Actividades.query.filter(Actividades.fecha_borrado.is_(None))

    if id_proceso:
        query = query.filter(Actividades.id_proceso == id_proceso)

    if search:
        search_term = f"%{search}%"
        query = query.filter(Actividades.nombre_actividad.ilike(search_term))

    return query.paginate(page=page, per_page=per_page, error_out=False)



def get_actividades_paginados_op(page=1, per_page=10, search='', id_procesos=None):
    try:
        offset = (page - 1) * per_page
        query = db.session.query(Actividades).filter(Actividades.fecha_borrado.is_(None))

        # Filtrar por múltiples procesos si se proporciona id_procesos
        if id_procesos:
            # Convertir id_procesos a una lista de enteros si es una cadena separada por comas
            process_ids = [int(pid) for pid in id_procesos.split(',')] if isinstance(id_procesos, str) else []
            if process_ids:
                query = query.filter(Actividades.id_proceso.in_(process_ids))

        if search:
            search_term = f"%{search}%"
            query = query.filter(Actividades.nombre_actividad.ilike(search_term))

        total = query.count()
        actividades = query.offset(offset).limit(per_page).all()

        results = [
            {
                "id": a.id_actividad,
                "text": a.nombre_actividad
            } for a in actividades
        ]

        return {
            "results": results,
            "pagination": {
                "more": (offset + per_page) < total
            }
        }
    except Exception as e:
        app.logger.error(f"Error en get_actividades_paginados: {e}")
        return {"results": [], "pagination": {"more": false}}


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
    paginated_query = query.paginate(page=page, per_page=per_page, error_out=False)
    ordenes_data = [
        {
            'id_op': ord.id_op,
            'codigo_op': ord.codigo_op,
            'cliente': ord.cliente.nombre_cliente if ord.cliente else None
        }
        for ord in paginated_query.items
    ]
    return ordenes_data, paginated_query.total


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
        clientes_data = [{
            'id_cliente': c.id_cliente,
            'nombre_cliente': c.nombre_cliente
        } for c in clientes]
        return clientes_data, total
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
        empresa = db.session.query(Empresa).options(joinedload(Empresa.usuario_reg)).filter_by(
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
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        empresas = pagination.items
        resultados = []
        for e in empresas:
            tipo_empleado_obj = Tipo_Empleado.query.filter(func.lower(Tipo_Empleado.tipo_empleado) == func.lower(e.tipo_empresa)).first()
            resultados.append({
                "id_empresa": e.id_empresa,
                "nombre_empresa": e.nombre_empresa,
                "tipo_empresa": e.tipo_empresa,
                "id_tipo_empleado": tipo_empleado_obj.id_tipo_empleado if tipo_empleado_obj else None
            })
        return {
            'empresas': resultados,
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    except Exception as e:
        app.logger.error(f"Error en get_empresas_paginadas: {str(e)}")
        return {'empresas': [], 'total': 0, 'page': page, 'per_page': per_page}


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

def get_detalles_pieza_maestra_options(grupo_detalles_pieza_param):
    """
    Obtiene las opciones de detalles de pieza para un grupo específico.
    Estas opciones se usarán para poblar los Select2 en el modal de detalles de pieza.
    """
    try:
        # Consultar la tabla DetallesPiezaMaestra filtrando por el grupo
        # Se usa func.lower para hacer la comparación insensible a mayúsculas/minúsculas
        opciones_query = DetallesPiezaMaestra.query.filter(
            func.lower(DetallesPiezaMaestra.grupo_detalles_pieza) == func.lower(grupo_detalles_pieza_param)
        ).order_by(DetallesPiezaMaestra.detalles_pieza).all()

        # Formatear para Select2: una lista de diccionarios con 'id' y 'text'
        # Aquí, tanto 'id' como 'text' serán el valor de 'detalles_pieza',
        # ya que es el valor que se almacenará y se mostrará.
        opciones_formateadas = [
            {"id": opcion.detalles_pieza, "text": opcion.detalles_pieza}
            for opcion in opciones_query
        ]
        
        app.logger.debug(f"Opciones para grupo '{grupo_detalles_pieza_param}': {opciones_formateadas}")
        return opciones_formateadas
    except Exception as e:
        app.logger.error(f"Error en get_detalles_pieza_maestra_options para el grupo '{grupo_detalles_pieza_param}': {e}", exc_info=True)
        return [] # Devolver lista vacía en caso de error




def get_all_empleados():
    """
    Obtiene todos los usuarios activos.
    """
    try:
        empleados = db.session.query(Users).filter(Users.fecha_borrado.is_(None),Users.rol == 'Administrador').order_by(Users.name_surname.asc()).all()
        return [{
            'id_empleado': e.id,
            'nombre_empleado': e.name_surname,
            'email_empleado': e.email_user,
            'cargo': e.rol
        } for e in empleados]
    except Exception as e:
        app.logger.error(f"Error en get_all_empleados: {e}", exc_info=True)
        return []