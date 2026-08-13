#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de conexión directa a PostgreSQL para diagnosticar el error
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'), encoding='utf-8')

print("=" * 70)
print("TEST DE CONEXIÓN POSTGRESQL")
print("=" * 70)

# Mostrar variables de entorno de PostgreSQL
print("\nVariables de entorno de PostgreSQL:")
pg_env_vars = [
    'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD',
    'PGAPPNAME', 'PGCLIENTENCODING', 'PGOPTIONS', 'PGTZ'
]
for var in pg_env_vars:
    value = os.getenv(var)
    if value:
        print(f"  {var} = {value}")

# Intentar importar psycopg2
print("\nImportando psycopg2...")
try:
    import psycopg2
    print("✅ psycopg2 importado correctamente")
except ImportError as e:
    print(f"❌ Error al importar psycopg2: {e}")
    exit(1)

# Intentar conectar con diferentes métodos
db_params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
}

print("\nParámetros de conexión:")
for key, value in db_params.items():
    if key == 'password':
        print(f"  {key}: {'*' * len(value)}")
    else:
        print(f"  {key}: {value}")

# Método 1: Conexión con diccionario
print("\n" + "-" * 70)
print("Método 1: Conexión con diccionario de parámetros")
print("-" * 70)
try:
    conn = psycopg2.connect(**db_params)
    print("✅ Conexión exitosa!")
    conn.close()
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Método 2: Conexión con DSN explícito
print("\n" + "-" * 70)
print("Método 2: Conexión con DSN explícito")
print("-" * 70)
dsn = f"dbname={db_params['dbname']} user={db_params['user']} password={db_params['password']} host={db_params['host']} port={db_params['port']}"
print(f"DSN (sin password): dbname={db_params['dbname']} user={db_params['user']} password=*** host={db_params['host']} port={db_params['port']}")
try:
    conn = psycopg2.connect(dsn)
    print("✅ Conexión exitosa!")
    conn.close()
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Método 3: Conexión con client_encoding explícito
print("\n" + "-" * 70)
print("Método 3: Conexión con client_encoding='UTF8'")
print("-" * 70)
db_params_with_encoding = db_params.copy()
db_params_with_encoding['options'] = '-c client_encoding=UTF8'
try:
    conn = psycopg2.connect(**db_params_with_encoding)
    print("✅ Conexión exitosa!")
    conn.close()
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
