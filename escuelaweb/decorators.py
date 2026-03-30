from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Decorador que permite acceso solo a Administradores, Directores y Superusers.
    Úsalo para funciones administrativas completas del sistema.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('login')
        
        if not (request.user.is_superuser or request.user.rol in ['Administrador', 'Director']):
            messages.error(request, 'No tienes permiso para acceder a esta página. Solo los administradores y directores pueden realizar esta acción.')
            return redirect('plataform')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def coordinador_required(view_func):
    """
    Decorador que permite acceso a Coordinadores, Directores, Administradores y Superusers.
    Úsalo SOLO para funciones de visualización/consulta, NO para crear/editar/eliminar.
    Para operaciones de modificación, usa @admin_required.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('login')
        
        if not (request.user.is_superuser or request.user.rol in ['Administrador', 'Director', 'Coordinador']):
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('plataform')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view 