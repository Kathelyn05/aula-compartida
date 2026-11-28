from django import forms

from .models import Comentario, Reporte, Valoracion

INPUT_CLASS = (
    'w-full rounded-lg border border-gray-300 px-3 py-2 '
    'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200'
)

PUNTUACION_CHOICES = (
    ('', 'Selecciona una puntuación'),
    (1, '1 - Muy baja'),
    (2, '2 - Baja'),
    (3, '3 - Aceptable'),
    (4, '4 - Buena'),
    (5, '5 - Excelente'),
)


class ValoracionForm(forms.ModelForm):
    puntuacion = forms.TypedChoiceField(
        label='Puntuación',
        choices=PUNTUACION_CHOICES,
        coerce=int,
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
        error_messages={
            'required': 'Selecciona una puntuación del 1 al 5.',
            'invalid_choice': 'Elige una puntuación válida del 1 al 5.',
        },
    )

    class Meta:
        model = Valoracion
        fields = ['puntuacion']


class ComentarioForm(forms.ModelForm):
    texto = forms.CharField(
        label='Comentario',
        min_length=3,
        max_length=1000,
        widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
        error_messages={
            'required': 'Escribe un comentario.',
            'min_length': 'El comentario debe tener al menos 3 caracteres.',
            'max_length': 'El comentario no puede superar los 1000 caracteres.',
        },
    )

    class Meta:
        model = Comentario
        fields = ['texto']


class ReporteForm(forms.ModelForm):
    motivo = forms.ChoiceField(
        label='Motivo',
        choices=Reporte.Motivo.choices,
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
        error_messages={
            'required': 'Selecciona un motivo para el reporte.',
            'invalid_choice': 'Selecciona un motivo válido.',
        },
    )
    descripcion = forms.CharField(
        label='Descripción (opcional)',
        required=False,
        widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
    )

    class Meta:
        model = Reporte
        fields = ['motivo', 'descripcion']
