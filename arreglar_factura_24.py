"""
Script rápido para arreglar la factura #24 que quedó sin pago
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context
from ventasweb.models import Factura, PagoFactura
from datetime import datetime

with schema_context('picapolloeka'):
    # Buscar factura #24
    try:
        factura = Factura.objects.get(numero_factura='FAC-20260803192909-00024')
        
        # Verificar si ya tiene pago
        if factura.pagos.exists():
            print(f"✓ Factura #{factura.numero_factura} ya tiene pago registrado")
        else:
            # Crear pago
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            pago = PagoFactura.objects.create(
                factura=factura,
                monto=factura.total,
                metodo_pago='efectivo',
                fecha_pago=factura.fecha_emision,
                registrado_por=factura.creado_por,
                numero_recibo=f"REC-{timestamp}-FIX",
                observaciones='Pago corregido manualmente'
            )
            print(f"✓ Pago creado para factura #{factura.numero_factura}")
            print(f"  - Monto: RD$ {pago.monto}")
            print(f"  - Fecha: {pago.fecha_pago}")
    except Factura.DoesNotExist:
        print("✗ Factura no encontrada")
