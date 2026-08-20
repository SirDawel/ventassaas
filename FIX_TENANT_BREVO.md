# ⚠️ Solución Rápida: Error "no schema has been selected to create in"

## 🔴 Problema

Al ejecutar `python manage.py migrate_schemas`, falla en el tenant "brevo":

```
django.db.migrations.exceptions.MigrationSchemaMissing: Unable to create the django_migrations table 
(no schema has been selected to create in)
```

## ✅ Causa

El tenant "brevo" existe en la base de datos pero su schema no existe en PostgreSQL, o está corrupto.

## 🛠️ Solución: Opción 1 - Eliminar Tenant Brevo (Recomendado)

Si no necesitas el tenant "brevo":

### 1. Subir scripts al servidor

```bash
# En tu máquina local
git add listar_tenants.py eliminar_tenant_brevo.py
git commit -m "Scripts para gestionar tenant brevo"
git push
```

### 2. En el servidor EC2

```bash
cd /var/www/ventas
git pull
source .venv/bin/activate

# Listar todos los tenants
python listar_tenants.py

# Eliminar tenant brevo
python eliminar_tenant_brevo.py
```

Confirma con "si" cuando te lo pida.

### 3. Ejecutar migraciones nuevamente

```bash
python manage.py migrate_schemas
```

## 🛠️ Solución: Opción 2 - Recrear Schema Manualmente

Si necesitas conservar el tenant "brevo":

### 1. Conectarse a PostgreSQL

```bash
sudo -u postgres psql ventassistemdb
```

### 2. Crear el schema manualmente

```sql
-- Verificar schemas existentes
\dn

-- Crear schema brevo si no existe
CREATE SCHEMA IF NOT EXISTS brevo;

-- Dar permisos al usuario
GRANT ALL PRIVILEGES ON SCHEMA brevo TO ventasuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA brevo TO ventasuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA brevo TO ventasuser;

-- Salir
\q
```

### 3. Ejecutar migraciones

```bash
cd /var/www/ventas
source .venv/bin/activate
python manage.py migrate_schemas
```

## 🛠️ Solución: Opción 3 - SQL Directo (Más Rápido)

```bash
# En el servidor
cd /var/www/ventas
source .venv/bin/activate
python manage.py shell
```

```python
from ventasweb.models import Client, Domain
from django.db import connection

# Ver el tenant problemático
tenant = Client.objects.get(schema_name='brevo')
print(f"Tenant: {tenant.nombre}")
print(f"Dominios: {[d.domain for d in tenant.domains.all()]}")

# Opción A: Eliminar completamente
with connection.cursor() as cursor:
    cursor.execute("DROP SCHEMA IF EXISTS brevo CASCADE;")
Domain.objects.filter(tenant=tenant).delete()
tenant.delete()
print("✅ Tenant eliminado")

# Opción B: Solo recrear schema
with connection.cursor() as cursor:
    cursor.execute("CREATE SCHEMA IF NOT EXISTS brevo;")
print("✅ Schema recreado")

exit()
```

Después ejecuta:

```bash
python manage.py migrate_schemas
```

## 🔍 Verificar Solución

```bash
# Listar todos los tenants y verificar schemas
python listar_tenants.py

# Probar migraciones
python manage.py migrate_schemas

# Si todo está bien, deberías ver:
# [standard:public] No migrations to apply.
# [1/X standard:tenant1] No migrations to apply.
# [2/X standard:tenant2] No migrations to apply.
# ... (sin errores)
```

## 📝 Prevención

Para evitar tenants corruptos en el futuro, SIEMPRE crea tenants usando scripts oficiales:

```python
# crear_nuevo_tenant.py
from ventasweb.models import Client, Domain
from django.contrib.auth import get_user_model

tenant = Client(
    schema_name='nombreempresa',
    nombre='Nombre Empresa',
    nombre_corto='nombreempresa',
    is_active=True
)
tenant.save()  # Esto crea el schema automáticamente

# Agregar dominios
Domain.objects.create(domain='nombreempresa.misventasflash.com', tenant=tenant, is_primary=True)
Domain.objects.create(domain='nombreempresa.localhost', tenant=tenant, is_primary=False)
```

## ⚡ Resumen Rápido

```bash
# Opción más rápida (si no necesitas el tenant):
cd /var/www/ventas
source .venv/bin/activate
python eliminar_tenant_brevo.py  # responde "si"
python manage.py migrate_schemas
sudo systemctl restart gunicorn
```

**✅ Problema resuelto. Las migraciones deberían ejecutarse sin errores.**
