"""
Script para verificar facturas DE HOY en picapolloeka
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context
from ventasweb.models import Factura, PagoFactura
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime

print("=" * 80)
print("DEBUG: Facturas HOY en picapolloeka")
print("=" * 80)

with schema_context('picapolloeka'):
    hoy = timezone.localtime(timezone.now())
    fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    print(f"\n✓ Rango de fechas:")
    print(f"  Inicio: {fecha_inicio}")
    print(f"  Fin: {fecha_fin}")
    
    # Facturas de hoy
    facturas_hoy = Factura.objects.filter(
        fecha_emision__gte=fecha_inicio,
        fecha_emision__lte=fecha_fin
    ).exclude(estado='anulada')
    
    print(f"\n✓ Facturas emitidas HOY: {facturas_hoy.count()}")
    
    if facturas_hoy.count() > 0:
        total_facturado = facturas_hoy.aggregate(total=Sum('total'))['total'] or 0
        print(f"✓ Total facturado HOY: RD$ {total_facturado:,.2f}")
        
        print(f"\nDETALLE DE FACTURAS DE HOY:")
        for factura in facturas_hoy:
            print(f"\n  Factura #{factura.numero_factura}")
            print(f"    - Fecha emisión: {factura.fecha_emision}")
            print(f"    - Total: RD$ {factura.total:,.2f}")
            print(f"    - Estado: {factura.estado}")
            print(f"    - Cliente: {factura.cliente}")
            
            # Verificar pagos de esta factura
            pagos = PagoFactura.objects.filter(factura=factura)
            print(f"    - Pagos registrados: {pagos.count()}")
            
            if pagos.count() > 0:
                for pago in pagos:
                    print(f"      * Pago #{pago.id}: RD$ {pago.monto:,.2f} - Fecha: {pago.fecha_pago} - Método: {pago.metodo_pago}")
            else:
                print(f"      ⚠️ NO HAY PAGOS REGISTRADOS para esta factura")
    
    # Pagos de hoy (independiente de la fecha de la factura)
    pagos_hoy = PagoFactura.objects.filter(
        fecha_pago__gte=fecha_inicio,
        fecha_pago__lte=fecha_fin
    ).exclude(factura__estado='anulada')
    
    print(f"\n{'='*80}")
    print(f"✓ Pagos realizados HOY (cualquier fecha de factura): {pagos_hoy.count()}")
    
    if pagos_hoy.count() > 0:
        total_cobrado = pagos_hoy.aggregate(total=Sum('monto'))['total'] or 0
        print(f"✓ Total cobrado HOY: RD$ {total_cobrado:,.2f}")
        
        print(f"\nDETALLE DE PAGOS DE HOY:")
        for pago in pagos_hoy:
            print(f"  - Pago #{pago.id}: RD$ {pago.monto:,.2f}")
            print(f"    Factura: #{pago.factura.numero_factura}")
            print(f"    Fecha pago: {pago.fecha_pago}")
            print(f"    Método: {pago.metodo_pago}")
    else:
        print(f"⚠️ NO HAY PAGOS REGISTRADOS HOY")
    
    print(f"\n{'='*80}")
    print("CONCLUSIÓN:")
    print(f"{'='*80}")
    print(f"El reporte muestra 'Total Ventas' = Total Cobrado (pagos del día)")
    print(f"NO muestra el total facturado, sino lo realmente pagado/cobrado")
    print(f"\nSi no hay pagos HOY, el reporte mostrará RD$ 0.00")
    print(f"Aunque haya facturas emitidas HOY con estado 'pagada'")
    print(f"{'='*80}")

print("\nFIN DEL DEBUG")
print("=" * 80)
