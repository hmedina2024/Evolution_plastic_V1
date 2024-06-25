#!/usr/bin/env python3.11.0

# Declarando nombre de la aplicación e inicializando, crear la aplicación Flask
from app import app

# Importando todos mis Routers (Rutas)
from routers.router_login import *
from routers.router_home import *
from routers.router_page_not_found import *

# Ejecutando el objeto Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000,debug=True)
