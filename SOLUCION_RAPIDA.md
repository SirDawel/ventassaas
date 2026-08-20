# 🚨 SOLUCIÓN INMEDIATA - Error de Migraciones

## ❌ Tu Error Actual

```
django.db.migrations.exceptions.MigrationSchemaMissing: Unable to create the django_migrations table
(no schema has been selected to create in)
```

**Causa:** Tienes uno o más tenants en la base de datos sin su schema correspondiente en PostgreSQL.

---

## ⚡ SOLUCIÓN EN 3 COMANDOS

Copia y pega estos comandos uno por uno en tu servidor:

### 1️⃣ Descargar la solución

```bash
cd /var/www/ventas
git pull
source .venv/bin/activate
```

### 2️⃣ Limpiar tenants corruptos

```bash
python limpiar_tenants_corruptos.py
```

**Cuando te pregunte, escribe:** `ELIMINAR`

### 3️⃣ Ejecutar migraciones

```bash
python manage.py migrate_schemas
```

**✅ Deberías ver:**
```
[standard:public] No migrations to apply.
[1/X standard:tenant1] No migrations to apply.
[2/X standard:tenant2] No migrations to apply.
```

---

## 🔥 OPCIÓN ALTERNATIVA: Un solo comando

Si prefieres automatizar todo:

```bash
bash fix_rapido.sh
```

Este script ejecuta todo automáticamente (requiere confirmar una vez escribiendo `ELIMINAR`).

---

## 🛠️ OPCIÓN SQL DIRECTA (si Python falla)

Si el script Python no funciona:

```bash
sudo -u postgres psql ventassistemdb
```

Dentro de PostgreSQL, ejecuta:

```sql
-- Ver tenants sin schema
SELECT c.schema_name, c.nombre
FROM ventasweb_client c
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.schemata s
    WHERE s.schema_name = c.schema_name
);

-- Para cada tenant que aparezca (por ejemplo 'brevo'), ejecuta:
DROP SCHEMA IF EXISTS brevo CASCADE;
DELETE FROM ventasweb_domain WHERE tenant_id IN (SELECT id FROM ventasweb_client WHERE schema_name = 'brevo');
DELETE FROM ventasweb_client WHERE schema_name = 'brevo';

-- Repite para cada tenant corrupto
-- Luego sal:
\q
```

Después ejecuta las migraciones:

```bash
python manage.py migrate_schemas
```

---

## ✅ Verificar que funciona

```bash
# Ver tenants válidos
python listar_tenants.py

# Reiniciar servicios
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker

# Ver que no hay errores
sudo systemctl status gunicorn
```

---

## 🎯 Siguiente paso: Configurar Gmail

Una vez resuelto el error de migraciones, configura el email:

```bash
nano /var/www/ventas/.env
```

Agrega (reemplaza con tus datos):

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=contraseña-de-16-digitos-de-aplicacion
DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

Obtén la contraseña de aplicación aquí: https://myaccount.google.com/apppasswords

```bash
# Reiniciar servicios
sudo systemctl restart gunicorn celery-worker celery-beat
```

---

## 📞 Si sigues teniendo problemas

1. **Ver el error exacto:**
   ```bash
   python manage.py migrate_schemas 2>&1 | grep -A 10 "Error"
   ```

2. **Ver qué tenant falla:**
   ```bash
   python manage.py migrate_schemas 2>&1 | grep "standard:"
   ```

3. **Verificar conexión a PostgreSQL:**
   ```bash
   sudo -u postgres psql -l
   ```

4. **Ver logs de Django:**
   ```bash
   sudo journalctl -u gunicorn -n 100
   ```

---

## 📋 Resumen de comandos (copiar todo)

```bash
# Copiar y pegar todo esto de una vez:
cd /var/www/ventas
git pull
source .venv/bin/activate
python limpiar_tenants_corruptos.py
# (escribir ELIMINAR cuando pregunte)
python manage.py migrate_schemas
sudo systemctl restart gunicorn celery-worker celery-beat
python listar_tenants.py
```

**✅ Listo. Tu sistema debería estar funcionando.**
