# 🔐 Sistema de Seguridad Implementado

## Resumen Ejecutivo

Se ha implementado un **sistema de seguridad robusto y profesional** para el sistema escolar, incluyendo:
- ✅ Protección contra ataques de fuerza bruta (Rate Limiting)
- ✅ Registro de intentos de login y auditoría de seguridad
- ✅ Gestión de sesiones activas con rastreo
- ✅ Soporte para JWT Tokens (Bearer tokens) para APIs
- ✅ Autenticación de dos factores (2FA) opcional
- ✅ Bloqueo automático de cuentas tras intentos fallidos
- ✅ Sistema de logs de seguridad con diferentes niveles de severidad

---

## 📋 Componentes Implementados

### 1. **Modelos de Seguridad** (4 nuevos modelos)

#### LoginAttempt
- Registra **todos los intentos de login** (exitosos y fallidos)
- Almacena: email, IP, user agent, fecha, razón de fallo
- Métodos útiles:
  - `get_recent_failed_attempts()`: Cuenta intentos fallidos recientes
  - `is_blocked()`: Verifica si una cuenta está bloqueada
  - `record_attempt()`: Registra un nuevo intento

#### SecurityLog
- **Registro de auditoría** de eventos de seguridad
- 15 tipos de eventos: LOGIN, LOGOUT, PASSWORD_CHANGE, ADMIN_ACTION, etc.
- 4 niveles de severidad: INFO, WARNING, ERROR, CRITICAL
- Almacena metadata adicional en formato JSON
- Método: `log_event()` para registrar eventos fácilmente

#### UserSession
- Rastrea **sesiones activas** de usuarios
- Almacena: usuario, IP, user agent, fechas de inicio/última actividad/cierre
- Métodos útiles:
  - `cerrar_sesion()`: Cierra una sesión específica
  - `get_active_sessions()`: Obtiene sesiones activas de un usuario
  - `cleanup_old_sessions()`: Limpia sesiones antiguas

#### TwoFactorAuth
- Sistema de **autenticación de dos factores (2FA)**
- Compatible con Google Authenticator y similares
- Incluye códigos de respaldo para emergencias
- Métodos:
  - `habilitar_2fa()`: Activa 2FA y genera códigos
  - `verificar_token()`: Verifica tokens TOTP
  - `get_qr_code_url()`: Genera URL para código QR

---

### 2. **Middleware de Seguridad** (4 middlewares)

#### RateLimitMiddleware
- **Limita la tasa de solicitudes** para prevenir ataques de fuerza bruta
- Configuración por tipo de endpoint:
  - Login: 5 intentos en 5 minutos
  - API: 100 requests en 1 minuto
  - General: 500 requests en 5 minutos
- Responde con HTTP 429 (Too Many Requests) cuando se excede el límite

#### SessionSecurityMiddleware
- **Gestiona la expiración de sesiones** por inactividad (4 horas por defecto)
- Actualiza última actividad en cada request
- Rastrea sesiones activas en la base de datos
- Cierra sesión automáticamente si expira

#### SecurityAuditMiddleware
- **Audita acciones en URLs críticas**:
  - /admin/
  - /api/
  - /usuarios/
  - /exportar/
  - /eliminar/
  - /facturas/anular/
  - /contabilidad/asientos/anular/
- Registra automáticamente en SecurityLog

#### LoginSecurityMiddleware
- **Bloquea cuentas** tras múltiples intentos fallidos
- Verificación antes de permitir acceso al login
- Bloqueo temporal de 15 minutos tras 5 intentos fallidos

---

### 3. **Vista de Login Mejorada**

La vista `login_view` ahora incluye:
- ✅ Verificación de bloqueo de cuenta antes de autenticar
- ✅ Registro de TODOS los intentos (exitosos y fallidos)
- ✅ Logging de eventos de seguridad
- ✅ Mensajes informativos al usuario (intentos restantes)
- ✅ Actualización de último acceso del usuario
- ✅ Inicialización de sesión con timestamp

#### Vista `logout_view` mejorada:
- ✅ Registro de evento de logout
- ✅ Cierre de sesión en base de datos
- ✅ Auditoría completa

---

### 4. **Utilidades de Seguridad**

#### JWTTokenManager (security_utils.py)
- Generación de **Access Tokens** (1 hora)
- Generación de **Refresh Tokens** (7 días)
- Verificación y decodificación de tokens
- Obtener usuario desde token
- **Uso**:
  ```python
  from escuelaweb.security_utils import JWTTokenManager
  
  # Generar token
  access_token = JWTTokenManager.generate_access_token(user)
  
  # Verificar token
  payload = JWTTokenManager.verify_token(access_token)
  
  # Obtener usuario desde token
  user = JWTTokenManager.get_user_from_token(access_token)
  ```

#### APIKeyManager
- Generación de  API keys únicas
- Hashing seguro de API keys
- Verificación de API keys

#### PasswordSecurityHelper
- Validación de contraseñas robustas
- Generación de contraseñas seguras
- Verificación de historial de contraseñas

#### SecurityHelper
- Sanitización de entrada (prevenir XSS)
- Verificación de URLs seguras para redirección
- Generación de tokens CSRF
- Detección de actividad sospechosa

---

### 5. **Vistas de Gestión de Seguridad**

#### Dashboard de Seguridad (`/seguridad/dashboard/`)
- Estadísticas generales de seguridad
- Usuarios activos vs total
- Sesiones activas
- Intentos de login (exitosos/fallidos últimas 24h)
- Eventos críticos y warnings (últimos 7 días)
- Últimos eventos de seguridad
- Usuarios con 2FA habilitado

#### Lista de Registros de Seguridad (`/seguridad/logs/`)
- Vista paginada de todos los logs
- Filtros por:
  - Tipo de evento
  - Nivel de severidad
  - Usuario
  - Rango de fechas
- Exportación a CSV

#### Lista de Intentos de Login (`/seguridad/intentos-login/`)
- Vista de todos los intentos de login
- Filtros por email, IP, fecha, estado
- Identificación de patrones sospechosos

#### Sesiones Activas (`/seguridad/sesiones/`)
- Lista de todas las sesiones activas
- Información de IP y dispositivo
- Capacidad de cerrar sesiones remotamente
- Útil para detectar sesiones no autorizadas

#### Mi Seguridad (`/seguridad/mi-configuracion/`)
- Vista para usuarios normales
- Ver sus propias sesiones activas
- Historial de intentos de login
- Eventos de seguridad relacionados
- Estado de 2FA

#### Exportar Logs (`/seguridad/export/`)
- Exportación de logs a CSV
- Aplicación de filtros antes de exportar
- Registro automático de la exportación

---

### 6. **Configuración en Settings**

Se agregaron las siguientes configuraciones:

```python
# CACHÉ (para Rate Limiting)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        ...
    }
}

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ACCESS_TOKEN_LIFETIME = 3600  # 1 hora
JWT_REFRESH_TOKEN_LIFETIME = 604800  # 7 días

# Login Security
MAX_LOGIN_ATTEMPTS = 5
LOGIN_BLOCK_DURATION = 900  # 15 minutos

# Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True

# Logging Configuration
LOGGING = {
    # Logs rotativos con 3 handlers:
    # - console: INFO a consola
    # - file: WARNING+ a django.log
    # - security_file: INFO a security.log
}
```

---

### 7. **Admin de Django**

Se registraron todos los modelos de seguridad:
- ✅ LoginAttempt (solo lectura)
- ✅ SecurityLog (solo lectura)
- ✅ UserSession (con acción para cerrar sesiones)
- ✅ TwoFactorAuth (solo lectura)

---

## 🚀 Cómo Usar el Sistema

### Para Administradores:

1. **Acceder al Dashboard de Seguridad**:
   - URL: `/seguridad/dashboard/`
   - Ver estadísticas en tiempo real
   - Monitorear eventos críticos

2. **Revisar Logs de Seguridad**:
   - URL: `/seguridad/logs/`
   - Filtrar por tipo de evento o severidad
   - Exportar a CSV para análisis

3. **Monitorear Intentos de Login**:
   - URL: `/seguridad/intentos-login/`
   - Identificar patrones de ataques
   - Ver IPs sospechosas

4. **Gestionar Sesiones Activas**:
   - URL: `/seguridad/sesiones/`
   - Ver todas las sesiones activas
   - Cerrar sesiones sospechosas

### Para Usuarios:

1. **Ver Mi Seguridad**:
   - URL: `/seguridad/mi-configuracion/`
   - Ver sesiones activas propias
   - Revisar historial de accesos

### Para Desarrolladores (APIs):

1. **Generar Token JWT**:
   ```python
   from escuelaweb.security_utils import JWTTokenManager
   
   # En una vista de API
   def api_login(request):
       user = authenticate(...)
       if user:
           access_token = JWTTokenManager.generate_access_token(user)
           refresh_token = JWTTokenManager.generate_refresh_token(user)
           return JsonResponse({
               'access_token': access_token,
               'refresh_token': refresh_token
           })
   ```

2. **Verificar Token en API**:
   ```python
   def api_protected_view(request):
       token = request.headers.get('Authorization', '').replace('Bearer ', '')
       user = JWTTokenManager.get_user_from_token(token)
       
       if not user:
           return JsonResponse({'error': 'Token inválido'}, status=401)
       
       # Procesar request...
   ```

3. **Registrar Eventos Personalizados**:
   ```python
   from escuelaweb.models import SecurityLog
   
   SecurityLog.log_event(
       tipo_evento='ADMIN_ACTION',
       descripcion='Usuario exportó datos de estudiantes',
       usuario=request.user,
       ip_address=get_client_ip(request),
       nivel_severidad='INFO',
       metadata={'total_records': 150}
   )
   ```

---

## 📊 Estadísticas y Reportes

El sistema ahora puede responder preguntas como:
- ¿Cuántos intentos de login fallidos hubo hoy?
- ¿Qué usuarios tienen sesiones activas?
- ¿Hubo eventos de seguridad críticos esta semana?
- ¿Qué IPs están generando más intentos fallidos?
- ¿Qué usuarios tienen 2FA habilitado?

---

## 🛡️ Protecciones Implementadas

1. **Contra Fuerza Bruta**:
   - Rate limiting por IP
   - Bloqueo temporal tras 5 intentos fallidos
   - Mensajes informativos sin revelar si existe el usuario

2. **Contra Secuestro de Sesión**:
   - Sesiones con expiración por inactividad
   - Rastreo de IP y user agent
   - Detección de cambios sospechosos

3. **Auditoría Completa**:
   - Todos los eventos importantes registrados
   - Logs con múltiples niveles de severidad
   - Exportación para análisis externo

4. **Conformidad con Buenas Prácticas**:
   - Cookies HttpOnly y SameSite
   - CSRF protection habilitado
   - Passwords hasheados con PBKDF2
   - Soporte para HTTPS en producción

---

## 📦 Dependencias Agregadas

```
PyJWT==2.10.1       # Para tokens JWT (Bearer tokens)
pyotp==2.9.0        # Para autenticación de dos factores (2FA)
qrcode==8.0         # Para generar códigos QR de 2FA
```

---

## 🔧 Próximos Pasos Recomendados

1. **Configurar URLs de Seguridad**:
   - Agregar las rutas en `urls.py` para las vistas de seguridad
   - Ejemplo:
     ```python
     from escuelaweb import security_views
     
     urlpatterns = [
         path('seguridad/', security_views.security_dashboard, name='security_dashboard'),
         path('seguridad/logs/', security_views.security_logs_list, name='security_logs_list'),
         path('seguridad/intentos/', security_views.login_attempts_list, name='login_attempts_list'),
         path('seguridad/sesiones/', security_views.active_sessions_list, name='active_sessions_list'),
         path('seguridad/sesiones/<int:session_id>/cerrar/', security_views.close_session, name='close_session'),
         path('seguridad/mi-configuracion/', security_views.my_security_settings, name='my_security_settings'),
         path('seguridad/export/', security_views.export_security_logs, name='export_security_logs'),
         path('seguridad/api/stats/', security_views.security_stats_api, name='security_stats_api'),
     ]
     ```

2. **Crear Templates de Seguridad**:
   - Necesitarás crear los templates HTML para las vistas:
     - `seguridad/dashboard.html`
     - `seguridad/logs_list.html`
     - `seguridad/login_attempts_list.html`
     - `seguridad/active_sessions_list.html`
     - `seguridad/my_security.html`

3. **Revisar y Actualizar .env**:
   ```env
   # Agregar estas configuraciones
   JWT_SECRET_KEY=tu-clave-secreta-diferente-de-secret-key
   MAX_LOGIN_ATTEMPTS=5
   LOGIN_BLOCK_DURATION=900
   SECURITY_LOG_RETENTION_DAYS=90
   ENABLE_2FA=False  # Cambiar a True cuando quieras habilitarlo
   ```

4. **Monitoreo Continuo**:
   - Revisar regularmente el dashboard de seguridad
   - Exportar logs periódicamente para análisis
   - Limpiar sesiones antiguas con un cron job

5. **Activar 2FA para Administradores** (opcional pero recomendado):
   - Acceder desde Django Admin o crear vista personalizada
   - Escanear código QR con Google Authenticator
   - Guardar códigos de respaldo en lugar seguro

---

## ✅ Testing Recomendado

1. **Probar Bloqueo de Cuenta**:
   - Intentar login con contraseña incorrecta 5 veces
   - Verificar que la cuenta se bloquea por 15 minutos
   - Verificar mensaje al usuario

2. **Probar Rate Limiting**:
   - Hacer múltiples requests rápidos a login
   - Verificar respuesta HTTP 429

3. **Probar Auditoría**:
   - Realizar acciones críticas (eliminar, anular, exportar)
   - Verificar que se registran en SecurityLog

4. **Probar JWT Tokens** (si usas APIs):
   - Generar token
   - Usar token en request con header `Authorization: Bearer <token>`
   - Verificar que token expira tras 1 hora

---

## 🎯 Conclusión

El sistema ahora cuenta con **seguridad de nivel empresarial** que incluye:
- ✅ Protección contra los ataques más comunes
- ✅ Auditoría completa de eventos
- ✅ Gestión avanzada de sesiones
- ✅ Soporte para JWT/Bearer tokens
- ✅ Base sólida para implementar 2FA

**Todo está registrado en:**
- Base de datos: modelos LoginAttempt, SecurityLog, UserSession, TwoFactorAuth
- Archivos log: `logs/django.log` y `logs/security.log`
- Django Admin: sección de seguridad

**El sistema es extensible y fácil de personalizar según necesidades específicas.**
