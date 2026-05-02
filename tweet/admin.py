from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser, Rental, RentalImage


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    # List view
    list_display = (
        'email',
        'phone_number',
        'first_name',
        'last_name',
        'is_staff'
    )

    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups'
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
        'phone_number'
    )

    ordering = ('email',)

    # Change user view
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {
            "fields": ("first_name", "last_name", "phone_number")
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
        ("Important dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    # Add user view (IMPORTANT FIX HERE)
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


class RentalImageInline(admin.TabularInline):
    model = RentalImage
    extra = 3  # How many extra empty forms to display


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    inlines = [RentalImageInline]
    list_display = ('title', 'user', 'price', 'location', 'property_type', 'created_at')
    list_filter = ('property_type', 'location')
    search_fields = ('title', 'description', 'location', 'user__email')
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(CustomUser, CustomUserAdmin)