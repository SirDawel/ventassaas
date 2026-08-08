import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import tenant_context, get_tenant_model
from ventasweb.models import Factura, PagoFactura
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

Tenant = get_tenant_model()

print(f"\n{'='*60}")
print(f"ARREGLAR FACTURAS SIN REGISTROS DE PAGO")
print(f"{'='*60}")

# Obtener el tenant picapolloeka
tenant = Tenant.objects.get(schema_name='picapolloeka')

with tenant_context(tenant):
    # Buscar facturas pagadas sin registros de pago
    facturas_pagadas = Factura.objects.filter(
        estado__in=['pagada', 'parcial']
    ).exclude(monto_pagado=0)
    
    print(f"\nBuscando facturas pagadas sin registros de pago...")
    print(f"Total de facturas pagadas/parciales: {facturas_pagadas.count()}")
    
    facturas_sin_pago = []
    for factura in facturas_pagadas:
        pagos = PagoFactura.objects.filter(factura=factura)
        if not pagos.exists():
            facturas_sin_pago.append(factura)
    
    print(f"\n⚠️ Facturas sin registros de pago: {len(facturas_sin_pago)}")
    
    if facturas_sin_pago:
        print(f"\n{'='*60}")
        print("CREANDO PAGOS FALTANTES")
        print(f"{'='*60}")
        
        for factura in facturas_sin_pago:
            print(f"\n📋 Factura #{factura.numero_factura}")
            print(f"   Cliente: {factura.cliente.get_full_name()}")
            print(f"   Total: RD$ {factura.total:,.2f}")
            print(f"   Estado: {factura.estado}")
            print(f"   Monto Pagado (campo): RD$ {factura.monto_pagado:,.2f}")
            print(f"   Fecha emisión: {factura.fecha_emision.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"   Creado por: {factura.creado_por.get_full_name() if factura.creado_por else 'N/A'}")
            
            try:
                # Crear el registro de pago que falta
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                numero_recibo = f"REC-{timestamp}-FIX-{factura.id}"
                
                pago = PagoFactura.objects.create(
                    factura=factura,
                    monto=factura.monto_pagado,
                    metodo_pago=factura.metodo_pago if factura.metodo_pago else 'efectivo',
                    fecha_pago=factura.fecha_emision,  # Usar la fecha de emisión de la factura
                    registrado_por=factura.creado_por,
                    numero_recibo=numero_recibo,
                    observaciones='Pago creado automáticamente para corregir reporte (faltaba registro)'
                )
                
                print(f"   ✅ Pago creado: {pago.numero_recibo}")
                print(f"      Monto: RD$ {pago.monto:,.2f}")
                print(f"      Fecha: {pago.fecha_pago.strftime('%d/%m/%Y %H:%M:%S')}")
                
            except Exception as e:
                print(f"   ❌ Error al crear pago: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print("✅ PROCESO COMPLETADO")
        print(f"{'='*60}")
        print(f"Pagos creados: {len(facturas_sin_pago)}")
        
        # Verificar nuevamente
        print(f"\nVerificando...")
        hoy = timezone.localtime(timezone.now())
        fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        pagos_hoy = PagoFactura.objects.filter(
            fecha_pago__gte=fecha_inicio,
            fecha_pago__lte=fecha_fin
        ).exclude(factura__estado='anulada')
        
        total_hoy = sum(p.monto for p in pagos_hoy)
        
        print(f"Pagos HOY: {pagos_hoy.count()}")
        print(f"Total cobrado HOY: RD$ {total_hoy:,.2f}")
        
    else:
        print("\n✅ No hay facturas sin registros de pago")

print(f"\n{'='*60}\n")
