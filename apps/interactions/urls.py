from django.urls import path

from .views import borrar_comentario, comentar, reportar, toggle_favorito, valorar

app_name = 'interactions'

urlpatterns = [
    path('<int:recurso_id>/valorar/', valorar, name='valorar'),
    path('<int:recurso_id>/comentar/', comentar, name='comentar'),
    path('comentarios/<int:comentario_id>/borrar/', borrar_comentario, name='comentario_borrar'),
    path('<int:recurso_id>/favorito/', toggle_favorito, name='toggle_favorito'),
    path('<int:recurso_id>/reportar/', reportar, name='reportar'),
]
