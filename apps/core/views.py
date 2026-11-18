import unicodedata

from django.db.models import Avg, Count, Q
from django.views.generic import ListView, TemplateView

from apps.academic.models import AnoAcademico, Asignatura, Carrera
from apps.resources.models import Recurso


def _normalizar(texto):
    if not texto:
        return ''
    texto = str(texto).lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['recursos_recientes'] = (
            Recurso.objects
            .filter(estado=Recurso.Estado.APROBADO)
            .select_related('asignatura', 'asignatura__ano', 'asignatura__ano__carrera', 'autor')
            .annotate(promedio=Avg('valoraciones__puntuacion'))
            .order_by('-fecha_creacion')[:6]
        )

        ctx['carreras'] = Carrera.objects.filter(activa=True).select_related('universidad')

        ctx['asignaturas_destacadas'] = (
            Asignatura.objects
            .filter(activa=True)
            .select_related('ano', 'ano__carrera')
            .annotate(num_recursos=Count('recursos'))
            .order_by('-num_recursos')[:6]
        )

        return ctx


class RecursoListView(ListView):
    model = Recurso
    template_name = 'search.html'
    context_object_name = 'recursos'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Recurso.objects
            .filter(estado=Recurso.Estado.APROBADO)
            .select_related('asignatura', 'asignatura__ano', 'asignatura__ano__carrera', 'autor')
            .annotate(promedio=Avg('valoraciones__puntuacion'))
        )

        carrera_id = self.request.GET.get('carrera', '').strip()
        if carrera_id.isdigit():
            qs = qs.filter(asignatura__ano__carrera_id=carrera_id)

        ano_id = self.request.GET.get('ano', '').strip()
        if ano_id.isdigit():
            qs = qs.filter(asignatura__ano_id=ano_id)

        asignatura_id = self.request.GET.get('asignatura', '').strip()
        if asignatura_id.isdigit():
            qs = qs.filter(asignatura_id=asignatura_id)

        tipo = self.request.GET.get('tipo', '').strip()
        if tipo in dict(Recurso.Tipo.choices):
            qs = qs.filter(tipo=tipo)

        orden = self.request.GET.get('orden', 'recientes')
        q = self.request.GET.get('q', '').strip()
        if q:
            nq = _normalizar(q)
            resultados = [
                r for r in qs
                if nq in _normalizar(r.titulo)
                or nq in _normalizar(r.descripcion)
                or nq in _normalizar(r.asignatura.nombre)
            ]
            if orden == 'antiguos':
                resultados.sort(key=lambda r: r.fecha_creacion)
            elif orden == 'valorados':
                resultados.sort(key=lambda r: (r.promedio or 0, r.fecha_creacion), reverse=True)
            elif orden == 'descargados':
                resultados.sort(key=lambda r: (r.contador_descargas, r.fecha_creacion), reverse=True)
            else:
                resultados.sort(key=lambda r: r.fecha_creacion, reverse=True)
            return resultados

        if orden == 'antiguos':
            qs = qs.order_by('fecha_creacion')
        elif orden == 'valorados':
            qs = qs.order_by('-promedio', '-fecha_creacion')
        elif orden == 'descargados':
            qs = qs.order_by('-contador_descargas', '-fecha_creacion')
        else:
            qs = qs.order_by('-fecha_creacion')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['carreras'] = Carrera.objects.filter(activa=True)
        ctx['anos'] = AnoAcademico.objects.select_related('carrera').order_by('carrera__nombre', 'numero')
        ctx['asignaturas'] = Asignatura.objects.filter(activa=True).select_related('ano', 'ano__carrera')
        ctx['tipos'] = Recurso.Tipo.choices
        ctx['filtros'] = {
            'q': self.request.GET.get('q', ''),
            'carrera': self.request.GET.get('carrera', ''),
            'ano': self.request.GET.get('ano', ''),
            'asignatura': self.request.GET.get('asignatura', ''),
            'tipo': self.request.GET.get('tipo', ''),
            'orden': self.request.GET.get('orden', 'recientes'),
        }
        return ctx
