from django import template
from django.db.models import Avg

from ..forms import ComentarioForm, ReporteForm, ValoracionForm
from ..models import Comentario, Favorito, Valoracion

register = template.Library()


@register.simple_tag(takes_context=True)
def datos_interacciones(context, recurso):
    user = context.get('user')
    autenticado = bool(getattr(user, 'is_authenticated', False))

    puntuacion_usuario = context.get('puntuacion_usuario')
    es_favorito = context.get('es_favorito')
    if autenticado:
        if puntuacion_usuario is None:
            puntuacion_usuario = Valoracion.objects.filter(
                recurso=recurso, usuario=user
            ).values_list('puntuacion', flat=True).first()
        if es_favorito is None:
            es_favorito = Favorito.objects.filter(
                recurso=recurso, usuario=user
            ).exists()

    valoracion_form = context.get('valoracion_form')
    if valoracion_form is None and autenticado:
        valoracion_form = ValoracionForm(initial={'puntuacion': puntuacion_usuario})

    comentario_form = context.get('comentario_form')
    if comentario_form is None and autenticado:
        comentario_form = ComentarioForm()

    reporte_form = context.get('reporte_form')
    if reporte_form is None and autenticado:
        reporte_form = ReporteForm()

    comentarios = context.get('comentarios')
    if comentarios is None:
        comentarios = Comentario.objects.filter(
            recurso=recurso, activo=True
        ).select_related('usuario').order_by('-fecha')

    promedio = context.get('promedio')
    if promedio is None:
        promedio = getattr(recurso, 'promedio', None)
    if promedio is None:
        promedio = Valoracion.objects.filter(recurso=recurso).aggregate(
            promedio=Avg('puntuacion')
        )['promedio']

    total_valoraciones = context.get('total_valoraciones')
    if total_valoraciones is None:
        total_valoraciones = recurso.valoraciones.count()

    return {
        'promedio': promedio,
        'total_valoraciones': total_valoraciones,
        'puntuacion_usuario': puntuacion_usuario,
        'es_favorito': es_favorito,
        'comentarios': comentarios,
        'valoracion_form': valoracion_form,
        'comentario_form': comentario_form,
        'reporte_form': reporte_form,
    }
