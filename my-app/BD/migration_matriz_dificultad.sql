-- ============================================================
-- Matriz de dificultad por proceso
-- Almacena el tiempo (días/horas) que toma cada proceso según
-- su grado de dificultad (1 = más fácil, 10 = más difícil).
-- La administra el usuario desde la pantalla de administración.
-- ============================================================

CREATE TABLE IF NOT EXISTS tbl_matriz_dificultad (
  id_matriz_dificultad INT AUTO_INCREMENT PRIMARY KEY,
  dificultad    TINYINT NOT NULL,           -- 1 a 10
  id_proceso    INT NOT NULL,
  tiempo_dias   DECIMAL(6,2) DEFAULT 0,
  tiempo_horas  DECIMAL(8,2) DEFAULT 0,
  fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (id_proceso) REFERENCES tbl_procesos(id_proceso) ON DELETE CASCADE,
  UNIQUE KEY uq_proceso_dificultad (id_proceso, dificultad),
  INDEX idx_matriz_proceso (id_proceso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Datos DEMO: genera las 10 filas de dificultad para cada
-- proceso activo. Valores de ejemplo (días crecen con la
-- dificultad; horas = días * 8). El admin los editará luego.
-- ------------------------------------------------------------
INSERT INTO tbl_matriz_dificultad (dificultad, id_proceso, tiempo_dias, tiempo_horas)
SELECT d.n,
       p.id_proceso,
       ROUND(d.n * 0.5, 2)      AS tiempo_dias,
       ROUND(d.n * 0.5 * 8, 2)  AS tiempo_horas
FROM tbl_procesos p
CROSS JOIN (
  SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
  UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
) d
WHERE p.fecha_borrado IS NULL
ON DUPLICATE KEY UPDATE tiempo_dias = VALUES(tiempo_dias);

-- ------------------------------------------------------------
-- Dificultad elegida por OP y proceso (opcional, NULL = sin definir)
-- ------------------------------------------------------------
ALTER TABLE tbl_orden_produccion_procesos
  ADD COLUMN dificultad TINYINT NULL AFTER id_proceso;
