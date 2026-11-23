from django.contrib import admin

from .models import AnoAcademico, Asignatura, Carrera, Universidad

class AnoAcademicoInline(admin.TabularInline):
    model = AnoAcademico
    extra = 1


class AsignaturaInline(admin.TabularInline):
    model = Asignatura
    extra = 1


@admin.register(Universidad)
class UniversidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'siglas', 'pais', 'ciudad', 'activa')
    search_fields = ('nombre', 'siglas')
    list_filter = ('activa', 'pais')


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'universidad', 'activa')
    search_fields = ('nombre',)
    list_filter = ('activa', 'universidad__pais')
    inlines = [AnoAcademicoInline]


@admin.register(AnoAcademico)
class AnoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('carrera', 'numero', 'nombre')
    list_filter = ('carrera',)
    search_fields = ('nombre', 'carrera__nombre', 'carrera__universidad__nombre')
    inlines = [AsignaturaInline]


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ano', 'get_carrera', 'activa')
    list_filter = ('ano', 'ano__carrera', 'activa')
    search_fields = ('nombre', 'codigo')

    @admin.display(description='Carrera', ordering='ano__carrera')
    def get_carrera(self, obj):
        return obj.ano.carrera


from django.contrib.admin import AdminSite

_ORDENES = {
    'academic': ['Universidad', 'Carrera', 'AnoAcademico', 'Asignatura'],
    'resources': ['Recurso', 'Archivo'],
}
_get_app_list_original = AdminSite.get_app_list


def _get_app_list_ordenado(self, request, app_label=None):
    app_list = _get_app_list_original(self, request, app_label)
    for app in app_list:
        orden = _ORDENES.get(app['app_label'])
        if orden:
            app['models'].sort(
                key=lambda m: orden.index(m['object_name'])
                if m['object_name'] in orden else 999
            )
    return app_list


AdminSite.get_app_list = _get_app_list_ordenado
