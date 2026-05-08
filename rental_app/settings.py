import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# -------------------------------------------------
# 1. BASE SETUP
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

# -------------------------------------------------
# 2. SECURITY & DOMAINS (FIXES THE 400 ERROR)
# -------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# Hardcoded Render domain to ensure handshake with the server
ALLOWED_HOSTS = [
    "rentalpro-web.onrender.com",
    "localhost",
    "127.0.0.1",
]

# Required for Django 4.0+ to allow form submissions on Render
CSRF_TRUSTED_ORIGINS = [
    "https://rentalpro-web.onrender.com"
]

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# -------------------------------------------------
# 3. APPS (SaaS-Ready Architecture)
# -------------------------------------------------
INSTALLED_APPS = [
    "cloudinary_storage",  # MUST stay at the top for media override
    "cloudinary",
    
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",

    # Custom Project Apps
    "tweet.apps.TweetConfig",

    # Authentication Suite (vassu_backup@gmail.com context)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

# -------------------------------------------------
# 4. MIDDLEWARE (WhiteNoise at Position 2)
# -------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Essential for Admin CSS
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
SITE_ID = 1

# -------------------------------------------------
# 5. TEMPLATES
# -------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# -------------------------------------------------
# 6. DATABASE (Render-Optimized)
# -------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}

# -------------------------------------------------
# 7. AUTHENTICATION & USER MODEL
# -------------------------------------------------
AUTH_USER_MODEL = "tweet.CustomUser"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/rentals/"
LOGOUT_REDIRECT_URL = "/"

# -------------------------------------------------
# 8. CLOUDINARY (Media Management)
# -------------------------------------------------
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
}

# -------------------------------------------------
# 9. STATIC & MEDIA (THE UI FIX)
# -------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Ensure local 'static' folder is checked for minimalist UI assets
STATICFILES_DIRS = [BASE_DIR / "static"]

# Legacy support strings for Cloudinary/WhiteNoise stability
STATICFILES_STORAGE = "whitenoise.storage.StaticFilesStorage"
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.StaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------
# 10. GOOGLE SOCIAL & LOCALIZATION
# -------------------------------------------------
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "key": ""
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"