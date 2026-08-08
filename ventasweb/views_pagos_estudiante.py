# views_pagos_estudiante.py
# Sistema de Pagos para Estudiantes
# Vistas para permitir que los estudiantes paguen sus facturas online

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    Factura, PagoFactura, CustomUser, AnhoEscolar, 
    Matricula, ConceptoPago, TarifaEstudiante, DetalleFactura, Articulo
)


@login_required
def estudiante_pagos(request):
    """
    Vista principal del sistema de pagos para estudiantes.
    Genera automáticamente facturas mensuales si no existen.
    Muestra TODAS las facturas del año (pendientes y vencidas) con moras calculadas automáticamente.
    """
    # Verificar que el usuario sea estudiante
    if request.user.rol != 'Estudiante':
        messages.error(request, 'Esta sección es solo para estudiantes.')
        return redirect('plataform')
    
    # Obtener año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo.')
        return redirect('plataform')
    
    # Verificar si el estudiante está matriculado en el año escolar activo
    # (tiene al menos una matrícula en alguna materia)
    tiene_matricula = Matricula.objects.filter(
        estudiante=request.user,
        anho_escolar=anho_escolar
    ).exists()
    
    if not tiene_matricula:
        messages.warning(request, 'No estás matriculado en el año escolar activo.')
        return redirect('plataform')
    
    # GENERAR FACTURAS MENSUALES AUTOMÁTICAMENTE SI NO EXISTEN
    facturas_generadas = generar_facturas_mensuales_estudiante(request.user, anho_escolar)
    
    # Mensaje informativo si se generaron facturas
    if facturas_generadas > 0:
        messages.success(request, f'Se generaron automáticamente {facturas_generadas} facturas mensuales para el año escolar.')
    
    # Obtener TODAS las facturas del estudiante para el año escolar (pendientes y vencidas)
    facturas_pendientes = Factura.objects.filter(
        cliente=request.user,
        anho_escolar=anho_escolar,
        estado__in=['pendiente', 'parcial', 'vencida']
    ).order_by('fecha_vencimiento')
    
    # Mensaje de advertencia si no hay facturas
    if not facturas_pendientes.exists():
        messages.warning(request, 
            'No se pudieron generar facturas mensuales. '
            'Verifica que exista un artículo llamado "Mensualidad" en el sistema. '
            'Contacta con administración si el problema persiste.')
    
    # Calcular moras automáticamente para facturas vencidas
    hoy = timezone.now().date()
    facturas_con_detalle = []
    
    for factura in facturas_pendientes:
        mora_aplicada = Decimal('0.00')
        descuento_aplicado = factura.descuento
        estado_pago = 'Pendiente'
        
        # Verificar si está vencida
        if factura.fecha_vencimiento and factura.fecha_vencimiento < hoy and factura.estado != 'pagada':
            estado_pago = 'Vencida'
            dias_vencidos = (hoy - factura.fecha_vencimiento).days
            
            # Calcular mora - 2% por cada 15 días, máximo 50%
            periodos_mora = (dias_vencidos // 15) + 1
            porcentaje_mora = min(periodos_mora * 2, 50)  # Máximo 50%
            mora_aplicada = (factura.subtotal * Decimal(str(porcentaje_mora)) / Decimal('100'))
        
        # Obtener concepto y descripción específica del mes desde los detalles
        try:
            primer_detalle = DetalleFactura.objects.filter(factura=factura).first()
            # Usar la descripción específica que incluye el mes (ej: "Mensualidad Enero 2026")
            concepto_nombre = primer_detalle.descripcion if primer_detalle and primer_detalle.descripcion else (primer_detalle.articulo.nombre if primer_detalle and hasattr(primer_detalle, 'articulo') else 'Varios')
        except:
            concepto_nombre = 'Varios'
        
        # Agregar información calculada a la factura
        factura.mora_aplicada = mora_aplicada
        factura.descuento_aplicado = descuento_aplicado
        factura.estado_pago = estado_pago
        factura.concepto = type('obj', (object,), {'nombre': concepto_nombre})()
        factura.total_con_mora = factura.total + mora_aplicada
        
        facturas_con_detalle.append(factura)
    
    # Calcular resúmenes
    total_pendiente = sum(f.total_con_mora - f.monto_pagado for f in facturas_con_detalle)
    total_mora = sum(f.mora_aplicada for f in facturas_con_detalle)
    total_descuento = sum(f.descuento_aplicado for f in facturas_con_detalle)
    
    # Contar meses del año (facturas pendientes)
    total_ano_meses = len(facturas_con_detalle)
    
    context = {
        'anho_escolar': anho_escolar,
        'facturas_pendientes': facturas_con_detalle,
        'total_pendiente': total_pendiente,
        'total_mora': total_mora,
        'total_descuento': total_descuento,
        'total_ano_meses': total_ano_meses,  # Nuevo: para el botón "Pagar Año Completo"
    }
    
    return render(request, 'cobros/estudiante_pagos.html', context)


def generar_facturas_mensuales_estudiante(estudiante, anho_escolar):
    """
    Genera automáticamente facturas mensuales para un estudiante en el año escolar activo.
    Crea una factura por cada mes entre la fecha de inicio y fin del año escolar.
    """
    import calendar
    
    # Obtener artículo de mensualidad
    try:
        # Buscar primero sin filtro activo para debug
        todos_articulos = Articulo.objects.filter(nombre__icontains='mensualidad')
        print(f"🔍 DEBUG: Total artículos con 'mensualidad': {todos_articulos.count()}")
        for art in todos_articulos:
            print(f"   - ID:{art.id} '{art.nombre}' Activo:{art.activo}")
        
        articulo_mensualidad = Articulo.objects.filter(
            nombre__icontains='mensualidad',
            activo=True
        ).first()
        
        if not articulo_mensualidad:
            print(f"❌ No se encontró artículo con 'mensualidad' ACTIVO para {estudiante.get_full_name()}")
            return 0  # No hay artículo de mensualidad configurado
        else:
            print(f"✅ Artículo encontrado: {articulo_mensualidad.nombre} (ID:{articulo_mensualidad.id}) - Precio: {articulo_mensualidad.precio_venta}")
    except Exception as e:
        print(f"❌ Error buscando artículo: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0
    
    # Obtener tarifa del estudiante o usar precio por defecto
    try:
        tarifa = TarifaEstudiante.objects.filter(
            estudiante=estudiante,
            activo=True
        ).first()
        monto = tarifa.monto if tarifa else articulo_mensualidad.precio_venta
    except:
        monto = articulo_mensualidad.precio_venta
    
    # Obtener día de vencimiento (del estudiante o por defecto día 10)
    try:
        if tarifa and tarifa.dia_vencimiento:
            dia_vencimiento = tarifa.dia_vencimiento
        elif hasattr(estudiante, 'grupo_familiar') and estudiante.grupo_familiar and hasattr(estudiante.grupo_familiar, 'dia_vencimiento'):
            dia_vencimiento = estudiante.grupo_familiar.dia_vencimiento
        else:
            dia_vencimiento = 10
    except:
        dia_vencimiento = 10
    
    # Calcular meses del año escolar
    fecha_inicio = anho_escolar.fecha_inicio
    fecha_fin = anho_escolar.fecha_fin
    meses_generados = 0
    
    # Nombre de meses en español
    nombres_meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Generar lista de meses entre fecha_inicio y fecha_fin
    ano_actual = fecha_inicio.year
    mes_actual = fecha_inicio.month
    
    while (ano_actual < fecha_fin.year) or (ano_actual == fecha_fin.year and mes_actual <= fecha_fin.month):
        # Crear fecha para el primer día del mes actual
        primer_dia_mes = datetime(ano_actual, mes_actual, 1).date()
        
        # VERIFICACIÓN MEJORADA: Buscar factura por mes/año en DetalleFactura
        # Primero buscar por DetalleFactura con mes y año específicos
        factura_existe_detalle = DetalleFactura.objects.filter(
            factura__cliente=estudiante,
            factura__anho_escolar=anho_escolar,
            mes=mes_actual,
            anio=ano_actual
        ).exists()
        
        # También verificar por fecha de emisión (por si hay facturas antiguas sin mes/año)
        factura_existe_fecha = Factura.objects.filter(
            cliente=estudiante,
            anho_escolar=anho_escolar,
            fecha_emision__year=ano_actual,
            fecha_emision__month=mes_actual
        ).exists()
        
        if factura_existe_detalle or factura_existe_fecha:
            # Ya existe una factura para este mes, saltar
            pass
        else:
            # Crear fecha de vencimiento (día X del mes actual)
            try:
                ultimo_dia_mes = calendar.monthrange(ano_actual, mes_actual)[1]
                dia_venc = min(dia_vencimiento, ultimo_dia_mes)
                fecha_vencimiento = datetime(ano_actual, mes_actual, dia_venc).date()
            except ValueError:
                fecha_vencimiento = primer_dia_mes
            
            # Generar número de factura único
            numero_factura = f"FACT-{ano_actual}{mes_actual:02d}-{estudiante.id:05d}"
            
            # Verificar que el número no exista (por si acaso)
            contador = 1
            numero_original = numero_factura
            while Factura.objects.filter(numero_factura=numero_factura).exists():
                numero_factura = f"{numero_original}-{contador}"
                contador += 1
            
            try:
                # Crear factura
                factura = Factura.objects.create(
                    numero_factura=numero_factura,
                    cliente=estudiante,
                    anho_escolar=anho_escolar,
                    fecha_vencimiento=fecha_vencimiento,
                    subtotal=monto,
                    total=monto,
                    estado='pendiente',
                    observaciones=f'Mensualidad de {nombres_meses[mes_actual]} {ano_actual}'
                )
                
                # Crear detalle de factura
                mes_nombre = nombres_meses[mes_actual]
                DetalleFactura.objects.create(
                    factura=factura,
                    articulo=articulo_mensualidad,
                    descripcion=f'Mensualidad {mes_nombre} {ano_actual}',
                    cantidad=1,
                    precio_unitario=monto,
                    mes=mes_actual,  # Mes específico (1-12)
                    anio=ano_actual  # Año específico
                )
                
                meses_generados += 1
                print(f"✅ Factura creada: {factura.numero_factura} - {mes_nombre} {ano_actual}")
            except Exception as e:
                print(f"❌ Error generando factura para {estudiante.get_full_name()}, mes {mes_actual}/{ano_actual}: {str(e)}")
        
        # Avanzar al siguiente mes
        mes_actual += 1
        if mes_actual > 12:
            mes_actual = 1
            ano_actual += 1
    
    return meses_generados


@login_required
@login_required
def procesar_pago_estudiante(request):
    """
    Procesa el pago de una o múltiples facturas mediante tarjeta de crédito.
    Soporta pago individual, pago de facturas seleccionadas, y pago del año completo.
    En un entorno de producción, aquí se integraría con una pasarela de pago real.
    """
    if request.method != 'POST':
        return redirect('estudiante_pagos')
    
    # Verificar que el usuario sea estudiante
    if request.user.rol != 'Estudiante':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('plataform')
    
    # Obtener IDs de facturas (pueden ser múltiples separadas por coma)
    facturas_ids_str = request.POST.get('facturas_ids', '')
    numero_tarjeta = request.POST.get('numero_tarjeta')
    nombre_titular = request.POST.get('nombre_titular')
    tipo_tarjeta = request.POST.get('tipo_tarjeta')
    fecha_expiracion = request.POST.get('fecha_expiracion')
    cvv = request.POST.get('cvv')
    
    # Validar campos requeridos
    if not all([facturas_ids_str, numero_tarjeta, nombre_titular, tipo_tarjeta, fecha_expiracion, cvv]):
        messages.error(request, 'Por favor completa todos los campos del formulario.')
        return redirect('estudiante_pagos')
    
    # Convertir IDs de facturas a lista
    try:
        facturas_ids = [int(id.strip()) for id in facturas_ids_str.split(',') if id.strip()]
    except ValueError:
        messages.error(request, 'IDs de facturas inválidos.')
        return redirect('estudiante_pagos')
    
    if not facturas_ids:
        messages.error(request, 'No se especificaron facturas para pagar.')
        return redirect('estudiante_pagos')
    
    # Obtener facturas
    facturas = Factura.objects.filter(
        id__in=facturas_ids,
        cliente=request.user,
        estado__in=['pendiente', 'parcial', 'vencida']
    )
    
    if not facturas.exists():
        messages.error(request, 'No se encontraron facturas válidas para pagar.')
        return redirect('estudiante_pagos')
    
    # Calcular monto total a pagar (incluyendo moras)
    hoy = timezone.now().date()
    monto_total_pagar = Decimal('0.00')
    facturas_procesadas = []
    
    for factura in facturas:
        # Calcular mora si está vencida
        mora_aplicada = Decimal('0.00')
        if factura.fecha_vencimiento and factura.fecha_vencimiento < hoy:
            dias_vencidos = (hoy - factura.fecha_vencimiento).days
            periodos_mora = (dias_vencidos // 15) + 1
            porcentaje_mora = min(periodos_mora * 2, 50)
            mora_aplicada = (factura.subtotal * Decimal(str(porcentaje_mora)) / Decimal('100'))
        
        # Calcular monto pendiente
        total_con_mora = factura.total + mora_aplicada
        monto_pendiente = total_con_mora - factura.monto_pagado
        
        facturas_procesadas.append({
            'factura': factura,
            'mora_aplicada': mora_aplicada,
            'total_con_mora': total_con_mora,
            'monto_pendiente': monto_pendiente
        })
        
        monto_total_pagar += monto_pendiente
    
    # SIMULACIÓN DE PAGO CON TARJETA
    # En producción, aquí iría la integración con la pasarela de pago real
    # (Stripe, PayPal, Cardnet, Azul, etc.)
    
    try:
        # Simular procesamiento de pago
        # En producción: procesar con API de pasarela
        pago_exitoso = True  # Simulación
        
        if pago_exitoso:
            facturas_pagadas = []
            referencia_global = f"CARD-{tipo_tarjeta.upper()}-{numero_tarjeta[-4:]}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Procesar cada factura
            for item in facturas_procesadas:
                factura = item['factura']
                mora_aplicada = item['mora_aplicada']
                total_con_mora = item['total_con_mora']
                monto_pendiente = item['monto_pendiente']
                
                # Actualizar el total de la factura si hay mora
                if mora_aplicada > 0:
                    factura.total = total_con_mora
                    factura.observaciones = (factura.observaciones or '') + f'\nMora aplicada: RD$ {mora_aplicada:.2f}'
                
                # Crear registro de pago usando PagoFactura
                pago = PagoFactura.objects.create(
                    factura=factura,
                    monto=monto_pendiente,
                    metodo_pago='tarjeta',
                    referencia=referencia_global,
                    observaciones=f"Pago online con tarjeta {tipo_tarjeta} terminada en {numero_tarjeta[-4:]}. Titular: {nombre_titular}",
                    registrado_por=request.user
                )
                
                # Actualizar factura
                factura.monto_pagado += monto_pendiente
                factura.metodo_pago = 'tarjeta'
                
                if factura.monto_pagado >= factura.total:
                    factura.estado = 'pagada'
                    factura.fecha_pago_completo = timezone.now()
                else:
                    factura.estado = 'parcial'
                
                factura.save()
                facturas_pagadas.append(factura.numero_factura)
            
            # Mensaje de éxito
            num_facturas = len(facturas_pagadas)
            if num_facturas == 1:
                mensaje = f'¡Pago procesado exitosamente! Factura {facturas_pagadas[0]} pagada por RD$ {monto_total_pagar:.2f}.'
            else:
                mensaje = f'¡Pago procesado exitosamente! {num_facturas} facturas pagadas por un total de RD$ {monto_total_pagar:.2f}.'
            
            mensaje += f' Referencia: {referencia_global}'
            messages.success(request, mensaje)
        else:
            messages.error(request, 'Error al procesar el pago. Por favor intenta nuevamente.')
            
    except Exception as e:
        messages.error(request, f'Error al procesar el pago: {str(e)}')
    
    return redirect('estudiante_pagos')


@login_required
def generar_facturas_mensuales_automatico(request):
    """
    Función auxiliar para generar facturas mensuales automáticamente.
    Esta función puede ser llamada por un cron job o tarea programada.
    """
    if request.user.rol not in ['Administrador', 'Secretaria']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('plataform')
    
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo.')
        return redirect('cobros_dashboard')
    
    # Obtener todas las matrículas del año escolar activo
    # Obtener lista única de estudiantes matriculados (pueden tener múltiples materias)
    estudiantes_matriculados = CustomUser.objects.filter(
        matriculas__anho_escolar=anho_escolar,
        rol='Estudiante'
    ).distinct()
    
    # Obtener el concepto de mensualidad
    try:
        articulo_mensualidad = Articulo.objects.filter(
            nombre__icontains='mensualidad',
            activo=True
        ).first()
        
        if not articulo_mensualidad:
            messages.error(request, 'No se encontró el artículo de mensualidad.')
            return redirect('cobros_dashboard')
    except Exception as e:
        messages.error(request, f'Error al buscar artículo de mensualidad: {str(e)}')
        return redirect('cobros_dashboard')
    
    # Fecha de emisión y vencimiento
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    # Vencimiento: día 10 del mes actual
    dia_vencimiento = 10
    try:
        fecha_vencimiento = hoy.replace(day=dia_vencimiento)
    except:
        fecha_vencimiento = hoy.replace(day=28)  # Por si el mes no tiene 10 días
    
    facturas_creadas = 0
    
    for estudiante in estudiantes_matriculados:
        # Verificar si ya existe una factura para este mes
        factura_existe = Factura.objects.filter(
            cliente=estudiante,
            fecha_emision__year=hoy.year,
            fecha_emision__month=hoy.month,
            anho_escolar=anho_escolar
        ).exists()
        
        if not factura_existe:
            # Obtener tarifa del estudiante  
            try:
                tarifa = TarifaEstudiante.objects.filter(
                    estudiante=estudiante,
                    activo=True
                ).first()
                monto = tarifa.monto if tarifa else articulo_mensualidad.precio_venta
            except Exception:
                monto = articulo_mensualidad.precio_venta
            
            # Crear factura
            numero_factura = f"FACT-{hoy.year}{hoy.month:02d}-{estudiante.id:05d}"
            
            try:
                factura = Factura.objects.create(
                    numero_factura=numero_factura,
                    cliente=estudiante,
                    anho_escolar=anho_escolar,
                    fecha_vencimiento=fecha_vencimiento,
                    subtotal=monto,
                    total=monto,
                    estado='pendiente',
                    creado_por=request.user
                )
                
                # Crear detalle de factura
                DetalleFactura.objects.create(
                    factura=factura,
                    articulo=articulo_mensualidad,
                    descripcion=f"Mensualidad {hoy.strftime('%B %Y')}",
                    cantidad=1,
                    precio_unitario=monto,
                    subtotal=monto
                )
                
                facturas_creadas += 1
            except Exception as e:
                print(f"Error creando factura para {estudiante.get_full_name()}: {str(e)}")
    
    messages.success(
        request,
        f'Se generaron {facturas_creadas} facturas mensuales automáticamente.'
    )
    
    return redirect('cobros_dashboard')
