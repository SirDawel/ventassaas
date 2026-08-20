-- Script SQL para limpiar TODOS los tenants corruptos
-- Ejecutar con: sudo -u postgres psql ventassistemdb -f limpiar_tenants_corruptos.sql

\echo '=========================================='
\echo 'LIMPIEZA DE TENANTS CORRUPTOS'
\echo '=========================================='

-- Paso 1: Ver todos los tenants en Django
\echo ''
\echo 'TENANTS EN DJANGO:'
\echo '------------------------------------------'
SELECT 
    schema_name,
    nombre,
    is_active,
    created::date as fecha_creacion
FROM ventasweb_client
ORDER BY created DESC;

-- Paso 2: Ver todos los schemas en PostgreSQL
\echo ''
\echo 'SCHEMAS EN POSTGRESQL:'
\echo '------------------------------------------'
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'public')
ORDER BY schema_name;

-- Paso 3: Encontrar tenants sin schema (corruptos)
\echo ''
\echo 'TENANTS CORRUPTOS (existen en Django pero no tienen schema):'
\echo '------------------------------------------'
SELECT 
    c.id,
    c.schema_name,
    c.nombre,
    string_agg(d.domain, ', ') as dominios
FROM ventasweb_client c
LEFT JOIN ventasweb_domain d ON d.tenant_id = c.id
WHERE NOT EXISTS (
    SELECT 1 
    FROM information_schema.schemata s
    WHERE s.schema_name = c.schema_name
)
GROUP BY c.id, c.schema_name, c.nombre;

\echo ''
\echo '=========================================='
\echo 'PARA ELIMINAR TENANTS CORRUPTOS, ejecuta:'
\echo 'sudo -u postgres psql ventassistemdb'
\echo ''
\echo 'Luego copia y pega:'
\echo '=========================================='
\echo ''
\echo '-- Eliminar tenant brevo (ejemplo)'
\echo 'DROP SCHEMA IF EXISTS brevo CASCADE;'
\echo 'DELETE FROM ventasweb_domain WHERE tenant_id IN (SELECT id FROM ventasweb_client WHERE schema_name = '\''brevo'\'');'
\echo 'DELETE FROM ventasweb_client WHERE schema_name = '\''brevo'\'';'
\echo ''
\echo '-- Repite para cada tenant corrupto que encuentres arriba'
\echo ''
