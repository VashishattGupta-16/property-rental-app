from django.contrib import admin
from .models import Rental, CustomUser
from django.contrib.auth.admin import UserAdmin
# Register your models here.

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Additional Info',
            {
                'fields': ('phone_number',),
            },
        ),
    )
    # Add phone_number to the add form
    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        (
            'Custom Fields',
            {
                'fields': (
                    'phone_number',
                ),
            },
        ),
    )
    list_display = ('username', 'email', 'phone_number', 'is_staff')

admin.site.register(Rental)
admin.site.register(CustomUser, CustomUserAdmin)