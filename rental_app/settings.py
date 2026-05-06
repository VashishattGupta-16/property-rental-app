import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# ==============================================================================
# 1. CORE PATHS & ENVIRONMENT CONFIGURATION
# ==============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment variables from a .env file (primarily for offline development)
load_dotenv()

# ==============================================================================
# 2. SECURITY CONFIGURATION
# ==============================================================================

# Secret key used for cryptographic signing. Uses env variable in production; falls back locally.
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key")

# Security Warning: Never run with debug turned on in production!
# DJANGO_DEBUG=True locally, and DJANGO_DEBUG=False in your Render environment.
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# List of strings representing the host/domain names that this Django site can serve.
ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",")

# CSRF Trusted Origins are required for secure form submissions (e.g., login, signups) in production.
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        ""
    ).split(",") if origin
]

# Set secure session and CSRF cookies only when running in production (where DEBUG is False)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Security headers to protect against clickjacking and content-type sniffing
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ==============================================================================
# 3. APPLICATION DEFINITION
# ==============================================================================

INSTALLED_APPS = [
    # Third-party storage apps (Must be declared before django.contrib.staticfiles)
    "cloudinary_storage",
    "cloudinary",

    # Custom local app
    "tweet.apps.TweetConfig",

    # Core Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",

    # Django-allauth authentication apps
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise must be placed directly beneath SecurityMiddleware to serve files instantly
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "rental_app.urls"
WSGI_APPLICATION = "rental_app.wsgi.application"

# Site ID required by Django's site framework (used by django-allauth)
SITE_ID = 1

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "rental_app" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ==============================================================================
# 4. DATABASE CONFIGURATION (HYBRID: LOCAL VS PRODUCTION)
# ==============================================================================

if os.getenv("DATABASE_URL"):
    # PRODUCTION (Connected via the DATABASE_URL environment variable on Render)
    # Automatically parses your Supabase URI and enforces SSL connections
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=600,
            ssl_require=True
        )
    }
    # Enforce standard SSL mode to prevent Gunicorn workers from hanging on Render
    DATABASES["default"]["OPTIONS"] = {
        "sslmode": "require"
    }
else:
    # LOCAL DEVELOPMENT (Reads local PostgreSQL server; SSL disabled to prevent errors)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "rental_db",
            "USER": "postgres",
            "PASSWORD": "admin123",
            "HOST": "127.0.0.1",
            "PORT": "5432",
            "OPTIONS": {
                "sslmode": "disable"
            }
        }
    }

# ==============================================================================
# 5. USER CUSTOMIZATION & AUTHENTICATION (ALLAUTH)
# ==============================================================================

# Tells Django to use your custom user model defined in the 'tweet' app
AUTH_USER_MODEL = "tweet.CustomUser"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Default Django backend
    "allauth.account.auth_backends.AuthenticationBackend",  # Allauth-specific backend
]

# Custom allauth settings to authenticate via email instead of usernames
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"

# Setup fields matching your custom user model structure
USER_MODEL_USERNAME_FIELD = "email"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"

# Prevent automatic logging out with a simple GET request
ACCOUNT_LOGOUT_ON_GET = False

# Navigation redirects
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/rentals/"
LOGOUT_REDIRECT_URL = "/"

# ==============================================================================
# 6. CLOUDINARY MEDIA STORAGE CONFIGURATION
# ==============================================================================

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", ""),
}

# ==============================================================================
# 7. STATIC & MEDIA FILE MANAGEMENT
# ==============================================================================

# Configuration for static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Configuration for user-uploaded files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# 🌟 CUSTOM STORAGE ENGINE: Tell WhiteNoise to ignore missing map/font files during compilation
from whitenoise.storage import CompressedManifestStaticFilesStorage

class ResilientWhiteNoiseStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False  # <--- This is the magic line that ignores missing files


# Defines how static and media files are stored on disk / cloud
STORAGES = {
    "default": {
        # Media files uploaded by users go directly to Cloudinary
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        # Use our custom resilient storage instead of default strict WhiteNoise
        "BACKEND": "rental_app.settings.ResilientWhiteNoiseStorage",
    },
}

# Fallback references for older packages/compatibility
STATICFILES_STORAGE = "rental_app.settings.ResilientWhiteNoiseStorage"
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# ==============================================================================
# 8. SOCIAL SIGN-IN PROVIDERS (GOOGLE AUTH)
# ==============================================================================

# Skip the second registration form and log users in automatically on signup click
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# ==============================================================================
# 9. LOCALIZATION
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Default primary key field type for automatically created model IDs
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"