from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academic.models import AnoAcademico, Asignatura, Carrera, Universidad
from apps.resources.models import Recurso
from apps.users.models import User


class MisRecursosTests(TestCase):
    def crear_usuario(self, email, username):
        usuario = User(email=email, username=username, is_active=True)
        usuario.set_password('pass12345')
        usuario.save()
        return usuario

    def crear_asignatura(self):
        universidad = Universidad.objects.create(nombre='Universidad B3', siglas='UB3')
        carrera = Carrera.objects.create(
            universidad=universidad,
            nombre='Carrera B3',
            codigo='B3',
        )
        ano = AnoAcademico.objects.create(carrera=carrera, numero=1, nombre='1º año')
        return Asignatura.objects.create(ano=ano, nombre='Asignatura B3', codigo='ASB3')

    def crear_recurso(self, autor, titulo, fecha=None):
        recurso = Recurso.objects.create(
            titulo=titulo,
            tipo=Recurso.Tipo.APUNTE,
            asignatura=self.asignatura,
            autor=autor,
        )
        if fecha:
            Recurso.objects.filter(pk=recurso.pk).update(fecha_creacion=fecha)
            recurso.refresh_from_db()
        return recurso

    def setUp(self):
        self.asignatura = self.crear_asignatura()
        self.url = reverse('resources:mis_recursos')

    def test_usuario_ve_solo_sus_recursos(self):
        yo = self.crear_usuario('yo-b3@example.com', 'yo-b3')
        otro = self.crear_usuario('otro-b3@example.com', 'otro-b3')
        mio = self.crear_recurso(yo, 'Recurso propio B3')
        ajeno = self.crear_recurso(otro, 'Recurso ajeno B3')
        self.client.force_login(yo)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, mio.titulo)
        self.assertNotContains(response, ajeno.titulo)
        self.assertNotIn(ajeno, response.context['recursos'])
        self.assertContains(response, f'href="{self.url}"')

    def test_anonimo_es_redirigido_al_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/login/'))

    def test_orden_mas_reciente_primero(self):
        usuario = self.crear_usuario('orden-b3@example.com', 'orden-b3')
        antiguo = self.crear_recurso(
            usuario,
            'Recurso antiguo B3',
            timezone.now() - timedelta(days=2),
        )
        reciente = self.crear_recurso(
            usuario,
            'Recurso reciente B3',
            timezone.now() - timedelta(days=1),
        )
        self.client.force_login(usuario)

        response = self.client.get(self.url)
        recursos = list(response.context['recursos'])

        self.assertEqual(recursos[0].pk, reciente.pk)
        self.assertEqual(recursos[1].pk, antiguo.pk)

    def test_empty_state(self):
        usuario = self.crear_usuario('vacio-b3@example.com', 'vacio-b3')
        self.client.force_login(usuario)

        response = self.client.get(self.url)

        self.assertContains(response, 'Aún no has publicado nada')

    def test_botones_editar_y_borrar_apuntan_a_urls_correctas(self):
        usuario = self.crear_usuario('botones-b3@example.com', 'botones-b3')
        recurso = self.crear_recurso(usuario, 'Recurso con botones B3')
        self.client.force_login(usuario)

        response = self.client.get(self.url)

        self.assertContains(response, reverse('resources:recurso_detalle', args=[recurso.pk]))
        self.assertContains(response, reverse('resources:recurso_editar', args=[recurso.pk]))
        self.assertContains(response, reverse('resources:recurso_borrar', args=[recurso.pk]))
        self.assertNotContains(response, 'href="#"')
