#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para agregar modelos stub POS
"""

modelos_pos = '''

# ============================================================================
# MODELOS POS (Stubs temporales para compatibilidad)
# ============================================================================

class TransaccionPOS(models.Model):
    """Stub temporal para transacciones POS"""
    transaction_id = models.CharField(max_length=100, unique=True)
    proveedor = models.CharField(max_length=50)
    terminal_id = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)
    estudiante = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    factura_pagada = models.ForeignKey('Factura', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(auto_now=True)
    referencia = models.CharField(max_length=100, blank=True)
    datos_webhook = models.JSONField(default=dict, blank=True)
    tarjeta_ultimos_4 = models.CharField(max_length=4, blank=True)
    tipo_tarjeta = models.CharField(max_length=20, blank=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Transacción POS"
        verbose_name_plural = "Transacciones POS"
        
    def __str__(self):
        return f"{self.transaction_id} - RD${self.monto}"


class TerminalEstudiante(models.Model):
    """Stub temporal para terminales POS"""
    terminal_id = models.CharField(max_length=50, unique=True)
    estudiante = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    proveedor = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Terminal-Estudiante"
        verbose_name_plural = "Terminales-Estudiantes"
    
    def __str__(self):
        return f"Terminal {self.terminal_id}"
'''

# Leer el archivo actual
with open('escuelaweb/models.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Agregar los modelos POS al final
with open('escuelaweb/models.py', 'w', encoding='utf-8') as f:
    f.write(contenido + modelos_pos)

print("✅ Modelos POS stub agregados exitosamente!")
