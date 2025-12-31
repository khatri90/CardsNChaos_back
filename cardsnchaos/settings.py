"""
Django settings for cardsnchaos project.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-cards-n-chaos-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS
# In production, you can set specific hosts via ALLOWED_HOSTS environment variable
# For containerized deployments, we allow all hosts since traffic comes through a load balancer
allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
if allowed_hosts_env:
    ALLOWED_HOSTS = allowed_hosts_env.split(',')
else:
    # Default: allow all hosts (safe behind load balancer)
    ALLOWED_HOSTS = ['*']

# Trust X-Forwarded-Host header from load balancer
USE_X_FORWARDED_HOST = True


# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'channels',
    # Local
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cardsnchaos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cardsnchaos.wsgi.application'
ASGI_APPLICATION = 'cardsnchaos.asgi.application'

# Database
# Use DATABASE_URL if provided (for PostgreSQL/production), otherwise SQLite (for local dev)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production: Use PostgreSQL from environment variable
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
    # Add connection timeout and SSL settings for Aiven/production databases
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000',
    }
    # Ensure SSL is required if not already in the URL
    if 'sslmode' not in DATABASE_URL.lower():
        DATABASES['default'].setdefault('OPTIONS', {})
        DATABASES['default']['OPTIONS']['sslmode'] = 'require'
else:
    # Development: Use SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise configuration for serving static files in production
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
# Allow all origins in development for network access (phone, tablet, etc.)
CORS_ALLOW_ALL_ORIGINS = True if DEBUG else False

# Get CORS origins from environment variable or use defaults
cors_origins_str = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,https://cnc-nfndkwav.deployra.app,https://cards-n-chaos.vercel.app')
CORS_ALLOWED_ORIGINS = cors_origins_str.split(',') if not DEBUG and cors_origins_str else []
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-user-id",  # Custom header for user authentication
    "ngrok-skip-browser-warning",  # Skip ngrok browser warning
]

# CSRF Configuration - trust origins
# IMPORTANT: Set CSRF_TRUSTED_ORIGINS environment variable to include your backend URL
# Example: "https://your-backend.deployra.app,https://cnc-nfndkwav.deployra.app"
csrf_defaults = 'http://localhost:5173,http://localhost:3000'
if not DEBUG:
    # In production, you MUST set CSRF_TRUSTED_ORIGINS environment variable
    # to include both your backend and frontend URLs
    csrf_defaults += ',https://cnc-nfndkwav.deployra.app,https://cards-n-chaos.vercel.app,https://uninjuring-raguel-untaintable.ngrok-free.dev'

csrf_origins_str = os.environ.get('CSRF_TRUSTED_ORIGINS', csrf_defaults)
CSRF_TRUSTED_ORIGINS = csrf_origins_str.split(',') if csrf_origins_str else []

# CSRF cookie settings
if DEBUG:
    CSRF_COOKIE_SAMESITE = 'None'
    CSRF_COOKIE_SECURE = False
else:
    CSRF_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True

# Session Configuration (for anonymous auth)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 30  # 30 days
SESSION_COOKIE_SAMESITE = 'None' if DEBUG else 'Lax'  # None needed for cross-origin WebSocket
SESSION_COOKIE_SECURE = not DEBUG  # True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'core.authentication.AnonymousSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
