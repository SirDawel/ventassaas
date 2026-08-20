# 🚀 Instalar Servicios de Celery en Systemd

## 📋 Problema

Al intentar reiniciar Celery, ves estos errores:

```
Failed to restart celery-worker.service: Unit celery-worker.service not found.
Failed to restart celery-beat.service: Unit celery-beat.service not found.
```

**Causa:** Los servicios de Celery no están configurados en systemd.

---

## ⚡ SOLUCIÓN RÁPIDA (2 minutos)

### Método 1: Script Automático (Recomendado)

```bash
cd /var/www/ventas
git pull
sudo bash instalar_celery_services.sh
```

**✅ Listo.** El script crea todo automáticamente.

---

### Método 2: Manual (si el script falla)

#### 1. Crear directorios necesarios

```bash
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown -R ubuntu:ubuntu /var/log/celery
sudo chown -R ubuntu:ubuntu /var/run/celery
```

#### 2. Copiar archivos de servicio

```bash
cd /var/www/ventas
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/
```

#### 3. Recargar systemd y habilitar servicios

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker.service
sudo systemctl enable celery-beat.service
```

#### 4. Iniciar servicios

```bash
sudo systemctl start celery-worker
sudo systemctl start celery-beat
```

#### 5. Verificar estado

```bash
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

**✅ Resultado esperado:** Ambos deben mostrar `Active: active (running)`

---

## 🔄 Comandos Útiles

### Ver estado de servicios

```bash
sudo systemctl status celery-worker
sudo systemctl status celery-beat
sudo systemctl status gunicorn
```

### Reiniciar servicios

```bash
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
sudo systemctl restart gunicorn
```

### Ver logs en tiempo real

```bash
# Logs de Celery Worker
sudo journalctl -u celery-worker -f

# Logs de Celery Beat
sudo journalctl -u celery-beat -f

# Logs de Gunicorn
sudo journalctl -u gunicorn -f
```

### Ver logs archivados

```bash
# Últimas 100 líneas del worker
sudo journalctl -u celery-worker -n 100

# Últimas 100 líneas del beat
sudo journalctl -u celery-beat -n 100
```

### Detener servicios

```bash
sudo systemctl stop celery-worker
sudo systemctl stop celery-beat
```

### Deshabilitar inicio automático (si no usas Celery)

```bash
sudo systemctl disable celery-worker
sudo systemctl disable celery-beat
```

---

## 📂 Ubicación de Archivos

### Archivos de servicio systemd
- `/etc/systemd/system/celery-worker.service`
- `/etc/systemd/system/celery-beat.service`

### Logs
- `/var/log/celery/worker.log`
- `/var/log/celery/beat.log`

### PIDs
- `/var/run/celery/worker.pid`
- `/var/run/celery/beat.pid`

### Schedule de tareas periódicas
- `/var/www/ventas/celerybeat-schedule`

---

## 🧪 Probar que Celery Funciona

### Verificar que Redis está corriendo

```bash
redis-cli ping
```

**✅ Resultado esperado:** `PONG`

### Verificar tareas en cola

```bash
cd /var/www/ventas
source .venv/bin/activate
python manage.py shell
```

```python
from celery import current_app

# Ver tareas registradas
print(current_app.tasks.keys())

# Enviar tarea de prueba
from ventasweb.tasks import test_task
result = test_task.delay()
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")

exit()
```

### Ver workers activos

```bash
cd /var/www/ventas
source .venv/bin/activate
celery -A VentasSys inspect active
```

---

## 🚨 Solución de Problemas

### Error: "celery-worker failed to start"

Ver el error específico:

```bash
sudo journalctl -u celery-worker -n 50
```

Errores comunes:

**1. Redis no está corriendo**
```bash
sudo systemctl status redis
sudo systemctl start redis
```

**2. Permisos incorrectos**
```bash
sudo chown -R ubuntu:ubuntu /var/log/celery
sudo chown -R ubuntu:ubuntu /var/run/celery
sudo chown -R ubuntu:ubuntu /var/www/ventas
```

**3. Entorno virtual corrupto**
```bash
cd /var/www/ventas
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**4. Puerto ya en uso**
```bash
# Ver procesos de Celery
ps aux | grep celery

# Matar procesos huérfanos
pkill -f 'celery worker'
pkill -f 'celery beat'

# Reiniciar servicio
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

### Ver configuración actual del servicio

```bash
sudo systemctl cat celery-worker
sudo systemctl cat celery-beat
```

### Recargar después de editar archivos .service

```bash
sudo systemctl daemon-reload
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

---

## 📊 Monitoreo

### Ver estadísticas de Celery

```bash
cd /var/www/ventas
source .venv/bin/activate
celery -A VentasSys inspect stats
```

### Ver tareas programadas

```bash
celery -A VentasSys inspect scheduled
```

### Ver tareas activas

```bash
celery -A VentasSys inspect active
```

---

## ✅ Verificación Final

```bash
# Todos los servicios deben estar activos
sudo systemctl status gunicorn celery-worker celery-beat --no-pager

# Debe mostrar:
# ● gunicorn.service - Gunicorn daemon
#    Active: active (running)
# ● celery-worker.service - Celery Worker Service
#    Active: active (running)
# ● celery-beat.service - Celery Beat Scheduler Service
#    Active: active (running)
```

**🎉 Si todos muestran "active (running)", tu sistema está completamente operativo.**

---

## 🔄 Actualizar después de cambios en el código

```bash
cd /var/www/ventas
git pull
source .venv/bin/activate
python manage.py migrate_schemas
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn celery-worker celery-beat
```

---

## 📚 Documentación Relacionada

- [GUIA_CELERY.md](GUIA_CELERY.md) - Guía completa de Celery
- [SOLUCION_RAPIDA.md](SOLUCION_RAPIDA.md) - Solución de errores comunes
- [CONFIGURAR_GMAIL_SMTP.md](CONFIGURAR_GMAIL_SMTP.md) - Configurar envío de emails
