# 🔧 GUÍA DE DIAGNÓSTICO - Cambios No Se Reflejan en EC2

## ⚠️ PROBLEMA PRINCIPAL
**Solo reiniciar nginx NO es suficiente.** Nginx es solo el proxy inverso, pero Django corre en un proceso separado (gunicorn/uwsgi).

---

## 📋 PASO 1: Identificar Qué Servicio Corre Django

Ejecuta estos comandos en tu EC2 para identificar el servicio:

```bash
# Verificar si gunicorn está corriendo
sudo systemctl status gunicorn
ps aux | grep gunicorn

# Verificar si uwsgi está corriendo
sudo systemctl status uwsgi
ps aux | grep uwsgi

# Verificar si supervisor está corriendo
sudo supervisorctl status
```

---

## 🔄 PASO 2: Reiniciar el Servicio Correcto

### Si usas **Gunicorn**:
```bash
sudo systemctl restart gunicorn
sudo systemctl status gunicorn  # Verificar que reinició OK
```

### Si usas **uWSGI**:
```bash
sudo systemctl restart uwsgi
```

### Si usas **Supervisor**:
```bash
sudo supervisorctl restart all
# o específico:
sudo supervisorctl restart escuela
```

---

## 📁 PASO 3: Recolectar Archivos Estáticos (CRÍTICO)

Los cambios en `header.html` incluyen **CSS inline**, necesitas:

```bash
cd /ruta/a/tu/proyecto

```

**¿Por qué?** Django sirve archivos estáticos desde `STATIC_ROOT` en producción, no desde `STATICFILES_DIRS`.

---

## 🧹 PASO 4: Limpiar Cachés

### Limpiar caché de Python:
```bash
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### Limpiar caché del navegador:
- **Chrome/Edge**: `Ctrl + Shift + R` (Windows) o `Cmd + Shift + R` (Mac)
- **Firefox**: `Ctrl + F5`
- **O abrir en ventana privada/incógnito**

---

## 🔍 PASO 5: Verificar Logs para Errores

```bash
# Logs de gunicorn
sudo journalctl -u gunicorn -n 50 --no-pager

# Logs de nginx
sudo tail -n 50 /var/log/nginx/error.log

# Logs de la aplicación Django (si los tienes configurados)
tail -n 50 /ruta/a/logs/django.log
```

---

## ✅ CHECKLIST COMPLETO DE DESPLIEGUE

Después de `git pull`, ejecuta EN ESTE ORDEN:

- [ ] 1. `git pull origin main` (ya lo hiciste)
- [ ] 2. `source venv/bin/activate` (activar entorno virtual)
- [ ] 3. `pip install -r requirements.txt` (por si hay nuevas dependencias)
- [ ] 4. `python manage.py migrate` (por si hay migraciones nuevas)
- [ ] 5. **`python manage.py collectstatic --noinput`** ⚠️ **CRÍTICO**
- [ ] 6. **`sudo systemctl restart gunicorn`** (o uwsgi/supervisor) ⚠️ **CRÍTICO**
- [ ] 7. `sudo systemctl restart nginx`
- [ ] 8. Hard refresh en navegador (`Ctrl + Shift + R`)

---

## 🚨 ERRORES COMUNES

### Error 1: "No module named 'X'"
**Solución**: No activaste el entorno virtual antes de pip install
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error 2: "Permission denied" en collectstatic
**Solución**: Problemas de permisos
```bash
sudo chown -R www-data:www-data staticfiles/
# O el usuario que usa gunicorn
sudo chown -R ubuntu:ubuntu staticfiles/
```

### Error 3: Cambios en Python no se reflejan
**Solución**: No reiniciaste gunicorn/uwsgi
```bash
sudo systemctl restart gunicorn
```

### Error 4: Cambios en templates no se reflejan
**Solución**: Tienes caché de templates en settings.py (verifica `TEMPLATES['OPTIONS']['loaders']`)

---

## 🎯 COMANDO RÁPIDO (Todo en Uno)

```bash
cd /home/ubuntu/Escuela && \
source venv/bin/activate && \
git pull origin main && \
pip install -r requirements.txt && \
python manage.py migrate && \
python manage.py collectstatic --noinput && \
sudo systemctl restart gunicorn && \
sudo systemctl restart nginx && \
echo "✅ Despliegue completado"
```

---

## 🔧 CONFIGURACIÓN RECOMENDADA

### En `settings.py` (producción):

```python
# Deshabilitar caché de templates en desarrollo
if DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]
else:
    # En producción usar caché
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]
```

---

## 📞 SI NADA FUNCIONA

1. **Revisa los logs**: `sudo journalctl -u gunicorn -n 100`
2. **Verifica permisos**: `ls -la staticfiles/`
3. **Prueba en incógnito**: Asegúrate que no es caché del navegador
4. **Revisa que el pull funcionó**: `git log -1` en el servidor
5. **Verifica que estás en la rama correcta**: `git branch`

---

## 💡 AUTOMATIZACIÓN

Para evitar este problema, crea el script `deploy.sh` en tu EC2 y ejecuta:

```bash
chmod +x deploy.sh
./deploy.sh
```

Esto ejecutará todos los pasos automáticamente.
