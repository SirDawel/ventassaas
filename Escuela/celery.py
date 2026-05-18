"""
Configuración de Celery para el proyecto Escuela
"""
import os
from celery import Celery
from celery.schedules import crontab

# Establece el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')

# Crea la instancia de Celery
app = Celery('Escuela')

# Lee la configuración desde settings.py usando el namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubre tareas en todas las apps instaladas
app.autodiscover_tasks()


# Configuración de tareas programadas
app.conf.beat_schedule = {
    # Verificar suscripciones próximas a vencer - Todos los días a las 8:00 AM
    'verificar-suscripciones-por-vencer': {
        'task': 'escuelaweb.tasks.verificar_suscripciones_por_vencer',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Enviar recordatorios de pago - Todos los días a las 9:00 AM
    'enviar-recordatorios-pago': {
        'task': 'escuelaweb.tasks.enviar_recordatorios_pago',
        'schedule': crontab(hour=9, minute=0),
    },
    
    # Actualizar estados de suscripciones vencidas - Cada hora
    'actualizar-suscripciones-vencidas': {
        'task': 'escuelaweb.tasks.actualizar_suscripciones_vencidas',
        'schedule': crontab(minute=0),  # Cada hora en punto
    },
    
    # Generar reporte mensual de suscripciones - Primer día del mes a las 10:00 AM
    'generar-reporte-mensual': {
        'task': 'escuelaweb.tasks.generar_reporte_mensual_suscripciones',
        'schedule': crontab(hour=10, minute=0, day_of_month=1),
    },
    
    # Verificar pagos pendientes en Stripe - Cada 6 horas
    'verificar-pagos-pendientes': {
        'task': 'escuelaweb.tasks.verificar_pagos_pendientes_stripe',
        'schedule': crontab(minute=0, hour='*/6'),  # 0:00, 6:00, 12:00, 18:00
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Tarea de prueba para verificar que Celery está funcionando
    """
    print(f'Request: {self.request!r}')
