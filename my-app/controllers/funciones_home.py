# Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename
import uuid  # Módulo de Python para crear un string
import json
import magic
import os
from os import remove, path  # Módulos para manejar archivos
from app import app  # Importa la instancia de Flask desde app.py
# Importa modelos desde models.py
from conexion.models import db, OrdenPiezasProcesos, OrdenPiezas, RendersOP, DocumentosOP, Operaciones, Empleados, Tipo_Empleado, Piezas, Procesos, Actividades, Clientes, TipoDocumento, OrdenProduccion, Jornadas, Users, Empresa
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
        return db.session.query(Empleados, Empresa).join(Empresa, Empleados.id_empresa == Empresa.id_empresa).filter(Empleados.fecha_borrado.is_(None)).order_by(Empleados.nombre_empleado.asc()).all()
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
            OrdenProduccion.id_op.desc()).first()
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


def procesar_form_cliente(dataForm, foto_perfil_cliente):
    try:
        documento_str = dataForm.get('documento', '')
        documento_sin_puntos = re.sub('[^0-9]+', '', documento_str)
        if not documento_sin_puntos:
            raise ValueError("Documento es requerido.")
        documento = int(documento_sin_puntos)

        nombre_cliente = dataForm.get('nombre_cliente')
        id_tipo_documento_str = dataForm.get('id_tipo_documento')
        if not nombre_cliente:
            raise ValueError("Nombre del cliente es requerido.")
        if not id_tipo_documento_str or not id_tipo_documento_str.isdigit():
            raise ValueError(
                "Tipo de documento es requerido y debe ser válido.")

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
ALLOWED_DOC_EXTENSIONS = {'png', 'jpg', 'jpeg',
                          'pdf', 'doc', 'docx', 'xls', 'xlsx'}
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
    """Procesa el formulario de orden de producción con transacciones atómicas"""
    errores = []
    id_usuario_registro = session.get('user_id')

    if not id_usuario_registro:
        app.logger.warning("Intento de procesar OP sin usuario autenticado.")
        # Devolver un error claro que el frontend pueda interpretar
        # Unauthorized
        return jsonify({'status': 'error', 'message': "Usuario no autenticado. Por favor, inicie sesión."}), 401

    # --- 1. Obtener y Validar Campos Principales de la OP ---
    codigo_op_str = dataForm.get('cod_op')
    id_cliente_str = dataForm.get('id_cliente')
    cantidad_op_str = dataForm.get('cantidad')
    id_empleado_str = dataForm.get('id_empleado')
    id_supervisor_str = dataForm.get('id_supervisor')  # Opcional
    fecha_str = dataForm.get('fecha')
    fecha_entrega_str = dataForm.get('fecha_entrega')

    # Campos de texto directos
    producto_val = dataForm.get('producto')
    version_val = dataForm.get('version', "1")
    cotizacion_val = dataForm.get('cotizacion')
    estado_val = dataForm.get('estado')
    medida_val = dataForm.get('medida')
    referencia_val = dataForm.get('referencia')
    odi_val = dataForm.get('odi')
    descripcion_general_op_val = dataForm.get('descripcion_general_op')
    empaque_val = dataForm.get('empaque')
    materiales_op_val = dataForm.get('materiales_op')

    # Validaciones y Conversiones para campos principales
    if not codigo_op_str or not codigo_op_str.strip():
        errores.append("El Código OP es requerido.")
        codigo_op_val = None
    else:
        try:
            codigo_op_val = int(codigo_op_str)
            # Opcional: Verificar unicidad aquí si prefieres un error temprano
            # if OrdenProduccion.query.filter_by(codigo_op=codigo_op_val, fecha_borrado=None).first():
            #     errores.append(f"El Código OP '{codigo_op_val}' ya existe.")
        except ValueError:
            errores.append("Código OP debe ser un número entero válido.")
            codigo_op_val = None

    if not id_cliente_str or not id_cliente_str.strip():
        # Asumiendo que es requerido aunque el modelo dice nullable=True
        errores.append("El Cliente es requerido.")
        id_cliente_val = None
    else:
        try:
            id_cliente_val = int(id_cliente_str)
            if not Clientes.query.filter_by(id_cliente=id_cliente_val, fecha_borrado=None).first():
                errores.append(
                    f"Cliente con ID '{id_cliente_val}' no encontrado o fue eliminado.")
        except ValueError:
            errores.append("ID Cliente debe ser un número entero válido.")
            id_cliente_val = None

    if not cantidad_op_str or not cantidad_op_str.strip():
        # Modelo: nullable=True, pero funcionalmente podría ser req.
        errores.append("La Cantidad para la OP es requerida.")
        cantidad_op_val = None
    else:
        try:
            cantidad_op_val = int(cantidad_op_str)
            if cantidad_op_val <= 0:
                errores.append(
                    "La Cantidad para la OP debe ser un número positivo.")
        except ValueError:
            errores.append(
                "Cantidad para la OP debe ser un número entero válido.")
            cantidad_op_val = None

    if not id_empleado_str or not id_empleado_str.strip():
        # Modelo: nullable=True
        errores.append("El Empleado (vendedor/responsable) es requerido.")
        id_empleado_val = None
    else:
        try:
            id_empleado_val = int(id_empleado_str)
            if not Empleados.query.filter_by(id_empleado=id_empleado_val, fecha_borrado=None).first():
                errores.append(
                    f"Empleado con ID '{id_empleado_val}' no encontrado o fue eliminado.")
        except ValueError:
            errores.append("ID Empleado debe ser un número entero válido.")
            id_empleado_val = None

    id_supervisor_val = None  # Es nullable en el modelo
    if id_supervisor_str and id_supervisor_str.strip():
        try:
            id_supervisor_val = int(id_supervisor_str)
            if not Empleados.query.filter_by(id_empleado=id_supervisor_val, fecha_borrado=None).first():
                errores.append(
                    f"Supervisor con ID '{id_supervisor_val}' no encontrado o fue eliminado.")
        except ValueError:
            # No añadir a errores si está vacío y es opcional
            errores.append("ID Supervisor debe ser un número entero válido.")

    fecha_val = None
    if not fecha_str or not fecha_str.strip():
        # Modelo: nullable=True
        errores.append("La Fecha de la OP es requerida.")
    else:
        try:
            fecha_val = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            errores.append("Formato de Fecha inválido (Use YYYY-MM-DD).")

    fecha_entrega_val = None
    if not fecha_entrega_str or not fecha_entrega_str.strip():
        # Modelo: nullable=True
        errores.append("La Fecha de Entrega es requerida.")
    else:
        try:
            fecha_entrega_val = datetime.strptime(
                fecha_entrega_str, '%Y-%m-%d').date()
        except ValueError:
            errores.append(
                "Formato de Fecha de Entrega inválido (Use YYYY-MM-DD).")

    if fecha_val and fecha_entrega_val and fecha_entrega_val < fecha_val:
        errores.append(
            "La fecha de entrega no puede ser anterior a la fecha de la OP.")

    # Validar campos de texto que consideres obligatorios funcionalmente
    # (Aunque el modelo los permita nulos, tu lógica de negocio podría requerirlos)
    if not estado_val or not estado_val.strip():
        errores.append("El Estado de la OP es requerido.")
    if not odi_val or not odi_val.strip():
        errores.append("El ODI es requerido.")
    if not descripcion_general_op_val or not descripcion_general_op_val.strip():
        errores.append("La Descripción General de la OP es requerida.")
    if not materiales_op_val or not materiales_op_val.strip():
        errores.append("Los Materiales de la OP son requeridos.")

    # --- 2. Validación de Archivos ---
    # (Tu código de validación de 'render' y 'documentos' usando validate_file)
    # Definir las rutas base para los archivos
    basepath = os.path.abspath(os.path.dirname(__file__))  # form_op.py
    # Asume que static está un nivel arriba
    static_base_path = os.path.normpath(os.path.join(basepath, '../static'))

    render_dir_relative = 'render_op'
    documentos_dir_relative = 'documentos_op'

    render_dir_abs = os.path.join(static_base_path, render_dir_relative)
    documentos_dir_abs = os.path.join(
        static_base_path, documentos_dir_relative)

    os.makedirs(render_dir_abs, exist_ok=True)
    os.makedirs(documentos_dir_abs, exist_ok=True)

    render_file_storage = files.get('render')
    path_render_a_guardar = None
    if render_file_storage and render_file_storage.filename:
        # Asumo que procesar_imagen_perfil está adaptado o es adecuado para esto
        valido, nombre_archivo_o_msg = procesar_imagen_perfil(
            render_file_storage, render_dir_relative, ALLOWED_RENDER_EXTENSIONS)
        if not valido:
            errores.append(f"Render: {nombre_archivo_o_msg}")
        elif nombre_archivo_o_msg:  # Si es valido y hay un nombre de archivo
            path_render_a_guardar = os.path.join(
                'static', render_dir_relative, nombre_archivo_o_msg).replace("\\", "/")

    documentos_a_guardar = []
    documentos_adjuntos_files = files.getlist('documentos')
    for doc_file_storage in documentos_adjuntos_files:
        if doc_file_storage and doc_file_storage.filename:
            valido, nombre_archivo_o_msg = procesar_imagen_perfil(
                doc_file_storage, documentos_dir_relative, ALLOWED_DOC_EXTENSIONS)
            if not valido:
                errores.append(
                    f"Documento '{secure_filename(doc_file_storage.filename)}': {nombre_archivo_o_msg}")
            elif nombre_archivo_o_msg:
                documentos_a_guardar.append({
                    "path": os.path.join('static', documentos_dir_relative, nombre_archivo_o_msg).replace("\\", "/"),
                    "nombre_original": secure_filename(doc_file_storage.filename)
                })

    # --- 3. Validación de Piezas Dinámicas ---
    piezas_lista_form = []
    piezas_json_str = dataForm.get('piezasData') 
    app.logger.debug(f"Contenido del campo 'piezas' (datos de piezas) recibido del formulario: '{piezas_json_str}'")

    if piezas_json_str and piezas_json_str.strip() and piezas_json_str.lower() != 'undefined' and piezas_json_str.lower() != 'null':
        try:
            parsed_data = json.loads(piezas_json_str)
            if isinstance(parsed_data, list):
                piezas_lista_form = parsed_data
                if not piezas_lista_form:
                    # Si las piezas son opcionales, esto es solo informativo.
                    app.logger.info(
                        "piezasData se parseó a una lista vacía. OP se creará sin piezas si otras validaciones pasan.")
                    # Si las piezas son OBLIGATORIAS, entonces:
                    # errores.append("Debe agregar al menos una pieza a la Orden de Producción.")
            else:
                errores.append(
                    "El formato de los datos de piezas no es una lista como se esperaba.")
                app.logger.warning(
                    f"piezasData ('{piezas_json_str}') se parseó a un tipo no esperado: {type(parsed_data)}")
        except json.JSONDecodeError:
            errores.append(
                "Error al decodificar los datos de las piezas (formato JSON inválido).")
            app.logger.warning(
                f"JSONDecodeError al parsear piezasData: '{piezas_json_str}'")
    else:
        # Si las piezas son opcionales:
        app.logger.info(
            "No se proporcionaron datos en piezasData o estaba vacío/nulo/undefined. OP se creará sin piezas si otras validaciones pasan.")
        # Si las piezas son OBLIGATORIAS:
        # errores.append("Debe agregar al menos una pieza a la Orden de Producción.")

    # Validación detallada de cada pieza si la lista no está vacía y no hay errores previos de parseo
    if not errores and piezas_lista_form:
        for idx, pieza_data_form in enumerate(piezas_lista_form, 1):
            id_pieza = pieza_data_form.get('id_pieza')
            cantidad_pieza_str = str(pieza_data_form.get('cantidad', ''))
            ids_procesos_seleccionados = pieza_data_form.get('ids_procesos', [])
            otro_proceso_nombre = pieza_data_form.get('otro_proceso')  # Nombre del nuevo proceso

            if not id_pieza or not str(id_pieza).strip():
                errores.append(f"Pieza #{idx}: El ID de la pieza es requerido.")
            else:
                try:
                    id_pieza = int(id_pieza)
                    pieza_db = Piezas.query.filter_by(id_pieza=id_pieza, fecha_borrado=None).first()
                    if not pieza_db:
                        errores.append(f"Pieza #{idx}: ID de pieza '{id_pieza}' no encontrado.")
                    else:
                        nombre_pieza_val = pieza_db.nombre_pieza  # Obtener el nombre desde la base de datos
                except ValueError:
                    errores.append(f"Pieza #{idx}: ID de pieza inválido.")
                    nombre_pieza_val = None

            if not cantidad_pieza_str.isdigit() or int(cantidad_pieza_str) <= 0:
                errores.append(f"Pieza #{idx} ('{nombre_pieza_val or 'N/A'}'): Cantidad es requerida y debe ser un número positivo.")

            if not ids_procesos_seleccionados and not (otro_proceso_nombre and otro_proceso_nombre.strip()):
                errores.append(f"Pieza #{idx} ('{nombre_pieza_val or 'N/A'}'): Debe seleccionar al menos un proceso existente o especificar un 'Otro Proceso' con nombre.")

            if 'otro_proceso_custom' in ids_procesos_seleccionados and not (otro_proceso_nombre and otro_proceso_nombre.strip()):
                errores.append(f"Pieza #{idx} ('{nombre_pieza_val or 'N/A'}'): Si selecciona la opción 'Otro Proceso', debe especificar su nombre.")

    # --- 4. Manejo de Errores Tempranos ---
    if errores:
        app.logger.warning(
            f"Errores de validación en procesar_form_op: {', '.join(errores)}")
        return jsonify({'status': 'error', 'message': ". ".join(errores) + "."}), 400

    # --- 5. Iniciar Transacción y Crear Registros ---
    try:
        app.logger.debug(
            f"Valores para OrdenProduccion: codigo_op={codigo_op_val}, id_cliente={id_cliente_val}, cantidad={cantidad_op_val}, id_empleado={id_empleado_val}, fecha={fecha_val}, estado={estado_val}")  # DEBUG
        orden = OrdenProduccion(
            codigo_op=codigo_op_val,
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
            descripcion_general=descripcion_general_op_val,
            empaque=empaque_val,
            materiales=materiales_op_val,
            id_usuario_registro=id_usuario_registro
        )
        db.session.add(orden)
        db.session.flush()  # Para obtener orden.id_op

        # Guardar Render si existe
        if path_render_a_guardar:
            nuevo_render = RendersOP(
                id_op=orden.id_op, render_path=path_render_a_guardar)
            db.session.add(nuevo_render)

        # Guardar Documentos
        for doc_info in documentos_a_guardar:
            nuevo_documento = DocumentosOP(
                id_op=orden.id_op,
                documento_path=doc_info["path"],
                documento_nombre_original=doc_info["nombre_original"]
            )
            db.session.add(nuevo_documento)

        # Procesar Piezas y sus Procesos
        for pieza_data_form in piezas_lista_form:
            id_pieza = int(pieza_data_form.get('id_pieza'))
            pieza_db = Piezas.query.filter_by(id_pieza=id_pieza, fecha_borrado=None).first()
            nombre_pieza_val = pieza_db.nombre_pieza if pieza_db else None
            cantidad_pieza_val = int(pieza_data_form.get('cantidad'))
            ids_procesos_seleccionados_val = pieza_data_form.get('ids_procesos', [])
            _otro_proceso_temp = pieza_data_form.get('otro_proceso')
            otro_proceso_nombre_val = _otro_proceso_temp.strip() if isinstance(_otro_proceso_temp, str) else ''

            ids_procesos_finales_para_pieza = []
            if isinstance(ids_procesos_seleccionados_val, list):
                for proc_id_str in ids_procesos_seleccionados_val:
                    if proc_id_str == 'otro_proceso_custom':
                        continue
                    try:
                        proc_id_int = int(proc_id_str)
                        proceso_db = Procesos.query.filter_by(id_proceso=proc_id_int, fecha_borrado=None).first()
                        if proceso_db:
                            ids_procesos_finales_para_pieza.append(proc_id_int)
                        else:
                            app.logger.warning(f"ID de proceso existente '{proc_id_str}' no encontrado o borrado, ignorado para pieza ID '{id_pieza}'.")
                    except ValueError:
                        app.logger.warning(f"ID de proceso no numérico '{proc_id_str}' ignorado para pieza ID '{id_pieza}'.")

            if otro_proceso_nombre_val:
                proceso_existente = Procesos.query.filter(func.lower(Procesos.nombre_proceso) == func.lower(otro_proceso_nombre_val), Procesos.fecha_borrado.is_(None)).first()
                if proceso_existente:
                    if proceso_existente.id_proceso not in ids_procesos_finales_para_pieza:
                        ids_procesos_finales_para_pieza.append(proceso_existente.id_proceso)
                else:
                    ultimo_proceso_cod_obj = Procesos.query.with_entities(Procesos.codigo_proceso).order_by(Procesos.id_proceso.desc()).first()
                    nuevo_codigo_num = 1
                    if ultimo_proceso_cod_obj and ultimo_proceso_cod_obj[0] and re.match(r"P\d+", ultimo_proceso_cod_obj[0]):
                        try:
                            nuevo_codigo_num = int(re.sub(r'\D', '', ultimo_proceso_cod_obj[0])) + 1
                        except:
                            max_id = db.session.query(func.max(Procesos.id_proceso)).scalar() or 0
                            nuevo_codigo_num = max_id + 1001
                    else:
                        max_id = db.session.query(func.max(Procesos.id_proceso)).scalar() or 0
                        nuevo_codigo_num = max_id + 1001

                    nuevo_codigo_proceso_str = f"P{nuevo_codigo_num:03d}"
                    while Procesos.query.filter_by(codigo_proceso=nuevo_codigo_proceso_str, fecha_borrado=None).first():
                        nuevo_codigo_num += 1
                        nuevo_codigo_proceso_str = f"P{nuevo_codigo_num:03d}"

                    nuevo_proceso_obj = Procesos(
                        codigo_proceso=nuevo_codigo_proceso_str,
                        nombre_proceso=otro_proceso_nombre_val,
                        descripcion_proceso=f"Proceso '{otro_proceso_nombre_val}' creado desde OP {orden.codigo_op}"
                    )
                    db.session.add(nuevo_proceso_obj)
                    db.session.flush()
                    if nuevo_proceso_obj.id_proceso not in ids_procesos_finales_para_pieza:
                        ids_procesos_finales_para_pieza.append(nuevo_proceso_obj.id_proceso)

            orden_pieza_obj = OrdenPiezas(
                id_op=orden.id_op,
                id_pieza=id_pieza,
                nombre_pieza_op=nombre_pieza_val,
                cantidad=cantidad_pieza_val,
                tamano=pieza_data_form.get('tamano'),
                montaje=pieza_data_form.get('montaje'),
                montaje_tamano=pieza_data_form.get('tamano_montaje'),
                material=pieza_data_form.get('material'),
                cantidad_material=pieza_data_form.get('cantidad_material'),
                descripcion_pieza=pieza_data_form.get('descripcion_pieza')
            )
            db.session.add(orden_pieza_obj)
            db.session.flush()

            for id_proc_final in set(ids_procesos_finales_para_pieza):
                db.session.add(OrdenPiezasProcesos(
                    id_orden_pieza=orden_pieza_obj.id_orden_pieza, id_proceso=id_proc_final))

        db.session.commit()
        app.logger.info(
            f"Orden de Producción {orden.codigo_op} (ID: {orden.id_op}) registrada exitosamente.")
        return jsonify({'status': 'success', 'message': 'Orden de Producción registrada exitosamente.', 'id_op': orden.id_op, 'redirect_url': url_for('lista_op', id_op=orden.id_op)}), 200

    except IntegrityError as ie:
        db.session.rollback()
        app.logger.error(
            f"Error de Integridad de BD en procesar_form_op: {str(ie)}", exc_info=True)
        # Revisar ie.orig.args o similar para mensajes específicos del motor de BD
        # Ejemplo: Comprobar si es por 'codigo_op' duplicado
        error_message = "Error de base de datos. Es posible que un valor único (como Código OP) ya exista."
        # if "Duplicate entry" in str(ie.orig) and "codigo_op" in str(ie.orig): # MySQL example
        #     error_message = f"El Código OP '{codigo_op_val}' ya está registrado."
        # 409 Conflict
        return jsonify({'status': 'error', 'message': error_message}), 409

    except SQLAlchemyError as e_sql:
        db.session.rollback()
        app.logger.error(
            f"Error de SQLAlchemy en procesar_form_op: {str(e_sql)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Error al interactuar con la base de datos.'}), 500

    except ValueError as ve:  # Errores de conversión o validación que no se atraparon antes
        db.session.rollback()
        app.logger.warning(
            f"Error de Valor en procesar_form_op (etapa final): {str(ve)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(ve)}), 400

    except Exception as e_inesperado:
        db.session.rollback()
        app.logger.error(
            f"Error inesperado en procesar_form_op: {str(e_inesperado)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Ocurrió un error inesperado al procesar la orden.'}), 500
    # El finally no es estrictamente necesario aquí si no hay recursos externos que cerrar siempre
    # y si la respuesta JSON ya se ha enviado.
    # Si se llega aquí sin un return explícito, es un error de lógica en los try/except.
    # No debería ser necesario un return None al final si todos los caminos están cubiertos.


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
            app.logger.warning(f"No se encontró la orden de producción con id_op={id_op}")
            return None

        orden, nombre_cliente, nombre_empleado_vendedor, nombre_supervisor, nombre_usuario_registro = result

        # Obtener las piezas asociadas con un solo JOIN
        piezas = db.session.query(
            OrdenPiezas,
            Piezas.nombre_pieza.label('nombre_pieza')
        ).outerjoin(
            Piezas, OrdenPiezas.id_pieza == Piezas.id_pieza
        ).filter(
            OrdenPiezas.id_op == orden.id_op,
            OrdenPiezas.fecha_borrado.is_(None)
        ).all()

        piezas_list = []
        for pieza, nombre_pieza in piezas:
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

            if not nombre_pieza:
                app.logger.warning(f"Pieza con id_pieza={pieza.id_pieza} no encontrada en tbl_piezas para id_op={id_op}")

            piezas_list.append({
                'id_orden_pieza': pieza.id_orden_pieza,
                'nombre_pieza': nombre_pieza if nombre_pieza else 'Desconocido',
                'cantidad': pieza.cantidad if pieza.cantidad else 'No especificado',
                'tamano': pieza.tamano if pieza.tamano else 'No especificado',
                'montaje': pieza.montaje if pieza.montaje else 'No especificado',
                'montaje_tamano': pieza.montaje_tamano if pieza.montaje_tamano else 'No especificado',
                'material': pieza.material if pieza.material else 'No especificado',
                'cantidad_material': pieza.cantidad_material if pieza.cantidad_material else 'No especificado',
                'descripcion_general': pieza.descripcion_pieza if pieza.descripcion_pieza else 'No especificado',  # Cambiado a descripcion_pieza
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
            'renders': renders,
            'documentos': documentos,
            'piezas': piezas_list
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

        orden = db.session.query(
            OrdenProduccion).filter_by(id_op=id_op).first()
        if not orden:
            app.logger.error(f"Orden con id_op {id_op} no encontrada")
            return jsonify({'success': False, 'message': 'Orden no encontrada'})

        # Convertir campos numéricos y validar
        codigo_op = int(data.form['cod_op']
                        ) if data.form['cod_op'] else orden.codigo_op
        id_cliente = int(
            data.form['id_cliente']) if data.form['id_cliente'] else orden.id_cliente
        cantidad = int(data.form['cantidad']
                       ) if data.form['cantidad'] else orden.cantidad
        id_empleado = int(
            data.form['id_empleado']) if data.form['id_empleado'] else orden.id_empleado
        id_supervisor = int(data.form['id_supervisor']) if data.form.get(
            'id_supervisor') and data.form['id_supervisor'].strip() else orden.id_supervisor

        # Convertir fechas
        fecha = datetime.strptime(
            data.form['fecha'], '%Y-%m-%d').date() if data.form['fecha'] else orden.fecha
        fecha_entrega = datetime.strptime(data.form['fecha_entrega'], '%Y-%m-%d').date(
        ) if data.form['fecha_entrega'] else orden.fecha_entrega

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
        # Obtener la versión actual, por defecto "0" si es None o vacío
        current_version = orden.version or "0"
        try:
            next_version = int(current_version) + 1
            orden.version = str(next_version)
        except ValueError:
            # Si la versión actual no es un número, establecer la próxima versión a "1"
            orden.version = "1"
            app.logger.warning(
                f"La versión actual de la OP {orden.id_op} no es un número válido: {current_version}. Estableciendo la próxima versión a 1.")

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
            old_renders = db.session.query(
                RendersOP).filter_by(id_op=id_op).all()
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
            render_dir = os.path.normpath(os.path.join(
                os.path.dirname(__file__), '../static/render_op'))
            os.makedirs(render_dir, exist_ok=True)
            render_path = os.path.normpath(
                os.path.join(render_dir, render_filename))
            render_file.save(render_path)
            render_path_relative = os.path.join(
                'static/render_op', render_filename).replace('\\', '/')
            nuevo_render = RendersOP(
                id_op=id_op, render_path=render_path_relative)
            db.session.add(nuevo_render)
            app.logger.debug(
                f"Archivo render guardado en: {render_path} (ruta relativa: {render_path_relative})")

        # Procesar eliminación de documentos
        if 'delete_docs[]' in data.form:
            docs_to_delete = data.form.getlist('delete_docs[]')
            for doc_id in docs_to_delete:
                doc = db.session.query(DocumentosOP).filter_by(
                    id_documento=doc_id).first()
                if doc:
                    file_path = os.path.join('static', doc.documento_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    db.session.delete(doc)
                    app.logger.debug(f"Documento eliminado: {file_path}")

        # Procesar nuevos documentos
        if 'documentos' in files:
            documentos_dir = os.path.normpath(os.path.join(
                os.path.dirname(__file__), '../static/documentos_op'))
            os.makedirs(documentos_dir, exist_ok=True)
            for doc in files.getlist('documentos'):
                if doc and doc.filename:
                    filename = secure_filename(doc.filename)
                    extension = os.path.splitext(filename)[1]
                    nuevo_name = (uuid.uuid4().hex + uuid.uuid4().hex)[:100]
                    doc_filename = f"doc_{nuevo_name}{extension}"
                    doc_path = os.path.normpath(
                        os.path.join(documentos_dir, doc_filename))
                    doc.save(doc_path)
                    doc_path_relative = os.path.join(
                        'static/documentos_op', doc_filename).replace('\\', '/')
                    nuevo_doc = DocumentosOP(
                        id_op=id_op,
                        documento_path=doc_path_relative,
                        documento_nombre_original=filename
                    )
                    db.session.add(nuevo_doc)
                    app.logger.debug(
                        f"Documento guardado en: {doc_path} (ruta relativa: {doc_path_relative})")

        # Procesar piezas
        piezas_json = data.form.get('piezas')
        if piezas_json:
            piezas = json.loads(piezas_json)
            # Eliminar todas las piezas existentes primero
            db.session.query(OrdenPiezas).filter_by(id_op=id_op).delete()
            for pieza_data in piezas:
                if not pieza_data.get('id_pieza'):
                    app.logger.error(
                        f"Pieza inválida, falta id_pieza: {pieza_data}")
                    continue
                id_pieza = int(pieza_data['id_pieza'])
                orden_pieza = OrdenPiezas(
                    id_op=id_op,
                    id_pieza=id_pieza,
                    cantidad=int(pieza_data['cabezoteCantidad']) if pieza_data.get(
                        'cabezoteCantidad') and pieza_data['cabezoteCantidad'].isdigit() else None,
                    tamano=pieza_data.get('cabezoteTamaño'),
                    montaje=pieza_data.get('cabezoteMontaje'),
                    montaje_tamano=pieza_data.get('cabezoteMontajeTamaño'),
                    material=pieza_data.get('cabezoteMaterial'),
                    cantidad_material=pieza_data.get(
                        'cabezoteCantidadMaterial'),
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
        app.logger.error(
            f"Error de conversión en procesar_actualizar_form_op: {str(ve)}")
        return jsonify({'success': False, 'message': str(ve)})
    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Se produjo un error en procesar_actualizar_form_op: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

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
        empleados_bd = query.order_by(
            Empleados.nombre_empleado,
            Empleados.apellido_empleado
        ).limit(per_page).offset(offset).all()

        return empleados_bd

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
