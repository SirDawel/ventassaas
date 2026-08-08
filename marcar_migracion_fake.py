"""
Script para marcar la migración 0062 como aplicada (fake) en todos los schemas de tenants
Esto es necesario porque los campos ya existen en la base de datos pero Django no lo sabe
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection
from ventasweb.tenant_models import Client

def marcar_migracion_fake():
    """Marca la migración 0062 como aplicada en todos los schemas de tenants"""
    
    print("🔧 MARCANDO MIGRACIÓN 0062 COMO APLICADA (FAKE)")
    print("=" * 70)
    
    # Obtener todos los tenants
    tenants = Client.objects.all()
    
    print(f"\n📁 Tenants encontrados: {tenants.count()}")
    for tenant in tenants:
        print(f"   - {tenant.schema_name}: {tenant.nombre}")
    
    print(f"\n🔨 Aplicando migración fake en cada schema...")
    print("=" * 70)
    
    exitosos = 0
    errores = 0
    
    for tenant in tenants:
        schema = tenant.schema_name
        
        # Saltar el schema public (ya se aplicó correctamente)
        if schema == 'public':
            continue
        
        try:
            with connection.cursor() as cursor:
                # Cambiar al schema del tenant
                cursor.execute(f'SET search_path TO "{schema}"')
                
                # Verificar si la migración ya está registrada
                cursor.execute("""
                    SELECT id FROM django_migrations 
                    WHERE app = 'ventasweb' 
                    AND name = '0062_clientecorporativo_comisionvendedor_cotizacion_and_more'
                """)
                
                if cursor.fetchone():
                    print(f"   ⏭ {schema}: Migración ya aplicada")
                else:
                    # Insertar el registro de migración como aplicada
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        VALUES ('ventasweb', '0062_clientecorporativo_comisionvendedor_cotizacion_and_more', NOW())
                    """)
                    connection.connection.commit()
                    print(f"   ✓ {schema}: Migración marcada como aplicada")
                
                exitosos += 1
                
        except Exception as e:
            print(f"   ✗ {schema}: Error - {e}")
            errores += 1
    
    print("\n" + "=" * 70)
    print(f"✅ PROCESO COMPLETADO:")
    print(f"   - Tenants exitosos: {exitosos}")
    if errores > 0:
        print(f"   - Errores: {errores}")
    
    print("\n✅ Ahora puedes aplicar las migraciones normalmente:")
    print("   python manage.py migrate")

if __name__ == '__main__':
    try:
        marcar_migracion_fake()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
