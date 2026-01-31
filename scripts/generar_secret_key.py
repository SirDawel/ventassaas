#!/usr/bin/env python
"""
Script para generar una SECRET_KEY segura para Django
"""
from django.core.management.utils import get_random_secret_key

print("=" * 60)
print("NUEVA SECRET_KEY PARA DJANGO")
print("=" * 60)
print("\nCopia esta clave y úsala en tu archivo .env:")
print("\nSECRET_KEY=" + get_random_secret_key())
print("\n" + "=" * 60)
print("⚠️  IMPORTANTE: Guarda esta clave de forma segura")
print("=" * 60)
