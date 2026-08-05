-- ------------------------------------------------------------
-- Permite asociar una operación diaria a una OP o a una ODI.
-- Regla de negocio: se debe asignar SOLO UNA de las dos
-- (la validación "exactamente una" se hace en la capa de aplicación,
--  ya que MySQL < 8.0.16 ignora los CHECK).
-- ------------------------------------------------------------

-- Nueva columna id_odi (FK opcional a la Orden de Diseño Industrial)
ALTER TABLE tbl_operaciones
  ADD COLUMN id_odi INT NULL AFTER id_op,
  ADD CONSTRAINT fk_operaciones_odi
      FOREIGN KEY (id_odi) REFERENCES tbl_ordendisenoindustrial (id_odi);

-- Aseguramos que id_op sea NULLABLE (ahora puede ir vacío cuando se usa una ODI).
-- Si la columna ya es NULL, esta sentencia no causa problema.
ALTER TABLE tbl_operaciones
  MODIFY COLUMN id_op INT NULL;
