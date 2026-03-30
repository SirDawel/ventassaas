"""
Vistas de gestión de seguridad y auditoría
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
import csv

from escuelaweb.models import SecurityLog, LoginAttempt, UserSession, TwoFactorAuth, CustomUser


def is_admin_or_director(user):
    """Verifica si el usuario es Administrador o Director"""
    return user.rol in ['Administrador', 'Director']


@login_required
@user_passes_test(is_admin_or_director)
def security_dashboard(request):
    """
    Dashboard principal de seguridad
    """
    # Estadísticas generales
    total_usuarios = CustomUser.objects.count()
    usuarios_activos = CustomUser.objects.filter(is_active=True).count()
    sesiones_activas = UserSession.objects.filter(activa=True).count()
    
    # Intentos de login recientes (últimas 24 horas)
    hace_24h = timezone.now() - timedelta(hours=24)
    intentos_exitosos = LoginAttempt.objects.filter(
        fecha__gte=hace_24h,
        exitoso=True
    ).count()
    intentos_fallidos = LoginAttempt.objects.filter(
        fecha__gte=hace_24h,
        exitoso=False
    ).count()
    
    # Eventos de seguridad críticos (últimos 7 días)
    hace_7d = timezone.now() - timedelta(days=7)
    eventos_criticos = SecurityLog.objects.filter(
        fecha__gte=hace_7d,
        nivel_severidad__in=['ERROR', 'CRITICAL']
    ).count()
    
    eventos_warning = SecurityLog.objects.filter(
        fecha__gte=hace_7d,
        nivel_severidad='WARNING'
    ).count()
    
    # Últimos eventos de seguridad
    ultimos_eventos = SecurityLog.objects.select_related('usuario').order_by('-fecha')[:10]
    
    # Últimos intentos de login
    ultimos_intentos = LoginAttempt.objects.select_related('user').order_by('-fecha')[:10]
    
    # Usuarios con 2FA habilitado
    usuarios_2fa = TwoFactorAuth.objects.filter(habilitado=True).count()
    
    context = {
        'titulo': 'Dashboard de Seguridad',
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'sesiones_activas': sesiones_activas,
        'intentos_exitosos': intentos_exitosos,
        'intentos_fallidos': intentos_fallidos,
        'eventos_criticos': eventos_criticos,
        'eventos_warning': eventos_warning,
        'ultimos_eventos': ultimos_eventos,
        'ultimos_intentos': ultimos_intentos,
        'usuarios_2fa': usuarios_2fa,
    }
    
    return render(request, 'seguridad/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_director)
def security_logs_list(request):
    """
    Lista de registros de seguridad con filtros
    """
    logs = SecurityLog.objects.select_related('usuario').order_by('-fecha')
    
    # Filtros
    tipo_evento = request.GET.get('tipo_evento')
    nivel_severidad = request.GET.get('nivel_severidad')
    usuario_id = request.GET.get('usuario')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if tipo_evento:
        logs = logs.filter(tipo_evento=tipo_evento)
    
    if nivel_severidad:
        logs = logs.filter(nivel_severidad=nivel_severidad)
    
    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)
    
    if fecha_desde:
        logs = logs.filter(fecha__gte=fecha_desde)
    
    if fecha_hasta:
        logs = logs.filter(fecha__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)
    
    # Opciones para filtros
    tipos_evento = SecurityLog.TIPO_EVENTO_CHOICES
    niveles_severidad = SecurityLog.NIVEL_SEVERIDAD_CHOICES
    usuarios = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'titulo': 'Registros de Seguridad',
        'logs': logs_page,
        'tipos_evento': tipos_evento,
        'niveles_severidad': niveles_severidad,
        'usuarios': usuarios,
        # Valores actuales de filtros
        'tipo_evento_actual': tipo_evento,
        'nivel_severidad_actual': nivel_severidad,
        'usuario_actual': usuario_id,
        'fecha_desde_actual': fecha_desde,
        'fecha_hasta_actual': fecha_hasta,
    }
    
    return render(request, 'seguridad/logs_list.html', context)


@login_required
@user_passes_test(is_admin_or_director)
def login_attempts_list(request):
    """
    Lista de intentos de login con filtros
    """
    intentos = LoginAttempt.objects.select_related('user').order_by('-fecha')
    
    # Filtros
    email = request.GET.get('email')
    exitoso = request.GET.get('exitoso')
    ip_address = request.GET.get('ip_address')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if email:
        intentos = intentos.filter(email__icontains=email)
    
    if exitoso:
        intentos = intentos.filter(exitoso=(exitoso == 'true'))
    
    if ip_address:
        intentos = intentos.filter(ip_address__icontains=ip_address)
    
    if fecha_desde:
        intentos = intentos.filter(fecha__gte=fecha_desde)
    
    if fecha_hasta:
        intentos = intentos.filter(fecha__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(intentos, 50)
    page = request.GET.get('page')
    intentos_page = paginator.get_page(page)
    
    context = {
        'titulo': 'Intentos de Login',
        'intentos': intentos_page,
        # Valores actuales de filtros
        'email_actual': email,
        'exitoso_actual': exitoso,
        'ip_address_actual': ip_address,
        'fecha_desde_actual': fecha_desde,
        'fecha_hasta_actual': fecha_hasta,
    }
    
    return render(request, 'seguridad/login_attempts_list.html', context)


@login_required
@user_passes_test(is_admin_or_director)
def active_sessions_list(request):
    """
    Lista de sesiones activas
    """
    sesiones = UserSession.objects.filter(activa=True).select_related('usuario').order_by('-fecha_ultima_actividad')
    
    # Filtro por usuario
    usuario_id = request.GET.get('usuario')
    if usuario_id:
        sesiones = sesiones.filter(usuario_id=usuario_id)
    
    usuarios = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'titulo': 'Sesiones Activas',
        'sesiones': sesiones,
        'usuarios': usuarios,
        'usuario_actual': usuario_id,
    }
    
    return render(request, 'seguridad/active_sessions_list.html', context)


@login_required
@user_passes_test(is_admin_or_director)
def close_session(request, session_id):
    """
    Cierra una sesión específica
    """
    if request.method == 'POST':
        try:
            sesion = UserSession.objects.get(id=session_id)
            sesion.cerrar_sesion()
            
            SecurityLog.log_event(
                tipo_evento='ADMIN_ACTION',
                descripcion=f'Sesión cerrada por {request.user.email} para usuario {sesion.usuario.email}',
                usuario=request.user,
                nivel_severidad='WARNING',
                metadata={
                    'target_user': sesion.usuario.email,
                    'session_id': session_id
                }
            )
            
            messages.success(request, f'Sesión de {sesion.usuario.get_full_name()} cerrada correctamente.')
        except UserSession.DoesNotExist:
            messages.error(request, 'Sesión no encontrada.')
    
    return redirect('active_sessions_list')


@login_required
def my_security_settings(request):
    """
    Configuración de seguridad del usuario actual
    """
    user = request.user
    
    # Obtener sesiones activas del usuario
    sesiones_activas = UserSession.get_active_sessions(user)
    
    # Últimos intentos de login
    ultimos_intentos = LoginAttempt.objects.filter(
        user=user
    ).order_by('-fecha')[:10]
    
    # Últimos eventos de seguridad
    ultimos_eventos = SecurityLog.objects.filter(
        usuario=user
    ).order_by('-fecha')[:10]
    
    # 2FA status
    try:
        two_factor = TwoFactorAuth.objects.get(usuario=user)
    except TwoFactorAuth.DoesNotExist:
        two_factor = None
    
    context = {
        'titulo': 'Mi Seguridad',
        'sesiones_activas': sesiones_activas,
        'ultimos_intentos': ultimos_intentos,
        'ultimos_eventos': ultimos_eventos,
        'two_factor': two_factor,
    }
    
    return render(request, 'seguridad/my_security.html', context)


@login_required
@user_passes_test(is_admin_or_director)
def export_security_logs(request):
    """
    Exporta registros de seguridad a CSV
    """
    # Aplicar filtros
    logs = SecurityLog.objects.select_related('usuario').order_by('-fecha')
    
    tipo_evento = request.GET.get('tipo_evento')
    nivel_severidad = request.GET.get('nivel_severidad')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if tipo_evento:
        logs = logs.filter(tipo_evento=tipo_evento)
    if nivel_severidad:
        logs = logs.filter(nivel_severidad=nivel_severidad)
    if fecha_desde:
        logs = logs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        logs = logs.filter(fecha__lte=fecha_hasta)
    
    # Crear CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="security_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Usuario', 'Email', 'Tipo Evento', 'Nivel Severidad', 'Descripción', 'IP Address'])
    
    for log in logs:
        writer.writerow([
            log.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            log.usuario.get_full_name() if log.usuario else 'N/A',
            log.email,
            log.get_tipo_evento_display(),
            log.get_nivel_severidad_display(),
            log.descripcion,
            log.ip_address or 'N/A'
        ])
    
    # Registrar exportación
    SecurityLog.log_event(
        tipo_evento='DATA_EXPORT',
        descripcion=f'Exportación de {logs.count()} registros de seguridad',
        usuario=request.user,
        nivel_severidad='INFO'
    )
    
    return response


@login_required
@user_passes_test(is_admin_or_director)
def security_stats_api(request):
    """
    API para obtener estadísticas de seguridad en tiempo real
    """
    periodo = request.GET.get('periodo', '7')  # días
    hace_n_dias = timezone.now() - timedelta(days=int(periodo))
    
    # Intentos de login por día
    intentos_por_dia = LoginAttempt.objects.filter(
        fecha__gte=hace_n_dias
    ).extra(
        select={'dia': 'DATE(fecha)'}
    ).values('dia').annotate(
        total=Count('id'),
        exitosos=Count('id', filter=Q(exitoso=True)),
        fallidos=Count('id', filter=Q(exitoso=False))
    ).order_by('dia')
    
    # Eventos de seguridad por tipo
    eventos_por_tipo = SecurityLog.objects.filter(
        fecha__gte=hace_n_dias
    ).values('tipo_evento').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Usuarios más activos
    usuarios_activos = SecurityLog.objects.filter(
        fecha__gte=hace_n_dias,
        usuario__isnull=False
    ).values(
        'usuario__email', 'usuario__first_name', 'usuario__last_name'
    ).annotate(
        total_eventos=Count('id')
    ).order_by('-total_eventos')[:10]
    
    data = {
        'intentos_por_dia': list(intentos_por_dia),
        'eventos_por_tipo': list(eventos_por_tipo),
        'usuarios_activos': list(usuarios_activos),
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin_or_director)
def blocked_accounts_list(request):
    """
    Lista de cuentas actualmente bloqueadas
    """
    # Obtener cuentas bloqueadas
    blocked_emails = LoginAttempt.get_blocked_accounts(max_attempts=5, block_minutes=15)
    
    # Obtener información adicional de cada cuenta
    blocked_accounts = []
    for email in blocked_emails:
        # Obtener usuario si existe
        user = CustomUser.objects.filter(email=email).first()
        
        # Contar intentos fallidos recientes
        hace_15min = timezone.now() - timedelta(minutes=15)
        intentos_fallidos = LoginAttempt.objects.filter(
            email=email,
            exitoso=False,
            fecha__gte=hace_15min
        ).count()
        
        # Último intento fallido
        ultimo_intento = LoginAttempt.objects.filter(
            email=email,
            exitoso=False,
            fecha__gte=hace_15min
        ).order_by('-fecha').first()
        
        blocked_accounts.append({
            'email': email,
            'user': user,
            'intentos_fallidos': intentos_fallidos,
            'ultimo_intento': ultimo_intento,
            'tiempo_restante': calcular_tiempo_restante(ultimo_intento.fecha) if ultimo_intento else None
        })
    
    context = {
        'titulo': 'Cuentas Bloqueadas',
        'blocked_accounts': blocked_accounts,
        'total_bloqueadas': len(blocked_accounts),
    }
    
    return render(request, 'seguridad/blocked_accounts_list.html', context)


@login_required
@user_passes_test(is_admin_or_director)
def unblock_account(request, email):
    """
    Desbloquea una cuenta específica
    """
    if request.method == 'POST':
        try:
            # Desbloquear cuenta
            count = LoginAttempt.unblock_account(email)
            
            # Registrar evento de seguridad
            SecurityLog.log_event(
                tipo_evento='ACCOUNT_UNLOCKED',
                descripcion=f'Cuenta {email} desbloqueada manualmente por {request.user.email}',
                usuario=request.user,
                email=email,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                nivel_severidad='INFO',
                metadata={
                    'admin_user': request.user.email,
                    'intentos_eliminados': count
                }
            )
            
            messages.success(
                request, 
                f'Cuenta {email} desbloqueada exitosamente. Se eliminaron {count} intento(s) fallido(s).'
            )
        except Exception as e:
            messages.error(request, f'Error al desbloquear cuenta: {str(e)}')
    
    return redirect('blocked_accounts_list')


@login_required
@user_passes_test(is_admin_or_director)
def unblock_all_accounts(request):
    """
    Desbloquea todas las cuentas bloqueadas
    """
    if request.method == 'POST':
        try:
            # Obtener cuentas bloqueadas
            blocked_emails = LoginAttempt.get_blocked_accounts(max_attempts=5, block_minutes=15)
            
            total_desbloqueados = 0
            for email in blocked_emails:
                count = LoginAttempt.unblock_account(email)
                if count > 0:
                    total_desbloqueados += 1
            
            # Registrar evento de seguridad
            SecurityLog.log_event(
                tipo_evento='ADMIN_ACTION',
                descripcion=f'{total_desbloqueados} cuentas desbloqueadas masivamente por {request.user.email}',
                usuario=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                nivel_severidad='WARNING',
                metadata={
                    'admin_user': request.user.email,
                    'cuentas_desbloqueadas': list(blocked_emails)
                }
            )
            
            messages.success(
                request, 
                f'{total_desbloqueados} cuenta(s) desbloqueada(s) exitosamente.'
            )
        except Exception as e:
            messages.error(request, f'Error al desbloquear cuentas: {str(e)}')
    
    return redirect('blocked_accounts_list')


def calcular_tiempo_restante(fecha_ultimo_intento):
    """
    Calcula el tiempo restante para el desbloqueo automático
    """
    tiempo_bloqueo = timedelta(minutes=15)
    tiempo_transcurrido = timezone.now() - fecha_ultimo_intento
    tiempo_restante = tiempo_bloqueo - tiempo_transcurrido
    
    if tiempo_restante.total_seconds() <= 0:
        return "Desbloqueado"
    
    minutos = int(tiempo_restante.total_seconds() // 60)
    segundos = int(tiempo_restante.total_seconds() % 60)
    
    return f"{minutos}min {segundos}seg"


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
