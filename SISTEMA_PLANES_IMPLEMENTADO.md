# 💵 SISTEMA DE PLANES Y LÍMITES - IMPLEMENTADO

## ✅ Cambios Realizados

### 1. Modelo Client Actualizado
**Archivo:** `ventasweb/tenant_models.py`

**Nuevos campos:**
- `max_facturas_mes` - Límite de facturas por mes según plan
- `max_sucursales` - Límite de sucursales
- `reportes_avanzados` - Habilita reportes avanzados (boolean)
- `facturacion_electronica` - Habilita facturación electrónica (boolean)
- `facturas_mes_actual` - Contador de facturas del mes actual
- `ultimo_reset_facturas` - Control de reset mensual automático
- `precio_mensual` - Precio del plan en USD
- `proximo_pago` - Fecha del próximo pago programado

**Nuevos métodos:**
- `configurar_limites_plan()` - Configura límites automáticamente según plan
- `puede_crear_factura()` - Verifica si puede crear más facturas
- `incrementar_facturas()` - Incrementa contador de facturas
- `contar_facturas_mes()` - Cuenta facturas del mes (auto-reset mensual)
- `get_info_plan()` - Retorna info completa del plan
- `get_porcentaje_uso_usuarios()` - Porcentaje de uso de usuarios
- `get_porcentaje_uso_facturas()` - Porcentaje de uso de facturas

---

## 💰 Planes Configurados (Súper Económicos)

### Plan GRATIS - $0/mes
- ✅ 30 días de prueba
- 👤 1 usuario
- 📄 50 facturas/mes
- 🏪 1 sucursal
- ❌ Sin reportes avanzados
- ❌ Sin facturación electrónica

### Plan BÁSICO - $5/mes 💚
- 👤 2 usuarios
- 📄 200 facturas/mes
- 🏪 1 sucursal
- ❌ Sin reportes avanzados
- ✅ Facturación electrónica

### Plan PLUS - $12/mes ⭐
- 👤 5 usuarios
- 📄 1,000 facturas/mes
- 🏪 2 sucursales
- ✅ Reportes avanzados
- ✅ Facturación electrónica

### Plan PRO - $25/mes 🚀
- 👤 15 usuarios
- 📄 ∞ Facturas ilimitadas
- 🏪 5 sucursales
- ✅ Reportes avanzados
- ✅ Facturación electrónica
- ✅ Soporte prioritario

---

## 🛡️ Middlewares de Límites

### 2. PlanLimitsMiddleware
**Archivo:** `ventasweb/middleware/plan_limits.py`

**Funcionalidad:**
- ✅ Bloquea creación de facturas si se alcanzó el límite
- ✅ Bloquea creación de usuarios si se alcanzó el límite
- ✅ Verifica si el plan está activo/expirado
- ✅ Responde con JSON para AJAX o HTML para navegación normal
- ✅ Muestra páginas de error amigables

### 3. BillingWarningMiddleware
**Archivo:** `ventasweb/middleware/plan_limits.py`

**Funcionalidad:**
- ⚠️ Alerta cuando se usa >80% de usuarios
- ⚠️ Alerta cuando se usa >80% de facturas del mes
- ⚠️ Alerta cuando faltan <7 días para vencimiento
- ✅ Usa el sistema de mensajes de Django

---

## 🎨 Templates de Error

### 4. Plantillas creadas:
- `templates/errors/plan_expirado.html` - Cuando el plan expiró
- `templates/errors/limite_facturas.html` - Límite de facturas alcanzado
- `templates/errors/limite_usuarios.html` - Límite de usuarios alcanzado

**Características:**
- ✅ Diseño moderno y responsivo
- ✅ Iconos Font Awesome
- ✅ Progreso visual del uso
- ✅ Botones para actualizar plan
- ✅ Información clara del problema

---

## 📋 PASOS PARA ACTIVAR EL SISTEMA

### Paso 1: Aplicar Migraciones

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Generar y aplicar migraciones
python aplicar_migracion_planes.py
```

### Paso 2: Actualizar Settings.py

Agregar los middlewares en `VentasSys/settings.py`:

```python
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # NUEVOS MIDDLEWARES DE PLANES
    'ventasweb.middleware.plan_limits.PlanLimitsMiddleware',        # ← Agregar
    'ventasweb.middleware.plan_limits.BillingWarningMiddleware',    # ← Agregar
]
```

### Paso 3: Actualizar Tenants Existentes (Opcional)

```powershell
# Script para actualizar tenants existentes con los nuevos campos
python manage.py shell
```

```python
from ventasweb.tenant_models import Client

# Actualizar todos los tenants
for tenant in Client.objects.all():
    # Configurar límites según su plan actual
    tenant.configurar_limites_plan()
    tenant.save()
    print(f"✅ {tenant.nombre} actualizado")
```

### Paso 4: Actualizar Código de Facturación

Cuando se crea una factura, incrementar el contador:

```python
# En tu vista/función de crear factura
from django_tenants.utils import tenant_context

def crear_factura(request):
    # ... código de creación de factura ...
    
    # Después de guardar la factura
    factura.save()
    
    # Incrementar contador del tenant
    request.tenant.incrementar_facturas()
    
    # ... resto del código ...
```

---

## 🧪 Probar el Sistema

### Crear tenant de prueba con plan básico:

```powershell
python manage.py shell
```

```python
from ventasweb.tenant_models import Client, Domain
from datetime import timedelta
from django.utils import timezone

# Crear tenant con plan básico
tenant = Client.objects.create(
    schema_name='tienda_test',
    nombre='Tienda de Prueba',
    nombre_corto='tienda_test',
    email_contacto='test@test.com',
    plan='basico',  # Plan básico $5/mes
    activo=True
)

# Asociar dominio
Domain.objects.create(
    domain='tienda-test.localhost',
    tenant=tenant,
    is_primary=True
)

print(f"✅ Tenant creado: {tenant.nombre}")
print(f"📋 Plan: {tenant.get_plan_display()}")
print(f"💰 Precio: ${tenant.precio_mensual}/mes")
print(f"👤 Usuarios: 0/{tenant.max_usuarios}")
print(f"📄 Facturas: 0/{tenant.max_facturas_mes}")
```

---

## 📊 Cálculo de Rentabilidad

### Costos AWS mensual: ~$40
### Ganancia por cliente según plan:

| Clientes | Plan Mix | Ingreso/Mes | Ganancia |
|----------|----------|-------------|----------|
| 10 | 100% Básico | $50 | $10 |
| 20 | 100% Básico | $100 | $60 |
| 30 | 70% Básico + 30% Plus | $141 | $101 |
| 50 | 50% Básico + 40% Plus + 10% Pro | $255 | $215 |
| 100 | 40% Básico + 40% Plus + 20% Pro | $480 | $440 |

**Break-even:** 8-9 clientes en plan básico

---

## 🚀 Próximos Pasos Recomendados

1. **✅ Sistema de Pagos (Stripe)**
   - Integrar Stripe para cobros automáticos
   - Webhooks para actualizar estado de suscripción
   - Portal de cliente para gestionar pagos

2. **📊 Dashboard de Billing**
   - Vista para el admin con métricas
   - Ingresos mensuales recurrentes (MRR)
   - Churn rate, upgrades, downgrades

3. **📧 Sistema de Notificaciones**
   - Email cuando se acerca al límite
   - Email cuando faltan 7 días para vencimiento
   - Email de renovación exitosa

4. **🎁 Sistema de Cupones**
   - Descuentos para promociones
   - Períodos de prueba extendidos
   - Referidos

---

## 🔧 Comandos Útiles

```powershell
# Ver info de un tenant
python manage.py shell
from ventasweb.tenant_models import Client
tenant = Client.objects.get(schema_name='boutique')
print(tenant.get_info_plan())

# Cambiar plan de un tenant
tenant.plan = 'plus'
tenant.configurar_limites_plan()
tenant.save()

# Resetear contador de facturas manualmente
tenant.facturas_mes_actual = 0
tenant.save()
```

---

## ⚠️ Notas Importantes

1. El contador de facturas se resetea automáticamente cada mes
2. Los límites se aplican ANTES de crear facturas/usuarios
3. Los planes pueden cambiarse en cualquier momento
4. Los precios están en USD pero puedes cambiar a tu moneda local
5. El sistema de límites NO afecta al tenant 'public'

---

## 📞 Soporte

Si tienes dudas o necesitas ayuda:
- Revisa los logs: `python manage.py runserver` (modo verbose)
- Verifica middlewares en settings.py
- Prueba las plantillas de error accediendo directamente

¡El sistema está listo para generar ingresos! 🚀💰
