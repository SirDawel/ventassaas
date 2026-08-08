import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import CustomUser

print("\n" + "=" * 80)
print("CONFIGURACIÓN DE DESCUENTO POR ESTUDIANTE")
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
            print(f"   └─ Descuento del grupo: {e.grupo_familiar.descuento_general}%")
        else:
            print(f"   👤 SIN GRUPO FAMILIAR")
            print(f"   └─ Descuento individual: {e.descuento_individual}%")
        
        print(f"\n   ✅ Descuento efectivo aplicable: {e.get_descuento()}%")
        print("-" * 80)

print("\n" + "=" * 80)
print("RESUMEN SOBRE DESCUENTO INDIVIDUAL")
print("=" * 80)
print("""
📌 CÓMO FUNCIONA:

1. Si el estudiante ESTÁ en un grupo familiar:
   → Se usa el DESCUENTO DEL GRUPO FAMILIAR
   
2. Si el estudiante NO está en un grupo familiar:
   → Se usa el DESCUENTO INDIVIDUAL del estudiante

📝 DÓNDE CONFIGURAR EL DESCUENTO INDIVIDUAL:

- Interfaz web: Editar Usuario → Sección "Configuración de Descuento Individual"
- Admin Django: Panel de administración → Usuarios → Editar

El campo es:
- Descuento Individual (0-100%): Porcentaje de descuento en mensualidades, 
  inscripción y transporte

💡 EJEMPLO DE USO:

# Configurar descuento individual para un estudiante
from escuelaweb.models import CustomUser

estudiante = CustomUser.objects.get(id=497)  # Reemplazar con ID correcto
estudiante.descuento_individual = 10.00  # 10% de descuento
estudiante.save()

print(f"✅ Descuento configurado para {estudiante.get_full_name()}")
print(f"   Descuento efectivo: {estudiante.get_descuento()}%")
""")
print("=" * 80 + "\n")
