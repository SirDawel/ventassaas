"""Script para ver artículos en la base de datos"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT id, codigo, codigo_barras, nombre FROM escuelaweb_articulo")
    rows = cursor.fetchall()
    
    print(f"Total de artículos: {len(rows)}")
    print("-" * 80)
    
    for row in rows:
        id_art, codigo, codigo_barras, nombre = row
        print(f"ID: {id_art}, Codigo: '{codigo}', CB: '{codigo_barras}', Nombre: {nombre}")
        
    # Contar los que tienen codigo_barras vacío
    cursor.execute("SELECT COUNT(*) FROM escuelaweb_articulo WHERE codigo_barras = ''")
    count = cursor.fetchone()[0]
    print(f"\nArtículos con codigo_barras vacío: {count}")
