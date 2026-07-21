"""
Settings de monitoring-service — sigue exactamente el mismo patrón que
usuario/academico/asistencia/reportes (ver README: "Cómo se dividió el
monolito"). Solo carga la app `monitoring` (propia) + `shared` (lectura).
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-prod')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [

    'django_prometheus',

    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.monitoring',
    'shared',
]

MIDDLEWARE = [

    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',

    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',

]

ROOT_URLCONF = 'monitoring.urls'
WSGI_APPLICATION = 'monitoring.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
    ]},
}]

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'sacarf_db'),
        'USER': os.getenv('DB_USER', 'sacarf_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Igual que academico/asistencia/reportes: el modelo de usuario real vive en
# usuario-service; aquí solo se lee vía `shared.Usuario` (managed=False).
AUTH_USER_MODEL = 'shared.Usuario'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['shared.auth.CustomJWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
}

CORS_ALLOWED_ORIGINS = os.getenv('FRONTEND_URL', 'http://localhost:5173').split(',')

LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# URL interna de Prometheus (nombre del servicio en docker-compose)
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')

