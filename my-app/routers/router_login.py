from app import app
from flask import render_template, request, flash, redirect, url_for, session, jsonify
from conexion.models import db, Users  # Importa SQLAlchemy y el modelo Users desde models.py
from werkzeug.security import check_password_hash
from controllers.funciones_login import (  # Importa las funciones actualizadas desde funciones_login.py
    recibe_insert_register_user, procesar_update_perfil, info_perfil_session, data_login_sesion
)
PATH_URL_LOGIN = "public/login"

@app.route('/', methods=['GET'])
def inicio():
    if 'conectado' in session:
        return render_template('public/base_cpanel.html', data_login=data_login_sesion())
    else:
        return render_template(f'{PATH_URL_LOGIN}/base_login.html')

@app.route('/mi-perfil', methods=['GET'])
def perfil():
    if 'conectado' in session:
        return render_template(f'public/perfil/perfil.html', info_perfil_session=info_perfil_session())
    else:
        return redirect(url_for('inicio'))

# Crear cuenta de usuario
@app.route('/register-user', methods=['GET'])
def cpanel_register_user():
    return render_template(f'{PATH_URL_LOGIN}/auth_register.html')

# Recuperar cuenta de usuario
@app.route('/recovery-password', methods=['GET'])
def cpanelRecoveryPassUser():
    if 'conectado' in session:
        return redirect(url_for('inicio'))
    else:
        return render_template(f'{PATH_URL_LOGIN}/auth_forgot_password.html')

# Crear cuenta de usuario
@app.route('/saved-register', methods=['GET', 'POST'])
def cpanel_register_user_bd():
    if request.method == 'POST' and 'name_surname' in request.form and 'pass_user' in request.form:
        name_surname = request.form['name_surname']
        email_user = request.form['email_user']
        pass_user = request.form['pass_user']
        rol = request.form['rol']

        result_data = recibe_insert_register_user(name_surname, email_user, pass_user, rol)
        if result_data != 0:
            flash('la cuenta fue creada correctamente.', 'success')
            return redirect(url_for('usuarios'))
        else:
            flash('No se pudo crear la cuenta, verifica los datos.', 'error')
            return redirect(url_for('cpanel_register_user'))
    else:
        flash('el método HTTP es incorrecto', 'error')
        return redirect(url_for('cpanel_register_user'))

# Actualizar datos de mi perfil
@app.route("/actualizar-datos-perfil", methods=['POST'])
def actualizar_perfil():
    if request.method == 'POST':
        if 'conectado' in session:
            respuesta = procesar_update_perfil(request.form)
            if respuesta == 1:
                flash('Los datos fueron actualizados correctamente.', 'success')
                return redirect(url_for('inicio'))
            elif respuesta == 0:
                flash('La contraseña actual está incorrecta, por favor verifica.', 'error')
                return redirect(url_for('perfil'))
            elif respuesta == 2:
                flash('Ambas claves deben ser iguales, por favor verifica.', 'error')
                return redirect(url_for('perfil'))
            elif respuesta == 3:
                flash('La Clave actual es obligatoria.', 'error')
                return redirect(url_for('perfil'))
        else:
            flash('primero debes iniciar sesión.', 'error')
            return redirect(url_for('inicio'))
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

# Validar sesión
@app.route('/login', methods=['GET', 'POST'])
def loginCliente():
    if 'conectado' in session:
        return redirect(url_for('inicio'))
    else:
        if request.method == 'POST' and 'email_user' in request.form and 'pass_user' in request.form:
            email_user = str(request.form['email_user'])
            pass_user = str(request.form['pass_user'])

            # Usar SQLAlchemy para consultar la base de datos
            try:
                user = Users.query.filter_by(email_user=email_user).first()
                if user and check_password_hash(user.pass_user, pass_user):  # Asegúrate de que pass_user sea el nombre correcto en el modelo
                    # Crear datos de sesión
                    session['conectado'] = True
                    session['id'] = user.id
                    session['name_surname'] = user.name_surname
                    session['email_user'] = user.email_user
                    session['rol'] = user.rol

                    flash('la sesión fue correcta.', 'success')
                    return redirect(url_for('inicio'))
                else:
                    flash('datos incorrectos, por favor revise.', 'error')
                    return render_template(f'{PATH_URL_LOGIN}/base_login.html')
            except Exception as e:
                app.logger.error(f"Error en login_cliente: {e}")
                flash('Ocurrió un error al iniciar sesión, intenta de nuevo.', 'error')
                return render_template(f'{PATH_URL_LOGIN}/base_login.html')
        else:
            flash('primero debes iniciar sesión.', 'error')
            return render_template(f'{PATH_URL_LOGIN}/base_login.html')

@app.route('/closed-session', methods=['GET'])
def cerraSesion():
    if request.method == 'GET':
        if 'conectado' in session:
            # Eliminar datos de sesión
            session.pop('conectado', None)
            session.pop('id', None)
            session.pop('name_surname', None)
            session.pop('email_user', None)
            flash('tu sesión fue cerrada correctamente.', 'success')
            return redirect(url_for('inicio'))
        else:
            flash('recuerde debe iniciar sesión.', 'error')
            return render_template(f'{PATH_URL_LOGIN}/base_login.html')

@app.route('/powerbi')
def powerbi_report():
    report_url = "https://app.powerbi.com/view?r=eyJrIjoiZWVhY2E2ZjEtY2MwOS00MDhhLWEzNjYtODE2OGNjMjJjYzI1IiwidCI6IjRiOTVlNzRhLTQwZGEtNDc0YS05OGZmLWY4ZjlhNWY2Njc3ZiIsImMiOjR9"
    resp_usuariosBD = True  # Asegúrate de que este valor refleja la existencia de datos
    print(f'resp_usuariosBD: {resp_usuariosBD}')  # Añade esto para depuración
    return render_template('public/reporte/powerbi_report.html', report_url=report_url, resp_usuariosBD=resp_usuariosBD)