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
        "127.0.0.1,localhost,theresidenceco-web.onrender.com,.onrender.com",
    ).split(",")
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "https://theresidenceco-web.onrender.com",
    ).split(",")
]

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

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
    'meta',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",

    # Third Party Apps
    "cloudinary",
    "cloudinary_storage",

    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # Local Apps
    "tweet.apps.TweetConfig",
]

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
            ],
        },
    },
]

# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing. PostgreSQL is required.")

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=not DEBUG  # Enforce SSL only in production (Render)
    )
}

# =========================================================
# CACHING (REDIS)
# =========================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
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
    'aggregate-analytics-every-night': {
        'task': 'tweet.tasks.aggregate_daily_analytics',
        'schedule': 3600.0 * 24, # Run once a day
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

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_USERNAME_REQUIRED = False

ACCOUNT_LOGIN_METHODS = {
    "email",
}

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

LOGIN_REDIRECT_URL = "/rentals/"

LOGOUT_REDIRECT_URL = "/"

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
# Meta CONFIGURATION
# =========================================================

META_SITE_PROTOCOL = 'https'
META_SITE_DOMAIN = 'rentalpro-web.onrender.com'
META_DEFAULT_KEYWORDS = [
    'rentals',
    'apartments',
    'real estate',
    'homes',
]
META_USE_SITES = False

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