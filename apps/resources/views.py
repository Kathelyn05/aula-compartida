import hashlib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Avg, F
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from .forms import RecursoForm
from .models import Archivo, Recurso


def calcular_hash_sha256(uploaded_file):
    sha = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        sha.update(chunk)
    uploaded_file.seek(0)
    return sha.hexdigest()


class RecursoEditForm(RecursoForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['archivo'].required = False
        self.fields['archivo'].help_text = 'Deja vacío para mantener el archivo actual.'

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            return None
        return super().clean_archivo()


class MisRecursosView(LoginRequiredMixin, ListView):
    model = Recurso
    template_name = 'resources/mis_recursos.html'
    context_object_name = 'recursos'

    def get_queryset(self):
        return (
            Recurso.objects
            .filter(autor=self.request.user)
            .select_related('asignatura', 'asignatura__ano', 'asignatura__ano__carrera')
            .order_by('-fecha_creacion')
        )


class RecursoCreateView(LoginRequiredMixin, View):
    template_name = 'resources/recurso_form.html'

    def get(self, request):
        form = RecursoForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RecursoForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        uploaded_file = form.cleaned_data['archivo']
        hash_sha256 = calcular_hash_sha256(uploaded_file)
        duplicado_global = Archivo.objects.filter(hash_sha256=hash_sha256).exists()

        try:
            with transaction.atomic():
                recurso = Recurso.objects.create(
                    titulo=form.cleaned_data['titulo'],
                    descripcion=form.cleaned_data.get('descripcion', ''),
                    tipo=form.cleaned_data['tipo'],
                    asignatura=form.cleaned_data['asignatura'],
                    autor=request.user,
                    estado=Recurso.Estado.PENDIENTE,
                )
                Archivo.objects.create(
                    recurso=recurso,
                    archivo=uploaded_file,
                    nombre_original=uploaded_file.name,
                    tipo_mime=getattr(uploaded_file, 'content_type', '') or '',
                    tamano_bytes=uploaded_file.size or 0,
                    hash_sha256=hash_sha256,
                )
        except IntegrityError:
            form.add_error('archivo', 'Archivo duplicado en este recurso.')
            return render(request, self.template_name, {'form': form})

        messages.success(request, 'Recurso publicado correctamente.')
        if duplicado_global:
            messages.warning(
                request,
                'Ya existe un archivo idéntico en el sistema. ¿Seguro que quieres publicarlo de nuevo?',
            )
        return redirect('core:home')


class RecursoUpdateView(LoginRequiredMixin, UpdateView):
    model = Recurso
    form_class = RecursoEditForm
    template_name = 'resources/recurso_editar.html'

    def get_object(self, queryset=None):
        recurso = super().get_object(queryset)
        if recurso.autor_id != self.request.user.pk:
            raise PermissionDenied
        return recurso

    def form_valid(self, form):
        archivo = form.cleaned_data.get('archivo')
        with transaction.atomic():
            recurso = form.save()
            if archivo:
                hash_sha256 = calcular_hash_sha256(archivo)
                archivo_anterior = recurso.archivos.first()
                if archivo_anterior:
                    archivo_anterior.archivo.delete(save=False)
                    archivo_anterior.delete()
                Archivo.objects.create(
                    recurso=recurso,
                    archivo=archivo,
                    nombre_original=archivo.name,
                    tipo_mime=getattr(archivo, 'content_type', '') or '',
                    tamano_bytes=archivo.size or 0,
                    hash_sha256=hash_sha256,
                )
        messages.success(self.request, 'Recurso actualizado correctamente')
        return redirect('resources:recurso_detalle', pk=recurso.pk)


class RecursoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Recurso
    template_name = 'resources/recurso_confirm_delete.html'
    success_url = reverse_lazy('core:home')

    def test_func(self):
        recurso = self.get_object()
        return self.request.user == recurso.autor

    def form_valid(self, form):
        for archivo in self.object.archivos.all():
            archivo.archivo.delete(save=False)
        messages.success(self.request, 'Recurso eliminado')
        return super().form_valid(form)


class RecursoDetailView(DetailView):
    model = Recurso
    template_name = 'resources/recurso_detail.html'
    context_object_name = 'recurso'

    def get_queryset(self):
        return (
            Recurso.objects
            .select_related('asignatura', 'asignatura__ano', 'asignatura__ano__carrera', 'autor')
            .prefetch_related('archivos')
            .annotate(promedio=Avg('valoraciones__puntuacion'))
        )

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Exception:
            return render(request, 'resources/recurso_no_encontrado.html', status=404)
        context = self.get_context_data(object=self.object)
        context['no_disponible'] = self.object.estado in (
            Recurso.Estado.RETIRADO,
            Recurso.Estado.RECHAZADO,
        )
        return self.render_to_response(context)


class ArchivoDownloadView(View):
    def get(self, request, pk):
        archivo = get_object_or_404(Archivo.objects.select_related('recurso'), pk=pk)
        if archivo.recurso.estado in (Recurso.Estado.RETIRADO, Recurso.Estado.RECHAZADO):
            raise Http404

        try:
            contenido = archivo.archivo.open('rb')
        except (FileNotFoundError, OSError):
            raise Http404

        Recurso.objects.filter(pk=archivo.recurso_id).update(
            contador_descargas=F('contador_descargas') + 1
        )

        return FileResponse(
            contenido,
            as_attachment=True,
            filename=archivo.nombre_original or archivo.archivo.name.split('/')[-1],
            content_type=archivo.tipo_mime or 'application/octet-stream',
        )
