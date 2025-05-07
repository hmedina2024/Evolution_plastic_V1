from app import app
from flask import render_template, request, flash, redirect, url_for, session, jsonify, Blueprint,request
from flask_paginate import Pagination, get_page_args
from controllers.funciones_home import get_total_operaciones,sql_lista_op_bd, get_total_op, sql_lista_jornadas_bd, get_total_jornadas
from controllers.funciones_home import sql_lista_empleadosBD, get_total_empleados
from controllers.funciones_home import sql_lista_procesos_bd, get_total_procesos
from controllers.funciones_home import sql_lista_actividades_bd, get_total_actividades
from controllers.funciones_home import sql_lista_usuarios_bd, get_total_usuarios
from conexion.models import db, Empresa,Empleados,OrdenProduccion,Tipo_Empleado,Clientes
from controllers.funciones_home import get_empleados_paginados, get_procesos_paginados, get_actividades_paginados, get_ordenes_paginadas,get_clientes_paginados

# Importando funciones desde funciones_home.py (ahora con SQLAlchemy)
from controllers.funciones_home import (get_empresas_paginadas, get_tipos_empleado_paginados,get_supervisores_paginados,
    procesar_form_empleado, procesar_form_empresa, procesar_imagen_perfil,procesar_actualizar_empresa, obtener_tipo_empleado,buscar_ordenes_produccion_bd,
    sql_lista_empleadosBD, sql_detalles_empleadosBD, empleados_reporte, generar_reporte_excel,sql_lista_empresasBD,
    buscar_empleado_bd, validate_document, buscar_empleado_unico, procesar_actualizacion_form,
    eliminar_empleado, sql_lista_usuarios_bd, eliminar_usuario, procesar_form_proceso,buscando_empresas,
    sql_lista_procesos_bd, sql_detalles_procesos_bd, buscar_proceso_unico, procesar_actualizar_form,
    eliminar_proceso, procesar_form_cliente, validar_documento_cliente, obtener_tipo_documento,
    procesar_imagen_cliente,  sql_detalles_clientes_bd, buscar_cliente_bd,buscar_operaciones_bd,
    buscar_cliente_unico, procesar_actualizacion_cliente, eliminar_cliente, procesar_form_actividad,
    sql_lista_actividades_bd, sql_detalles_actividades_bd, buscar_actividad_unico, procesar_actualizar_actividad,
    eliminar_actividad, obtener_id_empleados, obtener_nombre_empleado, obtener_proceso, obtener_actividad,
    procesar_form_operacion, sql_lista_operaciones_bd, sql_detalles_operaciones_bd, buscar_operacion_unico,
    procesar_actualizacion_operacion, eliminar_operacion, procesar_form_op, validar_cod_op, sql_lista_op_bd,
    sql_detalles_op_bd, buscar_op_unico, procesar_actualizar_form_op, eliminar_op, obtener_vendedor, obtener_op,
    procesar_form_jornada, sql_lista_jornadas_bd, sql_detalles_jornadas_bd, buscar_jornada_unico, procesar_actualizacion_jornada,
    eliminar_jornada
)

PATH_URL = "public/empleados"

#### Empleados
@app.route('/registrar-empleado', methods=['GET'])
def viewFormEmpleado():
    if 'conectado' in session:
        tipo_empleado = obtener_tipo_empleado()
        return render_template(f'{PATH_URL}/form_empleado.html', tipo_empleado=tipo_empleado)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/form-registrar-empleado', methods=['POST'])
def form_registrar_empleado():
    if 'conectado' in session:
        if 'foto_empleado' in request.files:
            foto_perfil = request.files['foto_empleado']
            exito, mensaje = procesar_form_empleado(request.form, foto_perfil)
            if exito:
                flash(mensaje, 'success')
                return redirect(url_for('lista_empleados'))
            else:
                flash(mensaje, 'error')
                # Pasar los datos del formulario para rellenar los campos en caso de error
                return render_template('public/empleados/form_empleado.html', data_form=request.form)
        else:
            flash('Debe cargar una foto del empleado.', 'error')
            return render_template('public/empleados/form_empleado.html', data_form=request.form)
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
        column_idx = int(order.get('column', 2))  # Por defecto, ordenar por "Nombre"
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
            7: None  # Columna "Acción" (no se ordena)
        }

        # Construir la consulta
        query = db.session.query(Empleados, Empresa).\
            join(Empresa, Empleados.id_empresa == Empresa.id_empresa).\
            filter(Empleados.fecha_borrado.is_(None))

        # Aplicar filtro por nombre
        if search_value:
            query = query.filter(Empleados.nombre_empleado.ilike(f'%{search_value}%'))

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
                'foto_empleado': empleado.foto_empleado if empleado.foto_empleado else ''
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
            return render_template(f'{PATH_URL}/form_empleado_update.html', respuestaEmpleado=respuestaEmpleado)
        else:
            flash('El empleado no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/actualizar-empleado/<int:id>', methods=['POST'])
def actualizar_empleado(id):
    if 'conectado' in session:
        result, message = procesar_actualizacion_form(request)
        if result:
            flash(message, 'success')
        else:
            flash(message, 'error')
        return redirect(url_for('lista_empleados'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/lista-de-usuarios", methods=['GET'])
def usuarios():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        resp_usuariosBD = sql_lista_usuarios_bd(page=page, per_page=per_page)
        total = get_total_usuarios()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
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
    return redirect(url_for('lista_empleados'))  # Siempre redirigir, incluso si falla

@app.route("/descargar-informe-empleados/", methods=['GET'])
def reporte_bd():
    if 'conectado' in session:
        return generar_reporte_excel()
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

#### Procesos
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
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        procesos = sql_lista_procesos_bd(page=page, per_page=per_page)
        total = get_total_procesos()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
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
    resp = eliminar_proceso(id_proceso)
    if resp:
        flash('El proceso fue eliminado correctamente', 'success')
        return redirect(url_for('lista_procesos'))

#### Clientes
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
            resultado = procesar_form_cliente(request.form, foto_perfil_cliente)
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
        order = data.get('order', [{'column': 0, 'dir': 'desc'}])  # Valor por defecto si no se envía

        clientes, total, total_filtered = buscar_cliente_bd(search, search_date, start, length, order)

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
        if respuestaCliente:
            return render_template('public/clientes/form_cliente_update.html', respuestaCliente=respuestaCliente)
        else:
            flash('El cliente no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/actualizar-cliente', methods=['POST'])
def actualizar_cliente():
    result_data = procesar_actualizacion_cliente(request)
    if result_data:
        return redirect(url_for('lista_clientes'))

@app.route('/borrar-cliente/<string:id_cliente>/<string:foto_cliente>', methods=['GET'])
def borrar_cliente(id_cliente, foto_cliente):
    resp = eliminar_cliente(id_cliente, foto_cliente)
    if resp:
        flash('El Cliente fue eliminado correctamente', 'success')
    else:
        flash('No se pudo eliminar el cliente. Intenta de nuevo.', 'error')
    return redirect(url_for('lista_clientes'))  # Siempre redirigir, incluso si falla

#### Actividades
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
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        actividades = sql_lista_actividades_bd(page=page, per_page=per_page)
        total = get_total_actividades()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
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
            detalle_actividad = sql_detalles_actividades_bd(codigo_actividad) or []
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

#### Operación Diaria
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

        operaciones, total, total_filtered = buscar_operaciones_bd(empleado, fecha, hora, start, length, order)

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

#### Orden de Producción
@app.route('/registrar-op', methods=['GET'])
def viewFormOp():
    if 'conectado' in session:
        clientes = buscar_cliente_bd()  # Usamos la versión paginada, pero aquí solo necesitamos una lista
        empleados = obtener_vendedor()
        return render_template('public/ordenproduccion/form_op.html', clientes=clientes, empleados=empleados)
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
        resultado = procesar_form_op(request.form)
        if resultado:
            flash('Orden de producción registrada correctamente.', 'success')  # Mensaje de éxito
            return redirect(url_for('lista_op'))
        else:
            flash('La orden de producción NO fue registrada.', 'error')
            return render_template('public/ordenproduccion/form_op.html')
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/lista-de-op', methods=['GET'])
def lista_op():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page=10  # Registros por página
        op = sql_lista_op_bd(page=page, per_page=per_page)
        total = get_total_op()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/ordenproduccion/lista_op.html', op=op, pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/detalles-op/<int:id_op>", methods=['GET'])  # Cambiamos string a int
def detalle_op(id_op=None):
    if 'conectado' in session:
        if id_op is None:
            return redirect(url_for('inicio'))
        else:
            app.logger.debug(f"Obteniendo detalles para id_op: {id_op}")
            detalle_op = sql_detalles_op_bd(id_op) or []
            return render_template('public/ordenproduccion/detalles_op.html', detalle_op=detalle_op)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/editar-op/<int:id>", methods=['GET'])
def viewEditarop(id):
    print(f"Recibido ID: {id}")
    if 'conectado' in session:
        respuestaOp = buscar_op_unico(id)
        if respuestaOp:
            return render_template('public/ordenproduccion/form_op_update.html', respuestaOp=respuestaOp)
        else:
            flash('La Orden de Producción no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/actualizar-op', methods=['POST'])
def actualizar_op():
    result_data = procesar_actualizar_form_op(request)
    if result_data:
        flash('Orden de producción actualizada correctamente', 'success')
        return redirect(url_for('lista_op'))
    else:
        flash('No se pudo actualizar la orden de producción', 'error')
        return redirect(url_for('lista_op'))

@app.route('/borrar-op/<int:id_op>', methods=['GET'])
def borrar_op(id_op):
    resp = eliminar_op(id_op)
    if resp:
        flash('La Orden de Producción fue eliminada correctamente', 'success')
        return redirect(url_for('lista_op'))

@app.route('/buscando-ordenes-produccion', methods=['POST'])
def buscando_ordenes_produccion():
    try:
        # Obtener los datos de la solicitud
        data = request.get_json()
        app.logger.debug(f"Datos recibidos: {data}")

        # Extraer parámetros del JSON
        codigo_op = data.get('codigo_op', '')
        fecha = data.get('fecha', '')
        draw = data.get('draw', 1)
        start = data.get('start', 0)
        length = data.get('length', 10)
        order = data.get('order', [{'column': 1, 'dir': 'desc'}])  # Por defecto: Cod. OP descendente

        # Llamar a la función de búsqueda con el parámetro de ordenamiento
        ordenes, total, total_filtered = buscar_ordenes_produccion_bd(codigo_op, fecha, start, length, order)

        # Preparar la respuesta
        response = {
            'draw': int(draw),
            'recordsTotal': total,
            'recordsFiltered': total_filtered,
            'data': ordenes,
            'fin': 1 if ordenes else 0
        }
        app.logger.debug(f"Respuesta enviada: {response}")
        return jsonify(response)

    except Exception as e:
        app.logger.error(f"Error en /buscando-ordenes-produccion: {str(e)}")
        return jsonify({"error": str(e)}), 500

#### Jornada
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
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        jornadas = sql_lista_jornadas_bd(page=page, per_page=per_page)
        total = get_total_jornadas()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/jornada/lista_jornadas.html', jornadas=jornadas, pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/form-registrar-jornada', methods=['POST'])
def form_jornada():
    if 'conectado' in session:
        resultado = procesar_form_jornada(request.form)
        if resultado:
            return redirect(url_for('lista_jornadas'))
        else:
            flash('La Jornada NO fue registrada.', 'error')
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
        if respuesta_jornada:
            return render_template('public/jornada/form_jornada_update.html', respuesta_jornada=respuesta_jornada)
        else:
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
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    
    empleados = get_empleados_paginados(page, per_page, search)
    empleados_data = [
        {
            'id_empleado': emp.id_empleado,
            'nombre_empleado': f"{emp.nombre_empleado} {emp.apellido_empleado or ''}".strip(),
            'empresa': emp.empresa.nombre_empresa if emp.empresa else None,
            'tipo_empleado': emp.tipo_empleado_ref.tipo_empleado if emp.tipo_empleado_ref else None
        }
        for emp in empleados
    ]
    return jsonify({'empleados': empleados_data})

@app.route('/api/supervisores', methods=['GET'])
def api_supervisores():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    supervisores = get_supervisores_paginados(page, per_page, search)
    return jsonify({'supervisores': supervisores})

@app.route('/api/procesos', methods=['GET'])
def api_procesos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    
    procesos = get_procesos_paginados(page, per_page, search)
    procesos_data = [
        {
            'id_proceso': proc.id_proceso,
            'nombre_proceso': proc.nombre_proceso
        }
        for proc in procesos
    ]
    return jsonify({'procesos': procesos_data})

@app.route('/api/actividades', methods=['GET'])
def api_actividades():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    
    actividades = get_actividades_paginados(page, per_page, search)
    actividades_data = [
        {
            'id_actividad': act.id_actividad,
            'nombre_actividad': act.nombre_actividad
        }
        for act in actividades
    ]
    return jsonify({'actividades': actividades_data})

@app.route('/api/ordenes-produccion', methods=['GET'])
def api_ordenes_produccion():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    
    ordenes = get_ordenes_paginadas(page, per_page, search)
    ordenes_data = [
        {
            'id_op': ord.id_op,
            'codigo_op': ord.codigo_op,
            'cliente': ord.cliente.nombre_cliente if ord.cliente else None
        }
        for ord in ordenes
    ]
    return jsonify({'ordenes': ordenes_data})


@app.route('/api/clientes', methods=['GET'])
def api_clientes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    clientes = get_clientes_paginados(page, per_page, search)
    return jsonify({'clientes': clientes})


### Listas para registrar empleados
        
@app.route('/api/empresas', methods=['GET'])
def api_empresas():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    id_empresa = request.args.get('id', None, type=int)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}, id={id_empresa}")
    empresas = get_empresas_paginadas(page, per_page, search, id_empresa)
    return jsonify({'empresas': empresas})

@app.route('/api/tipos-empleado', methods=['GET'])
def api_tipos_empleado():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    id_empresa = request.args.get('id_empresa', None, type=int)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}, id_empresa={id_empresa}")
    tipos = get_tipos_empleado_paginados(page, per_page, search, id_empresa)
    return jsonify({'tipos_empleado': tipos})



### EMPRESAS

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
        empresa = db.session.query(Empresa).filter_by(nit=nit, fecha_borrado=None).first()
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
            return redirect(url_for('lista_empresas'))  # Cambiado de 'inicio' a 'lista_empresas'
        elif isinstance(resultado, str):
            flash(resultado, 'error')
            return render_template('public/empresas/form_empresa.html', data_form=request.form)
        else:
            flash('La empresa NO fue registrada. Verifica los datos e intenta de nuevo.', 'error')
            return render_template('public/empresas/form_empresa.html', data_form=request.form)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
    
@app.route('/lista-de-empresas', methods=['GET'])
def lista_empresas():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        result = sql_lista_empresasBD(page=page, per_page=per_page)
        if result is None:
            flash('Error al cargar la lista de empresas.', 'error')
            return redirect(url_for('inicio'))
        
        empresas, total = result
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/empresas/lista_empresas.html', empresas=empresas, pagination=pagination)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
    
from controllers.funciones_home import sql_detalles_empresaBD, buscar_empresa_unica, eliminar_empresa  # Asegúrate de importar las nuevas funciones

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
        filter_empresa = data.get('empresa', '')  # Obtener el valor del filtro empresa

        result = buscando_empresas(draw, start, length, search_value, order_column, order_direction, filter_empresa)
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


