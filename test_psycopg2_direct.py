import os
import sys

# Establecer encoding de consola
if sys.platform == 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Limpiar variables de entorno de PostgreSQL
for key in list(os.environ.keys()):
    if key.startswith('PG'):
        print(f"Limpiando variable de entorno: {key}={os.environ[key]}")
        del os.environ[key]

# Establecer encoding explícito
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

try:
    import psycopg2
    print(f"✓ psycopg2 version: {psycopg2.__version__}")
    print(f"✓ libpq version: {psycopg2.__libpq_version__}")
    
    # Parámetros de conexión explícitos
    conn_params = {
        'dbname': 'ventassistemdb',
        'user': 'postgres',
        'password': 'QwnKxQAW6VjTN5fbqzL5',
        'host': 'localhost',
        'port': '5434',
        'client_encoding': 'UTF8',
        'connect_timeout': 10,
    }
    
    print("\nIntentando conectar con parámetros:")
    for key, value in conn_params.items():
        if key != 'password':
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {'*' * len(str(value))}")
    
    # Intentar conexión
    print("\nConectando...")
    conn = psycopg2.connect(**conn_params)
    print("✓ Conexión exitosa!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✓ PostgreSQL version: {version[0][:50]}...")
    
    cursor.close()
    conn.close()
    print("✓ Conexión cerrada correctamente")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}")
    print(f"   {str(e)}")
    import traceback
    traceback.print_exc()
