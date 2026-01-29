from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Prueba la creación de factura con detalle tipo mensualidad y verifica Mensualidad enlazada'

    def handle(self, *args, **options):
        from django.test import Client
        from escuelaweb.models import CustomUser, AnhoEscolar, ConceptoPago, Mensualidad
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Crear/obtener año escolar activo
        anho, _ = AnhoEscolar.objects.get_or_create(nombre='Test Anho', defaults={
            'fecha_inicio': '2025-09-01',
            'fecha_fin': '2026-06-30',
            'activo': True
        })
        if not anho.activo:
            anho.activo = True
            anho.save()

        # Crear concepto tipo mensualidad
        concepto, _ = ConceptoPago.objects.get_or_create(nombre='Mensualidad Test', defaults={
            'tipo': 'mensualidad',
            'monto': 150.00,
            'activo': True
        })

        # Crear estudiante de prueba
        estudiante_email = 'estudiante.test@example.com'
        estudiante, created = User.objects.get_or_create(email=estudiante_email, defaults={
            'first_name': 'Estudiante',
            'last_name': 'Test',
            'rol': 'Estudiante',
            'is_active': True,
        })
        if created:
            estudiante.set_password('testpass123')
            estudiante.save()

        # Crear admin y usarlo para autenticar
        admin_email = 'admin.test@example.com'
        admin, created = User.objects.get_or_create(email=admin_email, defaults={
            'first_name': 'Admin',
            'last_name': 'Test',
            'rol': 'Administrador',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        })
        if created:
            admin.set_password('adminpass')
            admin.save()

        client = Client()
        logged = client.login(username=admin_email, password='adminpass')
        print('Login admin:', logged)

        # Preparar POST para crear factura con un detalle mensual
        url = '/facturas/nueva/'
        post_data = {
            'estudiante_id_hidden': str(estudiante.id),
            'fecha_vencimiento': '',
            'observaciones': 'Prueba automatizada',
            'descuento_factura': '0',
            'impuesto': '0',
            'monto_pagado': '0',
            'metodo_pago': 'efectivo',
            'referencia_pago': '',
            'concepto_id[]': str(concepto.id),
            'articulo_id[]': '',
            'cantidad[]': '1',
            'precio[]': str(concepto.monto),
            'descuento[]': '0',
            'mes[]': '9',
            'anio[]': '2026',
        }

        response = client.post(url, post_data, follow=True, HTTP_HOST='localhost')
        print('POST status code:', response.status_code)

        # Buscar mensualidad
        m = Mensualidad.objects.filter(estudiante=estudiante, mes=9, anio=2026).first()
        if m:
            print('Mensualidad creada:', m)
            print('Estado:', m.estado, 'Factura:', getattr(m.factura, 'numero_factura', None))
        else:
            print('No se encontró Mensualidad para el estudiante/mes/anio especificado.')
        
        # Simular pago completo creando un PagoFactura y verificar que la mensualidad pase a 'pagada'
        try:
            from escuelaweb.models import PagoFactura
            factura_obj = Mensualidad.objects.filter(estudiante=estudiante, mes=9, anio=2026).first().factura
            if factura_obj:
                pago = PagoFactura.objects.create(
                    factura=factura_obj,
                    monto=factura_obj.total,
                    metodo_pago='efectivo',
                    registrado_por=admin
                )
                m_refreshed = Mensualidad.objects.get(pk=m.pk)
                print('Después del pago - Mensualidad estado:', m_refreshed.estado, 'fecha_pagado:', m_refreshed.fecha_pagado)
            else:
                print('No se encontró la factura para simular pago.')
        except Exception as e:
            print('Error al simular pago:', e)
