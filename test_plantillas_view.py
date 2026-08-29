import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from ventasweb.views_cotizaciones import plantillas_lista

# Crear un usuario de prueba
User = get_user_model()

try:
    user = User.objects.first()
    if user:
        print(f"Usuario encontrado: {user.email}")
    else:
        print("No hay usuarios en la base de datos")
        user = None
except Exception as e:
    print(f"Error al obtener usuario: {e}")
    user = None

# Intentar acceder a la vista directamente
print("\n=== Probando acceso directo a la vista ===")
try:
    factory = RequestFactory()
    request = factory.get('/plantillas/')
    request.user = user if user else None
    
    response = plantillas_lista(request)
    print(f"✓ Vista ejecutada. Status: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
except Exception as e:
    print(f"✗ Error al ejecutar vista: {type(e).__name__}: {e}")

# Intentar con Django test client
print("\n=== Probando con Django test client ===")
client = Client()
try:
    response = client.get('/plantillas/')
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("❌ Django devuelve 404")
    elif response.status_code == 302:
        print(f"↪ Redirige a: {response.url}")
    elif response.status_code == 200:
        print("✓ Respuesta exitosa")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
