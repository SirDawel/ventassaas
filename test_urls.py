import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.urls import reverse, resolve
from django.conf import settings

# Probar si la URL de plantillas está registrada
try:
    url = reverse('plantillas_lista')
    print(f"✓ URL reverse funciona: {url}")
except Exception as e:
    print(f"✗ Error en reverse: {e}")

# Probar si el resolver puede encontrar la URL
try:
    match = resolve('/plantillas/')
    print(f"✓ Resolver encontró: {match.func.__name__} en {match.func.__module__}")
except Exception as e:
    print(f"✗ Error en resolver: {e}")

# Listar todas las URLs que contienen 'plantillas'
from django.urls import get_resolver
resolver = get_resolver()
print("\n=== URLs que contienen 'plantillas' ===")
for pattern in resolver.url_patterns:
    try:
        pattern_str = str(pattern.pattern)
        if 'plantillas' in pattern_str:
            print(f"  - {pattern_str}")
    except:
        pass
