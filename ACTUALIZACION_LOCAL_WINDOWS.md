# Actualización Local - Windows (Django 4.2 → 5.1)

## 📋 RESUMEN

Esta guía te ayudará a actualizar tu entorno de desarrollo local en Windows a las versiones más recientes:
- Django 4.2.17 → **5.1.3**
- django-tenants 3.6.1 → **4.0.0**
- Python 3.11 → **3.13**
- PostgreSQL 14 → **16**
- Todas las dependencias actualizadas

---

## ⚠️ PASO 0: BACKUP COMPLETO

### 0.1. Backup de Base de Datos

```powershell
# Abrir PowerShell en E:\AWSAMAZON\Ventas
cd E:\AWSAMAZON\Ventas

# Crear carpeta de backups si no existe
New-Item -ItemType Directory -Force -Path "backups"

# Backup de PostgreSQL (ajustar puerto si es diferente)
$fecha = Get-Date -Format "yyyyMMdd_HHmmss"
& "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U postgres -h 127.0.0.1 -p 5434 ventassistemdb > "backups\backup_pre_upgrade_$fecha.sql"

Write-Host "✅ Backup creado: backups\backup_pre_upgrade_$fecha.sql" -ForegroundColor Green
```

### 0.2. Backup de Archivos Media

```powershell
# Backup de archivos subidos por usuarios
$fecha = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path "media\*" -DestinationPath "backups\media_backup_$fecha.zip" -Force

Write-Host "✅ Backup media creado: backups\media_backup_$fecha.zip" -ForegroundColor Green
```

### 0.3. Backup de Código (Git)

```powershell
# Commit actual antes de actualizar
git add -A
git status
git commit -m "Pre-upgrade backup - Django 4.2 to 5.1"
git tag v1.0-django4.2-backup

Write-Host "✅ Backup en Git creado con tag: v1.0-django4.2-backup" -ForegroundColor Green
```

---

## 🐍 PASO 1: INSTALAR PYTHON 3.13

### 1.1. Descargar Python 3.13

1. Ir a: https://www.python.org/downloads/
2. Descargar **Python 3.13.x** (Windows installer 64-bit)
3. Ejecutar instalador:
   - ✅ **Marcar:** "Add Python 3.13 to PATH"
   - ✅ **Marcar:** "Install for all users" (opcional)
   - Click en "Install Now"

### 1.2. Verificar Instalación

```powershell
# Abrir PowerShell NUEVO (para que cargue el PATH actualizado)
python --version
# Debe mostrar: Python 3.13.x

# Verificar pip
pip --version
# Debe mostrar: pip 24.x.x from ... (python 3.13)
```

---

## 🔄 PASO 2: CREAR NUEVO VIRTUALENV

### 2.1. Desactivar Virtualenv Actual

```powershell
# Si tienes un virtualenv activo
deactivate

# Ir a carpeta del proyecto
cd E:\AWSAMAZON\Ventas
```

### 2.2. Renombrar Virtualenv Anterior (Backup)

```powershell
# Renombrar .venv a .venv_old (por si necesitas rollback)
Rename-Item -Path ".venv" -NewName ".venv_old"

Write-Host "✅ Virtualenv anterior respaldado como .venv_old" -ForegroundColor Green
```

### 2.3. Crear Nuevo Virtualenv con Python 3.13

```powershell
# Crear nuevo virtualenv con Python 3.13
python -m venv .venv

Write-Host "✅ Nuevo virtualenv creado con Python 3.13" -ForegroundColor Green
```

### 2.4. Activar Nuevo Virtualenv

```powershell
# Activar virtualenv
.\.venv\Scripts\Activate.ps1

# Si da error de permisos de ejecución, ejecutar:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

# Intentar activar de nuevo
.\.venv\Scripts\Activate.ps1

# Verificar versión de Python en virtualenv
python --version
# Debe mostrar: Python 3.13.x
```

---

## 📦 PASO 3: INSTALAR DEPENDENCIAS ACTUALIZADAS

### 3.1. Actualizar pip

```powershell
# Actualizar pip a última versión
python -m pip install --upgrade pip

# Verificar
pip --version
```

### 3.2. Instalar Dependencias de Producción

```powershell
# Instalar desde el nuevo requirements
pip install -r requirements_produccion.txt

# Esto instalará:
# - Django 5.1.4
# - django-tenants 3.12.0
# - psycopg3 3.3.4
# - gunicorn 23.0.0
# - celery 5.6.3
# - redis 7.4.0
# - stripe 15.1.0
# - whitenoise 6.12.0
# - etc.
```

### 3.3. Instalar Dependencias de Desarrollo (Opcional)

```powershell
# Herramientas útiles para desarrollo
pip install django-extensions ipython ipdb

Write-Host "✅ Dependencias instaladas correctamente" -ForegroundColor Green
```

### 3.4. Verificar Instalación

```powershell
# Verificar Django
python -c "import django; print('Django version:', django.get_version())"
# Debe mostrar: Django version: 5.1.4

# Verificar django-tenants  
pip show django-tenants | Select-String "Version"
# Debe mostrar: Version: 3.12.0

# Verificar psycopg
python -c "import psycopg; print('psycopg version:', psycopg.__version__)"
# Debe mostrar: psycopg version: 3.3.x
```
```

---

## 🐘 PASO 4: ACTUALIZAR POSTGRESQL (Opcional pero Recomendado)

### 4.1. Descargar PostgreSQL 16

1. Ir a: https://www.postgresql.org/download/windows/
2. Descargar **PostgreSQL 16** (Windows x86-64)
3. Ejecutar instalador
4. **IMPORTANTE:** Usar un puerto diferente durante instalación (ej: 5416) para no afectar tu PostgreSQL 14 actual

### 4.2. Migrar Datos de PostgreSQL 14 a 16 (Opcional)

```powershell
# Opción A: Usar pg_dump y pg_restore
# Backup desde PostgreSQL 14
& "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U postgres -h 127.0.0.1 -p 5434 -Fc ventassistemdb > "backups\db_pg14.backup"

# Crear base de datos en PostgreSQL 16
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h 127.0.0.1 -p 5416 -c "CREATE DATABASE ventassistemdb;"

# Restaurar en PostgreSQL 16
& "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" -U postgres -h 127.0.0.1 -p 5416 -d ventassistemdb "backups\db_pg14.backup"
```

**ALTERNATIVA:** Seguir usando PostgreSQL 14 (funciona perfectamente con Django 5.1)

---

## ⚙️ PASO 5: ACTUALIZAR ARCHIVOS DE CONFIGURACIÓN

### 5.1. Actualizar .env (si es necesario)

```powershell
# Editar .env
notepad .env
```

**Verificar que tenga:**
```env
# Django
SECRET_KEY=tu_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.localhost

# Base de datos
DB_NAME=ventassistemdb
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=5434  # O 5416 si actualizaste a PostgreSQL 16

# Redis
REDIS_URL=redis://localhost:6379/0

# Stripe (usar test keys en desarrollo)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...

# Email (opcional en desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5.2. Verificar settings.py

```powershell
# Editar VentasSys/settings.py
code VentasSys\settings.py
```

**Cambios importantes:**

```python
# ============================================================================
# CONFIGURACIÓN ACTUALIZADA PARA DJANGO 5.1
# ============================================================================

# Base de datos con psycopg3 (django-tenants lo maneja automáticamente)
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',  # ← Ahora usa psycopg3
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}

# Middleware (verificar orden)
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # ← PRIMERO
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Archivos estáticos con WhiteNoise (nuevo)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 5.3. Buscar y Reemplazar Deprecaciones

```powershell
# Buscar ugettext_lazy (deprecado en Django 5.x)
Select-String -Path "*.py" -Pattern "ugettext_lazy" -Recurse

# Si encuentras alguno, reemplazar manualmente:
# from django.utils.translation import ugettext_lazy → gettext_lazy
```

---

## 🔄 PASO 6: EJECUTAR MIGRACIONES

### 6.1. Verificar Conexión a Base de Datos

```powershell
# Activar virtualenv si no está activo
.\.venv\Scripts\Activate.ps1

# Verificar que Django puede conectar
python manage.py check
```

### 6.2. Ver Migraciones Pendientes

```powershell
# Ver estado de migraciones
python manage.py showmigrations
```

### 6.3. Ejecutar Migraciones en Schema Público

```powershell
# Migrar schema público primero
python manage.py migrate_schemas --shared

# Si hay errores, revisar logs
```

### 6.4. Ejecutar Migraciones en Todos los Tenants

```powershell
# Migrar todos los schemas de tenants
python manage.py migrate_schemas

# Esto puede tardar dependiendo de cuántos tenants tengas
```

### 6.5. Recolectar Archivos Estáticos

```powershell
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

Write-Host "✅ Migraciones completadas correctamente" -ForegroundColor Green
```

---

## 🧪 PASO 7: TESTING Y VERIFICACIÓN

### 7.1. Iniciar Servidor de Desarrollo

```powershell
# Iniciar servidor Django
python manage.py runserver 0.0.0.0:8000
```

**Dejar corriendo y abrir otro PowerShell para pruebas**

### 7.2. Probar Acceso a Aplicación

```powershell
# Probar con curl (instalar si no lo tienes: winget install curl)
curl http://localhost:8000/

# O abrir en navegador:
# http://localhost:8000/
# http://picapolloeka.localhost:8000/
```

### 7.3. Iniciar Redis (si lo usas)

```powershell
# Iniciar Redis (si está instalado)
# Opción 1: Redis en WSL2
wsl redis-server

# Opción 2: Redis nativo Windows
# Descargar desde: https://github.com/microsoftarchive/redis/releases
# Ejecutar: redis-server.exe
```

### 7.4. Iniciar Celery Worker (Nueva Terminal)

```powershell
# Activar virtualenv
cd E:\AWSAMAZON\Ventas
.\.venv\Scripts\Activate.ps1

# Iniciar Celery Worker
celery -A VentasSys worker --pool=solo -l info

# Nota: En Windows usar --pool=solo o --pool=gevent
```

### 7.5. Iniciar Celery Beat (Otra Terminal)

```powershell
# Activar virtualenv
cd E:\AWSAMAZON\Ventas
.\.venv\Scripts\Activate.ps1

# Iniciar Celery Beat
celery -A VentasSys beat -l info
```

---

## ✅ PASO 8: CHECKLIST DE VERIFICACIÓN

Probar cada funcionalidad:

```powershell
# Usar este script para probar automáticamente
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

print('✅ Django:', django.get_version())

from django.contrib.auth import get_user_model
User = get_user_model()
print('✅ CustomUser model:', User.__name__)

from ventasweb.models import Articulo, Factura
print('✅ Models importados correctamente')

from django_tenants.utils import get_tenant_model
Tenant = get_tenant_model()
print('✅ Tenants:', Tenant.objects.count())

print('\n🎉 Todo funciona correctamente!')
"
```

### Checklist Manual:

- [ ] ✅ Servidor inicia sin errores
- [ ] ✅ Login funciona correctamente
- [ ] ✅ Puede acceder con diferentes usuarios (Administrador, Secretaria, Cliente)
- [ ] ✅ Crear usuario nuevo funciona
- [ ] ✅ Crear factura funciona
- [ ] ✅ Búsqueda de productos funciona
- [ ] ✅ Archivos estáticos se cargan (CSS, JS)
- [ ] ✅ Imágenes se muestran correctamente
- [ ] ✅ Celery procesa tareas
- [ ] ✅ Celery Beat ejecuta tareas programadas
- [ ] ✅ Redis funciona correctamente
- [ ] ✅ Todos los tenants funcionan (probar subdominios)

---

## 🔥 TROUBLESHOOTING

### Error: "No module named 'psycopg2'"

**Causa:** Código antiguo busca psycopg2.

**Solución:**
```powershell
# Django maneja esto automáticamente
# Si persiste, verificar que no haya imports directos:
Select-String -Path "*.py" -Pattern "import psycopg2" -Recurse
```

### Error: "ugettext_lazy is not defined"

**Causa:** Django 5.x removió `ugettext_lazy`.

**Solución:**
```powershell
# Buscar en código
Select-String -Path "*.py" -Pattern "ugettext_lazy" -Recurse

# Reemplazar manualmente por gettext_lazy
```

### Error: Celery no inicia en Windows

**Causa:** Celery 5.x tiene problemas con Windows.

**Solución:**
```powershell
# Usar pool=solo
celery -A VentasSys worker --pool=solo -l info

# O instalar gevent
pip install gevent
celery -A VentasSys worker --pool=gevent -l info
```

### Error: Redis no funciona

**Causa:** Redis no está instalado o no corre en Windows.

**Solución:**
```powershell
# Opción 1: Usar Redis en WSL2 (recomendado)
wsl --install  # Si no tienes WSL
wsl sudo apt update
wsl sudo apt install redis-server
wsl redis-server

# Opción 2: Redis nativo Windows (desactualizado pero funciona)
# Descargar: https://github.com/microsoftarchive/redis/releases
# Ejecutar redis-server.exe

# Opción 3: Docker Desktop
docker run -d -p 6379:6379 redis:latest
```

### Error: PostgreSQL no conecta

**Causa:** Puerto o credenciales incorrectas.

**Solución:**
```powershell
# Verificar que PostgreSQL corre
Get-Service -Name "postgresql*"

# Verificar conexión con psql
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -h 127.0.0.1 -p 5434 -l

# Verificar .env tiene puerto correcto
Get-Content .env | Select-String "DB_PORT"
```

---

## 🔄 ROLLBACK (Si algo sale mal)

### Volver a Versión Anterior

```powershell
# 1. Desactivar virtualenv nuevo
deactivate

# 2. Eliminar virtualenv nuevo
Remove-Item -Recurse -Force .venv

# 3. Restaurar virtualenv anterior
Rename-Item -Path ".venv_old" -NewName ".venv"

# 4. Activar virtualenv anterior
.\.venv\Scripts\Activate.ps1

# 5. Restaurar base de datos
$ultimoBackup = Get-ChildItem backups\backup_pre_upgrade_*.sql | Sort-Object -Descending | Select-Object -First 1
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -h 127.0.0.1 -p 5434 -d ventassistemdb -f $ultimoBackup.FullName

# 6. Restaurar código desde Git
git checkout v1.0-django4.2-backup

Write-Host "✅ Rollback completado" -ForegroundColor Green
```

---

## 📊 SCRIPTS ÚTILES

### Script de Testing Completo

Crear archivo `test_upgrade.ps1`:

```powershell
# test_upgrade.ps1
Write-Host "🧪 Probando actualización..." -ForegroundColor Cyan

# Activar virtualenv
.\.venv\Scripts\Activate.ps1

# Verificar versiones
Write-Host "`n📦 Versiones instaladas:" -ForegroundColor Yellow
python -c "import django; print('Django:', django.get_version())"
python -c "import django_tenants; print('django-tenants:', django_tenants.__version__)"
python -c "import psycopg; print('psycopg:', psycopg.__version__)"

# Check de Django
Write-Host "`n🔍 Django check:" -ForegroundColor Yellow
python manage.py check

# Listar tenants
Write-Host "`n🏢 Tenants disponibles:" -ForegroundColor Yellow
python manage.py list_tenants

Write-Host "`n✅ Tests completados!" -ForegroundColor Green
```

Ejecutar:
```powershell
.\test_upgrade.ps1
```

---

## 📝 NOTAS IMPORTANTES

1. **Backup antes de actualizar** - No se puede enfatizar esto suficiente
2. **Probar en horario seguro** - Mejor hacerlo cuando no estés bajo presión
3. **Tener tiempo** - La actualización puede tomar 30-60 minutos
4. **Documentar problemas** - Anota cualquier error para futuras referencias
5. **Rollback disponible** - Si algo falla, puedes volver atrás

---

## 🎯 SIGUIENTES PASOS

Después de actualizar localmente:

1. ✅ Usar el proyecto actualizado por varios días
2. ✅ Probar todas las funcionalidades críticas
3. ✅ Verificar performance (debe ser igual o mejor)
4. ✅ Cuando estés seguro, actualizar producción usando `PROMPT_DEPLOY_AWS_DJANGO_TENANTS.md`

---

**Fecha:** 2026-08-02  
**Versión:** 1.0  
**Autor:** Sistema de Ventas Multitenant
