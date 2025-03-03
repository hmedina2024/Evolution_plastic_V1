from app import app, db  # Importa db desde app.py

# Importando todos mis Routers (Rutas)
from routers.router_login import *
from routers.router_home import *
from routers.router_page_not_found import *

# Asegúrate de que los modelos se inicialicen con la app
with app.app_context():
    db.create_all()  # Crea las tablas si no existen (solo para desarrollo, coméntalo en producción)

# Ejecutando el objeto Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)