"""
Vistas para la gestión de grupos familiares
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from decimal import Decimal
from datetime import date
from calendar import monthrange

from .models import CustomUser, GrupoFamiliar, Factura, DetalleFactura, ConceptoPago, AnhoEscolar, TarifaEstudiante
import random


def generar_codigo_familia():
    """
    Genera un código único de familia con formato FA + 6 dígitos aleatorios
    Ej: FA123456, FA987654, etc.
    Los números son aleatorios entre 100000 y 999999
    """
    max_intentos = 100  # Prevenir loop infinito en caso improbable
    
    for _ in range(max_intentos):
        # Generar número aleatorio de 6 dígitos (100000-999999)
        numero_aleatorio = random.randint(100000, 999999)
        codigo = f"FA{numero_aleatorio}"
        
        # Verificar que no exista
        if not GrupoFamiliar.objects.filter(codigo_familia=codigo).exists():
            return codigo
    
    # En el caso extremadamente improbable de que no se encuentre un código único
    # después de 100 intentos, usar timestamp
    import time
    timestamp = int(time.time()) % 1000000
    return f"FA{timestamp:06d}"


@login_required
def grupos_familiares_lista(request):
    """Lista todos los grupos familiares"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener búsqueda
    buscar = request.GET.get('buscar', '')
    estado = request.GET.get('estado', '')
    
    # Consulta base
    grupos = GrupoFamiliar.objects.annotate(
        num_estudiantes=Count('estudiantes', filter=Q(estudiantes__rol='Estudiante', estudiantes__is_active=True))
    )
    
    # Aplicar filtros
    if buscar:
        grupos = grupos.filter(
            Q(codigo_familia__icontains=buscar) |
            Q(apellido_familia__icontains=buscar) |
            Q(responsable_pago__first_name__icontains=buscar) |
            Q(responsable_pago__last_name__icontains=buscar)
        )
    
    if estado == 'activo':
        grupos = grupos.filter(activo=True)
    elif estado == 'inactivo':
        grupos = grupos.filter(activo=False)
    
    grupos = grupos.order_by('apellido_familia')
    
    context = {
        'grupos': grupos,
        'buscar': buscar,
        'estado': estado,
    }
    
    return render(request, 'familias/grupos_lista.html', context)


@login_required
def grupo_familiar_crear(request):
    """Crear un nuevo grupo familiar"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            codigo_familia = request.POST.get('codigo_familia', '').strip().upper()
            
            # Si no se proporciona código o está vacío, generar uno automáticamente
            if not codigo_familia:
                codigo_familia = generar_codigo_familia()
            
            apellido_familia = request.POST.get('apellido_familia').strip()
            telefono_contacto = request.POST.get('telefono_contacto', '').strip()
            email_contacto = request.POST.get('email_contacto', '').strip()
            direccion = request.POST.get('direccion', '').strip()
            descuento_general = request.POST.get('descuento_general', 0)
            porcentaje_mora = request.POST.get('porcentaje_mora', 0)
            dia_vencimiento = request.POST.get('dia_vencimiento', 10)
            notas = request.POST.get('notas', '').strip()
            activo = request.POST.get('activo') == 'on'
            
            # Validar código único
            if GrupoFamiliar.objects.filter(codigo_familia=codigo_familia).exists():
                messages.error(request, f'Ya existe un grupo familiar con el código {codigo_familia}')
                return redirect('grupo_familiar_crear')
            
            # Crear grupo familiar
            grupo = GrupoFamiliar.objects.create(
                codigo_familia=codigo_familia,
                apellido_familia=apellido_familia,
                telefono_contacto=telefono_contacto or None,
                email_contacto=email_contacto or None,
                direccion=direccion or None,
                descuento_general=descuento_general or 0,
                porcentaje_mora=porcentaje_mora or 0,
                dia_vencimiento=dia_vencimiento or 10,
                notas=notas or None,
                activo=activo,
                creado_por=request.user
            )
            
            messages.success(request, f'Grupo familiar {grupo.apellido_familia} creado exitosamente con código {codigo_familia}.')
            return redirect('grupo_familiar_detalle', grupo_id=grupo.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear grupo familiar: {str(e)}')
            return redirect('grupo_familiar_crear')
    
    # GET - Generar código automáticamente para mostrar en el formulario
    codigo_sugerido = generar_codigo_familia()
    return render(request, 'familias/grupo_crear.html', {
        'codigo_sugerido': codigo_sugerido
    })


@login_required
def grupo_familiar_editar(request, grupo_id):
    """Editar un grupo familiar existente"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    grupo = get_object_or_404(GrupoFamiliar, id=grupo_id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos
            nuevo_codigo = request.POST.get('codigo_familia').strip().upper()
            
            # Validar código único si cambió
            if nuevo_codigo != grupo.codigo_familia:
                if GrupoFamiliar.objects.filter(codigo_familia=nuevo_codigo).exists():
                    messages.error(request, f'Ya existe un grupo familiar con el código {nuevo_codigo}')
                    return redirect('grupo_familiar_editar', grupo_id=grupo_id)
                grupo.codigo_familia = nuevo_codigo
            
            grupo.apellido_familia = request.POST.get('apellido_familia').strip()
            grupo.telefono_contacto = request.POST.get('telefono_contacto', '').strip() or None
            grupo.email_contacto = request.POST.get('email_contacto', '').strip() or None
            grupo.direccion = request.POST.get('direccion', '').strip() or None
            grupo.descuento_general = request.POST.get('descuento_general', 0) or 0
            grupo.porcentaje_mora = request.POST.get('porcentaje_mora', 0) or 0
            grupo.dia_vencimiento = request.POST.get('dia_vencimiento', 10) or 10
            grupo.notas = request.POST.get('notas', '').strip() or None
            grupo.activo = request.POST.get('activo') == 'on'
            
            grupo.save()
            
            messages.success(request, f'Grupo familiar {grupo.apellido_familia} actualizado exitosamente.')
            return redirect('grupo_familiar_detalle', grupo_id=grupo.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar grupo familiar: {str(e)}')
            return redirect('grupo_familiar_editar', grupo_id=grupo_id)
    
    context = {
        'grupo': grupo,
    }
    
    return render(request, 'familias/grupo_editar.html', context)


@login_required
def grupo_familiar_detalle(request, grupo_id):
    """Ver detalles de un grupo familiar y sus estudiantes"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    grupo = get_object_or_404(GrupoFamiliar, id=grupo_id)
    estudiantes = grupo.get_estudiantes_activos().order_by('last_name', 'first_name')
    
    # Calcular totales de mensualidades y agregar info de tarifa a cada estudiante
    total_mensualidades = Decimal('0.00')
    estudiantes_con_tarifa = []
    
    for estudiante in estudiantes:
        # Obtener tarifa de mensualidad del estudiante
        tarifa = TarifaEstudiante.objects.filter(
            estudiante=estudiante,
            concepto__tipo='mensualidad',
            activo=True
        ).first()
        
        if tarifa and tarifa.monto:
            total_mensualidades += tarifa.monto
            estudiante.tarifa_actual = tarifa
            estudiante.tiene_tarifa = True
        else:
            estudiante.tarifa_actual = None
            estudiante.tiene_tarifa = False
        
        estudiantes_con_tarifa.append(estudiante)
    
    # Aplicar descuento si existe
    total_con_descuento = total_mensualidades
    if grupo.descuento_general > 0:
        descuento = total_mensualidades * (grupo.descuento_general / 100)
        total_con_descuento = total_mensualidades - descuento
    
    context = {
        'grupo': grupo,
        'estudiantes': estudiantes_con_tarifa,
        'total_mensualidades': total_mensualidades,
        'total_con_descuento': total_con_descuento,
        'descuento_aplicado': total_mensualidades - total_con_descuento if grupo.descuento_general > 0 else 0,
    }
    
    return render(request, 'familias/grupo_detalle.html', context)


@login_required
def grupo_familiar_asignar_estudiante(request, grupo_id):
    """Asignar estudiantes a un grupo familiar"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    grupo = get_object_or_404(GrupoFamiliar, id=grupo_id)
    
    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        
        try:
            estudiante = CustomUser.objects.get(id=estudiante_id, rol='Estudiante')
            
            # Verificar si ya está en otro grupo
            if estudiante.grupo_familiar and estudiante.grupo_familiar != grupo:
                messages.warning(
                    request, 
                    f'{estudiante.get_full_name()} ya pertenece al grupo {estudiante.grupo_familiar.apellido_familia}. Se reasignará.'
                )
            
            estudiante.grupo_familiar = grupo
            estudiante.save()
            
            messages.success(request, f'{estudiante.get_full_name()} asignado al grupo {grupo.apellido_familia}.')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Estudiante no encontrado.')
        except Exception as e:
            messages.error(request, f'Error al asignar estudiante: {str(e)}')
        
        return redirect('grupo_familiar_detalle', grupo_id=grupo_id)
    
    # Búsqueda de estudiantes
    buscar = request.GET.get('buscar', '')
    estudiantes = CustomUser.objects.filter(rol='Estudiante', is_active=True)
    
    if buscar:
        estudiantes = estudiantes.filter(
            Q(first_name__icontains=buscar) |
            Q(last_name__icontains=buscar) |
            Q(codigo_barras__icontains=buscar) |
            Q(cedula__icontains=buscar)
        )
    
    estudiantes = estudiantes.order_by('last_name', 'first_name')[:50]  # Limitar resultados
    
    context = {
        'grupo': grupo,
        'estudiantes': estudiantes,
        'buscar': buscar,
    }
    
    return render(request, 'familias/grupo_asignar_estudiante.html', context)


@login_required
def grupo_familiar_remover_estudiante(request, grupo_id, estudiante_id):
    """Remover un estudiante de un grupo familiar"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('plataform')
    
    grupo = get_object_or_404(GrupoFamiliar, id=grupo_id)
    estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
    
    if estudiante.grupo_familiar == grupo:
        estudiante.grupo_familiar = None
        estudiante.save()
        messages.success(request, f'{estudiante.get_full_name()} removido del grupo familiar.')
    else:
        messages.error(request, 'El estudiante no pertenece a este grupo familiar.')
    
    return redirect('grupo_familiar_detalle', grupo_id=grupo_id)


@login_required
def grupo_familiar_facturar(request, grupo_id):
    """Facturar mensualidades de toda la familia"""
    if request.user.rol not in ['Secretaria', 'Administrador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    from django.utils import timezone
    from datetime import datetime
    import json
    
    grupo = get_object_or_404(GrupoFamiliar, id=grupo_id)
    estudiantes = grupo.get_estudiantes_activos().order_by('last_name', 'first_name')
    
    # Obtener año escolar activo
    try:
        anho_escolar = AnhoEscolar.objects.get(activo=True)
    except AnhoEscolar.DoesNotExist:
        messages.error(request, 'No hay un año escolar activo.')
        return redirect('grupo_familiar_detalle', grupo_id=grupo_id)
    
    # Obtener concepto de mensualidad
    try:
        concepto_mensualidad = ConceptoPago.objects.filter(tipo='mensualidad').first()
        if not concepto_mensualidad:
            messages.error(request, 'No existe un concepto de mensualidad configurado.')
            return redirect('grupo_familiar_detalle', grupo_id=grupo_id)
    except:
        messages.error(request, 'Error al obtener concepto de mensualidad.')
        return redirect('grupo_familiar_detalle', grupo_id=grupo_id)
    
    if request.method == 'POST':
        try:
            meses_seleccionados = request.POST.getlist('meses')  # Lista de meses
            anio = int(request.POST.get('anio'))
            metodo_pago = request.POST.get('metodo_pago', 'efectivo')
            monto_pagado = Decimal(request.POST.get('monto_pagado', '0') or '0')
            observaciones = request.POST.get('observaciones', '')
            
            if not meses_seleccionados:
                messages.error(request, 'Debes seleccionar al menos un mes.')
                return redirect('grupo_familiar_facturar', grupo_id=grupo_id)
            
            # Obtener estudiantes seleccionados
            estudiantes_ids = request.POST.getlist('estudiantes')
            
            if not estudiantes_ids:
                messages.error(request, 'Debes seleccionar al menos un estudiante.')
                return redirect('grupo_familiar_facturar', grupo_id=grupo_id)
            
            # Crear una factura por cada estudiante
            facturas_creadas = []
            total_facturas = Decimal('0.00')  # Para calcular distribución proporcional del pago
            
            for est_id in estudiantes_ids:
                estudiante = CustomUser.objects.get(id=est_id, rol='Estudiante')
                
                # Obtener tarifa de mensualidad del estudiante
                tarifa = TarifaEstudiante.objects.filter(
                    estudiante=estudiante,
                    concepto__tipo='mensualidad',
                    activo=True
                ).first()
                
                if not tarifa or not tarifa.monto:
                    messages.warning(request, f'{estudiante.get_full_name()} no tiene tarifa de mensualidad configurada.')
                    continue
                
                # Obtener meses ya pagados por este estudiante en este año
                detalles_pagados = DetalleFactura.objects.filter(
                    factura__cliente=estudiante,
                    factura__anho_escolar=anho_escolar,
                    concepto__tipo='mensualidad',
                    mes__isnull=False,
                    anio=anio,  # Solo del año que se está facturando
                    factura__estado__in=['pagada', 'pendiente', 'parcial']  # Excluir anuladas
                ).values_list('mes', flat=True)
                
                meses_pagados_set = set(detalles_pagados)
                
                # Filtrar meses para facturar (solo los que NO están pagados)
                meses_a_facturar = [m for m in meses_seleccionados if int(m) not in meses_pagados_set]
                
                # Si todos los meses ya están pagados, omitir este estudiante
                if not meses_a_facturar:
                    messages.info(request, f'{estudiante.get_full_name()} ya tiene pagados todos los meses seleccionados.')
                    continue
                
                # Generar número de factura único
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                import random
                random_suffix = random.randint(1000, 9999)
                numero_factura = f"FAC-{timestamp}-{random_suffix}"
                
                # Determinar descripción de meses
                meses_nombres = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                meses_texto = ', '.join([meses_nombres[int(m)-1] for m in meses_a_facturar])
                
                # Crear factura (sin monto_pagado aún, se distribuirá después)
                factura = Factura.objects.create(
                    numero_factura=numero_factura,
                    cliente=estudiante,
                    anho_escolar=anho_escolar,
                    metodo_pago=metodo_pago,
                    monto_pagado=Decimal('0'),  # Se actualizará después
                    observaciones=f"{observaciones}\nGrupo Familiar: {grupo.apellido_familia} ({grupo.codigo_familia})\nMeses: {meses_texto} {anio}",
                    creado_por=request.user
                )
                
                # Crear un detalle por cada mes a facturar (excluyendo pagados)
                monto_estudiante = tarifa.monto
                
                for mes_str in meses_a_facturar:
                    mes = int(mes_str)
                    # Aplicar descuento familiar si existe
                    descuento = Decimal('0.00')
                    if grupo.descuento_general > 0:
                        descuento = monto_estudiante * (grupo.descuento_general / 100)
                    
                    DetalleFactura.objects.create(
                        factura=factura,
                        concepto=concepto_mensualidad,
                        descripcion=f"{concepto_mensualidad.nombre} - {meses_nombres[mes-1]} {anio}",
                        mes=mes,
                        anio=anio,
                        cantidad=1,
                        precio_unitario=monto_estudiante,
                        descuento=descuento
                    )
                
                # Calcular fecha de vencimiento y aplicar mora si corresponde
                # Tomar el mes más antiguo de los meses a facturar para calcular vencimiento
                mes_mas_antiguo = min([int(m) for m in meses_a_facturar])
                
                # Calcular fecha de vencimiento basada en el día configurado del grupo
                dia_vencimiento = grupo.dia_vencimiento
                try:
                    fecha_vencimiento = date(anio, mes_mas_antiguo, dia_vencimiento)
                except ValueError:
                    # Si el mes no tiene ese día (ej: 31 en febrero), usar el último día del mes
                    ultimo_dia = monthrange(anio, mes_mas_antiguo)[1]
                    fecha_vencimiento = date(anio, mes_mas_antiguo, ultimo_dia)
                
                # Guardar fecha de vencimiento en la factura
                factura.fecha_vencimiento = fecha_vencimiento
                factura.save()
                
                # Verificar si está vencida y aplicar mora
                hoy = date.today()
                if hoy > fecha_vencimiento:
                    # La factura está vencida, calcular mora
                    porcentaje_mora = estudiante.get_porcentaje_mora()
                    
                    if porcentaje_mora > 0:
                        # Calcular subtotal antes de mora
                        subtotal = sum(detalle.get_total() for detalle in factura.detalles.all())
                        monto_mora = (subtotal * porcentaje_mora) / Decimal('100')
                        
                        # Crear o buscar concepto de mora
                        concepto_mora, created = ConceptoPago.objects.get_or_create(
                            tipo='otro',
                            nombre='Mora por Pago Atrasado',
                            defaults={
                                'monto': 0,
                                'descripcion': 'Recargo por pago fuera de fecha',
                                'activo': True
                            }
                        )
                        
                        # Agregar detalle de mora
                        DetalleFactura.objects.create(
                            factura=factura,
                            concepto=concepto_mora,
                            descripcion=f'Mora ({porcentaje_mora}% - Vencimiento: {fecha_vencimiento.strftime("%d/%m/%Y")})',
                            cantidad=1,
                            precio_unitario=monto_mora,
                            descuento=0
                        )
                        print(f"DEBUG MORA FAMILIA - ✓ Mora aplicada a factura {factura.numero_factura}: {porcentaje_mora}% = RD${monto_mora} (Vencimiento: {fecha_vencimiento})")
                
                # Calcular totales de esta factura
                factura.calcular_totales()
                total_facturas += factura.total  # Acumular para distribución proporcional
                
                facturas_creadas.append(factura)
            
            # Distribuir el pago proporcionalmente entre las facturas creadas
            if monto_pagado > 0 and facturas_creadas and total_facturas > 0:
                print(f"DEBUG FAMILIA - Distribuyendo pago: RD$ {monto_pagado} entre {len(facturas_creadas)} facturas. Total: RD$ {total_facturas}")
                
                # Si el pago es mayor o igual al total, pagar completo cada factura
                if monto_pagado >= total_facturas:
                    print(f"DEBUG FAMILIA - Pago completo o con exceso. Pagando total de cada factura.")
                    for factura in facturas_creadas:
                        # Asignar el total exacto de la factura (no más)
                        factura.monto_pagado = factura.total
                        factura.actualizar_estado()
                        factura.save()
                        print(f"  - Factura {factura.numero_factura}: Total RD$ {factura.total}, Pagado RD$ {factura.monto_pagado}, Estado: {factura.estado}")
                else:
                    # Si el pago es menor al total, distribución proporcional
                    print(f"DEBUG FAMILIA - Pago parcial. Distribución proporcional.")
                    for factura in facturas_creadas:
                        # Calcular proporción de esta factura respecto al total
                        proporcion = factura.total / total_facturas
                        factura.monto_pagado = (monto_pagado * proporcion).quantize(Decimal('0.01'))
                        factura.actualizar_estado()
                        factura.save()
                        print(f"  - Factura {factura.numero_factura}: Total RD$ {factura.total}, Pagado RD$ {factura.monto_pagado}, Estado: {factura.estado}")
            else:
                # Si no hay pago, solo actualizar estados
                for factura in facturas_creadas:
                    factura.actualizar_estado()
                    factura.save()
                    print(f"DEBUG FAMILIA - Factura {factura.numero_factura}: Sin pago, Estado: {factura.estado}")
            
            if facturas_creadas:
                # Contar total de meses facturados (algunos estudiantes pueden tener menos meses)
                total_detalles = sum(DetalleFactura.objects.filter(factura=f).count() for f in facturas_creadas)
                
                # Mensaje con información de pago
                mensaje = f'Se crearon {len(facturas_creadas)} factura(s) con {total_detalles} detalle(s) de mensualidad para el grupo familiar {grupo.apellido_familia}.'
                
                if monto_pagado > 0:
                    if monto_pagado >= total_facturas:
                        # Pago completo con o sin exceso
                        cambio = monto_pagado - total_facturas
                        mensaje += f' Facturas pagadas completamente (RD$ {total_facturas:.2f}).'
                        if cambio > 0:
                            mensaje += f' CAMBIO A DEVOLVER: RD$ {cambio:.2f}'
                    else:
                        # Pago parcial
                        mensaje += f' Pago parcial registrado: RD$ {monto_pagado:.2f} de RD$ {total_facturas:.2f}.'
                
                messages.success(request, mensaje)
                # Redirigir a la página principal de facturación con cliente genérico
                return redirect('/facturas/nueva/?estudiante_id=546')
            else:
                messages.warning(request, 'No se creó ninguna factura. Todos los estudiantes seleccionados ya tienen pagados los meses indicados.')
                return redirect('grupo_familiar_facturar', grupo_id=grupo_id)
                
        except Exception as e:
            messages.error(request, f'Error al crear facturas: {str(e)}')
            return redirect('grupo_familiar_facturar', grupo_id=grupo_id)
    
    # GET - Mostrar formulario
    # Calcular totales por estudiante y obtener meses pagados
    estudiantes_data = []
    total_general = Decimal('0.00')
    
    for estudiante in estudiantes:
        try:
            # Obtener tarifa de mensualidad
            tarifa = TarifaEstudiante.objects.filter(
                estudiante=estudiante,
                concepto__tipo='mensualidad',
                activo=True
            ).first()
            
            if tarifa and tarifa.monto:
                # Obtener meses ya pagados por este estudiante
                detalles_pagados = DetalleFactura.objects.filter(
                    factura__cliente=estudiante,
                    factura__anho_escolar=anho_escolar,
                    concepto__tipo='mensualidad',
                    mes__isnull=False,
                    anio__isnull=False,
                    factura__estado__in=['pagada', 'pendiente', 'parcial']  # Excluir anuladas
                ).values_list('mes', 'anio')
                
                # Convertir a set para eliminar duplicados
                meses_unicos = set(detalles_pagados)
                meses_pagados_list = [f"{mes}-{anio}" for mes, anio in meses_unicos]
                
                monto = tarifa.monto
                descuento = Decimal('0.00')
                if grupo.descuento_general > 0:
                    descuento = monto * (grupo.descuento_general / 100)
                
                monto_final = monto - descuento
                total_general += monto_final
                
                estudiantes_data.append({
                    'estudiante': estudiante,
                    'monto_base': monto,
                    'descuento': descuento,
                    'monto_final': monto_final,
                    'meses_pagados': meses_pagados_list  # Lista de meses ya pagados
                })
        except:
            pass
    
    # Obtener mes y año actual
    now = datetime.now()
    mes_actual = now.month
    anio_actual = now.year
    
    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    context = {
        'grupo': grupo,
        'estudiantes_data': estudiantes_data,
        'total_general': total_general,
        'meses': meses,
        'mes_actual': mes_actual,
        'anio_actual': anio_actual,
    }
    
    return render(request, 'familias/grupo_facturar.html', context)
