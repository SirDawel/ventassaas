#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir caracteres especiales mal codificados en archivos HTML y templates
"""

from pathlib import Path

# Mapeo de caracteres mal codificados
REEMPLAZOS = {
    'página': 'página',
    'está': 'está',
    'sesión': 'sesión',
    'contraseña': 'contraseña',
    'electrónico': 'electrónico',
    'activación': 'activación',
    'válido': 'válido',
    'después': 'después',
    'múltiples': 'múltiples',
    'último': 'último',
    'éxito': 'éxito',
    'año': 'año',
    'Año': 'Año',
    'años': 'años',
    'búsqueda': 'búsqueda',
    'período': 'período',
    'método': 'método',
    'día': 'día',
    'DÃ­a': 'Día',
    'días': 'días',
    'información': 'información',
    'InformaciÃ³n': 'Información',
    'código': 'código',
    'CÃ³digo': 'Código',
    'número': 'número',
    'NÃºmero': 'Número',
    'evaluación': 'evaluación',
    'configuración': 'configuración',
    'miércoles': 'miércoles',
    'MiÃ©rcoles': 'Miércoles',
    'sábado': 'sábado',
    'análisis': 'análisis',
    'AnÃ¡lisis': 'Análisis',
    'estadísticas': 'estadísticas',
    'gráfico': 'gráfico',
    'MÉTRICAS': 'MÉTRICAS',
    'métricas': 'métricas',
    'comparación': 'comparación',
    'artículos': 'artículos',
    'ArtÃ­culos': 'Artículos',
    'categoría': 'categoría',
    'descripción': 'descripción',
    'título': 'título',
    'TÃ­tulo': 'Título',
    'parámetros': 'parámetros',
    'técnico': 'técnico',
    'auditoría': 'auditoría',
    'eliminación': 'eliminación',
    'operación': 'operación',
    'sección': 'sección',
    'función': 'función',
    'versión': 'versión',
    'imágenes': 'imágenes',
    'autenticación': 'autenticación',
    'Recuperación': 'Recuperación',
    'recuperaciÃ³n': 'recuperación',
    '✓ ': '',
    'están': 'están',
    'qué': 'qué',
    'también': 'también',
    'será': 'será',
    'serán': 'serán',
    'órdenes': 'órdenes',
    'físicos': 'físicos',
    'crédito': 'crédito',
    'débito': 'débito',
    'facturaci�ón': 'facturación',
    'transacci�ón': 'transacción',
    'registr�ó': 'registró',
    'creaci�ón': 'creación',
    'modificaci�ón': 'modificación',
    'notificaci�ón': 'notificación',
}

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
        
        # Aplicar reemplazos
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
    """Procesa todos los archivos HTML, MD y TXT"""
    base_dir = Path(__file__).parent
    archivos_corregidos = 0
    archivos_procesados = 0
    
    print("🔍 Buscando archivos HTML/MD/TXT con problemas de codificación...\n")
    
    extensiones = ['*.html', '*.md', '*.txt', '*.js', '*.css']
    
    for extension in extensiones:
        for archivo in base_dir.rglob(extension):
            if any(parte in str(archivo) for parte in ['.venv', 'venv', '__pycache__', '.git', 'node_modules']):
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
