#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para resetear contraseña del administrador en tenant CEO
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import tenant_context
from ventasweb.models import Client, CustomUser

# Obtener tenant CEO
tenant = Client.objects.filter(schema_name='ceo').first()
print(f"✅ Tenant: {tenant.nombre} ({tenant.schema_name})")

# Resetear contraseña
with tenant_context(tenant):
    admin = CustomUser.objects.filter(
        rol='Administrador',
        is_active=True
    ).first()
    
    if admin:
        nueva_password = 'admin123'
        admin.set_password(nueva_password)
        admin.save()
        
        print(f"\n✅ Contraseña actualizada para:")
        print(f"   Email: {admin.email}")
        print(f"   Nueva contraseña: {nueva_password}")
        print(f"   Rol: {admin.rol}")
        print(f"\n🔐 Puedes iniciar sesión en http://ceo.localhost:8000/login/")
    else:
        print("❌ No se encontró usuario administrador")
