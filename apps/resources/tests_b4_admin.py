import tempfile

from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.academic.models import AnoAcademico, Asignatura, Carrera, Universidad
from apps.resources.models import Archivo, Recurso
from apps.users.models import User


class B4AdminModeracionTests(TestCase):
    def setUp(self):
        self.usuario = User(email='autor-b4@example.com', username='autor-b4', is_active=True)
        self.usuario.set_password('pass12345')
        self.usuario.save()

        self.administrador = User.objects.create_superuser(
            email='admin-b4@example.com',
            username='admin-b4',
            password='pass12345',
            rol=User.Rol.ADMINISTRADOR,
        )

        universidad = Universidad.objects.create(nombre='Universidad B4', siglas='UB4')
        carrera = Carrera.objects.create(
            universidad=universidad,
            nombre='Carrera B4',
            codigo='B4',
        )
        ano = AnoAcademico.objects.create(carrera=carrera, numero=1, nombre='1º año')
        self.asignatura = Asignatura.objects.create(
            ano=ano,
            nombre='Asignatura B4',
            codigo='ASB4',
        )

        self.tempdir = tempfile.TemporaryDirectory()
        self.override = override_settings(
            MEDIA_ROOT=self.tempdir.name,
            ALLOWED_HOSTS=['testserver'],
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.tempdir.cleanup)

        self.client.force_login(self.administrador)

    def crear_recurso(self, titulo, estado=Recurso.Estado.PENDIENTE):
        return Recurso.objects.create(
            titulo=titulo,
            descripcion='Recurso de prueba B4',
            tipo=Recurso.Tipo.APUNTE,
            asignatura=self.asignatura,
            autor=self.usuario,
            estado=estado,
        )

    def crear_archivo(self, recurso, nombre, hash_sha256):
        contenido = nombre.encode('utf-8')
        return Archivo.objects.create(
            recurso=recurso,
            archivo=SimpleUploadedFile(nombre, contenido, content_type='application/pdf'),
            nombre_original=nombre,
            tipo_mime='application/pdf',
            tamano_bytes=len(contenido),
            hash_sha256=hash_sha256,
        )

    def ejecutar_accion(self, modelo, action, pks):
        return self.client.post(
            reverse(f'admin:resources_{modelo}_changelist'),
            {
                'action': action,
                '_selected_action': list(pks),
                'index': 0,
            },
            follow=True,
        )

    def test_configuracion_y_acciones_aparecen_en_admin(self):
        recurso = self.crear_recurso('Recurso para acciones B4')
        self.crear_archivo(recurso, 'acciones.pdf', 'd' * 64)
        recurso_admin = admin.site._registry[Recurso]
        archivo_admin = admin.site._registry[Archivo]

        self.assertEqual(
            recurso_admin.list_display,
            ('titulo', 'asignatura', 'autor', 'estado', 'contador_descargas', 'fecha_creacion'),
        )
        self.assertEqual(
            recurso_admin.list_filter,
            ('estado', 'tipo', 'asignatura', 'fecha_creacion'),
        )
        self.assertEqual(recurso_admin.search_fields, ('titulo', 'descripcion'))
        self.assertEqual(
            archivo_admin.list_display,
            ('nombre_original', 'recurso', 'tamano_bytes', 'fecha_subida'),
        )
        self.assertEqual(archivo_admin.list_filter, ('tipo_mime',))

        changelist_recursos = self.client.get(reverse('admin:resources_recurso_changelist'))
        for texto in ('Aprobar seleccionados', 'Rechazar seleccionados', 'Retirar seleccionados'):
            self.assertContains(changelist_recursos, texto)

        changelist_archivos = self.client.get(reverse('admin:resources_archivo_changelist'))
        self.assertContains(changelist_archivos, 'Buscar duplicados por hash')

    def test_publicacion_nueva_es_pendiente(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse('resources:recurso_create'),
            {
                'titulo': 'Recurso publicado B4',
                'descripcion': 'Debe quedar pendiente',
                'tipo': Recurso.Tipo.APUNTE,
                'asignatura': self.asignatura.pk,
                'archivo': SimpleUploadedFile('publicado.pdf', b'publicado', content_type='application/pdf'),
            },
        )

        self.assertEqual(response.status_code, 302)
        recurso = Recurso.objects.get(titulo='Recurso publicado B4')
        self.assertEqual(recurso.estado, Recurso.Estado.PENDIENTE)

    def test_admin_aprueba_uno_y_varios_recursos(self):
        primero = self.crear_recurso('Aprobar uno B4')
        segundo = self.crear_recurso('Aprobar varios 1 B4')
        tercero = self.crear_recurso('Aprobar varios 2 B4')
        titulo_original = segundo.titulo
        descargas_originales = segundo.contador_descargas

        respuesta_uno = self.ejecutar_accion(
            'recurso', 'aprobar_seleccionados', [primero.pk]
        )
        primero.refresh_from_db()
        self.assertEqual(primero.estado, Recurso.Estado.APROBADO)
        self.assertContains(respuesta_uno, '1 recurso aprobado.')

        respuesta_varios = self.ejecutar_accion(
            'recurso', 'aprobar_seleccionados', [segundo.pk, tercero.pk]
        )
        segundo.refresh_from_db()
        tercero.refresh_from_db()
        self.assertEqual(segundo.estado, Recurso.Estado.APROBADO)
        self.assertEqual(tercero.estado, Recurso.Estado.APROBADO)
        self.assertEqual(segundo.titulo, titulo_original)
        self.assertEqual(segundo.contador_descargas, descargas_originales)
        self.assertContains(respuesta_varios, '2 recursos aprobados.')

    def test_admin_rechaza_uno_y_varios_recursos(self):
        primero = self.crear_recurso('Rechazar uno B4')
        segundo = self.crear_recurso('Rechazar varios 1 B4')
        tercero = self.crear_recurso('Rechazar varios 2 B4')

        respuesta_uno = self.ejecutar_accion(
            'recurso', 'rechazar_seleccionados', [primero.pk]
        )
        primero.refresh_from_db()
        self.assertEqual(primero.estado, Recurso.Estado.RECHAZADO)
        self.assertContains(respuesta_uno, '1 recurso rechazado.')

        respuesta_varios = self.ejecutar_accion(
            'recurso', 'rechazar_seleccionados', [segundo.pk, tercero.pk]
        )
        segundo.refresh_from_db()
        tercero.refresh_from_db()
        self.assertEqual(segundo.estado, Recurso.Estado.RECHAZADO)
        self.assertEqual(tercero.estado, Recurso.Estado.RECHAZADO)
        self.assertContains(respuesta_varios, '2 recursos rechazados.')

    def test_admin_retira_uno_y_varios_recursos(self):
        primero = self.crear_recurso('Retirar uno B4')
        segundo = self.crear_recurso('Retirar varios 1 B4')
        tercero = self.crear_recurso('Retirar varios 2 B4')

        respuesta_uno = self.ejecutar_accion(
            'recurso', 'retirar_seleccionados', [primero.pk]
        )
        primero.refresh_from_db()
        self.assertEqual(primero.estado, Recurso.Estado.RETIRADO)
        self.assertTrue(Recurso.objects.filter(pk=primero.pk).exists())
        self.assertContains(respuesta_uno, '1 recurso retirado.')

        respuesta_varios = self.ejecutar_accion(
            'recurso', 'retirar_seleccionados', [segundo.pk, tercero.pk]
        )
        segundo.refresh_from_db()
        tercero.refresh_from_db()
        self.assertEqual(segundo.estado, Recurso.Estado.RETIRADO)
        self.assertEqual(tercero.estado, Recurso.Estado.RETIRADO)
        self.assertContains(respuesta_varios, '2 recursos retirados.')

    def test_estados_publicos_en_home_y_busqueda(self):
        aprobado = self.crear_recurso('Visible aprobado B4', Recurso.Estado.APROBADO)
        pendiente = self.crear_recurso('Oculto pendiente B4', Recurso.Estado.PENDIENTE)
        rechazado = self.crear_recurso('Oculto rechazado B4', Recurso.Estado.RECHAZADO)
        retirado = self.crear_recurso('Oculto retirado B4', Recurso.Estado.RETIRADO)

        for url in (reverse('core:home'), reverse('core:search')):
            respuesta = self.client.get(url)
            self.assertContains(respuesta, aprobado.titulo)
            self.assertNotContains(respuesta, pendiente.titulo)
            self.assertNotContains(respuesta, rechazado.titulo)
            self.assertNotContains(respuesta, retirado.titulo)

    def test_duplicados_por_hash_entre_recursos_diferentes(self):
        primero = self.crear_recurso('Recurso hash uno B4', Recurso.Estado.APROBADO)
        segundo = self.crear_recurso('Recurso hash dos B4', Recurso.Estado.APROBADO)
        tercero = self.crear_recurso('Recurso hash unico B4', Recurso.Estado.APROBADO)
        hash_duplicado = 'a' * 64
        archivo_uno = self.crear_archivo(primero, 'duplicado_uno.pdf', hash_duplicado)
        archivo_dos = self.crear_archivo(segundo, 'duplicado_dos.pdf', hash_duplicado)
        archivo_unico = self.crear_archivo(tercero, 'unico.pdf', 'b' * 64)

        respuesta = self.ejecutar_accion(
            'archivo', 'buscar_duplicados_por_hash', [archivo_uno.pk]
        )

        self.assertContains(respuesta, hash_duplicado)
        self.assertContains(respuesta, 'duplicado_uno.pdf')
        self.assertContains(respuesta, 'duplicado_dos.pdf')
        self.assertContains(respuesta, primero.titulo)
        self.assertContains(respuesta, segundo.titulo)
        self.assertContains(respuesta, '2 archivos')
        mensaje = ' '.join(str(item) for item in respuesta.context['messages'])
        self.assertNotIn('unico.pdf', mensaje)

        archivo_uno.refresh_from_db()
        archivo_dos.refresh_from_db()
        archivo_unico.refresh_from_db()
        self.assertEqual(archivo_uno.hash_sha256, hash_duplicado)
        self.assertEqual(archivo_dos.hash_sha256, hash_duplicado)
        self.assertEqual(Recurso.objects.count(), 3)
        self.assertEqual(Archivo.objects.count(), 3)

    def test_sin_duplicados_por_hash(self):
        recurso = self.crear_recurso('Recurso sin duplicado B4', Recurso.Estado.APROBADO)
        archivo = self.crear_archivo(recurso, 'sin_duplicado.pdf', 'c' * 64)

        respuesta = self.ejecutar_accion(
            'archivo', 'buscar_duplicados_por_hash', [archivo.pk]
        )

        self.assertContains(
            respuesta,
            'No se encontraron archivos duplicados entre recursos diferentes.',
        )
