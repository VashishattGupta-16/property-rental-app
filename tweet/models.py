from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.indexes import GinIndex
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
# USER MODEL
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


class CustomUser(AbstractUser):
    class UserType(models.TextChoices):
        BROKER = "BROKER", "Broker"
        OWNER = "OWNER", "Owner"
        SEEKER = "SEEKER", "Seeker"

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
        max_length=20,
        choices=UserType.choices,
        blank=True,
        null=True
    )

    address = models.TextField(blank=True, null=True)
    current_location = models.CharField(max_length=255, blank=True, null=True)

    terms_accepted_at = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def profile_is_complete(self) -> bool:
        return bool(
            self.first_name
            and self.last_name
            and self.phone_number
            and self.user_type
            and self.address
            and self.current_location
        )

    def __str__(self):
        return self.email


# =========================
# RENTAL
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
        INDUSTRIAL = "INDUSTRIAL_PLOT", "Industrial Plot"

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

    location = models.CharField(max_length=255, db_index=True)
    address = models.TextField(blank=True, null=True)

    property_type = models.CharField(max_length=30, choices=PropertyTypes.choices, db_index=True)

    furnishing = models.CharField(max_length=100, blank=True)
    sqft = models.PositiveIntegerField()
    floor = models.CharField(max_length=50, blank=True)
    facing = models.CharField(max_length=50, blank=True)

    is_available = models.BooleanField(default=True)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    security_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    image = models.ImageField(
        upload_to="rentals/",
        storage=MediaCloudinaryStorage(),
        validators=[validate_image_size]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_available", "-created_at"], name="rental_avail_created_idx"),
            models.Index(fields=["property_type", "is_available", "-created_at"], name="rental_type_avail_created_idx"),
            models.Index(fields=["user", "-created_at"], name="rental_user_created_idx"),
            models.Index(fields=["is_available", "price"], name="rental_avail_price_idx"),
            # Trigram search indexes (requires Postgres pg_trgm extension)
            GinIndex(fields=["title"], name="rental_title_trgm_idx", opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["location"], name="rental_location_trgm_idx", opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["description"], name="rental_desc_trgm_idx", opclasses=["gin_trgm_ops"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title + "-" + get_random_string(5))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    # Wishlist ManyToMany (added by migration 0019)
    wishlisted_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='wishlisted_rentals',
        blank=True,
    )


# =========================
# PROPERTY SHARE
# =========================

class PropertyShare(models.Model):

    class Platform(models.TextChoices):
        WHATSAPP = "WHATSAPP", "WhatsApp"
        FACEBOOK = "FACEBOOK", "Facebook"
        TWITTER = "TWITTER", "Twitter"
        COPY = "COPY", "Copy Link"
        DIRECT = "DIRECT", "Direct"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="property_shares"
    )

    property = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name="shares"
    )

    platform = models.CharField(max_length=20, choices=Platform.choices)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.property.title} → {self.platform}"


# =========================
# PROPERTY VISIT
# =========================

class PropertyVisit(models.Model):
    share = models.ForeignKey(
        PropertyShare,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="property_visits"
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Visit - {self.id}"


# =========================
# PROPERTY INQUIRY
# =========================

class PropertyInquiry(models.Model):
    visit = models.OneToOneField(
        PropertyVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiry"
    )

    property = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name="inquiries"
    )

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Inquiry - {self.name}"


# =========================
# RENTAL IMAGE
# =========================

class RentalImage(models.Model):
    rental = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name="gallery"
    )

    image = models.ImageField(
        upload_to="rental_gallery/",
        storage=MediaCloudinaryStorage()
    )


class Wishlist(models.Model):
    """
    Legacy Wishlist model (created in migration 0007). Keep for compatibility
    with existing migrations that reference `Wishlist` and `wishlist_items`.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    rental = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'rental')

    def __str__(self):
        return f"Wishlist: {self.user_id} -> {self.rental_id}"
