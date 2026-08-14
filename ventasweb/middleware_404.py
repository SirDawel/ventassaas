# -*- coding: utf-8 -*-
"""
Middleware personalizado para manejar errores 404
Intercepta 404s incluso en DEBUG mode y muestra una página amigable
sin exponer todas las URLs del sistema
"""
from django.shortcuts import render
from django.http import Http404


class Custom404Middleware:
    """
    Middleware que captura errores 404 y muestra una página personalizada
    Funciona tanto en DEBUG=True como DEBUG=False
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Si la respuesta es 404, renderizar nuestro template personalizado
        if response.status_code == 404:
            return render(request, '404.html', status=404)
        
        return response
    
    def process_exception(self, request, exception):
        """
        Captura excepciones Http404 y devuelve nuestra página personalizada
        """
        if isinstance(exception, Http404):
            return render(request, '404.html', status=404)
        return None
