-- ============================================================
-- MIGRACIÓN: Historial de Versiones de OP
-- Fecha: 2026-06-04
-- Descripción: Agrega la columna snapshot_anterior a tbl_op_logs
--              para almacenar el estado completo de la OP antes
--              de cada actualización (sistema de versiones).
-- ============================================================

-- Agregar columna snapshot_anterior a tbl_op_logs
-- MEDIUMTEXT soporta hasta 16 MB, más que suficiente para el JSON completo de una OP
ALTER TABLE `tbl_op_logs`
  ADD COLUMN IF NOT EXISTS `snapshot_anterior` MEDIUMTEXT NULL
    COMMENT 'JSON con el estado completo de la OP ANTES de la actualización. Permite ver cómo estaba la OP en versiones anteriores.'
    AFTER `cambios`;

-- ---- POR SI NO FUNCIONA IF NOT EXISTS EN EL SERVIDOR ----
-- Usar esta versión si el servidor MySQL no soporta IF NOT EXISTS en ALTER TABLE:
-- ALTER TABLE `tbl_op_logs`
--   ADD COLUMN `snapshot_anterior` MEDIUMTEXT NULL
--     COMMENT 'JSON con el estado completo de la OP ANTES de la actualización.'
--     AFTER `cambios`;
