#!/usr/bin/env python
"""
Script para listar todos los tenants y verificar sus schemas
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

def verificar_schemas_postgresql():
    """Verifica qué schemas existen en PostgreSQL"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        return [row[0] for row in cursor.fetchall()]

def listar_tenants():
    """Lista todos los tenants y sus schemas"""
    print("\n" + "=" * 80)
    print("TENANTS EN BASE DE DATOS")
    print("=" * 80)
    
    # Listar tenants de Django
    tenants = Client.objects.all().order_by('schema_name')
    
    print(f"\nTotal tenants en Django: {tenants.count()}")
    print("-" * 80)
    
    for tenant in tenants:
        dominios = [d.domain for d in tenant.domains.all()]
        activo = "✅ Activo" if tenant.activo else "❌ Inactivo"
        print(f"\nSchema: {tenant.schema_name}")
        print(f"  Nombre: {tenant.nombre}")
        print(f"  Estado: {activo}")
        print(f"  Dominios: {', '.join(dominios)}")
        print(f"  Creado: {tenant.fecha_creacion}")
    
    # Verificar schemas en PostgreSQL
    print("\n" + "=" * 80)
    print("SCHEMAS EN POSTGRESQL")
    print("=" * 80)
    
    schemas_pg = verificar_schemas_postgresql()
    print(f"\nTotal schemas: {len(schemas_pg)}")
    print("-" * 80)
    
    for schema in schemas_pg:
        # Verificar si existe tenant asociado
        existe_tenant = Client.objects.filter(schema_name=schema).exists()
        if existe_tenant:
            print(f"✅ {schema} (tiene tenant)")
        else:
            print(f"⚠️  {schema} (huérfano - sin tenant)")
    
    # Verificar tenants sin schema
    print("\n" + "=" * 80)
    print("TENANTS SIN SCHEMA EN POSTGRESQL")
    print("=" * 80)
    
    tenants_sin_schema = []
    for tenant in tenants:
        if tenant.schema_name not in schemas_pg:
            tenants_sin_schema.append(tenant)
            print(f"❌ {tenant.schema_name} - {tenant.nombre}")
    
    if not tenants_sin_schema:
        print("✅ Todos los tenants tienen su schema")
    
    return tenants, schemas_pg, tenants_sin_schema

if __name__ == '__main__':
    try:
        listar_tenants()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
