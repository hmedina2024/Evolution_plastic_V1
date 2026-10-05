-- Cargo del contacto y medio por el que se consiguio el prospecto
-- (origen del prospecto: Teléfono, Email, WhatsApp, Referido, etc.).
ALTER TABLE tbl_prospectos
  ADD COLUMN cargo_prospecto VARCHAR(100) NULL AFTER empresa_prospecto,
  ADD COLUMN medio_contacto VARCHAR(50) NULL AFTER email_prospecto;
