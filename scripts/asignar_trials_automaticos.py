#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para asignar suscripciones trial automáticas a escuelas existentes
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django_tenants.utils import get_tenant_model
from escuelaweb.models import Plan, Suscripcion, CustomUser


def contar_usuarios_tenant(tenant):
    """Contar usuarios activos en un tenant"""
    from django.db import connection
    
    # Cambiar al schema del tenant
    connection.set_tenant(tenant)
    
    try:
        # Contar usuarios activos
        total_usuarios = CustomUser.objects.filter(is_active=True).count()
        estudiantes = CustomUser.objects.filter(is_active=True, rol='estudiante').count()
        
        return total_usuarios, estudiantes
    except Exception as e:
        print(f"   ⚠️  Error contando usuarios: {e}")
        return 0, 0
    finally:
        # Volver al schema public
        from django_tenants.utils import get_public_schema_name
        connection.set_schema(get_public_schema_name())


def seleccionar_plan_apropiado(total_usuarios, estudiantes):
    """Seleccionar el plan más apropiado según la cantidad de usuarios"""
    from django.db import connection
    from django_tenants.utils import get_public_schema_name
    
    # Asegurar que estamos en el schema public
    connection.set_schema(get_public_schema_name())
    
    # Intentar obtener planes en orden
    planes = Plan.objects.filter(activo=True).order_by('orden')
    
    if not planes.exists():
        print("❌ Error: No hay planes disponibles. Ejecuta crear_planes_suscripcion.py primero.")
        return None
    
    # Seleccionar plan según usuarios
    if total_usuarios <= 50:
        plan = planes.filter(tipo='BASICO').first()
    elif total_usuarios <= 200:
        plan = planes.filter(tipo='ESTANDAR').first()
    elif total_usuarios <= 500:
        plan = planes.filter(tipo='PROFESIONAL').first()
    else:
        plan = planes.filter(tipo='EMPRESARIAL').first()
    
    # Si no se encuentra el plan específico, usar el primer plan disponible
    if not plan:
        plan = planes.first()
    
    return plan


def asignar_trials():
    """Asignar trials automáticos a escuelas sin suscripción"""
    from django.db import connection
    from django_tenants.utils import get_public_schema_name
    
    print("🎯 Asignando suscripciones trial a escuelas existentes...")
    print("=" * 70)
    
    # Asegurar que estamos en el schema public
    connection.set_schema(get_public_schema_name())
    
    Client = get_tenant_model()
    
    # Obtener todos los tenants excepto 'public'
    tenants = Client.objects.exclude(schema_name='public').order_by('nombre')
    
    total_tenants = tenants.count()
    asignados = 0
    ya_tienen = 0
    
    print(f"📊 Total de escuelas encontradas: {total_tenants}\n")
    
    for tenant in tenants:
        print(f"🏫 Procesando: {tenant.nombre} ({tenant.schema_name})")
        
        # Verificar si ya tiene suscripción
        suscripcion_existente = Suscripcion.objects.filter(tenant=tenant).first()
        
        if suscripcion_existente:
            print(f"   ✓ Ya tiene suscripción: {suscripcion_existente.plan.nombre} ({suscripcion_existente.get_estado_display()})")
            ya_tienen += 1
        else:
            # Contar usuarios del tenant
            total_usuarios, estudiantes = contar_usuarios_tenant(tenant)
            print(f"   👥 Usuarios: {total_usuarios} (Estudiantes: {estudiantes})")
            
            # Seleccionar plan apropiado
            plan = seleccionar_plan_apropiado(total_usuarios, estudiantes)
            
            if not plan:
                print(f"   ❌ No se pudo asignar plan")
                continue
            
            # Crear suscripción trial
            fecha_inicio = datetime.now().date()
            fecha_fin_trial = fecha_inicio + timedelta(days=30)
            
            suscripcion = Suscripcion.objects.create(
                tenant=tenant,
                plan=plan,
                estado='TRIAL',
                periodo='MENSUAL',
                fecha_inicio=fecha_inicio,
                fecha_fin_trial=fecha_fin_trial,
                fecha_proximo_pago=fecha_fin_trial,
                auto_renovacion=False,
                notas=f'Trial automático asignado el {fecha_inicio.strftime("%d/%m/%Y")}. '
                      f'Usuarios actuales: {total_usuarios}, Estudiantes: {estudiantes}'
            )
            
            print(f"   ✅ Suscripción trial creada: {plan.nombre}")
            print(f"   📅 Trial expira: {fecha_fin_trial.strftime('%d/%m/%Y')}")
            print(f"   💰 Precio al finalizar trial: ${plan.precio_mensual}/mes")
            asignados += 1
        
        print("-" * 70)
    
    print("\n✨ Proceso completado!")
    print(f"📊 Resumen:")
    print(f"   • Total escuelas: {total_tenants}")
    print(f"   • Suscripciones trial creadas: {asignados}")
    print(f"   • Ya tenían suscripción: {ya_tienen}")
    
    if asignados > 0:
        print(f"\n💡 Las escuelas tienen 30 días de trial para probar el sistema.")
        print(f"   Después deberán configurar un método de pago para continuar.")


if __name__ == '__main__':
    try:
        asignar_trials()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
