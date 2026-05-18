"""Context processors for shared template data."""

from .models import ConfiguracionEscuela


def school_configuration(request):
    """Expose school configuration values to all templates safely."""
    default_name = "Mi Escuela"

    try:
        config = ConfiguracionEscuela.get_configuracion()
        school_name = (config.nombre_escuela or default_name).strip()
    except Exception:
        config = None
        school_name = default_name

    return {
        "configuracion_escuela": config,
        "nombre_escuela_config": school_name,
    }
