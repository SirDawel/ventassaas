import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import CustomUser

print("\n" + "=" * 80)
print("CONFIGURACIÓN DE MORA POR ESTUDIANTE")
print("=" * 80 + "\n")

estudiantes = CustomUser.objects.filter(rol='Estudiante').select_related('grupo_familiar')[:10]

if not estudiantes:
    print("No se encontraron estudiantes en el sistema.")
else:
    for e in estudiantes:
        print(f"\n📚 Estudiante: {e.get_full_name()} (ID: {e.id})")
        print(f"   Email: {e.email}")
        
        if e.grupo_familiar:
            print(f"   👨‍👩‍👧‍👦 Grupo Familiar: {e.grupo_familiar.apellido_familia}")
            print(f"   └─ Mora del grupo: {e.grupo_familiar.porcentaje_mora}%")
        else:
            print(f"   👤 SIN GRUPO FAMILIAR")
            print(f"   └─ Mora individual: {e.porcentaje_mora_individual}%")
        
        print(f"\n   ✅ Valores efectivos:")
        print(f"   ├─ Día vencimiento: {e.get_dia_vencimiento()}")
        print(f"   └─ Porcentaje mora: {e.get_porcentaje_mora()}%")
        print("-" * 80)

print("\n" + "=" * 80)
print("RESUMEN SOBRE MORA INDIVIDUAL")
print("=" * 80)
print("""
📌 CÓMO FUNCIONA:

1. Si el estudiante ESTÁ en un grupo familiar:
   → Se usa la mora del GRUPO FAMILIAR
   
2. Si el estudiante NO está en un grupo familiar:
   → Se usa la MORA INDIVIDUAL del estudiante

📝 DÓNDE CONFIGURAR LA MORA INDIVIDUAL:

- Interfaz web: Editar Usuario → Sección "Configuración de Mora Individual"
- Admin Django: Panel de administración → Usuarios → Editar

Los campos son:
- Día de vencimiento individual (1-31): Día del mes para vencimiento de pagos
- Porcentaje de mora individual (0-100): Porcentaje de recargo por pagos vencidos
""")
print("=" * 80 + "\n")
