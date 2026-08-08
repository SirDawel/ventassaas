"""Script para verificar facturas de un estudiante"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import Factura, DetalleFactura, CustomUser

# Buscar estudiante ID 124
try:
    estudiante = CustomUser.objects.get(id=124)
    print(f"\n=== Estudiante: {estudiante.get_full_name()} ===\n")
    
    facturas = Factura.objects.filter(cliente=estudiante).order_by('-fecha_emision')
    print(f"Total de facturas: {facturas.count()}\n")
    
    for factura in facturas[:5]:  # Primeras 5 facturas
        print(f"Factura: {factura.numero_factura}")
        print(f"  Fecha: {factura.fecha_emision}")
        print(f"  Subtotal: RD${factura.subtotal}")
        print(f"  Total: RD${factura.total}")
        print(f"  Monto Pagado: RD${factura.monto_pagado}")
        print(f"  Saldo: RD${factura.saldo_pendiente}")
        print(f"  Estado: {factura.estado}")
        
        detalles = factura.detalles.all()
        print(f"  Detalles ({detalles.count()}):")
        for detalle in detalles:
            print(f"    - {detalle.descripcion}")
            print(f"      Cantidad: {detalle.cantidad}, Precio: {detalle.precio_unitario}")
            print(f"      Subtotal: {detalle.get_subtotal()}, Total: {detalle.get_total()}")
        print()
        
except CustomUser.DoesNotExist:
    print("No se encontró estudiante con ID 124")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
