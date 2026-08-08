"""
Script para verificar y mostrar recuperaciones en la base de datos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import Matricula, Curso

# Buscar curso 3
curso = Curso.objects.get(id=3)
print(f"\n{'='*60}")
print(f"VERIFICANDO RECUPERACIONES - Curso: {curso.nombre}")
print(f"{'='*60}\n")

# Obtener todas las matrículas del curso
matriculas = Matricula.objects.filter(materia__curso=curso).select_related('estudiante', 'materia')

for m in matriculas:
    print(f"\n📚 Materia: {m.materia.nombre}")
    print(f"👤 Estudiante: {m.estudiante.get_full_name()}")
    print(f"-" * 50)
    
    # Competencia Lógica-Matemática
    print(f"  Competencia Lógica-Matemática:")
    print(f"    log_p1: {m.log_p1}  |  log_rp1: {m.log_rp1}")
    print(f"    log_p2: {m.log_p2}  |  log_rp2: {m.log_rp2}")
    print(f"    log_p3: {m.log_p3}  |  log_rp3: {m.log_rp3}")
    print(f"    log_p4: {m.log_p4}  |  log_rp4: {m.log_rp4}")
    
    # Verificar si necesita recuperaciones
    if m.log_p1 is not None and m.log_p1 < 70:
        if m.log_rp1 is None:
            print(f"    ⚠️  FALTA log_rp1 (nota {m.log_p1} < 70)")
        else:
            print(f"    ✓ Tiene log_rp1: {m.log_rp1}")
    
    if m.log_p2 is not None and m.log_p2 < 70:
        if m.log_rp2 is None:
            print(f"    ⚠️  FALTA log_rp2 (nota {m.log_p2} < 70)")
        else:
            print(f"    ✓ Tiene log_rp2: {m.log_rp2}")

print(f"\n{'='*60}")
print("Verificación completada")
print(f"{'='*60}\n")
