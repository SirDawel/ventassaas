from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('login')
        
        if request.user.rol != 'Administrador':
            messages.error(request, 'No tienes permiso para acceder a esta página. Solo los administradores pueden realizar esta acción.')
            return redirect('plataform')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view 