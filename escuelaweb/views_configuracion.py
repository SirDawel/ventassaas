"""
Vistas para la gestión de configuración de la escuela
"""
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import ConfiguracionEscuela
from .decorators import role_required


@login_required
@role_required('Administrador', 'Director')
def configuracion_escuela(request):
    """Vista para mostrar y editar la configuración de la escuela"""
    config = ConfiguracionEscuela.get_configuracion()
    
    if request.method == 'POST':
        # Actualizar campos básicos
        config.nombre_escuela = request.POST.get('nombre_escuela', '')
        config.rnc = request.POST.get('rnc', '')
        config.direccion = request.POST.get('direccion', '')
        config.telefono = request.POST.get('telefono', '')
        config.email = request.POST.get('email', '')
        config.sitio_web = request.POST.get('sitio_web', '')
        config.lema = request.POST.get('lema', '')
        config.mision = request.POST.get('mision', '')
        config.vision = request.POST.get('vision', '')
        
        # Información administrativa
        config.director_nombre = request.POST.get('director_nombre', '')
        config.codigo_centro = request.POST.get('codigo_centro', '')
        config.distrito_educativo = request.POST.get('distrito_educativo', '')
        config.regional_educativa = request.POST.get('regional_educativa', '')
        config.nivel_educativo = request.POST.get('nivel_educativo', '')
        config.modalidad = request.POST.get('modalidad', '')
        config.horario_atencion = request.POST.get('horario_atencion', '')
        
        # Año de fundación
        anho_fundacion = request.POST.get('anho_fundacion', '')
        if anho_fundacion:
            try:
                config.anho_fundacion = int(anho_fundacion)
            except ValueError:
                config.anho_fundacion = None
        else:
            config.anho_fundacion = None
        
        # Configuración de reportes
        config.pie_pagina_reportes = request.POST.get('pie_pagina_reportes', '')
        config.mostrar_logo_reportes = request.POST.get('mostrar_logo_reportes') == 'on'
        
        # Manejo de archivos
        if 'logo' in request.FILES:
            config.logo = request.FILES['logo']
        
        if 'director_firma' in request.FILES:
            config.director_firma = request.FILES['director_firma']
        
        # Eliminar logo si se solicita
        if request.POST.get('eliminar_logo') == 'on' and config.logo:
            config.logo.delete()
            config.logo = None
        
        # Eliminar firma si se solicita
        if request.POST.get('eliminar_firma') == 'on' and config.director_firma:
            config.director_firma.delete()
            config.director_firma = None
        
        try:
            config.save()
            messages.success(request, 'Configuración de la escuela actualizada con éxito.')
        except Exception as e:
            messages.error(request, f'Error al guardar la configuración: {str(e)}')
        
        return redirect('configuracion_escuela')
    
    context = {
        'config': config,
        'titulo': 'Configuración de la Escuela',
    }
    
    return render(request, 'est_forder/configuracion_escuela.html', context)
