@echo off
echo.
echo ========================================
echo   Verificando Redis
echo ========================================
echo.

REM Verificar si redis-cli está disponible
redis-cli --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis CLI instalado
    redis-cli --version
    echo.
) else (
    echo [X] Redis CLI no encontrado
    echo.
    echo Posibles soluciones:
    echo 1. Reinicia tu terminal/PowerShell
    echo 2. Agrega Redis al PATH manualmente:
    echo    C:\Program Files\Redis
    echo 3. Reinstala Redis con la opcion "Add to PATH"
    echo.
    goto :end
)

REM Verificar si el servicio está corriendo
echo Verificando servicio Redis...
sc query Redis >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Servicio Redis instalado
    sc query Redis | findstr "STATE"
    echo.
) else (
    echo [X] Servicio Redis no encontrado
    echo.
)

REM Probar conexión
echo Probando conexion...
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis esta corriendo!
    redis-cli ping
    echo.
    echo ========================================
    echo   REDIS INSTALADO Y FUNCIONANDO
    echo ========================================
    echo.
    echo Siguiente paso: Iniciar Celery
    echo Ejecuta: .\iniciar_celery_completo.bat
    echo.
) else (
    echo [X] Redis no esta corriendo
    echo.
    echo Iniciando Redis...
    net start Redis >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Redis iniciado correctamente
        redis-cli ping
    ) else (
        echo [X] No se pudo iniciar Redis
        echo Ejecuta como Administrador: net start Redis
    )
    echo.
)

:end
pause
