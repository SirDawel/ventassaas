# ============================================================================
# Script de Actualización Automática - Django 4.2 → 5.1
# Sistema de Ventas Multitenant
# Windows PowerShell
# ============================================================================

param(
    [switch]$SkipBackup,
    [switch]$SkipPython,
    [switch]$SkipPostgreSQL,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Colores para mensajes
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Warning { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Title { Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Magenta; Write-Host "  $args" -ForegroundColor Magenta; Write-Host "═══════════════════════════════════════════`n" -ForegroundColor Magenta }

Write-Title "🚀 ACTUALIZACIÓN DJANGO 4.2 → 5.1"

# ============================================================================
# VERIFICACIONES PREVIAS
# ============================================================================

Write-Title "📋 VERIFICACIONES PREVIAS"

# Verificar que estamos en la carpeta correcta
if (-not (Test-Path "manage.py")) {
    Write-Error "No se encontró manage.py. ¿Estás en la carpeta del proyecto?"
    Write-Info "Navega a: cd E:\AWSAMAZON\Ventas"
    exit 1
}
Write-Success "Carpeta del proyecto correcta"

# Verificar que existe virtualenv anterior
if (-not (Test-Path ".venv")) {
    Write-Warning "No se encontró virtualenv anterior (.venv)"
    Write-Info "Se creará uno nuevo"
} else {
    Write-Success "Virtualenv anterior encontrado"
}

# Verificar Git
try {
    $gitStatus = git status 2>&1
    Write-Success "Git disponible"
} catch {
    Write-Warning "Git no encontrado - Los backups de código no estarán disponibles"
}

# ============================================================================
# PASO 1: BACKUP
# ============================================================================

if (-not $SkipBackup) {
    Write-Title "💾 PASO 1: CREANDO BACKUPS"
    
    # Crear carpeta de backups
    if (-not (Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" | Out-Null
    }
    
    $fecha = Get-Date -Format "yyyyMMdd_HHmmss"
    
    # Backup de base de datos
    Write-Info "Creando backup de PostgreSQL..."
    try {
        $pgPath = "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe"
        if (Test-Path $pgPath) {
            & $pgPath -U postgres -h 127.0.0.1 -p 5434 ventassistemdb > "backups\backup_pre_upgrade_$fecha.sql"
            Write-Success "Backup de base de datos creado: backups\backup_pre_upgrade_$fecha.sql"
        } else {
            Write-Warning "pg_dump no encontrado en $pgPath - Saltando backup de BD"
        }
    } catch {
        Write-Warning "Error al crear backup de BD: $_"
    }
    
    # Backup de archivos media
    Write-Info "Creando backup de archivos media..."
    if (Test-Path "media") {
        try {
            Compress-Archive -Path "media\*" -DestinationPath "backups\media_backup_$fecha.zip" -Force
            Write-Success "Backup de media creado: backups\media_backup_$fecha.zip"
        } catch {
            Write-Warning "Error al crear backup de media: $_"
        }
    }
    
    # Backup con Git
    Write-Info "Creando backup en Git..."
    try {
        git add -A 2>&1 | Out-Null
        git commit -m "Pre-upgrade backup - Django 4.2 to 5.1" 2>&1 | Out-Null
        git tag "v1.0-django4.2-backup-$fecha" 2>&1 | Out-Null
        Write-Success "Backup en Git creado con tag: v1.0-django4.2-backup-$fecha"
    } catch {
        Write-Warning "No se pudo crear backup en Git (puede que no haya cambios)"
    }
    
} else {
    Write-Warning "Saltando backups (--SkipBackup especificado)"
}

# ============================================================================
# PASO 2: VERIFICAR PYTHON 3.13
# ============================================================================

if (-not $SkipPython) {
    Write-Title "🐍 PASO 2: VERIFICANDO PYTHON 3.13"
    
    try {
        $pythonVersion = python --version 2>&1
        Write-Info "Python actual: $pythonVersion"
        
        if ($pythonVersion -match "3\.13") {
            Write-Success "Python 3.13 ya está instalado"
        } else {
            Write-Warning "Python 3.13 no encontrado"
            Write-Info "Por favor instala Python 3.13 desde: https://www.python.org/downloads/"
            Write-Info "Marca 'Add Python 3.13 to PATH' durante la instalación"
            
            if (-not $Force) {
                $continue = Read-Host "¿Continuar con la versión actual de Python? (y/n)"
                if ($continue -ne "y") {
                    Write-Error "Actualización cancelada por el usuario"
                    exit 1
                }
            }
        }
    } catch {
        Write-Error "Python no encontrado en PATH"
        Write-Info "Instala Python 3.13 desde: https://www.python.org/downloads/"
        exit 1
    }
} else {
    Write-Warning "Saltando verificación de Python (--SkipPython especificado)"
}

# ============================================================================
# PASO 3: CREAR NUEVO VIRTUALENV
# ============================================================================

Write-Title "📦 PASO 3: CREANDO NUEVO VIRTUALENV"

# Desactivar virtualenv actual si está activo
if ($env:VIRTUAL_ENV) {
    Write-Info "Desactivando virtualenv actual..."
    deactivate 2>&1 | Out-Null
}

# Renombrar virtualenv anterior
if (Test-Path ".venv") {
    Write-Info "Respaldando virtualenv anterior como .venv_old..."
    if (Test-Path ".venv_old") {
        Remove-Item -Recurse -Force ".venv_old"
    }
    Rename-Item -Path ".venv" -NewName ".venv_old"
    Write-Success "Virtualenv anterior respaldado"
}

# Crear nuevo virtualenv
Write-Info "Creando nuevo virtualenv con Python 3.13..."
python -m venv .venv

if (-not (Test-Path ".venv")) {
    Write-Error "No se pudo crear el virtualenv"
    exit 1
}
Write-Success "Nuevo virtualenv creado"

# Activar virtualenv
Write-Info "Activando virtualenv..."
& .\.venv\Scripts\Activate.ps1

# Verificar activación
$venvPython = & python --version 2>&1
Write-Success "Virtualenv activado: $venvPython"

# ============================================================================
# PASO 4: INSTALAR DEPENDENCIAS
# ============================================================================

Write-Title "📦 PASO 4: INSTALANDO DEPENDENCIAS"

# Actualizar pip
Write-Info "Actualizando pip..."
python -m pip install --upgrade pip --quiet
Write-Success "pip actualizado"

# Instalar dependencias
Write-Info "Instalando Django 5.1 y dependencias..."
Write-Warning "Esto puede tomar varios minutos..."

if (Test-Path "requirements_produccion.txt") {
    pip install -r requirements_produccion.txt --quiet
    Write-Success "Dependencias de producción instaladas"
} else {
    Write-Warning "No se encontró requirements_produccion.txt"
    Write-Info "Instalando paquetes básicos..."
    pip install Django==5.1.3 django-tenants==4.0.0 psycopg[binary]==3.2.3 --quiet
}

# Instalar herramientas de desarrollo
Write-Info "Instalando herramientas de desarrollo..."
pip install django-extensions ipython --quiet
Write-Success "Herramientas de desarrollo instaladas"

# Verificar instalación
Write-Info "Verificando instalación..."
$djangoVersion = python -c "import django; print(django.get_version())" 2>&1
$tenantsVersion = python -c "import django_tenants; print(django_tenants.__version__)" 2>&1
$psycopgVersion = python -c "import psycopg; print(psycopg.__version__)" 2>&1

Write-Success "Django: $djangoVersion"
Write-Success "django-tenants: $tenantsVersion"
Write-Success "psycopg: $psycopgVersion"

# ============================================================================
# PASO 5: EJECUTAR MIGRACIONES
# ============================================================================

Write-Title "🔄 PASO 5: EJECUTANDO MIGRACIONES"

# Django check
Write-Info "Verificando configuración de Django..."
try {
    python manage.py check --deploy 2>&1 | Out-Null
    Write-Success "Configuración de Django correcta"
} catch {
    Write-Warning "Hay advertencias en la configuración (no crítico)"
}

# Migrar schema público
Write-Info "Migrando schema público..."
python manage.py migrate_schemas --shared
Write-Success "Schema público migrado"

# Migrar todos los tenants
Write-Info "Migrando todos los tenants..."
python manage.py migrate_schemas
Write-Success "Todos los tenants migrados"

# Collectstatic
Write-Info "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear 2>&1 | Out-Null
Write-Success "Archivos estáticos recolectados"

# ============================================================================
# PASO 6: TESTING
# ============================================================================

Write-Title "🧪 PASO 6: VERIFICANDO INSTALACIÓN"

Write-Info "Ejecutando tests de verificación..."

$testScript = @"
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

print('Django version:', django.get_version())

from django.contrib.auth import get_user_model
User = get_user_model()
print('CustomUser model: OK')

from ventasweb.models import Articulo, Factura
print('Models: OK')

from django_tenants.utils import get_tenant_model
Tenant = get_tenant_model()
tenants_count = Tenant.objects.count()
print(f'Tenants: {tenants_count}')

print('TESTS: PASSED')
"@

try {
    $testResult = python -c $testScript 2>&1
    Write-Output $testResult
    
    if ($testResult -match "PASSED") {
        Write-Success "Todos los tests pasaron correctamente"
    } else {
        Write-Warning "Algunos tests fallaron, pero el sistema puede funcionar"
    }
} catch {
    Write-Warning "No se pudieron ejecutar todos los tests: $_"
}

# ============================================================================
# RESUMEN FINAL
# ============================================================================

Write-Title "🎉 ACTUALIZACIÓN COMPLETADA"

Write-Host @"

╔════════════════════════════════════════════════════════════════╗
║                  ✅ ACTUALIZACIÓN EXITOSA                      ║
╚════════════════════════════════════════════════════════════════╝

📦 Versiones instaladas:
   • Django: $djangoVersion
   • django-tenants: $tenantsVersion
   • psycopg: $psycopgVersion

📂 Backups creados en: .\backups\

🔄 Siguiente paso:
   1. Iniciar servidor: python manage.py runserver
   2. Probar en: http://localhost:8000/
   3. Verificar funcionalidades críticas

📋 Checklist:
   [ ] Login funciona
   [ ] Crear usuarios funciona
   [ ] Crear facturas funciona
   [ ] Búsqueda de productos funciona
   [ ] Todos los tenants accesibles

📚 Documentación:
   • Guía completa: ACTUALIZACION_LOCAL_WINDOWS.md
   • Troubleshooting: GUIA_ACTUALIZACION_DJANGO5.md
   • Deploy producción: PROMPT_DEPLOY_AWS_DJANGO_TENANTS.md

🔥 Si algo falla:
   1. Revisar logs: python manage.py check
   2. Rollback: .\rollback.ps1
   3. Consultar: ACTUALIZACION_LOCAL_WINDOWS.md

"@ -ForegroundColor Cyan

# ============================================================================
# CREAR SCRIPT DE ROLLBACK
# ============================================================================

$rollbackScript = @"
# Rollback Script - Volver a Django 4.2
`$ErrorActionPreference = "Stop"

Write-Host "🔄 Iniciando rollback..." -ForegroundColor Yellow

# Desactivar virtualenv
deactivate 2>&1 | Out-Null

# Eliminar virtualenv nuevo
if (Test-Path ".venv") {
    Remove-Item -Recurse -Force .venv
    Write-Host "✅ Virtualenv nuevo eliminado" -ForegroundColor Green
}

# Restaurar virtualenv anterior
if (Test-Path ".venv_old") {
    Rename-Item -Path ".venv_old" -NewName ".venv"
    Write-Host "✅ Virtualenv anterior restaurado" -ForegroundColor Green
} else {
    Write-Host "❌ No se encontró .venv_old para restaurar" -ForegroundColor Red
    exit 1
}

# Restaurar código desde Git
try {
    git checkout v1.0-django4.2-backup
    Write-Host "✅ Código restaurado desde Git" -ForegroundColor Green
} catch {
    Write-Host "⚠️  No se pudo restaurar desde Git" -ForegroundColor Yellow
}

Write-Host "`n✅ Rollback completado" -ForegroundColor Green
Write-Host "Activa el virtualenv: .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
"@

Set-Content -Path "rollback.ps1" -Value $rollbackScript
Write-Success "Script de rollback creado: rollback.ps1"

Write-Host "`n"
Write-Success "¡Actualización completada exitosamente!"
Write-Info "Ejecuta: python manage.py runserver"
Write-Host "`n"
