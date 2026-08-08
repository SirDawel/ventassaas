"""
Comando de Django para desbloquear cuentas bloqueadas
Uso:
    python manage.py unblock_account email@example.com
    python manage.py unblock_account --all
    python manage.py unblock_account --list
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from ventasweb.models import LoginAttempt, SecurityLog, CustomUser


class Command(BaseCommand):
    help = 'Desbloquea cuentas bloqueadas por múltiples intentos fallidos de login'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            nargs='?',
            type=str,
            help='Email de la cuenta a desbloquear'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Desbloquear todas las cuentas bloqueadas'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Listar todas las cuentas bloqueadas'
        )
        parser.add_argument(
            '--attempts',
            type=int,
            default=5,
            help='Número mínimo de intentos fallidos para considerar bloqueada (default: 5)'
        )
        parser.add_argument(
            '--minutes',
            type=int,
            default=15,
            help='Ventana de tiempo en minutos para bloqueo (default: 15)'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        show_all = options.get('all')
        show_list = options.get('list')
        max_attempts = options.get('attempts')
        block_minutes = options.get('minutes')

        # Listar cuentas bloqueadas
        if show_list:
            self.list_blocked_accounts(max_attempts, block_minutes)
            return

        # Desbloquear todas las cuentas
        if show_all:
            self.unblock_all_accounts(max_attempts, block_minutes)
            return

        # Desbloquear cuenta específica
        if email:
            self.unblock_single_account(email)
            return

        # Si no se proporciona argumento, mostrar ayuda
        self.stdout.write(
            self.style.WARNING(
                'Debes proporcionar un email, --all para desbloquear todas, '
                'o --list para listar cuentas bloqueadas'
            )
        )
        self.stdout.write('\nEjemplos:')
        self.stdout.write('  python manage.py unblock_account usuario@ejemplo.com')
        self.stdout.write('  python manage.py unblock_account --all')
        self.stdout.write('  python manage.py unblock_account --list')

    def list_blocked_accounts(self, max_attempts, block_minutes):
        """Lista todas las cuentas bloqueadas"""
        self.stdout.write(
            self.style.HTTP_INFO(
                f'\n🔍 Buscando cuentas con {max_attempts}+ intentos fallidos '
                f'en los últimos {block_minutes} minutos...\n'
            )
        )

        blocked_emails = LoginAttempt.get_blocked_accounts(max_attempts, block_minutes)

        if not blocked_emails:
            self.stdout.write(self.style.SUCCESS('✓ No hay cuentas bloqueadas'))
            return

        self.stdout.write(
            self.style.WARNING(f'🔒 {len(blocked_emails)} cuenta(s) bloqueada(s):\n')
        )

        for email in blocked_emails:
            # Obtener usuario
            user = CustomUser.objects.filter(email=email).first()
            
            # Contar intentos fallidos
            intentos = LoginAttempt.get_recent_failed_attempts(email, block_minutes)
            
            # Último intento
            ultimo = LoginAttempt.objects.filter(
                email=email,
                exitoso=False
            ).order_by('-fecha').first()
            
            user_info = f" ({user.get_full_name()})" if user else ""
            fecha_info = ultimo.fecha.strftime('%Y-%m-%d %H:%M:%S') if ultimo else "N/A"
            
            self.stdout.write(
                f"  • {email}{user_info}\n"
                f"    Intentos fallidos: {intentos}\n"
                f"    Último intento: {fecha_info}\n"
            )

    def unblock_single_account(self, email):
        """Desbloquea una cuenta específica"""
        self.stdout.write(f'\n🔓 Desbloqueando cuenta: {email}...')

        # Verificar si está bloqueada
        if not LoginAttempt.is_blocked(email):
            self.stdout.write(
                self.style.WARNING(f'⚠ La cuenta {email} no está bloqueada')
            )
            return

        # Desbloquear
        count = LoginAttempt.unblock_account(email)

        # Registrar en log de seguridad
        SecurityLog.log_event(
            tipo_evento='ACCOUNT_UNLOCKED',
            descripcion=f'Cuenta desbloqueada vía comando manage.py',
            email=email,
            nivel_severidad='INFO',
            metadata={
                'intentos_eliminados': count,
                'method': 'management_command'
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Cuenta {email} desbloqueada exitosamente\n'
                f'  Se eliminaron {count} intento(s) fallido(s)'
            )
        )

    def unblock_all_accounts(self, max_attempts, block_minutes):
        """Desbloquea todas las cuentas bloqueadas"""
        self.stdout.write(
            self.style.HTTP_INFO('\n🔓 Desbloqueando todas las cuentas...\n')
        )

        blocked_emails = LoginAttempt.get_blocked_accounts(max_attempts, block_minutes)

        if not blocked_emails:
            self.stdout.write(self.style.SUCCESS('✓ No hay cuentas bloqueadas'))
            return

        self.stdout.write(
            self.style.WARNING(f'Se desbloquearán {len(blocked_emails)} cuenta(s)\n')
        )

        total_desbloqueados = 0
        for email in blocked_emails:
            count = LoginAttempt.unblock_account(email)
            if count > 0:
                total_desbloqueados += 1
                self.stdout.write(f'  ✓ {email} ({count} intentos eliminados)')

        # Registrar en log de seguridad
        SecurityLog.log_event(
            tipo_evento='ADMIN_ACTION',
            descripcion=f'{total_desbloqueados} cuentas desbloqueadas masivamente vía comando',
            nivel_severidad='WARNING',
            metadata={
                'cuentas_desbloqueadas': list(blocked_emails),
                'method': 'management_command'
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ {total_desbloqueados} cuenta(s) desbloqueada(s) exitrosamente'
            )
        )

