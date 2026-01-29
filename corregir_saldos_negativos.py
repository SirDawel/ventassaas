import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Escuela.settings')
django.setup()

from escuelaweb.models import Factura
from django.db.models import F

print("Buscando facturas con monto_pagado > total...")

# Buscar facturas donde el monto pagado es mayor que el total
facturas_con_exceso = Factura.objects.filter(monto_pagado__gt=F('total'))

print(f"\nFacturas encontradas: {facturas_con_exceso.count()}")

for factura in facturas_con_exceso:
    saldo_anterior = factura.total - factura.monto_pagado
    print(f"\nFactura: {factura.numero_factura}")
    print(f"  Total: RD${factura.total}")
    print(f"  Monto Pagado: RD${factura.monto_pagado}")
    print(f"  Saldo Pendiente (anterior): RD${saldo_anterior}")
    print(f"  Saldo Pendiente (nuevo): RD${factura.saldo_pendiente}")
    print(f"  Estado actual: {factura.estado}")
    
    # Actualizar estado
    factura.actualizar_estado()
    factura.save()
    
    print(f"  Estado actualizado: {factura.estado}")

print("\n✅ Corrección completada!")
print(f"Total de facturas actualizadas: {facturas_con_exceso.count()}")
