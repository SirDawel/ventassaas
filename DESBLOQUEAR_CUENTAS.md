# 🔓 Cómo Desbloquear Cuentas

El sistema bloquea automáticamente las cuentas tras **5 intentos fallidos de login** por un periodo de **15 minutos**.

---

## ✅ 1. Desbloqueo Automático (Recomendado)

**No necesitas hacer nada.** La cuenta se desbloquea automáticamente después de 15 minutos desde el último intento fallido.

- ⏱️ **Tiempo de bloqueo:** 15 minutos
- 🔄 **Automático:** Sí
- 📊 **Seguimiento:** Los intentos se registran en SecurityLog

---

## 🛠️ 2. Desbloqueo Manual desde Django Admin

### Opción A: Acción por lotes
1. Acceder a Django Admin: `/admin/`
2. Ir a **"Intentos de Login"** (LoginAttempt)
3. Buscar la cuenta bloqueada
4. **Seleccionar** los registros del usuario
5. En el menú "Acciones", elegir **"Desbloquear cuentas seleccionadas"**
6. Click en **"Ir"**

### Características:
- ✅ Muestra columna **"Estado de Cuenta"** (🔒 BLOQUEADO / ✓ Activo)
- ✅ Registra el desbloqueo en SecurityLog
- ✅ Muestra mensaje de confirmación
- ✅ Permite desbloquear múltiples cuentas a la vez

---

## 💻 3. Desbloqueo desde Terminal (Recomendado para Administradores)

### Comandos disponibles:

#### a) Listar cuentas bloqueadas
```bash
python manage.py unblock_account --list
```
**Salida:**
```
🔍 Buscando cuentas con 5+ intentos fallidos...

🔒 2 cuenta(s) bloqueada(s):

  • usuario@ejemplo.com (Juan Pérez)
    Intentos fallidos: 7
    Último intento: 2026-03-08 14:30:45

  • otro@ejemplo.com (María García)
    Intentos fallidos: 5
    Último intento: 2026-03-08 14:25:12
```

#### b) Desbloquear cuenta específica
```bash
python manage.py unblock_account usuario@ejemplo.com
```
**Salida:**
```
🔓 Desbloqueando cuenta: usuario@ejemplo.com...
✓ Cuenta usuario@ejemplo.com desbloqueada exitosamente
  Se eliminaron 7 intento(s) fallido(s)
```

#### c) Desbloquear TODAS las cuentas
```bash
python manage.py unblock_account --all
```
**Salida:**
```
🔓 Desbloqueando todas las cuentas...

  ✓ usuario@ejemplo.com (7 intentos eliminados)
  ✓ otro@ejemplo.com (5 intentos eliminados)

✓ 2 cuenta(s) desbloqueada(s) exitrosamente
```

#### d) Opciones avanzadas
```bash
# Ver cuentas con 3+ intentos en los últimos 10 minutos
python manage.py unblock_account --list --attempts 3 --minutes 10

# Desbloquear todas las cuentas con configuración personalizada
python manage.py unblock_account --all --attempts 3 --minutes 10
```

---

## 🌐 4. Desbloqueo desde Interfaz Web (Próximamente)

### URLs a agregar en `urls.py`:

```python
# Gestión de cuentas bloqueadas
path('seguridad/bloqueadas/', security_views.blocked_accounts_list, name='blocked_accounts_list'),
path('seguridad/desbloquear/<str:email>/', security_views.unblock_account, name='unblock_account'),
path('seguridad/desbloquear-todas/', security_views.unblock_all_accounts, name='unblock_all_accounts'),
```

### Características:
- 📋 Lista de cuentas bloqueadas con tiempo restante
- 🔓 Botón para desbloquear individualmente
- 🔓🔓 Botón para desbloquear todas
- 📊 Información de intentos fallidos
- ⏱️ Cuenta regresiva para desbloqueo automático

---

## 🔍 5. Verificar Estado de una Cuenta (Python Shell)

```python
python manage.py shell

from escuelaweb.models import LoginAttempt

# Verificar si está bloqueada
email = "usuario@ejemplo.com"
bloqueada = LoginAttempt.is_blocked(email)
print(f"¿Está bloqueada? {bloqueada}")

# Ver intentos fallidos recientes
intentos = LoginAttempt.get_recent_failed_attempts(email, minutes=15)
print(f"Intentos fallidos (últimos 15 min): {intentos}")

# Desbloquear
if bloqueada:
    count = LoginAttempt.unblock_account(email)
    print(f"✓ Desbloqueada. Se eliminaron {count} intentos")
```

---

## 📊 6. Métodos programáticos (Para desarrolladores)

### En tus vistas:

```python
from escuelaweb.models import LoginAttempt, SecurityLog

# Verificar si está bloqueada
if LoginAttempt.is_blocked('usuario@ejemplo.com'):
    print("Cuenta bloqueada")

# Obtener lista de cuentas bloqueadas
blocked_emails = LoginAttempt.get_blocked_accounts(max_attempts=5, block_minutes=15)
print(f"Cuentas bloqueadas: {blocked_emails}")

# Desbloquear cuenta
count = LoginAttempt.unblock_account('usuario@ejemplo.com')
print(f"Se eliminaron {count} intentos fallidos")

# Registrar el desbloqueo (opcional pero recomendado)
SecurityLog.log_event(
    tipo_evento='ACCOUNT_UNLOCKED',
    descripcion=f'Cuenta desbloqueada por {request.user.email}',
    email='usuario@ejemplo.com',
    usuario=request.user,
    nivel_severidad='INFO'
)
```

---

## ⚙️ Configuración del Sistema

Actualmente configurado en `settings.py`:

```python
MAX_LOGIN_ATTEMPTS = 5          # Intentos antes de bloquear
LOGIN_BLOCK_DURATION = 900      # 15 minutos (en segundos)
```

### Para cambiar la configuración:

1. Edita `.env`:
```env
MAX_LOGIN_ATTEMPTS=3           # Aumentar o reducir intentos permitidos
LOGIN_BLOCK_DURATION=1800      # Cambiar tiempo de bloqueo (30 min en este ejemplo)
```

2. O directamente en `settings.py`:
```python
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
LOGIN_BLOCK_DURATION = int(os.getenv('LOGIN_BLOCK_DURATION', '900'))
```

---

## 🚨 Escenarios Comunes

### Escenario 1: Usuario olvidó su contraseña
**Solución:** 
- Esperar 15 minutos (desbloqueo automático)
- O usar `python manage.py unblock_account email@usuario.com`
- Luego usar "Recuperar contraseña"

### Escenario 2: Ataque de fuerza bruta detectado
**Acción:**
- ✅ NO desbloquear inmediatamente
- ✅ Revisar logs: `/admin/` → "Intentos de Login"
- ✅ Verificar IPs sospechosas
- ✅ Contactar al usuario para confirmar
- ✅ Considerar cambio de contraseña

### Escenario 3: Múltiples usuarios bloqueados tras mantenimiento
**Solución:**
```bash
# Desbloquear todas al mismo tiempo
python manage.py unblock_account --all
```

### Escenario 4: Usuario reporta que no puede entrar
**Pasos:**
1. Verificar estado:
   ```bash
   python manage.py unblock_account --list
   ```
2. Si está bloqueada, desbloquear:
   ```bash
   python manage.py unblock_account email@usuario.com
   ```
3. Confirmar que puede entrar

---

## 📝 Registro de Desbloqueos

Todos los desbloqueos se registran en **SecurityLog** con:
- ✅ Tipo de evento: `ACCOUNT_UNLOCKED`
- ✅ Email de la cuenta
- ✅ Quién desbloqueó (usuario admin o "system")
- ✅ Método usado (admin, command, web interface)
- ✅ Cantidad de intentos eliminados

### Ver historial de desbloqueos:
```bash
# En Django Admin
/admin/escuelaweb/securitylog/

# Filtrar por:
- Tipo de evento: "Cuenta desbloqueada"
- Email: usuario específico
```

---

## ✅ Resumen Rápido

| Método | Comando/URL | Cuándo usar |
|--------|-------------|-------------|
| **Automático** | ⏳ Esperar 15 min | Usuario legítimo, sin urgencia |
| **Terminal** | `python manage.py unblock_account email` | Administrador con acceso SSH |
| **Django Admin** | `/admin/` → Intentos de Login | Desde navegador, casos individuales |
| **Comando --all** | `python manage.py unblock_account --all` | Desbloqueo masivo |
| **Python Shell** | `LoginAttempt.unblock_account(email)` | Scripts personalizados |

---

## 🔐 Mejores Prácticas

1. ✅ **Preferir desbloqueo automático** cuando sea posible
2. ✅ **Verificar logs** antes de desbloquear tras múltiples intentos
3. ✅ **Usar --list** primero para ver el alcance del problema
4. ✅ **Registrar la razón** del desbloqueo manual en notas
5. ✅ **Considerar 2FA** para usuarios con accesos sensibles
6. ✅ **Revisar IPs** sospechosas en LoginAttempt
7. ❌ **NO desbloquear** sin investigar patrones sospechosos

---

## 🆘 Soporte

Si tienes problemas:
1. Revisa logs: `logs/security.log`
2. Verifica configuración en `settings.py`
3. Usa `--list` para diagnosticar
4. Contacta al administrador del sistema
