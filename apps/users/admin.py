from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken, OutstandingToken,
)
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'username', 'first_name', 'last_name',
        'rol', 'is_active', 'is_staff', 'date_joined',
    )
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Quitar groups y user_permissions de filter_horizontal
    filter_horizontal = ()

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Información personal', {
            'fields': ('first_name', 'last_name'),
        }),
        ('Permisos y rol', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser'),
        }),
        ('Fechas importantes', {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'password1', 'password2',
                'rol', 'is_active',
            ),
        }),
    )

    # Hacer last_login y date_joined de solo lectura
    readonly_fields = ('last_login', 'date_joined')


# Ocultar la sección de Groups del admin
admin.site.unregister(Group)

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)