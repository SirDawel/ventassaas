# 🏢 Sistema de Ventas Multi-Tenant con Django

Sistema completo de ventas y facturación con arquitectura multi-tenant, gestión de clientes, vendedores, inventario, cotizaciones y reportes.

## 🌟 Características Principales

### 💼 Gestión de Ventas
- ✅ **Cotizaciones**: Crea cotizaciones para clientes antes de facturar
- ✅ **Facturación Completa**: Sistema robusto de facturación con múltiples métodos de pago
- ✅ **Gestión de Inventario**: Control de productos, categorías, stock y movimientos
- ✅ **Punto de Venta (POS)**: Interfaz rápida para ventas en mostrador

### 👥 Gestión de Clientes
- ✅ **Clientes Individuales**: Clientes regulares con límite de crédito
- ✅ **Clientes Corporativos**: Empresas con múltiples contactos y límites especiales
- ✅ **Crédito y Cobranza**: Control de cuentas por cobrar y límites de crédito
- ✅ **Descuentos Personalizados**: Descuentos por cliente o grupo

### 📊 Gestión de Vendedores
- ✅ **Comisiones Automáticas**: Cálculo automático de comisiones por venta
- ✅ **Metas Mensuales**: Seguimiento de metas y cumplimiento
- ✅ **Dashboard de Vendedor**: Panel personalizado para cada vendedor
- ✅ **Zonas de Venta**: Asignación territorial

### 📈 Reportes y Análisis
- ✅ **Reportes de Ventas**: Por período, vendedor, cliente, producto
- ✅ **Análisis de Comisiones**: Comisiones pendientes, pagadas, por vendedor
- ✅ **Cumplimiento de Metas**: Seguimiento y ranking de vendedores
- ✅ **Reportes de Inventario**: Stock, rotación, productos más vendidos
- ✅ **Cuentas por Cobrar**: Estado de pagos y clientes morosos

### 🏢 Multi-Tenancy
- ✅ **Empresas Independientes**: Cada empresa con su propia base de datos
- ✅ **Dominios Personalizados**: Subdominios para cada empresa
- ✅ **Datos Aislados**: Completa separación de datos entre empresas
- ✅ **Suscripciones**: Integración con Stripe para pagos recurrentes

### 🔒 Seguridad
- ✅ **Autenticación Robusta**: Sistema de login con bloqueo por intentos fallidos
- ✅ **Roles y Permisos**: Control granular de acceso por rol
- ✅ **Auditoría Completa**: Registro de todas las acciones importantes
- ✅ **Sesiones Seguras**: Control de sesiones por rol
- ✅ **2FA (Opcional)**: Autenticación de dos factores

## 🚀 Roles del Sistema

| Rol | Descripción | Permisos Principales |
|-----|-------------|---------------------|
| **Cliente** | Clientes que realizan compras | Ver sus facturas, realizar pagos |
| **Vendedor** | Vendedores con comisiones | Crear cotizaciones, ventas, ver comisiones |
| **Gerente** | Gerentes de área | Aprobar cotizaciones, ver reportes |
| **Supervisor** | Supervisores de vendedores | Supervisar vendedores, aprobar comisiones |
| **Secretaria** | Personal administrativo | Gestión de clientes, cobranza |
| **Almacenista** | Encargado de inventario | Gestión de inventario y stock |
| **Administrador** | Admin del sistema | Acceso completo al sistema |

## 📦 Instalación

### Requisitos Previos
- Python 3.8+
- PostgreSQL o SQLite
- Redis (para Celery)

### Instalación Rápida

```bash
# Clonar repositorio
git clone <tu-repo>
cd Ventas

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements_fase3_4.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tus configuraciones

# Ejecutar migraciones
python manage.py migrate

# Crear tenant público
python crear_tenant_publico.py

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### Migrar desde Sistema Escolar

Si estás migrando desde un sistema escolar existente:

```bash
# 1. CREAR BACKUP
copy db.sqlite3 db.sqlite3.backup

# 2. Aplicar nuevas migraciones
python manage.py makemigrations
python manage.py migrate

# 3. Ejecutar script de migración
python migrar_sistema_escolar_a_ventas.py

# 4. Verificar migración
python manage.py shell
>>> from escuelaweb.models import CustomUser
>>> print(CustomUser.objects.filter(rol='Cliente').count())
>>> print(CustomUser.objects.filter(rol='Vendedor').count())
```

Ver [GUIA_TRANSFORMACION_COMPLETA.md](GUIA_TRANSFORMACION_COMPLETA.md) para detalles.

## 🏗️ Estructura del Proyecto

```
Ventas/
├── Escuela/                    # Configuración del proyecto
│   ├── settings.py            # Configuración principal
│   ├── urls.py                # URLs principales
│   └── celery.py              # Configuración Celery
├── escuelaweb/                # Aplicación principal
│   ├── models.py              # Modelos de datos
│   ├── views.py               # Vistas principales
│   ├── views_cotizaciones.py  # Vistas de cotizaciones
│   ├── views_comisiones.py    # Vistas de comisiones
│   ├── views_pos.py           # Punto de venta
│   ├── forms.py               # Formularios
│   ├── admin.py               # Admin de Django
│   └── templates/             # Plantillas HTML
├── static/                    # Archivos estáticos
├── media/                     # Archivos subidos
├── requirements.txt           # Dependencias
└── manage.py                  # CLI de Django
```

## 📊 Modelos Principales

### Usuarios y Clientes
- **CustomUser**: Usuario del sistema (clientes, vendedores, etc.)
- **ClienteCorporativo**: Empresas/grupos de clientes

### Ventas
- **Cotizacion**: Cotizaciones para clientes
- **DetalleCotizacion**: Líneas de cotización
- **Factura**: Facturas de venta
- **DetalleFactura**: Líneas de factura
- **PagoFactura**: Pagos recibidos

### Vendedores
- **ComisionVendedor**: Comisiones por venta
- **MetaVendedor**: Metas mensuales

### Inventario
- **Articulo**: Productos y servicios
- **CategoriaArticulo**: Categorías de productos
- **MovimientoInventario**: Entradas/salidas de inventario

## 🎯 Guías de Uso

### Para Vendedores

```python
# Crear cotización
1. Ir a "Cotizaciones" → "Nueva Cotización"
2. Seleccionar cliente
3. Agregar productos
4. Guardar cotización
5. Cuando el cliente apruebe, convertir a factura

# Ver mis comisiones
1. Ir a "Mi Dashboard"
2. Ver "Mis Comisiones" del mes
3. Ver cumplimiento de meta
```

### Para Gerentes

```python
# Ver reportes de ventas
1. Ir a "Reportes" → "Ventas"
2. Seleccionar período
3. Filtrar por vendedor/producto/cliente
4. Exportar a Excel/PDF

# Aprobar comisiones
1. Ir a "Comisiones" → "Pendientes"
2. Revisar comisiones
3. Aprobar o rechazar
```

### Para Administradores

```python
# Configurar nuevo vendedor
1. Crear usuario con rol "Vendedor"
2. Asignar comisión (%)
3. Definir meta mensual
4. Asignar zona de venta

# Configurar cliente corporativo
1. Ir a "Clientes" → "Corporativos"
2. Crear nuevo cliente corporativo
3. Definir límite de crédito
4. Agregar contactos asociados
```

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# Django
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de Datos
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_password

# Stripe (Suscripciones)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0
```

### Configurar Celery (Tareas Asíncronas)

```bash
# Iniciar worker
celery -A Escuela worker -l info

# Iniciar beat (tareas programadas)
celery -A Escuela beat -l info

# O usar scripts batch (Windows)
iniciar_celery_completo.bat
```

## 📱 API (Opcional)

El sistema puede exponer API REST para integraciones:

```python
# Ejemplo: Consultar facturas
GET /api/facturas/
GET /api/facturas/{id}/
POST /api/facturas/
PUT /api/facturas/{id}/

# Ejemplo: Crear cotización
POST /api/cotizaciones/
{
    "cliente": 1,
    "vendedor": 2,
    "detalles": [
        {"articulo": 1, "cantidad": 5, "precio_unitario": 100}
    ]
}
```

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test escuelaweb

# Crear datos de prueba
python manage.py shell
>>> from escuelaweb.models import *
>>> # Crear vendedor, cliente, productos...
```

## 📚 Documentación Adicional

- [PLAN_TRANSFORMACION_VENTAS.md](PLAN_TRANSFORMACION_VENTAS.md) - Plan completo de transformación
- [GUIA_TRANSFORMACION_COMPLETA.md](GUIA_TRANSFORMACION_COMPLETA.md) - Guía paso a paso
- [GUIA_MULTITENANT.md](GUIA_MULTITENANT.md) - Configuración multi-tenant
- [GUIA_CELERY.md](GUIA_CELERY.md) - Tareas asíncronas
- [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) - Lista de seguridad

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es privado. Todos los derechos reservados.

## 💡 Soporte

Para soporte o preguntas:
- Email: soporte@tuempresa.com
- Docs: https://docs.tuempresa.com
- Issues: https://github.com/tuempresa/ventas/issues

## 🎉 Características Próximas

- [ ] App móvil para vendedores
- [ ] Integración con WhatsApp Business
- [ ] BI y Analytics avanzado
- [ ] Marketplace para clientes
- [ ] Integración con sistemas contables externos
- [ ] Firma electrónica de cotizaciones
- [ ] Geolocalización de vendedores

## 📊 Estadísticas del Proyecto

- **Modelos**: 30+ modelos de datos
- **Vistas**: 50+ vistas funcionales
- **Templates**: 40+ plantillas HTML
- **Líneas de Código**: 10,000+ líneas
- **Tests**: En desarrollo

---

**Versión**: 2.0.0 (Sistema de Ventas)  
**Última Actualización**: 2026-05-29  
**Desarrollado con**: Django 5.1+ y Python 3.8+
