import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
import django
django.setup()

from escuelaweb.models import CustomUser

print("="*70)
print("USUARIOS DEL SISTEMA")
print("="*70)

# Listar todos los usuarios activos
usuarios = CustomUser.objects.filter(is_active=True).order_by('rol', 'first_name')

if not usuarios.exists():
    print("\nNo hay usuarios activos en el sistema")
else:
    print(f"\nTotal usuarios activos: {usuarios.count()}\n")
    
    roles = {}
    for user in usuarios:
        rol = user.rol or 'Sin rol'
        if rol not in roles:
            roles[rol] = []
        roles[rol].append(user)
    
    for rol, users in sorted(roles.items()):
        print(f"\n{rol.upper()}:")
        print("-"*70)
        for user in users:
            print(f"  Usuario: {user.username or user.email}")
            print(f"  Nombre: {user.get_full_name()}")
            print(f"  Email: {user.email}")
            print()

print("="*70)
