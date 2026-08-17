-- ------------------------------------------------------------
-- Correos adicionales por proceso para las alertas de documentos.
-- Permite enviar a correos sueltos además de (o en vez de) una lista.
-- Se guardan separados por coma. Los destinatarios finales son la
-- unión de: miembros de la lista + estos correos.
-- ------------------------------------------------------------

ALTER TABLE tbl_alertas_proceso
  ADD COLUMN correos_extra TEXT NULL AFTER id_lista;
