"""
Script para cargar asientos contables de ejemplo
Ejecutar desde manage.py shell_plus o shell
"""

from datetime import date
from decimal import Decimal
from escuelaweb.models import AsientoContable, DetalleAsiento, PlanCuentas, CustomUser

def cargar_asientos_ejemplo():
    """Carga asientos contables de ejemplo"""
    
    print("=" * 80)
    print("CARGANDO ASIENTOS CONTABLES DE EJEMPLO")
    print("=" * 80)
    
    # Obtener un usuario administrador
    try:
        usuario = CustomUser.objects.filter(rol='Administrador').first()
        if not usuario:
            print("❌ No se encontró un usuario administrador. Abortando.")
            return
    except Exception as e:
        print(f"❌ Error al obtener usuario: {e}")
        return
    
    print(f"✓ Usuario para los asientos: {usuario.get_full_name()}")
    
    # Verificar que existan cuentas
    cuentas_necesarias = {
        'caja': PlanCuentas.objects.filter(codigo='1.01.01', es_detalle=True).first(),
        'banco': PlanCuentas.objects.filter(codigo='1.01.02', es_detalle=True).first(),
        'ingreso_matriculas': PlanCuentas.objects.filter(codigo='4.01.01', es_detalle=True).first(),
        'ingreso_mensualidades': PlanCuentas.objects.filter(codigo='4.01.02', es_detalle=True).first(),
        'gasto_salarios': PlanCuentas.objects.filter(codigo='5.01.01', es_detalle=True).first(),
        'gasto_servicios': PlanCuentas.objects.filter(codigo='5.02.01', es_detalle=True).first(),
        'cuentas_cobrar': PlanCuentas.objects.filter(codigo='1.02.01', es_detalle=True).first(),
    }
    
    # Verificar que todas las cuentas existan
    cuentas_faltantes = [nombre for nombre, cuenta in cuentas_necesarias.items() if not cuenta]
    if cuentas_faltantes:
        print(f"⚠ Cuentas no encontradas: {', '.join(cuentas_faltantes)}")
        print("⚠ Usando cuentas disponibles...")
    
    asientos_creados = 0
    
    # ========================================
    # ASIENTO 1: Apertura de Caja
    # ========================================
    if cuentas_necesarias['caja'] and cuentas_necesarias['banco']:
        try:
            asiento1 = AsientoContable.objects.create(
                numero_asiento='ASI-2026-001',
                fecha_asiento=date(2026, 1, 2),
                tipo_asiento='APERTURA',
                concepto='Asiento de apertura - Saldo inicial de caja y banco',
                estado='BORRADOR',
                creado_por=usuario
            )
            
            # Débito en Caja
            DetalleAsiento.objects.create(
                asiento=asiento1,
                linea=1,
                cuenta=cuentas_necesarias['caja'],
                descripcion='Saldo inicial en caja',
                debito=Decimal('5000000.00'),
                credito=Decimal('0.00')
            )
            
            # Débito en Banco
            DetalleAsiento.objects.create(
                asiento=asiento1,
                linea=2,
                cuenta=cuentas_necesarias['banco'],
                descripcion='Saldo inicial en banco',
                debito=Decimal('25000000.00'),
                credito=Decimal('0.00')
            )
            
            # Crédito en Capital (usar la primera cuenta de capital disponible)
            cuenta_capital = PlanCuentas.objects.filter(
                tipo_cuenta='CAPITAL',
                es_detalle=True,
                activo=True
            ).first()
            
            if cuenta_capital:
                DetalleAsiento.objects.create(
                    asiento=asiento1,
                    linea=3,
                    cuenta=cuenta_capital,
                    descripcion='Capital inicial',
                    debito=Decimal('0.00'),
                    credito=Decimal('30000000.00')
                )
                
                # Calcular totales
                asiento1.calcular_totales()
                asiento1.save()
                
                print(f"✓ Asiento {asiento1.numero_asiento} creado - {asiento1.concepto}")
                asientos_creados += 1
            else:
                print("⚠ No se encontró cuenta de capital, asiento 1 no creado")
                asiento1.delete()
        except Exception as e:
            print(f"❌ Error al crear asiento 1: {e}")
    
    # ========================================
    # ASIENTO 2: Ingreso por Matrículas
    # ========================================
    if cuentas_necesarias['caja'] and cuentas_necesarias['ingreso_matriculas']:
        try:
            asiento2 = AsientoContable.objects.create(
                numero_asiento='ASI-2026-002',
                fecha_asiento=date(2026, 1, 15),
                tipo_asiento='DIARIO',
                concepto='Cobro de matrículas del mes de enero',
                referencia='FACTURA-001 a FACTURA-020',
                estado='BORRADOR',
                creado_por=usuario
            )
            
            # Débito en Caja
            DetalleAsiento.objects.create(
                asiento=asiento2,
                linea=1,
                cuenta=cuentas_necesarias['caja'],
                descripcion='Cobro de matrículas - 20 estudiantes @ Gs. 250.000',
                debito=Decimal('5000000.00'),
                credito=Decimal('0.00')
            )
            
            # Crédito en Ingreso por Matrículas
            DetalleAsiento.objects.create(
                asiento=asiento2,
                linea=2,
                cuenta=cuentas_necesarias['ingreso_matriculas'],
                descripcion='Ingresos por matrículas enero 2026',
                debito=Decimal('0.00'),
                credito=Decimal('5000000.00')
            )
            
            # Calcular totales
            asiento2.calcular_totales()
            asiento2.save()
            
            print(f"✓ Asiento {asiento2.numero_asiento} creado - {asiento2.concepto}")
            asientos_creados += 1
        except Exception as e:
            print(f"❌ Error al crear asiento 2: {e}")
    
    # ========================================
    # ASIENTO 3: Ingreso por Mensualidades
    # ========================================
    if cuentas_necesarias['banco'] and cuentas_necesarias['ingreso_mensualidades']:
        try:
            asiento3 = AsientoContable.objects.create(
                numero_asiento='ASI-2026-003',
                fecha_asiento=date(2026, 1, 20),
                tipo_asiento='DIARIO',
                concepto='  mensualidades mes de enero',
                referencia='RECIBOS-101 a RECIBOS-150',
                estado='BORRADOR',
                creado_por=usuario
            )
            
            # Débito en Banco
            DetalleAsiento.objects.create(
                asiento=asiento3,
                linea=1,
                cuenta=cuentas_necesarias['banco'],
                descripcion='Transferencias por mensualidades - 50 estudiantes @ Gs. 400.000',
                debito=Decimal('20000000.00'),
                credito=Decimal('0.00')
            )
            
            # Crédito en Ingreso por Mensualidades
            DetalleAsiento.objects.create(
                asiento=asiento3,
                linea=2,
                cuenta=cuentas_necesarias['ingreso_mensualidades'],
                descripcion='Ingresos por mensualidades enero 2026',
                debito=Decimal('0.00'),
                credito=Decimal('20000000.00')
            )
            
            # Calcular totales
            asiento3.calcular_totales()
            asiento3.save()
            
            print(f"✓ Asiento {asiento3.numero_asiento} creado - {asiento3.concepto}")
            asientos_creados += 1
        except Exception as e:
            print(f"❌ Error al crear asiento 3: {e}")
    
    # ========================================
    # ASIENTO 4: Pago de Salarios
    # ========================================
    if cuentas_necesarias['banco'] and cuentas_necesarias['gasto_salarios']:
        try:
            asiento4 = AsientoContable.objects.create(
                numero_asiento='ASI-2026-004',
                fecha_asiento=date(2026, 1, 31),
                tipo_asiento='DIARIO',
                concepto='Pago de salarios del personal docente y administrativo',
                referencia='PLANILLA-ENE-2026',
                estado='BORRADOR',
                creado_por=usuario
            )
            
            # Débito en Gasto Salarios
            DetalleAsiento.objects.create(
                asiento=asiento4,
                linea=1,
                cuenta=cuentas_necesarias['gasto_salarios'],
                descripcion='Salarios personal enero 2026',
                debito=Decimal('15000000.00'),
                credito=Decimal('0.00')
            )
            
            # Crédito en Banco
            DetalleAsiento.objects.create(
                asiento=asiento4,
                linea=2,
                cuenta=cuentas_necesarias['banco'],
                descripcion='Transferencias bancarias por salarios',
                debito=Decimal('0.00'),
                credito=Decimal('15000000.00')
            )
            
            # Calcular totales
            asiento4.calcular_totales()
            asiento4.save()
            
            print(f"✓ Asiento {asiento4.numero_asiento} creado - {asiento4.concepto}")
            asientos_creados += 1
        except Exception as e:
            print(f"❌ Error al crear asiento 4: {e}")
    
    # ========================================
    # ASIENTO 5: Pago de Servicios
    # ========================================
    if cuentas_necesarias['caja'] and cuentas_necesarias['gasto_servicios']:
        try:
            asiento5 = AsientoContable.objects.create(
                numero_asiento='ASI-2026-005',
                fecha_asiento=date(2026, 1, 31),
                tipo_asiento='DIARIO',
                concepto='Pago de servicios públicos (agua, luz, internet)',
                referencia='FACTURAS-SERVICIOS-ENE',
                estado='BORRADOR',
                creado_por=usuario
            )
            
            # Débito en Gasto Servicios
            DetalleAsiento.objects.create(
                asiento=asiento5,
                linea=1,
                cuenta=cuentas_necesarias['gasto_servicios'],
                descripcion='Servicios públicos enero 2026',
                debito=Decimal('1500000.00'),
                credito=Decimal('0.00')
            )
            
            # Crédito en Caja
            DetalleAsiento.objects.create(
                asiento=asiento5,
                linea=2,
                cuenta=cuentas_necesarias['caja'],
                descripcion='Pago en efectivo servicios',
                debito=Decimal('0.00'),
                credito=Decimal('1500000.00')
            )
            
            # Calcular totales
            asiento5.calcular_totales()
            asiento5.save()
            
            print(f"✓ Asiento {asiento5.numero_asiento} creado - {asiento5.concepto}")
            asientos_creados += 1
        except Exception as e:
            print(f"❌ Error al crear asiento 5: {e}")
    
    print("\n" + "=" * 80)
    print(f"RESUMEN: {asientos_creados} asientos de ejemplo creados exitosamente")
    print("=" * 80)
    print("\n📋 Nota: Todos los asientos están en estado BORRADOR.")
    print("   Puede contabilizarlos desde la interfaz web o con el siguiente comando:\n")
    print("   from escuelaweb.models import AsientoContable")
    print("   asiento = AsientoContable.objects.get(numero_asiento='ASI-2026-001')")
    print("   asiento.contabilizar(usuario)")
    print("\n")

# Ejecutar la función automáticamente
cargar_asientos_ejemplo()
