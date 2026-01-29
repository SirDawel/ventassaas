import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import CustomUser

# Actualizar usuarios sin email
usuarios_sin_email = CustomUser.objects.filter(email__isnull=True) | CustomUser.objects.filter(email='')

print(f"Usuarios sin email encontrados: {usuarios_sin_email.count()}")

for usuario in usuarios_sin_email:
    # Generar email temporal basado en nombre o ID
    if usuario.cedula:
        nuevo_email = f"{usuario.cedula}@temp.escuela.edu.do"
    else:
        nuevo_email = f"usuario{usuario.id}@temp.escuela.edu.do"
    
    print(f"Actualizando usuario {usuario.id} - {usuario.get_full_name()} -> {nuevo_email}")
    usuario.email = nuevo_email
    usuario.save()

print("Actualización completada!")
