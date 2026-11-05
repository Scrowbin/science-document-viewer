"""Django settings for Scientific Document Manager project."""

import os
import sys

from django.core.exceptions import ImproperlyConfigured
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1')  # off unless .env turns it on
SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('SECRET_KEY must be set in backend/.env when DEBUG is off.')
    SECRET_KEY = 'django-insecure-dev-only-key'

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Local apps
    'apps.users',
    'apps.collections_app',
    'apps.documents',
]

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

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Database Configuration (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'scientific_library_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (PDF Document Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'apps.users.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # Scoped rate limits (ScopedRateThrottle on login/register, chat/summarize, PDF metadata extraction)
    'DEFAULT_THROTTLE_RATES': {
        'auth': os.getenv('THROTTLE_AUTH', '20/min'),
        'chat': os.getenv('THROTTLE_CHAT', '30/min'),
        'extract': os.getenv('THROTTLE_EXTRACT', '20/min'),
    },
}
if 'test' in sys.argv:  # the test suite logs in and asks many times per minute
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {k: '10000/min' for k in REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']}

# SimpleJWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # FR-01
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = False  # only the listed dev origins, even with DEBUG on
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = False  # the API uses Bearer tokens, not cookies
if DEBUG:
    # Vite moves to 5174, 5175, ... when 5173 is busy: accept any port, but only on this machine
    CORS_ALLOWED_ORIGIN_REGEXES = [r'^http://(localhost|127\.0\.0\.1):\d+$']

# Local Embedded RAG & LLM Configuration
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '60'))
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'intfloat/e5-small-v2')
CHUNKING_STRATEGY = os.getenv('CHUNKING_STRATEGY', 'hierarchical')  # 'hierarchical' (production default) | 'section_overlap'
QDRANT_MODE = os.getenv('QDRANT_MODE', 'local')  # 'local' (embedded SQLite) or 'server' (standalone Docker)
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_PREFER_GRPC = os.getenv('QDRANT_PREFER_GRPC', 'false').lower() == 'true'
QDRANT_GRPC_PORT = int(os.getenv('QDRANT_GRPC_PORT', '6334'))
QDRANT_STORAGE_PATH = os.path.join(BASE_DIR, os.getenv('QDRANT_STORAGE_PATH', 'media/qdrant_db'))
RAG_MIN_SIMILARITY_SCORE = float(os.getenv('RAG_MIN_SIMILARITY_SCORE', '0.80'))
# 'dense' (default; best on QASPER in the retrieval experiment) | 'rrf_legacy' (previous dense + whitespace-BM25 RRF k=60)
RAG_RETRIEVAL_MODE = os.getenv('RAG_RETRIEVAL_MODE', 'dense')
OLLAMA_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', '0'))
# Ollama context window, set explicitly (Ollama 0.40.13 default is 4096; real prompts peak ~2,300 tokens)
OLLAMA_NUM_CTX = int(os.getenv('OLLAMA_NUM_CTX', '4096'))
# Fill-budget context assembly: skip a parent that doesn't fit instead of stopping
# (off by default; see the chunking experiment notes in eval/README.md)
RAG_CONTEXT_FILL = os.getenv('RAG_CONTEXT_FILL', 'false').lower() in ('1', 'true', 'yes')

