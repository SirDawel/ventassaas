#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir caracteres especiales mal codificados
"""

from pathlib import Path

# Reemplazos de caracteres mal codificados
REEMPLAZOS = {
    'página': 'página',
    'está': 'está',
    'están': 'están',
    'sesión': 'sesión',
    'contraseña': 'contraseña',
    'Contraseña': 'Contraseña',
    'electrónico': 'electrónico',
    'activación': 'activación',
    'válido': 'válido',
    'después': 'después',
    'múltiples': 'múltiples',
    'último': 'último',
    'última': 'última',
    'éxito': 'éxito',
    'año': 'año',
    'Año': 'Año',
    'años': 'años',
    'búsqueda': 'búsqueda',
    'período': 'período',
    'método': 'método',
    'día': 'día',
    'días': 'días',
    'información': 'información',
    'código': 'código',
    'número': 'número',
    'automático': 'automático',
    'automáticamente': 'automáticamente',
    'matemático': 'matemático',
    'evaluación': 'evaluación',
    'configuración': 'configuración',
    'miércoles': 'miércoles',
    'sábado': 'sábado',
    'análisis': 'análisis',
    'estadísticas': 'estadísticas',
    'gráfico': 'gráfico',
    'MÉTRICAS': 'MÉTRICAS',
    'métricas': 'métricas',
    'comparación': 'comparación',
    'artículos': 'artículos',
    'categoría': 'categoría',
    'descripción': 'descripción',
    'título': 'título',
    'parámetros': 'parámetros',
    'técnico': 'técnico',
    'auditoría': 'auditoría',
    'eliminación': 'eliminación',
    'eliminó': 'eliminó',
    'operación': 'operación',
    'sección': 'sección',
    'función': 'función',
    'versión': 'versión',
    'imágenes': 'imágenes',
    'básicos': 'básicos',
    'autenticación': 'autenticación',
    'guardarán': 'guardarán',
    'Recuperación': 'Recuperación',
    'qué': 'qué',
    'también': 'también',
    'será': 'será',
    'serán': 'serán',
    'órdenes': 'órdenes',
    'físicos': 'físicos',
    'crédito': 'crédito',
    'débito': 'débito',
    'dinámica': 'dinámica',
    'según': 'según',
    'encontró': 'encontró',
    'petición': 'petición',
    'PETICIÓN': 'PETICIÓN',
    'lógica': 'lógica',
    'cuántos': 'cuántos',
    'anulación': 'anulación',
    'acción': 'acción',
    'Validación': 'Validación',
    'validación': 'validación',
    'confirmación': 'confirmación',
    'matrículas': 'matrículas',    'PETICIÓN': 'PETICIÓN',
    'ELIMINACIÓN': 'ELIMINACIÓN',
    'botón': 'botón',}

def corregir_archivo(ruta_archivo):
    """Corrige la codificación de un archivo"""
    try:
        contenido = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(ruta_archivo, 'r', encoding=encoding) as f:
                    contenido = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if contenido is None:
            return False
        
        contenido_original = contenido
        
        for mal_codificado, correcto in REEMPLAZOS.items():
            contenido = contenido.replace(mal_codificado, correcto)
        
        if contenido != contenido_original:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            print(f"✅ Corregido: {ruta_archivo}")
            return True
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
    
    for archivo in base_dir.rglob('*.py'):
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
