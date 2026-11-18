from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Valoracion(models.Model):
    recurso = models.ForeignKey('resources.Recurso', on_delete=models.CASCADE, related_name='valoraciones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='valoraciones')
    puntuacion = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Valoración'
        verbose_name_plural = 'Valoraciones'
        constraints = [
            models.UniqueConstraint(fields=['recurso', 'usuario'], name='una_valoracion_por_usuario'),
        ]


class Comentario(models.Model):
    recurso = models.ForeignKey('resources.Recurso', on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comentarios')
    texto = models.TextField()
    activo = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['-fecha']


class Favorito(models.Model):
    recurso = models.ForeignKey('resources.Recurso', on_delete=models.CASCADE, related_name='favoritos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritos')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        constraints = [
            models.UniqueConstraint(fields=['recurso', 'usuario'], name='un_favorito_por_usuario'),
        ]


class Reporte(models.Model):
    class Motivo(models.TextChoices):
        INCORRECTO = 'incorrecto', 'Material incorrecto'
        DUPLICADO = 'duplicado', 'Duplicado'
        DERECHOS = 'derechos', 'Derechos de autor'
        OFENSIVO = 'ofensivo', 'Contenido ofensivo'
        OTRO = 'otro', 'Otro'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        RESUELTO = 'resuelto', 'Resuelto'
        DESCARTADO = 'descartado', 'Descartado'

    recurso = models.ForeignKey('resources.Recurso', on_delete=models.CASCADE, related_name='reportes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reportes')
    motivo = models.CharField(max_length=20, choices=Motivo.choices)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-fecha']
