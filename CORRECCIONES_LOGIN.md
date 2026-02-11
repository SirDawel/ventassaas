# CORRECCIONES REALIZADAS AL SISTEMA DE LOGIN

## Fecha: 4 de Febrero de 2026

## Problemas Identificados:

1. **Sesiones muy cortas**: La configuración en `.env` tenía `SESSION_COOKIE_AGE=300` (5 minutos) lo que hacía que las sesiones expiraran muy rápido.

2. **Backend de autenticación**: Faltaba un backend personalizado para autenticación por email.

3. **Mensajes de error invisibles**: El template `login.html` no mostraba los mensajes de error de Django, por lo que cuando el login fallaba, el usuario no recibía ningún feedback visual.

## Soluciones Implementadas:

### 1. Configuración de Sesión (.env)
```env
# ANTES:
SESSION_COOKIE_AGE=300
SESSION_EXPIRE_AT_BROWSER_CLOSE=True

# DESPUÉS:
SESSION_COOKIE_AGE=14400  # 4 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE=False
```

### 2. Backend de Autenticación
- Creado nuevo archivo: `escuelaweb/backends.py`
- Implementa `EmailBackend` que permite autenticación usando email en lugar de username
- Actualizado `settings.py` para incluir el nuevo backend:
```python
AUTHENTICATION_BACKENDS = [
    'escuelaweb.backends.EmailBackend',  # Autenticación por email
    'django.contrib.auth.backends.ModelBackend',  # Fallback
]
```

### 3. Template de Login
- Agregados mensajes de error al template `login.html`
- Ahora muestra alertas de Bootstrap cuando hay errores de autenticación
- Los usuarios verán mensajes como:
  - "Correo electrónico o contraseña incorrectos"
  - "Tu cuenta no está activa"
  - "Por favor, completa todos los campos"

## Usuario de Prueba Creado:

Para probar el sistema de login, se ha creado un usuario de prueba:

```
Email: test@login.com
Password: 123456
Rol: Administrador
```

## Cómo Probar:

1. Asegúrate de que el servidor Django esté corriendo
2. Accede a http://localhost:8000/login/
3. Ingresa las credenciales del usuario de prueba
4. Deberías ser redirigido a `/anhos-escolares/` después de un login exitoso
5. Si ingresas credenciales incorrectas, verás un mensaje de error en rojo

## Usuarios Existentes:

Los siguientes usuarios están en el sistema pero necesitan restablecer sus contraseñas:
- liliana@gmail.com (Estudiante)
- angel@gmail.com (Estudiante)
- admin.test@example.com (Administrador)
- maria@gmail.com (Secretaria)
- jamedoe@gmail.com (Profesor)

Puedes usar el enlace "Olvidaste tu contraseña?" en la página de login para restablecer contraseñas.

## Scripts de Utilidad Creados:

1. **crear_usuario_prueba.py**: Crea un usuario de prueba con credenciales conocidas
2. **test_login.py**: Prueba la autenticación con diferentes contraseñas

## Próximos Pasos Recomendados:

1. Restablecer contraseñas de usuarios existentes si es necesario
2. Verificar que el email de restablecimiento de contraseña funcione correctamente
3. Considerar implementar un sistema de primer login obligatorio para cambiar contraseña
4. Agregar logs de intentos de login fallidos para seguridad

## Archivos Modificados:

- `.env` - Configuración de sesión
- `Escuela/settings.py` - Backend de autenticación
- `escuelaweb/backends.py` - Nuevo archivo
- `escuelaweb/templates/website/login.html` - Mensajes de error
- `crear_usuario_prueba.py` - Nuevo archivo de utilidad
- `test_login.py` - Nuevo archivo de utilidad

---

**Nota**: Todos los cambios han sido probados y la autenticación funciona correctamente con el usuario de prueba.
