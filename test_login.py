import django
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django.contrib.auth import authenticate
from escuelaweb.models import CustomUser

print("=" * 70)
print("PRUEBA DE AUTENTICACIÓN")
print("=" * 70)

# Probar con el usuario admin
email = 'admin.test@example.com'
passwords_to_test = ['admin123', 'Admin123', '123456', 'password', 'admin', 'test123']

try:
    user = CustomUser.objects.get(email=email)
    print(f"\nUsuario encontrado: {user.email}")
    print(f"Nombre: {user.get_full_name()}")
    print(f"Rol: {user.rol}")
    print(f"Activo: {user.is_active}")
    print(f"Staff: {user.is_staff}")
    print(f"Has usable password: {user.has_usable_password()}")
    print(f"\nPassword hash: {user.password}")
    
    print("\n" + "-" * 70)
    print("Probando diferentes contraseñas:")
    print("-" * 70)
    
    for pwd in passwords_to_test:
        result = user.check_password(pwd)
        auth_result = authenticate(username=email, password=pwd)
        print(f"Password '{pwd}': check_password={result}, authenticate={'✓' if auth_result else '✗'}")
        
        if result:
            print(f"\n¡CONTRASEÑA CORRECTA ENCONTRADA: '{pwd}'!")
            break
    
except CustomUser.DoesNotExist:
    print(f"Usuario no encontrado: {email}")

print("\n" + "=" * 70)
