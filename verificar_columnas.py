"""
Verificar si las columnas de ventas existen en la tabla customuser
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Verificar en schema public
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'ventasweb_customuser' 
        AND column_name IN ('tipo_cliente', 'limite_credito', 'comision_vendedor', 'meta_mensual', 'zona_venta')
        ORDER BY column_name
    """)
    
    print("📊 Columnas en public.ventasweb_customuser:")
    for row in cursor.fetchall():
        print(f"   ✓ {row[0]}: {row[1]}")
    
    if cursor.rowcount == 0:
        print("   ⚠ No se encontraron columnas de ventas!")
