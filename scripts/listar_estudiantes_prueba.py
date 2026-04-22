import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')

import django
django.setup()

from escuelaweb.models import CustomUser, Factura

# Buscar estudiantes con cédula
estudiantes = CustomUser.objects.filter(
    rol='Estudiante', 
    is_active=True
).exclude(cedula__isnull=True).exclude(cedula='')[:10]

print("=" * 60)
print("ESTUDIANTES CON CÉDULA PARA PRUEBA")
print("=" * 60)

if estudiantes.exists():
    for e in estudiantes:
        facturas_pendientes = Factura.objects.filter(
            cliente=e, 
            estado__in=['pendiente', 'vencida', 'parcial']
        ).count()
        
        print(f"\n📋 {e.get_full_name()}")
        print(f"   Cédula: {e.cedula}")
        print(f"   Email: {e.email}")
        print(f"   Facturas pendientes: {facturas_pendientes}")
else:
    print("\n⚠️  No hay estudiantes con cédula registrada")
    print("Para la prueba, usaremos una cédula ficticia: 402-1234567-8")
