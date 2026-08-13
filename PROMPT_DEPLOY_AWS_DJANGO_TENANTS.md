# PROMPT PARA IA: Despliegue Django Multitenant en AWS EC2

## CONTEXTO DEL PROYECTO

Tengo un sistema de ventas desarrollado en **Django 5.1** con **django-tenants 3.12** (sistema multitenant) que necesito desplegar en producción en AWS. Actualmente funciona en desarrollo local en Windows con PostgreSQL.

## STACK TECNOLÓGICO OBJETIVO

- **Servidor**: Ubuntu 24.04 LTS (Noble Numbat) en AWS EC2
- **Web Server**: Nginx (reverse proxy)
- **App Server**: Gunicorn (WSGI server para Django)
- **Base de Datos**: PostgreSQL 16+ (con soporte para schemas - requerido para django-tenants)
- **Python**: 3.13+
- **Framework**: Django 5.1.x (LTS)
- **Multitenant**: django-tenants 3.12+ (cada cliente tiene su propio schema en PostgreSQL)
- **Broker de Tareas**: Redis (para Celery)
- **Task Queue**: Celery + Celery Beat (tareas programadas)
- **SSL/TLS**: Let's Encrypt con Certbot
- **Process Manager**: systemd (para Gunicorn, Celery, Celery Beat)

## CONFIGURACIÓN ACTUAL DEL PROYECTO

### Estructura del proyecto:
```
Ventas/
├── VentasSys/          # Configuración principal Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── ventasweb/          # App principal
│   ├── models.py       # CustomUser, Articulo, Factura, etc.
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── manage.py
├── requirements.txt
├── requirements_fase3_4.txt  # Redis, Celery, Stripe
├── .env                      # Variables de entorno (no en git)
└── staticfiles/              # Archivos estáticos compilados
```

### Base de datos actual:
- **Host local**: 127.0.0.1:5434
- **Base de datos**: ventassistemdb
- **Schemas**: public (tenant público) + schemas individuales por tenant
- **Dominios locales**: *.localhost:8000 (ej: picapolloeka.localhost:8000)

### Dependencias principales:
```txt
Django==5.1.4
django-tenants==3.12.0
psycopg[binary]==3.3.4
psycopg2-binary==2.9.12
gunicorn==23.0.0
celery==5.6.3
redis==7.4.0
django-celery-beat==2.9.0
django-celery-results==2.6.0
stripe==15.1.0
python-dotenv==1.0.1
Pillow==11.0.0
whitenoise==6.12.0
```

## REQUERIMIENTOS DEL DEPLOYMENT

### 1. INSTANCIA EC2
- **Tipo**: t3.medium o superior (2 vCPU, 4 GB RAM mínimo)
- **SO**: Ubuntu 24.04 LTS (Noble Numbat)
- **Storage**: 30 GB SSD mínimo (GP3 recomendado)
- **Security Groups**:
  - Puerto 22 (SSH) - Solo tu IP
  - Puerto 80 (HTTP)
  - Puerto 443 (HTTPS)
  - Puerto 5432 (PostgreSQL) - Solo dentro de VPC si usas RDS

### 2. CONFIGURACIÓN DE DOMINIOS
El sistema multitenant requiere subdominios wildcard:
- **Dominio principal**: ventas.tudominio.com
- **Tenant público**: ventas.tudominio.com o public.ventas.tudominio.com
- **Tenants clientes**: [cliente].ventas.tudominio.com
  - Ejemplo: picapolloeka.ventas.tudominio.com
  - Ejemplo: restaurantepepito.ventas.tudominio.com

### 3. BASE DE DATOS
Opciones:
- **Opción A**: PostgreSQL 16 en la misma instancia EC2 (desarrollo/staging)
- **Opción B**: AWS RDS PostgreSQL 16 (producción recomendada)

Configuración requerida:
```sql
-- Extensión para django-tenants
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear base de datos
CREATE DATABASE ventasdb;

-- Usuario de aplicación
CREATE USER ventasapp WITH PASSWORD 'contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE ventasdb TO ventasapp;
```

### 4. VARIABLES DE ENTORNO (.env en producción)
```env
# Django
SECRET_KEY=tu_secret_key_super_segura_aqui
DEBUG=False
ALLOWED_HOSTS=.ventas.tudominio.com,ventas.tudominio.com
CSRF_TRUSTED_ORIGINS=https://*.ventas.tudominio.com,https://ventas.tudominio.com

# Base de datos
DB_NAME=ventasdb
DB_USER=ventasapp
DB_PASSWORD=contraseña_segura
DB_HOST=localhost  # o endpoint de RDS
DB_PORT=5432

# Email (para notificaciones)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

# Stripe (pagos)
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# Seguridad
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## INSTRUCCIONES PARA LA IA

Por favor, proporcióname una guía paso a paso COMPLETA para:

### FASE 1: Preparación del Servidor
1. Actualizar Ubuntu 24.04 LTS
2. Instalar dependencias del sistema (Python 3.13, pip, virtualenv, git)
3. Configurar firewall (UFW)
4. Crear usuario de aplicación (no usar root)
5. Configurar SSH key authentication

### FASE 2: Instalación de PostgreSQL
1. Instalar PostgreSQL 16+
2. Configurar para aceptar conexiones locales
3. Crear base de datos y usuario
4. Configurar autenticación (pg_hba.conf)
5. Habilitar extensiones necesarias
6. Configurar backups automáticos

### FASE 3: Instalación de Redis
1. Instalar Redis server
2. Configurar Redis como servicio systemd
3. Securizar Redis (requirepass)
4. Verificar funcionamiento

### FASE 4: Configuración de la Aplicación Django
1. Clonar repositorio o subir código
2. Crear virtualenv Python
3. Instalar dependencias (requirements.txt)
4. Configurar variables de entorno (.env)
5. Configurar settings.py para producción:
   - DEBUG = False
   - ALLOWED_HOSTS con wildcard para subdominios
   - DATABASES con PostgreSQL
   - STATIC_ROOT y MEDIA_ROOT
   - django-tenants TENANT_MODEL y TENANT_DOMAIN_MODEL
6. Ejecutar migraciones:
   ```bash
   python manage.py migrate_schemas --shared
   python manage.py migrate_schemas
   ```
7. Crear tenant público
8. Collectstatic
9. Crear superusuario

### FASE 5: Configuración de Gunicorn
1. Instalar Gunicorn en virtualenv
2. Crear archivo de configuración gunicorn.conf.py:
   - Workers según CPU (workers = 2 * CPU + 1)
   - Bind a socket Unix o puerto local
   - Timeout adecuado
   - Access log y error log
3. Crear servicio systemd para Gunicorn:
   - WorkingDirectory
   - Environment variables
   - ExecStart con virtualenv
   - User y Group
   - Restart=always
4. Habilitar y arrancar servicio

### FASE 6: Configuración de Nginx
1. Instalar Nginx
2. Crear configuración para el sitio:
   - Server name con wildcard (*.ventas.tudominio.com)
   - Proxy pass a Gunicorn
   - Configuración de archivos estáticos (/static/)
   - Configuración de archivos media (/media/)
   - Client max body size (para uploads)
   - Proxy headers (X-Forwarded-For, Host, etc.)
   - Gzip compression
3. Crear symlink en sites-enabled
4. Verificar configuración (nginx -t)
5. Recargar Nginx

### FASE 7: Configuración de SSL/TLS
1. Instalar Certbot para Nginx
2. Obtener certificado wildcard con DNS challenge:
   ```bash
   certbot certonly --manual --preferred-challenges dns \
     -d ventas.tudominio.com -d *.ventas.tudominio.com
   ```
3. Configurar renovación automática
4. Actualizar configuración Nginx para HTTPS
5. Redirigir HTTP a HTTPS

### FASE 8: Configuración de Celery
1. Crear servicio systemd para Celery Worker:
   - ExecStart: celery -A VentasSys worker
   - Concurrency según CPU
2. Crear servicio systemd para Celery Beat:
   - ExecStart: celery -A VentasSys beat
   - Scheduler: django-celery-beat
3. Habilitar y arrancar ambos servicios
4. Verificar logs

### FASE 9: DNS y Dominios
1. Configurar DNS en tu proveedor:
   - Registro A: ventas.tudominio.com → IP de EC2
   - Registro A: *.ventas.tudominio.com → IP de EC2
2. Configurar Elastic IP en AWS (IP estática)
3. Verificar propagación DNS

### FASE 10: Seguridad Adicional
1. Configurar fail2ban (protección SSH)
2. Configurar logrotate para logs de aplicación
3. Limitar acceso PostgreSQL solo a localhost
4. Configurar backups automáticos (base de datos y media)
5. Monitoreo básico (opcional: CloudWatch, Sentry)

### FASE 11: Testing Multitenant
1. Crear tenant de prueba desde shell Django
2. Verificar acceso por subdominio
3. Probar separación de datos entre tenants
4. Verificar funcionamiento de Celery tasks
5. Probar flujo completo de facturación

## CONSIDERACIONES ESPECIALES DJANGO-TENANTS

1. **Migraciones**: Siempre usar `migrate_schemas` en vez de `migrate`
   ```bash
   python manage.py migrate_schemas --shared  # Solo schema público
   python manage.py migrate_schemas           # Todos los schemas
   ```

2. **Creación de tenants**: Desde Django shell
   ```python
   from django_tenants.utils import schema_context
   from ventasweb.models import Tenant, Domain
   
   tenant = Tenant(schema_name='cliente1', name='Cliente 1')
   tenant.save()
   
   domain = Domain(domain='cliente1.ventas.tudominio.com', tenant=tenant, is_primary=True)
   domain.save()
   ```

3. **Wildcard subdomain**: Nginx debe capturar todos los subdominios
   ```nginx
   server_name ventas.tudominio.com *.ventas.tudominio.com;
   ```

4. **ALLOWED_HOSTS**: Debe incluir wildcard
   ```python
   ALLOWED_HOSTS = ['.ventas.tudominio.com', 'ventas.tudominio.com']
   ```

## FORMATO DE RESPUESTA ESPERADO

Por favor proporciona:
1. **Comandos exactos** para cada paso (copy-paste ready)
2. **Archivos de configuración completos** (Nginx, systemd, gunicorn)
3. **Explicación breve** de qué hace cada comando
4. **Troubleshooting común** para cada fase
5. **Checklist de verificación** al final de cada fase
6. **Comandos de diagnóstico** (logs, status de servicios)

## INFORMACIÓN ADICIONAL

- El proyecto usa **Celery** para tareas en segundo plano (procesamiento de pagos, notificaciones)
- Integración con **Stripe** para pagos recurrentes (suscripciones)
- Sistema de roles: Administrador, Gerente, Vendedor, Secretaria, Cliente
- Gestión de inventario, facturación, punto de venta (POS)
- Sistema de mora y vencimientos automáticos

## OBJETIVO FINAL

Un sistema Django multitenant completamente funcional en producción con:
- ✅ Alta disponibilidad
- ✅ SSL/TLS configurado
- ✅ Separación de datos por tenant (schema isolation)
- ✅ Backups automáticos
- ✅ Logs centralizados
- ✅ Servicios auto-restart
- ✅ Performance optimizado
- ✅ Seguridad hardened

---

**IMPORTANTE**: Este es un sistema en producción que manejará datos sensibles (facturas, pagos, clientes). La seguridad y estabilidad son críticas.

---

## JUSTIFICACIÓN TÉCNICA

### ¿Por qué Nginx en vez de Apache para Django?

1. **Performance**: Nginx es más ligero y eficiente manejando conexiones simultáneas (event-driven vs process-driven)
2. **Reverse Proxy**: Nginx es excelente como reverse proxy para Gunicorn (estándar de la industria Django)
3. **Archivos Estáticos**: Nginx sirve archivos estáticos/media más rápido que Apache con menor uso de recursos
4. **Memoria**: Nginx consume menos RAM (~10MB vs ~50-100MB de Apache por worker)
5. **Configuración**: Más simple y clara para aplicaciones Django modernas
6. **Websockets**: Mejor soporte nativo para WebSockets (útil para futuras features en tiempo real)
7. **SSL/TLS**: Mejor rendimiento en terminación SSL/TLS

### Stack Completo (LEPP):
- **L**inux (Ubuntu 24.04 LTS - Noble Numbat)
- **E**ngine-X (Nginx 1.24+) 
- **P**ostgreSQL 16+ (con schemas para multitenant)
- **P**ython 3.13+ con Django 5.1 + Gunicorn

### Mejoras en las versiones actualizadas:

**Django 5.1 vs 4.2:**
- Mejor rendimiento en queries ORM
- Soporte mejorado para PostgreSQL 16
- Nuevas features de seguridad
- Async views más estables
- Field groups en formularios
- Mejor manejo de JSON fields

**django-tenants 3.12 vs 3.6:**
- Compatibilidad total con Django 5.x
- Mejor manejo de migraciones por schema
- Performance mejorado en tenant switching
- Mejor soporte para conexiones async
- Fixes importantes de estabilidad

**Python 3.13 vs 3.11:**
- JIT compiler experimental (mejor performance)
- Mejor manejo de memoria
- f-strings más rápidos
- asyncio mejorado
- Mejor tipado estático

**PostgreSQL 16 vs 14:**
- Performance mejorado en queries paralelos
- Mejor manejo de JSON/JSONB
- Logical replication mejorado
- Monitoring más detallado
- Mejoras en vacuum y autovacuum

**psycopg 3.x vs psycopg2:**
- API moderna y más pythónica
- Soporte nativo para async/await
- Mejor performance
- Mejor manejo de tipos PostgreSQL
- Pipeline mode para queries en batch
