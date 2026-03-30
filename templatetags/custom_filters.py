from django import template
register = template.Library()

@register.filter
def dict_key(d, key):
    """Devuelve el valor de un diccionario por su clave."""
    try:
        return d.get(key)
    except Exception:
        return ''

@register.filter
def get_item(dictionary, key):
    """Obtiene un item de un diccionario usando una clave."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
