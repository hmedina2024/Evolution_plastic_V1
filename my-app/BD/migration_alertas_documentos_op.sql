-- ============================================================
-- Alertas de documentos faltantes por proceso en las OP
-- ------------------------------------------------------------
-- Cuando una OP tiene un proceso asociado y no se le han cargado
-- documentos para ese proceso tras cierto tiempo, se notifica por
-- correo a una Lista de Correos. La alerta se repite cada
-- 'dias_reenvio' mientras el documento siga faltando.
-- ============================================================

-- 1) Configuración de la alerta por proceso (editable desde la pantalla admin)
CREATE TABLE IF NOT EXISTS tbl_alertas_proceso (
  id_alerta_proceso INT AUTO_INCREMENT PRIMARY KEY,
  id_proceso    INT NOT NULL,
  dias_limite   INT NOT NULL DEFAULT 2,   -- días tras crear la OP para la 1ª alerta
  dias_reenvio  INT NOT NULL DEFAULT 1,   -- cada cuántos días recordar mientras falte
  id_lista      INT NULL,                 -- lista de correos destinataria
  activo        TINYINT(1) NOT NULL DEFAULT 1,
  fecha_registro      DATETIME DEFAULT CURRENT_TIMESTAMP,
  fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_alerta_proceso (id_proceso),
  FOREIGN KEY (id_proceso) REFERENCES tbl_procesos(id_proceso) ON DELETE CASCADE,
  FOREIGN KEY (id_lista)   REFERENCES tbl_listas_correos(id_lista) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2) Historial de alertas enviadas (control de reenvío / anti-spam)
CREATE TABLE IF NOT EXISTS tbl_alertas_documentos_log (
  id_alerta_log INT AUTO_INCREMENT PRIMARY KEY,
  id_op         INT NOT NULL,
  id_proceso    INT NOT NULL,
  fecha_envio   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  destinatarios TEXT NULL,   -- a quiénes se envió (auditoría)
  FOREIGN KEY (id_op)      REFERENCES tbl_ordenproduccion(id_op) ON DELETE CASCADE,
  FOREIGN KEY (id_proceso) REFERENCES tbl_procesos(id_proceso) ON DELETE CASCADE,
  INDEX idx_alerta_log_op_proc (id_op, id_proceso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
