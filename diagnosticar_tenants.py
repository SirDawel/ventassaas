import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context, tenant_context, get_tenant_model
from ventasweb.models import Factura, PagoFactura

Tenant = get_tenant_model()
from django.utils import timezone
from datetime import datetime

print(f"\n{'='*60}")
print(f"DIAGNÓSTICO MULTITENANT - FACTURAS Y PAGOS")
print(f"{'='*60}")

# Listar todos los tenants
tenants = Tenant.objects.all()
print(f"\nTenants disponibles: {tenants.count()}")

for tenant in tenants:
    print(f"\n{'='*60}")
    print(f"TENANT: {tenant.schema_name} ({tenant.nombre})")
    print(f"Dominio: {tenant.get_primary_domain()}")
    print(f"{'='*60}")
    
    # Usar el contexto del tenant
    with tenant_context(tenant):
        # Ver todas las facturas
        facturas = Factura.objects.all().order_by('-fecha_emision')[:10]
        total_facturas = Factura.objects.all().count()
        
        print(f"\nTotal de facturas: {total_facturas}")
        
        if facturas:
            print(f"\nÚltimas {facturas.count()} facturas:")
            for f in facturas:
                print(f"\n  Factura #{f.numero_factura}")
                print(f"  Cliente: {f.cliente.get_full_name()}")
                print(f"  Total: RD$ {f.total:,.2f}")
                print(f"  Estado: {f.estado}")
                print(f"  Monto Pagado: RD$ {f.monto_pagado:,.2f}")
                print(f"  Fecha emisión: {f.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")
                
                # Verificar pagos
                pagos = PagoFactura.objects.filter(factura=f)
                if pagos.exists():
                    total_pagos = sum(p.monto for p in pagos)
                    print(f"  ✓ Pagos registrados: {pagos.count()} - Total: RD$ {total_pagos:,.2f}")
                else:
                    if f.estado in ['pagada', 'parcial'] and f.monto_pagado > 0:
                        print(f"  ⚠️ PROBLEMA: Estado '{f.estado}', monto_pagado RD$ {f.monto_pagado:,.2f}")
                        print(f"     pero NO tiene registros en PagoFactura!")
        
        # Ver pagos de HOY
        hoy = timezone.localtime(timezone.now())
        fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        pagos_hoy = PagoFactura.objects.filter(
            fecha_pago__gte=fecha_inicio,
            fecha_pago__lte=fecha_fin
        ).exclude(factura__estado='anulada')
        
        print(f"\n  --- PAGOS DE HOY ---")
        print(f"  Fecha: {hoy.strftime('%d/%m/%Y')}")
        print(f"  Rango: {fecha_inicio.strftime('%H:%M')} a {fecha_fin.strftime('%H:%M')}")
        print(f"  Pagos HOY: {pagos_hoy.count()}")
        
        if pagos_hoy.exists():
            total_hoy = sum(p.monto for p in pagos_hoy)
            print(f"  Total cobrado HOY: RD$ {total_hoy:,.2f}")
            for p in pagos_hoy:
                print(f"\n    Pago #{p.numero_recibo}")
                print(f"    Monto: RD$ {p.monto:,.2f}")
                print(f"    Fecha: {p.fecha_pago.strftime('%d/%m/%Y %H:%M')}")
                print(f"    Registrado por: {p.registrado_por.get_full_name()}")
        else:
            print(f"  ❌ No hay pagos registrados HOY")
        
        # Ver todas los pagos (últimos 10)
        todos_pagos = PagoFactura.objects.all().order_by('-fecha_pago')[:10]
        if todos_pagos.exists():
            print(f"\n  --- ÚLTIMOS {todos_pagos.count()} PAGOS (todas las fechas) ---")
            for p in todos_pagos:
                print(f"\n    Pago #{p.numero_recibo}")
                print(f"    Factura: #{p.factura.numero_factura}")
                print(f"    Monto: RD$ {p.monto:,.2f}")
                print(f"    Fecha pago: {p.fecha_pago.strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"    Fecha factura: {p.factura.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"    Registrado por: {p.registrado_por.get_full_name()}")

print(f"\n{'='*60}\n")
