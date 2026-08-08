import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
import django
django.setup()

from escuelaweb.models import Factura, CustomUser

try:
    lucy = CustomUser.objects.get(cedula='01201012458')
    print(f"\n{'='*70}")
    print(f"📋 FACTURAS DE {lucy.get_full_name().upper()}")
    print(f"{'='*70}\n")
    
    facturas = lucy.facturas.all().order_by('-fecha_emision')
    
    if facturas.exists():
        for i, f in enumerate(facturas, 1):
            print(f"{i}. {f.numero_factura}")
            print(f"   Estado: {f.get_estado_display()}")
            print(f"   Total: RD$ {f.total:,.2f}")
            print(f"   Pagado: RD$ {f.monto_pagado:,.2f}")
            print(f"   Pendiente: RD$ {(f.total - f.monto_pagado):,.2f}")
            print(f"   Fecha emisión: {f.fecha_emision.strftime('%d/%m/%Y %H:%M')}")
            print(f"   Método pago: {f.metodo_pago}")
            print()
    else:
        print("⚠️  No tiene facturas registradas\n")
        
    print(f"{'='*70}")
    print(f"Total de facturas: {facturas.count()}")
    print(f"{'='*70}\n")
    
except CustomUser.DoesNotExist:
    print("\n❌ No se encontró el estudiante con cédula 01201012458\n")
except Exception as e:
    print(f"\n❌ Error: {str(e)}\n")
