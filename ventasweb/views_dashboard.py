"""
Vista del Dashboard Analytics con datos en tiempo real
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from .models import Factura, DetalleFactura, CustomUser, Articulo


@login_required
def dashboard_analytics(request):
    """
    Dashboard principal con métricas en tiempo real
    """
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
    fin_mes_anterior = inicio_mes - timedelta(seconds=1)
    
    # ========== KPI 1: Ventas del Mes ==========
    ventas_mes_actual = Factura.objects.filter(
        fecha_emision__gte=inicio_mes,
        estado='pagada'
    ).aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    ventas_mes_anterior = Factura.objects.filter(
        fecha_emision__gte=inicio_mes_anterior,
        fecha_emision__lt=inicio_mes,
        estado='pagada'
    ).aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    # Calcular porcentaje de cambio
    if ventas_mes_anterior > 0:
        cambio_ventas = ((ventas_mes_actual - ventas_mes_anterior) / ventas_mes_anterior) * 100
    else:
        cambio_ventas = 100 if ventas_mes_actual > 0 else 0
    
    # ========== KPI 2: Clientes Activos ==========
    clientes_activos = CustomUser.objects.filter(
        rol='Cliente',
        is_active=True
    ).count()
    
    # Clientes nuevos esta semana
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    clientes_nuevos_semana = CustomUser.objects.filter(
        rol='Cliente',
        date_joined__gte=inicio_semana
    ).count()
    
    # ========== KPI 3: Productos Vendidos ==========
    productos_vendidos_mes = DetalleFactura.objects.filter(
        factura__fecha_emision__gte=inicio_mes,
        factura__estado='pagada'
    ).aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    productos_vendidos_total = DetalleFactura.objects.filter(
        factura__estado='pagada'
    ).aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    # ========== KPI 4: Facturas Pendientes ==========
    facturas_pendientes = Factura.objects.filter(
        Q(estado='pendiente') | Q(estado='parcial')
    ).count()
    
    # ========== Ticket Promedio ==========
    ticket_promedio = Factura.objects.filter(
        fecha_emision__gte=inicio_mes,
        estado='pagada'
    ).aggregate(
        promedio=Avg('total')
    )['promedio'] or Decimal('0.00')
    
    # ========== Top 5 Productos Más Vendidos ==========
    top_productos = DetalleFactura.objects.filter(
        factura__fecha_emision__gte=inicio_mes,
        factura__estado='pagada'
    ).values(
        'articulo__id',
        'articulo__nombre',
        'articulo__categoria',
        'articulo__precio_venta'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-cantidad_vendida')[:5]
    
    # ========== Actividad Reciente ==========
    actividades = []
    
    # Últimas 5 ventas
    ultimas_ventas = Factura.objects.filter(
        estado='pagada'
    ).select_related('cliente').order_by('-fecha_emision')[:3]
    
    for venta in ultimas_ventas:
        tiempo_transcurrido = calcular_tiempo_transcurrido(venta.fecha_emision)
        actividades.append({
            'tipo': 'venta',
            'icono': 'fa-check',
            'color': 'success',
            'titulo': 'Nueva venta completada',
            'descripcion': f'Factura #{venta.numero_factura} - ${venta.total:,.2f}',
            'tiempo': tiempo_transcurrido
        })
    
    # Últimos 2 clientes nuevos
    ultimos_clientes = CustomUser.objects.filter(
        rol='Cliente'
    ).order_by('-date_joined')[:2]
    
    for cliente in ultimos_clientes:
        tiempo_transcurrido = calcular_tiempo_transcurrido(cliente.date_joined)
        actividades.append({
            'tipo': 'cliente',
            'icono': 'fa-user-plus',
            'color': 'primary',
            'titulo': 'Nuevo cliente registrado',
            'descripcion': f'{cliente.get_full_name() or cliente.email}',
            'tiempo': tiempo_transcurrido
        })
    
    # Productos con stock bajo
    productos_bajo_stock = Articulo.objects.filter(
        stock_actual__lte=F('stock_minimo'),
        stock_actual__gt=0
    )[:2]
    
    for producto in productos_bajo_stock:
        actividades.append({
            'tipo': 'stock',
            'icono': 'fa-exclamation',
            'color': 'warning',
            'titulo': 'Stock bajo detectado',
            'descripcion': f'{producto.nombre} - {producto.stock_actual} unidades',
            'tiempo': 'Ahora'
        })
    
    # Ordenar por tiempo (más reciente primero)
    actividades = sorted(actividades, key=lambda x: x['tiempo'] if x['tiempo'] != 'Ahora' else '0 minutos', reverse=False)[:5]
    
    context = {
        # KPIs
        'ventas_mes_actual': ventas_mes_actual,
        'cambio_ventas': cambio_ventas,
        'clientes_activos': clientes_activos,
        'clientes_nuevos_semana': clientes_nuevos_semana,
        'productos_vendidos_mes': productos_vendidos_mes,
        'productos_vendidos_total': productos_vendidos_total,
        'facturas_pendientes': facturas_pendientes,
        'ticket_promedio': ticket_promedio,
        
        # Top productos
        'top_productos': list(top_productos),
        
        # Actividades
        'actividades': actividades,
        
        # Meta info
        'mes_actual': inicio_mes.strftime('%B %Y'),
    }
    
    return render(request, 'website/dashboard_analytics.html', context)


def calcular_tiempo_transcurrido(fecha):
    """Calcula el tiempo transcurrido desde una fecha"""
    ahora = timezone.now()
    diferencia = ahora - fecha
    
    if diferencia.days > 0:
        if diferencia.days == 1:
            return 'Hace 1 día'
        return f'Hace {diferencia.days} días'
    
    horas = diferencia.seconds // 3600
    if horas > 0:
        if horas == 1:
            return 'Hace 1 hora'
        return f'Hace {horas} horas'
    
    minutos = (diferencia.seconds % 3600) // 60
    if minutos > 0:
        if minutos == 1:
            return 'Hace 1 minuto'
        return f'Hace {minutos} minutos'
    
    return 'Justo ahora'


@login_required
def api_ventas_tendencia(request):
    """
    API que devuelve datos de ventas para el gráfico de tendencias
    Formato: JSON con ventas de los últimos 6 meses
    """
    hoy = timezone.now()
    meses_datos = []
    labels = []
    
    # Obtener datos de los últimos 6 meses
    for i in range(5, -1, -1):
        fecha = hoy - timedelta(days=30*i)
        inicio_mes = fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if i > 0:
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        else:
            fin_mes = hoy
        
        ventas_mes = Factura.objects.filter(
            fecha_emision__gte=inicio_mes,
            fecha_emision__lte=fin_mes,
            estado='pagada'
        ).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')
        
        meses_datos.append(float(ventas_mes))
        labels.append(inicio_mes.strftime('%B'))
    
    return JsonResponse({
        'labels': labels,
        'data': meses_datos,
        'mes_actual': hoy.strftime('%B %Y')
    })


@login_required
def api_productos_chart(request):
    """
    API para gráfico de productos más vendidos (últimos 30 días)
    """
    hace_30_dias = timezone.now() - timedelta(days=30)
    
    top_productos = DetalleFactura.objects.filter(
        factura__fecha_emision__gte=hace_30_dias,
        factura__estado='pagada'
    ).values(
        'articulo__nombre'
    ).annotate(
        cantidad=Sum('cantidad')
    ).order_by('-cantidad')[:10]
    
    labels = [p['articulo__nombre'] for p in top_productos]
    data = [int(p['cantidad']) for p in top_productos]
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })


@login_required
def api_ventas_hoy(request):
    """
    API para ventas del día actual (actualización en tiempo real)
    """
    hoy = timezone.now().date()
    
    ventas_hoy = Factura.objects.filter(
        fecha_emision__date=hoy,
        estado='pagada'
    ).aggregate(
        total=Sum('total'),
        cantidad=Count('id')
    )
    
    return JsonResponse({
        'total': float(ventas_hoy['total'] or 0),
        'cantidad': ventas_hoy['cantidad'] or 0,
        'fecha': hoy.strftime('%d de %B, %Y')
    })
