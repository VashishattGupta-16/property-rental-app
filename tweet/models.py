import os
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.crypto import get_random_string

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
# USER MANAGER
# =========================

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

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

    class UserType(models.TextChoices):
        BROKER = "BROKER", "Broker"
        OWNER = "OWNER", "Owner"
        SEEKER = "SEEKER", "Looking for Property"

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

    user_type = models.CharField(
        max_length=50,
        choices=UserType.choices,
        blank=True,
        null=True
    )

    address = models.TextField(blank=True, null=True)
    current_location = models.CharField(max_length=255, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def profile_is_complete(self):
        return all([
            self.first_name,
            self.last_name,
            self.phone_number,
            self.user_type,
            self.address,
            self.current_location,
        ])


# =========================
# PROPERTY SHARE (FIXED LOCATION)
# =========================

class PropertyShare(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="property_shares"
    )

    property = models.ForeignKey(
        'Rental',
        on_delete=models.CASCADE,
        related_name="shares"
    )

    class Platform(models.TextChoices):
        WHATSAPP = "WHATSAPP", "WhatsApp"
        FACEBOOK = "FACEBOOK", "Facebook"
        TWITTER = "TWITTER", "Twitter"
        COPY = "COPY", "Copy Link"
        DIRECT = "DIRECT", "Direct"

    platform = models.CharField(
        max_length=20,
        choices=Platform.choices
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property.title} → {self.platform}"


# =========================
# PROPERTY LEAD
# =========================

class PropertyLead(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="property_leads"
    )

    property = models.ForeignKey(
        'Rental',
        on_delete=models.CASCADE,
        related_name="leads"
    )

    source = models.CharField(max_length=50)  # whatsapp, facebook, direct
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    converted = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property.title} → {self.source}"


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

    image = models.ImageField(
        upload_to='rentals/',
        storage=MediaCloudinaryStorage(),
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
# RENTAL GALLERY
# =========================

class RentalImage(models.Model):
    rental = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name="gallery"
    )

    image = models.ImageField(
        upload_to='rental_gallery/',
        storage=MediaCloudinaryStorage()
    )

    def __str__(self):
        return f"Image for {self.rental.title}"


# =========================
# WISHLIST
# =========================

class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    rental = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name="saved_by"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'rental')

    def __str__(self):
        return f"{self.user} → {self.rental}"