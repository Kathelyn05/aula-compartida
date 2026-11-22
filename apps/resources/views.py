import hashlib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.db.models import Avg, F
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView

from .forms import RecursoForm
from .models import Archivo, Recurso


def calcular_hash_sha256(uploaded_file):
    sha = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        sha.update(chunk)
    uploaded_file.seek(0)
    return sha.hexdigest()


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
                    estado=Recurso.Estado.APROBADO,
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
