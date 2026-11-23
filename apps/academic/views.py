from django.db.models import Avg, Prefetch
from django.views.generic import DetailView, ListView

from apps.resources.models import Recurso

from .models import AnoAcademico, Asignatura, Carrera


class CarreraListView(ListView):
    model = Carrera
    context_object_name = 'carreras'
    template_name = 'academic/carrera_list.html'
    queryset = (
        Carrera.objects.filter(activa=True)
        .select_related('universidad')
        .order_by('universidad__nombre', 'nombre')
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grupos = {}
        for carrera in context['carreras']:
            grupos.setdefault(carrera.universidad, []).append(carrera)
        context['grupos'] = grupos.items()
        return context


class CarreraDetailView(DetailView):
    model = Carrera
    context_object_name = 'carrera'
    template_name = 'academic/carrera_detail.html'
    queryset = Carrera.objects.filter(activa=True).select_related('universidad')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['anos'] = (
            AnoAcademico.objects.filter(carrera=self.object)
            .prefetch_related(
                Prefetch(
                    'asignaturas',
                    queryset=Asignatura.objects.filter(activa=True).order_by('nombre'),
                )
            )
            .order_by('numero')
        )
        return context


class AsignaturaDetailView(DetailView):
    model = Asignatura
    context_object_name = 'asignatura'
    template_name = 'academic/asignatura_detail.html'
    queryset = Asignatura.objects.filter(activa=True).select_related(
        'ano', 'ano__carrera', 'ano__carrera__universidad'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recursos'] = (
            Recurso.objects.filter(
                asignatura=self.object,
                estado=Recurso.Estado.APROBADO,
            )
            .select_related(
                'asignatura',
                'asignatura__ano',
                'asignatura__ano__carrera',
                'autor',
            )
            .annotate(promedio=Avg('valoraciones__puntuacion'))
            .order_by('-fecha_creacion')
        )
        return context
