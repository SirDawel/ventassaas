import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.models import Factura, PagoFactura, CustomUser
from django.utils import timezone

print(f"\n{'='*60}")
print(f"VERIFICANDO TODAS LAS FACTURAS EN LA BASE DE DATOS")
print(f"{'='*60}")

# Contar todas las facturas
total_facturas = Factura.objects.all().count()
print(f"\nTotal de facturas en la BD: {total_facturas}")

# Ver todas las facturas (limitado a 50)
facturas = Factura.objects.all().order_by('-fecha_emision')[:50]

if facturas:
    print(f"\nMostrando las últimas {facturas.count()} facturas:")
    for f in facturas:
        print(f"\n  Factura #{f.numero_factura}")
        print(f"  Cliente: {f.cliente.get_full_name()}")
        print(f"  Total: RD$ {f.total:,.2f}")
        print(f"  Estado: {f.estado}")
        print(f"  Monto Pagado (campo): RD$ {f.monto_pagado:,.2f}")
        print(f"  Creada por: {f.creado_por.get_full_name() if f.creado_por else 'N/A'}")
        print(f"  Fecha emisión: {f.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Verificar pagos
        pagos = PagoFactura.objects.filter(factura=f)
        print(f"  Pagos en PagoFactura: {pagos.count()}")
        if pagos.exists():
            total_pagos = sum(p.monto for p in pagos)
            print(f"  Total pagos registrados: RD$ {total_pagos:,.2f}")
            for p in pagos:
                print(f"    - RD$ {p.monto:,.2f} el {p.fecha_pago.strftime('%d/%m/%Y %H:%M')}")
        else:
            if f.estado in ['pagada', 'parcial'] and f.monto_pagado > 0:
                print(f"  ⚠️ PROBLEMA: Estado '{f.estado}' con monto_pagado RD$ {f.monto_pagado:,.2f}")
                print(f"     pero NO hay registros en PagoFactura!")

print(f"\n{'='*60}")
print(f"VERIFICANDO TODOS LOS PAGOS EN LA BASE DE DATOS")
print(f"{'='*60}")

total_pagos = PagoFactura.objects.all().count()
print(f"\nTotal de pagos en la BD: {total_pagos}")

pagos = PagoFactura.objects.all().order_by('-fecha_pago')[:50]

if pagos:
    print(f"\nMostrando los últimos {pagos.count()} pagos:")
    suma_total = sum(p.monto for p in pagos)
    print(f"Suma total de estos pagos: RD$ {suma_total:,.2f}")
    
    for p in pagos:
        print(f"\n  Pago #{p.numero_recibo}")
        print(f"  Factura: #{p.factura.numero_factura}")
        print(f"  Monto: RD$ {p.monto:,.2f}")
        print(f"  Fecha pago: {p.fecha_pago.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"  Registrado por: {p.registrado_por.get_full_name()}")

print(f"\n{'='*60}")
print(f"VERIFICANDO CONFIGURACIÓN DE ZONA HORARIA")
print(f"{'='*60}")

from django.conf import settings
print(f"\nTIME_ZONE en settings: {settings.TIME_ZONE}")
print(f"USE_TZ en settings: {settings.USE_TZ}")

ahora_naive = timezone.now()
ahora_local = timezone.localtime(timezone.now())

print(f"\ntimezone.now() [UTC]: {ahora_naive}")
print(f"timezone.localtime() [Local]: {ahora_local}")

print(f"\n{'='*60}\n")
