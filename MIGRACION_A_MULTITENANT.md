# 🔄 Migración a Multi-Tenant: Paso a Paso

## ✅ Garantía: Tu Código Actual NO Se Pierde

**Antes de empezar:**
- Haz backup completo del proyecto
- Tu código actual funcionará igual después
- Solo cambiarás configuración, no lógica

---

## 📋 Checklist de Migración

### ✅ Fase 1: Preparación (30 minutos)

- [ ] 1.1 Hacer backup de `db.sqlite3`
- [ ] 1.2 Exportar datos actuales
- [ ] 1.3 Instalar PostgreSQL
- [ ] 1.4 Crear base de datos PostgreSQL

### ✅ Fase 2: Instalación (15 minutos)

- [ ] 2.1 Instalar `django-tenants` y `psycopg2`
- [ ] 2.2 Actualizar `requirements.txt`

### ✅ Fase 3: Configuración (30 minutos)

- [ ] 3.1 Crear modelos `Escuela` y `Dominio`
- [ ] 3.2 Actualizar `settings.py`
- [ ] 3.3 Crear `urls_public.py`

### ✅ Fase 4: Migración (30 minutos)

- [ ] 4.1 Ejecutar migraciones
- [ ] 4.2 Crear tenant público
- [ ] 4.3 Crear primera escuela
- [ ] 4.4 Importar datos existentes

### ✅ Fase 5: Pruebas (30 minutos)

- [ ] 5.1 Probar acceso con subdominios
- [ ] 5.2 Verificar datos migrados
- [ ] 5.3 Crear segunda escuela de prueba
- [ ] 5.4 Verificar aislamiento de datos

**Tiempo total estimado: 2-3 horas**

---

## 🔧 Paso 1: Preparación y Backup

### 1.1 Backup del Proyecto

```bash
# Crear carpeta de respaldo
cd E:\Escuela_backup
cp -r Escuela Escuela_BACKUP_$(date +%Y%m%d)

# O en PowerShell:
Copy-Item -Path "E:\Escuela_backup\Escuela" -Destination "E:\Escuela_backup\Escuela_BACKUP_$(Get-Date -Format 'yyyyMMdd')" -Recurse
```

### 1.2 Exportar Datos Actuales

```bash
cd E:\Escuela_backup\Escuela
.\.venv\Scripts\Activate.ps1

# Exportar TODOS los datos
python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission > backup_completo.json

# Exportar solo datos de tu app
python manage.py dumpdata escuelaweb --natural-foreign --natural-primary > backup_escuelaweb.json
```

**Guarda estos archivos JSON en lugar seguro.**

---

## 🐘 Paso 2: Instalar PostgreSQL

### 2.1 Descargar e Instalar

1. Descargar desde: https://www.postgresql.org/download/windows/
2. Ejecutar instalador (PostgreSQL 16)
3. Durante instalación:
   - Puerto: `5432` (default)
   - Password superusuario: **Anota esto bien** 🔑
   - Locale: Spanish, Dominican Republic (opcional)

### 2.2 Crear Base de Datos

**Opción A: pgAdmin (GUI)**
1. Abrir pgAdmin 4
2. Conectar a PostgreSQL
3. Click derecho en "Databases" → "Create" → "Database"
   - Name: `escuela_multi_tenant`
   - Owner: postgres

**Opción B: Línea de comandos**
```bash
# Abrir psql
psql -U postgres

# Crear usuario
CREATE USER escuela_user WITH PASSWORD 'tu_password_seguro_123';

# Crear base de datos
CREATE DATABASE escuela_multi_tenant OWNER escuela_user;

# Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE escuela_multi_tenant TO escuela_user;

# Salir
\q
```

---

## 📦 Paso 3: Instalar Django-Tenants

```bash
cd E:\Escuela_backup\Escuela
.\.venv\Scripts\Activate.ps1

# Instalar paquetes
pip install django-tenants==3.5.0
pip install psycopg2-binary==2.9.9

# Actualizar requirements.txt
pip freeze > requirements.txt
```

---

## 🔧 Paso 4: Crear Modelos de Tenant

### 4.1 Crear archivo `escuelaweb/models_tenant.py`

```python
"""
Modelos para Multi-Tenant
Cada Escuela es un tenant separado con sus propios datos
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Escuela(TenantMixin):
    """
    Modelo principal de Tenant (Escuela)
    Cada escuela tiene su propio schema en PostgreSQL
    """
    # Información básica
    nombre = models.CharField("Nombre de la Escuela", max_length=200)
    nombre_corto = models.CharField("Nombre Corto/Slug", max_length=50, unique=True,
                                   help_text="Para subdominios (ej: 'santiago' para santiago.escuelaenlinea.com)")
    
    # Contacto
    email_contacto = models.EmailField("Email de Contacto")
    telefono = models.CharField("Teléfono", max_length=20, blank=True)
    direccion = models.TextField("Dirección", blank=True)
    
    # Configuración
    fecha_creacion = models.DateTimeField("Fecha de Creación", auto_now_add=True)
    activo = models.BooleanField("Activo", default=True)
    max_usuarios = models.IntegerField("Máximo de Usuarios", default=500)
    
    # Personalización (para futuro)
    logo = models.ImageField("Logo", upload_to='logos_escuelas/', blank=True, null=True)
    color_primario = models.CharField("Color Primario", max_length=7, default='#007bff',
                                     help_text="Color hex (ej: #007bff)")
    
    # Suscripción (opcional)
    PLANES = [
        ('basico', 'Básico'),
        ('profesional', 'Profesional'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    plan = models.CharField("Plan", max_length=50, choices=PLANES, default='basico')
    fecha_vencimiento = models.DateField("Fecha de Vencimiento", blank=True, null=True)
    
    # Configuración de django-tenants
    auto_create_schema = True  # Crear schema automáticamente
    auto_drop_schema = False   # NO borrar automáticamente
    
    class Meta:
        verbose_name = "Escuela"
        verbose_name_plural = "Escuelas"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def esta_activa(self):
        """Verifica si la escuela está activa y no vencida"""
        if not self.activo:
            return False
        if self.fecha_vencimiento:
            from django.utils import timezone
            return self.fecha_vencimiento >= timezone.now().date()
        return True


class Dominio(DomainMixin):
    """
    Dominios/subdominios asociados a cada escuela
    Una escuela puede tener múltiples dominios
    """
    tenant = models.ForeignKey(Escuela, related_name='dominios', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"
    
    def __str__(self):
        return f"{self.domain} → {self.tenant.nombre}"
```

### 4.2 Importar en `escuelaweb/models.py`

```python
# Al FINAL de escuelaweb/models.py, agregar:

# Modelos Multi-Tenant
from .models_tenant import Escuela, Dominio
```

---

## ⚙️ Paso 5: Actualizar Settings

### 5.1 Modificar `Escuela/settings.py`

```python
# ============================================
# MULTI-TENANT CONFIGURATION
# ============================================

# 1. Actualizar INSTALLED_APPS (agregar al INICIO)
INSTALLED_APPS = [
    'django_tenants',  # ⚠️ DEBE SER EL PRIMERO
    'escuelaweb',      # Tu app
    
    # Apps de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Resto de tus apps...
]

# 2. Actualizar DATABASE (reemplazar completamente)
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',  # ⚠️ Importante
        'NAME': 'escuela_multi_tenant',
        'USER': 'escuela_user',
        'PASSWORD': 'tu_password_seguro_123',  # ⚠️ Cambiar
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# 3. Configurar Tenant
TENANT_MODEL = "escuelaweb.Escuela"
TENANT_DOMAIN_MODEL = "escuelaweb.Dominio"

# 4. Apps compartidas vs por tenant
SHARED_APPS = [
    'django_tenants',
    'escuelaweb',  # Para modelos Escuela y Dominio
    
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',
]

TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    
    'escuelaweb',  # Tus modelos de estudiantes, profesores, etc.
]

# 5. Actualizar MIDDLEWARE (agregar al INICIO)
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # ⚠️ PRIMERO
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Resto de tu middleware...
]

# 6. Configurar schemas
PUBLIC_SCHEMA_NAME = 'public'
PUBLIC_SCHEMA_URLCONF = 'Escuela.urls_public'

# 7. URLs por tenant
ROOT_URLCONF = 'Escuela.urls'  # Tus URLs actuales

# 8. Permitir subdominios
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.localhost',           # *.localhost para desarrollo
    '.escuelaenlinea.com',  # *.escuelaenlinea.com para producción
]

# 9. CORS (si usas)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
```

---

## 🌐 Paso 6: Crear URLs Públicas

### Crear `Escuela/urls_public.py`

```python
"""
URLs para el dominio público (sin tenant)
Ejemplo: www.escuelaenlinea.com o localhost:8000

Este es el sitio donde las escuelas se registran
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.shortcuts import render

def home_publica(request):
    """Página principal pública"""
    return render(request, 'public/home.html', {
        'titulo': 'Escuela en Línea - Sistema de Gestión Escolar'
    })

def registro_escuela(request):
    """Formulario de registro de nuevas escuelas"""
    return render(request, 'public/registro.html', {
        'titulo': 'Registrar tu Escuela'
    })

urlpatterns = [
    path('', home_publica, name='home_publica'),
    path('registro/', registro_escuela, name='registro_escuela'),
    path('admin/', admin.site.urls),
]
```

---

## 🗄️ Paso 7: Ejecutar Migraciones

```bash
cd E:\Escuela_backup\Escuela
.\.venv\Scripts\Activate.ps1

# 1. Crear archivos de migración
python manage.py makemigrations

# 2. Migrar schema público (administración)
python manage.py migrate_schemas --shared

# Debería mostrar:
# Running migrations for schema public
# ...
# Applying escuelaweb.XXXX_escuela... OK
# Applying escuelaweb.XXXX_dominio... OK
```

---

## 🏫 Paso 8: Crear Tenant Público (Requerido)

```bash
python manage.py shell
```

```python
from escuelaweb.models_tenant import Escuela, Dominio

# Crear tenant público (obligatorio)
tenant_publico = Escuela(
    schema_name='public',
    nombre='Escuela en Línea',
    nombre_corto='public',
    email_contacto='admin@escuelaenlinea.com'
)
tenant_publico.save()

# Crear dominio público
dominio = Dominio()
dominio.domain = 'localhost'  # Para desarrollo
# dominio.domain = 'www.escuelaenlinea.com'  # Para producción
dominio.tenant = tenant_publico
dominio.is_primary = True
dominio.save()

print("✅ Tenant público creado")
exit()
```

---

## 🏫 Paso 9: Crear Primera Escuela (Migrar tus datos)

```bash
python manage.py shell
```

```python
from escuelaweb.models_tenant import Escuela, Dominio

# Crear tu escuela actual
mi_escuela = Escuela(
    schema_name='miescuela',  # ⚠️ Sin espacios, minúsculas
    nombre='Mi Escuela Actual',
    nombre_corto='miescuela',
    email_contacto='contacto@miescuela.edu',
    telefono='809-555-0000',
    max_usuarios=1000,
    plan='premium'
)
mi_escuela.save()

# Crear dominio
dominio = Dominio()
dominio.domain = 'miescuela.localhost'  # Desarrollo
# dominio.domain = 'miescuela.escuelaenlinea.com'  # Producción
dominio.tenant = mi_escuela
dominio.is_primary = True
dominio.save()

print(f"✅ Escuela creada: {dominio.domain}")
exit()
```

---

## 📥 Paso 10: Importar Datos Existentes

```bash
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Opción A: Importar todo
python manage.py loaddata backup_completo.json

# Opción B: Importar solo tu app
python manage.py loaddata backup_escuelaweb.json
```

**Si hay errores de permisos o IDs:**
```python
python manage.py shell
```

```python
from django_tenants.utils import schema_context
from escuelaweb.models_tenant import Escuela

# Activar el schema de tu escuela
escuela = Escuela.objects.get(nombre_corto='miescuela')

with schema_context(escuela.schema_name):
    # Aquí puedes crear/modificar datos manualmente
    from escuelaweb.models import CustomUser
    
    # Ver usuarios importados
    usuarios = CustomUser.objects.all()
    print(f"Total usuarios: {usuarios.count()}")
    
    for usuario in usuarios[:5]:
        print(f"- {usuario.email}")
```

---

## 🌐 Paso 11: Configurar Hosts Locales

### Windows: Editar `C:\Windows\System32\drivers\etc\hosts`

**Abrir Notepad como Administrador** y agregar:

```
127.0.0.1 localhost
127.0.0.1 www.localhost
127.0.0.1 miescuela.localhost
127.0.0.1 escuela2.localhost
```

---

## 🚀 Paso 12: Probar el Sistema

```bash
# Iniciar servidor
python manage.py runserver
```

### Probar Accesos:

1. **Sitio público:** http://localhost:8000/
   - Debe mostrar página de registro

2. **Tu escuela migrada:** http://miescuela.localhost:8000/
   - Login con tus usuarios existentes
   - Todos tus datos deberían estar ahí

3. **Admin público:** http://localhost:8000/admin/
   - Gestionar escuelas

---

## ✅ Verificación Final

### Checklist de Verificación:

```python
python manage.py shell
```

```python
from escuelaweb.models_tenant import Escuela, Dominio
from django_tenants.utils import schema_context

# 1. Ver todas las escuelas
escuelas = Escuela.objects.all()
print(f"Total escuelas: {escuelas.count()}")
for e in escuelas:
    print(f"  - {e.nombre} ({e.schema_name})")

# 2. Ver dominios
dominios = Dominio.objects.all()
for d in dominios:
    print(f"  - {d.domain} → {d.tenant.nombre}")

# 3. Verificar datos en tu escuela
escuela = Escuela.objects.get(nombre_corto='miescuela')

with schema_context(escuela.schema_name):
    from escuelaweb.models import CustomUser, Estudiante, Profesor
    
    print(f"\nDatos en {escuela.nombre}:")
    print(f"  - Usuarios: {CustomUser.objects.count()}")
    print(f"  - Estudiantes: {Estudiante.objects.count()}")
    print(f"  - Profesores: {Profesor.objects.count()}")
```

---

## 🎯 Próximos Pasos

Una vez migrado exitosamente:

1. ✅ Crear templates públicos (`public/home.html`, `public/registro.html`)
2. ✅ Implementar vista de registro de escuelas
3. ✅ Agregar personalización por escuela (logo, colores)
4. ✅ Sistema de facturación/suscripción
5. ✅ Deploy a producción con dominio real

---

## 🆘 Troubleshooting

### Error: "No module named django_tenants"
```bash
pip install django-tenants==3.5.0
```

### Error: "Relation does not exist"
```bash
python manage.py migrate_schemas --shared
```

### Error: "Permission denied for schema"
```sql
-- En PostgreSQL
GRANT ALL ON SCHEMA public TO escuela_user;
GRANT ALL ON SCHEMA miescuela TO escuela_user;
```

### No encuentra el subdomain
- Verificar `C:\Windows\System32\drivers\etc\hosts`
- Reiniciar navegador
- Limpiar caché DNS: `ipconfig /flushdns`

---

## 📞 Soporte

Si encuentras errores durante la migración:
1. Revisa los logs de Django
2. Verifica configuración de PostgreSQL
3. Asegúrate de que los backups estén seguros
4. Consulta la documentación: https://django-tenants.readthedocs.io/

**¡No pierdas tu trabajo anterior! Siempre mantén los backups.**
