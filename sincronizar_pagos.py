"""
Script de mantenimiento para sincronizar facturas pagadas con registros de pago.
Ejecutar periódicamente para mantener consistencia en los reportes.
"""
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

def sincronizar_facturas_tenant(tenant, crear_pagos=False):
    """
    Verifica y opcionalmente corrige inconsistencias en un tenant.
    
    Args:
        tenant: Objeto Tenant
        crear_pagos: Si es True, crea los pagos faltantes. Si es False, solo reporta.
    
    Returns:
        dict con estadísticas
    """
    with tenant_context(tenant):
        stats = {
            'total_facturas_pagadas': 0,
            'facturas_sin_pago': 0,
            'facturas_corregidas': 0,
            'pagos_creados': 0,
            'errores': []
        }
        
        # Buscar facturas pagadas/parciales
        facturas_pagadas = Factura.objects.filter(
            estado__in=['pagada', 'parcial']
        ).exclude(monto_pagado=0)
        
        stats['total_facturas_pagadas'] = facturas_pagadas.count()
        
        for factura in facturas_pagadas:
            # Verificar si tiene pagos registrados
            pagos = PagoFactura.objects.filter(factura=factura)
            total_pagos = sum(p.monto for p in pagos)
            
            if not pagos.exists() and factura.monto_pagado > 0:
                # Factura pagada sin registro de pago
                stats['facturas_sin_pago'] += 1
                
                if crear_pagos:
                    try:
                        # Crear el pago faltante
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        numero_recibo = f"REC-{timestamp}-SYNC-{factura.id}"
                        
                        pago = PagoFactura.objects.create(
                            factura=factura,
                            monto=factura.monto_pagado,
                            metodo_pago=factura.metodo_pago if factura.metodo_pago else 'efectivo',
                            fecha_pago=factura.fecha_emision,  # Usar fecha de emisión
                            registrado_por=factura.creado_por if factura.creado_por else None,
                            numero_recibo=numero_recibo,
                            observaciones='Pago sincronizado automáticamente por script de mantenimiento'
                        )
                        stats['pagos_creados'] += 1
                        stats['facturas_corregidas'] += 1
                        
                    except Exception as e:
                        stats['errores'].append({
                            'factura': factura.numero_factura,
                            'error': str(e)
                        })
            
            elif total_pagos != factura.monto_pagado:
                # Desincronización entre pagos y monto_pagado
                if crear_pagos:
                    # Corregir el monto_pagado basándose en los pagos reales
                    factura.monto_pagado = total_pagos
                    factura.actualizar_estado()
                    factura.save()
                    stats['facturas_corregidas'] += 1
        
        return stats


def main():
    print(f"\n{'='*70}")
    print("SCRIPT DE MANTENIMIENTO - SINCRONIZACIÓN DE PAGOS")
    print(f"{'='*70}")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Obtener todos los tenants
    tenants = Tenant.objects.all()
    print(f"\nTenants a verificar: {tenants.count()}")
    
    # Modo de ejecución
    print(f"\n{'='*70}")
    print("MODO: SOLO VERIFICACIÓN (no crea pagos)")
    print("Para crear pagos automáticamente, ejecutar con --crear-pagos")
    print(f"{'='*70}")
    
    # Por ahora, solo verificar (cambiar crear_pagos=True para corregir automáticamente)
    import sys
    crear_pagos = '--crear-pagos' in sys.argv
    
    if crear_pagos:
        print("\n⚠️ MODO DE CORRECCIÓN ACTIVADO - Se crearán los pagos faltantes")
        input("Presiona ENTER para continuar o CTRL+C para cancelar...")
    
    total_stats = {
        'total_facturas_pagadas': 0,
        'facturas_sin_pago': 0,
        'facturas_corregidas': 0,
        'pagos_creados': 0,
        'errores': []
    }
    
    for tenant in tenants:
        print(f"\n{'='*70}")
        print(f"Verificando: {tenant.nombre} ({tenant.schema_name})")
        print(f"{'='*70}")
        
        stats = sincronizar_facturas_tenant(tenant, crear_pagos=crear_pagos)
        
        print(f"  Facturas pagadas/parciales: {stats['total_facturas_pagadas']}")
        print(f"  Facturas sin registro de pago: {stats['facturas_sin_pago']}")
        
        if crear_pagos:
            print(f"  Facturas corregidas: {stats['facturas_corregidas']}")
            print(f"  Pagos creados: {stats['pagos_creados']}")
            if stats['errores']:
                print(f"  Errores: {len(stats['errores'])}")
                for error in stats['errores']:
                    print(f"    - {error['factura']}: {error['error']}")
        
        # Acumular estadísticas
        for key in total_stats:
            if key == 'errores':
                total_stats[key].extend(stats[key])
            else:
                total_stats[key] += stats[key]
    
    # Resumen final
    print(f"\n{'='*70}")
    print("RESUMEN GENERAL")
    print(f"{'='*70}")
    print(f"Total facturas pagadas: {total_stats['total_facturas_pagadas']}")
    print(f"Facturas sin registro de pago: {total_stats['facturas_sin_pago']}")
    
    if crear_pagos:
        print(f"Facturas corregidas: {total_stats['facturas_corregidas']}")
        print(f"Pagos creados: {total_stats['pagos_creados']}")
        print(f"Errores: {len(total_stats['errores'])}")
        
        if total_stats['pagos_creados'] > 0:
            print(f"\n✅ Se crearon {total_stats['pagos_creados']} pagos faltantes")
    else:
        if total_stats['facturas_sin_pago'] > 0:
            print(f"\n⚠️ Se encontraron {total_stats['facturas_sin_pago']} facturas sin registro de pago")
            print("Ejecutar con --crear-pagos para corregir automáticamente")
        else:
            print("\n✅ Todas las facturas tienen registros de pago correctos")
    
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
