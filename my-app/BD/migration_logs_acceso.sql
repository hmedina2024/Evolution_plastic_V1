-- Tabla de auditoría de accesos y acciones críticas
CREATE TABLE IF NOT EXISTS `tbl_logs_acceso` (
  `id_log_acceso` INT          NOT NULL AUTO_INCREMENT,
  `id_usuario`    INT          NULL,
  `usuario_texto` VARCHAR(150) NULL,
  `accion`        VARCHAR(50)  NOT NULL,
  `modulo`        VARCHAR(50)  NULL,
  `descripcion`   VARCHAR(255) NULL,
  `ip`            VARCHAR(45)  NULL,
  `fecha`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_log_acceso`),
  KEY `idx_logs_acceso_fecha` (`fecha`),
  KEY `idx_logs_acceso_accion` (`accion`),
  CONSTRAINT `fk_logs_acceso_usuario`
    FOREIGN KEY (`id_usuario`) REFERENCES `users`(`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
