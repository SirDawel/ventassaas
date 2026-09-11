#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para diagnosticar por qué no se muestran los planes
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection
from django_tenants.utils import get_public_schema_name, tenant_context
from ventasweb.models import Client, Plan, Suscripcion, CustomUser

print("🔍 Diagnóstico de Planes de Suscripción\n")
print("=" * 60)

# 1. Verificar planes en schema public
print("\n1️⃣ Verificando planes en schema PUBLIC:")
connection.set_schema(get_public_schema_name())
planes = Plan.objects.filter(activo=True).order_by('orden')
print(f"   Total de planes activos: {planes.count()}")
for plan in planes:
    print(f"   - {plan.nombre}: ${plan.precio_mensual}/mes (Orden: {plan.orden})")

# 2. Verificar tenant CEO
print("\n2️⃣ Verificando tenant CEO:")
tenant = Client.objects.filter(schema_name='ceo').first()
if tenant:
    print(f"   ✅ Tenant encontrado: {tenant.nombre}")
    print(f"   Schema: {tenant.schema_name}")
    
    # 3. Verificar suscripción del tenant
    print("\n3️⃣ Verificando suscripción:")
    suscripcion = Suscripcion.objects.filter(tenant=tenant).first()
    if suscripcion:
        print(f"   ✅ Suscripción encontrada:")
        print(f"      Plan: {suscripcion.plan.nombre}")
        print(f"      Estado: {suscripcion.estado}")
        print(f"      Periodo: {suscripcion.periodo}")
    else:
        print(f"   ⚠️  No hay suscripción para este tenant")
    
    # 4. Contar usuarios del tenant
    print("\n4️⃣ Verificando usuarios en tenant:")
    with tenant_context(tenant):
        total_usuarios = CustomUser.objects.filter(is_active=True).count()
        print(f"   Total de usuarios activos: {total_usuarios}")
        
        admins = CustomUser.objects.filter(is_active=True, rol='Administrador')
        print(f"   Administradores: {admins.count()}")
        for admin in admins:
            print(f"      - {admin.email}")
else:
    print(f"   ❌ Tenant 'ceo' no encontrado")

print("\n" + "=" * 60)
print("✅ Diagnóstico completado\n")
