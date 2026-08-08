"""
Script para renombrar todas las tablas de escuelaweb_* a ventasweb_* en TODOS los schemas
Incluye schema public y todos los schemas de tenants
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection

def renombrar_tablas_en_schema(cursor, schema_name):
    """Renombra todas las tablas de escuelaweb_* a ventasweb_* en un schema específico"""
    
    # Obtener todas las tablas con prefijo escuelaweb_ en este schema
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = %s 
        AND tablename LIKE 'escuelaweb_%%'
        ORDER BY tablename
    """, [schema_name])
    
    tablas = [row[0] for row in cursor.fetchall()]
    
    if not tablas:
        return 0
    
    print(f"\n   Renombrando {len(tablas)} tablas en schema '{schema_name}'...")
    
    renombradas = 0
    for tabla_vieja in tablas:
        tabla_nueva = tabla_vieja.replace('escuelaweb_', 'ventasweb_', 1)
        
        try:
            # Renombrar la tabla
            cursor.execute(f'ALTER TABLE "{schema_name}"."{tabla_vieja}" RENAME TO "{tabla_nueva}"')
            renombradas += 1
            
            # Renombrar la secuencia asociada si existe
            seq_vieja = f"{tabla_vieja}_id_seq"
            seq_nueva = f"{tabla_nueva}_id_seq"
            try:
                cursor.execute(f'ALTER SEQUENCE IF EXISTS "{schema_name}"."{seq_vieja}" RENAME TO "{seq_nueva}"')
            except:
                pass  # La secuencia puede no existir
                
        except Exception as e:
            if 'already exists' not in str(e):
                print(f"      ⚠ Error en {tabla_vieja}: {e}")
    
    return renombradas

def renombrar_todas_las_tablas():
    """Renombra tablas en public y en todos los schemas de tenants"""
    
    print("🔄 RENOMBRADO COMPLETO DE TABLAS: escuelaweb_* → ventasweb_*")
    print("=" * 70)
    
    with connection.cursor() as cursor:
        # Obtener todos los schemas (excepto los del sistema)
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY CASE WHEN schema_name = 'public' THEN 0 ELSE 1 END, schema_name
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📁 Schemas encontrados: {len(schemas)}")
        for schema in schemas:
            print(f"   - {schema}")
        
        print(f"\n🔨 Iniciando renombrado...")
        print("=" * 70)
        
        total_renombradas = 0
        schemas_procesados = 0
        
        for schema in schemas:
            renombradas = renombrar_tablas_en_schema(cursor, schema)
            if renombradas > 0:
                total_renombradas += renombradas
                schemas_procesados += 1
                print(f"      ✓ {renombradas} tablas renombradas")
        
        # Commit de todos los cambios
        connection.connection.commit()
        
        # Actualizar django_migrations
        print(f"\n📝 Actualizando tabla django_migrations...")
        cursor.execute("""
            UPDATE django_migrations 
            SET app = 'ventasweb' 
            WHERE app = 'escuelaweb'
        """)
        migraciones_actualizadas = cursor.rowcount
        connection.connection.commit()
        print(f"      ✓ {migraciones_actualizadas} registros de migraciones actualizados")
        
        print("\n" + "=" * 70)
        print(f"✅ RENOMBRADO COMPLETADO:")
        print(f"   - Schemas procesados: {schemas_procesados}/{len(schemas)}")
        print(f"   - Total tablas renombradas: {total_renombradas}")
        print(f"   - Migraciones actualizadas: {migraciones_actualizadas}")
        
        # Verificación final
        print(f"\n🔍 Verificación final...")
        print("=" * 70)
        
        for schema in schemas[:3]:  # Verificar solo los primeros 3 schemas
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_tables 
                WHERE schemaname = %s 
                AND tablename LIKE 'escuelaweb_%%'
            """, [schema])
            
            count_viejas = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_tables 
                WHERE schemaname = %s 
                AND tablename LIKE 'ventasweb_%%'
            """, [schema])
            
            count_nuevas = cursor.fetchone()[0]
            
            if count_viejas > 0:
                print(f"   ⚠ {schema}: {count_viejas} tablas antiguas pendientes, {count_nuevas} tablas nuevas")
            else:
                print(f"   ✓ {schema}: {count_nuevas} tablas renombradas correctamente")
        
        print("\n✅ ¡Proceso completado exitosamente!")
        print("\nAhora puedes reiniciar el servidor Django:")
        print("   python manage.py runserver")

if __name__ == '__main__':
    try:
        renombrar_todas_las_tablas()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
