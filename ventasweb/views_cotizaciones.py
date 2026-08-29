"""
Vistas para el sistema de cotizaciones
"""
from datetime import date, timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import (
    Cotizacion, DetalleCotizacion, Factura, DetalleFactura, 
    CustomUser, Articulo, PlantillaCotizacion, DetallePlantillaCotizacion,
    HistorialCotizacion
)
from .utils_pdf import generar_pdf_cotizacion


@login_required
def cotizaciones_lista(request):
    """Lista de cotizaciones"""
    # Filtros
    estado = request.GET.get('estado', '')
    cliente_id = request.GET.get('cliente', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    cotizaciones = Cotizacion.objects.select_related('cliente', 'vendedor', 'creado_por')
    
    # Aplicar filtros
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)
    if cliente_id:
        cotizaciones = cotizaciones.filter(cliente_id=cliente_id)
    if fecha_desde:
        cotizaciones = cotizaciones.filter(fecha_emision__gte=fecha_desde)
    if fecha_hasta:
        cotizaciones = cotizaciones.filter(fecha_emision__lte=fecha_hasta)
    
    # Estadísticas
    total_cotizaciones = cotizaciones.count()
    cotizaciones_pendientes = cotizaciones.filter(estado='enviada').count()
    cotizaciones_aceptadas = cotizaciones.filter(estado='aceptada').count()
    cotizaciones_convertidas = cotizaciones.filter(estado='convertida').count()
    
    # Monto total de cotizaciones activas (no rechazadas ni vencidas)
    monto_total = cotizaciones.filter(
        estado__in=['borrador', 'enviada', 'aceptada']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Clientes para el filtro
    clientes = CustomUser.objects.filter(rol='Cliente', is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'cotizaciones': cotizaciones.order_by('-fecha_emision')[:50],  # Últimas 50
        'total_cotizaciones': total_cotizaciones,
        'cotizaciones_pendientes': cotizaciones_pendientes,
        'cotizaciones_aceptadas': cotizaciones_aceptadas,
        'cotizaciones_convertidas': cotizaciones_convertidas,
        'monto_total': monto_total,
        'clientes': clientes,
        'estado_actual': estado,
        'cliente_actual': cliente_id,
    }
    
    return render(request, 'website/cotizaciones_lista.html', context)


@login_required
def cotizacion_crear(request):
    """Crear nueva cotización"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear cotización
                cliente_id = request.POST.get('cliente')
                cliente = get_object_or_404(CustomUser, id=cliente_id, rol='Cliente')
                
                vendedor_id = request.POST.get('vendedor')
                vendedor = None
                if vendedor_id:
                    vendedor = get_object_or_404(CustomUser, id=vendedor_id, rol='Vendedor')
                
                fecha_vencimiento = request.POST.get('fecha_vencimiento')
                if not fecha_vencimiento:
                    # Por defecto, vence en 30 días
                    fecha_vencimiento = (date.today() + timedelta(days=30)).isoformat()
                
                cotizacion = Cotizacion.objects.create(
                    cliente=cliente,
                    vendedor=vendedor,
                    fecha_vencimiento=fecha_vencimiento,
                    observaciones=request.POST.get('observaciones', ''),
                    notas_internas=request.POST.get('notas_internas', ''),
                    terminos_condiciones=request.POST.get('terminos_condiciones', ''),
                    creado_por=request.user
                )
                
                # Agregar detalles
                articulos_ids = request.POST.getlist('articulo_id[]')
                descripciones = request.POST.getlist('descripcion[]')
                cantidades = request.POST.getlist('cantidad[]')
                precios = request.POST.getlist('precio_unitario[]')
                descuentos = request.POST.getlist('descuento[]')
                
                subtotal = Decimal('0')
                descuento_total = Decimal('0')
                
                for i in range(len(descripciones)):
                    if descripciones[i].strip():
                        articulo = None
                        if articulos_ids[i]:
                            articulo = Articulo.objects.get(id=articulos_ids[i])
                        
                        cantidad = Decimal(cantidades[i] or '1')
                        precio_unitario = Decimal(precios[i] or '0')
                        descuento = Decimal(descuentos[i] or '0')
                        
                        DetalleCotizacion.objects.create(
                            cotizacion=cotizacion,
                            articulo=articulo,
                            descripcion=descripciones[i],
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento=descuento
                        )
                        
                        subtotal += cantidad * precio_unitario
                        descuento_total += descuento
                
                # Calcular totales
                impuesto_porcentaje = Decimal(request.POST.get('impuesto_porcentaje', '0'))
                impuesto = (subtotal - descuento_total) * (impuesto_porcentaje / Decimal('100'))
                total = subtotal - descuento_total + impuesto
                
                cotizacion.subtotal = subtotal
                cotizacion.descuento = descuento_total
                cotizacion.impuesto = impuesto
                cotizacion.total = total
                cotizacion.save()
                
                messages.success(request, f'Cotización {cotizacion.numero_cotizacion} creada exitosamente')
                return redirect('cotizacion_detalle', cotizacion_id=cotizacion.id)
        
        except Exception as e:
            messages.error(request, f'Error al crear cotización: {str(e)}')
    
    # GET: Mostrar formulario
    clientes = CustomUser.objects.filter(rol='Cliente', is_active=True).order_by('first_name', 'last_name')
    vendedores = CustomUser.objects.filter(rol='Vendedor', is_active=True).order_by('first_name', 'last_name')
    articulos = Articulo.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'clientes': clientes,
        'vendedores': vendedores,
        'articulos': articulos,
        'fecha_vencimiento_default': (date.today() + timedelta(days=30)).isoformat(),
    }
    
    return render(request, 'website/cotizacion_form.html', context)


@login_required
def cotizacion_detalle(request, cotizacion_id):
    """Ver detalle de una cotización"""
    cotizacion = get_object_or_404(
        Cotizacion.objects.select_related('cliente', 'vendedor', 'creado_por', 'factura_generada'),
        id=cotizacion_id
    )
    detalles = cotizacion.detalles.select_related('articulo').all()
    
    context = {
        'cotizacion': cotizacion,
        'detalles': detalles,
    }
    
    return render(request, 'website/cotizacion_detalle.html', context)


@login_required
def cotizacion_convertir_factura(request, cotizacion_id):
    """Convertir cotización en factura"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    
    if not cotizacion.puede_convertir_a_factura():
        messages.error(request, 'Esta cotización no puede ser convertida a factura')
        return redirect('cotizacion_detalle', cotizacion_id=cotizacion.id)
    
    if cotizacion.factura_generada:
        messages.warning(request, 'Esta cotización ya fue convertida a factura')
        return redirect('cotizacion_detalle', cotizacion_id=cotizacion.id)
    
    try:
        with transaction.atomic():
            # Crear factura
            factura = Factura.objects.create(
                cliente=cotizacion.cliente,
                vendedor=cotizacion.vendedor,
                subtotal=cotizacion.subtotal,
                descuento=cotizacion.descuento,
                impuesto=cotizacion.impuesto,
                total=cotizacion.total,
                estado='pendiente',
                observaciones=cotizacion.observaciones,
                notas_internas=f"Generada desde cotización {cotizacion.numero_cotizacion}\n{cotizacion.notas_internas or ''}",
                creado_por=request.user
            )
            
            # Copiar detalles
            for detalle in cotizacion.detalles.all():
                DetalleFactura.objects.create(
                    factura=factura,
                    articulo=detalle.articulo,
                    descripcion=detalle.descripcion,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    descuento=detalle.descuento
                )
                
                # Actualizar inventario si es artículo
                if detalle.articulo:
                    detalle.articulo.stock_actual -= detalle.cantidad
                    detalle.articulo.save()
            
            # Actualizar cotización
            cotizacion.estado = 'convertida'
            cotizacion.factura_generada = factura
            cotizacion.save()
            
            messages.success(request, f'Cotización convertida exitosamente a factura {factura.numero_factura}')
            return redirect('detalle_factura', factura_id=factura.id)
    
    except Exception as e:
        messages.error(request, f'Error al convertir cotización: {str(e)}')
        return redirect('cotizacion_detalle', cotizacion_id=cotizacion.id)


@login_required
def cotizacion_cambiar_estado(request, cotizacion_id):
    """Cambiar estado de una cotización"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    nuevo_estado = request.POST.get('estado')
    
    if nuevo_estado not in dict(Cotizacion.ESTADO_CHOICES):
        return JsonResponse({'error': 'Estado inválido'}, status=400)
    
    cotizacion.estado = nuevo_estado
    cotizacion.save()
    
    messages.success(request, f'Estado de cotización actualizado a {cotizacion.get_estado_display()}')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'estado': nuevo_estado})
    
    return redirect('cotizacion_detalle', cotizacion_id=cotizacion.id)


@login_required
def cotizacion_eliminar(request, cotizacion_id):
    """Eliminar una cotización (solo si es borrador)"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    
    if cotizacion.estado != 'borrador':
        messages.error(request, 'Solo se pueden eliminar cotizaciones en estado borrador')
        return redirect('cotizacion_detalle', cotizacion_id=cotizacion.id)
    
    numero = cotizacion.numero_cotizacion
    
    # Registrar en historial antes de eliminar
    HistorialCotizacion.objects.create(
        cotizacion=cotizacion,
        tipo_cambio='modificacion',
        descripcion=f'Cotización eliminada por {request.user.get_full_name()}',
        usuario=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    cotizacion.delete()
    
    messages.success(request, f'Cotización {numero} eliminada exitosamente')
    return redirect('cotizaciones_lista')


# ============================================================================
# NUEVAS FUNCIONALIDADES AVANZADAS
# ============================================================================

@login_required
def cotizacion_generar_pdf(request, cotizacion_id):
    """Genera y descarga el PDF de una cotización"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    
    # Registrar en historial
    HistorialCotizacion.objects.create(
        cotizacion=cotizacion,
        tipo_cambio='vista',
        descripcion=f'PDF generado por {request.user.get_full_name()}',
        usuario=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Generar PDF
    pdf_buffer = generar_pdf_cotizacion(cotizacion, request)
    
    # Preparar respuesta
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Cotizacion_{cotizacion.numero_cotizacion}.pdf"'
    
    return response


def cotizacion_publica(request, token):
    """Vista pública de cotización para clientes (sin login)"""
    try:
        cotizacion = Cotizacion.objects.select_related('cliente', 'vendedor').get(token_publico=token)
    except Cotizacion.DoesNotExist:
        raise Http404("Cotización no encontrada")
    
    # Registrar vista
    cotizacion.veces_vista += 1
    cotizacion.save()
    
    HistorialCotizacion.objects.create(
        cotizacion=cotizacion,
        tipo_cambio='vista',
        descripcion=f'Vista pública desde IP {request.META.get("REMOTE_ADDR")}',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    context = {
        'cotizacion': cotizacion,
        'detalles': cotizacion.detalles.all(),
        'puede_firmar': cotizacion.estado in ['enviada', 'borrador'] and not cotizacion.firma_cliente,
        'esta_vencida': cotizacion.esta_vencida(),
    }
    
    return render(request, 'website/cotizacion_publica.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def cotizacion_firmar(request, token):
    """Registra la firma digital del cliente"""
    try:
        cotizacion = Cotizacion.objects.get(token_publico=token)
    except Cotizacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cotización no encontrada'}, status=404)
    
    # Verificar que puede firmar
    if cotizacion.firma_cliente:
        return JsonResponse({'success': False, 'error': 'Esta cotización ya fue firmada'}, status=400)
    
    if cotizacion.estado not in ['enviada', 'borrador']:
        return JsonResponse({'success': False, 'error': 'Esta cotización no puede ser firmada'}, status=400)
    
    try:
        data = json.loads(request.body)
        firma_base64 = data.get('firma')
        
        if not firma_base64:
            return JsonResponse({'success': False, 'error': 'Firma no proporcionada'}, status=400)
        
        # Guardar firma
        ip_address = request.META.get('REMOTE_ADDR')
        cotizacion.firmar(firma_base64, ip_address)
        
        # Registrar en historial
        HistorialCotizacion.objects.create(
            cotizacion=cotizacion,
            tipo_cambio='firma',
            descripcion=f'Firmado por {cotizacion.cliente.get_full_name()} desde IP {ip_address}',
            ip_address=ip_address,
            datos_nuevos={'firma_fecha': timezone.now().isoformat()}
        )
        
        return JsonResponse({'success': True, 'message': 'Cotización firmada exitosamente'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def cotizacion_enviar_whatsapp(request, cotizacion_id):
    """Prepara URL para enviar cotización por WhatsApp"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    
    # Generar URL pública
    url_publica = cotizacion.get_url_publica(request)
    
    # Texto del mensaje
    mensaje = f"""
🧾 *Nueva Cotización - {cotizacion.numero_cotizacion}*

Hola {cotizacion.cliente.get_full_name()},

Te enviamos la cotización solicitada por un total de *RD$ {cotizacion.total:,.2f}*

📋 Ver cotización completa:
{url_publica}

✅ Válida hasta: {cotizacion.fecha_vencimiento.strftime('%d/%m/%Y')}

¿Tienes alguna pregunta? ¡Estamos para ayudarte!
    """.strip()
    
    # Registrar en historial
    HistorialCotizacion.objects.create(
        cotizacion=cotizacion,
        tipo_cambio='envio',
        descripcion=f'Preparado para envío por WhatsApp por {request.user.get_full_name()}',
        usuario=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Actualizar estado si es borrador
    if cotizacion.estado == 'borrador':
        cotizacion.estado = 'enviada'
        cotizacion.save()
    
    # Obtener teléfono del cliente
    telefono = cotizacion.cliente.telefono if hasattr(cotizacion.cliente, 'telefono') and cotizacion.cliente.telefono else ''
    
    # Limpiar número de teléfono (solo dígitos)
    import re
    telefono_limpio = re.sub(r'\D', '', telefono)
    
    # URL de WhatsApp
    if telefono_limpio:
        whatsapp_url = f"https://wa.me/{telefono_limpio}?text={mensaje}"
    else:
        whatsapp_url = f"https://wa.me/?text={mensaje}"
    
    return JsonResponse({
        'success': True,
        'whatsapp_url': whatsapp_url,
        'mensaje': mensaje,
        'telefono': telefono_limpio
    })


# ============================================================================
# PLANTILLAS DE COTIZACIÓN
# ============================================================================

@login_required
def plantillas_lista(request):
    """Lista de plantillas de cotización"""
    plantillas = PlantillaCotizacion.objects.filter(activa=True).prefetch_related('items')
    
    context = {
        'plantillas': plantillas,
    }
    
    return render(request, 'website/plantillas_lista.html', context)


@login_required
def plantilla_crear(request):
    """Crear nueva plantilla de cotización"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear plantilla
                plantilla = PlantillaCotizacion.objects.create(
                    nombre=request.POST.get('nombre'),
                    descripcion=request.POST.get('descripcion', ''),
                    dias_vencimiento=int(request.POST.get('dias_vencimiento', 30)),
                    terminos_condiciones=request.POST.get('terminos_condiciones', ''),
                    observaciones=request.POST.get('observaciones', ''),
                    creado_por=request.user
                )
                
                # Crear items de la plantilla
                descripciones = request.POST.getlist('descripcion[]')
                cantidades = request.POST.getlist('cantidad[]')
                precios = request.POST.getlist('precio_unitario[]')
                descuentos = request.POST.getlist('descuento[]')
                articulos_ids = request.POST.getlist('articulo[]')
                
                for idx, desc in enumerate(descripciones):
                    if desc.strip():
                        DetallePlantillaCotizacion.objects.create(
                            plantilla=plantilla,
                            descripcion=desc,
                            cantidad=Decimal(cantidades[idx]) if cantidades[idx] else 1,
                            precio_unitario=Decimal(precios[idx]) if precios[idx] else 0,
                            descuento=Decimal(descuentos[idx]) if descuentos[idx] else 0,
                            articulo_id=articulos_ids[idx] if articulos_ids[idx] and articulos_ids[idx] != '' else None,
                            orden=idx
                        )
                
                messages.success(request, f'Plantilla "{plantilla.nombre}" creada exitosamente')
                return redirect('plantillas_lista')
                
        except Exception as e:
            messages.error(request, f'Error al crear plantilla: {str(e)}')
    
    # GET request
    articulos = Articulo.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'articulos': articulos,
    }
    
    return render(request, 'website/plantilla_form.html', context)


@login_required
def cotizacion_desde_plantilla(request, plantilla_id):
    """Crea una cotización desde una plantilla"""
    plantilla = get_object_or_404(PlantillaCotizacion, id=plantilla_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                cliente_id = request.POST.get('cliente')
                vendedor_id = request.POST.get('vendedor')
                
                # Crear cotización
                cotizacion = Cotizacion.objects.create(
                    cliente_id=cliente_id,
                    vendedor_id=vendedor_id if vendedor_id else None,
                    fecha_vencimiento=date.today() + timedelta(days=plantilla.dias_vencimiento),
                    terminos_condiciones=plantilla.terminos_condiciones,
                    observaciones=plantilla.observaciones,
                    creado_por=request.user
                )
                
                # Copiar items de la plantilla
                subtotal = Decimal('0')
                total_descuento = Decimal('0')
                
                for item in plantilla.items.all():
                    detalle = DetalleCotizacion.objects.create(
                        cotizacion=cotizacion,
                        articulo=item.articulo,
                        descripcion=item.descripcion,
                        cantidad=item.cantidad,
                        precio_unitario=item.precio_unitario,
                        descuento=item.descuento
                    )
                    subtotal += detalle.get_subtotal()
                    total_descuento += detalle.descuento
                
                # Calcular totales
                itbis_porcentaje = Decimal(request.POST.get('itbis', '18'))
                cotizacion.subtotal = subtotal
                cotizacion.descuento = total_descuento
                cotizacion.impuesto = (subtotal - total_descuento) * (itbis_porcentaje / 100)
                cotizacion.total = subtotal - total_descuento + cotizacion.impuesto
                cotizacion.save()
                
                # Registrar en historial
                HistorialCotizacion.objects.create(
                    cotizacion=cotizacion,
                    tipo_cambio='creacion',
                    descripcion=f'Cotización creada desde plantilla "{plantilla.nombre}" por {request.user.get_full_name()}',
                    usuario=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Cotización {cotizacion.numero_cotizacion} creada desde plantilla')
                return redirect('cotizacion_detalle', cotizacion_id=cotizacion.id)
                
        except Exception as e:
            messages.error(request, f'Error al crear cotización: {str(e)}')
    
    # GET request
    clientes = CustomUser.objects.filter(rol='Cliente', is_active=True)
    vendedores = CustomUser.objects.filter(rol='Vendedor', is_active=True)
    
    context = {
        'plantilla': plantilla,
        'clientes': clientes,
        'vendedores': vendedores,
        'items': plantilla.items.all(),
    }
    
    return render(request, 'website/cotizacion_desde_plantilla.html', context)


@login_required
def cotizacion_historial(request, cotizacion_id):
    """Ver historial de cambios de una cotización"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    historial = cotizacion.historial.select_related('usuario').order_by('-fecha')
    
    context = {
        'cotizacion': cotizacion,
        'historial': historial,
    }
    
    return render(request, 'website/cotizacion_historial.html', context)

