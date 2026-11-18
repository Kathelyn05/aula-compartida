from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.users.urls')),
    path('academic/', include('apps.academic.urls')),
    path('recursos/', include('apps.resources.urls')),
    path('interacciones/', include('apps.interactions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'AulaCompartida — Administración'
admin.site.site_title = 'AulaCompartida'
admin.site.index_title = 'Panel de administración'
