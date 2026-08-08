"""
Vista de health check para monitoreo del sistema
"""
from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """
    Endpoint simple de health check para AWS ECS y monitoreo
    Verifica que la aplicación y la base de datos estén funcionando
    """
    try:
        # Verificar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'application': 'running'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
