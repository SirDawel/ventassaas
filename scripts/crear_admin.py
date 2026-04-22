import os
import sys

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')

import django
django.setup()

from escuelaweb.models import CustomUser

# Crear usuario administrador
print("\n" + "="*70)
print("CREAR USUARIO ADMINISTRADOR")
print("="*70 + "\n")

try:
    # Verificar si ya existe
    try:
        user = CustomUser.objects.get(email='admin@escuela.com')
        print("Usuario ya existe. Actualizando...")
        action = "Actualizado"
    except CustomUser.DoesNotExist:
        user = CustomUser()
        user.email = 'admin@escuela.com'
        action = "Creado"
    
    # Configurar datos
    user.first_name = 'Admin'
    user.last_name = 'Sistema'
    user.rol = 'Administrador'
    user.is_staff = True
    user.is_active = True
    user.is_superuser = True
    user.set_password('admin123')
    user.save()
    
    print(f"✅ {action} usuario administrador!\n")
    print("Credenciales:")
    print("-" * 70)
    print(f"  Email/Usuario: admin@escuela.com")
    print(f"  Contraseña:    admin123")
    print(f"  Rol:           {user.rol}")
    print("-" * 70)
    print("\nAcceso a facturas:")
    print("  1. Ir a: http://127.0.0.1:8000/")
    print("  2. Iniciar sesión con las credenciales de arriba")
    print("  3. Visitar: http://127.0.0.1:8000/facturas/")
    print("\n" + "="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}\n")
    import traceback
    traceback.print_exc()
