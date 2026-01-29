"""
Comando para registrar automáticamente las salidas a las 4:00 PM
para estudiantes y personal que poncharon entrada pero no salida.

Uso:
    python manage.py registrar_salidas_automaticas

Para ejecutar automáticamente todos los días a las 4:00 PM, configurar
en el cron de Linux o Task Scheduler de Windows.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time
from escuelaweb.models import AsistenciaPersonal


class Command(BaseCommand):
    help = 'Registra automáticamente las salidas a las 4:00 PM para quienes no poncharon salida'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hora',
            type=str,
            default='16:00',
            help='Hora de salida automática en formato HH:MM (por defecto: 16:00)',
        )
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha específica en formato YYYY-MM-DD (por defecto: hoy)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin aplicar cambios',
        )

    def handle(self, *args, **options):
        # Obtener la hora de salida configurada
        hora_str = options['hora']
        try:
            hora_partes = hora_str.split(':')
            hora_salida = time(int(hora_partes[0]), int(hora_partes[1]))
        except (ValueError, IndexError):
            self.stdout.write(
                self.style.ERROR(f'Formato de hora inválido: {hora_str}. Use HH:MM')
            )
            return

        # Obtener la fecha
        if options['fecha']:
            from datetime import datetime
            try:
                fecha = datetime.strptime(options['fecha'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'Formato de fecha inválido: {options["fecha"]}. Use YYYY-MM-DD')
                )
                return
        else:
            fecha = timezone.localtime(timezone.now()).date()

        # Buscar registros sin hora de salida
        registros_sin_salida = AsistenciaPersonal.objects.filter(
            fecha=fecha,
            hora_entrada__isnull=False,
            hora_salida__isnull=True
        ).select_related('usuario')

        total_registros = registros_sin_salida.count()

        if total_registros == 0:
            self.stdout.write(
                self.style.WARNING(
                    f'No hay registros sin salida para la fecha {fecha}'
                )
            )
            return

        # Mostrar información
        self.stdout.write(
            self.style.SUCCESS(
                f'\nEncontrados {total_registros} registros sin salida para {fecha}'
            )
        )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n=== MODO DRY RUN - No se aplicarán cambios ===\n')
            )

        # Procesar cada registro
        for registro in registros_sin_salida:
            mensaje = (
                f'- {registro.usuario.get_full_name()} ({registro.usuario.rol}): '
                f'Entrada: {registro.hora_entrada.strftime("%H:%M")} → '
                f'Salida: {hora_salida.strftime("%H:%M")}'
            )
            self.stdout.write(mensaje)

            if not options['dry_run']:
                registro.hora_salida = hora_salida
                registro.save(update_fields=['hora_salida'])

        # Mensaje final
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'\n=== DRY RUN COMPLETADO - No se aplicaron cambios ==='
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Se registraron {total_registros} salidas automáticas a las {hora_salida.strftime("%H:%M")}'
                )
            )
