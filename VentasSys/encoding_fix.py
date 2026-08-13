"""
Configuración de codificación para psycopg2 en Windows
Este módulo debe importarse ANTES de cualquier código de Django que use la base de datos
"""
import os
import sys
import locale

# Configurar el encoding del sistema
if sys.platform == 'win32':
    # Establecer UTF-8 como encoding por defecto
    if sys.version_info >= (3, 7):
        # Python 3.7+ soporta UTF-8 mode
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # Establecer locale a UTF-8
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, '.UTF-8')
        except:
            pass
    
    # Variables de entorno críticas para PostgreSQL
    os.environ['PGCLIENTENCODING'] = 'UTF8'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Limpiar variables que puedan causar conflictos
    vars_to_remove = []
    for key in os.environ.keys():
        if key.startswith('PG') and key not in ['PGCLIENTENCODING']:
            vars_to_remove.append(key)
    
    for key in vars_to_remove:
        del os.environ[key]

print("[ENCODING FIX] Configuración de encoding aplicada para Windows")
