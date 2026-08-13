"""
Script para crear registros de pago faltantes en facturas marcadas como 'pagada'
que no tienen registros en PagoFactura.

Esto arregla la inconsistencia donde facturas aparecen como pagadas pero
no se reflejan en los reportes de ventas porque faltan los registros de pago.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context, get_tenant_model
from ventasweb.models import Factura, PagoFactura, CustomUser
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import time

print("=" * 80)
print("ARREGLANDO PAGOS FALTANTES EN FACTURAS")
print("=" * 80)

# Obtener todos los tenants
Tenant = get_tenant_model()
tenants = Tenant.objects.all()

total_facturas_arregladas = 0
total_pagos_creados = 0
contador_global = 0  # Para evitar duplicados en numero_recibo

for tenant in tenants:
    print(f"\n{'='*80}")
    print(f"TENANT: {tenant.schema_name}")
    print(f"{'='*80}")
    
    with schema_context(tenant.schema_name):
        # Buscar facturas marcadas como 'pagada' sin registros de pago
        facturas_sin_pago = Factura.objects.filter(
            estado='pagada'
        ).exclude(
            id__in=PagoFactura.objects.values_list('factura_id', flat=True)
        )
        
        cantidad = facturas_sin_pago.count()
        print(f"\n✓ Facturas 'pagadas' sin registros de pago: {cantidad}")
        
        if cantidad == 0:
            print(f"  ✓ No hay facturas que arreglar en este tenant")
            continue
        
        # Procesar cada factura
        for factura in facturas_sin_pago:
            print(f"\n  Procesando factura #{factura.numero_factura}")
            print(f"    - Total: RD$ {factura.total:,.2f}")
            print(f"    - Fecha emisión: {factura.fecha_emision}")
            print(f"    - Cliente: {factura.cliente}")
            
            # Determinar usuario que registra el pago
            # Prioridad: creado_por > primer admin/director > primer usuario activo
            usuario_pago = None
            
            if hasattr(factura, 'creado_por') and factura.creado_por:
                usuario_pago = factura.creado_por
            else:
                # Buscar un administrador o director
                usuario_pago = CustomUser.objects.filter(
                    is_active=True,
                    rol__in=['Administrador', 'Director']
                ).first()
                
                if not usuario_pago:
                    # Último recurso: cualquier usuario activo
                    usuario_pago = CustomUser.objects.filter(is_active=True).first()
            
            if not usuario_pago:
                print(f"    ⚠️ ERROR: No hay usuarios activos en este tenant. Saltando.")
                continue
            
            # Generar número de recibo único
            contador_global += 1
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            numero_recibo_unico = f"REC-{timestamp}-AUTO-{contador_global:05d}"
            
            # Crear registro de pago
            try:
                pago = PagoFactura.objects.create(
                    factura=factura,
                    monto=factura.total,
                    metodo_pago='efectivo',  # Método por defecto
                    fecha_pago=factura.fecha_emision,  # Usar fecha de emisión
                    registrado_por=usuario_pago,
                    numero_recibo=numero_recibo_unico,  # Número único generado
                    observaciones='Pago generado automáticamente por script de corrección de datos'
                )
                
                print(f"    ✓ Pago creado exitosamente:")
                print(f"      - ID: {pago.id}")
                print(f"      - Monto: RD$ {pago.monto:,.2f}")
                print(f"      - Método: {pago.metodo_pago}")
                print(f"      - Registrado por: {usuario_pago.get_full_name()}")
                
                total_pagos_creados += 1
                total_facturas_arregladas += 1
                
            except Exception as e:
                print(f"    ✗ ERROR al crear pago: {e}")
        
        print(f"\n  RESUMEN TENANT {tenant.schema_name}:")
        print(f"    - Facturas arregladas: {cantidad}")
        print(f"    - Pagos creados: {cantidad}")

print(f"\n{'='*80}")
print("RESUMEN GENERAL")
print(f"{'='*80}")
print(f"✓ Total facturas arregladas: {total_facturas_arregladas}")
print(f"✓ Total pagos creados: {total_pagos_creados}")
print(f"\n✓ Los reportes ahora mostrarán correctamente las ventas")
print("=" * 80)
