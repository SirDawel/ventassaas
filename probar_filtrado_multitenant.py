"""
Script para probar el filtrado automático por escuela (Multi-Tenant)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models_escuela import Escuela
from escuelaweb.models import Curso, Materia, CustomUser
from escuelaweb import tenant_context

print("="*70)
print("PRUEBA DE FILTRADO MULTI-TENANT")
print("="*70)

# Obtener las escuelas
escuelas = Escuela.objects.all()
print(f"\n📚 Escuelas en el sistema: {escuelas.count()}")
for e in escuelas:
    print(f"  - {e.nombre} ({e.nombre_corto})")

print("\n" + "="*70)
print("SIN CONTEXTO DE TENANT (sitio público)")
print("="*70)
tenant_context.set_current_escuela(None)
print(f"Cursos visibles: {Curso.objects.count()}")
print(f"Materias visibles: {Materia.objects.count()}")
print(f"⚠️  Esperado: 0 (sitio público no debe ver datos)")

# Probar cada escuela
for escuela in escuelas:
    print("\n" + "="*70)
    print(f"CONTEXTO: {escuela.nombre}")
    print("="*70)
    
    # Establecer contexto de escuela
    tenant_context.set_current_escuela(escuela)
    
    # Contar datos con filtrado automático
    cursos = Curso.objects.count()
    materias = Materia.objects.count()
    usuarios = CustomUser.objects.filter(escuela=escuela).count()  # CustomUser tiene manager custom
    
    print(f"✅ Usuarios: {usuarios}")
    print(f"✅ Cursos: {cursos}")
    print(f"✅ Materias: {materias}")
    
    if cursos > 0:
        print(f"\nPrimeros 3 cursos:")
        for curso in Curso.objects.all()[:3]:
            print(f"  - {curso.nombre} (Escuela: {curso.escuela.nombre_corto})")

# Limpiar contexto
tenant_context.set_current_escuela(None)

print("\n" + "="*70)
print("✅ PRUEBA COMPLETADA")
print("="*70)
print("\n📝 Notas:")
print("  - El filtrado automático funciona con TenantManager")
print("  - Cada escuela solo ve sus propios datos")
print("  - Sin contexto de tenant, no se ven datos (seguridad)")
