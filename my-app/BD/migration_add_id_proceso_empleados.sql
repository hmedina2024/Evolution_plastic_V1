-- Migración para agregar el campo id_proceso a la tabla tbl_empleados
-- Fecha: 2026-03-01
-- Descripción: Agrega una columna id_proceso como clave foránea a tbl_procesos

-- Agregar la columna id_proceso a la tabla tbl_empleados
ALTER TABLE tbl_empleados 
ADD COLUMN id_proceso INT NULL;

-- Agregar la clave foránea
ALTER TABLE tbl_empleados 
ADD CONSTRAINT fk_empleados_proceso 
FOREIGN KEY (id_proceso) REFERENCES tbl_procesos(id_proceso);

-- Crear índice para mejorar el rendimiento de las consultas
CREATE INDEX idx_empleados_proceso ON tbl_empleados(id_proceso);

-- Comentario sobre la columna
COMMENT ON COLUMN tbl_empleados.id_proceso IS 'ID del proceso al que pertenece el empleado';
