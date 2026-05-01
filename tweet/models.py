import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.utils.text import slugify
from django.db.models.signals import post_delete
from django.dispatch import receiver

# --- VALIDATORS ---
def validate_image_size(value):
    limit = 2 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 2MB.')

# --- USER MODEL ---
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "User Account"
        verbose_name_plural = "User Accounts"

    def __str__(self):
        return f"{self.username} ({self.email})"

# --- RENTAL MODEL ---
class Rental(models.Model): 
    class PropertyTypes(models.TextChoices):
        HOUSE = 'HOUSE', 'House'
        APARTMENT = 'APARTMENT', 'Apartment'
        BHK1 = '1BHK', '1 BHK'
        BHK2 = '2BHK', '2 BHK'
        BHK3 = '3BHK', '3 BHK'
        PG = 'PG', 'PG / Co-Living'
        FLAT = 'FLAT', 'Flat'
        VILLA = 'VILLA', 'Villa'
        PLOT = 'PLOT', 'Residential Plot'
        SHOP = 'SHOP', 'Commercial Shop'
        OFFICE = 'OFFICE', 'Office Space'
        SHOWROOM = 'SHOWROOM', 'Showroom / SCO'
        INDUS_BUILDING = 'INDUS_BUILDING', 'Industrial Building'
        INDUS_PLOT = 'INDUS_PLOT', 'Industrial Plot'

    class Furnishing(models.TextChoices):
        FULLY_FURNISHED = 'FULLY-FURNISHED', 'Fully-Furnished'
        SEMI_FURNISHED = 'SEMI-FURNISHED', 'Semi-Furnished'
        UNFURNISHED = 'UNFURNISHED', 'Unfurnished'

    # Core Logic & Ownership
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='rentals'
    )
    title = models.CharField(max_length=150, verbose_name="Property Title")
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True) 
    description = models.TextField(verbose_name="Property Description")
    contact = models.CharField(max_length=15, verbose_name="Contact Number")
    # Financials (Optimized for search)
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        db_index=True,
        validators=[MinValueValidator(1.00)]
    )
    security_deposit = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        default=0.00
    )
    
    # Location
    location = models.CharField(max_length=255, db_index=True, verbose_name="City/Area")
    address = models.TextField(blank=True, null=True, verbose_name="Full Address")

    # Property Specifications
    property_type = models.CharField(
        max_length=50, 
        choices=PropertyTypes.choices, 
        default=PropertyTypes.HOUSE, 
        db_index=True
    )
    furnishing = models.CharField(
        max_length=50, 
        choices=Furnishing.choices, 
        default=Furnishing.UNFURNISHED
    )
    sqft = models.PositiveIntegerField(null=True, blank=True, verbose_name="Area (Sq. Ft)")
    bedrooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    floor = models.CharField(max_length=20, blank=True, null=True, verbose_name="Floor No.")
    facing = models.CharField(max_length=20, blank=True, null=True, verbose_name="Facing Direction")

    # Main Thumbnail
    image = models.ImageField(
        upload_to='rental_images/%Y/%m/', 
        validators=[validate_image_size, FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
        verbose_name="Main Thumbnail"
    )
    
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['price', 'property_type', 'location', 'is_available'])
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            # Create a unique-ish slug
            base_slug = slugify(f"{self.title}-{self.location}")
            self.slug = base_slug
            # Logic to ensure uniqueness can be added here if needed
        super().save(*args, **kwargs)

    def formatted_price(self):
        # Displays ₹50,000 style formatting
        return f"₹{int(self.price):,}"

    def __str__(self):
        return f"{self.title} - {self.location}"

# --- GALLERY MODEL ---
class RentalImage(models.Model):
    rental = models.ForeignKey(Rental, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='rental_gallery/%Y/%m/', 
        validators=[validate_image_size, FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
        verbose_name="Gallery Image"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gallery Photo"
        verbose_name_plural = "Gallery Photos"

# --- AUTO-DELETE FILES ON OBJECT DELETE ---
@receiver(post_delete, sender=Rental)
@receiver(post_delete, sender=RentalImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes file from filesystem when corresponding object is deleted."""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)