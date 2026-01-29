from django import template
register = template.Library()

@register.filter
def dict_key(d, key):
    """Devuelve el valor de un diccionario por su clave."""
    try:
        return d.get(key)
    except Exception:
        return ''
