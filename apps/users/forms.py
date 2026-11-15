import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

INPUT_CLASS = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 "
    "focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
)


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={"class": INPUT_CLASS, "autofocus": True, "placeholder": "tu@correo.com"}
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASS}),
    )

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class RegisterForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={"class": INPUT_CLASS, "placeholder": "tu@correo.com"}
        ),
    )
    username = forms.CharField(
        label="Nombre de usuario (opcional)",
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASS}),
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASS}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ese email ya está registrado.")
        return email

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ese nombre de usuario ya está en uso.")
        return username

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned_data

    def _unique_username(self, base):
        base = re.sub(r"[^\w.@+-]", "", base)[:140] or "usuario"
        username = base
        suffix = 2
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base}{suffix}"
            suffix += 1
        return username

    def save(self):
        email = self.cleaned_data["email"]
        username = self.cleaned_data["username"] or self._unique_username(
            email.split("@")[0]
        )
        return User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data["password1"],
        )
