# ==========================================
# GUÍA RÁPIDA: SISTEMA DE CELERY
# ==========================================

Este documento explica cómo usar el sistema de tareas asíncronas con Celery.

## 📋 Requisitos Previos

### 1. Instalar Redis

**Windows:**
- Descarga Redis desde: https://github.com/microsoftarchive/redis/releases
- Instala Redis-x64-3.2.100.msi
- Redis se ejecutará como servicio automáticamente

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Iniciar Redis
redis-server
```

### 2. Verificar que Redis está corriendo

```bash
redis-cli ping
# Debe responder: PONG
```

## 🚀 Iniciar Celery

### Opción 1: Worker de Celery (procesa tareas)

```bash
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Iniciar worker
celery -A Escuela worker --loglevel=info --pool=solo
```

**Nota para Windows:** Usa `--pool=solo` porque Windows no soporta el pool por defecto.

### Opción 2: Celery Beat (tareas programadas)

```bash
# En otra terminal, con el entorno virtual activado
celery -A Escuela beat --loglevel=info
```

### Opción 3: Ambos a la vez

```bash
# Inicia worker y beat juntos
celery -A Escuela worker --beat --loglevel=info --pool=solo
```

## 📊 Monitorear Celery

### Flower (Interfaz Web)

```bash
# Instalar Flower
pip install flower

# Iniciar Flower
celery -A Escuela flower
```

Luego abre: http://localhost:5555

## ⏰ Tareas Programadas

El sistema incluye las siguientes tareas automáticas:

| Tarea | Horario | Descripción |
|-------|---------|-------------|
| `verificar_suscripciones_por_vencer` | Todos los días a las 8:00 AM | Verifica suscripciones próximas a vencer |
| `enviar_recordatorios_pago` | Todos los días a las 9:00 AM | Envía recordatorios de pago |
| `actualizar_suscripciones_vencidas` | Cada hora | Actualiza estados de suscripciones vencidas |
| `generar_reporte_mensual` | Primer día del mes a las 10:00 AM | Genera reporte mensual |
| `verificar_pagos_pendientes` | Cada 6 horas | Verifica pagos pendientes en Stripe |

## 🧪 Probar Tareas

### Desde Python Shell

```python
# Abrir shell de Django
python manage.py shell

# Importar tareas
from escuelaweb.tasks import debug_celery, verificar_suscripciones_por_vencer

# Ejecutar tarea inmediatamente (síncrono)
debug_celery()

# Enviar tarea a Celery (asíncrono)
debug_celery.delay()

# Verificar suscripciones
verificar_suscripciones_por_vencer.delay()
```

### Desde código

```python
from escuelaweb.tasks import enviar_recordatorio_pago

# Enviar recordatorio para una suscripción específica
enviar_recordatorio_pago.delay(suscripcion_id=1)
```

## 🔧 Configuración

### Variables de Entorno (.env)

```bash
# Redis (Broker de Celery)
CELERY_BROKER_URL=redis://localhost:6379/0

# Email para reportes
ADMIN_EMAIL=admin@tuescuela.com
```

### Configuración en settings.py

Ya está configurado en `Escuela/settings.py`:
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND
- CELERY_TIMEZONE
- CELERY_BEAT_SCHEDULER

## 📝 Crear Nueva Tarea

### 1. Agregar tarea en `escuelaweb/tasks.py`

```python
from celery import shared_task

@shared_task
def mi_nueva_tarea(parametro):
    """Descripción de mi tarea"""
    # Tu código aquí
    return "Resultado"
```

### 2. Programar tarea (opcional)

En `Escuela/celery.py`, agrega a `beat_schedule`:

```python
'mi-tarea-diaria': {
    'task': 'escuelaweb.tasks.mi_nueva_tarea',
    'schedule': crontab(hour=10, minute=30),  # 10:30 AM
    'args': ('mi_parametro',)
},
```

### 3. Ejecutar tarea

```python
from escuelaweb.tasks import mi_nueva_tarea

# Asíncrono
mi_nueva_tarea.delay('valor')

# Síncrono (para testing)
mi_nueva_tarea('valor')
```

## 🐛 Solución de Problemas

### Redis no se conecta

```bash
# Verificar que Redis está corriendo
redis-cli ping

# En Windows, iniciar Redis manualmente
redis-server
```

### Worker no inicia en Windows

Usa `--pool=solo`:
```bash
celery -A Escuela worker --loglevel=info --pool=solo
```

### Tareas no se ejecutan

1. Verifica que el worker esté corriendo
2. Verifica que Beat esté corriendo (para tareas programadas)
3. Revisa los logs con `--loglevel=debug`

### Ver resultados de tareas

```python
from escuelaweb.models import TaskResult

# Ver todas las tareas
TaskResult.objects.all()

# Ver tarea específica
task = TaskResult.objects.get(task_id='tu-task-id')
print(task.result)
```

## 🎯 Casos de Uso

### Enviar emails masivos

```python
from escuelaweb.tasks import enviar_recordatorio_pago

# Enviar a todas las suscripciones próximas a vencer
suscripciones = Suscripcion.objects.filter(
    estado='ACTIVA',
    fecha_proximo_pago__lte=timezone.now() + timedelta(days=3)
)

for suscripcion in suscripciones:
    enviar_recordatorio_pago.delay(suscripcion.id)
```

### Generar reportes

```python
from escuelaweb.tasks import generar_reporte_mensual_suscripciones

# Generar reporte ahora
generar_reporte_mensual_suscripciones.delay()
```

### Sincronizar con Stripe

```python
from escuelaweb.tasks import verificar_pagos_pendientes_stripe

# Verificar todos los pagos pendientes
verificar_pagos_pendientes_stripe.delay()
```

## 📚 Recursos

- **Documentación Celery:** https://docs.celeryproject.org/
- **Crontab Guru:** https://crontab.guru/ (para horarios)
- **Redis:** https://redis.io/documentation

## ⚡ Comandos Rápidos

```bash
# Iniciar todo en desarrollo
celery -A Escuela worker --beat --loglevel=info --pool=solo

# Ver tareas activas
celery -A Escuela inspect active

# Ver tareas programadas
celery -A Escuela inspect scheduled

# Ver workers conectados
celery -A Escuela inspect active_queues

# Purgar todas las tareas
celery -A Escuela purge
```

## 🔐 Producción

Para producción, usa un gestor de procesos como **Supervisor** (Linux) o **NSSM** (Windows):

### Linux (Supervisor)

```bash
# Instalar supervisor
sudo apt-get install supervisor

# Crear configuración
sudo nano /etc/supervisor/conf.d/celery.conf
```

### Windows (NSSM)

```bash
# Descargar NSSM
# Instalar como servicio
nssm install CeleryWorker "C:\path\to\.venv\Scripts\celery.exe" "-A Escuela worker --loglevel=info --pool=solo"
nssm start CeleryWorker
```

---

**Última actualización:** 09/05/2026  
**Versión:** 1.0 - Fase 4 Implementada
