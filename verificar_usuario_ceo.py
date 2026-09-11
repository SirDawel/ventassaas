#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar usuarios en el tenant CEO
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

if not tenant:
    print("❌ Tenant 'ceo' no encontrado")
    print("\nTenants disponibles:")
    for t in Client.objects.all():
        print(f"  - {t.schema_name}: {t.nombre}")
    sys.exit(1)

print(f"✅ Tenant encontrado: {tenant.nombre} ({tenant.schema_name})")
print(f"   Dominio: {tenant.schema_name}.localhost:8000")
print()

# Verificar usuarios
with tenant_context(tenant):
    usuarios = CustomUser.objects.filter(is_active=True)
    
    if not usuarios.exists():
        print("❌ No hay usuarios activos en este tenant")
        print("\nCreando usuario administrador de prueba...")
        
        admin = CustomUser.objects.create_superuser(
            email='admin@ceo.com',
            password='admin123',
            rol='Administrador',
            nombre='Administrador',
            apellidos='CEO'
        )
        print(f"✅ Usuario creado:")
        print(f"   Email: admin@ceo.com")
        print(f"   Contraseña: admin123")
    else:
        print(f"✅ Usuarios activos encontrados: {usuarios.count()}")
        print()
        for user in usuarios[:5]:  # Mostrar máximo 5
            print(f"  - {user.email} - {user.rol}")
            if user.check_password('admin123'):
                print(f"    ✅ Contraseña es: admin123")
            elif user.check_password('123456'):
                print(f"    ✅ Contraseña es: 123456")

