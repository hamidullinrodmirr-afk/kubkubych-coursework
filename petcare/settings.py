import os
import sys
from pathlib import Path
from datetime import timedelta

from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1')

TESTING = 'test' in sys.argv

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN and not TESTING:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv('SENTRY_ENVIRONMENT', 'development'),
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.2')),
        send_default_pii=True,
    )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_filters',
    'corsheaders',
    'rest_framework_simplejwt',

    'django_celery_beat',

    'users',
    'products',
    'cart',
    'orders',
    'product_reviews',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SILKY_ENABLED = DEBUG and not TESTING
if SILKY_ENABLED:
    INSTALLED_APPS.append('silk')
    MIDDLEWARE.append('silk.middleware.SilkyMiddleware')
    SILKY_PYTHON_PROFILER = True
    SILKY_MAX_RECORDED_REQUESTS = 1000

ROOT_URLCONF = 'petcare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'petcare.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

CORS_ALLOW_ALL_ORIGINS = DEBUG

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/oauth/google/callback/')

VK_CLIENT_ID = os.getenv('VK_CLIENT_ID', '')
VK_CLIENT_SECRET = os.getenv('VK_CLIENT_SECRET', '')
VK_REDIRECT_URI = os.getenv('VK_REDIRECT_URI', 'http://localhost:8000/api/auth/oauth/vk/callback/')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '1025'))
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'noreply@kubkubych.ru'

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_PUBLISH_RETRY = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False
CELERY_BROKER_CONNECTION_RETRY = False
CELERY_BROKER_CONNECTION_MAX_RETRIES = 0
CELERY_BROKER_TRANSPORT_OPTIONS = {'socket_connect_timeout': 2, 'socket_timeout': 2}

CELERY_BEAT_SCHEDULE = {}

if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
