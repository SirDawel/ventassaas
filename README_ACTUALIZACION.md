# 🚀 Guía Rápida de Actualización Local

## 📋 Resumen

Actualiza tu sistema de desarrollo local de **Django 4.2 → 5.1** con un solo comando.

---

## ⚡ Actualización Automática (Recomendado)

### Opción 1: Script Automático Completo

```powershell
# Ejecutar script de actualización automática
.\actualizar.ps1
```

Este script hace TODO automáticamente:
- ✅ Crea backups (BD, media, Git)
- ✅ Verifica Python 3.13
- ✅ Crea nuevo virtualenv
- ✅ Instala todas las dependencias
- ✅ Ejecuta migraciones
- ✅ Verifica instalación
- ✅ Crea script de rollback

**Duración:** ~5-10 minutos

---

### Opción 2: Actualización con Opciones

```powershell
# Saltando backups (si ya los hiciste)
.\actualizar.ps1 -SkipBackup

# Saltando verificación de Python (si sabes que está instalado)
.\actualizar.ps1 -SkipPython

# Forzar actualización sin confirmaciones
.\actualizar.ps1 -Force

# Combinación
.\actualizar.ps1 -SkipBackup -Force
```

---

## 🧪 Verificación Post-Actualización

Después de actualizar, verifica que todo funcione:

```powershell
# Activar virtualenv
.\.venv\Scripts\Activate.ps1

# Ejecutar verificación completa
.\verificar.ps1
```

El script verificará:
- ✅ Versiones correctas instaladas
- ✅ Configuración Django
- ✅ Conexión a base de datos
- ✅ Modelos y tenants
- ✅ Redis (si aplica)
- ✅ Archivos estáticos

**Resultado esperado:** 90%+ de tests exitosos

---

## 🔄 Rollback (Si algo sale mal)

Si después de actualizar encuentras problemas:

```powershell
# Volver a versión anterior
.\rollback.ps1
```

Esto restaurará:
- ✅ Virtualenv anterior
- ✅ Código desde Git (si aplicable)
- ⚠️ Base de datos debes restaurarla manualmente

### Restaurar Base de Datos Manualmente:

```powershell
# Listar backups disponibles
Get-ChildItem backups\backup_pre_upgrade_*.sql

# Restaurar el más reciente
$backup = Get-ChildItem backups\backup_pre_upgrade_*.sql | Sort-Object -Descending | Select-Object -First 1
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -h 127.0.0.1 -p 5434 -d ventassistemdb -f $backup.FullName
```

---

## 📖 Actualización Manual (Paso a Paso)

Si prefieres hacerlo manualmente, sigue la guía completa:

```powershell
# Abrir guía en VS Code
code ACTUALIZACION_LOCAL_WINDOWS.md
```

O léela aquí: [ACTUALIZACION_LOCAL_WINDOWS.md](ACTUALIZACION_LOCAL_WINDOWS.md)

---

## 🎯 Después de Actualizar

### 1. Iniciar Servidor

```powershell
# Activar virtualenv
.\.venv\Scripts\Activate.ps1

# Iniciar servidor de desarrollo
python manage.py runserver
```

Abrir en navegador:
- http://localhost:8000/
- http://picapolloeka.localhost:8000/

### 2. Iniciar Celery (Si lo usas)

**Terminal 1 - Celery Worker:**
```powershell
.\.venv\Scripts\Activate.ps1
celery -A VentasSys worker --pool=solo -l info
```

**Terminal 2 - Celery Beat:**
```powershell
.\.venv\Scripts\Activate.ps1
celery -A VentasSys beat -l info
```

### 3. Iniciar Redis (Si no está corriendo)

```powershell
# Opción 1: Redis en WSL2
wsl redis-server

# Opción 2: Redis nativo Windows
# Ejecutar redis-server.exe

# Opción 3: Docker
docker run -d -p 6379:6379 redis:latest
```

---

## ✅ Checklist de Funcionalidades

Después de actualizar, verifica:

- [ ] **Login** - Puedes iniciar sesión
- [ ] **Crear Usuario** - Funciona creación con diferentes roles
- [ ] **Restricción Secretaria** - Solo puede crear Clientes
- [ ] **Crear Factura** - Sistema de facturación funciona
- [ ] **Búsqueda Productos** - Búsqueda unificada funciona
- [ ] **Tenants** - Puedes acceder a diferentes subdominios
- [ ] **Archivos Estáticos** - CSS/JS cargan correctamente
- [ ] **Imágenes** - Logos y fotos se muestran
- [ ] **Celery** - Tareas asíncronas funcionan
- [ ] **Stripe** - Pagos funcionan (usar test keys)

---

## 🆘 Troubleshooting

### Error: "Python no encontrado"

```powershell
# Instalar Python 3.13
# Descargar de: https://www.python.org/downloads/
# Marcar: "Add Python 3.13 to PATH"
```

### Error: "Script execution is disabled"

```powershell
# Permitir ejecución de scripts
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

# Intentar activar virtualenv de nuevo
.\.venv\Scripts\Activate.ps1
```

### Error: "PostgreSQL no conecta"

```powershell
# Verificar que PostgreSQL corre
Get-Service -Name "postgresql*"

# Si no corre, iniciar servicio
Start-Service postgresql-x64-14  # O tu versión
```

### Error: "Redis no disponible"

```powershell
# Redis no es crítico para desarrollo básico
# Solo necesario para Celery
# Instalar WSL2 + Redis o usar Docker
```

### Error: Celery no inicia en Windows

```powershell
# Usar pool=solo en Windows
celery -A VentasSys worker --pool=solo -l info

# O instalar gevent
pip install gevent
celery -A VentasSys worker --pool=gevent -l info
```

---

## 📚 Documentación Completa

| Archivo | Descripción |
|---------|-------------|
| [ACTUALIZACION_LOCAL_WINDOWS.md](ACTUALIZACION_LOCAL_WINDOWS.md) | Guía completa paso a paso |
| [GUIA_ACTUALIZACION_DJANGO5.md](GUIA_ACTUALIZACION_DJANGO5.md) | Breaking changes y soluciones |
| [PROMPT_DEPLOY_AWS_DJANGO_TENANTS.md](PROMPT_DEPLOY_AWS_DJANGO_TENANTS.md) | Deploy en producción AWS |
| [requirements_produccion.txt](requirements_produccion.txt) | Dependencias actualizadas |
| `actualizar.ps1` | Script de actualización automática |
| `verificar.ps1` | Script de verificación post-actualización |
| `rollback.ps1` | Script de rollback (creado automáticamente) |

---

## 📊 Comparación de Versiones

| Componente | Antes | Después | Mejora |
|------------|-------|---------|--------|
| Django | 4.2.17 | **5.1.4** | 10-15% más rápido |
| django-tenants | 3.6.1 | **3.12.0** | Compatible Django 5 |
| Python | 3.11+ | **3.13+** | JIT compiler |
| PostgreSQL | 14+ | **16+** | Queries más rápidos |
| psycopg | psycopg2 | **psycopg3 3.3.4** | API moderna |
| Celery | 5.3 | **5.6.3** | Más estable |
| Redis | 5.0 | **7.4.0** | Más rápido |
| Stripe | 8.0 | **15.1.0** | API actualizada |

---

## 🎯 Tiempo Estimado

| Tarea | Tiempo |
|-------|--------|
| Backups | 2-3 min |
| Instalar Python 3.13 | 5 min (primera vez) |
| Crear virtualenv | 1 min |
| Instalar dependencias | 3-5 min |
| Migraciones | 1-2 min |
| Verificación | 1 min |
| **TOTAL** | **~15-20 min** |

---

## ⚠️ Importante

1. **SIEMPRE haz backup antes de actualizar**
2. **No actualices en horario de producción** (si estás trabajando en algo crítico)
3. **Prueba todo después de actualizar**
4. **Ten el rollback listo por si acaso**

---

## 🚀 ¿Listo para Actualizar?

```powershell
# 1. Navegar a carpeta del proyecto
cd E:\AWSAMAZON\Ventas

# 2. Ejecutar actualización
.\actualizar.ps1

# 3. Verificar instalación
.\verificar.ps1

# 4. Iniciar servidor
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

---

## 💡 Consejos

- ✅ Actualiza un viernes para tener el fin de semana para resolver problemas
- ✅ Haz la actualización cuando NO tengas presión de deadlines
- ✅ Lee los mensajes del script, te guiará paso a paso
- ✅ Si algo falla, no entres en pánico - tienes rollback
- ✅ Prueba TODAS las funcionalidades después de actualizar

---

## 📞 Ayuda

Si encuentras problemas:

1. Ejecuta `.\verificar.ps1` para diagnóstico
2. Revisa [ACTUALIZACION_LOCAL_WINDOWS.md](ACTUALIZACION_LOCAL_WINDOWS.md) sección Troubleshooting
3. Revisa [GUIA_ACTUALIZACION_DJANGO5.md](GUIA_ACTUALIZACION_DJANGO5.md) para breaking changes
4. Si todo falla: `.\rollback.ps1`

---

**¡Buena suerte con la actualización! 🎉**
