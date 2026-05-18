#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear los planes de suscripción iniciales
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import Plan


def crear_planes():
    """Crear los 4 planes de suscripción base"""
    
    planes = [
        {
            'nombre': 'Plan Básico',
            'tipo': 'BASICO',
            'descripcion': 'Ideal para escuelas pequeñas con hasta 50 usuarios. Incluye funcionalidades esenciales.',
            'precio_mensual': 29.00,
            'precio_anual': 290.00,  # 10 meses (2 meses gratis)
            'max_usuarios': 50,
            'max_estudiantes': 200,
            'permite_reportes_avanzados': False,
            'permite_integracion_api': False,
            'permite_multiples_sedes': False,
            'soporte_prioritario': False,
            'orden': 1
        },
        {
            'nombre': 'Plan Estándar',
            'tipo': 'ESTANDAR',
            'descripcion': 'Para escuelas medianas con hasta 200 usuarios. Incluye reportes avanzados.',
            'precio_mensual': 79.00,
            'precio_anual': 790.00,  # 10 meses (2 meses gratis)
            'max_usuarios': 200,
            'max_estudiantes': 800,
            'permite_reportes_avanzados': True,
            'permite_integracion_api': False,
            'permite_multiples_sedes': False,
            'soporte_prioritario': False,
            'orden': 2
        },
        {
            'nombre': 'Plan Profesional',
            'tipo': 'PROFESIONAL',
            'descripcion': 'Para escuelas grandes con hasta 500 usuarios. Incluye API y múltiples sedes.',
            'precio_mensual': 149.00,
            'precio_anual': 1490.00,  # 10 meses (2 meses gratis)
            'max_usuarios': 500,
            'max_estudiantes': 2000,
            'permite_reportes_avanzados': True,
            'permite_integracion_api': True,
            'permite_multiples_sedes': True,
            'soporte_prioritario': False,
            'orden': 3
        },
        {
            'nombre': 'Plan Empresarial',
            'tipo': 'EMPRESARIAL',
            'descripcion': 'Sin límites de usuarios. Todas las funcionalidades con soporte prioritario.',
            'precio_mensual': 299.00,
            'precio_anual': 2990.00,  # 10 meses (2 meses gratis)
            'max_usuarios': 999999,  # Sin límite práctico
            'max_estudiantes': 999999,  # Sin límite práctico
            'permite_reportes_avanzados': True,
            'permite_integracion_api': True,
            'permite_multiples_sedes': True,
            'soporte_prioritario': True,
            'orden': 4
        }
    ]
    
    print("🎯 Creando planes de suscripción...")
    print("=" * 60)
    
    for plan_data in planes:
        # Verificar si el plan ya existe
        plan_existente = Plan.objects.filter(tipo=plan_data['tipo']).first()
        
        if plan_existente:
            print(f"⚠️  Plan {plan_data['nombre']} ya existe. Actualizando...")
            # Actualizar el plan existente
            for key, value in plan_data.items():
                setattr(plan_existente, key, value)
            plan_existente.activo = True
            plan_existente.save()
            print(f"✅ Plan {plan_data['nombre']} actualizado")
        else:
            # Crear nuevo plan
            plan = Plan.objects.create(**plan_data, activo=True)
            print(f"✅ Plan {plan_data['nombre']} creado exitosamente")
        
        print(f"   💰 Precio mensual: ${plan_data['precio_mensual']}")
        print(f"   💰 Precio anual: ${plan_data['precio_anual']}")
        print(f"   👥 Máx. usuarios: {plan_data['max_usuarios']}")
        print(f"   🎓 Máx. estudiantes: {plan_data['max_estudiantes']}")
        print("-" * 60)
    
    print("\n✨ Proceso completado exitosamente!")
    print(f"📊 Total de planes activos: {Plan.objects.filter(activo=True).count()}")
    

if __name__ == '__main__':
    try:
        crear_planes()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
