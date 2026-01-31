import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import AnhoEscolar

# Desactivar todos los años
AnhoEscolar.objects.all().update(activo=False)

# Activar el año 2025-2026
anho_2025 = AnhoEscolar.objects.get(nombre='Año 2025 - 2026')
anho_2025.activo = True
anho_2025.save()

print(f'Año escolar activado: {anho_2025.nombre}')
print(f'Fecha inicio: {anho_2025.fecha_inicio}')
print(f'Fecha fin: {anho_2025.fecha_fin}')
