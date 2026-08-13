# ============================================================================
# Script de Verificación Post-Actualización
# Verifica que todo funcione correctamente después de actualizar a Django 5.1
# ============================================================================

$ErrorActionPreference = "Stop"

function Write-Title { 
    Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $args" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════`n" -ForegroundColor Cyan 
}

function Write-Check { 
    param([string]$Message, [bool]$Success)
    if ($Success) {
        Write-Host "  ✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $Message" -ForegroundColor Red
    }
}

Write-Title "🧪 VERIFICACIÓN POST-ACTUALIZACIÓN"

$totalTests = 0
$passedTests = 0

# ============================================================================
# 1. VERIFICAR VIRTUALENV
# ============================================================================

Write-Host "1️⃣  Verificando virtualenv..." -ForegroundColor Yellow

$totalTests++
if ($env:VIRTUAL_ENV) {
    Write-Check "Virtualenv está activo" $true
    $passedTests++
} else {
    Write-Check "Virtualenv NO está activo" $false
    Write-Host "     Ejecuta: .\.venv\Scripts\Activate.ps1`n" -ForegroundColor Cyan
}

# ============================================================================
# 2. VERIFICAR VERSIONES
# ============================================================================

Write-Host "`n2️⃣  Verificando versiones..." -ForegroundColor Yellow

try {
    $pythonVer = python --version 2>&1
    $totalTests++
    if ($pythonVer -match "3\.13") {
        Write-Check "Python 3.13 instalado: $pythonVer" $true
        $passedTests++
    } else {
        Write-Check "Python: $pythonVer (se recomienda 3.13)" $false
    }
} catch {
    Write-Check "Python no encontrado" $false
    $totalTests++
}

try {
    $djangoVer = python -c "import django; print(django.get_version())" 2>&1
    $totalTests++
    if ($djangoVer -match "5\.1") {
        Write-Check "Django 5.1 instalado: $djangoVer" $true
        $passedTests++
    } else {
        Write-Check "Django: $djangoVer (se esperaba 5.1.x)" $false
    }
} catch {
    Write-Check "Django no instalado correctamente" $false
    $totalTests++
}

try {
    $tenantsVer = python -c "import django_tenants; print(django_tenants.__version__)" 2>&1
    $totalTests++
    if ($tenantsVer -match "4\.0") {
        Write-Check "django-tenants 4.0 instalado: $tenantsVer" $true
        $passedTests++
    } else {
        Write-Check "django-tenants: $tenantsVer (se esperaba 4.0.x)" $false
    }
} catch {
    Write-Check "django-tenants no instalado correctamente" $false
    $totalTests++
}

try {
    $psycopgVer = python -c "import psycopg; print(psycopg.__version__)" 2>&1
    $totalTests++
    if ($psycopgVer -match "3\.") {
        Write-Check "psycopg3 instalado: $psycopgVer" $true
        $passedTests++
    } else {
        Write-Check "psycopg: $psycopgVer (se esperaba 3.x)" $false
    }
} catch {
    Write-Check "psycopg3 no instalado correctamente" $false
    $totalTests++
}

# ============================================================================
# 3. VERIFICAR ARCHIVOS DEL PROYECTO
# ============================================================================

Write-Host "`n3️⃣  Verificando archivos del proyecto..." -ForegroundColor Yellow

$archivos = @(
    "manage.py",
    "VentasSys\settings.py",
    ".env",
    "requirements_produccion.txt"
)

foreach ($archivo in $archivos) {
    $totalTests++
    if (Test-Path $archivo) {
        Write-Check "$archivo existe" $true
        $passedTests++
    } else {
        Write-Check "$archivo NO encontrado" $false
    }
}

# ============================================================================
# 4. VERIFICAR CONFIGURACIÓN DJANGO
# ============================================================================

Write-Host "`n4️⃣  Verificando configuración Django..." -ForegroundColor Yellow

try {
    $checkOutput = python manage.py check 2>&1
    $totalTests++
    if ($LASTEXITCODE -eq 0) {
        Write-Check "Django check: OK" $true
        $passedTests++
    } else {
        Write-Check "Django check: Tiene errores" $false
        Write-Host "     $checkOutput" -ForegroundColor Gray
    }
} catch {
    Write-Check "No se pudo ejecutar Django check" $false
    $totalTests++
}

# ============================================================================
# 5. VERIFICAR BASE DE DATOS
# ============================================================================

Write-Host "`n5️⃣  Verificando base de datos..." -ForegroundColor Yellow

$dbTestScript = @"
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("OK")
except Exception as e:
    print(f"ERROR: {e}")
"@

try {
    $dbResult = python -c $dbTestScript 2>&1
    $totalTests++
    if ($dbResult -match "OK") {
        Write-Check "Conexión a base de datos: OK" $true
        $passedTests++
    } else {
        Write-Check "Conexión a base de datos: ERROR" $false
        Write-Host "     $dbResult" -ForegroundColor Gray
    }
} catch {
    Write-Check "No se pudo verificar base de datos" $false
    $totalTests++
}

# ============================================================================
# 6. VERIFICAR MODELOS
# ============================================================================

Write-Host "`n6️⃣  Verificando modelos Django..." -ForegroundColor Yellow

$modelsTestScript = @"
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    print(f"CustomUser: OK ({User.__name__})")
    
    from ventasweb.models import Articulo, Factura
    print("Models: OK")
    
    from django_tenants.utils import get_tenant_model
    Tenant = get_tenant_model()
    count = Tenant.objects.count()
    print(f"Tenants: OK ({count} tenants)")
    
except Exception as e:
    print(f"ERROR: {e}")
"@

try {
    $modelsResult = python -c $modelsTestScript 2>&1
    $totalTests += 3
    
    if ($modelsResult -match "CustomUser: OK") {
        Write-Check "CustomUser model: OK" $true
        $passedTests++
    } else {
        Write-Check "CustomUser model: ERROR" $false
    }
    
    if ($modelsResult -match "Models: OK") {
        Write-Check "Modelos principales: OK" $true
        $passedTests++
    } else {
        Write-Check "Modelos principales: ERROR" $false
    }
    
    if ($modelsResult -match "Tenants: OK") {
        $tenantsCount = ($modelsResult | Select-String -Pattern "Tenants: OK \((\d+)").Matches.Groups[1].Value
        Write-Check "django-tenants: OK ($tenantsCount tenants)" $true
        $passedTests++
    } else {
        Write-Check "django-tenants: ERROR" $false
    }
} catch {
    Write-Check "No se pudieron verificar modelos" $false
    $totalTests += 3
}

# ============================================================================
# 7. VERIFICAR REDIS (Opcional)
# ============================================================================

Write-Host "`n7️⃣  Verificando Redis (opcional)..." -ForegroundColor Yellow

try {
    $redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('OK')" 2>&1
    $totalTests++
    if ($redisTest -match "OK") {
        Write-Check "Redis: OK (conectado)" $true
        $passedTests++
    } else {
        Write-Check "Redis: No disponible (opcional)" $false
        Write-Host "     Para Celery necesitas Redis corriendo" -ForegroundColor Gray
    }
} catch {
    Write-Check "Redis: No instalado (opcional para Celery)" $false
    $totalTests++
}

# ============================================================================
# 8. VERIFICAR ARCHIVOS ESTÁTICOS
# ============================================================================

Write-Host "`n8️⃣  Verificando archivos estáticos..." -ForegroundColor Yellow

$totalTests++
if (Test-Path "staticfiles") {
    Write-Check "Carpeta staticfiles existe" $true
    $passedTests++
    
    $staticCount = (Get-ChildItem -Path "staticfiles" -Recurse -File).Count
    Write-Host "     $staticCount archivos estáticos encontrados" -ForegroundColor Gray
} else {
    Write-Check "Carpeta staticfiles NO existe" $false
    Write-Host "     Ejecuta: python manage.py collectstatic" -ForegroundColor Cyan
}

# ============================================================================
# RESUMEN
# ============================================================================

Write-Title "📊 RESUMEN"

$percentage = [math]::Round(($passedTests / $totalTests) * 100, 2)

Write-Host "  Tests ejecutados: $totalTests" -ForegroundColor White
Write-Host "  Tests exitosos:   $passedTests" -ForegroundColor Green
Write-Host "  Tests fallidos:   $($totalTests - $passedTests)" -ForegroundColor Red
Write-Host "  Porcentaje:       $percentage%" -ForegroundColor $(if ($percentage -ge 80) { "Green" } elseif ($percentage -ge 60) { "Yellow" } else { "Red" })

Write-Host ""

if ($percentage -ge 90) {
    Write-Host "  🎉 ¡EXCELENTE! El sistema está funcionando perfectamente" -ForegroundColor Green
    Write-Host "     Puedes iniciar el servidor: python manage.py runserver" -ForegroundColor Cyan
} elseif ($percentage -ge 70) {
    Write-Host "  ⚠️  ACEPTABLE. Hay algunos problemas menores" -ForegroundColor Yellow
    Write-Host "     Revisa los tests fallidos arriba" -ForegroundColor Cyan
} else {
    Write-Host "  ❌ PROBLEMAS DETECTADOS. Se requiere atención" -ForegroundColor Red
    Write-Host "     Revisa los errores y consulta: ACTUALIZACION_LOCAL_WINDOWS.md" -ForegroundColor Cyan
}

Write-Host ""

# ============================================================================
# PRÓXIMOS PASOS
# ============================================================================

Write-Host "📋 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Iniciar servidor de desarrollo:" -ForegroundColor White
Write-Host "     python manage.py runserver`n" -ForegroundColor Gray

Write-Host "  2. Probar en navegador:" -ForegroundColor White
Write-Host "     http://localhost:8000/" -ForegroundColor Gray
Write-Host "     http://picapolloeka.localhost:8000/`n" -ForegroundColor Gray

Write-Host "  3. Iniciar Celery (si lo usas):" -ForegroundColor White
Write-Host "     celery -A VentasSys worker --pool=solo -l info" -ForegroundColor Gray
Write-Host "     celery -A VentasSys beat -l info`n" -ForegroundColor Gray

Write-Host "  4. Verificar funcionalidades:" -ForegroundColor White
Write-Host "     [ ] Login" -ForegroundColor Gray
Write-Host "     [ ] Crear usuarios" -ForegroundColor Gray
Write-Host "     [ ] Crear facturas" -ForegroundColor Gray
Write-Host "     [ ] Búsqueda de productos" -ForegroundColor Gray
Write-Host "     [ ] Acceso a diferentes tenants`n" -ForegroundColor Gray

Write-Host "📚 DOCUMENTACIÓN:" -ForegroundColor Cyan
Write-Host "  • ACTUALIZACION_LOCAL_WINDOWS.md" -ForegroundColor Gray
Write-Host "  • GUIA_ACTUALIZACION_DJANGO5.md" -ForegroundColor Gray
Write-Host ""
