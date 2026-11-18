from django.urls import path

from .views import RecursoCreateView, RecursoDetailView

app_name = 'resources'

urlpatterns = [
    path('publicar/', RecursoCreateView.as_view(), name='recurso_create'),
    path('<int:pk>/', RecursoDetailView.as_view(), name='recurso_detalle'),
]
