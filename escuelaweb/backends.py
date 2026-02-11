"""
Backend de autenticación personalizado para permitir login con email
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend de autenticación que permite usar email en lugar de username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica un usuario usando su email y contraseña
        """
        try:
            # Buscar usuario por email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Si no se encuentra por email, intentar por username tradicional
            return None
        except User.MultipleObjectsReturned:
            # Si hay múltiples usuarios con el mismo email (no debería pasar)
            # tomar el primero
            user = User.objects.filter(email=username).first()
        
        # Verificar la contraseña
        if user and user.check_password(password):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Obtiene un usuario por su ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
