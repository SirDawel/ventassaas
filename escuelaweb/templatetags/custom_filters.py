
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
