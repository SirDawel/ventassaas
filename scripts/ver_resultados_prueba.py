import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
import django
django.setup()

from escuelaweb.models import TransaccionPOS, Factura

print("\n" + "=" * 70)
print("🎉 RESULTADO DE LA PRUEBA - PAGO POS SIMULADO")
print("=" * 70)

# Obtener la última transacción
try:
    t = TransaccionPOS.objects.latest('fecha_transaccion')
    
    print("\n📍 TRANSACCIÓN POS REGISTRADA:")
    print("-" * 70)
    print(f"   ID Transacción: {t.transaction_id}")
    print(f"   Proveedor: {t.proveedor.upper()}")
    print(f"   Terminal: {t.terminal_id}")
    print(f"   Estudiante: {t.estudiante.get_full_name()}")
    print(f"   Cédula: {t.estudiante.cedula}")
    print(f"   Monto: RD$ {t.monto:,.2f}")
    print(f"   Estado: {t.get_estado_display()}")
    print(f"   Tarjeta: {t.tipo_tarjeta} ****{t.tarjeta_ultimos_4}")
    print(f"   Fecha: {t.fecha_transaccion.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Obtener facturas pagadas
    pagos = t.estudiante.facturas.filter(
        estado__in=['pagada', 'parcial']
    ).order_by('-fecha_pago_completo')[:3]
    
    print("\n💳 FACTURAS AFECTADAS:")
    print("-" * 70)
    
    for factura in pagos:
        print(f"\n   📄 Factura: {factura.numero_factura}")
        print(f"      Total: RD$ {factura.total:,.2f}")
        print(f"      Pagado: RD$ {factura.monto_pagado:,.2f}")
        print(f"      Pendiente: RD$ {(factura.total - factura.monto_pagado):,.2f}")
        print(f"      Estado: {factura.get_estado_display()}")
        print(f"      Método de pago: {factura.metodo_pago}")
        
        if factura.pagos.exists():
            ultimo_pago = factura.pagos.latest('fecha_pago')
            print(f"      Último pago: RD$ {ultimo_pago.monto:,.2f} - {ultimo_pago.fecha_pago.strftime('%d/%m/%Y %H:%M')}")
    
    print("\n" + "=" * 70)
    print("✅ VER MÁS DETALLES EN EL ADMIN:")
    print("   http://127.0.0.1:8000/admin/escuelaweb/transaccionpos/")
    print("   http://127.0.0.1:8000/admin/escuelaweb/factura/")
    print("=" * 70)
    
except TransaccionPOS.DoesNotExist:
    print("\n⚠️  No hay transacciones POS registradas aún")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
