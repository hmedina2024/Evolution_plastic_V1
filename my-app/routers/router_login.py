# my-app/routers/router_login.py (Modificado)
from app import app
from flask import render_template, request, flash, redirect, url_for, session, jsonify
from conexion.models import db, Users
from werkzeug.security import check_password_hash
from controllers.funciones_login import (
    recibe_insert_register_user, procesar_update_perfil, info_perfil_session, data_login_sesion,
    # Importar constantes de retorno
    RESULTADO_EXITO, RESULTADO_ERROR_GENERAL, RESULTADO_ERROR_EMAIL_EXISTE,
    RESULTADO_ERROR_PASS_ACTUAL, RESULTADO_ERROR_PASS_NO_COINCIDEN, RESULTADO_ERROR_PASS_OBLIGATORIA,
    RESULTADO_ERROR_EMAIL_NUEVO_EXISTE # Importar si se usa explícitamente
)
# Importar el decorador
# Asegúrate de que la carpeta 'utils' exista en 'my-app' o ajusta la ruta
try:
    from utils.decorators import login_required
except ImportError:
    # Manejo básico si la estructura de carpetas es diferente o hay un error
    # Podrías loggear un error aquí si es necesario
    # Definir un decorador dummy para evitar errores si la importación falla
    def login_required(f):
        return f
    app.logger.warning("No se pudo importar 'login_required' desde 'utils.decorators'. Las rutas no estarán protegidas por sesión.")


PATH_URL_LOGIN = "public/login"

@app.route('/', methods=['GET'])
def inicio():
    if 'conectado' in session:
        # Si está conectado, muestra el panel principal
        return render_template('public/base_cpanel.html', data_login=data_login_sesion())
    else:
        # Si no, muestra la página de login
        return render_template(f'{PATH_URL_LOGIN}/base_login.html')

@app.route('/mi-perfil', methods=['GET'])
@login_required # Aplicar decorador
def perfil():
    # La comprobación de sesión la hace el decorador
    return render_template(f'public/perfil/perfil.html', info_perfil_session=info_perfil_session())

# Crear cuenta de usuario (ruta pública)
@app.route('/register-user', methods=['GET'])
def cpanel_register_user():
    # Considera si esta ruta debería ser accesible solo para admins logueados
    # Si es así, añade @login_required y quizás una verificación de rol
    return render_template(f'{PATH_URL_LOGIN}/auth_register.html')

# Recuperar cuenta de usuario (ruta pública)
@app.route('/recovery-password', methods=['GET'])
def cpanelRecoveryPassUser():
    if 'conectado' in session: # Evita que usuarios logueados vean esto
        return redirect(url_for('inicio'))
    else:
        return render_template(f'{PATH_URL_LOGIN}/auth_forgot_password.html')

# Guardar registro de usuario (ruta pública o protegida?)
@app.route('/saved-register', methods=['POST'])
def cpanel_register_user_bd():
    # Considera añadir @login_required y verificación de rol si solo admins pueden registrar
    if request.method == 'POST' and 'name_surname' in request.form and 'pass_user' in request.form:
        name_surname = request.form['name_surname']
        email_user = request.form['email_user']
        pass_user = request.form['pass_user']
        rol = request.form['rol']

        resultado = recibe_insert_register_user(name_surname, email_user, pass_user, rol)

        if resultado == RESULTADO_EXITO:
            flash('La cuenta fue creada correctamente.', 'success')
            # Redirigir a una página relevante, ¿quizás lista de usuarios si es admin?
            return redirect(url_for('inicio')) # O url_for('lista_usuarios') si existe
        # Los mensajes de error (email existe, error general) se flashean dentro de la función
        # Simplemente redirigimos al formulario de registro en caso de error
        return redirect(url_for('cpanel_register_user'))
    else:
        flash('Método HTTP incorrecto o faltan datos.', 'error')
        return redirect(url_for('cpanel_register_user'))

# Actualizar datos de mi perfil
@app.route("/actualizar-datos-perfil", methods=['POST'])
@login_required # Aplicar decorador
def actualizar_perfil():
    # La comprobación de sesión la hace el decorador
    if request.method == 'POST':
        respuesta = procesar_update_perfil(request.form)
        if respuesta == RESULTADO_EXITO:
            flash('Los datos fueron actualizados correctamente.', 'success')
            return redirect(url_for('perfil')) # Redirigir a perfil para ver cambios
        elif respuesta == RESULTADO_ERROR_PASS_ACTUAL:
            flash('La contraseña actual es incorrecta, por favor verifica.', 'error')
            return redirect(url_for('perfil'))
        elif respuesta == RESULTADO_ERROR_PASS_NO_COINCIDEN:
            flash('Las contraseñas nuevas no coinciden, por favor verifica.', 'error')
            return redirect(url_for('perfil'))
        elif respuesta == RESULTADO_ERROR_PASS_OBLIGATORIA:
            flash('La contraseña actual es obligatoria para realizar cambios.', 'error')
            return redirect(url_for('perfil'))
        elif respuesta == RESULTADO_ERROR_EMAIL_NUEVO_EXISTE:
             # El flash específico ("El nuevo email ya está registrado...") se maneja dentro de procesar_update_perfil
             return redirect(url_for('perfil'))
        else: # Otro error (ej. email inválido, error general)
             # El flash específico se maneja dentro de procesar_update_perfil o validar_datos_basicos
             return redirect(url_for('perfil'))
    # El GET es manejado por la ruta /mi-perfil


# Validar sesión (ruta pública)
@app.route('/login', methods=['GET', 'POST'])
def loginCliente():
    if 'conectado' in session:  # Evita que usuarios logueados vean esto
        return redirect(url_for('inicio'))

    if request.method == 'POST' and 'email_user' in request.form and 'pass_user' in request.form:
        email_user = str(request.form['email_user'])
        pass_user = str(request.form['pass_user'])

        try:
            user = Users.query.filter_by(email_user=email_user, fecha_borrado=None).first()
            if user and check_password_hash(user.pass_user, pass_user):
                # Crear datos de sesión
                session['user_id'] = user.id  # Usa solo 'user_id' como clave principal
                session['conectado'] = True
                session['name_surname'] = user.name_surname
                session['email_user'] = user.email_user
                session['rol'] = user.rol
                session.permanent = True  # Sesión permanente

                flash('Inicio de sesión correcto.', 'success')
                return redirect(url_for('inicio'))
            else:
                flash('Email o contraseña incorrectos.', 'error')
                return redirect(url_for('inicio'))
        except Exception as e:
            app.logger.error(f"Error en loginCliente: {e}")
            flash('Ocurrió un error al iniciar sesión.', 'error')
            return redirect(url_for('inicio'))
    else:
        return redirect(url_for('inicio'))


@app.route('/closed-session', methods=['GET'])
@login_required # Aplicar decorador
def cerraSesion():
    # La comprobación de sesión la hace el decorador
    session.pop('conectado', None)
    session.pop('id', None)
    session.pop('name_surname', None)
    session.pop('email_user', None)
    session.pop('rol', None) # Asegúrate de limpiar todos los datos de sesión
    flash('Tu sesión fue cerrada correctamente.', 'success')
    return redirect(url_for('inicio'))

# --- Ruta Power BI sin cambios ---
@app.route('/powerbi')
# @login_required # Descomentar si esta ruta también debe ser protegida
def powerbi_report():
    report_url = "https://app.powerbi.com/view?r=eyJrIjoiZWVhY2E2ZjEtY2MwOS00MDhhLWEzNjYtODE2OGNjMjJjYzI1IiwidCI6IjRiOTVlNzRhLTQwZGEtNDc0YS05OGZmLWY4ZjlhNWY2Njc3ZiIsImMiOjR9"
    # La lógica de resp_usuariosBD debería obtenerse de alguna fuente real si es necesaria
    resp_usuariosBD = True # Placeholder
    # print(f'resp_usuariosBD: {resp_usuariosBD}') # Eliminar print de depuración si no es necesario
    return render_template('public/reporte/powerbi_report.html', report_url=report_url, resp_usuariosBD=resp_usuariosBD)