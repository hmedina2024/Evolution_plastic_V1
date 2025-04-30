# my-app/utils/decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """
    Decorador para requerir inicio de sesión en una ruta.
    Redirige a la página de inicio si el usuario no está conectado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'conectado' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            # Asegúrate que 'inicio' es la ruta correcta para tu página de login/inicio
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)
    return decorated_function