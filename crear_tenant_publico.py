"""
Crear tenant público (public schema) requerido por django-tenants
Este tenant siempre debe existir
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.tenant_models import Client, Domain

# Crear o actualizar tenant público
public_tenant, created = Client.objects.get_or_create(
    schema_name='public',
    defaults={
        'nombre': 'Dominio Público',
        'nombre_corto': 'public',
        'email_contacto': 'soporte@sistemaescolar.com',
        'telefono': '',
        'direccion': '',
        'plan': 'enterprise',
        'max_usuarios': 99999,
        'activo': True,
        'fecha_vencimiento': None  # Sin vencimiento
    }
)

if created:
    print(f"✅ Tenant público creado: {public_tenant.nombre} (schema: {public_tenant.schema_name})")
else:
    print(f"ℹ️ Tenant público ya existe: {public_tenant.nombre} (schema: {public_tenant.schema_name})")

# Crear dominios para el tenant público
# Para desarrollo (localhost)
domain_local, created = Domain.objects.get_or_create(
    domain='localhost',
    defaults={
        'tenant': public_tenant,
        'is_primary': True
    }
)

if created:
    print(f"✅ Dominio localhost creado para tenant público")
else:
    print(f"ℹ️ Dominio localhost ya existe")

# Para producción (si aplica)
domain_prod, created = Domain.objects.get_or_create(
    domain='escuelaenlinea.com',
    defaults={
        'tenant': public_tenant,
        'is_primary': False
    }
)

if created:
    print(f"✅ Dominio escuelaenlinea.com creado para tenant público")
else:
    print(f"ℹ️ Dominio escuelaenlinea.com ya existe")

print("\n✅ Configuración del tenant público completada")
print("Ahora puedes registrar nuevas escuelas desde http://localhost:8000/registrar-escuela/")
