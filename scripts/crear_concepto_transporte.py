"""Script para crear conceptos de transporte en la base de datos"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
django.setup()

from escuelaweb.models import ConceptoPago
from decimal import Decimal

# Crear conceptos de transporte
conceptos_transporte = [
    {
        'nombre': 'Transporte Escolar',
        'tipo': 'transporte',
        'monto': Decimal('0.00'),  # El monto se define en la tarifa del estudiante
        'descripcion': 'Transporte escolar mensual',
        'activo': True
    },
]

print("Creando conceptos de transporte...")

for data in conceptos_transporte:
    concepto, created = ConceptoPago.objects.get_or_create(
        nombre=data['nombre'],
        tipo=data['tipo'],
        defaults={
            'monto': data['monto'],
            'descripcion': data['descripcion'],
            'activo': data['activo']
        }
    )
    
    if created:
        print(f"✅ Creado: {concepto.nombre} - {concepto.get_tipo_display()}")
    else:
        print(f"ℹ️  Ya existe: {concepto.nombre} - {concepto.get_tipo_display()}")

print("\n✅ Proceso completado!")
print("\nConceptos de transporte disponibles:")
transportes = ConceptoPago.objects.filter(tipo='transporte', activo=True)
for t in transportes:
    print(f"  - {t.nombre}")

if transportes.count() == 0:
    print("  ⚠️ No hay conceptos de transporte activos")
