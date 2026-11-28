from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from apps.academic.models import AnoAcademico, Asignatura, Carrera, Universidad
from apps.resources.models import Recurso

from .models import Comentario, Favorito, Reporte, Valoracion


class InteraccionesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='usuario',
            email='usuario@example.com',
            password='clave123',
        )
        universidad = Universidad.objects.create(nombre='Universidad de Prueba')
        carrera = Carrera.objects.create(universidad=universidad, nombre='Carrera de Prueba')
        ano = AnoAcademico.objects.create(carrera=carrera, numero=1)
        asignatura = Asignatura.objects.create(ano=ano, nombre='Asignatura de Prueba')
        cls.recurso = Recurso.objects.create(
            titulo='Recurso de prueba',
            tipo='apunte',
            asignatura=asignatura,
            autor=cls.usuario,
        )
        cls.url_valorar = reverse('interactions:valorar', args=[cls.recurso.pk])
        cls.url_comentar = reverse('interactions:comentar', args=[cls.recurso.pk])
        cls.url_favorito = reverse('interactions:toggle_favorito', args=[cls.recurso.pk])
        cls.url_reportar = reverse('interactions:reportar', args=[cls.recurso.pk])

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_detalle_muestra_formularios_utilizables(self):
        respuesta = self.client.get(reverse('resources:recurso_detalle', args=[self.recurso.pk]))
        html = respuesta.content.decode()
        self.assertIn('name="texto"', html)
        self.assertIn('name="puntuacion"', html)
        self.assertIn('<option value="1"', html)
        self.assertIn('name="motivo"', html)

    def test_dos_valoraciones_seguidas_no_crean_dos_registros(self):
        self.client.post(self.url_valorar, {'puntuacion': '4'})
        self.client.post(self.url_valorar, {'puntuacion': '2'})

        valoraciones = Valoracion.objects.filter(recurso=self.recurso, usuario=self.usuario)
        self.assertEqual(valoraciones.count(), 1)
        self.assertEqual(valoraciones.get().puntuacion, 2)

    def test_dos_toggles_dejan_el_estado_original_del_favorito(self):
        consulta = Favorito.objects.filter(recurso=self.recurso, usuario=self.usuario)
        self.assertFalse(consulta.exists())

        self.client.post(self.url_favorito)
        self.assertTrue(consulta.exists())

        self.client.post(self.url_favorito)
        self.assertFalse(consulta.exists())

    def test_comentario_desactivado_no_aparece_en_la_lista(self):
        Comentario.objects.create(
            recurso=self.recurso,
            usuario=self.usuario,
            texto='Comentario visible',
            activo=True,
        )
        Comentario.objects.create(
            recurso=self.recurso,
            usuario=self.usuario,
            texto='Comentario oculto',
            activo=False,
        )

        html = render_to_string('interactions/comentarios_lista.html', {
            'recurso': self.recurso,
            'comentarios': Comentario.objects.filter(recurso=self.recurso).order_by('-fecha'),
        })
        self.assertIn('Comentario visible', html)
        self.assertNotIn('Comentario oculto', html)

    def test_reporte_duplicado_no_se_crea(self):
        datos = {'motivo': Reporte.Motivo.DUPLICADO.value, 'descripcion': 'Primero'}
        self.client.post(self.url_reportar, datos)
        respuesta = self.client.post(
            self.url_reportar,
            {'motivo': Reporte.Motivo.DUPLICADO.value, 'descripcion': 'Segundo'},
        )

        reportes = Reporte.objects.filter(recurso=self.recurso, usuario=self.usuario)
        self.assertEqual(reportes.count(), 1)
        self.assertEqual(reportes.get().estado, Reporte.Estado.PENDIENTE)
        mensajes = [str(mensaje) for mensaje in get_messages(respuesta.wsgi_request)]
        self.assertIn('Ya reportaste este recurso', mensajes)

    def test_anonimo_es_redirigido_al_login_en_todas_las_acciones(self):
        self.client.logout()
        casos = [
            (self.url_valorar, {'puntuacion': '5'}),
            (self.url_comentar, {'texto': 'Comentario anónimo'}),
            (self.url_favorito, {}),
            (self.url_reportar, {'motivo': Reporte.Motivo.OTRO.value}),
        ]

        for url, datos in casos:
            with self.subTest(url=url):
                respuesta = self.client.post(url, datos)
                self.assertEqual(respuesta.status_code, 302)
                self.assertTrue(respuesta['Location'].startswith(reverse('login') + '?next='))

        self.assertFalse(Valoracion.objects.exists())
        self.assertFalse(Comentario.objects.exists())
        self.assertFalse(Favorito.objects.exists())
        self.assertFalse(Reporte.objects.exists())
