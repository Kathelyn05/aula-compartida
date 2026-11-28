from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.resources.models import Recurso

from .forms import ComentarioForm, ReporteForm, ValoracionForm
from .models import Comentario, Favorito, Reporte, Valoracion


def _mostrar_errores(request, form, tag):
    for errores in form.errors.values():
        for error in errores:
            messages.error(request, error, extra_tags=tag)


@login_required
@require_POST
def valorar(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    form = ValoracionForm(request.POST)
    if not form.is_valid():
        _mostrar_errores(request, form, 'valoracion')
        return redirect('resources:recurso_detalle', pk=recurso_id)

    _, creada = Valoracion.objects.update_or_create(
        recurso=recurso,
        usuario=request.user,
        defaults={'puntuacion': form.cleaned_data['puntuacion']},
    )
    if creada:
        messages.success(request, 'Tu valoración se ha guardado.', extra_tags='valoracion')
    else:
        messages.success(request, 'Tu valoración se ha actualizado.', extra_tags='valoracion')
    return redirect('resources:recurso_detalle', pk=recurso_id)


@login_required
@require_POST
def comentar(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    form = ComentarioForm(request.POST)
    if not form.is_valid():
        _mostrar_errores(request, form, 'comentario')
        return redirect('resources:recurso_detalle', pk=recurso_id)

    Comentario.objects.create(
        recurso=recurso,
        usuario=request.user,
        texto=form.cleaned_data['texto'],
        activo=True,
    )
    messages.success(request, 'Tu comentario se ha publicado.', extra_tags='comentario')
    return redirect('resources:recurso_detalle', pk=recurso_id)


@login_required
@require_POST
def borrar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, pk=comentario_id)
    if comentario.usuario_id != request.user.pk:
        raise PermissionDenied
    recurso_id = comentario.recurso_id
    comentario.delete()
    messages.success(request, 'Comentario eliminado.')
    return redirect('resources:recurso_detalle', pk=recurso_id)


@login_required
@require_POST
def toggle_favorito(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    favorito = Favorito.objects.filter(recurso=recurso, usuario=request.user).first()
    if favorito:
        favorito.delete()
        messages.info(request, 'Eliminado de favoritos.', extra_tags='favorito')
    else:
        Favorito.objects.create(recurso=recurso, usuario=request.user)
        messages.success(request, 'Añadido a favoritos.', extra_tags='favorito')
    return redirect('resources:recurso_detalle', pk=recurso_id)


@login_required
@require_POST
def reportar(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    form = ReporteForm(request.POST)
    if not form.is_valid():
        _mostrar_errores(request, form, 'reporte')
        return redirect('resources:recurso_detalle', pk=recurso_id)

    motivo = form.cleaned_data['motivo']
    if Reporte.objects.filter(recurso=recurso, usuario=request.user, motivo=motivo).exists():
        messages.info(request, 'Ya reportaste este recurso', extra_tags='reporte')
        return redirect('resources:recurso_detalle', pk=recurso_id)

    Reporte.objects.create(
        recurso=recurso,
        usuario=request.user,
        motivo=motivo,
        descripcion=form.cleaned_data.get('descripcion', ''),
        estado=Reporte.Estado.PENDIENTE,
    )
    messages.success(request, 'Tu reporte se ha enviado.', extra_tags='reporte')
    return redirect('resources:recurso_detalle', pk=recurso_id)
