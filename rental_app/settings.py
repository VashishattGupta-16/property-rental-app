"""
RentalPro v4.8 - Optimized Production Settings
"""
import os
from pathlib import Path

# --- BASE DIRECTORY ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY ---
SECRET_KEY = 'django-insecure-q*%z%14^psinrkf=n+6x144zvttpk2)^7o#8_=n-t)rsg#iork'
DEBUG = True
ALLOWED_HOSTS = []

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    # Core Custom App
    'tweet.apps.TweetConfig', 
    
    # Django Essentials
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',  # Correctly placed in Apps
    
    # Allauth Ecosystem
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
]

# --- MIDDLEWARE ARCHITECTURE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Logic for Auth state & Social Logins
    'allauth.account.middleware.AccountMiddleware', 
]

# --- SITES FRAMEWORK ---
SITE_ID = 1

# --- AUTHENTICATION CONFIGURATION ---
AUTH_USER_MODEL = 'tweet.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# --- URLS & TEMPLATES ---
ROOT_URLCONF = 'rental_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'rental_app', 'templates'),
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': (
                [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]
                if DEBUG
                else [
                    (
                        'django.template.loaders.cached.Loader',
                        [
                            'django.template.loaders.filesystem.Loader',
                            'django.template.loaders.app_directories.Loader',
                        ],
                    )
                ]
            ),
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Vital for Allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rental_app.wsgi.application'

# --- DATABASE ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rental_db',
        'USER': 'postgres',
        'PASSWORD': 'admin123', 
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# --- STATIC & MEDIA (Commercial Pathing) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- NAVIGATION & REDIRECTS ---
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/rentals/'
LOGOUT_REDIRECT_URL = 'rental_list'

# --- ALLAUTH SPECIFIC SETTINGAS ---
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none' # Set to 'mandatory' for production

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata' # Set to your local time in Punjab
USE_I18N = True
USE_TZ = True

# --- DEFAULT FIELD ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
