import hashlib
import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.academic.models import AnoAcademico, Asignatura, Carrera, Universidad
from apps.resources.models import Archivo, Recurso
from apps.users.models import User


class RecursoBorradoTests(TestCase):
    tempdir = tempfile.TemporaryDirectory()
    settings_override = override_settings(
        MEDIA_ROOT=tempdir.name,
        ALLOWED_HOSTS=['testserver'],
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        cls.tempdir.cleanup()
        super().tearDownClass()

    def crear_usuario(self, email, username):
        usuario = User(email=email, username=username, is_active=True)
        usuario.set_password('pass12345')
        usuario.save()
        return usuario

    def crear_asignatura(self):
        universidad = Universidad.objects.create(nombre='Universidad Test', siglas='UT')
        carrera = Carrera.objects.create(
            universidad=universidad,
            nombre='Carrera Test',
            codigo='CT',
        )
        ano = AnoAcademico.objects.create(carrera=carrera, numero=1, nombre='1º año')
        return Asignatura.objects.create(ano=ano, nombre='Asignatura Test', codigo='AT')

    def setUp(self):
        self.autor = self.crear_usuario('autor@example.com', 'autor')
        self.asignatura = self.crear_asignatura()
        contenido = b'contenido de prueba'
        self.recurso = Recurso.objects.create(
            titulo='Recurso de prueba para borrar',
            tipo=Recurso.Tipo.APUNTE,
            asignatura=self.asignatura,
            autor=self.autor,
        )
        self.archivo = Archivo.objects.create(
            recurso=self.recurso,
            archivo=SimpleUploadedFile('prueba.pdf', contenido, content_type='application/pdf'),
            nombre_original='prueba.pdf',
            tipo_mime='application/pdf',
            tamano_bytes=len(contenido),
            hash_sha256=hashlib.sha256(contenido).hexdigest(),
        )
        self.url = reverse('resources:recurso_borrar', args=[self.recurso.pk])

    def test_autor_puede_borrar_su_recurso_y_archivo(self):
        ruta = self.archivo.archivo.path
        self.assertTrue(os.path.exists(ruta))
        self.client.force_login(self.autor)

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('core:home'))
        self.assertFalse(Recurso.objects.filter(pk=self.recurso.pk).exists())
        self.assertFalse(Archivo.objects.filter(recurso_id=self.recurso.pk).exists())
        self.assertFalse(os.path.exists(ruta))

    def test_usuario_distinto_recibe_403(self):
        intruso = self.crear_usuario('intruso@example.com', 'intruso')
        self.client.force_login(intruso)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_anonimo_es_redirigido_al_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/login/'))

    def test_confirmacion_se_muestra_antes_de_borrar(self):
        self.client.force_login(self.autor)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recurso.titulo)
        self.assertTrue(Recurso.objects.filter(pk=self.recurso.pk).exists())
