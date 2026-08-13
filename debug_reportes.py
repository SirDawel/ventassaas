"""
Script de debug para verificar por qué no se están calculando las facturas en reportes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.models import Factura, PagoFactura
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum

print("=" * 80)
print("DEBUG: Reportes de Ventas")
print("=" * 80)

# Verificar facturas totales
total_facturas = Factura.objects.count()
print(f"\n✓ Total de facturas en la base de datos: {total_facturas}")

# Verificar facturas no anuladas
facturas_activas = Factura.objects.exclude(estado='anulada').count()
print(f"✓ Facturas activas (no anuladas): {facturas_activas}")

# Verificar facturas por estado
facturas_por_estado = {}
for estado in ['pendiente', 'parcial', 'pagada', 'anulada']:
    count = Factura.objects.filter(estado=estado).count()
    facturas_por_estado[estado] = count
    print(f"  - {estado}: {count}")

# Verificar pagos totales
total_pagos = PagoFactura.objects.count()
print(f"\n✓ Total de pagos registrados: {total_pagos}")

# Verificar rango de fechas de las facturas
primera_factura = Factura.objects.order_by('fecha_emision').first()
ultima_factura = Factura.objects.order_by('-fecha_emision').first()

if primera_factura:
    print(f"\n✓ Primera factura: {primera_factura.fecha_emision}")
    print(f"✓ Última factura: {ultima_factura.fecha_emision}")
else:
    print("\n✗ No hay facturas en la base de datos")

# Calcular totales por período
hoy = timezone.localtime(timezone.now())
print(f"\n✓ Fecha/hora actual (localtime): {hoy}")

# Hoy (período por defecto)
fecha_inicio_hoy = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
fecha_fin_hoy = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)

facturas_hoy = Factura.objects.filter(
    fecha_emision__gte=fecha_inicio_hoy,
    fecha_emision__lte=fecha_fin_hoy
).exclude(estado='anulada')

print(f"\n=== PERÍODO: HOY ({fecha_inicio_hoy.strftime('%d/%m/%Y')}) ===")
print(f"✓ Facturas de hoy: {facturas_hoy.count()}")

if facturas_hoy.count() > 0:
    total_facturado_hoy = facturas_hoy.aggregate(total=Sum('total'))['total'] or 0
    print(f"✓ Total facturado hoy: RD$ {total_facturado_hoy:,.2f}")
    
    for factura in facturas_hoy[:5]:  # Mostrar primeras 5
        print(f"  - Factura #{factura.numero_factura}: RD$ {factura.total:,.2f} - Estado: {factura.estado}")
else:
    print("✗ No hay facturas de hoy")

# Pagos de hoy
pagos_hoy = PagoFactura.objects.filter(
    fecha_pago__gte=fecha_inicio_hoy,
    fecha_pago__lte=fecha_fin_hoy
).exclude(factura__estado='anulada')

print(f"\n✓ Pagos registrados hoy: {pagos_hoy.count()}")

if pagos_hoy.count() > 0:
    total_cobrado_hoy = pagos_hoy.aggregate(total=Sum('monto'))['total'] or 0
    print(f"✓ Total cobrado hoy: RD$ {total_cobrado_hoy:,.2f}")
    
    for pago in pagos_hoy[:5]:  # Mostrar primeros 5
        print(f"  - Pago #{pago.id}: RD$ {pago.monto:,.2f} - Factura #{pago.factura.numero_factura}")
else:
    print("✗ No hay pagos registrados hoy")

# Esta semana
inicio_semana = hoy - timedelta(days=hoy.weekday())
fecha_inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)

facturas_semana = Factura.objects.filter(
    fecha_emision__gte=fecha_inicio_semana,
    fecha_emision__lte=fecha_fin_hoy
).exclude(estado='anulada')

print(f"\n=== PERÍODO: ESTA SEMANA ({fecha_inicio_semana.strftime('%d/%m')} - {fecha_fin_hoy.strftime('%d/%m/%Y')}) ===")
print(f"✓ Facturas esta semana: {facturas_semana.count()}")

if facturas_semana.count() > 0:
    total_facturado_semana = facturas_semana.aggregate(total=Sum('total'))['total'] or 0
    print(f"✓ Total facturado esta semana: RD$ {total_facturado_semana:,.2f}")

# Este mes
fecha_inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

facturas_mes = Factura.objects.filter(
    fecha_emision__gte=fecha_inicio_mes,
    fecha_emision__lte=fecha_fin_hoy
).exclude(estado='anulada')

print(f"\n=== PERÍODO: ESTE MES ({fecha_inicio_mes.strftime('%B %Y')}) ===")
print(f"✓ Facturas este mes: {facturas_mes.count()}")

if facturas_mes.count() > 0:
    total_facturado_mes = facturas_mes.aggregate(total=Sum('total'))['total'] or 0
    print(f"✓ Total facturado este mes: RD$ {total_facturado_mes:,.2f}")

# Verificar si hay problema con timezone
print(f"\n=== VERIFICACIÓN DE TIMEZONE ===")
print(f"✓ USE_TZ en settings: {os.environ.get('USE_TZ', 'True')}")
print(f"✓ Timezone actual: {timezone.get_current_timezone()}")

# Mostrar últimas 10 facturas con fechas
print(f"\n=== ÚLTIMAS 10 FACTURAS ===")
ultimas_facturas = Factura.objects.exclude(estado='anulada').order_by('-fecha_emision')[:10]

for factura in ultimas_facturas:
    print(f"  - #{factura.numero_factura}: RD$ {factura.total:,.2f} - {factura.fecha_emision} - Estado: {factura.estado}")

print("\n" + "=" * 80)
print("FIN DEL DEBUG")
print("=" * 80)
