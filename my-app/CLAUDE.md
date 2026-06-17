# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Web application for Evolution Plastics SAS to manage production processes, employees, clients, production orders (OP), and industrial design orders (ODI).

## Running the App

```powershell
# Activate virtual environment
.venv\Scripts\activate   # or venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (127.0.0.2:8000, debug mode)
python run.py

# Production (gunicorn — Linux/Mac only)
gunicorn app:app
```

There is no test suite. Manual testing via the browser is the only verification method.

## Environment Variables

Configure via a `.env` file in `my-app/` or system environment. The `SECRET_KEY` is **required** — the app raises `RuntimeError` at startup if missing. Other vars have defaults for local dev:

| Variable | Default |
|---|---|
| `SECRET_KEY` | *(no default — must be set)* |
| `DB_USER` | `root` |
| `DB_PASSWORD` | `""` |
| `DB_HOST` | `localhost` |
| `DB_NAME` | `evolution_db` |

## Database

MySQL via PyMySQL + SQLAlchemy ORM. Schema lives in [BD/crud_python.sql](BD/crud_python.sql); incremental changes are in `BD/migration_*.sql`. There is no automated migration tool — run new migration files directly against the MySQL database.

All timestamps use `America/Bogota` timezone (`pytz`) in `funciones_home.py`. The `fecha_borrado` pattern is used for soft deletes everywhere (see below).

## Architecture

### Entry point and initialization

- [run.py](run.py) — starts the app; imports all routers via `*` imports
- [app.py](app.py) — creates the Flask app, configures SQLAlchemy, CSRF (`Flask-WTF`), rate limiting (`Flask-Limiter`), and CORS
- [conexion/database.py](conexion/database.py) — holds the `db = SQLAlchemy()` instance; kept separate from `app.py` to break circular imports
- [conexion/models.py](conexion/models.py) — **all** SQLAlchemy models in one file

### Request handling

```
run.py
  └── routers/router_home.py          ← all business routes (employees, orders, etc.)
  └── routers/router_login.py         ← login / logout / user registration
  └── routers/router_page_not_found.py
        └── controllers/funciones_home.py   ← all business logic + DB queries
        └── controllers/funciones_login.py  ← auth logic
```

Routes are registered directly on the `app` object (no Flask Blueprints). Route handlers in `router_home.py` are thin — they delegate everything to `funciones_home.py`.

### Key external libraries

- `python-magic` — real MIME-type detection from file headers (not just extension)
- `reportlab` — PDF generation for OP print view (`generar_pdf_op_func`)
- `openpyxl` — Excel export for employee reports
- `Flask-WTF` + CSRF — all non-GET forms are CSRF-protected; AJAX forms send the token via `formData.append('csrf_token', ...)`
- `Flask-Limiter` — rate limit on login route (10 req/min per IP)
- `Flask-Mail` / `smtplib` — email notifications on OP update (`save_and_notify` action)

### Templates

`templates/public/` — organized by module:
`actividades`, `clientes`, `empleados`, `empresas`, `jornada`, `operaciones`, `ordendisenoindustrial`, `ordenproduccion`, `procesos`, `usuarios`, `perfil`, `reporte`

All templates extend `templates/public/base_cpanel.html`.

### Static files

Uploaded files are stored under `static/`:
- `fotos_empleados/` — employee/client profile photos (UUID-named)
- `documentos_op/` — OP attachments (UUID-named)
- `documentos_odi/` — ODI attachments
- `render_op/` — OP render images (UUID-named)

## Key Patterns

**Soft deletes**: Records are never hard-deleted. `fecha_borrado = NULL` means active; setting it to a datetime marks the record as deleted. Always filter with `fecha_borrado=None` (or `IS NULL`) when querying active records.

**Session-based auth**: Every protected route manually checks `if 'conectado' in session`. A `login_required` decorator exists in [utils/decorators.py](utils/decorators.py) but is **not** consistently used — new routes should follow the existing inline `if 'conectado' in session` pattern.

**DataTables server-side**: List views render an empty table, then POST to a `/buscando-*` endpoint that returns `{draw, recordsTotal, recordsFiltered, data}` JSON for server-side pagination and filtering.

**Select2 paginated dropdowns**: `/api/*` endpoints (e.g., `/api/empleados`, `/api/clientes`) return paginated results (`{results, pagination}`) for Select2 widgets. The `results` key must contain `{id, text}` objects.

**OP/ODI form responses**: `procesar_form_op`, `procesar_form_odi`, `procesar_actualizar_form_op`, and `procesar_actualizar_form_odi` return a `(json_response, status_code)` tuple — forms submit via AJAX, not a standard POST redirect.

**File upload validation**: `procesar_imagen_perfil(storage, subfolder, allowed_extensions, allowed_mimes=None)` handles both extension and real MIME-type checks, then saves the file with a UUID filename. For images pass `_ALLOWED_IMAGE_MIMES`; for documents pass `_ALLOWED_DOC_MIMES`. Both constants are defined at the top of [funciones_home.py](controllers/funciones_home.py). The `MAX_CONTENT_LENGTH` is 10 MB (enforced by Flask).

**OP update document flow**: The frontend ([form_op_update.html](templates/public/ordenproduccion/form_op_update.html)) manages a `selectedFiles` JS array. New files are sent as `documentos_nuevos[]`; IDs of documents to delete are sent as `idsDocumentosAEliminar`. The backend reads both in `procesar_actualizar_form_op`.

**Duplicate constants**: `ALLOWED_RENDER_EXTENSIONS` and `ALLOWED_DOC_EXTENSIONS` are defined **twice** in `funciones_home.py` (around lines 44–46 and again around lines 1924–1925). The second definition (line ~1925) is used by the OP creation functions and includes `zip`, `rar` in addition to the first definition. Be careful which set is in scope.

**OP audit log**: Every OP update writes a row to `tbl_op_logs` (model `OPLog`) with a JSON diff of changed fields (`cambios`) and the acting user.

**ODI → OP link**: An ODI (`OrdenDisenoIndustrial`) can be linked to an OP via `OrdenProduccion.id_odi_fk`. When an ODI is selected in the OP form, the fields `referencia`, `producto`, `id_cliente`, `id_empleado`, and `id_disenador_industrial` are auto-populated from the ODI and locked for editing.

## Business Modules

- **Empleados** — employees linked to an Empresa (company), optionally a Proceso and a Cargo
- **Empresas** — companies of type `Directo` or `Temporal`
- **Clientes** — clients with document type
- **Procesos / Actividades** — manufacturing processes and their sub-activities (Actividad belongs to one Proceso)
- **Operaciones** — daily work log entries per employee, linked to Proceso, Actividad, and optionally an OP
- **Jornadas** — attendance/shift tracking per employee
- **Orden de Producción (OP)** — production orders; can have Piezas (parts with their own processes/activities/specs), Documentos, Renders, URL links, and an audit log (`tbl_op_logs`). Multiple employees can be assigned: vendedor, supervisor, diseñador gráfico, diseñador industrial, costeador.
- **Orden de Diseño Industrial (ODI)** — industrial design orders that can be linked to an OP; have their own documents
- **Listas de Correos** — email distribution lists (`tbl_listas_correos` + `tbl_listas_miembros`) used when notifying via OP update
