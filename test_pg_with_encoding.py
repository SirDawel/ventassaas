#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test conexión con PGCLIENTENCODING configurado
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Configurar encoding ANTES de cargar cualquier cosa
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Cargar .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'), encoding='utf-8')

print("=" * 70)
print("TEST DE CONEXIÓN CON PGCLIENTENCODING=UTF8")
print("=" * 70)

db_params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'client_encoding': 'UTF8',
}

print("\nParámetros de conexión:")
for key, value in db_params.items():
    if key == 'password':
        print(f"  {key}: {'*' * len(value)}")
    else:
        print(f"  {key}: {value}")

print("\nVariables de entorno configuradas:")
print(f"  PGCLIENTENCODING: {os.getenv('PGCLIENTENCODING')}")
print(f"  PYTHONIOENCODING: {os.getenv('PYTHONIOENCODING')}")

try:
    import psycopg2
    print("\n✅ psycopg2 importado correctamente")
    
    print("\nIntentando conectar...")
    conn = psycopg2.connect(**db_params)
    print("✅ ¡CONEXIÓN EXITOSA!")
    
    # Obtener información del servidor
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\nServidor PostgreSQL: {version}")
    
    cursor.execute("SHOW server_encoding;")
    server_encoding = cursor.fetchone()[0]
    print(f"Server encoding: {server_encoding}")
    
    cursor.execute("SHOW client_encoding;")
    client_encoding = cursor.fetchone()[0]
    print(f"Client encoding: {client_encoding}")
    
    cursor.close()
    conn.close()
    print("\n✅ Conexión cerrada correctamente")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
