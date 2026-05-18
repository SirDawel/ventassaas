#!/usr/bin/env python
"""
Script para eliminar null=True y blank=True de los campos escuela
"""
import re

# Leer el archivo
with open('escuelaweb/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para buscar campos escuela con null=True, blank=True
pattern = r"(# Multi-Tenant: Escuela\s+escuela = models\.ForeignKey\(\s+'Escuela',\s+on_delete=models\.PROTECT,\s+related_name='[^']+',\s+verbose_name=\"Escuela\",)\s+null=True,\s+blank=True(\s+\))"

# Reemplazar eliminando null=True y blank=True
new_content = re.sub(pattern, r'\1\2', content)

# Contar cambios
original_count = content.count('null=True,\n        blank=True\n    )')
new_count = new_content.count('null=True,\n        blank=True\n    )')
cambios = original_count - new_count

print(f"Campos escuela con null=True encontrados: {cambios}")

# Guardar el archivo
with open('escuelaweb/models.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Archivo actualizado correctamente")
