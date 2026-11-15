from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .forms import RegisterForm
from .serializers import (
    ChangePasswordSerializer,
    EmailTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recursos"] = [
            {
                "tipo": "Apunte",
                "titulo": "Álgebra lineal: matrices y determinantes",
                "asignatura": "Matemática I",
                "autor": "Ana Pérez",
                "valoracion": 5,
                "estrellas": "★★★★★",
            },
            {
                "tipo": "Examen",
                "titulo": "Examen final de Programación II (2025)",
                "asignatura": "Programación II",
                "autor": "Luis García",
                "valoracion": 4,
                "estrellas": "★★★★☆",
            },
            {
                "tipo": "Libro",
                "titulo": "Introducción a los algoritmos (resumen)",
                "asignatura": "Estructuras de Datos",
                "autor": "María López",
                "valoracion": 5,
                "estrellas": "★★★★★",
            },
            {
                "tipo": "Ejercicio",
                "titulo": "Ejercicios resueltos de bases de datos",
                "asignatura": "Bases de Datos",
                "autor": "Carlos Ruiz",
                "valoracion": 4,
                "estrellas": "★★★★☆",
            },
            {
                "tipo": "Apunte",
                "titulo": "Anatomía: sistema cardiovascular",
                "asignatura": "Anatomía Humana",
                "autor": "Sofía Martínez",
                "valoracion": 5,
                "estrellas": "★★★★★",
            },
            {
                "tipo": "Examen",
                "titulo": "Preguntas de Derecho Civil I",
                "asignatura": "Derecho Civil",
                "autor": "Jorge Fernández",
                "valoracion": 3,
                "estrellas": "★★★☆☆",
            },
        ]
        context["carreras"] = [
            "Ingeniería Informática",
            "Medicina",
            "Derecho",
            "Contabilidad",
            "Ingeniería Civil",
            "Psicología",
        ]
        return context


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(
            self.request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        messages.success(
            self.request, f"¡Bienvenido a AulaCompartida, {user.username}!"
        )
        return super().form_valid(form)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginAPIView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class LogoutAPIView(APIView):
    def post(self, request):
        raw_refresh = request.data.get("refresh")
        if not raw_refresh:
            return Response(
                {"detail": "Falta el refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(raw_refresh).blacklist()
        except TokenError:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Contraseña actualizada."})
