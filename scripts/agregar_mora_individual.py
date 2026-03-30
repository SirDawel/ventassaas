"""
Script para agregar campo dia_vencimiento_individual a estudiantes existentes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import CustomUser

# Actualizar todos los estudiantes para que tengan día de vencimiento individual por defecto
estudiantes = CustomUser.objects.filter(rol='Estudiante')

print(f"Encontrados {estudiantes.count()} estudiantes")

for estudiante in estudiantes:
    if not hasattr(estudiante, 'dia_vencimiento_individual') or estudiante.dia_vencimiento_individual is None:
        estudiante.dia_vencimiento_individual = 10
        estudiante.save(update_fields=['dia_vencimiento_individual'])
        print(f"✓ Actualizado: {estudiante.get_full_name()} - Día vencimiento: 10")

print("\n✅ Proceso completado")
