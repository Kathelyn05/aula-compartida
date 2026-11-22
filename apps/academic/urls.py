from django.urls import path

from .views import CarreraDetailView, CarreraListView

app_name = 'academic'

urlpatterns = [
    path('carreras/', CarreraListView.as_view(), name='carrera_list'),
    path('carreras/<int:pk>/', CarreraDetailView.as_view(), name='carrera_detail'),
]
