from app import app
from flask import render_template, request, flash, redirect, url_for, session, jsonify, Blueprint
from flask_paginate import Pagination, get_page_args
from controllers.funciones_home import get_total_operaciones,sql_lista_op_bd, get_total_op, sql_lista_jornadas_bd, get_total_jornadas
from controllers.funciones_home import sql_lista_empleadosBD, get_total_empleados
from controllers.funciones_home import sql_lista_procesos_bd, get_total_procesos
from controllers.funciones_home import sql_lista_clientes_bd, get_total_clientes
from controllers.funciones_home import sql_lista_actividades_bd, get_total_actividades
from controllers.funciones_home import sql_lista_usuarios_bd, get_total_usuarios

from controllers.funciones_home import get_empleados_paginados, get_procesos_paginados, get_actividades_paginados, get_ordenes_paginadas


# Importando funciones desde funciones_home.py (ahora con SQLAlchemy)
from controllers.funciones_home import (
    procesar_form_empleado, procesar_imagen_perfil, obtener_tipo_empleado,
    sql_lista_empleadosBD, sql_detalles_empleadosBD, empleados_reporte, generar_reporte_excel,
    buscar_empleado_bd, validate_document, buscar_empleado_unico, procesar_actualizacion_form,
    eliminar_empleado, sql_lista_usuarios_bd, eliminar_usuario, procesar_form_proceso,
    sql_lista_procesos_bd, sql_detalles_procesos_bd, buscar_proceso_unico, procesar_actualizar_form as procesar_actualizar_form_proceso,
    eliminar_proceso, procesar_form_cliente, validar_documento_cliente, obtener_tipo_documento,
    procesar_imagen_cliente, sql_lista_clientes_bd, sql_detalles_clientes_bd, buscar_cliente_bd,
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
def form_empleado():
    if 'conectado' in session:
        if 'foto_empleado' in request.files:
            foto_perfil = request.files['foto_empleado']
            exito, mensaje = procesar_form_empleado(request.form, foto_perfil)
            if exito:
                flash(mensaje, 'success')
                return redirect(url_for('lista_empleados'))
            else:
                flash(mensaje, 'error')
                return render_template(f'{PATH_URL}/form_empleado.html', data_form=request.form)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/lista-de-empleados', methods=['GET'])
def lista_empleados():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        empleados = sql_lista_empleadosBD(page=page, per_page=per_page)
        total = get_total_empleados()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template(f'{PATH_URL}/lista_empleados.html', empleados=empleados, pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
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
        return render_template(f'{PATH_URL}/resultado_busqueda_empleado.html', data_busqueda=resultado_busqueda)
    else:
        return jsonify({'fin': 0})

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
        respuesta_empleado = buscar_empleado_unico(id)
        if respuesta_empleado:
            return render_template(f'{PATH_URL}/form_empleado_update.html', respuesta_empleado=respuesta_empleado)
        else:
            flash('El empleado no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/actualizar-empleado', methods=['POST'])
def actualizar_empleado():
    result_data = procesar_actualizacion_form(request)
    if result_data:
        return redirect(url_for('lista_empleados'))

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
        return redirect(url_for('lista_empleados'))

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
        respuesta_proceso = buscar_proceso_unico(id)
        if respuesta_proceso:
            return render_template('public/procesos/form_proceso_update.html', respuesta_proceso=respuesta_proceso)
        else:
            flash('El Proceso no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/actualizar-proceso', methods=['POST'])
def actualizar_proceso():
    result_data = procesar_actualizar_form_proceso(request)
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
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10  # Registros por página
        clientes = sql_lista_clientes_bd(page=page, per_page=per_page)
        total = get_total_clientes()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/clientes/lista_clientes.html', clientes=clientes, pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
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
    resultado_busqueda_cliente = buscar_cliente_bd(request.json['busqueda'])
    if resultado_busqueda_cliente:
        return render_template('public/clientes/resultado_busqueda_cliente.html', data_busqueda_cliente=resultado_busqueda_cliente)
    else:
        return jsonify({'fin': 0})

@app.route("/editar-cliente/<int:id>", methods=['GET'])
def viewEditarCliente(id):
    if 'conectado' in session:
        respuesta_cliente = buscar_cliente_unico(id)
        if respuesta_cliente:
            return render_template('public/clientes/form_cliente_update.html', respuesta_cliente=respuesta_cliente)
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
        return redirect(url_for('lista_clientes'))

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
            return render_template('public/actividades/form_actividad_update.html', respuesta_actividad=respuesta_actividad)
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
    if 'conectado' in session:
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
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/lista-de-operaciones', methods=['GET'])
def lista_operaciones():
    if 'conectado' in session:
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page=10  # Registros por página
        operaciones = sql_lista_operaciones_bd(page=page, per_page=per_page)
        total = get_total_operaciones()  # Usa la función optimizada
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('public/operaciones/lista_operaciones.html', 
                                operaciones=operaciones, 
                                pagination=pagination)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/detalles-operacion/<string:id_operacion>", methods=['GET'])
def detalle_operacion(id_operacion=None):
    if 'conectado' in session:
        if id_operacion is None:
            return redirect(url_for('inicio'))
        else:
            detalle_operacion = sql_detalles_operaciones_bd(id_operacion) or []
            return render_template('public/operaciones/detalles_operacion.html', detalle_operacion=detalle_operacion)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/editar-operacion/<int:id>", methods=['GET'])
def view_editar_operacion(id):
    if 'conectado' in session:
        respuesta_operacion = buscar_operacion_unico(id)
        if respuesta_operacion:
            return render_template('public/operaciones/form_operacion_update.html', respuesta_operacion=respuesta_operacion)
        else:
            flash('La Operacion no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

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
        clientes = sql_lista_clientes_bd()  # Usamos la versión paginada, pero aquí solo necesitamos una lista
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
            return redirect(url_for('lista_op'))
        else:
            flash('La op NO fue registrada.', 'error')
            return render_template('public/ordenproduccion/form_op.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
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

@app.route("/detalles-op/<string:id_op>", methods=['GET'])
def detalle_op(id_op=None):
    if 'conectado' in session:
        if id_op is None:
            return redirect(url_for('inicio'))
        else:
            detalle_op = sql_detalles_op_bd(id_op) or []
            return render_template('public/ordenproduccion/detalles_op.html', detalle_op=detalle_op)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/editar-op/<int:id>", methods=['GET'])
def viewEditarop(id):
    if 'conectado' in session:
        respuesta_op = buscar_op_unico(id)
        if respuesta_op:
            return render_template('public/ordenproduccion/form_op_update.html', respuesta_op=respuesta_op)
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
        return redirect(url_for('lista_op'))

@app.route('/borrar-op/<int:id_op>', methods=['GET'])
def borrar_op(id_op):
    resp = eliminar_op(id_op)
    if resp:
        flash('La Orden de Producción fue eliminada correctamente', 'success')
        return redirect(url_for('lista_op'))

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
    page = request.args.get('page', None, type=int)
    per_page = request.args.get('per_page', None, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    empleados = get_empleados_paginados(page, per_page, search)
    return jsonify({'empleados': empleados})

@app.route('/api/procesos', methods=['GET'])
def api_procesos():
    page = request.args.get('page', None, type=int)
    per_page = request.args.get('per_page', None, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    procesos = get_procesos_paginados(page, per_page, search)
    return jsonify({'procesos': procesos})

@app.route('/api/actividades', methods=['GET'])
def api_actividades():
    page = request.args.get('page', None, type=int)
    per_page = request.args.get('per_page', None, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    actividades = get_actividades_paginados(page, per_page, search)
    return jsonify({'actividades': actividades})

@app.route('/api/ordenes-produccion', methods=['GET'])
def api_ordenes_produccion():
    page = request.args.get('page', None, type=int)
    per_page = request.args.get('per_page', None, type=int)
    search = request.args.get('search', '', type=str)
    app.logger.debug(f"Parámetros recibidos: page={page}, per_page={per_page}, search={search}")
    ordenes = get_ordenes_paginadas(page, per_page, search)
    return jsonify({'ordenes': ordenes})