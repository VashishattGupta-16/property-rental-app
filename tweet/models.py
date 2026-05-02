import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.db.models.signals import post_delete
from django.dispatch import receiver


# =========================
# VALIDATORS
# =========================

def validate_image_size(value):
    limit = 2 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise ValidationError("File too large. Max size is 2MB.")


phone_validator = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message="Enter a valid phone number (10–15 digits)."
)


# =========================
# CUSTOM USER
# =========================

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[phone_validator],
        blank=True,
        null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        if self.first_name:
            return self.first_name
        return self.email


# =========================
# RENTAL MODEL
# =========================

class Rental(models.Model):

    class PropertyTypes(models.TextChoices):
        HOUSE = 'HOUSE', 'House'
        APARTMENT = 'APARTMENT', 'Apartment'
        BHK1 = '1BHK', '1 BHK'
        BHK2 = '2BHK', '2 BHK'
        BHK3 = '3BHK', '3 BHK'
        PG = 'PG', 'PG'
        VILLA = 'VILLA', 'Villa'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rentals"
    )

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)

    description = models.TextField()

    contact = models.CharField(
        max_length=15,
        validators=[phone_validator]   # ✅ FIXED
    )

    price = models.DecimalField(max_digits=12, decimal_places=2)

    location = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)

    property_type = models.CharField(max_length=50, choices=PropertyTypes.choices)

    # Fields from form that were missing in model
    furnishing = models.CharField(max_length=100, blank=True)
    sqft = models.PositiveIntegerField()
    floor = models.CharField(max_length=50, blank=True)
    facing = models.CharField(max_length=50, blank=True)

    image = models.ImageField(upload_to="rental_images/%Y/%m/")

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title + "-" + get_random_string(5))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# =========================
# RENTAL IMAGE MODEL
# =========================

class RentalImage(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(
        upload_to="rental_gallery/%Y/%m/",
        validators=[validate_image_size]
    )

    def __str__(self):
        return f"Image for {self.rental.title}"


# =========================
# DELETE FILES AUTO
# =========================

@receiver(post_delete, sender=Rental)
def delete_rental_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(post_delete, sender=RentalImage)
def delete_rental_gallery_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)