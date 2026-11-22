from django.db.models import Prefetch
from django.views.generic import DetailView, ListView

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
