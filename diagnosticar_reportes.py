import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.models import Factura, PagoFactura, CustomUser
from django.utils import timezone
from datetime import datetime

# Obtener la fecha de hoy
hoy = timezone.localtime(timezone.now())
fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)

print(f"\n{'='*60}")
print(f"DIAGNÓSTICO DE REPORTES DE VENTAS")
print(f"{'='*60}")
print(f"Fecha actual: {hoy.strftime('%d/%m/%Y %H:%M:%S')}")
print(f"Rango HOY: {fecha_inicio.strftime('%d/%m/%Y %H:%M')} a {fecha_fin.strftime('%d/%m/%Y %H:%M')}")

# 1. Facturas de HOY
print(f"\n{'='*60}")
print("1. FACTURAS EMITIDAS HOY")
print(f"{'='*60}")

facturas_hoy = Factura.objects.filter(
    fecha_emision__gte=fecha_inicio,
    fecha_emision__lte=fecha_fin
).exclude(estado='anulada')

print(f"Total de facturas HOY: {facturas_hoy.count()}")

for f in facturas_hoy:
    print(f"\n  Factura #{f.numero_factura}")
    print(f"  Cliente: {f.cliente.get_full_name()}")
    print(f"  Total: RD$ {f.total:,.2f}")
    print(f"  Estado: {f.estado}")
    print(f"  Monto Pagado: RD$ {f.monto_pagado:,.2f}")
    print(f"  Creada por: {f.creado_por.get_full_name() if f.creado_por else 'N/A'}")
    print(f"  Fecha emisión: {f.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")

# 2. Pagos registrados HOY
print(f"\n{'='*60}")
print("2. PAGOS REGISTRADOS HOY (en tabla PagoFactura)")
print(f"{'='*60}")

pagos_hoy = PagoFactura.objects.filter(
    fecha_pago__gte=fecha_inicio,
    fecha_pago__lte=fecha_fin
).exclude(factura__estado='anulada')

print(f"Total de pagos registrados HOY: {pagos_hoy.count()}")
total_pagos = sum(p.monto for p in pagos_hoy)
print(f"Suma total de pagos HOY: RD$ {total_pagos:,.2f}")

for p in pagos_hoy:
    print(f"\n  Pago #{p.numero_recibo}")
    print(f"  Factura: #{p.factura.numero_factura}")
    print(f"  Monto: RD$ {p.monto:,.2f}")
    print(f"  Método: {p.metodo_pago}")
    print(f"  Registrado por: {p.registrado_por.get_full_name()}")
    print(f"  Fecha pago: {p.fecha_pago.strftime('%d/%m/%Y %H:%M:%S')}")

# 3. Verificar por usuario
print(f"\n{'='*60}")
print("3. PAGOS POR USUARIO")
print(f"{'='*60}")

usuarios_con_pagos = CustomUser.objects.filter(
    pagos_registrados__fecha_pago__gte=fecha_inicio,
    pagos_registrados__fecha_pago__lte=fecha_fin
).distinct()

for usuario in usuarios_con_pagos:
    pagos_usuario = pagos_hoy.filter(registrado_por=usuario)
    total_usuario = sum(p.monto for p in pagos_usuario)
    print(f"\n  {usuario.get_full_name()} ({usuario.rol})")
    print(f"  Cantidad de pagos: {pagos_usuario.count()}")
    print(f"  Total: RD$ {total_usuario:,.2f}")

# 4. Facturas sin pagos registrados
print(f"\n{'='*60}")
print("4. FACTURAS PAGADAS SIN REGISTRO EN PagoFactura")
print(f"{'='*60}")

facturas_pagadas = facturas_hoy.filter(estado__in=['pagada', 'parcial'])
facturas_sin_pago = []

for f in facturas_pagadas:
    pagos = PagoFactura.objects.filter(factura=f)
    if not pagos.exists():
        facturas_sin_pago.append(f)
        print(f"\n  ⚠️ Factura #{f.numero_factura}")
        print(f"     Cliente: {f.cliente.get_full_name()}")
        print(f"     Total: RD$ {f.total:,.2f}")
        print(f"     Estado: {f.estado}")
        print(f"     Monto Pagado (campo): RD$ {f.monto_pagado:,.2f}")
        print(f"     ❌ NO tiene registros en PagoFactura")

if not facturas_sin_pago:
    print("\n  ✓ Todas las facturas pagadas tienen registros de pago")

print(f"\n{'='*60}")
print("RESUMEN")
print(f"{'='*60}")
print(f"Facturas HOY: {facturas_hoy.count()}")
print(f"Pagos registrados HOY: {pagos_hoy.count()}")
print(f"Total en reportes debería ser: RD$ {total_pagos:,.2f}")
print(f"{'='*60}\n")
