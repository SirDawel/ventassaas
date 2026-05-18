"""
Script para eliminar campos escuela FK y TenantManager de models.py
"""
import re

def limpiar_models_py():
    """Elimina campos escuela y objects = TenantManager() de models.py"""
    
    with open('escuelaweb/models.py', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    lineas = contenido.split('\n')
    lineas_nuevas = []
    i = 0
    
    while i < len(lineas):
        linea = lineas[i]
        
        # Caso 1: Eliminar línea "objects = TenantManager()"
        if re.match(r'^\s*objects\s*=\s*TenantManager\(\)\s*$', linea):
            print(f"❌ Eliminando línea {i+1}: {linea.strip()}")
            i += 1
            continue
        
        # Caso 2: Eliminar campo escuela FK (puede ser multi-línea)
        if re.match(r'^\s*escuela\s*=\s*models\.ForeignKey\s*\(', linea):
            print(f"❌ Eliminando campo escuela FK en línea {i+1}")
            
            # Si la línea termina con ), es una sola línea
            if ')' in linea:
                i += 1
                continue
            
            # Si no, buscar el cierre del paréntesis
            i += 1
            while i < len(lineas) and ')' not in lineas[i]:
                print(f"   ... continuación en línea {i+1}")
                i += 1
            
            # Saltar también la línea con el cierre
            if i < len(lineas):
                print(f"   ... cierre en línea {i+1}")
                i += 1
            continue
        
        # Mantener la línea
        lineas_nuevas.append(linea)
        i += 1
    
    # Escribir el resultado
    with open('escuelaweb/models.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lineas_nuevas))
    
    print(f"\n✅ Archivo models.py limpiado")
    print(f"📊 Líneas originales: {len(lineas)}")
    print(f"📊 Líneas nuevas: {len(lineas_nuevas)}")
    print(f"📊 Líneas eliminadas: {len(lineas) - len(lineas_nuevas)}")

if __name__ == '__main__':
    limpiar_models_py()
