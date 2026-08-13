import psycopg2
import sys

print("Intentando crear la base de datos ventassistemdb...\n")

try:
    # Conectar a la base de datos 'postgres' (que siempre existe)
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='QwnKxQAW6VjTN5fbqzL5',
        host='127.0.0.1',
        port='5434'
    )
    
    # Necesitamos autocommit para crear bases de datos
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Verificar si la base de datos ya existe
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='ventassistemdb'")
    exists = cursor.fetchone()
    
    if exists:
        print("✓ La base de datos 'ventassistemdb' ya existe")
    else:
        # Crear la base de datos
        cursor.execute("CREATE DATABASE ventassistemdb ENCODING 'UTF8'")
        print("✓ Base de datos 'ventassistemdb' creada exitosamente")
    
    cursor.close()
    conn.close()
    
    print("\n¡Proceso completado!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}")
    print(f"   {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
