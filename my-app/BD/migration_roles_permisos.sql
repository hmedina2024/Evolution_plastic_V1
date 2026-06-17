-- Sistema de Roles y Permisos administrable desde la UI
CREATE TABLE IF NOT EXISTS `tbl_roles` (
  `id_rol`         INT          NOT NULL AUTO_INCREMENT,
  `nombre_rol`     VARCHAR(50)  NOT NULL,
  `descripcion`    VARCHAR(255) NULL,
  `es_sistema`     TINYINT(1)   NOT NULL DEFAULT 0,
  `fecha_registro` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_borrado`  DATETIME     NULL,
  PRIMARY KEY (`id_rol`),
  UNIQUE KEY `uq_nombre_rol` (`nombre_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `tbl_permisos` (
  `id_permiso`  INT          NOT NULL AUTO_INCREMENT,
  `modulo`      VARCHAR(50)  NOT NULL,
  `accion`      VARCHAR(20)  NOT NULL,
  `clave`       VARCHAR(80)  NOT NULL,
  `descripcion` VARCHAR(255) NULL,
  PRIMARY KEY (`id_permiso`),
  UNIQUE KEY `uq_clave_permiso` (`clave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `tbl_roles_permisos` (
  `id_rol_permiso` INT NOT NULL AUTO_INCREMENT,
  `id_rol`     INT NOT NULL,
  `id_permiso` INT NOT NULL,
  PRIMARY KEY (`id_rol_permiso`),
  UNIQUE KEY `uq_rol_permiso` (`id_rol`, `id_permiso`),
  CONSTRAINT `fk_rp_rol`     FOREIGN KEY (`id_rol`)     REFERENCES `tbl_roles`(`id_rol`)       ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_rp_permiso` FOREIGN KEY (`id_permiso`) REFERENCES `tbl_permisos`(`id_permiso`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- El catálogo de permisos y la semilla de roles base (Administrador/Supervisor/
-- Operativo) con sus permisos iniciales se cargan automáticamente desde la app
-- (función seed_permisos_y_roles) la primera vez, replicando los permisos
-- actuales para no cambiar el comportamiento existente.
