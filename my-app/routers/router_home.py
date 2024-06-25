from app import app
from flask import render_template, request, flash, redirect, url_for, session,  jsonify, Blueprint
from mysql.connector.errors import Error


# Importando cenexión a BD
from controllers.funciones_home import *

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
def formEmpleado():
    if 'conectado' in session:
        if 'foto_empleado' in request.files:
            foto_perfil = request.files['foto_empleado']
            exito, mensaje = procesar_form_empleado(request.form, foto_perfil)
            if exito:
                flash(mensaje, 'success')
                return redirect(url_for('lista_empleados'))
            else:
                flash(mensaje, 'error')
                return render_template(f'{PATH_URL}/form_empleado.html', dataForm=request.form)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/lista-de-empleados', methods=['GET'])
def lista_empleados():
    if 'conectado' in session:
        return render_template(f'{PATH_URL}/lista_empleados.html', empleados=sql_lista_empleadosBD())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-empleado/<int:idEmpleado>", methods=['GET'])
def detalleEmpleado(idEmpleado=None):
    if 'conectado' in session:
        # Verificamos si el parámetro idEmpleado es None o no está presente en la URL
        if idEmpleado is None:
            return redirect(url_for('inicio'))
        else:
            detalle_empleado = sql_detalles_empleadosBD(idEmpleado) or []
            return render_template(f'{PATH_URL}/detalles_empleado.html', detalle_empleado=detalle_empleado)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Buscadon de empleados
@app.route("/buscando-empleado", methods=['POST'])
def viewBuscarEmpleadoBD():
    resultadoBusqueda = buscarEmpleadoBD(request.json['busqueda'])
    if resultadoBusqueda:
        return render_template(f'{PATH_URL}/resultado_busqueda_empleado.html', dataBusqueda=resultadoBusqueda)
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
        respuestaEmpleado = buscarEmpleadoUnico(id)
        if respuestaEmpleado:
            return render_template(f'{PATH_URL}/form_empleado_update.html', respuestaEmpleado=respuestaEmpleado)
        else:
            flash('El empleado no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Recibir formulario para actulizar informacion de empleado
@app.route('/actualizar-empleado', methods=['POST'])
def actualizarEmpleado():
    resultData = procesar_actualizacion_form(request)
    if resultData:
        return redirect(url_for('lista_empleados'))


@app.route("/lista-de-usuarios", methods=['GET'])
def usuarios():
    if 'conectado' in session:
        resp_usuariosBD = lista_usuariosBD()
        return render_template('public/usuarios/lista_usuarios.html', resp_usuariosBD=resp_usuariosBD)
    else:
        return redirect(url_for('inicioCpanel'))


@app.route('/borrar-usuario/<string:id>', methods=['GET'])
def borrarUsuario(id):
    resp = eliminarUsuario(id)
    if resp:
        flash('El Usuario fue eliminado correctamente', 'success')
        return redirect(url_for('usuarios'))


@app.route('/borrar-empleado/<string:id_empleado>/<string:foto_empleado>', methods=['GET'])
def borrarEmpleado(id_empleado, foto_empleado):
    resp = eliminarEmpleado(id_empleado, foto_empleado)
    if resp:
        flash('El Empleado fue eliminado correctamente', 'success')
        return redirect(url_for('lista_empleados'))


@app.route("/descargar-informe-empleados/", methods=['GET'])
def reporteBD():
    if 'conectado' in session:
        return generarReporteExcel()
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
    
    
    
    
    
#### PROCESOS
@app.route('/registrar-proceso', methods=['GET'])
def viewFormProceso():
    if 'conectado' in session:
        return render_template('public/procesos/form_proceso.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    

@app.route('/form-registrar-proceso', methods=['POST'])
def formProceso():
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
        return render_template('public/procesos/lista_procesos.html', procesos=sql_lista_procesosBD())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-proceso/<string:codigo_proceso>", methods=['GET'])
def detalleProceso(codigo_proceso=None):
    if 'conectado' in session:
        # Verificamos si el parámetro codigo_proceso es None o no está presente en la URL
        if codigo_proceso is None:
            return redirect(url_for('inicio'))
        else:
            detalle_proceso = sql_detalles_procesosBD(codigo_proceso) or []
            return render_template('public/procesos/detalles_proceso.html', detalle_proceso=detalle_proceso)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Buscador de proceso
# @app.route("/buscando-proceso", methods=['POST'])
# def viewBuscarProcesoBD():
#     resultadoBusqueda2 = buscarProcesoBD(request.json['busqueda'])
#     if resultadoBusqueda2:
#         return render_template('public/procesos/resultado_busqueda_proceso.html', dataBusqueda2=resultadoBusqueda2)
#     else:   
#         return jsonify({'fin': 0})


@app.route("/editar-proceso/<int:id>", methods=['GET'])
def viewEditarproceso(id):
    if 'conectado' in session:
        respuestaProceso = buscarProcesoUnico(id)
        if respuestaProceso:
            return render_template('public/procesos/form_proceso_update.html', respuestaProceso=respuestaProceso)
        else:
            flash('El Proceso no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Recibir formulario para actulizar informacion de proceso
@app.route('/actualizar-proceso', methods=['POST'])
def actualizarProceso():
    resultData = procesar_actualizar_form(request)
    if resultData:
        return redirect(url_for('lista_procesos'))


# @app.route("/lista-de-usuarios", methods=['GET'])
# def usuarios():
#     if 'conectado' in session:
#         resp_usuariosBD = lista_usuariosBD()
#         return render_template('public/usuarios/lista_usuarios.html', resp_usuariosBD=resp_usuariosBD)
#     else:
#         return redirect(url_for('inicioCpanel'))


# @app.route('/borrar-usuario/<string:id>', methods=['GET'])
# def borrarUsuario(id):
#     resp = eliminarUsuario(id)
#     if resp:
#         flash('El Usuario fue eliminado correctamente', 'success')
#         return redirect(url_for('usuarios'))


@app.route('/borrar-proceso/<int:id_proceso>', methods=['GET'])
def borrarProceso(id_proceso):
    resp = eliminarProceso(id_proceso)
    if resp:
        flash('El proceso fue eliminado correctamente', 'success')
        return redirect(url_for('lista_procesos'))


# @app.route("/descargar-informe-empleados/", methods=['GET'])
# def reporteBD():
#     if 'conectado' in session:
#         return generarReporteExcel()
#     else:
#         flash('primero debes iniciar sesión.', 'error')
#         return redirect(url_for('inicio'))




#### CLIENTES
@app.route('/registrar-cliente', methods=['GET'])
def viewFormCliente():
    tipo_documento = obtener_tipo_documento()
    if 'conectado' in session:
        return render_template('public/clientes/form_cliente.html',tipo_documento=tipo_documento)
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/form-registrar-cliente', methods=['POST'])
def formCliente():
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
        return render_template('public/clientes/lista_clientes.html', clientes=sql_lista_clientesBD())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-cliente/<int:idCliente>", methods=['GET'])
def detalleCliente(idCliente=None):
    if 'conectado' in session:
        # Verificamos si el parámetro idCliente es None o no está presente en la URL
        if idCliente is None:
            return redirect(url_for('inicio'))
        else:
            detalle_cliente = sql_detalles_clientesBD(idCliente) or []
            return render_template('public/clientes/detalles_cliente.html', detalle_cliente=detalle_cliente)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Buscador de clientes
@app.route("/buscando-cliente", methods=['POST'])
def viewBuscarClienteBD():
    resultadoBusquedaCliente = buscarClienteBD(request.json['busqueda'])
    if resultadoBusquedaCliente:
        return render_template('public/clientes/resultado_busqueda_cliente.html', dataBusquedacliente=resultadoBusquedaCliente)
    else:
        return jsonify({'fin': 0})


@app.route("/editar-cliente/<int:id>", methods=['GET'])
def viewEditarCliente(id):
    if 'conectado' in session:
        respuestaCliente = buscarClienteUnico(id)
        if respuestaCliente:
            return render_template('public/clientes/form_cliente_update.html', respuestaCliente=respuestaCliente)
        else:
            flash('El cliente no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Recibir formulario para actulizar informacion de cliente
@app.route('/actualizar-cliente', methods=['POST'])
def actualizarCliente():
    resultData = procesar_actualizacion_cliente(request)
    if resultData:
        return redirect(url_for('lista_clientes'))


@app.route('/borrar-cliente/<string:id_cliente>/<string:foto_cliente>', methods=['GET'])
def borrarCliente(id_cliente, foto_cliente):
    resp = eliminarCliente(id_cliente, foto_cliente)
    if resp:
        flash('El Cliente fue eliminado correctamente', 'success')
        return redirect(url_for('lista_clientes'))


# @app.route("/descargar-informe-clientes/", methods=['GET'])
# def reporteBD():
#     if 'conectado' in session:
#         return generarReporteExcel()
#     else:
#         flash('primero debes iniciar sesión.', 'error')
#         return redirect(url_for('inicio'))





#### ACTIVIDADES
@app.route('/registrar-actividad', methods=['GET'])
def viewFormActividad():
    if 'conectado' in session:
        return render_template('public/actividades/form_actividades.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    

@app.route('/form-registrar-actividad', methods=['POST'])
def formActividad():
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
        return render_template('public/actividades/lista_actividades.html', actividades=sql_lista_actividadesBD())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-actividad/<string:codigo_actividad>", methods=['GET'])
def detalleActividad(codigo_actividad=None):
    if 'conectado' in session:
        # Verificamos si el parámetro codigo_actividad es None o no está presente en la URL
        if codigo_actividad is None:
            return redirect(url_for('inicio'))
        else:
            detalle_actividad = sql_detalles_actividadesBD(codigo_actividad) or []
            return render_template('public/actividades/detalles_actividad.html', detalle_actividad=detalle_actividad)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/editar-actividad/<int:id>", methods=['GET'])
def viewEditaractividad(id):
    if 'conectado' in session:
        respuestaActividad = buscarActividadUnico(id)
        if respuestaActividad:
            return render_template('public/actividades/form_actividad_update.html', respuestaActividad=respuestaActividad)
        else:
            flash('La Actividad no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Recibir formulario para actulizar informacion de proceso
@app.route('/actualizar-actividad', methods=['POST'])
def actualizarActividad():
    resultData = procesar_actualizar_actividad(request)
    if resultData:
        return redirect(url_for('lista_actividades'))
    else:
        # Manejar el caso en que resultData sea falso
        return "Ocurrió un error al actualizar la actividad"

@app.route('/borrar-actividad/<int:id_actividad>', methods=['GET'])
def borrarActividad(id_actividad):
    resp = eliminarActividad(id_actividad)
    if resp:
        flash('La Actividad fue eliminado correctamente', 'success')
        return redirect(url_for('lista_actividades'))







#### OPERACIóN DIARIA
@app.route('/registrar-operacion', methods=['GET', 'POST'])
def viewFormOperacion():
    if request.method == 'POST':
        id_empleado = request.form.get('id_empleado')
        nombre_empleado = obtener_nombre_empleado(id_empleado)
        return jsonify(nombre_empleado=nombre_empleado)
    else:
        id_empleados = obtener_id_empleados()
        if 'conectado' in session:
            nombre_proceso = obtener_proceso()
            nombre_actividad = obtener_actividad()
            codigo_op = obtener_op()# Llamar a la nueva función
            return render_template('public/operaciones/form_operaciones.html', nombre_proceso=nombre_proceso, id_empleados=id_empleados, nombre_actividad=nombre_actividad,codigo_op=codigo_op)
        else:
            flash('Primero debes iniciar sesión.', 'error')
            return redirect(url_for('inicio'))
        
        
@app.route('/lista-de-operaciones', methods=['GET'])
def lista_operaciones():
    if 'conectado' in session:
        return render_template('public/operaciones/lista_operaciones.html', operaciones=sql_lista_operacionesBD())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
@app.route('/form-registrar-operacion', methods=['POST'])
def formOperacion():
    if 'conectado' in session:
        resultado = procesar_form_operacion(request.form)
        if resultado:
            return redirect(url_for('lista_operaciones'))
        else:
            flash('La Operacion NO fue registrada.', 'error')
            return render_template('public/operaciones/form_operaciones.html')
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
    
@app.route("/detalles-operacion/<string:id_operacion>", methods=['GET'])
def detalleOperacion(id_operacion=None):
    if 'conectado' in session:
        # Verificamos si el parámetro id_operacion es None o no está presente en la URL
        if id_operacion is None:
            return redirect(url_for('inicio'))
        else:
            detalle_operacion = sql_detalles_operacionesBD(id_operacion) or []
            return render_template('public/operaciones/detalles_operacion.html', detalle_operacion=detalle_operacion)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
@app.route("/editar-operacion/<int:id>", methods=['GET'])
def viewEditarOperacion(id):
    if 'conectado' in session:
        respuestaOperacion = buscarOperacionUnico(id)
        if respuestaOperacion:
            return render_template('public/operaciones/form_operacion_update.html', respuestaOperacion=respuestaOperacion)
        else:
            flash('La Operacion no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
# Recibir formulario para actulizar informacion de cliente
@app.route('/actualizar-operacion', methods=['POST'])
def actualizarOperacion():
    resultData = procesar_actualizacion_operacion(request)
    if resultData:
        return redirect(url_for('lista_operaciones'))
    
@app.route('/borrar-operacion/<int:id_operacion>', methods=['GET'])
def borrarOperacion(id_operacion):
    resp = eliminarOperacion(id_operacion)
    if resp:
        flash('La operacion fue eliminada correctamente', 'success')
        return redirect(url_for('lista_operaciones'))
    



    
#### ORDER DE PRODUCCIóN
@app.route('/registrar-op', methods=['GET'])
def viewFormOp():
    if 'conectado' in session:
        clientes = sql_lista_clientesBD()
        empleados = obtener_vendedor()
        return render_template('public/ordenproduccion/form_op.html', clientes=clientes, empleados=empleados )  # Pasar datos de empleados al render_template
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route('/validar-codigo-op', methods=['POST'])
def validate_cod_op():
    documento = request.form.get('documento')
    if validar_cod_op(documento):
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@app.route('/form-registrar-op', methods=['POST'])
def formOp():
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
        return render_template('public/ordenproduccion/lista_op.html', op=sql_lista_opBD())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route("/detalles-op/<string:idOp>", methods=['GET'])
def detalleOp(idOp=None):
    if 'conectado' in session:
        # Verificamos si el parámetro codigo_op es None o no está presente en la URL
        if idOp is None:
            return redirect(url_for('inicio'))
        else:
            detalle_op = sql_detalles_opBD(idOp) or []
            return render_template('public/ordenproduccion/detalles_op.html', detalle_op=detalle_op)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    

@app.route("/editar-op/<int:id>", methods=['GET'])
def viewEditarop(id):
    if 'conectado' in session:
        respuestaOp = buscarOpUnico(id)
        if respuestaOp:
            return render_template('public/ordenproduccion/form_op_update.html', respuestaOp=respuestaOp)
        else:
            flash('La Orden de Producción no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


# Recibir formulario para actulizar informacion de la orden de producción
@app.route('/actualizar-op', methods=['POST'])
def actualizarOp():
    resultData = procesar_actualizar_form_op(request)
    if resultData:
        return redirect(url_for('lista_op'))


@app.route('/borrar-op/<int:id_op>', methods=['GET'])
def borrarOp(id_op):
    resp = eliminarOp(id_op)
    if resp:
        flash('La Orden de Producción fue eliminada correctamente', 'success')
        return redirect(url_for('lista_op'))
    
    
    

#### JORNADA
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
            codigo_op = obtener_op()# Llamar a la nueva función
            return render_template('public/jornada/form_jornadas.html', nombre_proceso=nombre_proceso, id_empleados=id_empleados, nombre_actividad=nombre_actividad,codigo_op=codigo_op)
        else:
            flash('Primero debes iniciar sesión.', 'error')
            return redirect(url_for('inicio'))
        
        
@app.route('/lista-de-jornadas', methods=['GET'])
def lista_jornadas():
    if 'conectado' in session:
        return render_template('public/jornada/lista_jornadas.html', jornadas=sql_lista_jornadasBD())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
@app.route('/form-registrar-jornada', methods=['POST'])
def formJornada():
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
def detalleJornada(id_jornada=None):
    if 'conectado' in session:
        # Verificamos si el parámetro id_jornada es None o no está presente en la URL
        if id_jornada is None:
            return redirect(url_for('inicio'))
        else:
            detalle_jornada = sql_detalles_jornadasBD(id_jornada) or []
            return render_template('public/jornada/detalles_jornada.html', detalle_jornada=detalle_jornada)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
@app.route("/editar-jornada/<int:id>", methods=['GET'])
def viewEditarJornada(id):
    if 'conectado' in session:
        respuestaJornada = buscarJornadaUnico(id)
        if respuestaJornada:
            return render_template('public/jornada/form_jornada_update.html', respuestaJornada=respuestaJornada)
        else:
            flash('La Jornada no existe.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
# Recibir formulario para actulizar informacion de la jornada
@app.route('/actualizar-jornada', methods=['POST'])
def actualizarJornada():
    resultData = procesar_actualizacion_jornada(request)
    if resultData:
        return redirect(url_for('lista_jornadas'))
    
@app.route('/borrar-jornada/<int:id_jornada>', methods=['GET'])
def borrarJornada(id_jornada):
    resp = eliminarJornada(id_jornada)
    if resp:
        flash('La Jornada fue eliminada correctamente', 'success')
        return redirect(url_for('lista_jornadas'))