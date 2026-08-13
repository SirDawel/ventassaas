"""
Crear tenant respuestoalmanzar
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.tenant_models import Client, Domain

print("=" * 70)
print("CREACIÓN DE TENANT: respuestoalmanzar")
print("=" * 70)

# Verificar si ya existe
try:
    tenant = Client.objects.get(nombre_corto='respuestoalmanzar')
    print(f"⚠️  El tenant 'respuestoalmanzar' ya existe")
    print(f"   Nombre: {tenant.nombre}")
    print(f"   Schema: {tenant.schema_name}")
except Client.DoesNotExist:
    # Crear el tenant
    print("\n➤ Creando tenant...")
    tenant = Client(
        schema_name='respuestoalmanzar',
        nombre='Repuesto Almanzar',
        nombre_corto='respuestoalmanzar',
        email_contacto='info@respuestoalmanzar.com',
        telefono='',
        direccion='',
        plan='premium',
        max_usuarios=100,
        activo=True,
        fecha_vencimiento=None
    )
    tenant.save()
    print(f"✅ Tenant creado: {tenant.nombre}")

# Crear dominios
print("\n" + "=" * 70)
print("DOMINIOS")
print("=" * 70)

dominios = [
    ('respuestoalmanzar.localhost', True),
    ('respuestoalmanzar.localhost:8001', False),
]

for domain_name, is_primary in dominios:
    domain, created = Domain.objects.get_or_create(
        domain=domain_name,
        defaults={
            'tenant': tenant,
            'is_primary': is_primary
        }
    )
    
    if created:
        print(f"✅ Dominio '{domain_name}' creado")
    else:
        print(f"ℹ️  Dominio '{domain_name}' ya existe")

print("\n" + "=" * 70)
print("¡COMPLETADO!")
print("=" * 70)
print("\n✅ Ahora puedes acceder en:")
print("   - http://respuestoalmanzar.localhost:8001/login/")
print("\n⚠️  NOTA: Necesitas agregar esto a tu archivo hosts:")
print("   127.0.0.1  respuestoalmanzar.localhost")
print("\n" + "=" * 70)
