import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VentasSys.settings')
import django
django.setup()

from escuelaweb.models import AnhoEscolar, Factura, CustomUser

print("\n" + "="*70)
print("🔍 VERIFICACIÓN DE AÑO ESCOLAR")
print("="*70)

try:
    # Ver año escolar activo
    anho_activo = AnhoEscolar.objects.get(activo=True)
    print(f"\n✅ Año escolar ACTIVO:")
    print(f"   Nombre: {anho_activo}")
    print(f"   ID: {anho_activo.id}")
    
    # Ver la factura de Lucy
    factura = Factura.objects.get(numero_factura='FAC-20260314141627-5223')
    print(f"\n📄 Factura FAC-20260314141627-5223:")
    print(f"   Cliente: {factura.cliente.get_full_name()}")
    print(f"   Año escolar: {factura.anho_escolar}")
    print(f"   ID año: {factura.anho_escolar.id}")
    print(f"   Estado: {factura.get_estado_display()}")
    
    # Comparar
    print(f"\n{'='*70}")
    if anho_activo.id == factura.anho_escolar.id:
        print("✅ La factura SÍ pertenece al año escolar activo")
        print("   → DEBERÍA aparecer en http://127.0.0.1:8000/facturas/")
    else:
        print("⚠️  La factura NO pertenece al año escolar activo")
        print("   → NO aparecerá en la lista de facturas")
    print("="*70)
    
    # Contar facturas en el año activo
    total_facturas = Factura.objects.filter(anho_escolar=anho_activo).count()
    print(f"\n📊 Total de facturas en año activo: {total_facturas}")
    
    # Ver si Lucy tiene facturas en el año activo
    lucy = CustomUser.objects.get(cedula='01201012458')
    facturas_lucy_activo = Factura.objects.filter(
        cliente=lucy,
        anho_escolar=anho_activo
    ).count()
    print(f"📋 Facturas de Lucy en año activo: {facturas_lucy_activo}")
    
    print("\n" + "="*70 + "\n")
    
except AnhoEscolar.DoesNotExist:
    print("\n❌ No hay año escolar activo configurado\n")
except Factura.DoesNotExist:
    print("\n❌ No se encontró la factura FAC-20260314141627-5223\n")
except Exception as e:
    print(f"\n❌ Error: {str(e)}\n")
    import traceback
    traceback.print_exc()
