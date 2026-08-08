"""
Este módulo asegura que Celery se cargue cuando Django inicie
"""

# Importa la aplicación Celery
from .celery import app as celery_app

__all__ = ('celery_app',)
