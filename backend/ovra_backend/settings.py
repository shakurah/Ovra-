# settings.py (or load from .env)
import os
from dotenv import load_dotenv
load_dotenv()
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "daily-ingestion": {
        "task": "boe.tasks.ingest_boe_task",
        "schedule": crontab(hour=7, minute=0),  # every day at 07:00
    },
}

BOE_RSS_URL = os.getenv("BOE_RSS_URL", "https://www.boe.es/rss/boe.php")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", None)
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", None)
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", None)
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "boe-articles")

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.example.com")
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Deepseek config
AGENT_URL = os.getenv("DEEPSEEK_AGENT_URL", None) + "/api/v1/chat/completions"
API_KEY = os.getenv("DEEPSEEK_API_KEY", None)
DEEPSEEK_MAX_TOKENS = 800


SECRET_KEY = '^!uf9qps&v7!b+7jgxj$^!91#48gb+@by=bl35pe#8ps8p71h@'

# Redis as broker + backend
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Optional settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
from pathlib import Path

BASEDIR = Path(__file__).resolve().parent.parent
# Database configuration for PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ovra_db',
        'USER': 'ovra_user',
        'PASSWORD': 'password123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chat',
    'users',
    'boe',
    'metrics',
    "django_prometheus",
    'django_extensions', 
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',        


]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ]
}



ALLOWED_HOSTS = ["chat.artisting.es", "www.chat.artisting.es"]

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

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # put this at the top
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',   # required
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # required
    'django.contrib.messages.middleware.MessageMiddleware',    # required
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]
APPEND_SLASH = False
CSRF_TRUSTED_ORIGINS = ['https://chat.artisting.es']
CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = 'ovra_backend.urls'
DEBUG = False
STATIC_URL = '/static/'
STATIC_ROOT = BASEDIR / "staticfiles"
MEDIA_URL =  '/media/'
MEDIA_ROOT = BASEDIR / "media"


CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://chat.artisting.es",  # add this when you deploy
]
