import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django_tenants.utils import schema_context
from django.db import connection

# Verificar en el schema public
print("\n=== Schema PUBLIC ===")
with schema_context('public'):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        AND table_name LIKE '%plantilla%'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    if tables:
        print(f"Tablas encontradas: {tables}")
    else:
        print("❌ No se encontraron tablas de plantillas")

# Verificar en un schema de tenant
print("\n=== Schema LUCYBOUTIQUE ===")
with schema_context('lucyboutique'):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='lucyboutique' 
        AND table_name LIKE '%plantilla%'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    if tables:
        print(f"Tablas encontradas: {tables}")
    else:
        print("❌ No se encontraron tablas de plantillas")
