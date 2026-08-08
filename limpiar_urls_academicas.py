"""
Script para comentar URLs académicas (estudiantes, cursos, materias, matrículas, tarifas, etc.)
en el archivo ventasweb/urls.py
"""
import os
import re

archivo_urls = 'ventasweb/urls.py'

# Palabras clave a buscar para comentar las URLs
palabras_clave_comentar = [
    'estudiante', 'curso', 'materia', 'matricula', 'inscrib',
    'tarifa', 'evaluacion', 'rubrica', 'diagnostica', 'portafolio',
    'registro-anecdotico', 'cuaderno', 'lista-cotejo', 'cotejo',
    'asistencia/seleccionar-materia', 'asistencia/pasar-lista', 'asistencia/historial',
    'notas', 'calificacion', 'reporte-notas', 'record-calificaciones',
    'hoja-calificaciones', 'reporte_general', 'reporte_notas'
]

print("Leyendo archivo ventasweb/urls.py...")
with open(archivo_urls, 'r', encoding='utf-8') as f:
    lineas = f.readlines()

nuevas_lineas = []
contador_comentadas = 0
en_bloque_academico = False

for i, linea in enumerate(lineas):
    linea_lower = linea.lower()
    
    # Si es una línea que ya está comentada, mantenerla
    if linea.strip().startswith('#'):
        nuevas_lineas.append(linea)
        continue
    
    # Detectar si es una URL (path(...))
    if 'path(' in linea:
        debe_comentar = False
        
        # Verificar si contiene alguna palabra clave académica
        for palabra in palabras_clave_comentar:
            if palabra in linea_lower:
                debe_comentar = True
                break
        
        if debe_comentar:
            # Si no está ya comentada, comentarla
            if not linea.strip().startswith('#'):
                espacios = len(linea) - len(linea.lstrip())
                nueva_linea = ' ' * espacios + '# ' + linea.lstrip()
                nuevas_lineas.append(nueva_linea)
                contador_comentadas += 1
                print(f"Comentada línea {i+1}: {linea.strip()[:80]}...")
            else:
                nuevas_lineas.append(linea)
        else:
            nuevas_lineas.append(linea)
    else:
        nuevas_lineas.append(linea)

# Escribir el archivo actualizado
print(f"\nEscribiendo cambios a {archivo_urls}...")
with open(archivo_urls, 'w', encoding='utf-8') as f:
    f.writelines(nuevas_lineas)

print(f"\n✅ Proceso completado!")
print(f"   Total de URLs comentadas: {contador_comentadas}")
print(f"\nURLs académicas deshabilitadas. El sistema ahora solo mostrará opciones de ventas.")
