from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Rol(models.TextChoices):
        USUARIO = 'usuario', 'Usuario'
        MODERADOR = 'moderador', 'Moderador'
        ADMINISTRADOR = 'administrador', 'Administrador'

    email = models.EmailField("email", unique=True)
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.USUARIO,
        verbose_name='Rol',
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    @property
    def es_moderador(self):
        return self.rol in (self.Rol.MODERADOR, self.Rol.ADMINISTRADOR)

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR
