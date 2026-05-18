@echo off
REM ==========================================
REM Instalador de Redis para Windows
REM ==========================================

echo.
echo ========================================
echo   Instalador de Redis para Windows
echo ========================================
echo.

echo Redis no viene preinstalado en Windows.
echo.
echo Opciones para instalar Redis:
echo.
echo [1] Descargar Redis precompilado (Recomendado)
echo     https://github.com/microsoftarchive/redis/releases
echo     Descargar: Redis-x64-3.2.100.msi
echo.
echo [2] Usar Memurai (Redis para Windows - Gratis)
echo     https://www.memurai.com/get-memurai
echo.
echo [3] Usar Docker (si tienes Docker Desktop)
echo     docker run -d -p 6379:6379 redis
echo.
echo [4] Usar WSL2 con Ubuntu (Avanzado)
echo     wsl --install
echo     sudo apt-get install redis-server
echo.
echo ========================================
echo.

set /p choice="Selecciona una opcion (1-4): "

if "%choice%"=="1" (
    echo.
    echo Abriendo pagina de descarga de Redis...
    start https://github.com/microsoftarchive/redis/releases/download/win-3.2.100/Redis-x64-3.2.100.msi
    echo.
    echo Instrucciones:
    echo 1. Descarga el archivo Redis-x64-3.2.100.msi
    echo 2. Ejecuta el instalador
    echo 3. Acepta todas las opciones por defecto
    echo 4. Redis se instalara como servicio de Windows
    echo 5. Vuelve a ejecutar este script para verificar
    echo.
    pause
) else if "%choice%"=="2" (
    echo.
    echo Abriendo pagina de Memurai...
    start https://www.memurai.com/get-memurai
    echo.
    echo Instrucciones:
    echo 1. Descarga Memurai Developer Edition (Gratis)
    echo 2. Instala Memurai
    echo 3. Memurai es 100%% compatible con Redis
    echo.
    pause
) else if "%choice%"=="3" (
    echo.
    echo Iniciando Redis en Docker...
    docker run -d --name redis-escuela -p 6379:6379 redis:latest
    if %errorlevel% equ 0 (
        echo [OK] Redis iniciado en Docker
        echo.
        echo Para detener: docker stop redis-escuela
        echo Para iniciar: docker start redis-escuela
    ) else (
        echo [ERROR] No se pudo iniciar Redis en Docker
        echo Asegurate de tener Docker Desktop instalado y corriendo
    )
    echo.
    pause
) else if "%choice%"=="4" (
    echo.
    echo Para instalar WSL2:
    echo 1. Abre PowerShell como Administrador
    echo 2. Ejecuta: wsl --install
    echo 3. Reinicia tu PC
    echo 4. Abre Ubuntu desde el menu inicio
    echo 5. Ejecuta: sudo apt-get update
    echo 6. Ejecuta: sudo apt-get install redis-server
    echo 7. Ejecuta: redis-server
    echo.
    pause
) else (
    echo Opcion no valida
    pause
)

echo.
echo ========================================
echo   Verificando instalacion...
echo ========================================
echo.

redis-cli ping
if %errorlevel% equ 0 (
    echo.
    echo [OK] Redis esta instalado y funcionando correctamente!
    echo.
) else (
    echo.
    echo [INFO] Redis aun no esta disponible.
    echo Instala Redis y luego ejecuta: redis-server
    echo.
)

pause
