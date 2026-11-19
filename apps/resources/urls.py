from django.urls import path

from .views import RecursoCreateView, RecursoDetailView, RecursoUpdateView

app_name = 'resources'

urlpatterns = [
    path('publicar/', RecursoCreateView.as_view(), name='recurso_create'),
    path('<int:pk>/editar/', RecursoUpdateView.as_view(), name='recurso_editar'),
    path('<int:pk>/', RecursoDetailView.as_view(), name='recurso_detalle'),
]
