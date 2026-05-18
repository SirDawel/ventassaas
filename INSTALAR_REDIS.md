# 🔴 INSTALACIÓN DE REDIS - PASO A PASO

## 📍 Estado Actual
Redis NO está instalado todavía. El navegador se abrió pero necesitas completar la instalación.

---

## ✅ OPCIÓN 1: Instalación Manual (Más confiable)

### Paso 1: Descargar
**Link directo:** https://github.com/microsoftarchive/redis/releases/download/win-3.2.100/Redis-x64-3.2.100.msi

O busca en la página que se abrió: `Redis-x64-3.2.100.msi` (3.3 MB)

### Paso 2: Instalar
1. Doble click en el archivo `.msi` descargado
2. **Setup Wizard:**
   - Welcome → Click **"Next"**
   - License Agreement → Check "I accept" → **"Next"**
   - **Installation Folder:** C:\Program Files\Redis → **"Next"**
   - ✅ **IMPORTANTE:** Marca **"Add Redis to PATH"** (si aparece)
   - Click **"Install"**
   - Si pide permisos de Administrador → Click **"Yes"**
   - Espera 1-2 minutos...
   - Click **"Finish"**

### Paso 3: Verificar
1. **CIERRA Y REABRE** PowerShell (importante para que reconozca Redis)
2. Ejecuta:
   ```powershell
   .\verificar_redis.bat
   ```

**Deberías ver:**
```
[OK] Redis CLI instalado
Redis server v=3.2.100
[OK] Servicio Redis instalado
STATE: RUNNING
[OK] Redis esta corriendo!
PONG
```

---

## ✅ OPCIÓN 2: Instalación Automática (Si tienes Chocolatey)

Si tienes Chocolatey instalado:

```powershell
# En PowerShell como Administrador
choco install redis-64 -y

# Verificar
redis-cli --version
redis-cli ping
```

---

## ✅ OPCIÓN 3: Memurai (Alternativa moderna - Recomendada si opción 1 falla)

Memurai es una versión moderna de Redis para Windows:

1. **Descargar:** https://www.memurai.com/get-memurai
2. Click en **"Download Memurai Developer"** (Gratis)
3. Instalar el `.msi`
4. Se instala como servicio automáticamente
5. Verificar:
   ```powershell
   memurai-cli ping
   # Debe responder: PONG
   ```

**Configuración para usar Memurai:**
En tu archivo `.env`, usa:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
```
(Memurai es 100% compatible con Redis)

---

## 🔧 Solución de Problemas

### ❌ "redis-cli no se reconoce como comando"

**Solución 1: Reiniciar terminal**
- Cierra PowerShell completamente
- Abre nueva terminal
- Prueba: `redis-cli --version`

**Solución 2: Agregar al PATH manualmente**
1. Presiona `Windows + X` → "Sistema"
2. Click en "Configuración avanzada del sistema"
3. Click en "Variables de entorno"
4. En "Variables del sistema", busca "Path"
5. Click "Editar"
6. Click "Nuevo"
7. Agrega: `C:\Program Files\Redis`
8. Click "Aceptar" en todo
9. Reinicia PowerShell

**Solución 3: Usar ruta completa**
```powershell
& "C:\Program Files\Redis\redis-cli.exe" ping
```

### ❌ "El servicio Redis no se pudo iniciar"

**Opción A: Iniciar manualmente (PowerShell como Admin)**
```powershell
net start Redis
```

**Opción B: Iniciar redis-server directamente**
```powershell
redis-server
# Dejar esta ventana abierta mientras trabajas
```

**Opción C: Usar servicios de Windows**
1. Presiona `Windows + R`
2. Escribe: `services.msc`
3. Busca "Redis"
4. Click derecho → "Iniciar"
5. Click derecho → "Propiedades" → Tipo de inicio: "Automático"

---

## 📊 Una vez Redis esté funcionando:

1. **Verificar con el script:**
   ```powershell
   .\verificar_redis.bat
   ```

2. **Verificar el sistema completo:**
   ```powershell
   & e:\Escuela_backup\Escuela\.venv\Scripts\python.exe verificar_sistema.py
   ```

3. **Iniciar Celery:**
   ```powershell
   .\iniciar_celery_completo.bat
   ```

4. **Iniciar Django (en otra terminal):**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   python manage.py runserver
   ```

5. **Abrir navegador:**
   http://prueba.localhost:8000/suscripcion/

---

## 🎯 ¿Dónde estás ahora?

- [ ] **Paso 1:** Descargar Redis-x64-3.2.100.msi
- [ ] **Paso 2:** Ejecutar el instalador
- [ ] **Paso 3:** Cerrar y reabrir PowerShell
- [ ] **Paso 4:** Ejecutar `.\verificar_redis.bat`
- [ ] **Paso 5:** Ver "PONG" en la respuesta

**Cuando veas "PONG", Redis está listo! 🎉**

---

**¿Necesitas ayuda?**
- Si el instalador no arranca, descarga desde el link directo arriba
- Si Redis no aparece en PATH, usa las soluciones del troubleshooting
- Si todo falla, prueba Memurai (Opción 3) - es más fácil

**Última actualización:** 09/05/2026
