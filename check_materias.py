import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import Materia, AnhoEscolar, Curso

anho_activo = AnhoEscolar.objects.get(activo=True)
print(f'Año activo: {anho_activo.nombre}')

cursos_activos = Curso.objects.filter(anho_escolar=anho_activo)
print(f'Cursos en año activo: {cursos_activos.count()}')

materias_activo = Materia.objects.filter(curso__anho_escolar=anho_activo)
print(f'Materias en año activo: {materias_activo.count()}')

print(f'Total materias: {Materia.objects.count()}')

print('\nPrimeras 5 materias totales:')
for m in Materia.objects.select_related('curso__anho_escolar').all()[:5]:
    print(f'  - {m.nombre} -> Curso: {m.curso.nombre} -> Año: {m.curso.anho_escolar.nombre}')

print(f'\nTotal cursos: {Curso.objects.count()}')
print('Cursos por año:')
for anho in AnhoEscolar.objects.all():
    count = Curso.objects.filter(anho_escolar=anho).count()
    print(f'  - {anho.nombre}: {count} cursos')
