-- ============================================================
-- Otorga los permisos del nuevo modulo de Actividad Comercial a los
-- roles Supervisor y Operativo YA EXISTENTES.
-- ------------------------------------------------------------
-- El sembrado automatico de permisos (seed_permisos_y_roles, que corre
-- solo al arrancar la app) SIEMPRE actualiza al rol Administrador con
-- los permisos nuevos, pero SOLO asigna el set completo de permisos a
-- un rol Supervisor/Operativo si ese rol se esta creando por primera
-- vez. Si esos roles ya existian en la BD (caso normal en un sistema
-- en produccion), no reciben automaticamente los permisos de modulos
-- agregados despues. Esta migracion corrige eso puntualmente para el
-- modulo de Actividad Comercial.
--
-- IMPORTANTE: ejecutar DESPUES de haber arrancado la app al menos una
-- vez con el codigo nuevo (el arranque siembra las filas en
-- tbl_permisos que esta consulta necesita). Es segura de re-ejecutar:
-- si el permiso ya estaba otorgado, no se duplica.
-- ============================================================

INSERT INTO tbl_roles_permisos (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM tbl_roles r
JOIN tbl_permisos p ON p.clave IN (
    'comercial.ver', 'comercial.crear', 'comercial.editar', 'comercial.eliminar',
    'prospectos.ver', 'prospectos.crear', 'prospectos.editar'
)
WHERE r.nombre_rol = 'Operativo'
  AND NOT EXISTS (
      SELECT 1 FROM tbl_roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );

INSERT INTO tbl_roles_permisos (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM tbl_roles r
JOIN tbl_permisos p ON p.clave IN (
    'comercial.ver', 'comercial.crear', 'comercial.editar', 'comercial.eliminar',
    'prospectos.ver', 'prospectos.crear', 'prospectos.editar',
    'metas_comercial.ver', 'metas_comercial.editar'
)
WHERE r.nombre_rol = 'Supervisor'
  AND NOT EXISTS (
      SELECT 1 FROM tbl_roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
