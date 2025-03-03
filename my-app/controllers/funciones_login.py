# Importando paquetes desde Flask
from flask import session, flash
from app import app  # Importa la instancia de Flask desde app.py
from conexion.models import db, Users  # Importa SQLAlchemy y el modelo Users desde models.py
from werkzeug.security import check_password_hash, generate_password_hash
import re
import datetime


def recibe_insert_register_user(name_surname, email_user, pass_user, rol):
    respuesta_validar = validar_data_register_login(name_surname, email_user, pass_user, rol)

    if respuesta_validar:
        nueva_password = generate_password_hash(pass_user, method='scrypt')
        try:
            # Verificar si el email ya existe usando SQLAlchemy
            existing_user = Users.query.filter_by(email_user=email_user).first()
            if existing_user:
                flash('el registro no fue procesado ya existe la cuenta', 'error')
                return 0  # Indica que el email ya existe

            # Crear nuevo usuario
            new_user = Users(
                name_surname=name_surname,
                email_user=email_user,
                pass_user=nueva_password,
                rol=rol,
                created_user=datetime.datetime.now()
            )
            db.session.add(new_user)
            db.session.commit()
            return 1  # Indica éxito
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error en recibe_insert_register_user: {e}")
            return 0
    else:
        return 0  # Indica fallo en la validación

# Validando la data del Registro para el login
def validar_data_register_login(name_surname, email_user, pass_user, rol):
    try:
        # Verificar si el email ya existe usando SQLAlchemy
        user_bd = Users.query.filter_by(email_user=email_user).first()
        if user_bd:
            flash('el registro no fue procesado ya existe la cuenta', 'error')
            return False
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email_user):
            flash('el Correo es invalido', 'error')
            return False
        elif not name_surname or not email_user or not pass_user or not rol:
            flash('por favor llene los campos del formulario.', 'error')
            return False
        else:
            return True  # La cuenta no existe y los datos son válidos
    except Exception as e:
        app.logger.error(f"Error en validar_data_register_login: {e}")
        return False

def info_perfil_session():
    try:
        user_id = session.get('id')
        if user_id:
            user = Users.query.filter_by(id=user_id).first()
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
    # Extraer datos del diccionario data_form
    user_id = session.get('id')
    name_surname = data_form.get('name_surname')
    email_user = data_form.get('email_user')
    pass_actual = data_form.get('pass_actual')
    new_pass_user = data_form.get('new_pass_user')
    repetir_pass_user = data_form.get('repetir_pass_user')

    if not pass_actual or not email_user:
        return 3  # Clave actual obligatoria

    try:
        user = Users.query.filter_by(id=user_id).first()
        if not user:
            return 0  # Usuario no encontrado

        # Verificar contraseña actual
        if not check_password_hash(user.pass_user, pass_actual):
            return 0  # Contraseña actual incorrecta

        # Verificar que las nuevas contraseñas coincidan
        if new_pass_user and new_pass_user != repetir_pass_user:
            return 2  # Claves no coinciden

        # Actualizar datos del perfil
        user.name_surname = name_surname
        user.email_user = email_user

        # Actualizar contraseña si se proporciona
        if new_pass_user:
            user.pass_user = generate_password_hash(new_pass_user, method='scrypt')

        db.session.commit()
        return 1  # Indica éxito
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en procesar_update_perfil: {e}")
        return 0

def update_perfil_sin_pass(user_id, name_surname):
    try:
        user = Users.query.filter_by(id=user_id).first()
        if user:
            user.name_surname = name_surname
            db.session.commit()
            return 1  # Indica éxito
        return 0
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en update_perfil_sin_pass: {e}")
        return 0

def data_login_sesion():
    try:
        user_id = session.get('id')
        if user_id:
            user = Users.query.filter_by(id=user_id).first()
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