from flask import session, flash
from app import app
from conexion.models import db, Users
from werkzeug.security import check_password_hash, generate_password_hash
import re
import datetime

# --- Constantes para códigos de retorno ---
RESULTADO_EXITO = 1
RESULTADO_ERROR_GENERAL = 0
RESULTADO_ERROR_EMAIL_EXISTE = -1
RESULTADO_ERROR_PASS_ACTUAL = -2
RESULTADO_ERROR_PASS_NO_COINCIDEN = -3
RESULTADO_ERROR_PASS_OBLIGATORIA = -4
RESULTADO_ERROR_EMAIL_NUEVO_EXISTE = -5
# --- Fin Constantes ---


def recibe_insert_register_user(name_surname, email_user, pass_user, rol):
    if not validar_datos_basicos_registro(name_surname, email_user, pass_user, rol):
        # El flash de error se maneja dentro de validar_datos_basicos_registro
        return RESULTADO_ERROR_GENERAL

    nueva_password = generate_password_hash(pass_user, method='scrypt')

    try:
        # Verificar si el email ya existe (UNA SOLA VEZ)
        existing_user = Users.query.filter_by(email_user=email_user).first()
        if existing_user:
            flash('El email proporcionado ya está registrado.', 'error')
            return RESULTADO_ERROR_EMAIL_EXISTE

        # Crear nuevo usuario
        new_user = Users(
            name_surname=name_surname,
            email_user=email_user,
            pass_user=nueva_password,
            rol=rol
            # created_user se maneja por default=func.now() en el modelo
        )
        db.session.add(new_user)
        db.session.commit()
        return RESULTADO_EXITO
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en recibe_insert_register_user: {e}")
        flash('Ocurrió un error al crear la cuenta.', 'error')
        return RESULTADO_ERROR_GENERAL

# Nueva función para validar solo datos básicos (sin consultar BD)
def validar_datos_basicos_registro(name_surname, email_user, pass_user, rol):
    if not name_surname or not email_user or not pass_user or not rol:
        flash('Por favor llene todos los campos del formulario.', 'error')
        return False
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email_user):
        flash('El formato del correo electrónico es inválido.', 'error')
        return False
    # Añadir aquí otras validaciones (ej. longitud contraseña)
    # elif len(pass_user) < 8:
    #     flash('La contraseña debe tener al menos 8 caracteres.', 'error')
    #     return False
    else:
        return True

def info_perfil_session():
    try:
        user_id = session.get('id')
        if user_id:
            user = Users.query.get(user_id) # .get() es más eficiente por PK
            if user:
                return {
                    'name_surname': user.name_surname,
                    'email_user': user.email_user
                }
        return None
    except Exception as e:
        app.logger.error(f"Error en info_perfil_session: {e}")
        return None

def procesar_update_perfil(data_form):
    user_id = session.get('id')
    name_surname = data_form.get('name_surname')
    email_user = data_form.get('email_user')
    pass_actual = data_form.get('pass_actual')
    new_pass_user = data_form.get('new_pass_user')
    repetir_pass_user = data_form.get('repetir_pass_user')

    # Validar campos básicos obligatorios
    if not name_surname or not email_user:
         flash('El nombre y el email son obligatorios.', 'error')
         return RESULTADO_ERROR_GENERAL
    if not pass_actual:
        flash('La contraseña actual es obligatoria para realizar cambios.', 'error')
        return RESULTADO_ERROR_PASS_OBLIGATORIA

    try:
        user = Users.query.get(user_id) # Usar .get() por PK
        if not user:
            flash('Usuario no encontrado.', 'error')
            return RESULTADO_ERROR_GENERAL

        # Verificar contraseña actual
        if not check_password_hash(user.pass_user, pass_actual):
            # El flash se maneja en el router basado en el código de retorno
            return RESULTADO_ERROR_PASS_ACTUAL

        email_cambiado = user.email_user != email_user
        nuevo_email_valido = True
        if email_cambiado:
            # Validar formato del nuevo email
            if not re.match(r'[^@]+@[^@]+\.[^@]+', email_user):
                flash('El formato del nuevo correo electrónico es inválido.', 'error')
                return RESULTADO_ERROR_GENERAL # O un código específico si prefieres

            # Verificar si el nuevo email ya existe
            existing_email = Users.query.filter(Users.email_user == email_user, Users.id != user_id).first()
            if existing_email:
                flash('El nuevo email ya está registrado por otro usuario.', 'error')
                nuevo_email_valido = False
                # Devolvemos error, pero el usuario puede intentarlo de nuevo sin cambiar el email
                return RESULTADO_ERROR_EMAIL_NUEVO_EXISTE

        # Actualizar contraseña si se proporciona y es válida
        if new_pass_user:
            # Añadir validación de longitud si se desea
            # if len(new_pass_user) < 8:
            #     flash('La nueva contraseña debe tener al menos 8 caracteres.', 'error')
            #     return RESULTADO_ERROR_GENERAL
            if new_pass_user != repetir_pass_user:
                # El flash se maneja en el router basado en el código de retorno
                return RESULTADO_ERROR_PASS_NO_COINCIDEN
            user.pass_user = generate_password_hash(new_pass_user, method='scrypt')
            flash('Contraseña actualizada correctamente.', 'info') # Mensaje adicional

        # Actualizar nombre y email (si es válido)
        user.name_surname = name_surname
        if email_cambiado and nuevo_email_valido:
            user.email_user = email_user

        db.session.commit()

        # Actualizar sesión si el nombre o email cambiaron
        session['name_surname'] = user.name_surname
        if email_cambiado and nuevo_email_valido:
            session['email_user'] = user.email_user

        return RESULTADO_EXITO
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en procesar_update_perfil: {e}")
        flash('Ocurrió un error al actualizar el perfil.', 'error')
        return RESULTADO_ERROR_GENERAL

def data_login_sesion():
    try:
        user_id = session.get('id')
        if user_id:
            user = Users.query.get(user_id) # Usar .get() por PK
            if user:
                return {
                    'id': user.id,
                    'name_surname': user.name_surname,
                    'email_user': user.email_user,
                    'rol': user.rol
                }
        return None
    except Exception as e:
        app.logger.error(f"Error en data_login_sesion: {e}")
        return None

# --- Función update_perfil_sin_pass eliminada ---
