# 🏫 Guía: Convertir a Sistema Multi-Tenant (Multi-Escuela)

## 📋 Resumen

Convertir el proyecto actual en un sistema donde múltiples escuelas puedan usar la misma plataforma con datos completamente separados.

**Ejemplo:**
- `www.escuelaenlinea.com` → Página principal/registro
- `colegiosantiago.escuelaenlinea.com` → Colegio Santiago
- `escuelalaesperanza.escuelaenlinea.com` → Escuela La Esperanza

---

## 🎯 Solución Recomendada: Django-Tenants

### ¿Qué es Django-Tenants?

Es un paquete que permite tener **múltiples "inquilinos" (tenants)** en una sola instalación de Django:
- Cada escuela = 1 tenant
- Cada tenant tiene su propio **schema** en PostgreSQL
- Los datos están **completamente aislados**
- El código es compartido

### Arquitectura

```
escuelaenlinea.com (público)
├── colegiosantiago.escuelaenlinea.com
│   ├── Schema: colegiosantiago
│   ├── Profesores, Estudiantes, Notas...
│   └── Completamente aislado
│
├── escuelalaesperanza.escuelaenlinea.com
│   ├── Schema: escuelalaesperanza
│   ├── Profesores, Estudiantes, Notas...
│   └── Completamente aislado
│
└── liceoelporvenir.escuelaenlinea.com
    ├── Schema: liceoelporvenir
    ├── Profesores, Estudiantes, Notas...
    └── Completamente aislado
```

---

## 📦 Paso 1: Instalación y Configuración

### 1.1 Instalar Dependencias

```bash
# En tu entorno virtual
pip install django-tenants
pip install psycopg2-binary  # Driver PostgreSQL
```

### 1.2 Migrar de SQLite a PostgreSQL

**Instalar PostgreSQL:**
- Descargar desde: https://www.postgresql.org/download/
- Instalar (usar puerto 5432 por defecto)
- Crear usuario y base de datos

```sql
-- En PostgreSQL
CREATE USER escuela_user WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE escuela_multi_tenant OWNER escuela_user;
GRANT ALL PRIVILEGES ON DATABASE escuela_multi_tenant TO escuela_user;
```

### 1.3 Actualizar requirements.txt

```txt
# Agregar al final
django-tenants==3.5.0
psycopg2-binary==2.9.9
```

---

## ⚙️ Paso 2: Configurar Django

### 2.1 Crear modelo de Tenant (Escuela)

**Crear: `escuelaweb/models_tenant.py`**

```python
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Escuela(TenantMixin):
    """
    Modelo principal de Tenant (Escuela)
    Cada escuela es un tenant separado
    """
    nombre = models.CharField(max_length=200)
    nombre_corto = models.CharField(max_length=50, unique=True)  # Para subdominios
    
    # Información de contacto
    email_contacto = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    
    # Configuración
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    max_usuarios = models.IntegerField(default=500)  # Límite de usuarios
    
    # Personalización
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    color_primario = models.CharField(max_length=7, default='#007bff')  # Hex color
    
    # Plan/Suscripción (opcional)
    plan = models.CharField(max_length=50, default='basico')  # basico, premium, enterprise
    fecha_vencimiento = models.DateField(blank=True, null=True)
    
    auto_create_schema = True
    auto_drop_schema = False  # No borrar automáticamente
    
    class Meta:
        verbose_name = "Escuela"
        verbose_name_plural = "Escuelas"
    
    def __str__(self):
        return self.nombre


class Dominio(DomainMixin):
    """
    Dominios/subdominios asociados a cada escuela
    """
    tenant = models.ForeignKey(Escuela, related_name='dominios', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"
```

### 2.2 Actualizar settings.py

```python
# Escuela/settings.py

# 1. Agregar al principio de INSTALLED_APPS
INSTALLED_APPS = [
    'django_tenants',  # Debe ser el PRIMERO
    'escuelaweb',
    'django.contrib.admin',
    'django.contrib.auth',
    # ... resto de apps
]

# 2. Configurar base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',  # ⚠️ Importante
        'NAME': 'escuela_multi_tenant',
        'USER': 'escuela_user',
        'PASSWORD': 'tu_password_seguro',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# 3. Configurar django-tenants
TENANT_MODEL = "escuelaweb.Escuela"  # Modelo de Escuela
TENANT_DOMAIN_MODEL = "escuelaweb.Dominio"  # Modelo de Dominio

# 4. Definir apps compartidas vs apps por tenant
SHARED_APPS = [
    'django_tenants',  # Debe estar aquí
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'escuelaweb',  # Para modelos compartidos
]

TENANT_APPS = [
    'django.contrib.contenttypes',
    'escuelaweb',  # Modelos específicos de cada escuela
]

# 5. Middleware (reemplazar el primero)
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # ⚠️ Debe ser el PRIMERO
    'django.middleware.security.SecurityMiddleware',
    # ... resto de middleware
]

# 6. Contexto público (dominio principal sin tenant)
PUBLIC_SCHEMA_NAME = 'public'
PUBLIC_SCHEMA_URLCONF = 'Escuela.urls_public'  # URLs públicas

# 7. URLs por tenant
ROOT_URLCONF = 'Escuela.urls'  # URLs de cada escuela

# 8. Permitir subdominios en desarrollo
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.escuelaenlinea.com',  # Producción
    '*.localhost',  # Desarrollo con subdominios
]
```

### 2.3 Crear URLs Públicas

**Crear: `Escuela/urls_public.py`**

```python
"""
URLs para el dominio público (sin tenant)
Ejemplo: www.escuelaenlinea.com
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='public/home.html'), name='home'),
    path('registro/', include('escuelaweb.urls_registro')),  # Registro de escuelas
    path('admin/', admin.site.urls),
]
```

---

## 🚀 Paso 3: Migración

### 3.1 Crear Migraciones

```bash
python manage.py makemigrations
```

### 3.2 Migrar Schema Público

```bash
python manage.py migrate_schemas --shared
```

### 3.3 Crear Tenant Público

```python
from escuelaweb.models_tenant import Escuela, Dominio

# Crear tenant público (requerido)
tenant_publico = Escuela(
    schema_name='public',
    nombre='Escuela en Línea',
    nombre_corto='public',
    email_contacto='admin@escuelaenlinea.com'
)
tenant_publico.save()

# Crear dominio público
dominio = Dominio()
dominio.domain = 'localhost'  # o 'www.escuelaenlinea.com'
dominio.tenant = tenant_publico
dominio.is_primary = True
dominio.save()
```

---

## 🏫 Paso 4: Crear Escuelas (Tenants)

### 4.1 Vista de Registro de Escuelas

**Crear: `escuelaweb/views_registro.py`**

```python
from django.shortcuts import render, redirect
from django.contrib import messages
from .models_tenant import Escuela, Dominio
from django.db import connection

def registrar_escuela(request):
    """Vista pública para registrar nuevas escuelas"""
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        nombre_corto = request.POST.get('nombre_corto').lower().strip()
        email = request.POST.get('email')
        
        # Validar
        if Escuela.objects.filter(nombre_corto=nombre_corto).exists():
            messages.error(request, 'Este nombre corto ya está en uso')
            return render(request, 'public/registro.html')
        
        # Crear tenant
        tenant = Escuela(
            schema_name=nombre_corto,
            nombre=nombre,
            nombre_corto=nombre_corto,
            email_contacto=email
        )
        tenant.save()
        
        # Crear dominio
        dominio = Dominio()
        dominio.domain = f'{nombre_corto}.localhost'  # Dev
        # dominio.domain = f'{nombre_corto}.escuelaenlinea.com'  # Producción
        dominio.tenant = tenant
        dominio.is_primary = True
        dominio.save()
        
        messages.success(request, 
            f'¡Escuela creada! Accede en: {dominio.domain}')
        
        return redirect('login')
    
    return render(request, 'public/registro.html')
```

### 4.2 Crear Escuela desde Admin/Script

```python
from escuelaweb.models_tenant import Escuela, Dominio

# Crear escuela
escuela = Escuela(
    schema_name='colegiosantiago',
    nombre='Colegio Santiago',
    nombre_corto='colegiosantiago',
    email_contacto='info@colegiosantiago.edu',
    telefono='809-555-0000',
    max_usuarios=300,
    plan='premium'
)
escuela.save()

# Crear dominio
dominio = Dominio()
dominio.domain = 'colegiosantiago.localhost'  # Desarrollo
# dominio.domain = 'colegiosantiago.escuelaenlinea.com'  # Producción
dominio.tenant = escuela
dominio.is_primary = True
dominio.save()

print(f"✅ Escuela creada: {dominio.domain}")
```

---

## 🔧 Paso 5: Ajustar Modelos Existentes

### 5.1 No requieren cambios

Todos tus modelos actuales (`CustomUser`, `Profesor`, `Estudiante`, etc.) funcionarán automáticamente porque estarán en el schema del tenant.

### 5.2 Solo agregar en models.py

```python
# Al inicio del archivo
from django_tenants.utils import schema_context

# Los modelos existentes NO necesitan cambios
# Django-Tenants maneja el aislamiento automáticamente
```

---

## 🌐 Paso 6: Probar en Desarrollo

### 6.1 Configurar hosts locales

**Windows:** Editar `C:\Windows\System32\drivers\etc\hosts`

```
127.0.0.1 colegiosantiago.localhost
127.0.0.1 escuelalaesperanza.localhost
127.0.0.1 www.localhost
```

### 6.2 Iniciar servidor

```bash
python manage.py runserver
```

### 6.3 Acceder

- `http://www.localhost:8000/` → Sitio público
- `http://colegiosantiago.localhost:8000/` → Colegio Santiago
- `http://escuelalaesperanza.localhost:8000/` → Escuela La Esperanza

---

## 📊 Ventajas de Esta Solución

✅ **Aislamiento Total**: Imposible mezclar datos entre escuelas
✅ **Escalable**: Miles de escuelas en un servidor
✅ **Mantenimiento Simple**: Un código, múltiples escuelas
✅ **Backup Individual**: Backup por escuela si es necesario
✅ **Personalización**: Cada escuela puede tener su logo/colores
✅ **Migraciones Automáticas**: Una migración actualiza todos los tenants

---

## 🚨 Consideraciones Importantes

### Seguridad
- Cada escuela está **completamente aislada**
- Los usuarios solo ven datos de su escuela
- No hay forma de acceder a otra escuela

### Performance
- PostgreSQL maneja schemas muy eficientemente
- Menos recursos que bases de datos separadas
- Conexiones compartidas

### Limitaciones
- Requiere PostgreSQL (no SQLite)
- Búsquedas cross-tenant más complejas
- Reportes globales requieren código especial

---

## 📚 Recursos

- [django-tenants Documentation](https://django-tenants.readthedocs.io/)
- [PostgreSQL Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [Multi-tenancy Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/multi-tenancy)

---

## 🆘 Próximos Pasos

1. ✅ Decidir si usar esta arquitectura
2. ⚙️ Instalar PostgreSQL
3. 📦 Instalar django-tenants
4. 🔧 Configurar settings.py
5. 🏗️ Crear modelos Tenant
6. 🚀 Migrar base de datos
7. 🏫 Crear primera escuela de prueba
8. ✨ Personalizar por escuela (logo, colores)

---

**¿Necesitas ayuda implementando esto? ¡Avísame y te guío paso a paso!**
