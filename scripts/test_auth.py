"""
Script para probar la autenticación y verificar configuración de usuarios
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django.contrib.auth import authenticate
from escuelaweb.models import CustomUser
from django.db import connection

print("=" * 70)
print("TEST DE AUTENTICACIÓN")
print("=" * 70)

# 1. Verificar conexión a base de datos
print("\n1. Verificando conexión a base de datos...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   ✓ Conectado a PostgreSQL: {version[0]}")
except Exception as e:
    print(f"   ✗ Error de conexión: {e}")

# 2. Listar usuarios activos
print("\n2. Usuarios activos en el sistema:")
print("   " + "-" * 66)
users = CustomUser.objects.filter(is_active=True)[:5]
for user in users:
    print(f"   Email: {user.email:40} | Rol: {user.rol:15} | Active: {user.is_active}")
    print(f"   Has password: {user.has_usable_password():5} | Can login: {user.check_password('test')}")
    print(f"   Password hash: {user.password[:60]}...")
    print("   " + "-" * 66)

# 3. Solicitar credenciales para probar
print("\n3. Prueba de autenticación:")
print("   Ingresa las credenciales para probar el login\n")

email = input("   Email: ").strip()
password = input("   Password: ").strip()

print(f"\n   Intentando autenticar: {email}")

# 4. Verificar si el usuario existe
print("\n4. Verificando usuario en base de datos...")
try:
    user = CustomUser.objects.get(email=email)
    print(f"   ✓ Usuario encontrado: {user.get_full_name()}")
    print(f"   - Rol: {user.rol}")
    print(f"   - Activo: {user.is_active}")
    print(f"   - Staff: {user.is_staff}")
    print(f"   - Password usable: {user.has_usable_password()}")
    print(f"   - Check password: {user.check_password(password)}")
except CustomUser.DoesNotExist:
    print(f"   ✗ Usuario no encontrado con email: {email}")
    print("\n" + "=" * 70)
    exit()

# 5. Probar autenticación con el backend
print("\n5. Probando autenticación con authenticate()...")
authenticated_user = authenticate(username=email, password=password)

if authenticated_user:
    print(f"   ✓ AUTENTICACIÓN EXITOSA")
    print(f"   - Usuario: {authenticated_user.get_full_name()}")
    print(f"   - Email: {authenticated_user.email}")
    print(f"   - Rol: {authenticated_user.rol}")
else:
    print(f"   ✗ AUTENTICACIÓN FALLIDA")
    print(f"   - El usuario existe pero las credenciales no coinciden")
    print(f"   - Verifica que la contraseña sea correcta")

print("\n" + "=" * 70)
print("TEST COMPLETADO")
print("=" * 70)
