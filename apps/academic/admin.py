from django.contrib import admin

from .models import AnoAcademico, Asignatura, Carrera, Universidad

admin.site.register(Universidad)
admin.site.register(Carrera)
admin.site.register(AnoAcademico)
admin.site.register(Asignatura)
