@echo off
REM ==========================================
REM Iniciar Celery Beat (Tareas Programadas)
REM ==========================================

echo.
echo ========================================
echo   Iniciando Celery Beat
echo ========================================
echo.

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Verificar que Redis está corriendo
redis-cli ping > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Redis no está corriendo!
    echo.
    echo Por favor, inicia Redis primero:
    echo   1. Abre una terminal
    echo   2. Ejecuta: redis-server
    echo.
    pause
    exit /b 1
)

echo [OK] Redis está corriendo
echo.

REM Iniciar Celery Beat
echo Iniciando Celery Beat (tareas programadas)...
echo (Presiona Ctrl+C para detener)
echo.

celery -A Escuela beat --loglevel=info

pause
