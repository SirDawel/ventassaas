@echo off
echo.
echo ========================================
echo   REINICIANDO SERVIDOR DJANGO
echo ========================================
echo.

REM Matar procesos Python/Uvicorn
echo Deteniendo procesos Python...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo Limpiando cache...
if exist "escuelaweb\__pycache__" (
    rd /s /q "escuelaweb\__pycache__"
)
if exist "Escuela\__pycache__" (
    rd /s /q "Escuela\__pycache__"
)

echo.
echo ========================================
echo   SERVIDOR DETENIDO
echo ========================================
echo.
echo Para iniciar el servidor ejecuta:
echo   .\.venv\Scripts\Activate.ps1
echo   python manage.py runserver
echo.
echo O con uvicorn:
echo   uvicorn Escuela.asgi:application --host 127.0.0.1 --port 8000
echo.
pause
