"""
Script para verificar la configuración de Stripe
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("VERIFICACIÓN DE CONFIGURACIÓN DE STRIPE")
print("=" * 60)
print()

# Verificar STRIPE_PUBLIC_KEY
public_key = settings.STRIPE_PUBLIC_KEY
print(f"STRIPE_PUBLIC_KEY:")
if public_key:
    print(f"  ✓ Configurada: {public_key[:15]}...{public_key[-10:]}")
    if public_key.startswith('pk_test_'):
        print("  ✓ Es una clave de PRUEBA (correcto para desarrollo)")
    elif public_key.startswith('pk_live_'):
        print("  ⚠ Es una clave de PRODUCCIÓN")
    else:
        print("  ✗ NO es una clave válida de Stripe (debe empezar con pk_test_ o pk_live_)")
else:
    print("  ✗ NO CONFIGURADA - Los campos de pago estarán DESHABILITADOS")
    print("  → Solución: Agregar STRIPE_PUBLIC_KEY al archivo .env")
print()

# Verificar STRIPE_SECRET_KEY
secret_key = settings.STRIPE_SECRET_KEY
print(f"STRIPE_SECRET_KEY:")
if secret_key:
    print(f"  ✓ Configurada: {secret_key[:15]}...{secret_key[-10:]}")
    if secret_key.startswith('sk_test_'):
        print("  ✓ Es una clave de PRUEBA (correcto para desarrollo)")
    elif secret_key.startswith('sk_live_'):
        print("  ⚠ Es una clave de PRODUCCIÓN")
    else:
        print("  ✗ NO es una clave válida de Stripe (debe empezar con sk_test_ o sk_live_)")
else:
    print("  ✗ NO CONFIGURADA - Los pagos NO funcionarán")
    print("  → Solución: Agregar STRIPE_SECRET_KEY al archivo .env")
print()

# Verificar STRIPE_TEST_MODE
test_mode = settings.STRIPE_TEST_MODE
print(f"STRIPE_TEST_MODE: {test_mode}")
if test_mode:
    print("  ✓ Modo de prueba activado (recomendado para desarrollo)")
else:
    print("  ⚠ Modo de producción - USA DINERO REAL")
print()

# Verificar STRIPE_WEBHOOK_SECRET
webhook_secret = settings.STRIPE_WEBHOOK_SECRET
print(f"STRIPE_WEBHOOK_SECRET:")
if webhook_secret:
    print(f"  ✓ Configurada: {webhook_secret[:15]}...")
else:
    print("  ⚠ NO CONFIGURADA - Los webhooks no funcionarán")
    print("  → Solución: Instalar Stripe CLI y ejecutar:")
    print("     stripe listen --forward-to localhost:8000/webhooks/stripe/")
print()

# Resumen
print("=" * 60)
print("RESUMEN")
print("=" * 60)

issues = []
if not public_key:
    issues.append("❌ STRIPE_PUBLIC_KEY no configurada → Los campos estarán DESHABILITADOS")
if not secret_key:
    issues.append("❌ STRIPE_SECRET_KEY no configurada → Los pagos no funcionarán")
if not webhook_secret:
    issues.append("⚠ STRIPE_WEBHOOK_SECRET no configurada → Los webhooks no funcionarán")

if issues:
    print("\n⚠ PROBLEMAS ENCONTRADOS:\n")
    for issue in issues:
        print(f"  {issue}")
    print("\n📋 SOLUCIÓN:")
    print("  1. Ve a: https://dashboard.stripe.com/apikeys")
    print("  2. Copia las claves de PRUEBA (pk_test_ y sk_test_)")
    print("  3. Agrégalas al archivo .env:")
    print()
    print("     STRIPE_PUBLIC_KEY=pk_test_...")
    print("     STRIPE_SECRET_KEY=sk_test_...")
    print()
    print("  4. Reinicia el servidor Django")
    print()
else:
    print("\n✅ Stripe está correctamente configurado!")
    print("   Los campos de pago deberían funcionar correctamente.")
    print()
    print("📝 TARJETAS DE PRUEBA:")
    print("   Número: 4242 4242 4242 4242")
    print("   Fecha: 12/28 (cualquier fecha futura)")
    print("   CVV: 123 (cualquier 3 dígitos)")
    print()

print("=" * 60)
