from django.urls import path

from .views import comentar, reportar, toggle_favorito, valorar

app_name = 'interactions'

urlpatterns = [
    path('<int:recurso_id>/valorar/', valorar, name='valorar'),
    path('<int:recurso_id>/comentar/', comentar, name='comentar'),
    path('<int:recurso_id>/favorito/', toggle_favorito, name='toggle_favorito'),
    path('<int:recurso_id>/reportar/', reportar, name='reportar'),
]
