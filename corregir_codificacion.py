#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir caracteres especiales mal codificados en archivos Python
Convierte caracteres UTF-8 mal interpretados a su forma correcta
"""

import os
import re
from pathlib import Path

# Mapeo de caracteres mal codificados a sus equivalentes correctos
REEMPLAZOS = {
    'página': 'página',
    'está': 'está',
    'sesión': 'sesión',
    'contraseña': 'contraseña',
    'electrónico': 'electrónico',
    'activación': 'activación',
    'válido': 'válido',
    'después': 'después',
    'Después': 'Después',
    'múltiples': 'múltiples',
    'Múltiples': 'Múltiples',
    'último': 'último',
    'éxito': 'éxito',
    'año': 'año',
    'Año': 'Año',
    'años': 'años',
    'Años': 'Años',
    'búsqueda': 'búsqueda',
    'Búsqueda': 'Búsqueda',
    'período': 'período',
    'Período': 'Período',
    'método': 'método',
    'Método': 'Método',
    'día': 'día',
    'Día': 'Día',
    'días': 'días',
    'Días': 'Días',
    'información': 'información',
    'Información': 'Información',
    'código': 'código',
    'Código': 'Código',
    'número': 'número',
    'Número': 'Número',
    'automático': 'automático',
    'matemático': 'matemático',
    'evaluación': 'evaluación',
    'Evaluación': 'Evaluación',
    'configuración': 'configuración',
    'Configuración': 'Configuración',
    'miércoles': 'miércoles',
    'Miércoles': 'Miércoles',
    'sábado': 'sábado',
    'Sábado': 'Sábado',
    'análisis': 'análisis',
    'Análisis': 'Análisis',
    'estadísticas': 'estadísticas',
    'Estadísticas': 'Estadísticas',
    'gráfico': 'gráfico',
    'Gráfico': 'Gráfico',
    'MÉTRICAS': 'MÉTRICAS',
    'métricas': 'métricas',
    'Métricas': 'Métricas',
    'comparación': 'comparación',
    'Comparación': 'Comparación',
    'artículos': 'artículos',
    'Artículos': 'Artículos',
    'categoría': 'categoría',
    'Categoría': 'Categoría',
    'descripción': 'descripción',
    'Descripción': 'Descripción',
    'título': 'título',
    'Título': 'Título',
    'parámetros': 'parámetros',
    'Parámetros': 'Parámetros',
    'técnico': 'técnico',
    'Técnico': 'Técnico',
    'auditoría': 'auditoría',
    'Auditoría': 'Auditoría',
    'redirección': 'redirección',
    'eliminación': 'eliminación',
    'Eliminación': 'Eliminación',
    'operación': 'operación',
    'Operación': 'Operación',
    'sección': 'sección',
    'Sección': 'Sección',
    'función': 'función',
    'Función': 'Función',
    'versión': 'versión',
    'Versión': 'Versión',
    'imágenes': 'imágenes',
    'básicos': 'básicos',
    'autenticación': 'autenticación',
    'guardarán': 'guardarán',
    'Recuperación': 'Recuperación',
    'recuperación': 'recuperación',
    '¡': '¡',
    '¿': '¿',
    '': '',
    '': '',
    '': '',
    '': '',
    '': '',
    'paréntesis': 'paréntesis',
    'están': 'están',
    'qué': 'qué',
    'Qué': 'Qué',
    'también': 'también',
    'También': 'También',
    'será': 'será',
    'Será': 'Será',
    'serán': 'serán',
    'última': 'última',
    'órdenes': 'órdenes',
    'físicos': 'físicos',    'automáticamente': 'automáticamente',
    'dinámica': 'dinámica',
    'Dinámico': 'Dinámico',
    'según': 'según',
    'Según': 'Según',
    'encontró': 'encontró',
    'petición': 'petición',
    'PETICIÓN': 'PETICIÓN',
    'lógica': 'lógica',
    'Lógica': 'Lógica',
    'obligatoriedad': 'obligatoriedad',
    '⚠️': '⚠️',
    '✓': '✓',
    '': '',
    '': '',
    '': '',
    ''': "'",
    '-': '-',
    'cuántos': 'cuántos',
    'anulación': 'anulación',
    'acción': 'acción',
    'Validación': 'Validación',
    'validación': 'validación',
    'confirmación': 'confirmación',
    'PETICIÓN': 'PETICIÓN',    'Contraseña': 'Contraseña',
    'contraseña': 'contraseña',
    'eliminó': 'eliminó',
    'matrículas': 'matrículas',}

def corregir_archivo(ruta_archivo):
    """Corrige la codificación de un archivo"""
    try:
        # Leer el archivo con diferentes codificaciones
        contenido = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(ruta_archivo, 'r', encoding=encoding) as f:
                    contenido = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if contenido is None:
            print(f"❌ No se pudo leer: {ruta_archivo}")
            return False
        
        contenido_original = contenido
        
        # Aplicar todos los reemplazos
        for mal_codificado, correcto in REEMPLAZOS.items():
            contenido = contenido.replace(mal_codificado, correcto)
        
        # Si hubo cambios, guardar el archivo
        if contenido != contenido_original:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            print(f"✅ Corregido: {ruta_archivo}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error en {ruta_archivo}: {str(e)}")
        return False

def main():
    """Procesa todos los archivos Python en el proyecto"""
    base_dir = Path(__file__).parent
    archivos_corregidos = 0
    archivos_procesados = 0
    
    print("🔍 Buscando archivos Python con problemas de codificación...\n")
    
    # Buscar todos los archivos .py
    for archivo in base_dir.rglob('*.py'):
        # Saltar directorios virtuales y cache
        if any(parte in str(archivo) for parte in ['.venv', 'venv', '__pycache__', '.git']):
            continue
        
        archivos_procesados += 1
        if corregir_archivo(archivo):
            archivos_corregidos += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Resumen:")
    print(f"   - Archivos procesados: {archivos_procesados}")
    print(f"   - Archivos corregidos: {archivos_corregidos}")
    print(f"{'='*60}")
    
    if archivos_corregidos > 0:
        print("\n✅ ¡Corrección completada exitosamente!")
    else:
        print("\n✅ No se encontraron archivos con problemas de codificación.")

if __name__ == '__main__':
    main()
