"""
Script para verificar facturas en todos los schemas (multitenant)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context, get_tenant_model
from ventasweb.models import Factura, PagoFactura
from django.db.models import Sum

print("=" * 80)
print("DEBUG: Verificando facturas en TODOS los tenants")
print("=" * 80)

# Obtener todos los tenants
Tenant = get_tenant_model()
tenants = Tenant.objects.all()

print(f"\n✓ Total de tenants registrados: {tenants.count()}")

for tenant in tenants:
    print(f"\n{'='*80}")
    print(f"TENANT: {tenant.schema_name} - {tenant.domain_url if hasattr(tenant, 'domain_url') else 'N/A'}")
    print(f"{'='*80}")
    
    with schema_context(tenant.schema_name):
        # Contar facturas en este tenant
        total_facturas = Factura.objects.count()
        facturas_activas = Factura.objects.exclude(estado='anulada').count()
        total_pagos = PagoFactura.objects.count()
        
        print(f"  ✓ Facturas totales: {total_facturas}")
        print(f"  ✓ Facturas activas: {facturas_activas}")
        print(f"  ✓ Pagos registrados: {total_pagos}")
        
        if facturas_activas > 0:
            total_facturado = Factura.objects.exclude(estado='anulada').aggregate(
                total=Sum('total')
            )['total'] or 0
            print(f"  ✓ Total facturado: RD$ {total_facturado:,.2f}")
            
            # Mostrar últimas 5 facturas
            print(f"\n  ÚLTIMAS 5 FACTURAS:")
            ultimas = Factura.objects.exclude(estado='anulada').order_by('-fecha_emision')[:5]
            for factura in ultimas:
                print(f"    - #{factura.numero_factura}: RD$ {factura.total:,.2f} - {factura.fecha_emision.strftime('%d/%m/%Y %H:%M')} - Estado: {factura.estado}")
        
        if total_pagos > 0:
            total_cobrado = PagoFactura.objects.exclude(
                factura__estado='anulada'
            ).aggregate(total=Sum('monto'))['total'] or 0
            print(f"  ✓ Total cobrado: RD$ {total_cobrado:,.2f}")

print(f"\n{'='*80}")
print("FIN DEL DEBUG")
print("=" * 80)
