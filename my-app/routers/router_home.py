# Asegúrate de importar las nuevas funciones
from controllers.funciones_home import sql_detalles_empresaBD, buscar_empresa_unica, eliminar_empresa
from werkzeug.exceptions import RequestEntityTooLarge
from app import app
import json
from flask import send_file, abort,render_template, request, flash, redirect, url_for, session, jsonify, Blueprint, request
from flask_paginate import Pagination, get_page_args
from controllers.funciones_home import get_total_operaciones, sql_lista_op_bd,  sql_lista_jornadas_bd, get_total_jornadas
from controllers.funciones_home import sql_lista_empleadosBD, get_total_empleados
from controllers.funciones_home import sql_lista_procesos_bd, get_total_procesos
from controllers.funciones_home import sql_lista_actividades_bd, get_total_actividades
from controllers.funciones_home import sql_lista_usuarios_bd, get_total_usuarios
from conexion.models import db, OPLog, Empresa, Empleados, OrdenProduccion, Tipo_Empleado,ListasCorreos,ListasMiembros, Clientes
from sqlalchemy import func, and_
from controllers.funciones_home import get_empleados_paginados, get_piezas_paginados,get_procesos_paginados, get_actividades_paginados,get_actividades_paginados_op, get_ordenes_paginadas, get_clientes_paginados

# Importando funciones desde funciones_home.py (ahora con SQLAlchemy)
from controllers.funciones_home import (get_empresas_paginadas, get_tipos_empleado_paginados, get_supervisores_paginados,get_disenadores_graficos_paginados,get_disenadores_industriales_paginados,
                                        procesar_form_empleado, procesar_form_empresa, procesar_imagen_perfil, procesar_actualizar_empresa, obtener_tipo_empleado, buscar_ordenes_produccion_bd,
                                        sql_lista_empleadosBD, sql_detalles_empleadosBD, empleados_reporte, generar_reporte_excel, sql_lista_empresasBD,
                                        buscar_empleado_bd, validate_document, buscar_empleado_unico, procesar_actualizacion_form,
                                        eliminar_empleado, sql_lista_usuarios_bd, eliminar_usuario, procesar_form_proceso, buscando_empresas,
                                        sql_lista_procesos_bd, sql_detalles_procesos_bd, buscar_proceso_unico, procesar_actualizar_form, # procesar_actualizar_form estaba duplicado
                                        eliminar_proceso, procesar_form_cliente, validar_documento_cliente, obtener_tipo_documento,
                                        procesar_imagen_cliente,  sql_detalles_clientes_bd, buscar_cliente_bd, buscar_operaciones_bd,
                                        buscar_cliente_unico, procesar_actualizacion_cliente, eliminar_cliente, procesar_form_actividad,
                                        sql_lista_actividades_bd, sql_detalles_actividades_bd, buscar_actividad_unico, procesar_actualizar_actividad,
                                        eliminar_actividad, obtener_id_empleados, obtener_nombre_empleado, obtener_proceso, obtener_actividad,
                                        procesar_form_operacion, sql_lista_operaciones_bd, sql_detalles_operaciones_bd, buscar_operacion_unico,
                                        procesar_actualizacion_operacion, eliminar_operacion, procesar_form_op, validar_cod_op, sql_lista_op_bd,
                                        sql_detalles_op_bd,  procesar_actualizar_form_op, eliminar_op, obtener_vendedor, obtener_op,
                                        procesar_form_jornada, sql_lista_jornadas_bd, sql_detalles_jornadas_bd, buscar_jornada_unico, procesar_actualizacion_jornada,
                                        eliminar_jornada, generar_codigo_op, get_jornadas_serverside,
                                        get_detalles_pieza_maestra_options, # Nueva función para el modal
                                        obtener_datos_op_para_edicion, # Importar la nueva función
                                        get_all_empleados,generar_pdf_op_func
                                        )

PATH_URL = "public/empleados"

# Empleados


@app.route('/registrar-empleado', methods=['GET'])
def viewFormEmpleado():
    if 'conectado' in session:
        tipo_empleado = obtener_tipo_empleado()
        if tipo_empleado:
            # Convertir los objetos Tipo_Empleado a diccionarios para compatibilidad con el template
            tipos_empleado = [{'id_tipo_empleado': t.id_tipo_empleado, 'tipo_empleado': t.tipo_empleado} for t in tipo_empleado]
        else:
            tipos_empleado = []
        return render_template(f'{PATH_URL}/form_empleado.html', tipos_empleado=tipos_empleado)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/form-registrar-empleado', methods=['GET', 'POST'])
def form_registrar_empleado():
    if 'conectado' in session:
        if request.method == 'POST':
            if 'foto_empleado' in request.files:
                foto_perfil = request.files['foto_empleado']
                exito, mensaje = procesar_form_empleado(request.form, foto_perfil)
                if exito:
                    flash(mensaje, 'success')
                    return redirect(url_for('lista_empleados'))
                else:
                    flash(mensaje, 'error')
                    # Pasar los datos del formulario para rellenar los campos en caso de error
                    tipos_empleado = obtener_tipo_empleado() or []
                    tipos_empleado_list = [{'id_tipo_empleado': t.id_tipo_empleado, 'tipo_empleado': t.tipo_empleado} for t in tipos_empleado]
                    return render_template('public/empleados/form_empleado.html', data_form=request.form, tipos_empleado=tipos_empleado_list)
            else:
                flash('Debe cargar una foto del empleado.', 'error')
                tipos_empleado = obtener_tipo_empleado() or []
                tipos_empleado_list = [{'id_tipo_empleado': t.id_tipo_empleado, 'tipo_empleado': t.tipo_empleado} for t in tipos_empleado]
                return render_template('public/empleados/form_empleado.html', data_form=request.form, tipos_empleado=tipos_empleado_list)
        else:
            # Cargar el formulario inicialmente
            tipos_empleado = obtener_tipo_empleado() or []
            tipos_empleado_list = [{'id_tipo_empleado': t.id_tipo_empleado, 'tipo_empleado': t.tipo_empleado} for t in tipos_empleado]
            return render_template('public/empleados/form_empleado.html', data_form=None, tipos_empleado=tipos_empleado_list)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/lista-de-empleados", methods=['GET'])
def lista_empleados():
    if 'conectado' in session:
        return render_template(f'{PATH_URL}/lista_empleados.html')
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-empleado/<int:id_empleado>", methods=['GET'])
def detalle_empleado(id_empleado=None):
    if 'conectado' in session:
        if id_empleado is None:
            return redirect(url_for('inicio'))
        else:
            detalle_empleado = sql_detalles_empleadosBD(id_empleado) or []
            return render_template(f'{PATH_URL}/detalles_empleado.html', detalle_empleado=detalle_empleado)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Búsqueda de empleados


@app.route("/buscando-empleado", methods=['POST'])
def view_buscar_empleado_bd():
    resultado_busqueda = buscar_empleado_bd(request.json['busqueda'])

    if resultado_busqueda:
        return jsonify({'data': resultado_busqueda})
    else:
        return jsonify({'data': [], 'fin': 0})


@app.route("/buscando-empleados", methods=['POST'])
def buscando_empleados():
    try:
        # Obtener parámetros de DataTables
        draw = int(request.json.get('draw', 1))
        start = int(request.json.get('start', 0))
        length = int(request.json.get('length', 10))
        search_value = request.json.get('nombre', '').strip()

        # Obtener parámetros de ordenamiento
        order = request.json.get('order', [{}])[0]
        # Por defecto, ordenar por "Nombre"
        column_idx = int(order.get('column', 2))
        direction = order.get('dir', 'asc')

        # Mapear índices de columnas a nombres de campos
        column_mapping = {
            0: None,  # Columna "#" (índice, no se ordena)
            1: Empleados.documento,
            2: Empleados.nombre_empleado,
            3: Empleados.apellido_empleado,
            4: Empresa.tipo_empresa,
            5: Empresa.nombre_empresa,
            6: Empleados.cargo,
            7: Empleados.fecha_registro,
            8: None  # Columna "Acción" (no se ordena)
        }

        # Subconsulta para obtener el registro más reciente por documento
        subquery = db.session.query(
            Empleados.documento,
            func.max(Empleados.fecha_registro).label('max_fecha')
        ).group_by(Empleados.documento).subquery()

        # Construir la consulta
        query = db.session.query(Empleados, Empresa).\
            join(Empresa, Empleados.id_empresa == Empresa.id_empresa).\
            join(subquery, and_(
                Empleados.documento == subquery.c.documento,
                Empleados.fecha_registro == subquery.c.max_fecha
            ))

        # Aplicar filtro por nombre
        if search_value:
            query = query.filter(
                Empleados.nombre_empleado.ilike(f'%{search_value}%'))

        # Obtener el total de registros sin filtrar
        total_records = query.count()

        # Aplicar ordenamiento
        if column_idx in column_mapping and column_mapping[column_idx]:
            if direction == 'desc':
                query = query.order_by(column_mapping[column_idx].desc())
            else:
                query = query.order_by(column_mapping[column_idx].asc())
        else:
            # Ordenamiento por defecto si la columna no es ordenable
            query = query.order_by(Empleados.nombre_empleado.asc())

        # Obtener el total de registros filtrados
        filtered_records = query.count()

        # Aplicar paginación
        empleados = query.offset(start).limit(length).all()

        # Formatear los datos para DataTables
        data = []
        for empleado, empresa in empleados:
            data.append({
                'id_empleado': empleado.id_empleado,
                'documento': empleado.documento,
                'nombre_empleado': empleado.nombre_empleado,
                'apellido_empleado': empleado.apellido_empleado,
                'tipo_empresa': empresa.tipo_empresa,
                'nombre_empresa': empresa.nombre_empresa,
                'cargo': empleado.cargo,
                'fecha_registro': empleado.fecha_registro.strftime('%Y-%m-%d %I:%M %p') if empleado.fecha_registro else None,
                'foto_empleado': empleado.foto_empleado if empleado.foto_empleado else '',
                'estado': 'Activo' if not empleado.fecha_borrado else 'Inactivo'
            })

        return jsonify({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data,
            'fin': 1
        })
    except Exception as e:
        app.logger.error(f"Error en buscando_empleados: {str(e)}")
        return jsonify({
            'draw': draw,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'fin': 0,
            'error': str(e)
        })


@app.route('/validate-document', methods=['POST'])
def validate_document_route():
    documento = request.form.get('documento')
    if validate_document(documento):
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})


@app.route("/editar-empleado/<int:id>", methods=['GET'])
def viewEditarEmpleado(id):
    if 'conectado' in session:
        respuestaEmpleado = buscar_empleado_unico(id)
        if respuestaEmpleado:
            tipos_empleado = obtener_tipo_empleado()
            return render_template(f'{PATH_URL}/form_empleado_update.html', respuestaEmpleado=respuestaEmpleado, tipos_empleado=tipos_empleado)
        else:
            flash('El empleado no existe o esta inactivo.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/actualizar-empleado/<int:id>', methods=['GET', 'POST'])
def actualizar_empleado(id):
    if 'conectado' in session:
        if request.method == 'POST':
            result, message = procesar_actualizacion_form(request)
            if result:
                flash(message, 'success')
                return redirect(url_for('lista_empleados'))
            else:
                flash(message, 'error')
                # Obtener los tipos de empleado para el formulario
                tipo_empleado = obtener_tipo_empleado()
                if tipo_empleado:
                    tipos_empleado = [{'id_tipo_empleado': t.id_tipo_empleado, 'tipo_empleado': t.tipo_empleado} for t in tipo_empleado]
                else:
                    tipos_empleado = []
                # Obtener el empleado para mostrar los datos
                empleado = db.session.query(Empleados).filter_by(id_empleado=id).first()
                return render_template(f'{PATH_URL}/form_empleado.html', respuestaEmpleado=empleado, tipos_empleado=tipos_empleado)
        else:
            # Método GET: Mostrar el formulario con los datos del empleado
            empleado = db.session.query(Empleados).filter_by(id_empleado=id).first()
            if empleado:
                tipo_empleado = obtener_tipo_empleado()
                if tipo_empleado:
                    tipos_empleado = [{'id_tipo_empleado': t.id_tipo_empleado, 'tipo_empleado': t.tipo_empleado} for t in tipo_empleado]
                else:
                    tipos_empleado = []
                return render_template(f'{PATH_URL}/form_empleado.html', respuestaEmpleado=empleado, tipos_empleado=tipos_empleado)
            else:
                return render_template(f'{PATH_URL}/form_empleado.html', respuestaEmpleado=None)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/lista-de-usuarios", methods=['GET'])
def usuarios():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(
            page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        resp_usuariosBD = sql_lista_usuarios_bd(page=page, per_page=per_page)
        total = get_total_usuarios()  # Usa la función optimizada
        pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/usuarios/lista_usuarios.html', resp_usuariosBD=resp_usuariosBD, pagination=pagination)
    else:
        return redirect(url_for('inicio'))


@app.route('/borrar-usuario/<string:id>', methods=['GET'])
def borrar_usuario(id):
    resp = eliminar_usuario(id)
    if resp:
        flash('El Usuario fue eliminado correctamente', 'success')
        return redirect(url_for('usuarios'))


@app.route('/borrar-empleado/<string:id_empleado>/<string:foto_empleado>', methods=['GET'])
def borrar_empleado(id_empleado, foto_empleado):
    resp = eliminar_empleado(id_empleado, foto_empleado)
    if resp:
        flash('El Empleado fue eliminado correctamente', 'success')
    else:
        flash('No se pudo eliminar el empleado. Intenta de nuevo.', 'error')
    # Siempre redirigir, incluso si falla
    return redirect(url_for('lista_empleados'))


@app.route("/descargar-informe-empleados/", methods=['GET'])
def reporte_bd():
    if 'conectado' in session:
        return generar_reporte_excel()
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

# Procesos


@app.route('/registrar-proceso', methods=['GET'])
def viewFormProceso():
    if 'conectado' in session:
        return render_template('public/procesos/form_proceso.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/form-registrar-proceso', methods=['POST'])
def form_proceso():
    if 'conectado' in session:
        resultado = procesar_form_proceso(request.form)
        if resultado:
            return redirect(url_for('lista_procesos'))
        else:
            flash('El proceso NO fue registrado.', 'error')
            return render_template('public/procesos/form_proceso.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/lista-de-procesos', methods=['GET'])
def lista_procesos():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(
            page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        procesos = sql_lista_procesos_bd(page=page, per_page=per_page)
        total = get_total_procesos()  # Usa la función optimizada
        pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/procesos/lista_procesos.html', procesos=procesos, pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-proceso/<string:codigo_proceso>", methods=['GET'])
def detalle_proceso(codigo_proceso=None):
    if 'conectado' in session:
        if codigo_proceso is None:
            return redirect(url_for('inicio'))
        else:
            detalle_proceso = sql_detalles_procesos_bd(codigo_proceso) or []
            return render_template('public/procesos/detalles_proceso.html', detalle_proceso=detalle_proceso)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/editar-proceso/<int:id>", methods=['GET'])
def viewEditarproceso(id):
    if 'conectado' in session:
        respuestaProceso = buscar_proceso_unico(id)
        if respuestaProceso:
            return render_template('public/procesos/form_proceso_update.html', respuestaProceso=respuestaProceso)
        else:
            flash('El Proceso no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/actualizar-proceso', methods=['POST'])
def actualizar_proceso():
    result_data = procesar_actualizar_form(request)
    if result_data:
        return redirect(url_for('lista_procesos'))


@app.route('/borrar-proceso/<int:id_proceso>', methods=['GET'])
def borrar_proceso(id_proceso):
    success, message = eliminar_proceso(id_proceso)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('lista_procesos'))

# Clientes


@app.route('/registrar-cliente', methods=['GET'])
def viewFormCliente():
    tipo_documento = obtener_tipo_documento()
    if 'conectado' in session:
        return render_template('public/clientes/form_cliente.html', tipo_documento=tipo_documento)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/form-registrar-cliente', methods=['POST'])
def form_cliente():
    if 'conectado' in session:
        if 'foto_cliente' in request.files:
            foto_perfil_cliente = request.files['foto_cliente']
            resultado = procesar_form_cliente(
                request.form, foto_perfil_cliente)
            if resultado:
                return redirect(url_for('lista_clientes'))
            else:
                flash('El cliente NO fue registrado.', 'error')
                return render_template('public/clientes/form_cliente.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/validar-documento-cliente', methods=['POST'])
def validate_document_cliente():
    documento = request.form.get('documento')
    if validar_documento_cliente(documento):
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})


@app.route('/lista-de-clientes', methods=['GET'])
def lista_clientes():
    if 'conectado' in session:
        return render_template('public/clientes/lista_clientes.html')
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-cliente/<int:id_cliente>", methods=['GET'])
def detalle_cliente(id_cliente=None):
    if 'conectado' in session:
        if id_cliente is None:
            return redirect(url_for('inicio'))
        else:
            detalle_cliente = sql_detalles_clientes_bd(id_cliente) or []
            return render_template('public/clientes/detalles_cliente.html', detalle_cliente=detalle_cliente)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

# Búsqueda de clientes


@app.route("/buscando-cliente", methods=['POST'])
def view_buscar_cliente_bd():
    try:
        data = request.get_json()
        app.logger.debug(f"Datos recibidos: {data}")

        search = data.get('busqueda', '')
        search_date = data.get('fecha', '')
        draw = data.get('draw', 1)
        start = data.get('start', 0)
        length = data.get('length', 10)
        # Valor por defecto si no se envía
        order = data.get('order', [{'column': 0, 'dir': 'desc'}])

        clientes, total, total_filtered = buscar_cliente_bd(
            search, start, length)

        response = {
            "draw": int(draw),
            "recordsTotal": total,
            "recordsFiltered": total_filtered,
            "data": clientes,
            "fin": 1 if clientes else 0
        }
        app.logger.debug(f"Respuesta enviada: {response}")
        return jsonify(response)

    except Exception as e:
        app.logger.error(f"Error en /buscando-cliente: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/editar-cliente/<int:id>", methods=['GET'])
def viewEditarCliente(id):
    if 'conectado' in session:
        respuestaCliente = buscar_cliente_unico(id)
        tipo_documento = obtener_tipo_documento() # Obtener la lista de tipos de documento
        if respuestaCliente:
            return render_template('public/clientes/form_cliente_update.html', respuestaCliente=respuestaCliente, tipo_documento=tipo_documento)
        else:
            flash('El cliente no existe.', 'error')
            return redirect(url_for('lista_clientes')) # Redirigir a la lista, no a inicio
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/actualizar-cliente', methods=['POST'])
def actualizar_cliente():
    result_data = procesar_actualizacion_cliente(request)
    if result_data:
        flash('Cliente actualizado correctamente.', 'success')
        return redirect(url_for('lista_clientes'))
    else:
        flash('Error al actualizar el cliente. Intente de nuevo.', 'error')
        # Necesitamos el ID para redirigir de nuevo al formulario de edición
        id_cliente = request.form.get('id_cliente')
        if id_cliente:
            return redirect(url_for('viewEditarCliente', id=id_cliente))
        else:
            return redirect(url_for('lista_clientes')) # Fallback si no hay ID


@app.route('/borrar-cliente/<string:id_cliente>/<string:foto_cliente>', methods=['GET'])
def borrar_cliente(id_cliente, foto_cliente):
    resp = eliminar_cliente(id_cliente, foto_cliente)
    if resp:
        flash('El Cliente fue eliminado correctamente', 'success')
    else:
        flash('No se pudo eliminar el cliente. Intenta de nuevo.', 'error')
    # Siempre redirigir, incluso si falla
    return redirect(url_for('lista_clientes'))

# Actividades


@app.route('/registrar-actividad', methods=['GET'])
def viewFormActividad():
    if 'conectado' in session:
        return render_template('public/actividades/form_actividades.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/form-registrar-actividad', methods=['POST'])
def form_actividad():
    if 'conectado' in session:
        resultado = procesar_form_actividad(request.form)
        if resultado:
            return redirect(url_for('lista_actividades'))
        else:
            flash('La Actividad NO fue registrada.', 'error')
            return render_template('public/actividades/form_actividades.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/lista-de-actividades', methods=['GET'])
def lista_actividades():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(
            page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        actividades = sql_lista_actividades_bd(page=page, per_page=per_page)
        total = get_total_actividades()  # Usa la función optimizada
        pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/actividades/lista_actividades.html', actividades=actividades, pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-actividad/<string:codigo_actividad>", methods=['GET'])
def detalle_actividad(codigo_actividad=None):
    if 'conectado' in session:
        if codigo_actividad is None:
            return redirect(url_for('inicio'))
        else:
            detalle_actividad = sql_detalles_actividades_bd(
                codigo_actividad) or []
            return render_template('public/actividades/detalles_actividad.html', detalle_actividad=detalle_actividad)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/editar-actividad/<int:id>", methods=['GET'])
def viewEditaractividad(id):
    if 'conectado' in session:
        respuesta_actividad = buscar_actividad_unico(id)
        if respuesta_actividad:
            return render_template('public/actividades/form_actividad_update.html', respuestaActividad=respuesta_actividad)
        else:
            flash('La Actividad no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/actualizar-actividad', methods=['POST'])
def actualizar_actividad():
    result_data = procesar_actualizar_actividad(request)
    if result_data:
        return redirect(url_for('lista_actividades'))
    else:
        return "Ocurrió un error al actualizar la actividad"


@app.route('/borrar-actividad/<int:id_actividad>', methods=['GET'])
def borrar_actividad(id_actividad):
    resp = eliminar_actividad(id_actividad)
    if resp:
        flash('La Actividad fue eliminada correctamente', 'success')
        return redirect(url_for('lista_actividades'))

# Operación Diaria


@app.route('/registrar-operacion', methods=['GET', 'POST'])
def viewFormOperacion():
    if request.method == 'POST':
        id_empleado = request.form.get('id_empleado')
        nombre_empleado = obtener_nombre_empleado(id_empleado)
        return jsonify(nombre_empleado=nombre_empleado)
    else:
        if 'conectado' in session:
            return render_template('public/operaciones/form_operaciones.html')
        else:
            flash('Primero debes iniciar sesión.', 'error')
            return redirect(url_for('inicio'))


@app.route('/form-registrar-operacion', methods=['POST'])
def form_operacion():
    if 'conectado' not in session or 'user_id' not in session:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

    resultado = procesar_form_operacion(request.form)
    if resultado == 1:
        flash('La operación fue registrada correctamente.', 'success')
        return redirect(url_for('lista_operaciones'))
    elif isinstance(resultado, str):  # Si es un mensaje de error
        flash(resultado, 'error')
        return render_template('public/operaciones/form_operaciones.html')
    else:
        flash('La Operación NO fue registrada. Verifica los datos e intenta de nuevo.', 'error')
        return render_template('public/operaciones/form_operaciones.html')




@app.route('/lista-de-operaciones', methods=['GET'])
def lista_operaciones():
    if 'conectado' in session:
        return render_template('public/operaciones/lista_operaciones.html')
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/buscando-operaciones', methods=['POST'])
def buscar_operaciones():
    try:
        data = request.get_json()
        app.logger.debug(f"Datos recibidos: {data}")

        empleado = data.get('empleado', '')
        fecha = data.get('fecha', '')
        hora = data.get('hora', '')
        draw = data.get('draw', 1)
        start = data.get('start', 0)
        length = data.get('length', 10)
        order = data.get('order', [{'column': 0, 'dir': 'desc'}])

        operaciones, total, total_filtered = buscar_operaciones_bd(
            empleado, fecha, hora, start, length, order)

        response = {
            "draw": int(draw),
            "recordsTotal": total,
            "recordsFiltered": total_filtered,
            "data": operaciones,
            "fin": 1 if operaciones else 0
        }
        app.logger.debug(f"Respuesta enviada: {response}")
        return jsonify(response)

    except Exception as e:
        app.logger.error(f"Error en /buscando-operaciones: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/detalles-operacion/<string:id_operacion>", methods=['GET'])
def detalle_operacion(id_operacion=None):
    if 'conectado' not in session:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

    if id_operacion is None:
        flash('ID de operación no proporcionado.', 'error')
        return redirect(url_for('inicio'))

    detalle_operacion = sql_detalles_operaciones_bd(id_operacion)
    if detalle_operacion is None:
        flash('No se encontró la operación solicitada.', 'error')
        detalle_operacion = []

    return render_template('public/operaciones/detalles_operacion.html', detalle_operacion=detalle_operacion)


@app.route("/editar-operacion/<int:id>", methods=['GET', 'POST'])
def view_editar_operacion(id):
    if 'conectado' not in session:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

    if request.method == 'GET':
        respuestaOperacion = buscar_operacion_unico(id)
        if respuestaOperacion:
            return render_template('public/operaciones/form_operacion_update.html', respuestaOperacion=respuestaOperacion)
        else:
            flash('La Operación no existe.', 'error')
            return redirect(url_for('inicio'))

    if request.method == 'POST':
        result = procesar_actualizacion_operacion(request)
        if result == 1:
            flash('Operación actualizada exitosamente.', 'success')
            return redirect(url_for('lista_operaciones'))
        else:
            flash('Error al actualizar la operación. Inténtalo de nuevo.', 'error')
            return redirect(url_for('view_editar_operacion', id=id))


@app.route('/actualizar-operacion', methods=['POST'])
def actualizar_operacion():
    result_data = procesar_actualizacion_operacion(request)
    if result_data:
        return redirect(url_for('lista_operaciones'))


@app.route('/borrar-operacion/<int:id_operacion>', methods=['GET'])
def borrar_operacion(id_operacion):
    resp = eliminar_operacion(id_operacion)
    if resp:
        flash('La operacion fue eliminada correctamente', 'success')
        return redirect(url_for('lista_operaciones'))

# Orden de Producción


@app.route('/registrar-op', methods=['GET'])
def viewFormOp():
    if 'conectado' in session:
        # Usamos la versión paginada, pero aquí solo necesitamos una lista
        clientes = buscar_cliente_bd()
        empleados = obtener_vendedor()
        codigo_op = generar_codigo_op()  # Generar el código de OP
        return render_template('public/ordenproduccion/form_op.html', clientes=clientes, empleados=empleados, codigo_op=codigo_op)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/validar-codigo-op', methods=['POST'])
def validate_cod_op():
    codigo_op = request.form.get('documento')
    if validar_cod_op(codigo_op):
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})


@app.route('/form-registrar-op', methods=['POST'])
def form_op():
    if 'conectado' in session:
        try:
            # procesar_form_op ahora devuelve una tupla (respuesta_json, status_code)
            respuesta_json, status_code = procesar_form_op(request.form, request.files)
            return respuesta_json, status_code
        except RequestEntityTooLarge:
            app.logger.error("Error: Archivo demasiado grande en /form-registrar-op")
            return jsonify({'status': 'error', 'message': 'Uno o más archivos exceden el tamaño máximo permitido (5MB).'}), 413
        except Exception as e:
            app.logger.error(f"Error inesperado en /form-registrar-op: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Ocurrió un error inesperado en el servidor.'}), 500
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/lista-de-op', methods=['GET'])
def lista_op():
    if 'conectado' in session:
        return render_template('public/ordenproduccion/lista_op.html')
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-op/<string:codigo_op>", methods=['GET'])
def detalle_op(codigo_op=None):
    if 'conectado' not in session:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

    if codigo_op is None:
        flash('Código de orden no proporcionado.', 'error')
        return redirect(url_for('inicio'))

    app.logger.debug(f"Obteniendo detalles para codigo_op: {codigo_op}")
    detalle_op = sql_detalles_op_bd(codigo_op)
    return render_template('public/ordenproduccion/detalles_op.html', detalle_op=detalle_op)


@app.route("/editar-op/<string:codigo_op>", methods=['GET'])
def viewEditarop(codigo_op=None): # Esta será la única función para esta ruta
    if 'conectado' not in session or not session.get('conectado'):
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

    if codigo_op is None:
        flash('Código de orden no proporcionado.', 'error')
        return redirect(url_for('inicio'))

    app.logger.debug(f"Accediendo a editar OP con codigo_op: {codigo_op}")
    # Asegúrate de que la función obtener_datos_op_para_edicion esté importada correctamente al inicio del archivo.
    # from controllers.funciones_home import obtener_datos_op_para_edicion
    resultado_carga = obtener_datos_op_para_edicion(codigo_op)
    
    datos_op = None
    if isinstance(resultado_carga, tuple) and len(resultado_carga) == 2:
        datos_op = resultado_carga[0]
        status_code = resultado_carga[1]
        if status_code != 200:
            flash(datos_op.get('message', 'Error al cargar la orden de producción para edición.'), 'danger')
            return redirect(url_for('lista_op'))
    elif isinstance(resultado_carga, dict) and 'status' in resultado_carga and resultado_carga['status'] == 'error':
        flash(resultado_carga.get('message', 'Error al cargar la orden de producción para edición.'), 'danger')
        return redirect(url_for('lista_op'))
    elif isinstance(resultado_carga, dict): # Si solo devuelve el dict de datos (caso no esperado pero cubierto)
         datos_op = resultado_carga
    else:
        flash('Respuesta inesperada al cargar datos de la orden.', 'danger')
        return redirect(url_for('lista_op'))

    if not datos_op: # Chequeo adicional por si algo falló en la asignación anterior
        flash('Orden de producción no encontrada o error fatal al cargar sus datos.', 'danger')
        return redirect(url_for('lista_op'))
 
    # La variable datos_op ya contiene toda la información estructurada necesaria.
    page_title = f"Editar Orden de Producción #{datos_op.get('codigo_op', '')}"
    
    return render_template('public/ordenproduccion/form_op_update.html',
                           op_data=datos_op, # Cambiado de datos_op a op_data
                           page_title=page_title)
 
@app.route('/actualizar-op/<string:codigo_op>', methods=['POST'])
def actualizar_op(codigo_op):
    # Pasar codigo_op a la función de procesamiento
    result_data = procesar_actualizar_form_op(codigo_op, request.form, request.files)
    if isinstance(result_data, dict):
        return jsonify(result_data)
    else:
        return jsonify({'success': False, 'message': 'Error desconocido al procesar la solicitud'})

@app.route('/borrar-op/<int:id_op>', methods=['GET'])
def borrar_op(id_op):
    if 'conectado' not in session:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

    resultado = eliminar_op(id_op)
    if resultado == 1:
        flash('Orden de producción eliminada correctamente.', 'success')
    else:
        flash('No se pudo eliminar la orden de producción.', 'error')

    return redirect(url_for('lista_op'))


@app.route('/buscando-ordenes-produccion', methods=['POST'])
def buscando_ordenes_produccion():
    if 'conectado' not in session:
        return jsonify({"error": "No autorizado", "data": []}), 401

    # Obtener parámetros enviados por DataTables
    draw = request.json.get('draw', 1)
    start = request.json.get('start', 0)
    length = request.json.get('length', 10)
    search_codigo_op = request.json.get('codigo_op', '')
    search_fecha = request.json.get('fecha', '')
    search_nombre_cliente = request.json.get('nombre_cliente', '')

    # Llamar a la función ajustada
    result = sql_lista_op_bd(
        draw=draw,
        start=start,
        length=length,
        search_codigo_op=search_codigo_op,
        search_fecha=search_fecha,
        search_nombre_cliente=search_nombre_cliente
    )

    return jsonify(result)
@app.route('/buscando-jornadas', methods=['POST'])
def buscando_jornadas_route(): # Renombrada para evitar conflicto si 'buscando_jornadas' ya existe como función
    if 'conectado' not in session:
        return jsonify({'error': 'Usuario no autenticado'}), 401
    try:
        data = request.get_json()
        draw = data.get('draw', 1)
        start = data.get('start', 0)
        length = data.get('length', 10)
        search_empleado = data.get('empleado', '').strip()
        search_fecha = data.get('fecha', '').strip()
        # Asegúrate de que 'order' exista y tenga al menos un elemento.
        order_info = data.get('order')
        if not order_info or not isinstance(order_info, list) or len(order_info) == 0:
            order_info = [{'column': 1, 'dir': 'asc'}] # Orden por defecto si no se proporciona

        # Llama a la función del controlador
        jornadas_data, total_records, filtered_records = get_jornadas_serverside(
            draw=draw,
            start=start,
            length=length,
            search_empleado=search_empleado,
            search_fecha=search_fecha,
            order_info=order_info[0] # Pasa el primer diccionario de ordenamiento
        )

        return jsonify({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': jornadas_data
        })
    except Exception as e:
        app.logger.error(f"Error en /buscando-jornadas: {str(e)}")
        # Considera devolver un error más específico o registrar más detalles
        return jsonify({'error': 'Ocurrió un error al procesar la solicitud.', 'details': str(e)}), 500

# Jornada


@app.route('/registrar-jornada', methods=['GET', 'POST'])
def viewFormJornada():
    if request.method == 'POST':
        id_empleado = request.form.get('id_empleado')
        nombre_empleado = obtener_nombre_empleado(id_empleado)
        return jsonify(nombre_empleado=nombre_empleado)
    else:
        id_empleados = obtener_id_empleados()
        if 'conectado' in session:
            nombre_proceso = obtener_proceso()
            nombre_actividad = obtener_actividad()
            codigo_op = obtener_op()  # Llamar a la nueva función
            return render_template('public/jornada/form_jornadas.html', nombre_proceso=nombre_proceso, id_empleados=id_empleados, nombre_actividad=nombre_actividad, codigo_op=codigo_op)
        else:
            flash('Primero debes iniciar sesión.', 'error')
            return redirect(url_for('inicio'))


@app.route('/lista-de-jornadas', methods=['GET'])
def lista_jornadas():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(
            page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        jornadas = sql_lista_jornadas_bd(page=page, per_page=per_page)
        total = get_total_jornadas()  # Usa la función optimizada
        pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/jornada/lista_jornadas.html', jornadas=jornadas, pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/form-registrar-jornada', methods=['POST'])
def form_jornada():
    if 'conectado' in session:
        try:
            resultado = procesar_form_jornada(request.form)
            if resultado:
                flash('Jornada registrada correctamente', 'success')
                return redirect(url_for('lista_jornadas'))
            else:
                flash('La Jornada NO fue registrada.', 'error')
                return render_template('public/jornada/form_jornadas.html')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Ocurrió un error en form_jornada: {e}")
            flash(f"Error al registrar la jornada: {e}", 'error')
            return render_template('public/jornada/form_jornadas.html')
        else:
            flash('primero debes iniciar sesión.', 'error')
            return redirect(url_for('inicio'))


@app.route("/detalles-jornada/<string:id_jornada>", methods=['GET'])
def detalle_jornada(id_jornada=None):
    if 'conectado' in session:
        if id_jornada is None:
            return redirect(url_for('inicio'))
        else:
            detalle_jornada = sql_detalles_jornadas_bd(id_jornada) or []
            return render_template('public/jornada/detalles_jornada.html', detalle_jornada=detalle_jornada)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/editar-jornada/<int:id>", methods=['GET'])
def viewEditarJornada(id):
    if 'conectado' in session:
        respuesta_jornada = buscar_jornada_unico(id)
        app.logger.debug(f"Respuesta de buscar_jornada_unico en la RUTA viewEditarJornada: {respuesta_jornada}") # Log para ver el contenido
        if respuesta_jornada:
            # Asegurarse de que el nombre de la variable coincida con el que espera el template
            return render_template('public/jornada/form_jornada_update.html', respuestaJornada=respuesta_jornada)
        else:
            app.logger.debug(f"respuesta_jornada es None o Falsy en la RUTA viewEditarJornada, mostrando flash.") # Log
            flash('La Jornada no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/actualizar-jornada', methods=['POST'])
def actualizar_jornada():
    result_data = procesar_actualizacion_jornada(request)
    if result_data:
        return redirect(url_for('lista_jornadas'))
@app.route('/actualizar-jornada/<int:id_jornada>', methods=['POST'])
def actualizar_jornada_post(id_jornada):
    if 'conectado' not in session:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
    if request.method == 'POST':
        # Aquí llamaremos a la función que procesa la actualización en funciones_home.py
        # Asumimos que se llamará procesar_actualizacion_jornada y que recibirá el id y request.form
        exito, mensaje = procesar_actualizacion_jornada(id_jornada, request.form)
        if exito:
            flash(mensaje, 'success')
            return redirect(url_for('lista_jornadas'))
        else:
            flash(mensaje, 'error')
            # Si falla, volvemos a cargar el formulario de edición con los datos actuales
            # para que el usuario pueda corregir.
            respuestaJornada = buscar_jornada_unico(id_jornada) # Re-obtener datos para el form
            return render_template('public/jornada/form_jornada_update.html', respuestaJornada=respuestaJornada)
    # Si no es POST, redirigir o manejar como error, aunque esta ruta es solo para POST.
    return redirect(url_for('lista_jornadas'))


@app.route('/borrar-jornada/<int:id_jornada>', methods=['GET'])
def borrar_jornada(id_jornada):
    resp = eliminar_jornada(id_jornada)
    if resp:
        flash('La Jornada fue eliminada correctamente', 'success')
        return redirect(url_for('lista_jornadas'))


# Rutas API para cargar opciones dinámicamente
@app.route('/api/empleados', methods=['GET'])
def api_empleados():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")

    empleados, total_empleados = get_empleados_paginados(page, per_page, search)
    empleados_data = [
        {
            'id_empleado': emp.id_empleado,
            'nombre_empleado': f"{emp.nombre_empleado} {emp.apellido_empleado or ''}".strip(),
            'empresa': emp.empresa.nombre_empresa if emp.empresa else None,
            'tipo_empleado': emp.tipo_empleado_ref.tipo_empleado if emp.tipo_empleado_ref else None
        }
        for emp in empleados
    ]
    more = (page * per_page) < total_empleados
    return jsonify({'empleados': empleados_data, 'pagination': {'more': more}, 'total': total_empleados})


@app.route('/api/empleados/all', methods=['GET'])
def api_all_empleados():
    if 'conectado' in session:
        empleados = get_all_empleados()
        return jsonify(empleados)
    return jsonify({"error": "No autorizado"}), 401


@app.route('/api/supervisores', methods=['GET'])
def api_supervisores():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    supervisores = get_supervisores_paginados(page, per_page, search)
    return jsonify({'supervisores': supervisores})


@app.route('/api/disenadores_graficos', methods=['GET'])
def api_disenadores_graficos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    disenadores_graficos = get_disenadores_graficos_paginados(page, per_page, search)
    return jsonify({'disenadores_graficos': disenadores_graficos})

@app.route('/api/disenadores_industriales', methods=['GET'])
def api_disenadores_industriales():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    disenadores_industriales = get_disenadores_industriales_paginados(page, per_page, search)
    return jsonify({'disenadores_industriales': disenadores_industriales})


@app.route('/api/procesos', methods=['GET'])
def api_procesos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")

    procesos, total_procesos = get_procesos_paginados(page, per_page, search)
    procesos_data = [
        {
            'id_proceso': proc.id_proceso,
            'nombre_proceso': proc.nombre_proceso.upper()
        }
        for proc in procesos
    ]
    more = (page * per_page) < total_procesos
    return jsonify({'procesos': procesos_data, 'pagination': {'more': more}, 'total': total_procesos})


@app.route('/api/piezas', methods=['GET'])
def api_piezas():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")

    piezas = get_piezas_paginados(page, per_page, search)
    piezas_data = [
        {
            'id_pieza': piez.id_pieza,
            'nombre_pieza': piez.nombre_pieza.upper()
        }
        for piez in piezas
    ]
    return jsonify({'piezas': piezas_data})


@app.route('/api/actividades_op', methods=['GET'])
def api_actividades_op():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    id_procesos = request.args.get('id_proceso', None)  # Puede ser None o una cadena como "1,2,3"
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}, id_procesos={id_procesos}")

    actividades_data = get_actividades_paginados_op(page, per_page, search, id_procesos)
    return jsonify(actividades_data)

@app.route('/api/actividades', methods=['GET'])
def api_actividades():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    id_proceso = request.args.get('id_proceso', None, type=int)

    paginated_actividades = get_actividades_paginados(page, per_page, search, id_proceso)
    
    actividades = paginated_actividades.items
    total_actividades = paginated_actividades.total

    actividades_data = [
        {
            'id_actividad': str(act.id_actividad),
            'nombre_actividad': act.nombre_actividad.upper()
        }
        for act in actividades
    ]
    
    return jsonify({
        'actividades': actividades_data,
        'total': total_actividades
    })



@app.route('/api/ordenes-produccion', methods=['GET'])
def api_ordenes_produccion():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")

    ordenes_data, total_ordenes = get_ordenes_paginadas(page, per_page, search)
    more = (page * per_page) < total_ordenes
    return jsonify({'ordenes': ordenes_data, 'pagination': {'more': more}, 'total': total_ordenes})


@app.route('/api/clientes', methods=['GET'])
def api_clientes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(
        f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    clientes, total_clientes = get_clientes_paginados(page, per_page, search)
    more = (page * per_page) < total_clientes
    return jsonify({'clientes': clientes, 'pagination': {'more': more}})

@app.route('/api/detalles-pieza-maestra-opciones', methods=['GET'])
def api_detalles_pieza_maestra_opciones():
    grupo = request.args.get('grupo', type=str)
    if not grupo:
        return jsonify({'status': 'error', 'message': 'Parámetro "grupo" es requerido.'}), 400
    
    # Esta función necesita ser creada en funciones_home.py
    options = get_detalles_pieza_maestra_options(grupo)
    # Se espera que 'options' sea una lista de diccionarios, ej: [{'id': 'valor_detalle', 'text': 'valor_detalle'}]
    return jsonify(options)


# Listas para registrar empleados

@app.route('/api/empresas', methods=['GET'])
def api_empresas():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    id_empresa = request.args.get('id', None, type=int)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}, id={id_empresa}")
    empresas_data = get_empresas_paginadas(page, per_page, search, id_empresa)
    return jsonify(empresas_data)


@app.route('/api/tipos-empleado', methods=['GET'])
def api_tipos_empleado():
    try:
        tipos = Tipo_Empleado.query.filter_by(fecha_borrado=None).order_by(Tipo_Empleado.id_tipo_empleado.asc()).all()
        return jsonify({'tipos_empleado': [{'id_tipo_empleado': t.id_tipo_empleado, 'tipo_empleado': t.tipo_empleado} for t in tipos]})
    except Exception as e:
        app.logger.error(f"Error en api_tipos_empleado: {e}")
        return jsonify({'tipos_empleado': []})


@app.route('/api/users/all', methods=['GET'])
def api_all_users():
    if 'conectado' in session:
        users = get_all_empleados()
        return jsonify(users)
    # Si no está conectado, la redirección (302) puede ocurrir por un decorador
    # o una configuración de la app. Devolver un 401 es más apropiado para APIs.
    return jsonify({"error": "No autorizado"}), 401


# EMPRESAS

@app.route('/registrar-empresa', methods=['GET'])
def viewFormEmpresa():
    if 'conectado' in session:
        return render_template('public/empresas/form_empresa.html')
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/validar-nit-empresa', methods=['POST'])
def validar_nit_empresa():
    try:
        nit = request.form.get('nit')
        if not nit:
            return jsonify({'exists': False, 'error': 'El NIT es requerido.'}), 400

        # Verificar si el NIT ya existe
        empresa = db.session.query(Empresa).filter_by(
            nit=nit, fecha_borrado=None).first()
        if empresa:
            return jsonify({'exists': True, 'error': 'El NIT ya está registrado.'}), 400

        return jsonify({'exists': False})

    except Exception as e:
        app.logger.error(f"Error en /validar-nit-empresa: {str(e)}")
        return jsonify({'exists': False, 'error': 'Error al validar el NIT: ' + str(e)}), 500


@app.route('/form-registrar-empresa', methods=['POST'])
def form_registrar_empresa():
    if 'conectado' in session:
        resultado = procesar_form_empresa(request.form)
        if resultado == 1:
            flash('La empresa fue registrada correctamente.', 'success')
            # Cambiado de 'inicio' a 'lista_empresas'
            return redirect(url_for('lista_empresas'))
        elif isinstance(resultado, str):
            flash(resultado, 'error')
            return render_template('public/empresas/form_empresa.html', data_form=request.form)
        else:
            flash(
                'La empresa NO fue registrada. Verifica los datos e intenta de nuevo.', 'error')
            return render_template('public/empresas/form_empresa.html', data_form=request.form)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/lista-de-empresas', methods=['GET'])
def lista_empresas():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(
            page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        result = sql_lista_empresasBD(page=page, per_page=per_page)
        if result is None:
            flash('Error al cargar la lista de empresas.', 'error')
            return redirect(url_for('inicio'))

        empresas, total = result
        pagination = Pagination(
            page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/empresas/lista_empresas.html', empresas=empresas, pagination=pagination)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-empresa/<int:id_empresa>", methods=['GET'])
def detalle_empresa(id_empresa=None):
    if 'conectado' in session:
        if id_empresa is None:
            return redirect(url_for('inicio'))
        else:
            detalle_empresa = sql_detalles_empresaBD(id_empresa)
            if detalle_empresa:
                return render_template('public/empresas/detalles_empresa.html', detalle_empresa=detalle_empresa)
            else:
                flash('La empresa no existe.', 'error')
                return redirect(url_for('lista_empresas'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/editar-empresa/<int:id>", methods=['GET'])
def viewEditarEmpresa(id):
    if 'conectado' in session:
        respuestaEmpresa = buscar_empresa_unica(id)
        if respuestaEmpresa:
            return render_template('public/empresas/form_empresa_update.html', respuestaEmpresa=respuestaEmpresa)
        else:
            flash('La empresa no existe.', 'error')
            return redirect(url_for('lista_empresas'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/borrar-empresa/<int:id_empresa>', methods=['GET'])
def borrar_empresa(id_empresa):
    if 'conectado' in session:
        resp = eliminar_empresa(id_empresa)
        if resp:
            flash('La empresa fue eliminada correctamente', 'success')
        else:
            flash('No se pudo eliminar la empresa. Intenta de nuevo.', 'error')
        return redirect(url_for('lista_empresas'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/actualizar-empresa', methods=['POST'])
def actualizar_empresa():
    if 'conectado' in session:
        resultado = procesar_actualizar_empresa(request)
        if resultado == 1:
            flash('La empresa fue actualizada correctamente.', 'success')
            return redirect(url_for('lista_empresas'))
        else:
            flash(resultado, 'error')
            return redirect(url_for('viewEditarEmpresa', id=request.form.get('id_empresa')))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/buscando-empresas', methods=['POST'])
def buscando_empresas_route():
    if 'conectado' in session:
        data = request.get_json()
        draw = data.get('draw', 1)
        start = data.get('start', 0)
        length = data.get('length', 10)
        search_value = data.get('search', {}).get('value', '')
        order = data.get('order', [{}])[0]
        order_column = int(order.get('column', 1))
        order_direction = order.get('dir', 'desc')
        # Obtener el valor del filtro empresa
        filter_empresa = data.get('empresa', '')

        result = buscando_empresas(
            draw, start, length, search_value, order_column, order_direction, filter_empresa)
        return jsonify(result)
    else:
        return jsonify({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "fin": 0,
            "error": "No autorizado"
        })


@app.route('/versions-op/<int:id_op>', methods=['GET'])
def versions_op(id_op):
    if 'conectado' not in session:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
    # Consultar la orden para verificar existencia
    orden = OrdenProduccion.query.filter_by(id_op=id_op, fecha_borrado=None).first()
    if not orden:
        flash(f'Orden de Producción con ID {id_op} no encontrada.', 'error')
        return redirect(url_for('lista_op'))
    
    # Consultar los logs para esta OP
    logs = OPLog.query.filter_by(id_op=id_op).order_by(OPLog.version_number.desc()).all()
    
    return render_template('public/ordenproduccion/versions_op.html', logs=logs, id_op=id_op, orden=orden)


@app.route('/generar-pdf-op/<string:codigo_op>', methods=['GET'])
def generar_pdf_op(codigo_op):
    # Obtener detalles de la OP desde tu función real
    detalle_op = sql_detalles_op_bd(codigo_op)
    if not detalle_op:
        abort(404)

    # Llamar a la función en funciones_home.py para generar el buffer
    buffer = generar_pdf_op_func(detalle_op, codigo_op)

    # Enviar el archivo PDF
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"OP_{codigo_op}.pdf",
        mimetype='application/pdf'
    )
    
    
# Obtener todas las listas y sus miembros
@app.route('/api/listas-correos', methods=['GET'])
def get_listas_correos():
    listas = ListasCorreos.query.all()
    resultado = []
    for lista in listas:
        miembros_ids = [m.id_empleado for m in lista.miembros]
        resultado.append({
            'id_lista': lista.id_lista,
            'nombre_lista': lista.nombre_lista,
            'miembros': miembros_ids
        })
    return jsonify(resultado)

# Crear una nueva lista
@app.route('/api/listas-correos/crear', methods=['POST'])
def crear_lista_correo():
    data = request.json
    nombre = data.get('nombre')
    ids_empleados = data.get('ids_empleados', []) # Array de IDs [1, 5, 20]

    if not nombre or not ids_empleados:
        return jsonify({'status': 'error', 'message': 'Faltan datos'}), 400

    nueva_lista = ListasCorreos(nombre_lista=nombre)
    db.session.add(nueva_lista)
    db.session.flush() # Para obtener el ID de la nueva lista

    for id_emp in ids_empleados:
        nuevo_miembro = ListasMiembros(id_lista=nueva_lista.id_lista, id_empleado=id_emp)
        db.session.add(nuevo_miembro)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Grupo creado correctamente'})

# Eliminar una lista
@app.route('/api/listas-correos/eliminar/<int:id_lista>', methods=['DELETE'])
def eliminar_lista_correo(id_lista):
    lista = ListasCorreos.query.get(id_lista)
    if lista:
        db.session.delete(lista)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Grupo eliminado'})
    return jsonify({'status': 'error', 'message': 'Grupo no encontrado'}), 404