#!/usr/bin/env python
"""
Script para diagnosticar problemas de subdominios en producción
Verifica tenants, dominios y configuración
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from ventasweb.tenant_models import Client, Domain
from django.conf import settings
from django.db import connection

def diagnosticar():
    print("\n" + "=" * 80)
    print("🔍 DIAGNÓSTICO DE SUBDOMINIOS - SISTEMA MULTITENANT")
    print("=" * 80)
    
    # 1. Verificar configuración de Django
    print("\n📋 1. CONFIGURACIÓN DE DJANGO")
    print("-" * 80)
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
    
    # Verificar si permite subdominios
    permite_subdominios = any(
        host.startswith('.') or host.startswith('*') 
        for host in settings.ALLOWED_HOSTS
    )
    if permite_subdominios:
        print("✅ ALLOWED_HOSTS permite subdominios")
    else:
        print("❌ ALLOWED_HOSTS NO permite subdominios")
        print("   Debe incluir: .misventasflash.com o *.misventasflash.com")
    
    # 2. Verificar base de datos
    print("\n📊 2. BASE DE DATOS")
    print("-" * 80)
    print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
    print(f"Nombre: {settings.DATABASES['default']['NAME']}")
    print(f"Host: {settings.DATABASES['default']['HOST']}")
    
    # 3. Listar todos los tenants
    print("\n🏢 3. TENANTS REGISTRADOS")
    print("-" * 80)
    
    tenants = Client.objects.all().order_by('nombre_corto')
    
    if not tenants.exists():
        print("❌ NO hay tenants registrados")
        print("   Debes crear al menos un tenant público y tus tenants de negocio")
        return
    
    print(f"Total tenants: {tenants.count()}\n")
    
    for tenant in tenants:
        print(f"\n{'─' * 60}")
        print(f"Schema: {tenant.schema_name}")
        print(f"Nombre: {tenant.nombre}")
        print(f"Nombre corto: {tenant.nombre_corto}")
        print(f"Plan: {tenant.plan}")
        print(f"Activo: {'✅ Sí' if tenant.activo else '❌ No'}")
        print(f"Fecha creación: {tenant.fecha_creacion}")
        
        # Listar dominios asociados
        dominios = Domain.objects.filter(tenant=tenant)
        if dominios.exists():
            print(f"Dominios ({dominios.count()}):")
            for dom in dominios:
                primario = "⭐ " if dom.is_primary else "   "
                print(f"  {primario}{dom.domain}")
        else:
            print("❌ Sin dominios configurados")
    
    # 4. Verificar schemas en PostgreSQL
    print("\n" + "=" * 80)
    print("🗄️  4. SCHEMAS EN POSTGRESQL")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        schemas = [row[0] for row in cursor.fetchall()]
    
    print(f"Total schemas: {len(schemas)}\n")
    for schema in schemas:
        tenant_existe = Client.objects.filter(schema_name=schema).exists()
        if tenant_existe:
            print(f"✅ {schema}")
        else:
            print(f"⚠️  {schema} (huérfano - sin tenant)")
    
    # 5. Verificar dominio específico
    print("\n" + "=" * 80)
    print("🔎 5. VERIFICAR DOMINIO ESPECÍFICO")
    print("=" * 80)
    
    dominio_buscar = input("\nIngresa el dominio a buscar (ej: boutique.misventasflash.com): ").strip()
    
    if dominio_buscar:
        try:
            dominio = Domain.objects.get(domain=dominio_buscar)
            print(f"\n✅ Dominio '{dominio_buscar}' ENCONTRADO")
            print(f"   Tenant: {dominio.tenant.nombre}")
            print(f"   Schema: {dominio.tenant.schema_name}")
            print(f"   Primario: {'Sí' if dominio.is_primary else 'No'}")
            print(f"   Tenant activo: {'✅ Sí' if dominio.tenant.activo else '❌ No'}")
            
            if not dominio.tenant.activo:
                print("\n⚠️  PROBLEMA: El tenant existe pero está INACTIVO")
                print("   Solución: Activar el tenant")
        except Domain.DoesNotExist:
            print(f"\n❌ Dominio '{dominio_buscar}' NO ENCONTRADO")
            print("\n🔧 SOLUCIÓN:")
            print(f"   1. Crear el tenant si no existe")
            print(f"   2. Asociar el dominio '{dominio_buscar}' al tenant")
            
            # Buscar por subdominio
            subdomain = dominio_buscar.split('.')[0]
            tenant_similar = Client.objects.filter(nombre_corto__icontains=subdomain).first()
            
            if tenant_similar:
                print(f"\n💡 Encontré un tenant similar:")
                print(f"   Nombre: {tenant_similar.nombre}")
                print(f"   Schema: {tenant_similar.schema_name}")
                print(f"   Nombre corto: {tenant_similar.nombre_corto}")
                print(f"\n   ¿Quieres asociar el dominio '{dominio_buscar}' a este tenant? (s/n)")
                respuesta = input("   > ").strip().lower()
                
                if respuesta == 's':
                    Domain.objects.create(
                        domain=dominio_buscar,
                        tenant=tenant_similar,
                        is_primary=False
                    )
                    print(f"\n✅ Dominio '{dominio_buscar}' asociado exitosamente")
                    print(f"   Ahora deberías poder acceder a: https://{dominio_buscar}")
    
    # 6. Resumen y recomendaciones
    print("\n" + "=" * 80)
    print("📝 RESUMEN Y RECOMENDACIONES")
    print("=" * 80)
    
    print("\n✅ Para que los subdominios funcionen en producción necesitas:")
    print("   1. ALLOWED_HOSTS debe incluir: .misventasflash.com")
    print("   2. Cada tenant debe tener su dominio configurado")
    print("   3. Los tenants deben estar activos (activo=True)")
    print("   4. DNS debe apuntar *.misventasflash.com a tu servidor EC2")
    print("   5. Certificado SSL debe soportar wildcard (*.misventasflash.com)")
    
    print("\n🔧 Archivos importantes:")
    print("   - .env en producción: Verifica ALLOWED_HOSTS")
    print("   - Django settings: django_tenants.middleware.main.TenantMainMiddleware")
    print("   - Nginx: proxy_set_header Host $host;")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    try:
        diagnosticar()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
