-- ------------------------------------------------------------
-- Orden de compra por especificación de pieza.
-- Valor numérico entero, OPCIONAL y que puede repetirse
-- (una misma orden de compra puede cubrir varios ítems).
-- ------------------------------------------------------------

ALTER TABLE tbl_orden_pieza_especificaciones
  ADD COLUMN orden_compra INT NULL AFTER reproceso;
