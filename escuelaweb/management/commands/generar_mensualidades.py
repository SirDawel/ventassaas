from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Genera mensualidades para todos los estudiantes usando TarifaEstudiante para el mes/anio proporcionado.'

    def add_arguments(self, parser):
        parser.add_argument('--mes', type=int, required=True, help='Mes numérico (1-12)')
        parser.add_argument('--anio', type=int, required=True, help='Año (ej. 2026)')

    def handle(self, *args, **options):
        from escuelaweb.models import TarifaEstudiante, Mensualidad, AnhoEscolar, CustomUser

        mes = options['mes']
        anio = options['anio']

        if not (1 <= mes <= 12):
            self.stderr.write('Mes inválido, debe ser entre 1 y 12')
            return

        try:
            anho_escolar = AnhoEscolar.objects.get(activo=True)
        except AnhoEscolar.DoesNotExist:
            self.stderr.write('No hay un año escolar activo.')
            return

        tarifas = TarifaEstudiante.objects.filter(activo=True)
        creadas = 0
        for tarifa in tarifas.select_related('estudiante', 'concepto'):
            estudiante = tarifa.estudiante
            # Evitar duplicados
            existe = Mensualidad.objects.filter(estudiante=estudiante, anho_escolar=anho_escolar, mes=mes, anio=anio).exists()
            if existe:
                continue

            Mensualidad.objects.create(
                estudiante=estudiante,
                anho_escolar=anho_escolar,
                mes=mes,
                anio=anio,
                concepto=tarifa.concepto,
                descripcion=tarifa.get_tipo_display(),
                monto=tarifa.monto,
                creado_por=tarifa.creado_por
            )
            creadas += 1

        self.stdout.write(f'Mensualidades creadas: {creadas} para {mes}/{anio}')
