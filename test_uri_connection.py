import sys
import os

# Limpiar cualquier variable de entorno de PostgreSQL
for key in list(os.environ.keys()):
    if key.startswith('PG'):
        del os.environ[key]

try:
    import psycopg2
    from urllib.parse import quote_plus
    
    print("✓ psycopg2 version:", psycopg2.__version__)
    
    # Parámetros de conexión
    user = 'postgres'
    password = 'QwnKxQAW6VjTN5fbqzL5'
    host = 'localhost'
    port = '5434'
    dbname = 'ventassistemdb'
    
    # Codificar la contraseña para URI
    encoded_password = quote_plus(password)
    
    # Construir URI de conexión
    uri = f'postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}?client_encoding=utf8'
    
    print(f"\nURI (sin contraseña): postgresql://{user}:***@{host}:{port}/{dbname}")
    print("\nIntentando conectar con URI...")
    
    conn = psycopg2.connect(uri)
    print("✓ ¡Conexión exitosa con URI!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✓ PostgreSQL version: {version[0][:70]}...")
    
    cursor.close()
    conn.close()
    print("✓ Conexión cerrada correctamente")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}")
    print(f"   {str(e)}")
    import traceback
    traceback.print_exc()
