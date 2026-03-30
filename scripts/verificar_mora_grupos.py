"""
Script para verificar que los campos de mora estén configurados correctamente
en los grupos familiares existentes.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import GrupoFamiliar, CustomUser

print("\n" + "="*80)
print("VERIFICACIÓN DE CAMPOS DE MORA EN GRUPOS FAMILIARES")
print("="*80 + "\n")

# Verificar todos los grupos familiares
grupos = GrupoFamiliar.objects.all()

if not grupos.exists():
    print("❌ No hay grupos familiares en la base de datos.\n")
else:
    print(f"✅ Se encontraron {grupos.count()} grupo(s) familiar(es):\n")
    
    for grupo in grupos:
        print(f"\n📋 Grupo: {grupo.apellido_familia} ({grupo.codigo_familia})")
        print(f"   Estado: {'✅ Activo' if grupo.activo else '❌ Inactivo'}")
        print(f"   Descuento General: {grupo.descuento_general}%")
        print(f"   Porcentaje de Mora: {grupo.porcentaje_mora}%")
        
        # Verificar tipo de dato
        print(f"   Tipo descuento_general: {type(grupo.descuento_general)}")
        print(f"   Tipo porcentaje_mora: {type(grupo.porcentaje_mora)}")
        
        # Verificar si son None o tienen valor
        if grupo.descuento_general is None:
            print("   ⚠️  PROBLEMA: descuento_general es None")
        if grupo.porcentaje_mora is None:
            print("   ⚠️  PROBLEMA: porcentaje_mora es None")
        
        # Contar estudiantes
        num_estudiantes = grupo.estudiantes.filter(rol='Estudiante', is_active=True).count()
        print(f"   Estudiantes: {num_estudiantes}")

print("\n" + "="*80)
print("VERIFICACIÓN DE CAMPOS DE MORA EN ESTUDIANTES INDIVIDUALES")
print("="*80 + "\n")

# Verificar estudiantes sin grupo familiar
estudiantes_sin_grupo = CustomUser.objects.filter(
    rol='Estudiante',
    is_active=True,
    grupo_familiar__isnull=True
)

if estudiantes_sin_grupo.exists():
    print(f"✅ Se encontraron {estudiantes_sin_grupo.count()} estudiante(s) sin grupo familiar:\n")
    
    for estudiante in estudiantes_sin_grupo[:10]:  # Mostrar los primeros 10
        print(f"\n👤 Estudiante: {estudiante.get_full_name()}")
        print(f"   Porcentaje Mora Individual: {estudiante.porcentaje_mora_individual}%")
        print(f"   Tipo: {type(estudiante.porcentaje_mora_individual)}")
        
        if estudiante.porcentaje_mora_individual is None:
            print("   ⚠️  PROBLEMA: porcentaje_mora_individual es None")
else:
    print("ℹ️  Todos los estudiantes están asignados a grupos familiares.\n")

print("\n" + "="*80)
print("RESUMEN")
print("="*80 + "\n")

# Verificar si hay algún grupo con mora configurada
grupos_con_mora = GrupoFamiliar.objects.filter(porcentaje_mora__gt=0)
print(f"✅ Grupos con mora configurada (> 0%): {grupos_con_mora.count()}")

estudiantes_con_mora = CustomUser.objects.filter(
    rol='Estudiante',
    porcentaje_mora_individual__gt=0
)
print(f"✅ Estudiantes con mora individual configurada (> 0%): {estudiantes_con_mora.count()}")

print("\n")
