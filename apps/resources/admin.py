from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.db.models import Count
from django.utils.translation import ngettext

from .models import Archivo, Recurso


class ArchivoInline(admin.TabularInline):
    model = Archivo
    extra = 0
    readonly_fields = ('nombre_original', 'tipo_mime', 'tamano_bytes', 'hash_sha256', 'fecha_subida')


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'asignatura', 'autor', 'estado', 'contador_descargas', 'fecha_creacion')
    list_filter = ('estado', 'tipo', 'asignatura', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion')
    list_select_related = ('asignatura', 'autor')
    inlines = [ArchivoInline]

    @admin.action(description='Aprobar seleccionados')
    def aprobar_seleccionados(self, request, queryset):
        cantidad = queryset.update(estado=Recurso.Estado.APROBADO)
        self.message_user(
            request,
            ngettext(
                '%(count)s recurso aprobado.',
                '%(count)s recursos aprobados.',
                cantidad,
            ) % {'count': cantidad},
            messages.SUCCESS,
        )

    @admin.action(description='Rechazar seleccionados')
    def rechazar_seleccionados(self, request, queryset):
        cantidad = queryset.update(estado=Recurso.Estado.RECHAZADO)
        self.message_user(
            request,
            ngettext(
                '%(count)s recurso rechazado.',
                '%(count)s recursos rechazados.',
                cantidad,
            ) % {'count': cantidad},
            messages.SUCCESS,
        )

    @admin.action(description='Retirar seleccionados')
    def retirar_seleccionados(self, request, queryset):
        cantidad = queryset.update(estado=Recurso.Estado.RETIRADO)
        self.message_user(
            request,
            ngettext(
                '%(count)s recurso retirado.',
                '%(count)s recursos retirados.',
                cantidad,
            ) % {'count': cantidad},
            messages.SUCCESS,
        )

    actions = (
        delete_selected,
        aprobar_seleccionados,
        rechazar_seleccionados,
        retirar_seleccionados,
    )


@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ('nombre_original', 'recurso', 'tamano_bytes', 'fecha_subida')
    list_filter = ('tipo_mime',)
    search_fields = ('nombre_original', 'hash_sha256', 'recurso__titulo')

    @admin.action(description='Buscar duplicados por hash')
    def buscar_duplicados_por_hash(self, request, queryset):
        hashes = list(queryset.values_list('hash_sha256', flat=True).distinct())
        if not hashes:
            self.message_user(
                request,
                'No se encontraron archivos duplicados entre recursos diferentes.',
                messages.INFO,
            )
            return

        grupos = list(
            Archivo.objects
            .filter(hash_sha256__in=hashes)
            .values('hash_sha256')
            .annotate(total=Count('id'), recursos=Count('recurso', distinct=True))
            .filter(recursos__gt=1)
            .order_by('hash_sha256')
        )
        if not grupos:
            self.message_user(
                request,
                'No se encontraron archivos duplicados entre recursos diferentes.',
                messages.INFO,
            )
            return

        max_grupos = 5
        lineas = []
        for grupo in grupos[:max_grupos]:
            archivos = (
                Archivo.objects
                .filter(hash_sha256=grupo['hash_sha256'])
                .select_related('recurso')
                .order_by('recurso_id', 'nombre_original')
            )
            detalle = '; '.join(
                f'{archivo.nombre_original} → {archivo.recurso}' for archivo in archivos
            )
            lineas.append(
                f"{grupo['hash_sha256']} ({grupo['total']} archivos): {detalle}"
            )
        if len(grupos) > max_grupos:
            lineas.append(f'... y {len(grupos) - max_grupos} grupos más.')

        self.message_user(
            request,
            'Duplicados por hash entre recursos distintos: ' + ' | '.join(lineas),
            messages.WARNING,
        )

    actions = (delete_selected, buscar_duplicados_por_hash)
