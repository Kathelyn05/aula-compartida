from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Universidad(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    siglas = models.CharField(max_length=20, blank=True)
    pais = models.CharField(max_length=80, blank=True)
    ciudad = models.CharField(max_length=80, blank=True)
    activa = models.BooleanField(default=True)
    class Meta:
        verbose_name = 'Universidad'
        verbose_name_plural = 'Universidades'
        ordering = ['nombre']

    def __str__(self):
        return self.siglas or self.nombre


class Carrera(models.Model):
    universidad = models.ForeignKey(Universidad, on_delete=models.CASCADE, related_name='carreras')
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=20, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('universidad', 'nombre')
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.universidad})'


class AnoAcademico(models.Model):
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name='anos')
    numero = models.PositiveSmallIntegerField(
        help_text='Año de la carrera: 1, 2, 3, 4, 5 o 6',
        validators=[MinValueValidator(1), MaxValueValidator(6)],
    )
    nombre = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('carrera', 'numero')
        verbose_name = 'Año académico'
        verbose_name_plural = 'Años académicos'
        ordering = ['carrera', 'numero']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(numero__gte=1, numero__lte=6),
                name='anoacademico_numero_1_6',
            )
        ]

    def __str__(self):
        return f'{self.carrera.nombre} · {self.numero}º año'


class Asignatura(models.Model):
    ano = models.ForeignKey(AnoAcademico, on_delete=models.CASCADE, related_name='asignaturas')
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=20, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('ano', 'nombre')
        verbose_name = 'Asignatura'
        verbose_name_plural = 'Asignaturas'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.ano})'
