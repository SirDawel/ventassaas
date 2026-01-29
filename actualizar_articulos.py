"""Script para arreglar artículos"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Actualizar artículos con codigo_barras NULL, copiando el valor de codigo
    cursor.execute("""
        UPDATE escuelaweb_articulo 
        SET codigo_barras = codigo 
        WHERE codigo_barras IS NULL
    """)
    
    print(f"Artículos actualizados: {cursor.rowcount}")
    
    # Verificar
    cursor.execute("SELECT id, codigo, codigo_barras, nombre FROM escuelaweb_articulo")
    rows = cursor.fetchall()
    
    print("\nArtículos después de actualizar:")
    print("-" * 80)
    for row in rows:
        id_art, codigo, codigo_barras, nombre = row
        print(f"ID: {id_art}, Codigo: '{codigo}', CB: '{codigo_barras}', Nombre: {nombre}")
