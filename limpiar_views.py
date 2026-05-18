#!/usr/bin/env python
"""Script para limpiar última línea de views.py con encoding corrupto"""

# Leer archivo con latin-1
with open('escuelaweb/views.py', 'r', encoding='latin-1') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print(f"Last line: {repr(lines[-1])}")

# Eliminar última línea si es un comentario corrupto
if lines[-1].strip().startswith('#'):
    print("Eliminando última línea corrupta...")
    lines = lines[:-1]

# Escribir con UTF-8
with open('escuelaweb/views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Archivo limpiado correctamente")
