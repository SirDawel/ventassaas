"""
Agregar dominio 127.0.0.1 al tenant público
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.tenant_models import Client, Domain

# Obtener tenant público
public_tenant = Client.objects.get(schema_name='public')

# Agregar dominio 127.0.0.1
domain_ip, created = Domain.objects.get_or_create(
    domain='127.0.0.1',
    defaults={
        'tenant': public_tenant,
        'is_primary': False  # localhost es primary
    }
)

if created:
    print(f"✅ Dominio 127.0.0.1 creado para tenant público")
else:
    print(f"ℹ️ Dominio 127.0.0.1 ya existe")

print("\n📋 Dominios del tenant público:")
for domain in Domain.objects.filter(tenant=public_tenant):
    print(f"  - {domain.domain} (primary: {domain.is_primary})")
