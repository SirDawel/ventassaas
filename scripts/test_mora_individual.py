"""
Script para verificar y probar la configuración de mora individual de estudiantes.

Este script muestra:
1. Cómo se configura la mora para estudiantes individuales (sin grupo familiar)
2. Cómo se usa la mora del grupo familiar cuando el estudiante pertenece a uno
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import CustomUser, GrupoFamiliar

def mostrar_configuracion_mora():
    """Muestra la configuración de mora para diferentes estudiantes"""
    
    print("\n" + "="*80)
    print("CONFIGURACIÓN DE MORA POR ESTUDIANTE")
    print("="*80 + "\n")
    
    estudiantes = CustomUser.objects.filter(rol='Estudiante').select_related('grupo_familiar')[:10]
    
    if not estudiantes:
        print("No se encontraron estudiantes en el sistema.")
        return
    
    for estudiante in estudiantes:
        print(f"\n📚 Estudiante: {estudiante.get_full_name()} (ID: {estudiante.id})")
        print(f"   Email: {estudiante.email}")
        
        if estudiante.grupo_familiar:
            print(f"\n   👨‍👩‍👧‍👦 GRUPO FAMILIAR: {estudiante.grupo_familiar.apellido_familia}")
            print(f"   ├─ Día de vencimiento: {estudiante.grupo_familiar.dia_vencimiento}")
            print(f"   ├─ Porcentaje de mora: {estudiante.grupo_familiar.porcentaje_mora}%")
            print(f"   └─ 📝 Se usa la configuración del GRUPO FAMILIAR")
        else:
            print(f"\n   👤 SIN GRUPO FAMILIAR (Estudiante Individual)")
            print(f"   ├─ Día de vencimiento individual: {estudiante.dia_vencimiento_individual}")
            print(f"   ├─ Porcentaje de mora individual: {estudiante.porcentaje_mora_individual}%")
            print(f"   └─ 📝 Se usa la configuración INDIVIDUAL")
        
        # Mostrar valores efectivos usando los métodos del modelo
        print(f"\n   ✅ Valores efectivos aplicados:")
        print(f"   ├─ Día de vencimiento efectivo: {estudiante.get_dia_vencimiento()}")
        print(f"   └─ Porcentaje de mora efectivo: {estudiante.get_porcentaje_mora()}%")
        print("-" * 80)

def configurar_mora_ejemplo():
    """Muestra cómo configurar mora individual para un estudiante"""
    
    print("\n" + "="*80)
    print("EJEMPLO: CONFIGURAR MORA INDIVIDUAL")
    print("="*80 + "\n")
    
    # Buscar un estudiante sin grupo familiar
    estudiante = CustomUser.objects.filter(
        rol='Estudiante', 
        grupo_familiar__isnull=True
    ).first()
    
    if not estudiante:
        print("No se encontró ningún estudiante sin grupo familiar.")
        print("\n💡 Para crear un estudiante y configurar su mora individual:")
        print("""
        from escuelaweb.models import CustomUser
        
        # Crear o buscar estudiante
        estudiante = CustomUser.objects.get(id=ID_ESTUDIANTE)
        
        # Configurar mora individual (solo aplica si NO está en grupo familiar)
        estudiante.porcentaje_mora_individual = 15.00  # 15% de recargo por mora
        estudiante.dia_vencimiento_individual = 10      # Vence el día 10 de cada mes
        estudiante.save()
        
        print(f"Configuración guardada para {estudiante.get_full_name()}")
        """)
    else:
        print(f"✅ Ejemplo con estudiante: {estudiante.get_full_name()}")
        print(f"\nConfiguración actual:")
        print(f"├─ Porcentaje de mora individual: {estudiante.porcentaje_mora_individual}%")
        print(f"└─ Día de vencimiento individual: {estudiante.dia_vencimiento_individual}")
        
        print(f"\n💡 Para cambiar la configuración desde el código:")
        print(f"""
        estudiante = CustomUser.objects.get(id={estudiante.id})
        estudiante.porcentaje_mora_individual = 15.00  # 15% de recargo
        estudiante.dia_vencimiento_individual = 10      # Vence el día 10
        estudiante.save()
        """)
        
        print(f"\n💡 Para cambiar desde la interfaz web:")
        print(f"   1. Ve a la lista de usuarios/estudiantes")
        print(f"   2. Haz clic en 'Editar' para el estudiante")
        print(f"   3. Busca la sección 'Configuración de Mora Individual'")
        print(f"   4. Ingresa el día de vencimiento (1-31) y el porcentaje de mora (0-100)")
        print(f"   5. Guarda los cambios")

if __name__ == '__main__':
    mostrar_configuracion_mora()
    configurar_mora_ejemplo()
    
    print("\n" + "="*80)
    print("✅ RESUMEN")
    print("="*80)
    print("""
    📌 CÓMO FUNCIONA EL SISTEMA DE MORA:
    
    1. ESTUDIANTE EN GRUPO FAMILIAR:
       - Se usa el porcentaje de mora del grupo familiar
       - Se usa el día de vencimiento del grupo familiar
       - Los campos individuales son ignorados
    
    2. ESTUDIANTE SIN GRUPO FAMILIAR (INDIVIDUAL):
       - Se usa el porcentaje de mora individual del estudiante
       - Se usa el día de vencimiento individual del estudiante
       - Se configura en el formulario del estudiante
    
    📝 DÓNDE CONFIGURAR:
    
    - Interfaz web: Editar usuario → Sección "Configuración de Mora Individual"
    - Admin Django: Panel de administración → Usuarios → Configuración de Mora Individual
    - Código Python: Actualizar campos 'porcentaje_mora_individual' y 'dia_vencimiento_individual'
    
    ⚠️ IMPORTANTE:
    - Esta configuración solo aplica si el estudiante NO está en un grupo familiar
    - Si se asigna el estudiante a un grupo familiar después, se usará la mora del grupo
    """)
    print("="*80 + "\n")
