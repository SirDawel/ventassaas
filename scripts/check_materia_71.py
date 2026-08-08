import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import Materia, AnhoEscolar, CustomUser

anho_activo = AnhoEscolar.objects.get(activo=True)
print(f'Año activo: {anho_activo.nombre}')

# Verificar materia 71
try:
    materia71 = Materia.objects.get(id=71)
    print(f'\nMateria ID 71:')
    print(f'  - Nombre: {materia71.nombre}')
    print(f'  - Curso: {materia71.curso.nombre}')
    print(f'  - Año escolar: {materia71.curso.anho_escolar.nombre}')
    print(f'  - Profesor: {materia71.profesor.get_full_name() if materia71.profesor else "Sin profesor"}')
except Materia.DoesNotExist:
    print('Materia 71 no existe')

# Verificar materias del año activo
materias_activo = Materia.objects.filter(curso__anho_escolar=anho_activo)
print(f'\nMaterias en año activo: {materias_activo.count()}')

# Verificar usuarios profesores
profesores = CustomUser.objects.filter(rol='Profesor')
print(f'\nTotal profesores: {profesores.count()}')
print('Profesores:')
for prof in profesores[:5]:
    materias_prof = Materia.objects.filter(profesor=prof, curso__anho_escolar=anho_activo).count()
    print(f'  - {prof.get_full_name()} ({prof.email}): {materias_prof} materias en año activo')
