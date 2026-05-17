from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import (
    CustomUser,
    Rental,
    RentalImage,
    PropertyShare,
    PropertyLead,
)


# =========================
# USER ADMIN
# =========================

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = (
        'email',
        'phone_number',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'user_type',
        'groups',
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
        'phone_number',
    )

    ordering = ('email',)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {
            "fields": (
                "first_name",
                "last_name",
                "phone_number",
                "user_type",
                "address",
                "current_location",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "phone_number",
                "first_name",
                "last_name",
                "password1",
                "password2",
            ),
        }),
    )


# =========================
# RENTAL IMAGE INLINE
# =========================

class RentalImageInline(admin.TabularInline):
    model = RentalImage
    extra = 2


# =========================
# RENTAL ADMIN
# =========================

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    inlines = [RentalImageInline]

    list_display = (
        'title',
        'user',
        'price',
        'location',
        'property_type',
        'is_available',
        'created_at',
    )

    list_filter = (
        'property_type',
        'location',
        'is_available',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'location',
        'user__email',
    )

    prepopulated_fields = {'slug': ('title',)}

    ordering = ('-created_at',)


# =========================
# PROPERTY SHARE ADMIN
# =========================

@admin.register(PropertyShare)
class PropertyShareAdmin(admin.ModelAdmin):
    list_display = (
        'property',
        'user',
        'platform',
        'created_at',
    )

    list_filter = (
        'platform',
        'created_at',
    )

    search_fields = (
        'property__title',
        'user__email',
    )

    ordering = ('-created_at',)


# =========================
# PROPERTY LEAD ADMIN
# =========================

@admin.register(PropertyLead)
class PropertyLeadAdmin(admin.ModelAdmin):
    list_display = (
        'property',
        'user',
        'source',
        'ip_address',
        'converted',
        'clicked_at',
    )

    list_filter = (
        'source',
        'converted',
        'clicked_at',
    )

    search_fields = (
        'property__title',
        'user__email',
        'ip_address',
    )

    ordering = ('-clicked_at',)


# =========================
# USER REGISTRATION
# =========================

admin.site.register(CustomUser, CustomUserAdmin)