# -*- coding: utf-8 -*-
"""Verificar planes en la base de datos"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection
from django_tenants.utils import get_public_schema_name
from escuelaweb.models import Plan, Suscripcion

# Cambiar al schema público
connection.set_schema(get_public_schema_name())

print("=" * 60)
print("VERIFICACIÓN DE PLANES Y SUSCRIPCIONES")
print("=" * 60)

# Verificar planes
planes = Plan.objects.all()
print(f"\n✓ Planes encontrados: {planes.count()}")
for plan in planes:
    print(f"  - ID: {plan.id} | {plan.nombre} | {plan.tipo} | ${plan.precio_mensual}/mes")

# Verificar suscripciones
suscripciones = Suscripcion.objects.all()
print(f"\n✓ Suscripciones encontradas: {suscripciones.count()}")
for suscripcion in suscripciones:
    try:
        tenant_nombre = suscripcion.tenant.nombre if suscripcion.tenant else "N/A"
        plan_nombre = suscripcion.plan.nombre if suscripcion.plan else "SIN PLAN"
        print(f"  - Tenant: {tenant_nombre} | Plan: {plan_nombre} | Estado: {suscripcion.estado}")
    except Exception as e:
        print(f"  - ERROR al leer suscripción ID {suscripcion.id}: {e}")

print("\n" + "=" * 60)
