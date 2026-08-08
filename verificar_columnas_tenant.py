"""
Verificar columnas en un schema de tenant específico
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection

schemas_a_verificar = ['evangelico', 'cced', 'prueba']

for schema in schemas_a_verificar:
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = %s 
            AND table_name = 'ventasweb_customuser' 
            AND column_name IN ('tipo_cliente', 'limite_credito', 'comision_vendedor', 'meta_mensual', 'zona_venta')
            ORDER BY column_name
        """, [schema])
        
        print(f"\n📊 Columnas en {schema}.ventasweb_customuser:")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"   ✓ {row[0]}: {row[1]}")
        else:
            print("   ⚠ No se encontraron columnas de ventas!")
