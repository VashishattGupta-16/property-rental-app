import os
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.crypto import get_random_string

# Cloudinary Imports
from cloudinary.models import CloudinaryField
from cloudinary_storage.storage import MediaCloudinaryStorage

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
# CUSTOM USER MANAGER
# =========================

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

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

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email

# =========================
# RENTAL MODEL
# =========================

class Rental(models.Model):
    class PropertyTypes(models.TextChoices):
        HOUSE = "HOUSE", "House"
        APARTMENT = "APARTMENT", "Apartment"
        BHK1 = "1BHK", "1 BHK"
        BHK2 = "2BHK", "2 BHK"
        BHK3 = "3BHK", "3 BHK"
        PG = "PG", "PG"
        VILLA = "VILLA", "Villa"
        SHOWROOM = "SHOWROOM", "Showroom"
        INDUSTRIAL_PLOT = "INDUSTRIAL_PLOT", "Industrial Plot"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rentals"
    )

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    contact = models.CharField(max_length=15, validators=[phone_validator])
    price = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    property_type = models.CharField(max_length=50, choices=PropertyTypes.choices)
    furnishing = models.CharField(max_length=100, blank=True)
    sqft = models.PositiveIntegerField()
    floor = models.CharField(max_length=50, blank=True)
    facing = models.CharField(max_length=50, blank=True)
    is_available = models.BooleanField(default=True)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    security_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Standardized ImageField for Cloudinary Storage
    image = models.ImageField(
        upload_to='rentals/', 
        storage=MediaCloudinaryStorage(), 
        null=True, 
        blank=True,
        validators=[validate_image_size]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title + "-" + get_random_string(5))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

# =========================
# RENTAL IMAGE MODEL (GALLERY)
# =========================

class RentalImage(models.Model):
    rental = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name="gallery"
    )
    # Using ImageField here for consistency across the app
    image = models.ImageField(
        upload_to='rental_gallery/', 
        storage=MediaCloudinaryStorage()
    )

    def __str__(self):
        return f"Image for {self.rental.title}"

#  whishlist
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)