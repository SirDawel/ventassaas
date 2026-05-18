"""
Script de Verificación del Sistema Completo
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from django.db import connection
from django_tenants.utils import get_public_schema_name
from escuelaweb.models import Plan, Suscripcion, CustomUser

def verificar_sistema():
    """Verifica que todos los componentes estén configurados"""
    
    print("=" * 60)
    print("  VERIFICACIÓN DEL SISTEMA COMPLETO")
    print("=" * 60)
    print()
    
    errores = []
    warnings = []
    
    # 1. Verificar Base de Datos
    print("✓ Verificando Base de Datos...")
    try:
        connection.ensure_connection()
        print("  ✅ Conexión a PostgreSQL: OK")
    except Exception as e:
        errores.append(f"Base de datos: {e}")
        print(f"  ❌ Error de conexión: {e}")
    
    # 2. Verificar Planes
    print("\n✓ Verificando Planes de Suscripción...")
    try:
        connection.set_schema(get_public_schema_name())
        planes = Plan.objects.filter(activo=True).count()
        if planes >= 4:
            print(f"  ✅ Planes configurados: {planes}")
        else:
            warnings.append(f"Solo hay {planes} planes activos. Se esperan 4.")
            print(f"  ⚠️  Solo hay {planes} planes. Ejecuta: python scripts/crear_planes_suscripcion.py")
    except Exception as e:
        errores.append(f"Planes: {e}")
        print(f"  ❌ Error al verificar planes: {e}")
    
    # 3. Verificar Suscripciones
    print("\n✓ Verificando Suscripciones...")
    try:
        suscripciones = Suscripcion.objects.count()
        print(f"  ✅ Suscripciones creadas: {suscripciones}")
        
        # Ver estado de cada tenant
        for sus in Suscripcion.objects.select_related('tenant', 'plan').all():
            print(f"     - {sus.tenant.nombre}: {sus.plan.nombre} ({sus.estado})")
            
    except Exception as e:
        errores.append(f"Suscripciones: {e}")
        print(f"  ❌ Error al verificar suscripciones: {e}")
    
    # 4. Verificar Stripe
    print("\n✓ Verificando Configuración de Stripe...")
    from django.conf import settings
    
    if settings.STRIPE_SECRET_KEY:
        if settings.STRIPE_SECRET_KEY.startswith('sk_test_'):
            print("  ✅ Stripe Secret Key: Configurada (TEST)")
        elif settings.STRIPE_SECRET_KEY.startswith('sk_live_'):
            print("  ✅ Stripe Secret Key: Configurada (LIVE)")
        else:
            warnings.append("Stripe secret key no parece válida")
            print("  ⚠️  Stripe Secret Key: Formato no reconocido")
    else:
        warnings.append("Stripe no está configurado")
        print("  ⚠️  Stripe Secret Key: No configurada")
        print("     Agrega STRIPE_SECRET_KEY en .env")
    
    if settings.STRIPE_PUBLIC_KEY:
        print("  ✅ Stripe Public Key: Configurada")
    else:
        print("  ⚠️  Stripe Public Key: No configurada")
    
    # 5. Verificar Celery
    print("\n✓ Verificando Configuración de Celery...")
    
    if settings.CELERY_BROKER_URL:
        print(f"  ✅ Broker URL: {settings.CELERY_BROKER_URL}")
    else:
        warnings.append("Celery broker no configurado")
        print("  ⚠️  Broker URL: No configurado")
    
    # Intentar importar tareas
    try:
        from escuelaweb import tasks
        print("  ✅ Módulo de tareas: Importado correctamente")
        
        # Contar tareas
        tareas = [attr for attr in dir(tasks) if not attr.startswith('_')]
        print(f"  ✅ Tareas disponibles: {len(tareas)}")
        
    except Exception as e:
        errores.append(f"Tareas: {e}")
        print(f"  ❌ Error al importar tareas: {e}")
    
    # 6. Verificar Redis
    print("\n✓ Verificando Redis...")
    try:
        import redis
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        print("  ✅ Redis: Conectado y funcionando")
    except ImportError:
        warnings.append("Librería redis no instalada")
        print("  ⚠️  Librería redis no instalada (pip install redis)")
    except Exception as e:
        warnings.append(f"Redis no está corriendo: {e}")
        print(f"  ⚠️  Redis: No conectado ({e})")
        print("     Inicia Redis con: redis-server")
        print("     O instala Redis: .\\instalar_redis.bat")
    
    # 7. Verificar Email
    print("\n✓ Verificando Configuración de Email...")
    if settings.EMAIL_HOST_USER:
        print(f"  ✅ Email: Configurado ({settings.EMAIL_HOST})")
    else:
        warnings.append("Email no configurado")
        print("  ⚠️  Email: No configurado")
        print("     Agrega EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en .env")
    
    # 8. Verificar Apps de Celery
    print("\n✓ Verificando Apps de Django...")
    celery_apps = [
        'django_celery_beat',
        'django_celery_results'
    ]
    for app in celery_apps:
        if app in settings.INSTALLED_APPS:
            print(f"  ✅ {app}: Instalado")
        else:
            errores.append(f"App {app} no está en INSTALLED_APPS")
            print(f"  ❌ {app}: No instalado")
    
    # 9. Verificar Templates
    print("\n✓ Verificando Templates de Suscripción...")
    import os
    templates = [
        'escuelaweb/templates/suscripcion/dashboard.html',
        'escuelaweb/templates/suscripcion/planes.html',
        'escuelaweb/templates/suscripcion/checkout.html',
        'escuelaweb/templates/suscripcion/pago_exitoso.html',
    ]
    for template in templates:
        if os.path.exists(template):
            print(f"  ✅ {os.path.basename(template)}")
        else:
            errores.append(f"Template faltante: {template}")
            print(f"  ❌ {os.path.basename(template)}: No encontrado")
    
    # Resumen
    print("\n" + "=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    
    if not errores and not warnings:
        print("\n✅ ¡TODO PERFECTO! El sistema está completamente configurado.")
        print("\nPróximos pasos:")
        print("1. Iniciar Django: python manage.py runserver")
        print("2. Iniciar Celery: .\\iniciar_celery_completo.bat")
        print("3. Abrir: http://prueba.localhost:8000/suscripcion/")
        
    else:
        if errores:
            print(f"\n❌ {len(errores)} ERROR(ES) CRÍTICO(S):")
            for i, error in enumerate(errores, 1):
                print(f"   {i}. {error}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} ADVERTENCIA(S):")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")
        
        print("\n📖 Consulta la guía: INICIO_RAPIDO_SISTEMA_COMPLETO.md")
    
    print("\n" + "=" * 60)
    
    return len(errores) == 0

if __name__ == '__main__':
    try:
        exito = verificar_sistema()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
