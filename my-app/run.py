from app import app, db  # Importa db desde app.py

# Importando todos mis Routers (Rutas)
from routers.router_login import *
from routers.router_home import *
from routers.router_page_not_found import *


# Ejecutando el objeto Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)