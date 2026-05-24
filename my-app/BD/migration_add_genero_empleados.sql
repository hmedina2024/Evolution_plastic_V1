-- Migración para agregar campo género a la tabla tbl_empleados
-- Fecha: 2026-04-26
-- Descripción: Agrega el campo género como ENUM con opciones Masculino, Femenino, Otro

-- Agregar la columna género a la tabla tbl_empleados
ALTER TABLE tbl_empleados 
ADD COLUMN genero ENUM('Masculino', 'Femenino', 'Otro') NULL 
AFTER email_empleado;

-- Comentario para documentar el campo
ALTER TABLE tbl_empleados 
MODIFY COLUMN genero ENUM('Masculino', 'Femenino', 'Otro') NULL 
COMMENT 'Género del empleado: Masculino, Femenino u Otro';