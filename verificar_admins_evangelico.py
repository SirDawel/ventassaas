# -*- coding: utf-8 -*-
"""Verificar usuarios administradores en evangelico"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection
from django_tenants.utils import get_tenant_model
from ventasweb.models import CustomUser

# Obtener tenant evangelico
Client = get_tenant_model()
try:
    tenant = Client.objects.get(schema_name='evangelico')
    print(f"\n✓ Tenant encontrado: {tenant.nombre}")
    
    # Cambiar al schema del tenant
    connection.set_schema(tenant.schema_name)
    
    # Buscar usuarios staff
    usuarios_staff = CustomUser.objects.filter(is_staff=True)
    print(f"\n✓ Usuarios administradores (staff) en evangelico: {usuarios_staff.count()}")
    
    for user in usuarios_staff:
        print(f"  - Email: {user.email}")
        print(f"    Nombre: {user.first_name} {user.last_name}")
        print(f"    Rol: {user.rol}")
        print(f"    is_staff: {user.is_staff}")
        print(f"    is_superuser: {user.is_superuser}")
        print(f"    Activo: {user.is_active}")
        print()
    
    # Si no hay usuarios staff, listar todos los usuarios activos
    if usuarios_staff.count() == 0:
        print("⚠️  No hay usuarios staff. Usuarios activos disponibles:")
        usuarios_activos = CustomUser.objects.filter(is_active=True)[:10]
        for user in usuarios_activos:
            print(f"  - {user.email} (Rol: {user.rol})")
        
except Client.DoesNotExist:
    print("❌ Tenant 'evangelico' no encontrado")
