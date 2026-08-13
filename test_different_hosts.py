import sys
import os

# Limpiar variables de entorno
for key in list(os.environ.keys()):
    if key.startswith('PG'):
        del os.environ[key]

try:
    import psycopg2
    
    print("Probando diferentes métodos de conexión...\n")
    
    # Parámetros base
    params_list = [
        {
            'dbname': 'ventassistemdb',
            'user': 'postgres',
            'password': 'QwnKxQAW6VjTN5fbqzL5',
            'host': '127.0.0.1',  # Usar IP en lugar de localhost
            'port': '5434',
        },
        {
            'dbname': 'ventassistemdb',
            'user': 'postgres',
            'password': 'QwnKxQAW6VjTN5fbqzL5',
            'host': '::1',  # IPv6 localhost
            'port': '5434',
        }
    ]
    
    for i, params in enumerate(params_list, 1):
        print(f"--- Intento {i}: host={params['host']} ---")
        try:
            conn = psycopg2.connect(**params)
            print(f"✓ ¡ÉXITO! Conexión establecida con host={params['host']}")
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✓ PostgreSQL: {version[0][:60]}...")
            
            cursor.close()
            conn.close()
            print(f"✓ Prueba {i} completada correctamente\n")
            break
            
        except Exception as e:
            print(f"✗ Error con host={params['host']}: {type(e).__name__}: {str(e)[:100]}\n")
            continue
    else:
        print("❌ Todos los intentos fallaron")
        
except Exception as e:
    print(f"\n❌ Error fatal: {type(e).__name__}")
    print(f"   {str(e)}")
