import os
from pathlib import Path

import cloudinary
import dj_database_url
from dotenv import load_dotenv

# =========================================================
# BASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key")
DEBUG = env_bool("DJANGO_DEBUG", default=True)

allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS")
if allowed_hosts:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = [
        "127.0.0.1",
        "localhost",
        "rentalpro-web.onrender.com",
        ".onrender.com",
    ]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "https://rentalpro-web.onrender.com",
    ).split(",")
    if o.strip()
]

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =========================================================
# APPS
# =========================================================

INSTALLED_APPS = [
    'jet',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # NOTE: django-cloudinary-storage overrides the `collectstatic` command if it
    # appears before `django.contrib.staticfiles`. Since we use Cloudinary for
    # MEDIA only, keep `staticfiles` first.
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",

    "cloudinary_storage",
    "cloudinary",

    "tweet.apps.TweetConfig",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "allauth.account.middleware.AccountMiddleware",
]

# =========================================================
# URLS
# =========================================================

ROOT_URLCONF = "rental_app.urls"
WSGI_APPLICATION = "rental_app.wsgi.application"
SITE_ID = 1

# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "rental_app" / "templates"],
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
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =========================================================
# AUTH
# =========================================================

AUTH_USER_MODEL = "tweet.CustomUser"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/rentals/"
LOGOUT_REDIRECT_URL = "/"

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
        "APPS": [
            {
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
    }
}

# =========================================================
# CLOUDINARY (MEDIA ONLY)
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
# STATIC (WHITENOISE ONLY)
# =========================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise recommends CompressedManifestStaticFilesStorage for production
# caching + compression.
STORAGES = {
    # User uploads (MEDIA) -> Cloudinary
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    # Collected static files (STATIC) -> WhiteNoise (local filesystem)
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# =========================================================
# MEDIA (PREFIX ONLY; FILES STORED IN CLOUDINARY)
# =========================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# =========================================================
# DEFAULT AUTO FIELD
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# jet
JET_SIDE_MENU_ITEMS = [
    {
        'label': 'Dashboard',
        'url': '/admin/',
        'icon': 'fa-solid fa-gauge',
        'items': [],
    },
    {
        'label': 'Rentals',
        'url': '/admin/tweet/rental/',
        'icon': 'fa-solid fa-house',
        'items': [],
    },
    {
        'label': 'Gallery Images',
        'url': '/admin/tweet/galleryimage/',
        'icon': 'fa-solid fa-image',
        'items': [],
    },
    {
        'label': 'Users',
        'url': '/admin/tweet/customuser/',
        'icon': 'fa-solid fa-users',
        'items': [],
    },
]
