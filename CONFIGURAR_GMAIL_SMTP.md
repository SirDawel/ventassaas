# Configuración de Gmail SMTP para Envío de Emails

## 📧 Configuración Requerida

Tu aplicación ya está preparada para usar Gmail SMTP. Solo necesitas configurar las variables de entorno.

## 🔐 Paso 1: Crear Contraseña de Aplicación en Gmail

1. Ve a tu cuenta de Google: https://myaccount.google.com/security
2. Activa la **Verificación en dos pasos** (si no la tienes activa)
3. Ve a **Contraseñas de aplicaciones**: https://myaccount.google.com/apppasswords
4. Selecciona "Correo" y "Otro (nombre personalizado)"
5. Escribe: "Sistema de Ventas"
6. Copia la contraseña de 16 caracteres generada

## 📝 Paso 2: Configurar Variables de Entorno en Producción

En tu servidor EC2, edita el archivo `.env`:

```bash
cd /var/www/ventas
nano .env
```

Agrega o actualiza estas variables:

```bash
# ============================================
# CONFIGURACIÓN DE EMAIL (Gmail SMTP)
# ============================================
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion-de-16-caracteres
DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

**⚠️ IMPORTANTE:** 
- Usa la contraseña de aplicación, NO tu contraseña normal de Gmail
- No incluyas espacios en la contraseña

## 🔄 Paso 3: Reiniciar Servicios

```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

## ✅ Paso 4: Probar Envío de Email

Crea un script de prueba en el servidor:

```bash
nano /var/www/ventas/probar_email.py
```

Contenido:

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
        subject='Prueba de Email - Sistema de Ventas',
        message='Este es un email de prueba desde tu sistema.',
        from_email=os.getenv('DEFAULT_FROM_EMAIL'),
        recipient_list=['tu-email@gmail.com'],
        fail_silently=False,
    )
    print("✅ Email enviado exitosamente")
except Exception as e:
    print(f"❌ Error al enviar email: {e}")
```

Ejecutar:

```bash
cd /var/www/ventas
source .venv/bin/activate
python probar_email.py
```

## 🎯 Casos de Uso

Tu sistema enviará emails automáticamente para:

1. ✅ **Registro de empresa** - Email de bienvenida y activación
2. 📧 **Recuperación de contraseña** - Link de reset
3. 🔐 **Activación de cuenta** - Confirmar email del usuario
4. 🔔 **Notificaciones** - Alertas del sistema
5. 💳 **Facturas** - Si activas AUTO_EMAIL_INVOICES=True

## 🚨 Solución de Problemas

### Error: "SMTPAuthenticationError"
- Verifica que usas la contraseña de aplicación, no la normal
- Asegúrate de tener la verificación en dos pasos activa

### Error: "Connection refused"
- Verifica EMAIL_PORT=587 y EMAIL_USE_TLS=True
- Asegúrate de que el puerto 587 no está bloqueado por firewall

### Error: "Username and Password not accepted"
- Regenera la contraseña de aplicación en Google
- Copia y pega la contraseña sin espacios

### Emails no llegan
- Revisa la carpeta de SPAM del destinatario
- Verifica que DEFAULT_FROM_EMAIL está configurado correctamente
- Revisa los logs de Celery: `sudo journalctl -u celery-worker -f`

## 📊 Límites de Gmail SMTP

- **500 emails por día** para cuentas Gmail normales
- **2000 emails por día** para cuentas Google Workspace
- Si necesitas más, considera usar SendGrid o Amazon SES

## 🔄 Alternativas (si Gmail no es suficiente)

### SendGrid (Recomendado para producción)
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=tu-api-key-de-sendgrid
```

### Amazon SES
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-smtp-username
EMAIL_HOST_PASSWORD=tu-smtp-password
```
