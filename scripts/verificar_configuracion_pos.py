"""
Script para verificar la configuración del sistema POS
Este script te dice exactamente qué falta configurar
"""

import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
import django
django.setup()

from django.conf import settings
from escuelaweb.models import CustomUser, Factura, TransaccionPOS, TerminalEstudiante

print("=" * 80)
print("🔍 VERIFICACIÓN DE CONFIGURACIÓN - SISTEMA POS FÍSICOS")
print("=" * 80)
print()

# Variables a verificar
verificaciones = []

def check(condicion, mensaje_ok, mensaje_error):
    """Helper para verificar condiciones"""
    if condicion:
        print(f"✅ {mensaje_ok}")
        return True
    else:
        print(f"❌ {mensaje_error}")
        verificaciones.append(mensaje_error)
        return False

# ============================================
# 1. VERIFICAR PROVEEDOR
# ============================================
print("📋 1. PROVEEDOR DE PAGO")
print("-" * 80)

proveedor = getattr(settings, 'PAYMENT_PROVIDER', None)
if proveedor:
    print(f"✅ Proveedor configurado: {proveedor.upper()}")
else:
    print("❌ No hay proveedor configurado en PAYMENT_PROVIDER")
    verificaciones.append("Configurar PAYMENT_PROVIDER en .env")

print()

# ============================================
# 2. VERIFICAR CREDENCIALES CARDNET
# ============================================
if proveedor == 'cardnet':
    print("📋 2. CREDENCIALES CARDNET")
    print("-" * 80)
    
    api_key = getattr(settings, 'CARDNET_API_KEY', '')
    merchant_id = getattr(settings, 'CARDNET_MERCHANT_ID', '')
    webhook_secret = getattr(settings, 'CARDNET_WEBHOOK_SECRET', '')
    api_url = getattr(settings, 'CARDNET_API_URL', '')
    
    check(
        api_key and api_key != 'PENDIENTE_SOLICITAR',
        f"API Key configurado: {api_key[:10]}...",
        "CARDNET_API_KEY pendiente de configurar"
    )
    
    check(
        merchant_id and merchant_id != 'PENDIENTE_SOLICITAR',
        f"Merchant ID configurado: {merchant_id}",
        "CARDNET_MERCHANT_ID pendiente de configurar"
    )
    
    check(
        webhook_secret and webhook_secret != 'PENDIENTE_SOLICITAR',
        f"Webhook Secret configurado: {webhook_secret[:10]}...",
        "CARDNET_WEBHOOK_SECRET pendiente de configurar"
    )
    
    check(
        api_url,
        f"URL API: {api_url}",
        "CARDNET_API_URL no configurado"
    )
    
    if 'sandbox' in api_url.lower():
        print("⚠️  Estás usando la URL de SANDBOX (pruebas)")
    else:
        print("✅ Estás usando la URL de PRODUCCIÓN")
    
    print()

# ============================================
# 3. VERIFICAR CREDENCIALES AZUL
# ============================================
if proveedor == 'azul':
    print("📋 2. CREDENCIALES AZUL")
    print("-" * 80)
    
    user = getattr(settings, 'AZUL_USER', '')
    password = getattr(settings, 'AZUL_PASSWORD', '')
    store_id = getattr(settings, 'AZUL_STORE_ID', '')
    webhook_secret = getattr(settings, 'AZUL_WEBHOOK_SECRET', '')
    api_url = getattr(settings, 'AZUL_API_URL', '')
    
    check(
        user and user != 'PENDIENTE_SOLICITAR',
        f"Usuario configurado: {user}",
        "AZUL_USER pendiente de configurar"
    )
    
    check(
        password and password != 'PENDIENTE_SOLICITAR',
        f"Password configurado: {'*' * len(password)}",
        "AZUL_PASSWORD pendiente de configurar"
    )
    
    check(
        store_id and store_id != 'PENDIENTE_SOLICITAR',
        f"Store ID configurado: {store_id}",
        "AZUL_STORE_ID pendiente de configurar"
    )
    
    check(
        webhook_secret and webhook_secret != 'PENDIENTE_SOLICITAR',
        f"Webhook Secret configurado: {webhook_secret[:10]}...",
        "AZUL_WEBHOOK_SECRET pendiente de configurar"
    )
    
    check(
        api_url,
        f"URL API: {api_url}",
        "AZUL_API_URL no configurado"
    )
    
    if 'sandbox' in api_url.lower():
        print("⚠️  Estás usando la URL de SANDBOX (pruebas)")
    else:
        print("✅ Estás usando la URL de PRODUCCIÓN")
    
    print()

# ============================================
# 4. VERIFICAR IMPRESORA
# ============================================
print("📋 3. CONFIGURACIÓN DE IMPRESORA")
print("-" * 80)

auto_print = getattr(settings, 'AUTO_PRINT_INVOICES', False)
printer_enabled = getattr(settings, 'POS_PRINTER_ENABLED', False)
printer_type = getattr(settings, 'POS_PRINTER_TYPE', 'file')

print(f"{'✅' if auto_print else '❌'} Impresión automática: {'HABILITADA' if auto_print else 'DESHABILITADA'}")
print(f"{'✅' if printer_enabled else 'ℹ️ '} Impresora POS: {'HABILITADA' if printer_enabled else 'DESHABILITADA'}")
print(f"ℹ️  Tipo de impresora: {printer_type.upper()}")

if printer_type == 'network':
    ip = getattr(settings, 'POS_PRINTER_IP', 'No configurado')
    port = getattr(settings, 'POS_PRINTER_PORT', 'No configurado')
    print(f"   → Impresora en red: {ip}:{port}")
    
elif printer_type == 'usb':
    vendor = getattr(settings, 'POS_PRINTER_VENDOR_ID', 'No configurado')
    product = getattr(settings, 'POS_PRINTER_PRODUCT_ID', 'No configurado')
    print(f"   → Impresora USB: Vendor {hex(vendor)}, Product {hex(product)}")
    
elif printer_type == 'file':
    path = getattr(settings, 'POS_PRINTER_PATH', 'No configurado')
    print(f"   → Archivo de prueba: {path}")
    print(f"   💡 Perfecto para pruebas sin impresora física")

print()

# ============================================
# 5. VERIFICAR EMAIL
# ============================================
print("📋 4. CONFIGURACIÓN DE EMAIL")
print("-" * 80)

auto_email = getattr(settings, 'AUTO_EMAIL_INVOICES', False)
email_backend = settings.EMAIL_BACKEND
email_host = getattr(settings, 'EMAIL_HOST', 'No configurado')
email_user = getattr(settings, 'EMAIL_HOST_USER', 'No configurado')

print(f"{'✅' if auto_email else '❌'} Email automático: {'HABILITADO' if auto_email else 'DESHABILITADO'}")
print(f"ℹ️  Backend: {email_backend}")
print(f"ℹ️  Host: {email_host}")
print(f"ℹ️  Usuario: {email_user}")

print()

# ============================================
# 6. VERIFICAR BASE DE DATOS
# ============================================
print("📋 5. BASE DE DATOS")
print("-" * 80)

try:
    total_estudiantes = CustomUser.objects.filter(rol='Estudiante', is_active=True).count()
    total_facturas = Factura.objects.count()
    facturas_pendientes = Factura.objects.filter(estado__in=['pendiente', 'vencida', 'parcial']).count()
    total_transacciones = TransaccionPOS.objects.count()
    total_terminales = TerminalEstudiante.objects.filter(activo=True).count()
    
    print(f"✅ Estudiantes activos: {total_estudiantes}")
    print(f"✅ Facturas totales: {total_facturas}")
    print(f"✅ Facturas pendientes: {facturas_pendientes}")
    print(f"ℹ️  Transacciones POS registradas: {total_transacciones}")
    print(f"ℹ️  Terminales asociados: {total_terminales}")
    
    if total_estudiantes == 0:
        print("⚠️  No hay estudiantes registrados")
        verificaciones.append("Registrar al menos un estudiante para probar")
    
    if facturas_pendientes == 0:
        print("⚠️  No hay facturas pendientes")
        verificaciones.append("Generar facturas mensuales para probar pagos")
    
except Exception as e:
    print(f"❌ Error consultando base de datos: {str(e)}")
    verificaciones.append("Verificar conexión a base de datos")

print()

# ============================================
# 7. VERIFICAR URLS
# ============================================
print("📋 6. URLS DE WEBHOOK")
print("-" * 80)

site_url = getattr(settings, 'SITE_URL', '127.0.0.1:8000')
print(f"ℹ️  URL del sitio: {site_url}")

if proveedor == 'cardnet':
    webhook_url = f"https://{site_url}/webhooks/pos/cardnet/"
    print(f"📍 URL webhook Cardnet: {webhook_url}")
    
elif proveedor == 'azul':
    webhook_url = f"https://{site_url}/webhooks/pos/azul/"
    print(f"📍 URL webhook Azul: {webhook_url}")

if '127.0.0.1' in site_url or 'localhost' in site_url:
    print()
    print("⚠️  IMPORTANTE: Para recibir webhooks reales necesitas:")
    print("   1. Un dominio público con HTTPS (ej. https://www.tuescuela.edu.do)")
    print("   2. O usar ngrok para desarrollo: ngrok http 8000")
    print("      Luego usa la URL que te da: https://abc123.ngrok.io/webhooks/pos/cardnet/")

print()

# ============================================
# RESUMEN FINAL
# ============================================
print("=" * 80)
print("📊 RESUMEN")
print("=" * 80)

if not verificaciones:
    print("🎉 ¡TODO CONFIGURADO CORRECTAMENTE!")
    print()
    print("PRÓXIMOS PASOS:")
    print("1. Configurar el webhook en el portal de " + (proveedor or 'tu proveedor').upper())
    print("2. Probar con: python scripts/test_webhook_pos.py " + (proveedor or 'cardnet'))
    print("3. Ver resultados en: http://127.0.0.1:8000/admin/escuelaweb/transaccionpos/")
else:
    print(f"⚠️  HAY {len(verificaciones)} CONFIGURACIÓN(ES) PENDIENTE(S):")
    print()
    for i, item in enumerate(verificaciones, 1):
        print(f"   {i}. {item}")
    print()
    print("📖 LEE LA GUÍA: GUIA_CONFIGURACION_PASO_A_PASO.md")

print()
print("=" * 80)
