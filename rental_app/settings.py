import os
from pathlib import Path

from dotenv import load_dotenv
import dj_database_url

# ==============================================================================
# Base directory setup
# ==============================================================================

# This points to the root folder of your Django project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env during local development
load_dotenv()

# ==============================================================================
# Security settings
# ==============================================================================

# Use the environment secret key in production.
# Fallback key is only for local development.
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-dev-key"
)

# DEBUG should only be True on your local machine
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# Hosts allowed to access the project
ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",")

# Required for secure POST requests in production
# Example:
# DJANGO_CSRF_TRUSTED_ORIGINS=https://yourapp.onrender.com
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        ""
    ).split(",")
    if origin.strip()
]

# Secure cookies only in production
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Extra browser security protections
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ==============================================================================
# Installed applications
# ==============================================================================

INSTALLED_APPS = [
    # Cloudinary handles uploaded media files
    "cloudinary_storage",
    "cloudinary",

    # Your local app
    "tweet.apps.TweetConfig",

    # Default Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",

    # Authentication packages
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

# ==============================================================================
# Middleware
# ==============================================================================

MIDDLEWARE = [
    # Django security middleware
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise serves static files efficiently
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Required by django-allauth
    "allauth.account.middleware.AccountMiddleware",
]

# ==============================================================================
# URL & WSGI configuration
# ==============================================================================

ROOT_URLCONF = "rental_app.urls"

WSGI_APPLICATION = "rental_app.wsgi.application"

# Required for django-allauth
SITE_ID = 1

# ==============================================================================
# Templates
# ==============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        # Global template folders
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
# Database configuration
# ==============================================================================

# Production database (Render / Supabase / Railway etc.)
if os.getenv("DATABASE_URL"):

    DATABASES = {
        "default": dj_database_url.parse(
            os.getenv("DATABASE_URL"),
            conn_max_age=600,
            ssl_require=True,
        )
    }

    # Force SSL in production
    DATABASES["default"]["OPTIONS"] = {
        "sslmode": "require"
    }

# Local PostgreSQL database
else:

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "rental_db",
            "USER": "postgres",
            "PASSWORD": "admin123",
            "HOST": "127.0.0.1",
            "PORT": "5432",

            # Disable SSL locally to avoid:
            # "server does not support SSL"
            "OPTIONS": {
                "sslmode": "disable"
            },
        }
    }

# ==============================================================================
# Custom user model & authentication
# ==============================================================================

AUTH_USER_MODEL = "tweet.CustomUser"

AUTHENTICATION_BACKENDS = [
    # Default Django login system
    "django.contrib.auth.backends.ModelBackend",

    # django-allauth authentication
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Login using email instead of username
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"

# Match your custom user model
USER_MODEL_USERNAME_FIELD = "email"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"

# Prevent accidental logout through URL GET requests
ACCOUNT_LOGOUT_ON_GET = False

# Redirects after login/logout
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/rentals/"
LOGOUT_REDIRECT_URL = "/"

# ==============================================================================
# Cloudinary setup for uploaded media
# ==============================================================================

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", ""),
}

# ==============================================================================
# Static & media files
# ==============================================================================

# URL for static files
STATIC_URL = "/static/"

# Folder where collectstatic gathers files
STATIC_ROOT = BASE_DIR / "staticfiles"

# Additional static folder
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# User uploaded files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# IMPORTANT:
# Using CompressedStaticFilesStorage avoids
# WhiteNoise manifest errors during Render deploys.
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedStaticFilesStorage"
)

# Cloudinary stores uploaded media
DEFAULT_FILE_STORAGE = (
    "cloudinary_storage.storage.MediaCloudinaryStorage"
)

# ==============================================================================
# Google authentication
# ==============================================================================

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        },

        "SCOPE": [
            "profile",
            "email",
        ],

        "AUTH_PARAMS": {
            "access_type": "online"
        },
    }
}

# ==============================================================================
# Internationalization
# ==============================================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

# ==============================================================================
# Default primary key type
# ==============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"