import os

from django import forms

from apps.academic.models import Asignatura

from .models import Recurso

ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 20 * 1024 * 1024

INPUT_CLASS = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 "
    "focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
)


class RecursoForm(forms.ModelForm):
    archivo = forms.FileField(label='Archivo', required=True)

    class Meta:
        model = Recurso
        fields = ['titulo', 'descripcion', 'tipo', 'asignatura']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'descripcion': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            'tipo': forms.Select(attrs={'class': INPUT_CLASS}),
            'asignatura': forms.Select(attrs={'class': INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = True
        self.fields['tipo'].required = True
        self.fields['asignatura'].required = True
        self.fields['archivo'].required = True
        self.fields['asignatura'].queryset = Asignatura.objects.filter(activa=True).select_related(
            'ano', 'ano__carrera'
        ).order_by('ano__carrera__nombre', 'ano__numero', 'nombre')
        self.fields['archivo'].widget.attrs.update({'class': INPUT_CLASS})

    def clean_titulo(self):
        titulo = (self.cleaned_data.get('titulo') or '').strip()
        if not titulo:
            raise forms.ValidationError('Este campo es obligatorio.')
        if len(titulo) < 5:
            raise forms.ValidationError('El título debe tener al menos 5 caracteres.')
        return titulo

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            raise forms.ValidationError('Este campo es obligatorio.')
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                'Extensión no permitida. Usa: .pdf, .doc, .docx, .ppt, .pptx, .jpg, .jpeg, .png.'
            )
        if archivo.size > MAX_FILE_SIZE:
            raise forms.ValidationError('El archivo supera el tamaño máximo de 20 MB.')
        return archivo
