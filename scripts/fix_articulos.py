"""Script para arreglar artículos con codigo_barras vacío"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import Articulo
from datetime import datetime
import random

# Buscar artículos con codigo_barras vacío o None
articulos = Articulo.objects.filter(codigo_barras__in=['', None])

print(f"Se encontraron {articulos.count()} artículos con codigo_barras vacío")

for articulo in articulos:
    # Generar un código único
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = random.randint(1000, 9999)
    nuevo_codigo = f"ART{timestamp}{random_suffix}"
    
    # Asegurar que sea único
    while Articulo.objects.filter(codigo_barras=nuevo_codigo).exists():
        random_suffix = random.randint(1000, 9999)
        nuevo_codigo = f"ART{timestamp}{random_suffix}"
    
    articulo.codigo_barras = nuevo_codigo
    articulo.save()
    print(f"Artículo ID {articulo.id} actualizado con código: {nuevo_codigo}")

print("¡Listo!")
