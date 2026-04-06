# Seguridad Mejorada: Eliminación de Usuarios

## 📋 Descripción

Se ha implementado un sistema de seguridad mejorado para la eliminación de usuarios. Ahora se requieren **dos factores de autenticación** para confirmar la eliminación:

1. **Contraseña del usuario actual**: Para verificar que es el usuario autorizado quien está realizando la acción
2. **Código de anulación**: Código mensual que solo conocen los administradores del sistema

## 🔐 Validaciones Implementadas

### 1. Validación de Permisos
- **Solo** usuarios con rol: **Administrador** o **Secretaria** pueden eliminar usuarios (los Directores NO pueden eliminar)
- No se puede eliminar superusuarios
- No se puede eliminar el propio usuario (auto-eliminación)

### 2. Validación de Contraseña
- Se requiere la contraseña del usuario que está realizando la eliminación
- La contraseña se valida usando `check_password()` de Django
- Incluye botón para mostrar/ocultar contraseña

### 3. Validación de Código de Anulación
- Se requiere el código de anulación mensual vigente
- El código se valida usando la clase `CodigoAnulacion`
- El código cambia cada mes automáticamente
- Conversión automática a mayúsculas

### 4. Registro de Auditoría Completo
- Se registra la eliminación en `SecurityLog` antes de ejecutarla
- **Información guardada en el log:**
  - Usuario eliminado: nombre, email, rol, cédula
  - Usuario que eliminó: nombre, email, rol
  - Dirección IP desde donde se realizó la acción
  - User Agent (navegador/sistema operativo)
  - Fecha y hora exacta
  - Confirmación de validación con código de anulación
- Nivel de severidad: **WARNING**
- Tipo de evento: **ADMIN_ACTION**

### 5. Vista de Logs de Usuarios Eliminados
- Acceso exclusivo para Administradores y Secretaria
- Muestra los últimos 100 registros de eliminaciones
- Información detallada de cada eliminación
- Disponible en: `/users/log-eliminados/`
- Botón de acceso directo desde la lista de usuarios

## 🎯 Flujo de Eliminación

```
1. Usuario accede a eliminar usuario
   ↓
2. Sistema valida permisos (Admin/Director/Secretaria)
   ↓
3. Sistema verifica que no sea superusuario ni auto-eliminación
   ↓
4. Se muestra formulario con:
   - Información del usuario a eliminar
   - Campo de contraseña
   - Campo de código de anulación
   ↓
5. Usuario ingresa contraseña y código
   ↓
6. Sistema valida:
   - Contraseña correcta ✓
   - Código de anulación válido ✓
   ↓
7. Sistema registra la acción en SecurityLog
   ↓
8. Usuario es eliminado
   ↓
9. Mensaje de éxito y redirección a lista
```

## 💻 Archivos Modificados

### 1. `escuelaweb/views.py`
- Función `user_delete()` (línea ~1022-1076)
  - Cambiado: Solo Administrador y Secretaria pueden eliminar (eliminado Director)
  - Agregada validación de contraseña y código de anulación
  - Validaciones adicionales de seguridad
  - Registro completo en SecurityLog con metadata detallada
  
- Función `log_usuarios_eliminados()` (línea ~8123-8143) **NUEVA**
  - Vista exclusiva para Administradores y Secretaria
  - Muestra historial de eliminaciones con detalles completos
  - Últimos 100 registros ordenados por fecha

### 2. `escuelaweb/templates/users/user_confirm_delete.html`
- Rediseño completo del formulario
- Agregado campo de contraseña con visibilidad toggle
- Agregado campo de código de anulación
- Validación de formulario con Bootstrap
- JavaScript para auto-convertir código a mayúsculas
- Mejor interfaz de usuario con advertencias claras
- Aviso de registro en log

### 3. `escuelaweb/templates/users/log_usuarios_eliminados.html` **NUEVO**
- Template completo para visualizar logs de eliminaciones
- Tabla responsiva con información detallada
- Vista colapsable para detalles adicionales
- Muestra:
  - Usuario eliminado (nombre, email, rol, cédula)
  - Usuario que eliminó (nombre, email, rol)
  - IP y navegador
  - Fecha y hora
  - Confirmación de código de anulación
  
### 4. `escuelaweb/urls.py`
- Agregada ruta: `path('users/log-eliminados/', views.log_usuarios_eliminados, name='log_usuarios_eliminados')`

### 5. `escuelaweb/templates/users/user_list.html`
- Agregado botón "Log Eliminados" en header
- Visible solo para Administradores y Secretaria

## 🔑 Obtener Código de Anulación

Los administradores pueden obtener el código de anulación vigente de tres formas:

### Opción 1: Panel de Administración Django
```
1. Ir a Admin Django
2. Buscar "Códigos de Anulación"
3. Ver el código del mes actual
```

### Opción 2: Management Command
```bash
python manage.py generar_codigo_anulacion
```

### Opción 3: Vista en la Aplicación
```
Ir a: /codigo-anulacion/
```

## 📊 Consultar Log de Usuarios Eliminados

### Acceso a la Vista de Logs

Los **Administradores y Secretaria** pueden consultar el historial completo de eliminaciones:

#### Opción 1: Desde Lista de Usuarios
1. Ir a **Lista de Usuarios**
2. Click en el botón **"Log Eliminados"** (botón amarillo en la esquina superior derecha)

#### Opción 2: URL Directa
```
/users/log-eliminados/
```

### Información Mostrada en el Log

Cada registro de eliminación incluye:

**Usuario Eliminado:**
- Nombre completo
- Email
- Rol
- Cédula (si disponible)

**Usuario que Eliminó:**
- Nombre completo
- Email  
- Rol (con badge de color)

**Detalles Técnicos:**
- Dirección IP
- Navegador y sistema operativo (User Agent)
- Fecha y hora exacta
- Confirmación de uso de código de anulación
- Nivel de severidad del evento

**Características:**
- Vista colapsable con detalles adicionales
- Tabla responsiva y ordenada por fecha (más recientes primero)
- Últimos 100 registros disponibles
- Contador total de eliminaciones
- Información de seguridad completa

## 📝 Mensajes de Error

El sistema muestra los siguientes mensajes según el caso:

| Error | Mensaje |
|-------|---------|
| Permisos insuficientes (Director u otro rol) | "No tienes permiso para eliminar usuarios. Solo Administradores y Secretaria pueden realizar esta acción." |
| Intentar eliminar superusuario | "No se puede eliminar un superusuario." |
| Intentar auto-eliminarse | "No puedes eliminarte a ti mismo." |
| Campos vacíos | "Debe ingresar la contraseña y el código de anulación." |
| Contraseña incorrecta | "Contraseña incorrecta." |
| Código incorrecto | "Código de anulación incorrecto." |
| Error en eliminación | "Error al eliminar usuario: [detalle del error]" |
| Eliminación exitosa | "Usuario [nombre] eliminado exitosamente." |

## 🛡️ Seguridad

Esta implementación proporciona:

- ✅ **Doble factor de autenticación** para eliminación
- ✅ **Prevención de eliminación accidental**
- ✅ **Auditoría completa** de eliminaciones con metadata detallada
- ✅ **Control de acceso estricto** basado en roles (solo Admin y Secretaria)
- ✅ **Protección contra auto-eliminación**
- ✅ **Protección de cuentas críticas** (superusuarios)
- ✅ **Registro de IP y navegador** para trazabilidad completa
- ✅ **Vista de consulta de logs** para auditoría histórica
- ✅ **Información detallada** de quién eliminó a quién, cuándo y desde dónde

## 🧪 Pruebas Recomendadas

### Test 1: Eliminación Exitosa (Administrador)
1. Acceder como Administrador
2. Ir a eliminar un usuario estudiante
3. Ingresar contraseña correcta
4. Ingresar código de anulación correcto
5. Verificar que se elimina correctamente
6. Verificar registro en SecurityLog
7. **NUEVO:** Ir a "Log Eliminados" y verificar que aparece el registro

### Test 2: Contraseña Incorrecta
1. Acceder como Administrador
2. Intentar eliminar usuario
3. Ingresar contraseña incorrecta
4. Verificar mensaje de error
5. Usuario NO debe eliminarse
6. NO debe aparecer en el log

### Test 3: Código Incorrecto
1. Acceder como Administrador
2. Intentar eliminar usuario
3. Ingresar contraseña correcta
4. Ingresar código incorrecto
5. Verificar mensaje de error
6. Usuario NO debe eliminarse
7. NO debe aparecer en el log

### Test 4: Protección Superusuario
1. Acceder como Administrador
2. Intentar eliminar un superusuario
3. Verificar mensaje de error inmediato
4. No debe mostrar formulario

### Test 5: Auto-eliminación
1. Acceder como Administrador
2. Intentar eliminarse a sí mismo
3. Verificar mensaje de error
4. No debe permitir la acción

### Test 6: Director NO puede eliminar **NUEVO**
1. Acceder como **Director**
2. Intentar acceder a eliminar usuario
3. Verificar mensaje: "No tienes permiso para eliminar usuarios. Solo Administradores y Secretaria pueden realizar esta acción."
4. Redirigir a plataforma

### Test 7: Secretaria SÍ puede eliminar **NUEVO**
1. Acceder como **Secretaria**
2. Ir a eliminar estudiante
3. Ingresar contraseña y código correcto
4. Verificar eliminación exitosa
5. Verificar registro en log con su información

### Test 8: Consulta de Log **NUEVO**
1. Acceder como Administrador o Secretaria
2. Ir a Lista de Usuarios
3. Click en botón "Log Eliminados"
4. Verificar que se muestran los registros
5. Expandir detalles de un registro
6. Verificar que toda la información es correcta
7. **Como Director:** No debe ver el botón "Log Eliminados"

## 📊 Modelo CodigoAnulacion

El código de anulación se gestiona mediante el modelo `CodigoAnulacion`:

```python
class CodigoAnulacion(models.Model):
    mes = models.IntegerField()  # 1-12
    anio = models.IntegerField()  # 2026, 2027, etc.
    codigo = models.CharField(max_length=10)
    creado = models.DateTimeField(auto_now_add=True)
```

**Métodos principales:**
- `generar_codigo()`: Genera código aleatorio de 8 caracteres
- `obtener_codigo_actual()`: Obtiene o crea código del mes actual
- `validar_codigo(codigo)`: Valida si un código es correcto

## 🔄 Mantenimiento

- El código de anulación se genera automáticamente cada mes
- Los códigos anteriores permanecen en la base de datos para auditoría
- Se recomienda cambiar el código manualmente en caso de compromiso
- Los administradores deben guardar el código en lugar seguro

## ✨ Mejoras Futuras Sugeridas

1. **Notificación por email** al eliminar un usuario
2. **Soft delete** en lugar de eliminación física
3. **Historial de usuarios eliminados** con posibilidad de restauración
4. **Confirmación adicional por SMS** para cuentas críticas
5. **Límite de intentos** para el código de anulación
6. **Expiración de código** después de varios usos
7. **Exportación de logs** a CSV/PDF para auditorías externas
8. **Dashboard de estadísticas** de eliminaciones por período

---

## 📈 Resumen de Cambios (Actualización Abril 2026)

### ✅ Restricción de Permisos
- **Antes:** Administrador, Director y Secretaria podían eliminar usuarios
- **Ahora:** Solo **Administrador** y **Secretaria** pueden eliminar usuarios
- **Razón:** Mayor control y seguridad en operaciones críticas

### ✅ Log de Auditoría Mejorado
- **Antes:** Registro básico en SecurityLog
- **Ahora:** Registro completo con metadata detallada en formato JSON
- **Incluye:** Usuario eliminado (nombre, email, rol, cédula), usuario que eliminó (nombre, email, rol), IP, user agent, confirmación de código

### ✅ Vista de Consulta de Logs
- **Nueva funcionalidad:** Página dedicada para ver historial de eliminaciones
- **Acceso:** Solo Administradores y Secretaria
- **Muestra:** Últimos 100 registros con información completa y colapsable
- **Ubicación:** Botón directo desde Lista de Usuarios + URL `/users/log-eliminados/`

---

**Primera Implementación:** Abril 2026  
**Última Actualización:** Abril 6, 2026  
**Compatibilidad:** Django 3.x+  
**Seguridad:** Alta (Doble factor de autenticación + Auditoría completa)  
**Nivel de Acceso:** Restringido (Solo Administrador y Secretaria)
