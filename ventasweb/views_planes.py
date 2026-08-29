"""
Vistas para gestión de planes y billing
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

@login_required
def mi_plan(request):
    """Dashboard de uso del plan actual del tenant"""
    if not hasattr(request, 'tenant') or request.tenant.schema_name == 'public':
        messages.error(request, 'Esta función solo está disponible para tenants.')
        return redirect('plataform')
    
    tenant = request.tenant
    
    # Obtener información del plan
    info_plan = tenant.get_info_plan()
    
    # Calcular porcentajes de uso
    porcentaje_usuarios = tenant.get_porcentaje_uso_usuarios()
    porcentaje_facturas = tenant.get_porcentaje_uso_facturas()
    
    context = {
        'tenant': tenant,
        'info_plan': info_plan,
        'porcentaje_usuarios': porcentaje_usuarios,
        'porcentaje_facturas': porcentaje_facturas,
    }
    
    return render(request, 'planes/mi_plan.html', context)


def planes_pricing(request):
    """Página pública de planes y precios"""
    planes = [
        {
            'nombre': 'Gratis',
            'precio': '$0',
            'periodo': '30 días de prueba',
            'color': 'secondary',
            'destacado': False,
            'caracteristicas': [
                '1 usuario',
                '50 facturas/mes',
                '1 sucursal',
                'Soporte por email',
            ],
            'no_incluye': [
                'Reportes avanzados',
                'Facturación electrónica',
            ]
        },
        {
            'nombre': 'Básico',
            'precio': '$5',
            'periodo': 'por mes',
            'color': 'primary',
            'destacado': False,
            'caracteristicas': [
                '2 usuarios',
                '200 facturas/mes',
                '1 sucursal',
                'Facturación electrónica',
                'Soporte por email',
            ],
            'no_incluye': [
                'Reportes avanzados',
            ]
        },
        {
            'nombre': 'Plus',
            'precio': '$12',
            'periodo': 'por mes',
            'color': 'success',
            'destacado': True,
            'caracteristicas': [
                '5 usuarios',
                '1,000 facturas/mes',
                '2 sucursales',
                'Reportes avanzados',
                'Facturación electrónica',
                'Soporte prioritario',
            ],
            'no_incluye': []
        },
        {
            'nombre': 'Pro',
            'precio': '$25',
            'periodo': 'por mes',
            'color': 'warning',
            'destacado': False,
            'caracteristicas': [
                '15 usuarios',
                'Facturas ilimitadas',
                '5 sucursales',
                'Reportes avanzados',
                'Facturación electrónica',
                'API completa',
                'Soporte 24/7',
                'Personalización',
            ],
            'no_incluye': []
        },
    ]
    
    # Si el usuario está autenticado, mostrar su plan actual
    plan_actual = None
    if request.user.is_authenticated and hasattr(request, 'tenant'):
        if request.tenant.schema_name != 'public':
            plan_actual = request.tenant.plan
    
    context = {
        'planes': planes,
        'plan_actual': plan_actual,
    }
    
    return render(request, 'planes/pricing.html', context)


@login_required
def cambiar_plan(request):
    """Cambiar el plan del tenant"""
    if not hasattr(request, 'tenant') or request.tenant.schema_name == 'public':
        return JsonResponse({'error': 'No disponible para este tenant'}, status=400)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    nuevo_plan = request.POST.get('plan')
    
    if nuevo_plan not in ['gratis', 'basico', 'plus', 'pro']:
        return JsonResponse({'error': 'Plan inválido'}, status=400)
    
    tenant = request.tenant
    plan_anterior = tenant.plan
    
    # Cambiar plan
    tenant.plan = nuevo_plan
    tenant.configurar_limites_plan()
    tenant.save()
    
    # Log del cambio
    print(f"BILLING - Tenant {tenant.nombre} cambió de plan {plan_anterior} → {nuevo_plan}")
    
    messages.success(
        request, 
        f'¡Plan actualizado exitosamente! Ahora estás en el plan {tenant.get_plan_display()}'
    )
    
    return JsonResponse({
        'success': True,
        'mensaje': 'Plan actualizado',
        'plan_nuevo': tenant.get_plan_display(),
        'precio': str(tenant.precio_mensual),
    })


@login_required
def uso_api(request):
    """API para obtener uso actual (AJAX)"""
    if not hasattr(request, 'tenant') or request.tenant.schema_name == 'public':
        return JsonResponse({'error': 'No disponible'}, status=400)
    
    tenant = request.tenant
    
    data = {
        'usuarios': {
            'actual': tenant.contar_usuarios(),
            'maximo': tenant.max_usuarios,
            'porcentaje': tenant.get_porcentaje_uso_usuarios(),
        },
        'facturas': {
            'actual': tenant.contar_facturas_mes(),
            'maximo': tenant.max_facturas_mes if tenant.max_facturas_mes < 99999 else 'ilimitado',
            'porcentaje': tenant.get_porcentaje_uso_facturas(),
        },
        'plan': {
            'nombre': tenant.get_plan_display(),
            'precio': str(tenant.precio_mensual),
            'activo': tenant.esta_activa(),
        }
    }
    
    return JsonResponse(data)
