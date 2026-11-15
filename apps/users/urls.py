from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm
from .views import HomeView, RegisterView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
]
