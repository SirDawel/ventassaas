"""
Script para verificar qué tablas existen en la base de datos y en qué schemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection

def verificar_tablas():
    """Verifica qué tablas existen y en qué schemas"""
    
    print("🔍 VERIFICANDO TABLAS EN LA BASE DE DATOS")
    print("=" * 70)
    
    with connection.cursor() as cursor:
        # Listar todos los schemas
        print("\n📁 Schemas disponibles:")
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        for schema in schemas:
            print(f"   - {schema}")
        
        # Para cada schema, listar tablas con prefijo escuelaweb_ o ventasweb_
        print("\n📊 Tablas por schema:")
        print("=" * 70)
        
        for schema in schemas:
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = %s 
                AND (tablename LIKE 'escuelaweb_%%' OR tablename LIKE 'ventasweb_%%')
                ORDER BY tablename
            """, [schema])
            
            tablas = [row[0] for row in cursor.fetchall()]
            
            if tablas:
                print(f"\n{schema}:")
                for tabla in tablas:
                    # Contar registros
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{tabla}"')
                        count = cursor.fetchone()[0]
                        print(f"   {'✓' if tabla.startswith('ventasweb_') else '⚠'} {tabla}: {count} registros")
                    except:
                        print(f"   ✗ {tabla}: error al contar")
        
        # Verificar tabla django_migrations
        print("\n📝 Estado de migraciones:")
        print("=" * 70)
        cursor.execute("""
            SELECT DISTINCT app, COUNT(*) as num_migrations
            FROM public.django_migrations 
            WHERE app IN ('escuelaweb', 'ventasweb')
            GROUP BY app
        """)
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} migraciones")

if __name__ == '__main__':
    try:
        verificar_tablas()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
