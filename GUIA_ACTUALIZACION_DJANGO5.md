
# Guía de Actualización: Django 4.2 → 5.1 + django-tenants 3.6 → 3.12

## 📋 RESUMEN DE ACTUALIZACIONES

| Componente | Versión Anterior | Versión Nueva | Cambios Críticos |
|------------|------------------|---------------|------------------|
| Django | 4.2.17 | 5.1.4 | ⚠️ Breaking changes menores |
| django-tenants | 3.6.1 | 3.12.0 | ✅ Compatible con Django 5.x |
| PostgreSQL | 14+ | 16+ | ✅ Sin breaking changes |
| Python | 3.11+ | 3.13+ | ✅ Retrocompatible |
| psycopg | psycopg2 2.9.9 | psycopg3 3.3.4 | ⚠️ Cambio de API |
| Celery | 5.3.4 | 5.6.3 | ✅ Mejoras de estabilidad |
| Redis | 5.0.1 | 7.4.0 | ✅ Performance mejorado |
| Stripe | 8.0.0 | 15.1.0 | ⚠️ Cambios API importantes |
| Ubuntu | 22.04 LTS | 24.04 LTS | ✅ Sin breaking changes |

## 🚀 PASOS DE ACTUALIZACIÓN

### PASO 1: Backup Completo

```bash
# Backup de base de datos
pg_dump -U ventasapp -h localhost ventassistemdb > backup_pre_upgrade_$(date +%Y%m%d).sql

# Backup de archivos media
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Backup de código
git add -A
git commit -m "Pre-upgrade backup - Django 4.2 to 5.1"
git tag v1-django4.2-backup
```

### PASO 2: Crear Entorno de Prueba

```bash
# Crear nuevo virtualenv con Python 3.13
python3.13 -m venv venv_django5
source venv_django5/bin/activate

# Instalar nuevas dependencias
pip install --upgrade pip
pip install -r requirements_produccion.txt
```

### PASO 3: Actualizar settings.py

#### 3.1. Cambiar Engine de PostgreSQL (psycopg2 → psycopg3)

**ANTES (psycopg2):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',  # ← Basado en psycopg2
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}
```

**DESPUÉS (psycopg3):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',  # ← Ahora usa psycopg3 automáticamente
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            # Opciones específicas de psycopg3 (opcional)
            'connect_timeout': 10,
        },
    }
}
```

#### 3.2. Actualizar Middleware (si es necesario)

Django 5.1 requiere ciertos middleware. Verificar:

```python
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # ← Debe ir primero
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

#### 3.3. Configurar WhiteNoise (nuevo en stack)

```python
# Archivos estáticos con WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### PASO 4: Revisar Código Django

#### 4.1. Formularios - Field Groups (Django 5.1)

Django 5.1 introduce field groups en formularios. Si usas formularios personalizados:

**OPCIONAL - Aprovechar nueva feature:**
```python
class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telefono']
        field_groups = {
            'info_personal': ['first_name', 'last_name'],
            'contacto': ['email', 'telefono'],
        }
```

#### 4.2. Deprecaciones Removidas

Verificar si usas alguna de estas (deprecadas en Django 4.x, removidas en 5.x):

```python
# ❌ YA NO FUNCIONA:
from django.utils.translation import ugettext_lazy

# ✅ USAR EN SU LUGAR:
from django.utils.translation import gettext_lazy

# ❌ YA NO FUNCIONA:
url(r'^pattern/$', view)  # Old url() function

# ✅ USAR EN SU LUGAR:
path('pattern/', view)  # Modern path()
re_path(r'^pattern/$', view)  # Para regex
```

#### 4.3. Cambios en Admin (menores)

Si personalizaste el admin, revisar:

```python
# Django 5.1 tiene mejor soporte para facets en filters
class UserAdmin(admin.ModelAdmin):
    list_filter = [
        ('rol', admin.ChoicesFieldListFilter),  # ← Mejorado en 5.1
    ]
```

### PASO 5: Actualizar Código Stripe

Stripe 8.0 → 15.1 tiene cambios significativos en la API:

**ANTES (Stripe 8.0):**
```python
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Crear customer
customer = stripe.Customer.create(
    email=user.email,
    name=user.get_full_name()
)
```

**DESPUÉS (Stripe 15.1):**
```python
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# API mejorada con mejor tipado y nuevos métodos
customer = stripe.Customer.create(
    email=user.email,
    name=user.get_full_name(),
    metadata={'tenant_id': tenant.id}  # ← Recomendado para multitenant
)

# Nota: Revisar documentación de Stripe para cambios en:
# - Webhooks (versión de API actualizada)
# - Métodos de pago (mejoras en Payment Intents)
# - Suscripciones (nuevas opciones de billing)
```

### PASO 6: Ejecutar Migraciones

```bash
# Activar virtualenv nuevo
source venv_django5/bin/activate

# Verificar que django-tenants funciona
python manage.py showmigrations

# Migrar schema público
python manage.py migrate_schemas --shared

# Migrar todos los tenants
python manage.py migrate_schemas

# Crear archivos estáticos
python manage.py collectstatic --noinput
```

### PASO 7: Testing

#### 7.1. Pruebas Locales

```bash
# Iniciar servidor de desarrollo
python manage.py runserver 0.0.0.0:8000

# Probar acceso a tenant público
curl http://localhost:8000/

# Probar acceso a tenant cliente
curl -H "Host: picapolloeka.localhost" http://localhost:8000/
```

#### 7.2. Verificar Celery

```bash
# Verificar que Redis funciona
redis-cli ping  # Debe responder: PONG

# Iniciar Celery worker
celery -A VentasSys worker -l info

# Iniciar Celery beat (en otra terminal)
celery -A VentasSys beat -l info
```

#### 7.3. Verificar PostgreSQL 16

```bash
# Verificar versión
psql -U ventasapp -d ventassistemdb -c "SELECT version();"

# Verificar schemas
psql -U ventasapp -d ventassistemdb -c "\dn"

# Debe mostrar: public, picapolloeka, y otros tenants
```

### PASO 8: Deploy en Producción (Ubuntu 24.04)

#### 8.1. Actualizar Sistema Operativo

```bash
# Si estás en Ubuntu 22.04, actualizar a 24.04
sudo do-release-upgrade

# Si es instalación nueva, usar Ubuntu 24.04 LTS desde el inicio
```

#### 8.2. Instalar Python 3.13

```bash
# En Ubuntu 24.04
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# Verificar versión
python3.13 --version  # Python 3.13.x
```

#### 8.3. Instalar PostgreSQL 16

```bash
# Agregar repositorio oficial de PostgreSQL
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

sudo apt update
sudo apt install -y postgresql-16 postgresql-contrib-16

# Verificar versión
psql --version  # PostgreSQL 16.x
```

#### 8.4. Desplegar Aplicación

Seguir el prompt completo en: `PROMPT_DEPLOY_AWS_DJANGO_TENANTS.md`

## ⚠️ TROUBLESHOOTING

### Error: "No module named 'psycopg2'"

**Causa:** Código antiguo importa psycopg2 directamente.

**Solución:**
```bash
# Buscar imports de psycopg2
grep -r "import psycopg2" .

# Cambiar a psycopg (si es necesario)
# En la mayoría de casos, Django maneja esto automáticamente
```

### Error: "ugettext_lazy not found"

**Causa:** Django 5.x removió `ugettext_lazy`.

**Solución:**
```bash
# Buscar todas las referencias
grep -r "ugettext_lazy" .

# Reemplazar con gettext_lazy
sed -i 's/ugettext_lazy/gettext_lazy/g' **/*.py
```

### Error: Stripe API cambió

**Causa:** Stripe 11.x tiene cambios menores en API.

**Solución:**
Revisar documentación oficial: https://stripe.com/docs/upgrades

### Performance lento después de actualizar

**Causa:** PostgreSQL 16 requiere ANALYZE después de upgrade.

**Solución:**
```sql
-- Conectar a base de datos
psql -U ventasapp -d ventassistemdb

-- Analizar todas las tablas
ANALYZE VERBOSE;

-- Vacuumm completo (hacer en horario de baja carga)
VACUUM ANALYZE;
```

## 📊 CHECKLIST POST-ACTUALIZACIÓN

- [ ] ✅ Todas las migraciones ejecutadas correctamente
- [ ] ✅ Servidor de desarrollo funciona en localhost
- [ ] ✅ Todos los tenants accesibles por subdominio
- [ ] ✅ Login funciona correctamente
- [ ] ✅ Creación de usuarios funciona (diferentes roles)
- [ ] ✅ Facturación funciona correctamente
- [ ] ✅ Búsqueda de productos funciona
- [ ] ✅ Celery procesa tareas correctamente
- [ ] ✅ Celery Beat ejecuta tareas programadas
- [ ] ✅ Stripe procesa pagos (usar test keys)
- [ ] ✅ Archivos estáticos se cargan correctamente
- [ ] ✅ Upload de imágenes funciona
- [ ] ✅ Emails se envían correctamente
- [ ] ✅ Logs se generan sin errores
- [ ] ✅ Performance aceptable (comparar con versión anterior)
- [ ] ✅ Backups automáticos funcionan

## 🎯 VENTAJAS DE LA ACTUALIZACIÓN

### Django 5.1:
- ✅ Mejor performance en queries ORM (10-15% más rápido)
- ✅ Mejor soporte para PostgreSQL 16
- ✅ Field groups en formularios (mejor UX)
- ✅ Admin mejorado con facets
- ✅ Seguridad actualizada

### django-tenants 3.12:
- ✅ Compatible con Django 5.x
- ✅ Mejor performance en tenant switching
- ✅ Migraciones más rápidas y estables
- ✅ Fixes importantes de bugs
- ✅ Mejor documentación

### Python 3.13:
- ✅ JIT compiler experimental (performance boost)
- ✅ Mejor manejo de memoria
- ✅ f-strings más rápidos

### Celery 5.6:
- ✅ Mejor estabilidad en Windows
- ✅ Performance mejorado
- ✅ Mejor manejo de errores

### Redis 7.4:
- ✅ Performance significativamente mejorado
- ✅ Mejor uso de memoria
- ✅ Nuevas estructuras de datos

### PostgreSQL 16:
- ✅ Queries paralelos más rápidos
- ✅ Mejor performance JSON/JSONB
- ✅ Monitoring mejorado

### psycopg3:
- ✅ API moderna
- ✅ Soporte async/await nativo
- ✅ Mejor performance
- ✅ Pipeline mode para batch queries

## 📞 SOPORTE

Si encuentras problemas durante la actualización:

1. Revisar logs: `python manage.py check --deploy`
2. Verificar compatibilidad: https://docs.djangoproject.com/en/5.1/releases/5.1/
3. Documentación django-tenants: https://django-tenants.readthedocs.io/
4. Rollback si es necesario: restaurar desde backup

---

**Fecha de creación:** 2026-08-02  
**Autor:** Sistema de Ventas Multitenant  
**Versión:** 1.0
