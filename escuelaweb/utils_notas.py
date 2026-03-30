"""
Utilidades para el manejo de notas y calificaciones
"""
from decimal import Decimal, ROUND_HALF_UP


def redondear_nota(valor, decimales=2):
    """
    Redondea una nota usando las reglas matemáticas estándar (ROUND_HALF_UP).
    En el redondeo matemático estándar, .5 siempre se redondea hacia arriba.
    
    Ejemplos:
        70.4 -> 70
        70.5 -> 71
        70.45 -> 70 (con 0 decimales)
        70.45 -> 70.5 (con 1 decimal)
        70.455 -> 70.46 (con 2 decimales)
    
    Args:
        valor: float o int - el valor a redondear
        decimales: int - cantidad de decimales (default: 2)
    
    Returns:
        float - valor redondeado, o None si el valor es None
    """
    if valor is None:
        return None
    
    try:
        # Convertir a Decimal para usar ROUND_HALF_UP
        if isinstance(valor, str):
            valor = valor.replace(',', '.')
        
        decimal_val = Decimal(str(valor))
        
        # Crear el formato de redondeo con la cantidad de decimales especificada
        if decimales == 0:
            formato = Decimal('1')
        else:
            formato = Decimal('0.' + '0' * decimales)
        
        # Redondear usando ROUND_HALF_UP (redondeo matemático estándar)
        redondeado = decimal_val.quantize(formato, rounding=ROUND_HALF_UP)
        
        # Convertir a float si hay decimales, a int si no
        if decimales == 0:
            return int(redondeado)
        else:
            return float(redondeado)
            
    except (ValueError, TypeError, ArithmeticError):
        return None


def redondear_promedio(notas_list):
    """
    Calcula y redondea el promedio de una lista de notas.
    
    Args:
        notas_list: list - lista de notas (pueden contener None)
    
    Returns:
        float - promedio redondeado a 2 decimales, o None si no hay suficientes notas
    """
    valores = []
    for nota in notas_list:
        if nota is not None:
            try:
                if isinstance(nota, str):
                    nota = nota.replace(',', '.')
                valores.append(float(nota))
            except (ValueError, TypeError):
                pass
    
    if not valores or len(valores) < len(notas_list):
        return None
    
    promedio = sum(valores) / len(valores)
    return redondear_nota(promedio, decimales=2)


def calcular_nota_completiva(promedio_final, examen_completivo):
    """
    Calcula la nota completiva: 50% promedio + 50% examen
    
    Args:
        promedio_final: float - promedio del período
        examen_completivo: float - nota del examen completivo
    
    Returns:
        float - nota completiva redondeada a 2 decimales
    """
    if promedio_final is None or examen_completivo is None:
        return None
    
    nota = (float(promedio_final) * 0.50) + (float(examen_completivo) * 0.50)
    return redondear_nota(nota, decimales=2)


def calcular_nota_extraordinaria(promedio_final, examen_extraordinario):
    """
    Calcula la nota extraordinaria: 30% promedio + 70% examen
    
    Args:
        promedio_final: float - promedio del período
        examen_extraordinario: float - nota del examen extraordinario
    
    Returns:
        float - nota extraordinaria redondeada a 2 decimales
    """
    if promedio_final is None or examen_extraordinario is None:
        return None
    
    nota = (float(promedio_final) * 0.30) + (float(examen_extraordinario) * 0.70)
    return redondear_nota(nota, decimales=2)
