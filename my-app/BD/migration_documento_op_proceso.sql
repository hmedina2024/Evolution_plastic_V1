-- ------------------------------------------------------------
-- Permite asignar cada documento de la OP a un proceso de la OP.
-- La asignación es OPCIONAL (id_proceso puede quedar NULL).
-- ------------------------------------------------------------

ALTER TABLE tbl_documentos_op
  ADD COLUMN id_proceso INT NULL AFTER id_op,
  ADD CONSTRAINT fk_documentos_op_proceso
      FOREIGN KEY (id_proceso) REFERENCES tbl_procesos (id_proceso);
