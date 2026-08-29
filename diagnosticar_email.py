"""
Script de diagnóstico de configuración de email
Verifica la configuración actual y prueba el envío de email
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.conf import settings
from django.core.mail import EmailMessage

print("\n" + "="*70)
print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN DE EMAIL")
print("="*70 + "\n")

# Verificar configuración actual
print("📧 Configuración actual:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"   EMAIL_HOST_USER: {'✅ Configurado' if settings.EMAIL_HOST_USER else '❌ NO CONFIGURADO (VACÍO)'}")
print(f"   EMAIL_HOST_PASSWORD: {'✅ Configurado' if settings.EMAIL_HOST_PASSWORD else '❌ NO CONFIGURADO (VACÍO)'}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL if settings.DEFAULT_FROM_EMAIL else '❌ NO CONFIGURADO'}")

print("\n" + "-"*70)

# Verificar si hay archivo .env
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_file):
    print(f"✅ Archivo .env encontrado: {env_file}")
else:
    print(f"❌ Archivo .env NO ENCONTRADO")
    print(f"   Ubicación esperada: {env_file}")

print("\n" + "-"*70)

# Diagnóstico del problema
if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
    print("\n⚠️  PROBLEMA IDENTIFICADO:")
    print("   Las credenciales de email NO están configuradas.")
    print("   El sistema NO PUEDE enviar correos electrónicos.\n")
    print("📝 SOLUCIÓN:")
    print("   1. Crea un archivo .env en la raíz del proyecto")
    print("   2. Agrega las siguientes variables:\n")
    print("      EMAIL_HOST_USER=tu_correo@gmail.com")
    print("      EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion")
    print("      DEFAULT_FROM_EMAIL=tu_correo@gmail.com\n")
    print("   3. Si usas Gmail, necesitas una 'Contraseña de Aplicación':")
    print("      https://myaccount.google.com/apppasswords")
    print("\n" + "="*70 + "\n")
else:
    print("\n✅ Credenciales configuradas. Probando envío de email...\n")
    
    try:
        email = EmailMessage(
            subject='🧪 Prueba de Email - Sistema de Ventas',
            body='Este es un email de prueba para verificar la configuración.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],
        )
        email.send(fail_silently=False)
        print("✅ EMAIL ENVIADO EXITOSAMENTE!")
        print(f"   Revisa la bandeja de entrada de: {settings.EMAIL_HOST_USER}")
    except Exception as e:
        print(f"❌ ERROR AL ENVIAR EMAIL:")
        print(f"   {type(e).__name__}: {str(e)}")
        print("\n   Posibles causas:")
        print("   - Contraseña incorrecta")
        print("   - Debes usar una 'Contraseña de Aplicación' de Gmail")
        print("   - Verificación de 2 pasos no configurada en Gmail")
        print("   - Firewall bloqueando el puerto 587")
    
    print("\n" + "="*70 + "\n")
