-- ============================================================
-- Índices de rendimiento para los dashboards
-- ------------------------------------------------------------
-- MySQL no soporta "CREATE INDEX IF NOT EXISTS", así que se usa
-- un procedimiento que verifica information_schema antes de crear.
-- Es seguro re-ejecutar este archivo: no duplica índices.
-- ============================================================

DROP PROCEDURE IF EXISTS crear_indice_si_no_existe;

DELIMITER //
CREATE PROCEDURE crear_indice_si_no_existe(
    IN p_tabla   VARCHAR(64),
    IN p_indice  VARCHAR(64),
    IN p_columnas VARCHAR(255)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE table_schema = DATABASE()
          AND table_name   = p_tabla
          AND index_name   = p_indice
    ) THEN
        SET @sql = CONCAT('CREATE INDEX ', p_indice, ' ON ', p_tabla, ' (', p_columnas, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

-- Avance de producción: SUM(cantidad) WHERE id_actividad = X GROUP BY id_op
CALL crear_indice_si_no_existe('tbl_operaciones', 'idx_oper_actividad_op', 'id_actividad, id_op');

-- Consultas de operaciones por rango de fecha (dashboards y estándares)
CALL crear_indice_si_no_existe('tbl_operaciones', 'idx_oper_fecha_inicio', 'fecha_hora_inicio');

-- Productividad por empleado en un periodo
CALL crear_indice_si_no_existe('tbl_operaciones', 'idx_oper_empleado_fecha', 'id_empleado, fecha_hora_inicio');

-- Documentos pendientes: (id_op, id_proceso) activos
CALL crear_indice_si_no_existe('tbl_documentos_op', 'idx_docop_op_proceso', 'id_op, id_proceso');

-- Listados de OP activas y filtros por estado
CALL crear_indice_si_no_existe('tbl_ordenproduccion', 'idx_op_borrado_estado', 'fecha_borrado, estado');

-- OPs por fecha de creación (filtro de periodo del dashboard)
CALL crear_indice_si_no_existe('tbl_ordenproduccion', 'idx_op_fecha', 'fecha');

DROP PROCEDURE IF EXISTS crear_indice_si_no_existe;
