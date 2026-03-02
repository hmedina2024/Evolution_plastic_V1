# Resumen de Cambios - Sistema de Empleados

## Fecha: 2026-03-01

## Descripción General
Se han realizado modificaciones en el sistema de gestión de empleados para automatizar la asignación del tipo de empleado basándose en el tipo de empresa seleccionada, y se ha agregado un campo de proceso para cada empleado.

---

## Cambios Realizados

### 1. **Modelo de Datos** (`conexion/models.py`)
- ✅ Agregado campo `id_proceso` a la tabla `Empleados`
- ✅ Agregada relación con la tabla `Procesos`

```python
id_proceso = db.Column(db.Integer, db.ForeignKey('tbl_procesos.id_proceso'), nullable=True)
proceso = db.relationship('Procesos', backref='empleados_proceso')
```

### 2. **Migración de Base de Datos** (`BD/migration_add_id_proceso_empleados.sql`)
- ✅ Creado script SQL para agregar la columna `id_proceso` a la tabla `tbl_empleados`
- ✅ Incluye clave foránea hacia `tbl_procesos`
- ✅ Incluye índice para mejorar el rendimiento

**IMPORTANTE:** Debes ejecutar este script en tu base de datos antes de usar la aplicación:
```sql
-- Ejecutar en tu gestor de base de datos
source BD/migration_add_id_proceso_empleados.sql;
```

### 3. **Formulario de Registro** (`templates/public/empleados/form_empleado.html`)
- ✅ Eliminado el campo visible de "Tipo Empleado"
- ✅ Agregado campo oculto para `tipo_empleado` que se llena automáticamente
- ✅ Agregado campo desplegable para "Proceso"
- ✅ Actualizado JavaScript para:
  - Detectar el tipo de empresa al seleccionar una empresa
  - Asignar automáticamente el tipo de empleado (1=Directo, 2=Temporal)
  - Cargar procesos mediante Select2 con búsqueda dinámica

### 4. **Formulario de Actualización** (`templates/public/empleados/form_empleado_update.html`)
- ✅ Aplicados los mismos cambios que en el formulario de registro
- ✅ Mantiene compatibilidad con empleados existentes

### 5. **Página de Detalles del Empleado** (`templates/public/empleados/detalles_empleado.html`)
- ✅ Rediseñado con formato profesional y moderno
- ✅ Agregado campo de "Proceso" con badge visual
- ✅ Organizado en secciones: Información Personal, Contacto, Laboral y Fotografía
- ✅ Mejorados estilos con gradientes y sombras
- ✅ Badges de colores para Tipo de Empleado y Proceso
- ✅ Iconos Bootstrap para mejor visualización

### 6. **Controladores Backend** (`controllers/funciones_home.py`)

#### Función `procesar_form_empleado`:
- ✅ Agregada lógica para obtener automáticamente el tipo de empleado desde la empresa
- ✅ Agregada validación del campo `id_proceso`
- ✅ Actualizado para guardar el proceso del empleado

#### Función `procesar_actualizacion_form`:
- ✅ Agregada lógica para manejar el tipo de empleado automático
- ✅ Agregada validación y actualización del campo `id_proceso`

#### Función `buscar_empleado_unico`:
- ✅ Agregado JOIN con la tabla `Procesos`
- ✅ Incluye `id_proceso` y `nombre_proceso` en el resultado

### 6. **Endpoints API**
- ✅ El endpoint `/api/empresas` ya devuelve el campo `tipo_empresa`
- ✅ El endpoint `/api/procesos` ya existe y funciona correctamente

---

## Lógica de Asignación Automática

### Tipo de Empleado según Tipo de Empresa:
- **Empresa Temporal** → `id_tipo_empleado = 2`
- **Empresa Directo** → `id_tipo_empleado = 1`

Esta asignación se realiza automáticamente en dos lugares:
1. **Frontend (JavaScript)**: Al seleccionar la empresa, se llena el campo oculto
2. **Backend (Python)**: Como respaldo, si no viene el tipo de empleado, se obtiene de la empresa

---

## Pasos para Completar la Implementación

### 1. Ejecutar la Migración de Base de Datos
```bash
# Conéctate a tu base de datos y ejecuta:
mysql -u tu_usuario -p tu_base_de_datos < BD/migration_add_id_proceso_empleados.sql

# O si usas PostgreSQL:
psql -U tu_usuario -d tu_base_de_datos -f BD/migration_add_id_proceso_empleados.sql
```

### 2. Verificar que los Procesos Existan en la Base de Datos
Asegúrate de tener procesos registrados en la tabla `tbl_procesos`:
```sql
SELECT * FROM tbl_procesos WHERE fecha_borrado IS NULL;
```

### 3. Verificar los Tipos de Empleado
Confirma que existen los registros en `tbl_tipo_empleado`:
```sql
SELECT * FROM tbl_tipo_empleado;
-- Debe tener al menos:
-- id_tipo_empleado = 1 para "Directo"
-- id_tipo_empleado = 2 para "Temporal"
```

### 4. Reiniciar la Aplicación
```bash
# Si usas Flask directamente:
python run.py

# O si usas un servidor de producción, reinicia el servicio
```

---

## Pruebas Recomendadas

### Prueba 1: Registro de Nuevo Empleado
1. Ir a "Registrar Nuevo Empleado"
2. Seleccionar una empresa de tipo "Temporal"
3. Verificar que el tipo de empleado se asigne automáticamente (revisar en consola del navegador)
4. Seleccionar un proceso
5. Completar los demás campos y guardar
6. Verificar en la base de datos que `id_tipo_empleado = 2` y `id_proceso` tenga el valor correcto

### Prueba 2: Registro con Empresa Directa
1. Repetir el proceso anterior pero con una empresa de tipo "Directo"
2. Verificar que `id_tipo_empleado = 1`

### Prueba 3: Actualización de Empleado Existente
1. Editar un empleado existente
2. Cambiar la empresa
3. Verificar que el tipo de empleado se actualice automáticamente
4. Cambiar el proceso
5. Guardar y verificar los cambios

### Prueba 4: Empleados Existentes sin Proceso
Los empleados existentes tendrán `id_proceso = NULL` hasta que sean editados.
Esto es normal y no causará errores ya que el campo es nullable.

---

## Archivos Modificados

1. ✅ `conexion/models.py` - Modelo Empleados
2. ✅ `controllers/funciones_home.py` - Funciones de procesamiento
3. ✅ `templates/public/empleados/form_empleado.html` - Formulario de registro
4. ✅ `templates/public/empleados/form_empleado_update.html` - Formulario de actualización
5. ✅ `BD/migration_add_id_proceso_empleados.sql` - Script de migración (NUEVO)

---

## Notas Importantes

1. **Compatibilidad hacia atrás**: Los empleados existentes seguirán funcionando. El campo `id_proceso` es nullable.

2. **Validación**: El sistema valida que se seleccione un proceso al crear o actualizar empleados.

3. **Tipo de Empleado**: Aunque el campo ya no es visible, sigue siendo obligatorio en la base de datos y se asigna automáticamente.

4. **Búsqueda de Procesos**: El campo de proceso usa Select2 con búsqueda dinámica, permitiendo buscar procesos por nombre.

5. **Logs**: El sistema registra en consola del navegador el tipo de empresa y el tipo de empleado asignado para facilitar el debugging.

---

## Soporte y Mantenimiento

Si necesitas agregar más lógica o validaciones:
- **Frontend**: Modifica el evento `select2:select` en los archivos HTML
- **Backend**: Modifica las funciones `procesar_form_empleado` y `procesar_actualizacion_form`

---

## Autor
Cambios realizados el 2026-03-01
