#!/usr/bin/env python
"""
Script para detectar y eliminar automáticamente tenants corruptos
(tenants que existen en la BD pero su schema no existe en PostgreSQL)
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

def verificar_schema_existe(schema_name):
    """Verifica si un schema existe en PostgreSQL"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            );
        """, [schema_name])
        return cursor.fetchone()[0]

def listar_schemas_postgresql():
    """Lista todos los schemas en PostgreSQL"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        return [row[0] for row in cursor.fetchall()]

def eliminar_tenant_corrupto(tenant):
    """Elimina un tenant corrupto de Django y PostgreSQL"""
    try:
        schema_name = tenant.schema_name
        
        # Eliminar el schema de PostgreSQL si existe (aunque sea inválido)
        with connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            print(f"   ✅ Schema '{schema_name}' eliminado de PostgreSQL")
        
        # Eliminar dominios asociados
        dominios = list(tenant.domains.all())
        for dominio in dominios:
            print(f"   🗑️  Eliminando dominio: {dominio.domain}")
            dominio.delete()
        
        # Eliminar tenant
        tenant_nombre = tenant.nombre
        tenant.delete()
        print(f"   ✅ Tenant '{tenant_nombre}' eliminado de Django")
        
        return True
    except Exception as e:
        print(f"   ❌ Error al eliminar tenant: {e}")
        return False

def main():
    print("=" * 80)
    print("DETECTAR Y LIMPIAR TENANTS CORRUPTOS")
    print("=" * 80)
    
    # Obtener todos los tenants de Django
    tenants = Client.objects.all().order_by('schema_name')
    schemas_pg = listar_schemas_postgresql()
    
    print(f"\n📊 Total tenants en Django: {tenants.count()}")
    print(f"📊 Total schemas en PostgreSQL: {len(schemas_pg)}")
    print(f"\n🔍 Verificando integridad de tenants...\n")
    
    tenants_corruptos = []
    tenants_validos = []
    
    for tenant in tenants:
        schema_existe = verificar_schema_existe(tenant.schema_name)
        
        if schema_existe:
            tenants_validos.append(tenant)
            print(f"✅ {tenant.schema_name:<20} - {tenant.nombre} (OK)")
        else:
            tenants_corruptos.append(tenant)
            dominios = [d.domain for d in tenant.domains.all()]
            print(f"❌ {tenant.schema_name:<20} - {tenant.nombre} (CORRUPTO)")
            print(f"   Dominios: {', '.join(dominios) if dominios else 'ninguno'}")
    
    # Resumen
    print("\n" + "=" * 80)
    print(f"✅ Tenants válidos: {len(tenants_validos)}")
    print(f"❌ Tenants corruptos: {len(tenants_corruptos)}")
    print("=" * 80)
    
    if not tenants_corruptos:
        print("\n🎉 No se encontraron tenants corruptos. Todo está bien.")
        return
    
    # Preguntar si eliminar
    print("\n⚠️  TENANTS CORRUPTOS ENCONTRADOS:")
    for tenant in tenants_corruptos:
        print(f"   - {tenant.schema_name} ({tenant.nombre})")
    
    print("\n¿Deseas eliminar estos tenants corruptos?")
    confirmar = input("Escribe 'ELIMINAR' para confirmar: ")
    
    if confirmar == 'ELIMINAR':
        print("\n🗑️  Eliminando tenants corruptos...\n")
        
        eliminados = 0
        for tenant in tenants_corruptos:
            print(f"Procesando: {tenant.schema_name} ({tenant.nombre})")
            if eliminar_tenant_corrupto(tenant):
                eliminados += 1
            print()
        
        print("=" * 80)
        print(f"✅ Eliminados exitosamente: {eliminados}/{len(tenants_corruptos)}")
        print("=" * 80)
        print("\n✅ Limpieza completada. Ahora puedes ejecutar:")
        print("   python manage.py migrate_schemas")
    else:
        print("\n❌ Operación cancelada. No se eliminó nada.")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
