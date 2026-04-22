import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
import django
django.setup()

from escuelaweb.models import CustomUser

print("\n" + "="*70)
print("👥 USUARIOS DEL SISTEMA")
print("="*70 + "\n")

# Mostrar administradores y secretarias
admins = CustomUser.objects.filter(is_active=True, rol='Administrador')
secretarias = CustomUser.objects.filter(is_active=True, rol='Secretaria')

print("🔐 ADMINISTRADORES:")
for u in admins:
    print(f"   {u.username} - {u.get_full_name()}")

print("\n📝 SECRETARIAS:")
for u in secretarias:
    print(f"   {u.username} - {u.get_full_name()}")

print("\n" + "="*70)
print("💡 ACCESO A /facturas/:")
print("   Requiere rol: Secretaria o Administrador")
print("="*70 + "\n")
