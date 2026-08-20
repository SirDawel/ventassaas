# 🚀 Pasos para Solucionar Errores en Producción

## 📋 Resumen de Problemas

1. ✅ Tenant "brevo" corrupto - causa error en migraciones
2. ✅ Configurar Gmail SMTP para envío de emails

## ⚡ Solución Rápida (5 minutos)

### Paso 1: Actualizar código en el servidor

```bash
# Conectarse al servidor EC2
ssh usuario@tu-servidor

# Ir al directorio del proyecto
cd /var/www/ventas

# Descargar últimos cambios
git pull

# Activar entorno virtual
source .venv/bin/activate
```

### Paso 2: Eliminar tenant brevo corrupto

```bash
# Listar todos los tenants (opcional, para ver el problema)
python listar_tenants.py

# Eliminar tenant brevo
python eliminar_tenant_brevo.py
```

Cuando te pregunte: `⚠️ ¿Estás seguro de eliminar el tenant 'brevo'? (si/no):`

Escribe: **si**

### Paso 3: Ejecutar migraciones

```bash
python manage.py migrate_schemas
```

**✅ Resultado esperado:** Las migraciones deben completarse sin errores para todos los tenants.

### Paso 4: Configurar Gmail SMTP

#### 4.1 Obtener contraseña de aplicación de Gmail

1. Ve a: https://myaccount.google.com/apppasswords
2. Activa verificación en dos pasos si no la tienes
3. Crea una contraseña de aplicación para "Correo"
4. **Copia la contraseña de 16 caracteres**

#### 4.2 Editar archivo .env

```bash
nano /var/www/ventas/.env
```

Agrega o actualiza estas líneas:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

**⚠️ Reemplaza:**
- `tu-email@gmail.com` con tu email real
- `xxxx xxxx xxxx xxxx` con la contraseña de aplicación de 16 caracteres

Guarda con: `Ctrl + X`, luego `Y`, luego `Enter`

### Paso 5: Reiniciar servicios

```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

### Paso 6: Probar que todo funciona

#### 6.1 Verificar que el servidor está corriendo

```bash
sudo systemctl status gunicorn
sudo systemctl status celery-worker
```

Ambos deben mostrar: `Active: active (running)`

#### 6.2 Probar envío de email

```bash
nano /var/www/ventas/probar_email.py
```

Pega este código:

```python
#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, '/var/www/ventas')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.core.mail import send_mail

try:
    send_mail(
        subject='✅ Prueba de Email - Sistema de Ventas',
        message='Este es un email de prueba desde tu sistema de producción.',
        from_email=os.getenv('DEFAULT_FROM_EMAIL'),
        recipient_list=['tu-email@gmail.com'],  # Cambia esto por tu email
        fail_silently=False,
    )
    print("✅ Email enviado exitosamente")
except Exception as e:
    print(f"❌ Error al enviar email: {e}")
```

Ejecuta:

```bash
python probar_email.py
```

**✅ Resultado esperado:** Deberías recibir un email en tu bandeja de entrada (o spam).

#### 6.3 Probar registro de empresa

1. Ve a: https://misventasflash.com/registrar-empresa/
2. Completa el formulario
3. Verifica que:
   - ✅ No hay error 500
   - ✅ Recibes email de activación
   - ✅ La empresa se registra correctamente

## 🎯 Verificación Final

```bash
# Ver tenants activos
python listar_tenants.py

# Ver logs en tiempo real
sudo journalctl -u gunicorn -f

# Ver logs de Celery
sudo journalctl -u celery-worker -f
```

## ❌ Solución de Problemas

### Error: "Authentication failed" en email

```bash
# Verificar configuración
nano /var/www/ventas/.env

# Asegúrate de:
# 1. Usar contraseña de APLICACIÓN, no tu contraseña normal
# 2. No hay espacios extra en la contraseña
# 3. EMAIL_USE_TLS=True (no False)
```

### Error: "No module named 'ventasweb'"

```bash
# Verifica que estás en el directorio correcto
cd /var/www/ventas

# Activa el entorno virtual
source .venv/bin/activate

# Verifica que Django está instalado
python -c "import django; print(django.VERSION)"
```

### El servidor no arranca después de los cambios

```bash
# Ver el error específico
sudo journalctl -u gunicorn -n 50

# Reiniciar todo
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

## 📚 Documentación Completa

- **Configuración Gmail SMTP:** [CONFIGURAR_GMAIL_SMTP.md](CONFIGURAR_GMAIL_SMTP.md)
- **Solucionar tenant brevo:** [FIX_TENANT_BREVO.md](FIX_TENANT_BREVO.md)

## ✅ Checklist Final

- [ ] `git pull` ejecutado
- [ ] Tenant brevo eliminado
- [ ] Migraciones ejecutadas sin errores
- [ ] Gmail SMTP configurado en .env
- [ ] Servicios reiniciados
- [ ] Email de prueba enviado
- [ ] Registro de empresa funciona sin error 500

**🎉 Todo listo. Tu sistema debe estar funcionando correctamente en producción.**
