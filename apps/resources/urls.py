from django.urls import path

from .views import (
    DescargarArchivoView,
    MisRecursosView,
    RecursoCreateView,
    RecursoDeleteView,
    RecursoDetailView,
    RecursoUpdateView,
)

app_name = 'resources'

urlpatterns = [
    path('mis-recursos/', MisRecursosView.as_view(), name='mis_recursos'),
    path('publicar/', RecursoCreateView.as_view(), name='recurso_create'),
    path('<int:pk>/editar/', RecursoUpdateView.as_view(), name='recurso_editar'),
    path('<int:pk>/borrar/', RecursoDeleteView.as_view(), name='recurso_borrar'),
    path('archivos/<int:pk>/descargar/', DescargarArchivoView.as_view(), name='archivo_descargar'),
    path('<int:pk>/', RecursoDetailView.as_view(), name='recurso_detalle'),
]
