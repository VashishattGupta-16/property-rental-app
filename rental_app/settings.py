import os
from pathlib import Path

import cloudinary
import dj_database_url
from dotenv import load_dotenv

# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def normalize_domain(value):
    value = (value or "").strip()
    value = value.removeprefix("https://").removeprefix("http://")
    return value.rstrip("/")


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key")

DEBUG = env_bool("DJANGO_DEBUG", True)

if not DEBUG and SECRET_KEY == "django-insecure-dev-key":
    raise ValueError(
        "The SECRET_KEY setting must be set to a unique, secret value in production. "
        "Please set the SECRET_KEY environment variable."
    )

PUBLIC_SITE_DOMAIN = normalize_domain(
    os.getenv("DJANGO_SITE_DOMAIN")
    or os.getenv("RENDER_EXTERNAL_HOSTNAME")
    or ("localhost:8000" if DEBUG else "rentalpro-web.onrender.com")
)

PUBLIC_SITE_URL = (
    f"http://{PUBLIC_SITE_DOMAIN}" if DEBUG else f"https://{PUBLIC_SITE_DOMAIN}"
)

CANONICAL_HOST = normalize_domain(
    os.getenv("DJANGO_CANONICAL_HOST") or PUBLIC_SITE_DOMAIN
)

ENFORCE_CANONICAL_HOST = env_bool("DJANGO_ENFORCE_CANONICAL_HOST", not DEBUG)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        f"127.0.0.1,localhost,{PUBLIC_SITE_DOMAIN.split(':')[0]},.onrender.com,rentalpro-web.onrender.com",
    ).split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        f"http://127.0.0.1:8000,http://localhost:8000,http://{PUBLIC_SITE_DOMAIN},https://*.onrender.com,https://rentalpro-web.onrender.com",
    ).split(",")
    if origin.strip()
]

# =========================================================
# SESSION & COOKIE SETTINGS  ← FIXED
# =========================================================

# Always use database-backed sessions (reliable for OAuth state)
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Keep session alive across requests
SESSION_SAVE_EVERY_REQUEST = True

# 1 day session lifetime
SESSION_COOKIE_AGE = 86400

# "Lax" is CRITICAL — "Strict" breaks OAuth redirects from Google
SESSION_COOKIE_SAMESITE = "Lax"

# Must be False for local http:// development
SESSION_COOKIE_SECURE = False if DEBUG else True

# Prevent JS from reading session cookie
SESSION_COOKIE_HTTPONLY = True

# Do NOT set a cookie domain for local dev — None means current host only
SESSION_COOKIE_DOMAIN = os.getenv("DJANGO_SESSION_COOKIE_DOMAIN") or None

# CSRF settings
CSRF_COOKIE_SECURE = False if DEBUG else True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_DOMAIN = os.getenv("DJANGO_CSRF_COOKIE_DOMAIN") or SESSION_COOKIE_DOMAIN

SECURE_SSL_REDIRECT = not DEBUG

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =========================================================
# INSTALLED APPS
# =========================================================

INSTALLED_APPS = [
    # Django Apps
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",       # ← Required for session storage
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",          # ← Required for allauth Site model
    "django.contrib.postgres",

    # Third Party Apps
    "cloudinary",
    "cloudinary_storage",
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "widget_tweaks",

    # Local Apps
    "tweet.apps.TweetConfig",
]

JAZZMIN_SETTINGS = {
    "site_title": "RentalPro Admin",
    "site_header": "RentalPro",
    "site_brand": "RentalPro",
    "welcome_sign": "Welcome to Rental Dashboard",
    "show_sidebar": True,
    "navigation_expanded": True,
}

# =========================================================
# MIDDLEWARE  ← ORDER MATTERS
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",  # ← 2nd, before everything
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "tweet.middleware.ProfileCompletionMiddleware",
]

# =========================================================
# URLS & WSGI
# =========================================================

ROOT_URLCONF = "rental_app.urls"

WSGI_APPLICATION = "rental_app.wsgi.application"

# Must match the Site entry in Django Admin → Sites
SITE_ID = 1

# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "rental_app" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # ← Required by allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tweet.context_processors.base_template",
            ],
        },
    },
]

# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL must be set for PostgreSQL. "
        "Configure DATABASE_URL in your environment or .env file."
    )

DEFAULT_CONN_MAX_AGE = int(
    os.getenv("DJANGO_CONN_MAX_AGE", "0" if DEBUG else "600")
)

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=DEFAULT_CONN_MAX_AGE,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# =========================================================
# CACHING
# =========================================================

if os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }

# =========================================================
# CORS
# =========================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
]

# =========================================================
# CUSTOM USER MODEL
# =========================================================

AUTH_USER_MODEL = "tweet.CustomUser"

# =========================================================
# AUTHENTICATION BACKENDS
# =========================================================

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
}

# =========================================================
# DJANGO ALLAUTH  ← FIXED
# =========================================================

ACCOUNT_AUTHENTICATION_METHOD = "email"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http" if DEBUG else "https"

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_USERNAME_REQUIRED = False

ACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_UNIQUE_EMAIL = True

ACCOUNT_USER_MODEL_USERNAME_FIELD = None

ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"

LOGIN_URL = "/accounts/login/"

LOGIN_REDIRECT_URL = "/rentals/"

LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_ON_GET = True

# =========================================================
# GOOGLE OAUTH  ← FIXED (PKCE DISABLED)
# =========================================================

SOCIALACCOUNT_ADAPTER = "tweet.adapters.SocialAccountAdapter"

SOCIALACCOUNT_QUERY_EMAIL = True

# Setting to False ensures new users see the signup form before account creation
SOCIALACCOUNT_AUTO_SIGNUP = True

SOCIALACCOUNT_EMAIL_REQUIRED = True

SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

# Skip the "Do you want to connect?" confirmation page
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True

SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_STORE_TOKENS = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        # ↓ PKCE DISABLED — PKCE stores code_verifier in session.
        #   If the session is not persisted between the login redirect
        #   and the Google callback (common with service workers or
        #   cookie issues), PKCE verification fails with "unknown" error.
        #   Keep False for local dev; re-enable only after confirming
        #   sessions are stable in production.
        "OAUTH_PKCE_ENABLED": False,
    }
}

# Enable verbose logging for socialaccount flows to aid debugging (prints by adapter)
SOCIALACCOUNT_LOGGING = True

WHITENOISE_MANIFEST_STRICT = False

# =========================================================
# CLOUDINARY
# =========================================================

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    "SECURE": True,
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
    api_key=CLOUDINARY_STORAGE["API_KEY"],
    api_secret=CLOUDINARY_STORAGE["API_SECRET"],
    secure=True,
)

# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STORAGES = {
    # Media → Cloudinary
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    # Static → WhiteNoise
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# =========================================================
# MEDIA FILES
# =========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# =========================================================
# DEFAULT AUTO FIELD
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =========================================================
# LOGGING
# =========================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
        
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
        }
    },
    "filters": {
        "ignore_uptimerobot": {
            "()": "rental_app.log_filters.UptimeRobotFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["ignore_uptimerobot"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}