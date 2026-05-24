# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Web application for Evolution Plastics SAS to manage production processes, employees, clients, production orders (OP), and industrial design orders (ODI).

## Running the App

```powershell
# Activate virtual environment
.venv\Scripts\activate   # or venv\Scripts\activate

# Run development server (127.0.0.2:8000, debug mode)
python run.py

# Production (gunicorn — Linux/Mac only)
gunicorn app:app
```

## Environment Variables

Configure via a `.env` file in `my-app/` or system environment. Defaults are hardcoded in [app.py](app.py) for local development:

| Variable | Default |
|---|---|
| `SECRET_KEY` | `secretEvolutioControllocalhost` |
| `DB_USER` | `root` |
| `DB_PASSWORD` | `Yamasaqui2024*` |
| `DB_HOST` | `localhost` |
| `DB_NAME` | `evolution_db` |

## Database

MySQL via PyMySQL + SQLAlchemy ORM. Schema lives in [BD/crud_python.sql](BD/crud_python.sql); incremental changes are applied manually using the `BD/migration_*.sql` files. There is no automated migration tool — run new migration files directly against the MySQL database.

## Architecture

### Entry point and initialization

- [run.py](run.py) — starts the app; imports all routers via `*` imports
- [app.py](app.py) — creates the Flask app, configures SQLAlchemy, loads env vars
- [conexion/database.py](conexion/database.py) — holds the `db = SQLAlchemy()` instance; kept separate from `app.py` to break circular imports
- [conexion/models.py](conexion/models.py) — all SQLAlchemy models in one file

### Request handling

```
run.py
  └── routers/router_home.py       ← all business routes (employees, orders, etc.)
  └── routers/router_login.py      ← login / logout / user registration
  └── routers/router_page_not_found.py
        └── controllers/funciones_home.py   ← all business logic
        └── controllers/funciones_login.py  ← auth logic
```

Routes are registered directly on the `app` object (no Flask Blueprints). All route handlers live in `router_home.py` and delegate to `funciones_home.py` for database queries and processing.

### Templates

`templates/public/` — organized by module:
`actividades`, `clientes`, `empleados`, `empresas`, `jornada`, `operaciones`, `ordendisenoindustrial`, `ordenproduccion`, `procesos`, `usuarios`, `perfil`, `reporte`

All templates extend `templates/public/base_cpanel.html`.

### Static files

Uploaded files are stored under `static/`:
- `fotos_empleados/` — employee/client profile photos (stored with SHA-256 hash filenames)
- `documentos_op/` — OP attachments
- `documentos_odi/` — ODI attachments
- `render_op/` — OP render images

## Key Patterns

**Soft deletes**: Records are never hard-deleted. `fecha_borrado = NULL` means active; setting it to a datetime marks the record as deleted. Always filter with `fecha_borrado=None` (or `IS NULL`) when querying active records.

**Session-based auth**: Every protected route manually checks `if 'conectado' in session`. A `login_required` decorator exists in [utils/decorators.py](utils/decorators.py) but is not consistently used — new routes should use the existing inline pattern for consistency.

**DataTables server-side**: List views render an empty table, then POST to a `/buscando-*` endpoint that returns `{draw, recordsTotal, recordsFiltered, data}` JSON for server-side pagination and filtering.

**Select2 paginated dropdowns**: `/api/*` endpoints (e.g., `/api/empleados`, `/api/clientes`) return paginated results for Select2 widgets used in forms.

**OP/ODI form responses**: `procesar_form_op` and `procesar_form_odi` return a `(json_response, status_code)` tuple instead of a redirect, because the forms submit via AJAX.

## Business Modules

- **Empleados** — employees linked to an Empresa (company) and optionally a Proceso
- **Empresas** — companies of type `Directo` or `Temporal`
- **Clientes** — clients with document type
- **Procesos / Actividades** — manufacturing processes and their sub-activities
- **Operaciones** — daily work log entries per employee
- **Jornadas** — attendance/shift tracking
- **Orden de Producción (OP)** — production orders; can have Piezas (parts), Documentos, Renders, URL links, and an audit log (`tbl_op_logs`)
- **Orden de Diseño Industrial (ODI)** — industrial design orders that can be linked to an OP
