from django import template

register = template.Library()

@register.filter
def get_nota(matricula, materia_id):
    # Si la matrícula corresponde a la materia, devuelve la nota final
    if hasattr(matricula, 'materia') and matricula.materia.id == materia_id:
        return getattr(matricula, 'nota_final', None)
    return None

from django import template

register = template.Library()

@register.filter
def get_ra(obj, idx):
    try:
        return getattr(obj, f'ra_{int(idx)+1}', '')
    except:
        return ''

@register.filter
def range_filter(n):
    try:
        return range(int(n))
    except:
        return range(0)

@register.filter
def index(Lista, i):
    try:
        return Lista[int(i)]
    except:
        return ''

@register.filter
def get_attr(obj, attr_name):
    """Obtiene el valor de un atributo dinámico de un objeto."""
    return getattr(obj, attr_name, '')

@register.filter
def get_value(obj, field_name):
    """Devuelve el valor de un campo o atributo dinámico."""
    return getattr(obj, field_name, '')

@register.filter
def get_dynamic_value(obj, prefix_and_number):
    """
    Permite obtener valores como com_p1, com_p2, etc.
    Ejemplo:
    {{ matricula|get_dynamic_value:'com_p1' }}
    """
    return getattr(obj, prefix_and_number, '')

@register.filter
def attr(obj, name):
    return getattr(obj, name)

@register.filter
def get_item(dictionary, key):
    """Obtiene un item de un diccionario usando una clave dinámica."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide el valor por el argumento"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def calcular_edad(fecha_nacimiento):
    """Calcula la edad a partir de la fecha de nacimiento"""
    if not fecha_nacimiento:
        return None
    try:
        from datetime import date
        today = date.today()
        edad = today.year - fecha_nacimiento.year
        # Ajustar si aún no ha cumplido años este año
        if (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1
        return edad
    except:
        return None

@register.filter
def formato_nota(valor, decimales=2):
    """
    Formatea una nota aplicando redondeo matemático estándar (ROUND_HALF_UP).
    Retorna el valor redondeado con el número de decimales especificado.
    
    Uso en templates:
        {{ nota|formato_nota }}          -> redondea a 2 decimales (default)
        {{ nota|formato_nota:0 }}        -> redondea a entero
        {{ promedio|formato_nota:1 }}    -> redondea a 1 decimal
    """
    if valor is None or valor == '':
        return '-'
    
    try:
        from escuelaweb.utils_notas import redondear_nota
        # Convertir decimales a int
        try:
            decimales = int(decimales)
        except:
            decimales = 2
        
        resultado = redondear_nota(valor, decimales=decimales)
        
        # Formatear con los decimales especificados
        if decimales == 0:
            return int(resultado)
        else:
            return f"{resultado:.{decimales}f}"
    except:
        return str(valor)
