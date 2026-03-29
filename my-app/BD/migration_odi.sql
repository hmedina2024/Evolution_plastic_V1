-- ============================================================
-- MIGRACIÓN: Módulo Órdenes de Diseño Industrial (ODI)
-- Fecha: 2026-03-24
-- Descripción: Crea las tablas necesarias para el módulo ODI
--              y agrega la relación con las Órdenes de Producción
-- ============================================================

-- ------------------------------------------------------------
-- TABLA PRINCIPAL: tbl_ordendisenoindustrial
-- Almacena las Órdenes de Diseño Industrial (ODI)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tbl_ordendisenoindustrial` (
  `id_odi`                  INT           NOT NULL AUTO_INCREMENT,
  `codigo_odi`              VARCHAR(50)   NOT NULL UNIQUE COMMENT 'Código único de la ODI, ej: ODI-2024-001',
  `proyecto`                VARCHAR(200)  NULL     COMMENT 'Equivalente a Referencia en OP. Se lleva automáticamente a la OP.',
  `pieza`                   VARCHAR(200)  NULL     COMMENT 'Equivalente a Producto en OP. Se lleva automáticamente a la OP.',
  `id_cliente`              INT           NULL     COMMENT 'FK a tbl_clientes. Se lleva automáticamente a la OP.',
  `id_empleado`             INT           NULL     COMMENT 'Comercial/Vendedor. FK a tbl_empleados. Se lleva a la OP.',
  `id_disenador_industrial` INT           NULL     COMMENT 'Diseñador Industrial. FK a tbl_empleados. Se lleva a la OP.',
  `fecha_brif`              DATE          NULL     COMMENT 'Fecha de Brief. Propio de la ODI, NO se lleva a OP.',
  `diseno_o_producto`       VARCHAR(200)  NULL     COMMENT 'Diseño o Producto. Propio de la ODI, NO se lleva a OP.',
  `fecha_entrega`           DATE          NULL     COMMENT 'Fecha de Entrega. Propio de la ODI, NO se lleva a OP.',
  `fecha_produccion`        DATE          NULL     COMMENT 'Fecha de Producción. Propio de la ODI, NO se lleva a OP.',
  `estado`                  VARCHAR(50)   NULL     DEFAULT 'ACTIVO' COMMENT 'Estado de la ODI: ACTIVO, CERRADO, ANULADO',
  `fecha_registro`          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `id_usuario_registro`     INT           NULL,
  `fecha_borrado`           DATETIME      NULL,
  PRIMARY KEY (`id_odi`),
  UNIQUE KEY `uq_codigo_odi` (`codigo_odi`),
  KEY `fk_odi_cliente_idx`              (`id_cliente`),
  KEY `fk_odi_empleado_idx`             (`id_empleado`),
  KEY `fk_odi_disenador_industrial_idx` (`id_disenador_industrial`),
  KEY `fk_odi_usuario_idx`              (`id_usuario_registro`),
  CONSTRAINT `fk_odi_cliente`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `tbl_clientes` (`id_cliente`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_odi_empleado`
    FOREIGN KEY (`id_empleado`)
    REFERENCES `tbl_empleados` (`id_empleado`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_odi_disenador_industrial`
    FOREIGN KEY (`id_disenador_industrial`)
    REFERENCES `tbl_empleados` (`id_empleado`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_odi_usuario`
    FOREIGN KEY (`id_usuario_registro`)
    REFERENCES `users` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Órdenes de Diseño Industrial (ODI). Los campos proyecto, pieza, id_cliente, id_empleado e id_disenador_industrial se transfieren automáticamente a la OP cuando se selecciona una ODI.';


-- ------------------------------------------------------------
-- TABLA: tbl_documentos_odi
-- Almacena los documentos adjuntos de cada ODI
-- (Misma estructura que tbl_documentos_op)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tbl_documentos_odi` (
  `id_documento_odi`        INT           NOT NULL AUTO_INCREMENT,
  `id_odi`                  INT           NOT NULL,
  `documento_path`          VARCHAR(255)  NOT NULL COMMENT 'Hash del archivo en disco',
  `documento_nombre_original` VARCHAR(255) NOT NULL COMMENT 'Nombre original del archivo',
  `fecha_registro`          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado`           DATETIME      NULL,
  PRIMARY KEY (`id_documento_odi`),
  KEY `fk_doc_odi_idx` (`id_odi`),
  CONSTRAINT `fk_doc_odi`
    FOREIGN KEY (`id_odi`)
    REFERENCES `tbl_ordendisenoindustrial` (`id_odi`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Documentos adjuntos de las Órdenes de Diseño Industrial';


-- ------------------------------------------------------------
-- MODIFICACIÓN: tbl_ordenproduccion
-- Agrega la FK a la ODI para relacionar OP con ODI
-- Cuando se selecciona una ODI en la OP, los campos
-- referencia, producto, id_cliente, id_empleado e
-- id_disenador_industrial se llenan automáticamente.
-- ------------------------------------------------------------
-- Verificar si la columna id_odi ya existe antes de agregarla
-- (Si ya existe como VARCHAR, se puede dejar o migrar a INT FK)
-- NOTA: La columna 'odi' ya existe en tbl_ordenproduccion como VARCHAR(50).
-- Agregamos una nueva columna 'id_odi_fk' como FK a tbl_ordendisenoindustrial.
-- La columna 'odi' existente se puede usar para el código textual de la ODI.

ALTER TABLE `tbl_ordenproduccion`
  ADD COLUMN IF NOT EXISTS `id_odi_fk` INT NULL
    COMMENT 'FK a tbl_ordendisenoindustrial. Cuando se selecciona una ODI, los campos referencia, producto, id_cliente, id_empleado e id_disenador_industrial se llenan automáticamente.'
    AFTER `odi`;

ALTER TABLE `tbl_ordenproduccion`
  ADD CONSTRAINT `fk_op_odi`
    FOREIGN KEY IF NOT EXISTS (`id_odi_fk`)
    REFERENCES `tbl_ordendisenoindustrial` (`id_odi`)
    ON DELETE SET NULL ON UPDATE CASCADE;


-- ------------------------------------------------------------
-- DIRECTORIO para documentos ODI
-- (Crear manualmente en el servidor: static/documentos_odi/)
-- ------------------------------------------------------------
-- No se puede crear con SQL, pero se documenta aquí:
-- mkdir -p static/documentos_odi/


-- ------------------------------------------------------------
-- DATOS DE EJEMPLO (opcional, comentado)
-- ------------------------------------------------------------
/*
INSERT INTO `tbl_ordendisenoindustrial`
  (`codigo_odi`, `proyecto`, `pieza`, `id_cliente`, `id_empleado`, `id_disenador_industrial`,
   `fecha_brif`, `diseno_o_producto`, `fecha_entrega`, `fecha_produccion`, `estado`, `id_usuario_registro`)
VALUES
  ('ODI-2024-001', 'Proyecto Ejemplo', 'Pieza de Prueba', 1, 1, 1,
   '2024-01-15', 'Diseño', '2024-02-15', '2024-02-01', 'ACTIVO', 1);
*/
