from django.contrib import admin

from .models import Archivo, Recurso


class ArchivoInline(admin.TabularInline):
    model = Archivo
    extra = 0
    readonly_fields = ('nombre_original', 'tipo_mime', 'tamano_bytes', 'hash_sha256', 'fecha_subida')


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'asignatura', 'autor', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tipo')
    search_fields = ('titulo', 'descripcion')
    inlines = [ArchivoInline]


@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ('nombre_original', 'recurso', 'tamano_bytes', 'hash_sha256', 'fecha_subida')
    search_fields = ('nombre_original', 'hash_sha256')
