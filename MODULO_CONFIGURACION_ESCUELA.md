# Módulo de Configuración de la Escuela

## Descripción

Este módulo permite a los administradores configurar la información institucional de la escuela que se mostrará en reportes, facturas y documentos oficiales.

## Características

### Información que se puede configurar:

#### Información Básica
- Nombre de la escuela
- RNC
- Dirección
- Teléfono
- Correo electrónico
- Sitio web

#### Identidad Institucional
- Logo de la escuela (200x200px recomendado)
- Lema institucional
- Misión
- Visión

#### Datos Administrativos
- Nombre del director
- Firma del director (imagen con fondo transparente)
- Código del centro educativo
- Distrito educativo
- Regional educativa
- Nivel educativo (Inicial, Básica, Media, etc.)
- Modalidad (General, Técnico-Profesional, etc.)
- Horario de atención
- Año de fundación

#### Configuración de Reportes
- Pie de página para reportes oficiales
- Activar/desactivar logo en reportes

## Uso

### Acceso por Administradores

1. Inicia sesión con un usuario con rol **Administrador** o **Director**
2. Navega a `/configuracion/escuela/`
3. Completa los campos deseados
4. Guarda la configuración

### Acceso desde el Admin de Django

También puedes configurar desde el panel de administración de Django:
1. Accede a `/admin/`
2. Busca "Configuración de la Escuela"
3. Edita el único registro disponible

## Integración en Reportes

Para usar la configuración de la escuela en tus reportes, templates o PDFs:

```python
from escuelaweb.models import ConfiguracionEscuela

def mi_reporte(request):
    config = ConfiguracionEscuela.get_configuracion()
    
    context = {
        'config': config,
        # otros datos...
    }
    
    return render(request, 'mi_reporte.html', context)
```

### En templates HTML/PDF:

```html
{% load static %}

<div class="encabezado-reporte">
    {% if config.mostrar_logo_reportes and config.logo %}
        <img src="{{ config.logo.url }}" alt="Logo" height="80">
    {% endif %}
    
    <h1>{{ config.nombre_escuela }}</h1>
    
    {% if config.lema %}
        <p class="lema">{{ config.lema }}</p>
    {% endif %}
    
    <p>
        {{ config.direccion }}<br>
        Tel: {{ config.telefono }} | Email: {{ config.email }}<br>
        RNC: {{ config.rnc }}
    </p>
</div>

<!-- Contenido del reporte -->

<div class="pie-pagina">
    {{ config.pie_pagina_reportes }}
</div>
```

## Modelo de Datos

### ConfiguracionEscuela

Solo existe **un único registro** en la base de datos. El sistema garantiza esto automáticamente.

**Método principal:**
- `ConfiguracionEscuela.get_configuracion()` - Obtiene o crea la configuración

## Archivos del Módulo

- `models.py` - Modelo ConfiguracionEscuela
- `views.py` - Vista configuracion_escuela
- `admin.py` - Registro en Django Admin
- `templates/est_forder/configuracion_escuela.html` - Template de configuración
- `urls.py` - Ruta: `path("configuracion/escuela/", ...)`

## Permisos

Solo usuarios con rol **Administrador** o **Director** pueden acceder y modificar la configuración.

## Próximos Pasos

1. Crear migraciones: `python manage.py makemigrations`
2. Aplicar migraciones: `python manage.py migrate`
3. Acceder a `/configuracion/escuela/` y completar los datos
4. Integrar en tus reportes existentes (reporte_general, facturas, etc.)

## Ejemplo de Integración en Reporte General

Modifica `reporte_general` en views.py:

```python
def reporte_general(request, curso_id):
    from .models import ConfiguracionEscuela
    
    config = ConfiguracionEscuela.get_configuracion()
    curso = get_object_or_404(Curso, id=curso_id)
    # ... resto del código ...
    
    return render(request, "est_forder/reporte_general.html", {
        "curso": curso,
        "reporte_estudiantes": reporte_estudiantes,
        "config": config,  # <-- Agregar esto
    })
```

Y en el template `reporte_general.html`, agrega el encabezado:

```html
<div class="encabezado-institucional">
    {% if config.logo %}
        <img src="{{ config.logo.url }}" alt="Logo" height="60">
    {% endif %}
    <h2>{{ config.nombre_escuela }}</h2>
    <p>{{ config.direccion }}</p>
</div>
```
