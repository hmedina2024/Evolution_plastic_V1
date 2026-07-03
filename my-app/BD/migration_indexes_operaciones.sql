-- Índices para mejorar rendimiento del Dashboard de Operaciones
-- Las queries del dashboard filtran constantemente por fecha_hora_inicio;
-- sin este índice cada consulta hace un full table scan sobre tbl_operaciones.

ALTER TABLE tbl_operaciones
  ADD INDEX idx_op_fecha_inicio (fecha_hora_inicio),
  ADD INDEX idx_op_novedad (novedad(50));
