#!/usr/bin/env python
"""
Script para eliminar el tenant brevo corrupto
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.models import Client, Domain
from django.db import connection

def eliminar_tenant_brevo():
    """Elimina el tenant brevo y su schema"""
    try:
        # Buscar tenant brevo
        tenant = Client.objects.filter(schema_name='brevo').first()
        
        if not tenant:
            print("❌ Tenant 'brevo' no encontrado en la base de datos")
            return
        
        print(f"✅ Tenant encontrado: {tenant.nombre} (schema: {tenant.schema_name})")
        print(f"   Dominios: {[d.domain for d in tenant.domains.all()]}")
        
        # Eliminar el schema si existe
        schema_name = tenant.schema_name
        with connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            print(f"✅ Schema '{schema_name}' eliminado de PostgreSQL")
        
        # Eliminar dominios asociados
        Domain.objects.filter(tenant=tenant).delete()
        print("✅ Dominios eliminados")
        
        # Eliminar tenant
        tenant.delete()
        print("✅ Tenant 'brevo' eliminado completamente")
        
    except Exception as e:
        print(f"❌ Error al eliminar tenant: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("ELIMINAR TENANT BREVO CORRUPTO")
    print("=" * 60)
    
    confirmar = input("\n⚠️  ¿Estás seguro de eliminar el tenant 'brevo'? (si/no): ")
    
    if confirmar.lower() == 'si':
        eliminar_tenant_brevo()
    else:
        print("❌ Operación cancelada")
