-- Tabla de URLs asociadas a ODIs
CREATE TABLE IF NOT EXISTS `tbl_odi_urls` (
  `id_odi_url`     INT          NOT NULL AUTO_INCREMENT,
  `id_odi`         INT          NOT NULL,
  `url`            TEXT         NOT NULL,
  `fecha_registro` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_odi_url`),
  CONSTRAINT `fk_odi_url_odi`
    FOREIGN KEY (`id_odi`) REFERENCES `tbl_ordendisenoindustrial`(`id_odi`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
