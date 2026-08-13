#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para diagnosticar problemas de codificación en variables de entorno
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env con diferentes métodos
BASE_DIR = Path(__file__).resolve().parent

print("=" * 70)
print("DIAGNÓSTICO DE CODIFICACIÓN - VARIABLES DE ENTORNO")
print("=" * 70)

# Método 1: Sin especificar encoding
print("\n1. Cargando .env SIN especificar encoding:")
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Revisar cada variable relacionada con la base de datos
db_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']

for var in db_vars:
    value = os.getenv(var, '')
    print(f"\n{var}:")
    print(f"  Valor: {value}")
    print(f"  Tipo: {type(value)}")
    print(f"  Longitud: {len(value)}")
    
    # Mostrar bytes
    try:
        value_bytes = value.encode('utf-8')
        print(f"  Bytes UTF-8: {value_bytes}")
        print(f"  Hex: {value_bytes.hex()}")
    except Exception as e:
        print(f"  ❌ Error al codificar: {e}")
    
    # Buscar caracteres no-ASCII
    non_ascii = [c for c in value if ord(c) > 127]
    if non_ascii:
        print(f"  ⚠️ Caracteres no-ASCII encontrados: {non_ascii}")

# Probar construir el DSN como lo hace psycopg2
print("\n" + "=" * 70)
print("CONSTRUCCIÓN DEL DSN (Connection String)")
print("=" * 70)

db_name = os.getenv('DB_NAME', '')
db_user = os.getenv('DB_USER', '')
db_password = os.getenv('DB_PASSWORD', '')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')

dsn = f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}"
print(f"\nDSN completo:\n{dsn}")
print(f"\nLongitud del DSN: {len(dsn)}")

# Mostrar caracteres alrededor de la posición 96
if len(dsn) >= 96:
    print(f"\nCaracteres alrededor de la posición 96:")
    start = max(0, 96 - 10)
    end = min(len(dsn), 96 + 10)
    print(f"  Posiciones {start}-{end}: '{dsn[start:end]}'")
    print(f"  Carácter en posición 96: '{dsn[96]}' (ord: {ord(dsn[96])})")

# Intentar codificar el DSN
try:
    dsn_bytes = dsn.encode('utf-8')
    print(f"\n✅ DSN se puede codificar a UTF-8")
    print(f"Bytes totales: {len(dsn_bytes)}")
    if len(dsn_bytes) >= 96:
        print(f"Byte en posición 96: 0x{dsn_bytes[96]:02x} ('{chr(dsn_bytes[96])}')")
except UnicodeEncodeError as e:
    print(f"\n❌ Error al codificar DSN: {e}")

print("\n" + "=" * 70)
