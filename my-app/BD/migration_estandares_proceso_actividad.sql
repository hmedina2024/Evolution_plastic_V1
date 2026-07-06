-- Tabla de estándares de tiempo por proceso/actividad
-- Almacena el histórico de rendimientos para cálculos automáticos de personal

CREATE TABLE IF NOT EXISTS tbl_estandares_proceso_actividad (
  id_estandar INT AUTO_INCREMENT PRIMARY KEY,
  id_proceso INT NOT NULL,
  id_actividad INT NOT NULL,

  -- Métricas de tiempo (en minutos)
  tiempo_promedio_minuto DECIMAL(10, 4) NOT NULL DEFAULT 0,
  desviacion_estandar DECIMAL(10, 4) NOT NULL DEFAULT 0,
  tiempo_minimo DECIMAL(10, 4),
  tiempo_maximo DECIMAL(10, 4),

  -- Clasificación de dificultad
  dificultad ENUM('BAJA', 'MEDIA', 'ALTA') NOT NULL DEFAULT 'MEDIA',
  variabilidad_porcentaje DECIMAL(5, 2) NOT NULL DEFAULT 0,

  -- Fiabilidad de los datos
  cantidad_muestras INT NOT NULL DEFAULT 0,
  porcentaje_novedades DECIMAL(5, 2) NOT NULL DEFAULT 0,

  -- Auditoría
  fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- Restricciones
  FOREIGN KEY (id_proceso) REFERENCES tbl_procesos(id_proceso) ON DELETE CASCADE,
  FOREIGN KEY (id_actividad) REFERENCES tbl_actividades(id_actividad) ON DELETE CASCADE,
  UNIQUE KEY uq_proceso_actividad (id_proceso, id_actividad),
  INDEX idx_dificultad (dificultad),
  INDEX idx_muestras (cantidad_muestras)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de histórico de proyecciones (para mejorar precisión en el tiempo)
CREATE TABLE IF NOT EXISTS tbl_proyecciones_personal (
  id_proyeccion INT AUTO_INCREMENT PRIMARY KEY,

  -- Referencia a las OPs
  ids_op_seleccionadas JSON NOT NULL, -- ["OP-001", "OP-002"]

  -- Cálculo
  personas_necesarias_recomendado DECIMAL(5, 2) NOT NULL,
  personas_asignadas INT,
  tiempo_total_minutos INT NOT NULL,

  -- Resultados reales (después de ejecutarse la semana)
  personas_usadas_reales INT,
  tiempo_real_minutos INT,
  eficiencia_real DECIMAL(5, 2),

  -- Auditoría
  semana_inicio DATE NOT NULL,
  semana_fin DATE NOT NULL,
  id_usuario INT,
  fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (id_usuario) REFERENCES tbl_users(id),
  INDEX idx_semana (semana_inicio, semana_fin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
