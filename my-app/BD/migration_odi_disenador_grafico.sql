-- Agrega columna id_disenador_grafico a la tabla de ODIs
ALTER TABLE `tbl_ordendisenoindustrial`
  ADD COLUMN IF NOT EXISTS `id_disenador_grafico` INT NULL
  AFTER `id_disenador_industrial`,
  ADD CONSTRAINT `fk_odi_disenador_grafico`
    FOREIGN KEY (`id_disenador_grafico`) REFERENCES `tbl_empleados`(`id_empleado`)
    ON DELETE SET NULL ON UPDATE CASCADE;
