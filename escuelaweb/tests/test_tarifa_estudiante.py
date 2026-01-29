from django.test import TestCase, Client
from django.urls import reverse
from escuelaweb.models import CustomUser, ConceptoPago, TarifaEstudiante

class TarifaEstudianteCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_user(
            email='admin@example.com',
            password='pass1234',
            first_name='Admin',
            last_name='User',
            rol='Administrador',
            is_staff=True,
            is_superuser=True,
        )
        self.student = CustomUser.objects.create_user(
            email='est@example.com',
            password='pass1234',
            first_name='Est',
            last_name='Student',
            rol='Estudiante',
        )
        self.concepto = ConceptoPago.objects.create(nombre='Mensualidad Base', tipo='mensualidad', monto='100.00')
        self.client.login(username='admin@example.com', password='pass1234')

    def test_create_tarifa(self):
        resp = self.client.post(reverse('tarifa_create'), {
            'estudiante': self.student.id,
            'tipo': 'mensualidad',
            'concepto': self.concepto.id,
            'monto': '150.00',
            'activo': 'on'
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(TarifaEstudiante.objects.filter(estudiante=self.student, tipo='mensualidad').exists())

    def test_list_tarifas(self):
        TarifaEstudiante.objects.create(estudiante=self.student, tipo='mensualidad', concepto=self.concepto, monto='150.00')
        resp = self.client.get(reverse('tarifas_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Mensualidad')

    def test_edit_tarifa(self):
        t = TarifaEstudiante.objects.create(estudiante=self.student, tipo='mensualidad', concepto=self.concepto, monto='150.00')
        resp = self.client.post(reverse('tarifa_edit', args=[t.pk]), {
            'estudiante': self.student.id,
            'tipo': 'mensualidad',
            'concepto': self.concepto.id,
            'monto': '200.00',
            'activo': 'on'
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        t.refresh_from_db()
        self.assertEqual(str(t.monto), '200.00')

    def test_delete_tarifa(self):
        t = TarifaEstudiante.objects.create(estudiante=self.student, tipo='mensualidad', concepto=self.concepto, monto='150.00')
        resp = self.client.post(reverse('tarifa_delete', args=[t.pk]), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(TarifaEstudiante.objects.filter(pk=t.pk).exists())
