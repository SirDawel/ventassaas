#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Buscar archivos de configuración de PostgreSQL que puedan causar problemas de encoding
"""
import os
from pathlib import Path

print("=" * 70)
print("BÚSQUEDA DE ARCHIVOS DE CONFIGURACIÓN POSTGRESQL")
print("=" * 70)

# Ubicaciones comunes de archivos de configuración en Windows
appdata = os.getenv('APPDATA')
programdata = os.getenv('PROGRAMDATA')
home = Path.home()

config_locations = [
    (appdata, 'postgresql'),
    (programdata, 'postgresql'),
    (home, '.postgresql'),
    (home, 'AppData', 'Roaming', 'postgresql'),
    (home, 'AppData', 'Local', 'postgresql'),
]

found_files = []

for location_parts in config_locations:
    if not location_parts[0]:
        continue
    
    if isinstance(location_parts, tuple):
        location = Path(*[str(p) for p in location_parts if p])
    else:
        location = Path(location_parts)
    
    if location.exists():
        print(f"\n📁 Revisando: {location}")
        
        # Buscar archivos de configuración comunes
        config_files = [
            'pgpass.conf',
            'pg_service.conf',
            '.pgpass',
            'postgresql.conf',
        ]
        
        for config_file in config_files:
            file_path = location / config_file
            if file_path.exists():
                print(f"  ✅ Encontrado: {file_path}")
                found_files.append(file_path)
                
                # Intentar leer el archivo y detectar encoding
                try:
                    # Intentar UTF-8
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"      - Codificación: UTF-8 ✅")
                    print(f"      - Tamaño: {len(content)} caracteres")
                except UnicodeDecodeError as e:
                    print(f"      - ❌ Error UTF-8: {e}")
                    
                    # Intentar con otras codificaciones
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                content = f.read()
                            print(f"      - Codificación detectada: {encoding}")
                            print(f"      - Tamaño: {len(content)} caracteres")
                            
                            # Mostrar contenido (ocultando passwords)
                            lines = content.split('\n')
                            print(f"      - Líneas: {len(lines)}")
                            if len(content) >= 96:
                                print(f"      - Carácter en posición 96: '{content[96]}' (ord: {ord(content[96])})")
                            break
                        except Exception:
                            continue
                except Exception as e:
                    print(f"      - ❌ Error: {e}")

# Buscar en PGPASSFILE
pgpassfile = os.getenv('PGPASSFILE')
if pgpassfile:
    print(f"\n🔑 Variable PGPASSFILE definida: {pgpassfile}")
    if Path(pgpassfile).exists():
        print(f"  ✅ Archivo existe: {pgpassfile}")
        found_files.append(Path(pgpassfile))

# Buscar en PGSYSCONFDIR
pgsysconfdir = os.getenv('PGSYSCONFDIR')
if pgsysconfdir:
    print(f"\n⚙️ Variable PGSYSCONFDIR definida: {pgsysconfdir}")

if not found_files:
    print("\n❌ No se encontraron archivos de configuración de PostgreSQL")
    print("\nEsto es bueno - significa que el problema está en otro lado.")
else:
    print(f"\n{'=' * 70}")
    print(f"Total de archivos encontrados: {len(found_files)}")
    print(f"{'=' * 70}")

# Revisar variables de entorno que psycopg2 podría estar leyendo
print(f"\n{'=' * 70}")
print("VARIABLES DE ENTORNO POSTGRESQL")
print(f"{'=' * 70}")

pg_vars = [
    'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD',
    'PGPASSFILE', 'PGSYSCONFDIR', 'PGSERVICEFILE', 'PGOPTIONS',
    'PGSSLMODE', 'PGCLIENTENCODING', 'PGCONNECT_TIMEOUT', 'PGAPPNAME'
]

found_vars = False
for var in pg_vars:
    value = os.getenv(var)
    if value:
        found_vars = True
        print(f"{var} = {value if 'PASS' not in var else '***'}")

if not found_vars:
    print("No se encontraron variables de entorno de PostgreSQL")

print(f"\n{'=' * 70}")
