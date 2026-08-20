-- Script SQL para eliminar tenant brevo corrupto directamente en PostgreSQL
-- Ejecutar con: sudo -u postgres psql ventassistemdb < eliminar_brevo.sql

-- Ver información del tenant antes de eliminar
SELECT 
    id, 
    schema_name, 
    nombre, 
    nombre_corto,
    is_active,
    created
FROM ventasweb_client 
WHERE schema_name = 'brevo';

-- Ver dominios asociados
SELECT 
    id,
    domain,
    is_primary,
    tenant_id
FROM ventasweb_domain
WHERE tenant_id IN (SELECT id FROM ventasweb_client WHERE schema_name = 'brevo');

-- Eliminar schema de PostgreSQL (con CASCADE para eliminar todo su contenido)
DROP SCHEMA IF EXISTS brevo CASCADE;

-- Eliminar dominios asociados al tenant
DELETE FROM ventasweb_domain 
WHERE tenant_id IN (SELECT id FROM ventasweb_client WHERE schema_name = 'brevo');

-- Eliminar el tenant de la tabla
DELETE FROM ventasweb_client 
WHERE schema_name = 'brevo';

-- Verificar que se eliminó
SELECT COUNT(*) as tenants_brevo_restantes 
FROM ventasweb_client 
WHERE schema_name = 'brevo';

-- Listar schemas restantes en PostgreSQL
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schema_name;

-- Listar todos los tenants restantes
SELECT 
    schema_name,
    nombre,
    is_active,
    created
FROM ventasweb_client
ORDER BY created DESC;
