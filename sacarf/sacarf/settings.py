import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-=tyhwmlorbn#_sx-vu4_92j7s*0&7f9ee6jn!zjef(opi5lo-i')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

SERVICE_NAME = os.getenv('SERVICE_NAME', 'all')

# ---------------------------------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------------------------------
BASE_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_yasg',
]

if SERVICE_NAME in ('all', 'init', 'usuario'):
    OWN_APPS = ['apps.usuario']
elif SERVICE_NAME == 'academico':
    OWN_APPS = ['shared', 'apps.academico']
elif SERVICE_NAME == 'asistencia':
    OWN_APPS = ['shared', 'apps.asistencia']
elif SERVICE_NAME == 'reportes':
    OWN_APPS = ['shared', 'apps.reportes']
else:
    OWN_APPS = ['apps.usuario', 'apps.academico', 'apps.asistencia', 'apps.reportes']

if SERVICE_NAME in ('all', 'init'):
    OWN_APPS = ['apps.usuario', 'apps.academico', 'apps.asistencia', 'apps.reportes']

INSTALLED_APPS = BASE_APPS + THIRD_PARTY_APPS + OWN_APPS

# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'sacarf.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'sacarf.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'sacarf_db'),
        'USER': os.getenv('DB_USER', 'sacarf_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'sacarf_2026'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

# ---------------------------------------------------------------------------
# AUTH (varía según el servicio)
# ---------------------------------------------------------------------------
if SERVICE_NAME in ('all', 'init', 'usuario'):
    AUTH_USER_MODEL = 'usuario.Usuario'
    AUTHENTICATION_BACKENDS = [
        'apps.usuario.authentication.EmailOrUsernameModelBackend',
    ]
else:
    AUTH_USER_MODEL = 'shared.Usuario'
    AUTHENTICATION_BACKENDS = [
        'shared.auth.EmailOrUsernameModelBackend',
    ]

# Email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
PASSWORD_RESET_TIMEOUT = int(os.getenv('PASSWORD_RESET_TIMEOUT', '30'))

# ---------------------------------------------------------------------------
# REST FRAMEWORK
# ---------------------------------------------------------------------------
if SERVICE_NAME in ('all', 'init', 'usuario'):
    AUTH_CLASS = 'apps.usuario.authentication.CustomJWTAuthentication'
else:
    AUTH_CLASS = 'shared.auth.CustomJWTAuthentication'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (AUTH_CLASS,),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

if SERVICE_NAME not in ('all', 'init', 'usuario'):
    MIGRATION_MODULES = {
        'shared': None,
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
