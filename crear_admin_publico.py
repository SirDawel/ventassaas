"""
Crear usuario admin en el tenant público para poder hacer login desde 127.0.0.1
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from ventasweb.tenant_models import Client

User = get_user_model()

# Obtener el tenant público
tenant = Client.objects.get(schema_name='public')

print(f"\n✅ Creando usuario en tenant público: {tenant.nombre}")

with schema_context(tenant.schema_name):
    admin_user, created = User.objects.get_or_create(
        email='admin@admin.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'Sistema',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'rol': 'Administrador'
        }
    )
    
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✅ Usuario creado: admin@admin.com")
    else:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✅ Password actualizado: admin@admin.com")
    
    print(f"🔑 Password: admin123")
    print(f"🌐 URL: http://127.0.0.1:8000/login/\n")
