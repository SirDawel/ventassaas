"""
Script para limpiar notas inválidas (fuera del rango 0-100)
Este script establece en None todas las notas que estén fuera del rango válido.
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import Matricula

def limpiar_notas_invalidas():
    """Limpia todas las notas que estén fuera del rango válido"""
    
    # Campos de notas por competencias (deben estar entre 0 y 100)
    campos_notas = [
        'com_p1', 'com_rp1', 'com_p2', 'com_rp2', 'com_p3', 'com_rp3', 'com_p4', 'com_rp4', 'com_rp',
        'log_p1', 'log_rp1', 'log_p2', 'log_rp2', 'log_p3', 'log_rp3', 'log_p4', 'log_rp4', 'log_rp',
        'cie_p1', 'cie_rp1', 'cie_p2', 'cie_rp2', 'cie_p3', 'cie_rp3', 'cie_p4', 'cie_rp4', 'cie_rp',
        'eti_p1', 'eti_rp1', 'eti_p2', 'eti_rp2', 'eti_p3', 'eti_rp3', 'eti_p4', 'eti_rp4', 'eti_rp',
        'ex_com', 'ex_ext', 'ex_esp'
    ]
    
    # Campos RA (deben estar entre 0 y 10)
    campos_ra = ['ra_1', 'ra_2', 'ra_3', 'ra_4', 'ra_5', 'ra_6', 'ra_7', 'ra_8', 'ra_9', 'ra_10']
    
    matriculas_corregidas = 0
    campos_corregidos = 0
    
    print("🔍 Buscando notas inválidas...")
    print("-" * 80)
    
    for matricula in Matricula.objects.all():
        matricula_modificada = False
        
        # Revisar campos de notas (0-100)
        for campo in campos_notas:
            valor = getattr(matricula, campo)
            if valor is not None:
                if valor < 0 or valor > 100:
                    print(f"⚠️  Matrícula {matricula.id} - Estudiante: {matricula.estudiante.get_full_name()}")
                    print(f"   Campo: {campo} = {valor} (fuera de rango 0-100)")
                    print(f"   Acción: Establecido en None")
                    setattr(matricula, campo, None)
                    campos_corregidos += 1
                    matricula_modificada = True
        
        # Revisar campos RA (0-10)
        for campo in campos_ra:
            valor = getattr(matricula, campo)
            if valor is not None:
                if valor < 0 or valor > 10:
                    print(f"⚠️  Matrícula {matricula.id} - Estudiante: {matricula.estudiante.get_full_name()}")
                    print(f"   Campo: {campo} = {valor} (fuera de rango 0-10)")
                    print(f"   Acción: Establecido en None")
                    setattr(matricula, campo, None)
                    campos_corregidos += 1
                    matricula_modificada = True
        
        # Guardar si hubo cambios (sin validación para permitir guardado)
        if matricula_modificada:
            matricula.save(skip_validation=True)
            matriculas_corregidas += 1
    
    print("-" * 80)
    print(f"\n✅ Proceso completado:")
    print(f"   📊 Matrículas corregidas: {matriculas_corregidas}")
    print(f"   📝 Campos corregidos: {campos_corregidos}")
    
    if matriculas_corregidas == 0:
        print("\n🎉 No se encontraron notas inválidas. Base de datos limpia!")
    else:
        print("\n✨ Notas inválidas limpiadas exitosamente.")
        print("💡 Ahora puedes recargar la página sin errores.")

if __name__ == '__main__':
    try:
        limpiar_notas_invalidas()
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
