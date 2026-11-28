import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.academic.models import AnoAcademico, Asignatura, Carrera, Universidad
from apps.resources.models import Recurso
from apps.users.models import User


class EstadoPublicacionTests(TestCase):
    def setUp(self):
        self.usuario = User(email='publicador@example.com', username='publicador', is_active=True)
        self.usuario.set_password('pass12345')
        self.usuario.save()

        universidad = Universidad.objects.create(nombre='Universidad Estado', siglas='UE')
        carrera = Carrera.objects.create(
            universidad=universidad,
            nombre='Carrera Estado',
            codigo='CE',
        )
        ano = AnoAcademico.objects.create(carrera=carrera, numero=1, nombre='1º año')
        self.asignatura = Asignatura.objects.create(
            ano=ano,
            nombre='Asignatura Estado',
            codigo='ASE',
        )

        self.tempdir = tempfile.TemporaryDirectory()
        self.override = override_settings(
            MEDIA_ROOT=self.tempdir.name,
            ALLOWED_HOSTS=['testserver'],
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.tempdir.cleanup)

        self.client.force_login(self.usuario)

    def publicar(self, titulo='Recurso de prueba estado'):
        return self.client.post(
            reverse('resources:recurso_create'),
            {
                'titulo': titulo,
                'descripcion': 'Descripción de prueba',
                'tipo': Recurso.Tipo.APUNTE,
                'asignatura': self.asignatura.pk,
                'archivo': SimpleUploadedFile('prueba.pdf', b'contenido', content_type='application/pdf'),
                'estado': Recurso.Estado.APROBADO,
            },
        )

    def test_publicacion_guarda_estado_pendiente(self):
        response = self.publicar()

        self.assertEqual(response.status_code, 302)
        recurso = Recurso.objects.get(titulo='Recurso de prueba estado')
        self.assertEqual(recurso.estado, Recurso.Estado.PENDIENTE)

    def test_pendiente_no_aparece_en_home_ni_busqueda(self):
        self.publicar('Recurso pendiente oculto')

        home = self.client.get(reverse('core:home'))
        busqueda = self.client.get(reverse('core:search'))

        self.assertNotContains(home, 'Recurso pendiente oculto')
        self.assertNotContains(busqueda, 'Recurso pendiente oculto')

    def test_usuario_no_puede_aprobar_al_editar(self):
        self.publicar('Recurso editado por autor')
        recurso = Recurso.objects.get(titulo='Recurso editado por autor')

        response = self.client.post(
            reverse('resources:recurso_editar', args=[recurso.pk]),
            {
                'titulo': 'Recurso editado por autor',
                'descripcion': 'Descripción editada',
                'tipo': Recurso.Tipo.APUNTE,
                'asignatura': self.asignatura.pk,
                'estado': Recurso.Estado.APROBADO,
            },
        )

        recurso.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(recurso.estado, Recurso.Estado.PENDIENTE)

    def test_editar_recurso_aprobado_existente_no_cambia_su_estado(self):
        recurso = Recurso.objects.create(
            titulo='Recurso aprobado existente',
            tipo=Recurso.Tipo.APUNTE,
            asignatura=self.asignatura,
            autor=self.usuario,
            estado=Recurso.Estado.APROBADO,
        )

        response = self.client.post(
            reverse('resources:recurso_editar', args=[recurso.pk]),
            {
                'titulo': 'Recurso aprobado existente',
                'descripcion': 'Descripción editada',
                'tipo': Recurso.Tipo.APUNTE,
                'asignatura': self.asignatura.pk,
                'estado': Recurso.Estado.RETIRADO,
            },
        )

        recurso.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(recurso.estado, Recurso.Estado.APROBADO)
