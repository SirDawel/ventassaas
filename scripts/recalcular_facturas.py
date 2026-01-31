#!/usr/bin/env python
"""
Script para recalcular totales de todas las facturas
Ejecutar con: python scripts/recalcular_facturas.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import Factura, DetalleFactura

print("=" * 60)
print("RECALCULANDO TODAS LAS FACTURAS")
print("=" * 60)

# Primero, asegurar que todos los detalles tengan descripción
print("\n1. Actualizando descripciones de detalles...")
detalles_sin_desc = DetalleFactura.objects.filter(descripcion__isnull=True) | DetalleFactura.objects.filter(descripcion='')
detalles_actualizados = 0
for detalle in detalles_sin_desc:
    detalle.descripcion = detalle.concepto.nombre
    detalle.save(update_fields=['descripcion'])
    detalles_actualizados += 1
print(f"   ✓ {detalles_actualizados} detalles actualizados")

# Recalcular totales de todas las facturas
print("\n2. Recalculando totales de facturas...")
facturas_actualizadas = 0
for factura in Factura.objects.all():
    # Calcular totales
    factura.calcular_totales()
    factura.actualizar_estado()
    factura.save()
    
    facturas_actualizadas += 1
    detalles_count = factura.detalles.count()
    print(f"   ✓ {factura.numero_factura}: {detalles_count} detalles, Total: RD${factura.total}")

print(f"\n{'=' * 60}")
print(f"COMPLETADO: {facturas_actualizadas} facturas recalculadas")
print(f"{'=' * 60}\n")
