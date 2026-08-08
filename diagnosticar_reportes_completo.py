import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.models import Factura, PagoFactura, CustomUser
from django.utils import timezone
from datetime import datetime, timedelta

print(f"\n{'='*60}")
print(f"DIAGNÓSTICO COMPLETO - ÚLTIMAS FACTURAS Y PAGOS")
print(f"{'='*60}")

# Ver todas las facturas recientes (últimos 7 días)
hoy = timezone.localtime(timezone.now())
hace_7_dias = hoy - timedelta(days=7)

print(f"\nFecha actual del sistema: {hoy.strftime('%d/%m/%Y %H:%M:%S')}")

print(f"\n{'='*60}")
print("TODAS LAS FACTURAS (últimos 7 días)")
print(f"{'='*60}")

facturas_recientes = Factura.objects.filter(
    fecha_emision__gte=hace_7_dias
).exclude(estado='anulada').order_by('-fecha_emision')

print(f"Total de facturas (últimos 7 días): {facturas_recientes.count()}")

for f in facturas_recientes:
    print(f"\n  Factura #{f.numero_factura}")
    print(f"  Cliente: {f.cliente.get_full_name()}")
    print(f"  Total: RD$ {f.total:,.2f}")
    print(f"  Estado: {f.estado}")
    print(f"  Monto Pagado: RD$ {f.monto_pagado:,.2f}")
    print(f"  Creada por: {f.creado_por.get_full_name() if f.creado_por else 'N/A'}")
    print(f"  Fecha emisión: {f.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Verificar pagos asociados
    pagos = PagoFactura.objects.filter(factura=f)
    if pagos.exists():
        print(f"  Pagos registrados: {pagos.count()}")
        for p in pagos:
            print(f"    - RD$ {p.monto:,.2f} ({p.fecha_pago.strftime('%d/%m/%Y %H:%M')})")
    else:
        if f.estado in ['pagada', 'parcial']:
            print(f"  ⚠️ Estado '{f.estado}' pero SIN pagos en PagoFactura!")

print(f"\n{'='*60}")
print("TODOS LOS PAGOS (últimos 7 días)")
print(f"{'='*60}")

pagos_recientes = PagoFactura.objects.filter(
    fecha_pago__gte=hace_7_dias
).exclude(factura__estado='anulada').order_by('-fecha_pago')

print(f"Total de pagos (últimos 7 días): {pagos_recientes.count()}")
total_pagos_recientes = sum(p.monto for p in pagos_recientes)
print(f"Suma total: RD$ {total_pagos_recientes:,.2f}")

for p in pagos_recientes:
    print(f"\n  Pago #{p.numero_recibo}")
    print(f"  Factura: #{p.factura.numero_factura}")
    print(f"  Monto: RD$ {p.monto:,.2f}")
    print(f"  Método: {p.metodo_pago}")
    print(f"  Registrado por: {p.registrado_por.get_full_name()}")
    print(f"  Fecha pago: {p.fecha_pago.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"  Fecha emisión factura: {p.factura.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")

print(f"\n{'='*60}")
print("ANÁLISIS DE FECHAS")
print(f"{'='*60}")

# Verificar si hay diferencia entre fecha_emision y fecha_pago
if pagos_recientes.exists():
    print("\nComparando fechas de emisión vs fechas de pago:")
    for p in pagos_recientes[:10]:  # Primeros 10
        fecha_emision = p.factura.fecha_emision
        fecha_pago = p.fecha_pago
        diferencia = (fecha_pago - fecha_emision).total_seconds() / 60  # en minutos
        
        print(f"\n  Factura #{p.factura.numero_factura}:")
        print(f"    Emisión: {fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"    Pago:    {fecha_pago.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"    Diferencia: {abs(diferencia):.0f} minutos")

print(f"\n{'='*60}\n")
