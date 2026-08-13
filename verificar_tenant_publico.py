"""
Verificar y crear tenant público si no existe
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.tenant_models import Client, Domain

print("=" * 70)
print("VERIFICACIÓN Y CREACIÓN DE TENANT PÚBLICO")
print("=" * 70)

# Verificar si existe tenant público
try:
    public_tenant = Client.objects.get(schema_name='public')
    print(f"✅ Tenant público ya existe: {public_tenant.nombre}")
    print(f"   Schema: {public_tenant.schema_name}")
    print(f"   Email: {public_tenant.email_contacto}")
    print(f"   Activo: {public_tenant.activo}")
except Client.DoesNotExist:
    print("⚠️ Tenant público NO existe. Creando...")
    
    public_tenant = Client(
        schema_name='public',
        nombre='Sistema de Ventas - Dominio Público',
        nombre_corto='public',
        email_contacto='admin@ventassistema.com',
        telefono='',
        direccion='',
        plan='enterprise',
        max_usuarios=99999,
        activo=True,
        fecha_vencimiento=None
    )
    public_tenant.save()
    print(f"✅ Tenant público creado: {public_tenant.nombre}")

print("\n" + "=" * 70)
print("DOMINIOS DEL TENANT PÚBLICO")
print("=" * 70)

# Verificar dominios
dominios_existentes = Domain.objects.filter(tenant=public_tenant)
print(f"\nDominios actuales ({dominios_existentes.count()}):")
for domain in dominios_existentes:
    print(f"  - {domain.domain} (primary: {domain.is_primary})")

# Crear dominios necesarios
dominios_requeridos = [
    ('localhost', True),
    ('127.0.0.1', False),
]

print("\n" + "-" * 70)
print("Verificando dominios requeridos...")
print("-" * 70)

for domain_name, is_primary in dominios_requeridos:
    domain, created = Domain.objects.get_or_create(
        domain=domain_name,
        defaults={
            'tenant': public_tenant,
            'is_primary': is_primary
        }
    )
    
    if created:
        print(f"✅ Dominio '{domain_name}' creado (primary: {is_primary})")
    else:
        # Actualizar tenant si es necesario
        if domain.tenant != public_tenant:
            domain.tenant = public_tenant
            domain.save()
            print(f"🔄 Dominio '{domain_name}' actualizado al tenant público")
        else:
            print(f"ℹ️  Dominio '{domain_name}' ya existe (primary: {domain.is_primary})")

print("\n" + "=" * 70)
print("CONFIGURACIÓN COMPLETADA")
print("=" * 70)
print("\n✅ El sistema está listo para funcionar en:")
print("   - http://localhost:8001")
print("   - http://127.0.0.1:8001")
print("\n" + "=" * 70)
