import hashlib
import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.academic.models import AnoAcademico, Asignatura, Carrera, Universidad
from apps.resources.forms import MAX_FILE_SIZE
from apps.resources.models import Archivo, Recurso
from apps.users.models import User


class ResourcesBasicTests(TestCase):
    def setUp(self):
        self.usuario = self.crear_usuario('autor-b5@example.com', 'autor-b5')
        self.otro_usuario = self.crear_usuario('otro-b5@example.com', 'otro-b5')

        universidad = Universidad.objects.create(nombre='Universidad B5', siglas='UB5')
        carrera = Carrera.objects.create(
            universidad=universidad,
            nombre='Carrera B5',
            codigo='B5',
        )
        ano = AnoAcademico.objects.create(carrera=carrera, numero=1, nombre='1º año')
        self.asignatura = Asignatura.objects.create(
            ano=ano,
            nombre='Asignatura B5',
            codigo='ASB5',
        )

        self.tempdir = tempfile.TemporaryDirectory()
        self.override = override_settings(
            MEDIA_ROOT=self.tempdir.name,
            ALLOWED_HOSTS=['testserver'],
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.tempdir.cleanup)

    def crear_usuario(self, email, username):
        usuario = User(email=email, username=username, is_active=True)
        usuario.set_password('pass12345')
        usuario.save()
        return usuario

    def crear_recurso(self, autor, titulo, estado=Recurso.Estado.APROBADO, descargas=0):
        recurso = Recurso.objects.create(
            titulo=titulo,
            descripcion='Recurso de prueba B5',
            tipo=Recurso.Tipo.APUNTE,
            asignatura=self.asignatura,
            autor=autor,
            estado=estado,
        )
        if descargas:
            Recurso.objects.filter(pk=recurso.pk).update(contador_descargas=descargas)
            recurso.refresh_from_db()
        return recurso

    def crear_archivo(self, recurso, nombre, contenido):
        archivo = Archivo.objects.create(
            recurso=recurso,
            archivo=SimpleUploadedFile(nombre, contenido, content_type='application/pdf'),
            nombre_original=nombre,
            tipo_mime='application/pdf',
            tamano_bytes=len(contenido),
            hash_sha256=hashlib.sha256(contenido).hexdigest(),
        )
        return archivo

    def publicar(self, nombre, contenido):
        return self.client.post(
            reverse('resources:recurso_create'),
            {
                'titulo': 'Publicación B5',
                'descripcion': 'Descripción de prueba',
                'tipo': Recurso.Tipo.APUNTE,
                'asignatura': self.asignatura.pk,
                'archivo': SimpleUploadedFile(nombre, contenido, content_type='application/pdf'),
            },
        )

    def test_publicacion_exitosa_crea_recurso_y_archivo(self):
        self.client.force_login(self.usuario)
        contenido = b'contenido de la publicacion'

        response = self.publicar('apunte-b5.pdf', contenido)

        self.assertEqual(response.status_code, 302)
        recurso = Recurso.objects.get(titulo='Publicación B5')
        self.assertEqual(recurso.estado, Recurso.Estado.PENDIENTE)
        self.assertEqual(recurso.autor, self.usuario)
        self.assertEqual(recurso.archivos.count(), 1)
        archivo = recurso.archivos.get()
        self.assertEqual(archivo.nombre_original, 'apunte-b5.pdf')
        self.assertEqual(archivo.tamano_bytes, len(contenido))
        self.assertEqual(archivo.hash_sha256, hashlib.sha256(contenido).hexdigest())
        self.assertTrue(os.path.exists(archivo.archivo.path))

    def test_archivo_demasiado_grande_no_crea_registros(self):
        self.client.force_login(self.usuario)

        response = self.publicar('grande-b5.pdf', b'x' * (MAX_FILE_SIZE + 1))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'El archivo supera el tamaño máximo de 20 MB.',
            str(response.context['form'].errors['archivo']),
        )
        self.assertEqual(Recurso.objects.count(), 0)
        self.assertEqual(Archivo.objects.count(), 0)
        self.assertEqual(os.listdir(self.tempdir.name), [])

    def test_extension_no_permitida_no_crea_registros(self):
        self.client.force_login(self.usuario)

        response = self.publicar('malware-b5.exe', b'contenido')

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Extensión no permitida.',
            str(response.context['form'].errors['archivo']),
        )
        self.assertEqual(Recurso.objects.count(), 0)
        self.assertEqual(Archivo.objects.count(), 0)
        self.assertEqual(os.listdir(self.tempdir.name), [])

    def test_descarga_incrementa_contador_del_recurso(self):
        contenido = b'contenido descargable'
        recurso = self.crear_recurso(self.usuario, 'Recurso descargable B5', descargas=3)
        archivo = self.crear_archivo(recurso, 'descarga-b5.pdf', contenido)
        self.client.force_login(self.usuario)

        detalle = self.client.get(reverse('resources:recurso_detalle', args=[recurso.pk]))
        self.assertContains(detalle, reverse('resources:archivo_descargar', args=[archivo.pk]))

        response = self.client.get(reverse('resources:archivo_descargar', args=[archivo.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('descarga-b5.pdf', response['Content-Disposition'])
        self.assertEqual(b''.join(response.streaming_content), contenido)
        recurso.refresh_from_db()
        self.assertEqual(recurso.contador_descargas, 4)

    def test_autor_puede_borrar_su_recurso_y_archivo(self):
        recurso = self.crear_recurso(self.usuario, 'Recurso propio B5')
        archivo = self.crear_archivo(recurso, 'propio-b5.pdf', b'propio')
        ruta = archivo.archivo.path
        self.client.force_login(self.usuario)

        response = self.client.post(reverse('resources:recurso_borrar', args=[recurso.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('core:home'))
        self.assertFalse(Recurso.objects.filter(pk=recurso.pk).exists())
        self.assertFalse(Archivo.objects.filter(pk=archivo.pk).exists())
        self.assertFalse(os.path.exists(ruta))

    def test_usuario_no_puede_borrar_recurso_ajeno(self):
        recurso = self.crear_recurso(self.usuario, 'Recurso ajeno B5', descargas=2)
        archivo = self.crear_archivo(recurso, 'ajeno-b5.pdf', b'ajeno')
        ruta = archivo.archivo.path
        self.client.force_login(self.otro_usuario)

        response = self.client.post(reverse('resources:recurso_borrar', args=[recurso.pk]))

        self.assertEqual(response.status_code, 403)
        recurso.refresh_from_db()
        archivo.refresh_from_db()
        self.assertEqual(recurso.estado, Recurso.Estado.APROBADO)
        self.assertEqual(recurso.contador_descargas, 2)
        self.assertEqual(archivo.nombre_original, 'ajeno-b5.pdf')
        self.assertTrue(os.path.exists(ruta))
