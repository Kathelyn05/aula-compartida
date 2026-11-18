from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
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


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("core:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
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
