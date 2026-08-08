from django.core.management.base import BaseCommand
from ventasweb.models import CodigoAnulacion


class Command(BaseCommand):
    help = 'Genera el código de anulación para el mes actual'

    def handle(self, *args, **kwargs):
        codigo = CodigoAnulacion.obtener_codigo_actual()
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Código generado: {codigo.codigo} para {codigo.mes}/{codigo.anio}'
            )
        )

