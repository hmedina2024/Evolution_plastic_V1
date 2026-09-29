-- ============================================================
-- Actividad Comercial: bitácora unificada de Visitas y Llamadas
-- ------------------------------------------------------------
-- Un vendedor registra una actividad (visita presencial, llamada,
-- videollamada, email o reunión) contra un Cliente YA existente O un
-- Prospecto (empresa/persona que aún no es cliente formal). Nunca ambos.
--
-- Prospectos existe porque tbl_clientes exige documento/NIT obligatorio,
-- dato que normalmente no se tiene en el primer contacto comercial.
-- Cuando el negocio se concreta, el prospecto se "convierte" a Cliente
-- y conserva todo su historial de actividad.
-- ============================================================

-- 1) Prospectos: clientes potenciales, antes de tener documento/NIT
CREATE TABLE IF NOT EXISTS tbl_prospectos (
  id_prospecto        INT AUTO_INCREMENT PRIMARY KEY,
  nombre_prospecto    VARCHAR(150) NOT NULL,
  empresa_prospecto   VARCHAR(150) NULL,
  telefono_prospecto  VARCHAR(50)  NULL,
  email_prospecto     VARCHAR(100) NULL,
  fecha_registro      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  id_usuario_registro INT NULL,
  convertido          TINYINT(1) NOT NULL DEFAULT 0,
  fecha_conversion    DATETIME NULL,
  id_cliente_resultante INT NULL,
  fecha_borrado       DATETIME NULL,
  FOREIGN KEY (id_usuario_registro) REFERENCES users(id),
  FOREIGN KEY (id_cliente_resultante) REFERENCES tbl_clientes(id_cliente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2) Actividad Comercial: la bitácora unificada (visitas + llamadas + ...)
CREATE TABLE IF NOT EXISTS tbl_actividad_comercial (
  id_actividad_comercial INT AUTO_INCREMENT PRIMARY KEY,
  id_empleado         INT NOT NULL,          -- vendedor que ejecuta la actividad
  id_cliente          INT NULL,              -- exactamente uno de estos dos
  id_prospecto        INT NULL,
  tipo_actividad       VARCHAR(30) NOT NULL, -- Visita presencial | Llamada | Videollamada | Email | Reunión
  fecha_hora_inicio   DATETIME NOT NULL,
  fecha_hora_fin      DATETIME NULL,         -- opcional: permite medir duración
  alcance             TEXT NOT NULL,         -- objetivo/alcance de la actividad
  resultado           TEXT NULL,             -- qué pasó / observaciones
  proximo_paso        TEXT NULL,             -- siembra del futuro seguimiento (Fase 3)
  fecha_registro      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  id_usuario_registro INT NULL,
  fecha_borrado       DATETIME NULL,
  FOREIGN KEY (id_empleado)  REFERENCES tbl_empleados(id_empleado),
  FOREIGN KEY (id_cliente)   REFERENCES tbl_clientes(id_cliente),
  FOREIGN KEY (id_prospecto) REFERENCES tbl_prospectos(id_prospecto),
  FOREIGN KEY (id_usuario_registro) REFERENCES users(id),
  INDEX idx_actcom_empleado_fecha (id_empleado, fecha_hora_inicio),
  INDEX idx_actcom_cliente (id_cliente),
  INDEX idx_actcom_prospecto (id_prospecto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3) Metas de actividad por vendedor (cuotas + config de alerta de inactividad)
CREATE TABLE IF NOT EXISTS tbl_metas_actividad_vendedor (
  id_meta                  INT AUTO_INCREMENT PRIMARY KEY,
  id_empleado              INT NOT NULL,
  actividades_semana_min   INT NOT NULL DEFAULT 10,
  dias_sin_actividad_alerta INT NOT NULL DEFAULT 5,
  id_lista                 INT NULL,   -- a quién notificar si incumple (opcional)
  activo                   TINYINT(1) NOT NULL DEFAULT 1,
  fecha_registro           DATETIME DEFAULT CURRENT_TIMESTAMP,
  fecha_actualizacion      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_meta_empleado (id_empleado),
  FOREIGN KEY (id_empleado) REFERENCES tbl_empleados(id_empleado) ON DELETE CASCADE,
  FOREIGN KEY (id_lista) REFERENCES tbl_listas_correos(id_lista) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4) Historial de alertas comerciales enviadas (anti-spam / control de reenvío)
CREATE TABLE IF NOT EXISTS tbl_alertas_comercial_log (
  id_log        INT AUTO_INCREMENT PRIMARY KEY,
  id_empleado   INT NOT NULL,
  tipo_alerta   VARCHAR(30) NOT NULL,  -- 'inactividad' | 'cuota_semanal'
  fecha_envio   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  destinatarios TEXT NULL,
  FOREIGN KEY (id_empleado) REFERENCES tbl_empleados(id_empleado) ON DELETE CASCADE,
  INDEX idx_alertacom_empleado_tipo (id_empleado, tipo_alerta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
