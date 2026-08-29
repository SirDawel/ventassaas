#!/usr/bin/env python
"""
Script para actualizar tenants existentes con los nuevos campos de planes
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.tenant_models import Client
from django.utils import timezone
from datetime import timedelta

def actualizar_tenants():
    print("\n" + "=" * 80)
    print("🔄 ACTUALIZANDO TENANTS EXISTENTES CON LÍMITES DE PLANES")
    print("=" * 80)
    
    tenants = Client.objects.all().order_by('nombre_corto')
    
    print(f"\nTotal tenants: {tenants.count()}\n")
    
    for tenant in tenants:
        print(f"\n{'─' * 60}")
        print(f"📦 Tenant: {tenant.nombre} (schema: {tenant.schema_name})")
        print(f"   Plan actual: {tenant.get_plan_display()}")
        
        # Preguntar qué plan asignar si no está definido correctamente
        if tenant.plan not in ['gratis', 'basico', 'plus', 'pro']:
            print(f"\n   ⚠️  Plan '{tenant.plan}' no reconocido")
            print(f"   Opciones:")
            print(f"   1. gratis - $0/mes (trial 30 días)")
            print(f"   2. basico - $5/mes")
            print(f"   3. plus - $12/mes")
            print(f"   4. pro - $25/mes")
            
            opcion = input(f"   Selecciona plan para {tenant.nombre} (1-4, Enter para 'basico'): ").strip()
            
            planes = {
                '1': 'gratis',
                '2': 'basico',
                '3': 'plus',
                '4': 'pro',
                '': 'basico'
            }
            
            nuevo_plan = planes.get(opcion, 'basico')
            tenant.plan = nuevo_plan
            print(f"   ✅ Plan cambiado a: {nuevo_plan}")
        
        # Configurar límites según el plan
        print(f"   🔧 Configurando límites...")
        tenant.configurar_limites_plan()
        
        # Si no está activo, activarlo
        if not tenant.activo:
            tenant.activo = True
            print(f"   ✅ Tenant activado")
        
        # Guardar
        tenant.save()
        
        # Mostrar configuración
        print(f"\n   📊 Configuración actualizada:")
        print(f"      Plan: {tenant.get_plan_display()}")
        print(f"      Precio: ${tenant.precio_mensual}/mes")
        print(f"      Usuarios: {tenant.contar_usuarios()}/{tenant.max_usuarios}")
        print(f"      Facturas/mes: {tenant.facturas_mes_actual}/{tenant.max_facturas_mes if tenant.max_facturas_mes < 99999 else '∞'}")
        print(f"      Sucursales: {tenant.max_sucursales}")
        print(f"      Reportes avanzados: {'✅' if tenant.reportes_avanzados else '❌'}")
        print(f"      Facturación electrónica: {'✅' if tenant.facturacion_electronica else '❌'}")
        print(f"      Activo: {'✅' if tenant.activo else '❌'}")
        if tenant.fecha_vencimiento:
            print(f"      Vence: {tenant.fecha_vencimiento.strftime('%d/%m/%Y')}")
        if tenant.proximo_pago:
            print(f"      Próximo pago: {tenant.proximo_pago.strftime('%d/%m/%Y')}")
    
    print("\n" + "=" * 80)
    print("✅ TODOS LOS TENANTS ACTUALIZADOS")
    print("=" * 80)
    
    # Resumen
    print("\n📊 RESUMEN POR PLAN:")
    for plan_code, plan_name in [('gratis', 'Gratis'), ('basico', 'Básico'), ('plus', 'Plus'), ('pro', 'Pro')]:
        count = Client.objects.filter(plan=plan_code).count()
        if count > 0:
            plan_obj = Client.objects.filter(plan=plan_code).first()
            precio = plan_obj.precio_mensual if plan_obj else 0
            print(f"   {plan_name}: {count} tenants (${precio}/mes cada uno)")
    
    # Calcular MRR (Monthly Recurring Revenue)
    from django.db.models import Sum
    mrr = Client.objects.aggregate(total=Sum('precio_mensual'))['total'] or 0
    print(f"\n💰 MRR (Ingreso Mensual Recurrente): ${mrr:.2f}/mes")
    print(f"💰 ARR (Ingreso Anual Recurrente): ${mrr * 12:.2f}/año")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    try:
        actualizar_tenants()
    except KeyboardInterrupt:
        print("\n\n✋ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
