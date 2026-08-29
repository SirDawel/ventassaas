"""
Script para generar y aplicar migración de los cambios en Client
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.core.management import call_command

print("\n" + "=" * 80)
print("🔄 ACTUALIZACIÓN DEL MODELO DE PLANES Y LÍMITES")
print("=" * 80)

print("\n📝 Generando migraciones...")
try:
    call_command('makemigrations', 'ventasweb')
    print("✅ Migraciones generadas")
except Exception as e:
    print(f"❌ Error al generar migraciones: {e}")
    sys.exit(1)

print("\n📊 Aplicando migraciones...")
try:
    call_command('migrate', 'ventasweb')
    print("✅ Migraciones aplicadas")
except Exception as e:
    print(f"❌ Error al aplicar migraciones: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ACTUALIZACIÓN COMPLETADA")
print("=" * 80)

print("\n📋 Nuevos campos agregados al modelo Client:")
print("   - max_facturas_mes: Límite de facturas por mes")
print("   - max_sucursales: Límite de sucursales")
print("   - reportes_avanzados: Habilita reportes avanzados")
print("   - facturacion_electronica: Habilita facturación electrónica")
print("   - facturas_mes_actual: Contador de facturas del mes")
print("   - ultimo_reset_facturas: Fecha del último reset")
print("   - precio_mensual: Precio del plan mensual")
print("   - proximo_pago: Fecha del próximo pago")

print("\n📋 Planes actualizados:")
print("   - Gratis: $0/mes - 1 usuario, 50 facturas/mes, 1 sucursal")
print("   - Básico: $5/mes - 2 usuarios, 200 facturas/mes, 1 sucursal")
print("   - Plus: $12/mes - 5 usuarios, 1000 facturas/mes, 2 sucursales")
print("   - Pro: $25/mes - 15 usuarios, ilimitado, 5 sucursales")

print("\n⚠️  IMPORTANTE:")
print("   1. Actualiza settings.py para agregar los nuevos middlewares")
print("   2. Los tenants existentes mantendrán su configuración actual")
print("   3. Nuevos tenants se crearán con límites automáticos según su plan")

print("\n" + "=" * 80 + "\n")
