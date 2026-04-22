"""
Script para eliminar TODAS las facturas automáticas del año escolar activo
y regenerarlas correctamente (una por mes).
Ejecutar: python reset_facturas_mensuales.py
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import Factura, CustomUser, AnhoEscolar

# Obtener año escolar activo
try:
    anho_escolar = AnhoEscolar.objects.get(activo=True)
    print(f"📅 Año escolar activo: {anho_escolar.nombre}")
except AnhoEscolar.DoesNotExist:
    print("❌ No hay año escolar activo")
    sys.exit(1)

print("\n⚠️  Este script eliminará TODAS las facturas automáticas generadas")
print("    del año escolar activo y las regenerará correctamente.")
print("    ¿Estás seguro? (escribe 'SI' para continuar)")

respuesta = input("\n> ")

if respuesta.upper() != 'SI':
    print("❌ Operación cancelada")
    sys.exit(0)

# Eliminar facturas automáticas (las que tienen número FACT-YYYYMM-XXXXX)
facturas_automaticas = Factura.objects.filter(
    anho_escolar=anho_escolar,
    numero_factura__startswith='FACT-'
)

total = facturas_automaticas.count()
print(f"\n🗑️  Eliminando {total} facturas automáticas...")

facturas_automaticas.delete()

print(f"✅ {total} facturas eliminadas")
print(f"\n💡 Ahora accede a http://127.0.0.1:8000/estudiante-pagos/")
print(f"   El sistema regenerará automáticamente las facturas mensuales")
print(f"   (UNA SOLA por cada mes del año escolar)")
