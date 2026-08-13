"""
Script para corregir las fechas de los pagos automáticos
Los pagos deben tener la misma fecha que la factura, no la fecha actual
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context, get_tenant_model
from ventasweb.models import Factura, PagoFactura

print("=" * 80)
print("CORRIGIENDO FECHAS DE PAGOS AUTOMÁTICOS")
print("=" * 80)

# Obtener todos los tenants
Tenant = get_tenant_model()
tenants = Tenant.objects.all()

total_corregidos = 0

for tenant in tenants:
    print(f"\n{'='*80}")
    print(f"TENANT: {tenant.schema_name}")
    print(f"{'='*80}")
    
    with schema_context(tenant.schema_name):
        # Buscar pagos automáticos (tienen el texto específico en observaciones)
        pagos_automaticos = PagoFactura.objects.filter(
            observaciones__icontains='Pago generado automáticamente por script'
        )
        
        cantidad = pagos_automaticos.count()
        print(f"\n✓ Pagos automáticos encontrados: {cantidad}")
        
        if cantidad == 0:
            print(f"  ✓ No hay pagos que corregir en este tenant")
            continue
        
        # Corregir cada pago
        for pago in pagos_automaticos:
            fecha_anterior = pago.fecha_pago
            fecha_correcta = pago.factura.fecha_emision
            
            # Solo actualizar si las fechas son diferentes
            if fecha_anterior.date() != fecha_correcta.date():
                pago.fecha_pago = fecha_correcta
                pago.save()
                
                print(f"\n  ✓ Pago #{pago.id} - Factura #{pago.factura.numero_factura}")
                print(f"    Fecha anterior: {fecha_anterior}")
                print(f"    Fecha correcta: {fecha_correcta}")
                
                total_corregidos += 1
            else:
                print(f"  ✓ Pago #{pago.id} ya tiene fecha correcta")

print(f"\n{'='*80}")
print("RESUMEN")
print(f"{'='*80}")
print(f"✓ Total de pagos corregidos: {total_corregidos}")
print(f"\n✓ Los reportes ahora mostrarán las fechas correctas")
print("=" * 80)
