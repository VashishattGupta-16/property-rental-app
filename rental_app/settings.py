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

    return value.lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-dev-key",
)

DEBUG = env_bool(
    "DJANGO_DEBUG",
    True,
)

if not DEBUG and SECRET_KEY == "django-insecure-dev-key":
    raise ValueError(
        "The SECRET_KEY setting must be set to a unique, secret value in production. "
        "Please set the SECRET_KEY environment variable."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,rentalpro-web.onrender.com,.onrender.com,.ngrok-free.dev",
    ).split(",")
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,https://rentalpro-web.onrender.com,https://*.onrender.com,https://*.ngrok-free.dev",
    ).split(",")
]

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_SSL_REDIRECT = not DEBUG

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

# =========================================================
# INSTALLED APPS
# =========================================================

INSTALLED_APPS = [
    # Django Apps
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
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
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "tweet.middleware.UptimeRobotMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",

    # WhiteNoise
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "tweet.middleware.HtmxVaryMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Allauth
    "allauth.account.middleware.AccountMiddleware",

    # Custom Middleware
    "tweet.middleware.ProfileCompletionMiddleware",
]

# =========================================================
# URLS & WSGI
# =========================================================

ROOT_URLCONF = "rental_app.urls"

WSGI_APPLICATION = "rental_app.wsgi.application"

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
                "django.template.context_processors.request",
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

DATABASES = {
    "default": dj_database_url.parse(DATABASE_URL)
}

# =========================================================
# CACHING (REDIS)
# =========================================================

# Fallback to local memory cache if Redis is not available locally
if os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
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
# CELERY CONFIGURATION
# =========================================================

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True # Recommended for production

# Example periodic task schedule
CELERY_BEAT_SCHEDULE = {
    'drain-visit-buffer-every-hour': {
        'task': 'tweet.tasks.drain_visit_buffer',
        'schedule': 3600.0,  # Run every hour
    },
    'train-recommendations-daily': {
        'task': 'tweet.tasks.train_recommendation_model',
        'schedule': 3600.0 * 24,  # Run once a day
    },
}

# =========================================================
# CORS HEADERS
# =========================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
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
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': { 'anon': '100/day', 'user': '1000/day' }
}

# =========================================================
# DJANGO ALLAUTH CONFIGURATION
# =========================================================

ACCOUNT_AUTHENTICATION_METHOD = "email"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http" if DEBUG else "https"

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_USERNAME_REQUIRED = False

ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]

ACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_UNIQUE_EMAIL = True

ACCOUNT_USER_MODEL_USERNAME_FIELD = None

ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"

LOGIN_URL = "/accounts/login/"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_LOGOUT_ON_GET = True

# =========================================================
# GOOGLE AUTH
# =========================================================

SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_AUTO_SIGNUP = True

SOCIALACCOUNT_EMAIL_REQUIRED = True

SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True

SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_STORE_TOKENS = False

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "EMAIL_AUTHENTICATION": True,
        "EMAIL_AUTHENTICATION_AUTO_CONNECT": True,
        "VERIFIED_EMAIL": True,
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": True,
        "APPS": [
            {
                "client_id": os.getenv(
                    "GOOGLE_CLIENT_ID",
                    "",
                ),
                "secret": os.getenv(
                    "GOOGLE_CLIENT_SECRET",
                    "",
                ),
                "key": "",
            }
        ],
    }
}

# =========================================================
# CLOUDINARY CONFIGURATION
# =========================================================

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv(
        "CLOUDINARY_CLOUD_NAME"
    ),
    "API_KEY": os.getenv(
        "CLOUDINARY_API_KEY"
    ),
    "API_SECRET": os.getenv(
        "CLOUDINARY_API_SECRET"
    ),
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
    # Media Files -> Cloudinary
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
        ),
    },

    # Static Files -> WhiteNoise
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
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

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)

# =========================================================
# LOGGING
# =========================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": { "verbose": { "format": "%(levelname)s %(asctime)s %(module)s %(message)s" } },
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
