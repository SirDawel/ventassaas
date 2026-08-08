"""
Script para listar todas las URLs registradas en Django
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def list_urls(lis, acc=None):
    if acc is None:
        acc = []
    if not lis:
        return
    l = lis[0]
    if isinstance(l, URLPattern):
        yield acc + [str(l.pattern)], l.name
    elif isinstance(l, URLResolver):
        yield from list_urls(l.url_patterns, acc + [str(l.pattern)])
    yield from list_urls(lis[1:], acc)

print("URLs registradas en el sistema:")
print("=" * 70)

resolver = get_resolver()
urls_con_nombre = []

for p, name in list_urls(resolver.url_patterns):
    url = ''.join(p)
    if name:
        urls_con_nombre.append((url, name))

# Filtrar solo las que contienen 'plataform', 'index', 'base', 'login'
palabras_clave = ['plataform', 'index', 'base', 'login', 'noticias']

print("\nURLs relevantes encontradas:")
for url, name in sorted(urls_con_nombre):
    if any(palabra in name.lower() or palabra in url.lower() for palabra in palabras_clave):
        print(f"  {name:30} -> {url}")

print("\nBuscando específicamente 'plataform':")
plataform_urls = [(url, name) for url, name in urls_con_nombre if 'plataform' in name.lower()]
if plataform_urls:
    for url, name in plataform_urls:
        print(f"  ✓ {name:30} -> {url}")
else:
    print("  ✗ No se encontró ninguna URL con nombre 'plataform'")
