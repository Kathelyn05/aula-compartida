from django.db import models
from django.conf import settings


class Recurso(models.Model):
    class Tipo(models.TextChoices):
        APUNTE = 'apunte', 'Apuntes y resúmenes'
        EJERCICIO = 'ejercicio', 'Ejercicios resueltos'
        LIBRO = 'libro', 'Libros y documentos'
        EXAMEN = 'examen', 'Exámenes anteriores'
        VIDEOCLASE = 'videoclase', 'Videoclase (enlace)'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de revisión'
        APROBADO = 'aprobado', 'Aprobado'
        RECHAZADO = 'rechazado', 'Rechazado'
        RETIRADO = 'retirado', 'Retirado'

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    asignatura = models.ForeignKey('academic.Asignatura', on_delete=models.PROTECT, related_name='recursos')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recursos')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.APROBADO)
    url_externa = models.URLField(blank=True, help_text='Solo para videoclases')
    contador_descargas = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado', 'asignatura']),
            models.Index(fields=['-fecha_creacion']),
        ]

    def __str__(self):
        return self.titulo


class Archivo(models.Model):
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='recursos/%Y/%m/')
    nombre_original = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=100, blank=True)
    tamano_bytes = models.BigIntegerField(default=0)
    hash_sha256 = models.CharField(max_length=64, db_index=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Archivo'
        verbose_name_plural = 'Archivos'
        constraints = [
            models.UniqueConstraint(fields=['recurso', 'hash_sha256'], name='archivo_unico_por_recurso'),
        ]

    def __str__(self):
        return self.nombre_original
