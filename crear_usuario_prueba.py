import django
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import CustomUser
from django.contrib.auth import authenticate

print("=" * 70)
print("CREAR USUARIO DE PRUEBA")
print("=" * 70)

# Crear o actualizar usuario de prueba
user, created = CustomUser.objects.get_or_create(
    email='test@login.com',
    defaults={
        'first_name': 'Test',
        'last_name': 'Login',
        'rol': 'Administrador',
        'is_staff': True,
        'is_active': True
    }
)

# Establecer contraseña
user.set_password('123456')
user.save()

print(f"\n{'Creado' if created else 'Actualizado'} usuario: {user.email}")
print(f"Nombre: {user.get_full_name()}")
print(f"Rol: {user.rol}")
print(f"Contraseña establecida: 123456")

# Probar autenticación
print("\n" + "-" * 70)
print("Probando autenticación...")
print("-" * 70)

auth_user = authenticate(username='test@login.com', password='123456')

if auth_user:
    print("✓ AUTENTICACIÓN EXITOSA")
    print(f"  Usuario autenticado: {auth_user.get_full_name()}")
else:
    print("✗ AUTENTICACIÓN FALLIDA")
    print("  Hay un problema con el backend de autenticación")

print("\n" + "=" * 70)
print("INSTRUCCIONES:")
print("=" * 70)
print("\nAhora puedes probar el login con:")
print("  Email: test@login.com")
print("  Password: 123456")
print("\n" + "=" * 70)
