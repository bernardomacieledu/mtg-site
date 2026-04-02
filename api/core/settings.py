import pymysql
pymysql.install_as_MySQLdb()

import os
from pathlib import Path

try:
    import MySQLdb  # noqa
except ImportError:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-me-in-production-mtgnexus'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'mtg_api',
    'auth_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request']}}]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mtg_db',
        'USER': 'mtg_ingest',
        'PASSWORD': 'ulJD653C>p6E',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# CORS — permite o Vue (qualquer porta local) acessar a API
CORS_ALLOW_ALL_ORIGINS = True   # Em produção, troque por CORS_ALLOWED_ORIGINS

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 24,
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

SCRYFALL_CACHE_TIMEOUT = 86400
SCRYFALL_CACHE_DIR = BASE_DIR / 'cache'
os.makedirs(SCRYFALL_CACHE_DIR, exist_ok=True)


AUTH_USER_MODEL = 'auth_app.User'
JWT_SECRET = 'mtg-nexus-jwt-secret-change-me'
