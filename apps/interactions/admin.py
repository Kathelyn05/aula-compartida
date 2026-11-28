from django.contrib import admin, messages
from django.utils.text import Truncator

from .models import Comentario, Favorito, Reporte, Valoracion


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'usuario', 'motivo', 'estado', 'fecha')
    list_filter = ('estado', 'motivo')
    search_fields = ('recurso__titulo', 'usuario__email')
    actions = ('marcar_como_resuelto', 'descartar')

    @admin.action(description='Marcar como resuelto')
    def marcar_como_resuelto(self, request, queryset):
        actualizados = queryset.update(estado=Reporte.Estado.RESUELTO)
        self.message_user(
            request,
            f'{actualizados} reporte(s) marcado(s) como resuelto.',
            messages.SUCCESS,
        )

    @admin.action(description='Descartar')
    def descartar(self, request, queryset):
        actualizados = queryset.update(estado=Reporte.Estado.DESCARTADO)
        self.message_user(
            request,
            f'{actualizados} reporte(s) descartado(s).',
            messages.SUCCESS,
        )


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'usuario', 'texto_truncado', 'activo', 'fecha')
    list_filter = ('activo', 'fecha')
    actions = ('desactivar', 'activar')

    @admin.action(description='Desactivar')
    def desactivar(self, request, queryset):
        actualizados = queryset.update(activo=False)
        self.message_user(
            request,
            f'{actualizados} comentario(s) desactivado(s).',
            messages.SUCCESS,
        )

    @admin.action(description='Activar')
    def activar(self, request, queryset):
        actualizados = queryset.update(activo=True)
        self.message_user(
            request,
            f'{actualizados} comentario(s) activado(s).',
            messages.SUCCESS,
        )

    def texto_truncado(self, obj):
        return Truncator(obj.texto).chars(60)

    texto_truncado.short_description = 'Texto'


@admin.register(Valoracion)
class ValoracionAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'usuario', 'puntuacion', 'fecha')
    list_filter = ('puntuacion',)


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'usuario', 'fecha')
