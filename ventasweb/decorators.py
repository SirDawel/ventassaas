from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Decorador que permite acceso solo a Administradores, Secretarias, Directores y Superusers.
    Úsalo para funciones administrativas completas del sistema.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('login')
        
        if not (request.user.is_superuser or request.user.rol in ['Administrador', 'Director', 'Secretaria']):
            messages.error(request, 'No tienes permiso para acceder a esta página. Solo los administradores, directores y secretarias pueden realizar esta acción.')
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


# ================================================================
# HELPERS PARA PERMISOS DE GESTIÓN DE NOTAS
# ================================================================

def puede_editar_notas(user, materia=None):
    """
    Determina si un usuario puede EDITAR notas (crear/modificar).
    
    Roles con permiso de edición:
    - Administrador: Acceso total
    - Secretaria: Acceso total
    - Director: Acceso total
    - Profesor: Solo sus propias materias
    
    Args:
        user: Usuario autenticado
        materia: Objeto Materia (opcional, requerido para Profesor)
    
    Returns:
        bool: True si puede editar, False si no
    """
    if not user.is_authenticated:
        return False
    
    # Superuser siempre puede
    if user.is_superuser:
        return True
    
    # Administrador, Secretaria, Director pueden editar todo
    if user.rol in ['Administrador', 'Secretaria', 'Director']:
        return True
    
    # Profesor solo puede editar sus propias materias
    if user.rol == 'Profesor' and materia:
        return materia.profesor == user
    
    return False


def puede_ver_notas(user, materia=None):
    """
    Determina si un usuario puede VER notas (solo lectura).
    
    Roles con permiso de visualización:
    - Administrador: Acceso total
    - Secretaria: Acceso total
    - Director: Acceso total
    - Coordinador: Acceso total (solo lectura)
    - Profesor: Solo sus propias materias
    - Estudiante: Solo sus propias notas (requiere matrícula)
    
    Args:
        user: Usuario autenticado
        materia: Objeto Materia (opcional)
    
    Returns:
        bool: True si puede ver, False si no
    """
    if not user.is_authenticated:
        return False
    
    # Roles con acceso total de visualización
    if user.is_superuser or user.rol in ['Administrador', 'Secretaria', 'Director', 'Coordinador']:
        return True
    
    # Profesor puede ver sus materias
    if user.rol == 'Profesor' and materia:
        return materia.profesor == user
    
    # Estudiante puede ver sus propias notas (validar matrícula en vista)
    if user.rol == 'Estudiante':
        return True
    
    return False 