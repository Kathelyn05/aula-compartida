from django.urls import path

from .views import HomeView, RecursoListView


app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('buscar/', RecursoListView.as_view(), name='search'),
]
