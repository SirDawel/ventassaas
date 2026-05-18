# 🚀 GUÍA DE INICIO RÁPIDO - SISTEMA COMPLETO

## ✅ Estado Actual

- ✅ Fase 1: Base de Datos - Completada
- ✅ Fase 2: Admin & UI - Completada  
- ✅ Fase 3: Stripe - Completada
- ✅ Fase 4: Celery - Completada

---

## 📋 PASO 1: Verificar Django

### Iniciar el servidor:
```bash
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

### Probar acceso:
- Abrir navegador: http://prueba.localhost:8000/
- Login como admin
- Ir a: http://prueba.localhost:8000/suscripcion/

**✅ Si funciona, continuar al Paso 2**

---

## 📋 PASO 2: Instalar Redis

### Opción A: Redis Precompilado (Más Fácil)

1. **Ejecutar el instalador:**
   ```bash
   .\instalar_redis.bat
   ```
   Seleccionar opción **[1]**

2. **O descargar manualmente:**
   - Ir a: https://github.com/microsoftarchive/redis/releases
   - Descargar: `Redis-x64-3.2.100.msi`
   - Instalar (siguiente, siguiente, finalizar)
   - Redis se instala como servicio de Windows

3. **Verificar:**
   ```bash
   redis-cli ping
   # Debe responder: PONG
   ```

### Opción B: Memurai (Redis para Windows - Más Moderno)

1. Ir a: https://www.memurai.com/get-memurai
2. Descargar Memurai Developer (Gratis)
3. Instalar
4. Verificar: `memurai-cli ping`

### Opción C: Docker (Si tienes Docker Desktop)

```bash
docker run -d --name redis-escuela -p 6379:6379 redis:latest
```

---

## 📋 PASO 3: Configurar Variables de Entorno

### Crear archivo `.env` (si no existe):

```bash
# Copiar ejemplo
Copy-Item .env.example .env

# O crear manualmente
notepad .env
```

### Agregar estas líneas mínimas:

```bash
# REDIS/CELERY
CELERY_BROKER_URL=redis://localhost:6379/0

# STRIPE (Modo TEST)
STRIPE_PUBLIC_KEY=pk_test_tu_clave_aqui
STRIPE_SECRET_KEY=sk_test_tu_clave_aqui
STRIPE_WEBHOOK_SECRET=whsec_tu_secret_aqui
STRIPE_TEST_MODE=True

# EMAIL (Opcional para pruebas)
ADMIN_EMAIL=admin@tuescuela.com
```

**Nota:** Para probar sin Stripe, puedes dejar las claves vacías por ahora.

---

## 📋 PASO 4: Iniciar Celery

### Una vez Redis esté corriendo:

**Opción A: Script automático**
```bash
.\iniciar_celery_completo.bat
```

**Opción B: Manual**
```bash
.\.venv\Scripts\Activate.ps1
celery -A Escuela worker --beat --loglevel=info --pool=solo
```

**Deberías ver:**
```
[2026-05-09 22:00:00] celery@TU-PC ready.
[2026-05-09 22:00:00] - ** ---------- [config]
[2026-05-09 22:00:00] - ** ---------- .> app:         Escuela:0x...
[2026-05-09 22:00:00] - ** ---------- .> broker:      redis://localhost:6379/0
```

**✅ Si ves "ready", Celery está funcionando**

---

## 🧪 PASO 5: Probar el Sistema

### 5.1 Probar Celery (Tarea de Prueba)

```bash
# En otra terminal
.\.venv\Scripts\Activate.ps1
python manage.py shell
```

```python
# En el shell de Django
from escuelaweb.tasks import debug_celery

# Ejecutar tarea
result = debug_celery.delay()
print(f"Task ID: {result.id}")

# Ver resultado (esperar 2-3 segundos)
from django_celery_results.models import TaskResult
task = TaskResult.objects.latest('date_created')
print(f"Estado: {task.status}")
print(f"Resultado: {task.result}")
```

**✅ Si status="SUCCESS", Celery funciona correctamente**

### 5.2 Probar Verificación de Suscripciones

```python
# En el mismo shell
from escuelaweb.tasks import verificar_suscripciones_por_vencer

# Ejecutar verificación
verificar_suscripciones_por_vencer.delay()

# Ver resultado
TaskResult.objects.latest('date_created').result
# Debería mostrar cuántas suscripciones encontró
```

### 5.3 Probar Dashboard de Suscripciones

1. Abrir navegador: http://prueba.localhost:8000/suscripcion/
2. Deberías ver:
   - Tu plan actual (probablemente en TRIAL)
   - Días restantes de prueba
   - Uso de usuarios/estudiantes
   - Historial de pagos (vacío por ahora)

3. Click en "Ver Planes Disponibles"
4. Deberías ver los 4 planes:
   - Básico ($29/mes)
   - Estándar ($79/mes)
   - Profesional ($149/mes)
   - Empresarial ($299/mes)

---

## 🎨 PASO 6: Configurar Stripe (Para Pagos Reales)

### 6.1 Crear Cuenta de Stripe

1. Ir a: https://stripe.com
2. Registrarse (gratis)
3. Activar cuenta de prueba

### 6.2 Obtener Claves de API

1. Ir a: https://dashboard.stripe.com/apikeys
2. Copiar:
   - **Publishable key** (empieza con `pk_test_...`)
   - **Secret key** (empieza con `sk_test_...`)

3. Agregar a `.env`:
   ```bash
   STRIPE_PUBLIC_KEY=pk_test_51Ab...
   STRIPE_SECRET_KEY=sk_test_51Ab...
   ```

### 6.3 Configurar Webhook (Opcional para testing local)

1. Instalar Stripe CLI:
   ```bash
   # Descargar desde: https://stripe.com/docs/stripe-cli
   ```

2. Login:
   ```bash
   stripe login
   ```

3. Forwarding local:
   ```bash
   stripe listen --forward-to localhost:8000/webhooks/stripe/
   # Copiar el webhook secret (whsec_...)
   ```

4. Agregar a `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

---

## 💳 PASO 7: Probar Flujo de Pago

### 7.1 Desde la UI

1. Ir a: http://prueba.localhost:8000/suscripcion/planes/
2. Click en "Activar Ahora" en cualquier plan
3. Se abre página de checkout
4. Click en "Proceder al Pago Seguro"
5. Redirige a Stripe Checkout
6. Usar tarjeta de prueba: `4242 4242 4242 4242`
   - Fecha: Cualquier fecha futura
   - CVC: 123
   - ZIP: 12345
7. Completar pago
8. Redirige a página de éxito
9. Verificar en dashboard que suscripción está ACTIVA

### 7.2 Verificar en Base de Datos

```python
# En shell de Django
from escuelaweb.models import Suscripcion, HistorialPago

# Ver suscripción
sus = Suscripcion.objects.first()
print(f"Estado: {sus.estado}")
print(f"Plan: {sus.plan.nombre}")
print(f"Stripe ID: {sus.stripe_subscription_id}")

# Ver pagos
pagos = HistorialPago.objects.all()
for pago in pagos:
    print(f"{pago.numero_factura}: ${pago.monto} - {pago.estado}")
```

---

## 📊 PASO 8: Monitorear Tareas de Celery

### Ver Tareas Activas

```bash
celery -A Escuela inspect active
```

### Ver Tareas Programadas

```bash
celery -A Escuela inspect scheduled
```

### Instalar Flower (Monitor Web)

```bash
pip install flower
celery -A Escuela flower
```

Abrir: http://localhost:5555

---

## 🔍 PASO 9: Verificar Emails (Opcional)

### Configurar Gmail (para pruebas)

1. En tu Gmail, activar "Verificación en 2 pasos"
2. Generar "Contraseña de aplicación":
   - https://myaccount.google.com/apppasswords
   - Nombre: "Escuela Django"
   - Copiar contraseña generada

3. Agregar a `.env`:
   ```bash
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=tu_email@gmail.com
   EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
   DEFAULT_FROM_EMAIL=tu_email@gmail.com
   ```

### Probar Envío

```python
# En shell
from django.core.mail import send_mail

send_mail(
    'Test',
    'Mensaje de prueba',
    'tu_email@gmail.com',
    ['destinatario@example.com'],
)
# Debería devolver: 1
```

---

## ❓ Solución de Problemas

### Redis no se conecta

```bash
# Verificar servicio
services.msc  # Buscar "Redis"

# O iniciar manualmente
redis-server
```

### Celery no inicia

```bash
# Verificar Redis primero
redis-cli ping

# Verificar que .venv esté activado
.\.venv\Scripts\Activate.ps1

# Usar pool=solo en Windows
celery -A Escuela worker --pool=solo --loglevel=debug
```

### Django no encuentra Celery

```bash
# Verificar que las dependencias estén instaladas en .venv
& e:\Escuela_backup\Escuela\.venv\Scripts\python.exe -m pip list | Select-String celery
```

### Stripe no funciona

```bash
# Verificar claves en .env
# Asegurarse de que sean claves de TEST (pk_test_, sk_test_)
# Verificar que no tengan espacios ni comillas extra
```

---

## 📝 Resumen de Comandos

```bash
# 1. Iniciar Django
.\.venv\Scripts\Activate.ps1
python manage.py runserver

# 2. Iniciar Redis (si no está como servicio)
redis-server

# 3. Iniciar Celery
.\iniciar_celery_completo.bat

# 4. Abrir navegador
http://prueba.localhost:8000/suscripcion/
```

---

## 🎉 ¡Listo!

Tu sistema está completamente configurado con:
- ✅ Django multi-tenant
- ✅ Sistema de suscripciones
- ✅ Pagos con Stripe
- ✅ Tareas automáticas con Celery
- ✅ Emails transaccionales

**Para producción, revisar:**
- [FASE_3_STRIPE_COMPLETADA.md](FASE_3_STRIPE_COMPLETADA.md)
- [FASE_4_CELERY_COMPLETADA.md](FASE_4_CELERY_COMPLETADA.md)
- [GUIA_CELERY.md](GUIA_CELERY.md)

---

**Última actualización:** 09/05/2026  
**Versión:** 1.0 - Sistema Completo
