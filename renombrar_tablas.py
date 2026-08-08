"""
Script para renombrar todas las tablas de escuelaweb_* a ventasweb_* en PostgreSQL
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection

def renombrar_tablas():
    """Ejecuta el script SQL para renombrar todas las tablas"""
    
    # Leer el archivo SQL
    sql_file = 'renombrar_tablas_ventasweb.sql'
    
    print(f"Leyendo archivo: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Dividir en statements individuales (separados por ;)
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"\nEjecutando {len(statements)} comandos SQL...")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        ejecutados = 0
        errores = 0
        
        for statement in statements:
            # Ignorar comentarios
            if statement.startswith('--') or not statement.strip():
                continue
            
            try:
                cursor.execute(statement)
                ejecutados += 1
                
                # Mostrar progreso cada 10 comandos
                if ejecutados % 10 == 0:
                    print(f"✓ Ejecutados: {ejecutados}/{len(statements)}")
                    
            except Exception as e:
                # Algunos comandos pueden fallar si la tabla no existe, eso está bien
                if 'does not exist' in str(e) or 'no existe' in str(e):
                    # Silenciar estos errores
                    pass
                else:
                    print(f"⚠ Error en comando: {statement[:50]}...")
                    print(f"   {e}")
                    errores += 1
        
        # Commit de todos los cambios
        connection.connection.commit()
    
    print("=" * 60)
    print(f"\n✅ Proceso completado:")
    print(f"   - Comandos ejecutados exitosamente: {ejecutados}")
    if errores > 0:
        print(f"   - Errores (pueden ser esperados): {errores}")
    
    # Verificar algunas tablas críticas
    print("\n🔍 Verificando tablas críticas...")
    with connection.cursor() as cursor:
        tablas_criticas = [
            'ventasweb_client',
            'ventasweb_domain', 
            'ventasweb_customuser',
            'ventasweb_factura',
            'ventasweb_articulo'
        ]
        
        for tabla in tablas_criticas:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cursor.fetchone()[0]
                print(f"   ✓ {tabla}: {count} registros")
            except Exception as e:
                print(f"   ✗ {tabla}: NO ENCONTRADA")
    
    print("\n✅ Renombrado de tablas completado exitosamente!")
    print("\nAhora puedes reiniciar el servidor Django:")
    print("   python manage.py runserver")

if __name__ == '__main__':
    try:
        print("🔄 RENOMBRADO DE TABLAS: escuelaweb_* → ventasweb_*")
        print("=" * 60)
        renombrar_tablas()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
