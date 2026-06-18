"""
Django settings for backend_soutenance project.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import config


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Sécurité
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

# Hosts autorisés — inclut automatiquement le domaine Render si défini
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Applications installées
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Applications tierces
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'channels',
    # Applications du projet
    'accounts',
    'hopitaux',
    'messagerie',
    'rendezvous',
    'resultats',
    'notifications',
    'Chatbot',
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

ROOT_URLCONF = 'backend_soutenance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'backend_soutenance.wsgi.application'

import dj_database_url

DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    # Base de données PostgreSQL locale
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'soutenance_data_base',
            'USER': 'postgres',
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'accounts.User'

# Authentification personnalisée (Email ou Numéro de Téléphone)
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrPhoneModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Porto-Novo'
USE_I18N = True
USE_TZ = True

# Fichiers statiques et médias
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Configuration JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Configuration Email
# En développement : les emails s'affichent dans la console (terminal)
# En production : changer pour 'django.core.mail.backends.smtp.EmailBackend'
# On force le SMTP même en développement pour que vous receviez les vrais e-mails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@HOPITEL-benin.com')
BREVO_API_KEY = config('BREVO_API_KEY', default='')

# URL du frontend
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:8080')

# URL du backend (pour les liens de validation d'emails qui doivent ouvrir une page web sur le backend)
BACKEND_URL = config('BACKEND_URL', default='http://localhost:8000')

# URL du service WhatsApp (Microservice Node.js)
WHATSAPP_SERVICE_URL = config('WHATSAPP_SERVICE_URL', default='http://localhost:3001')

# ── Feature Toggles ──────────────────────────────────────────────────────
# Pour désactiver les services externes si nécessaire (SMTP/WhatsApp)
ENABLE_EMAILS = config('ENABLE_EMAILS', default=True, cast=bool)
ENABLE_WHATSAPP = config('ENABLE_WHATSAPP', default=True, cast=bool)
AUTO_ACTIVATE_USER = config('AUTO_ACTIVATE_USER', default=False, cast=bool)

# ── Soutenance / Debug Mode ──────────────────────────────────────────────
# Rediriger toutes les notifications vers une adresse/numéro unique
SOUTENANCE_MODE = config('SOUTENANCE_MODE', default=True, cast=bool)
SOUTENANCE_EMAIL = config('SOUTENANCE_EMAIL', default='sidickelpc123@gmail.com')
SOUTENANCE_WHATSAPP = config('SOUTENANCE_WHATSAPP', default='2290168765927')

# CORS
# En local : tout autoriser (pratique pour les tests).
# En production : RESTREINDRE aux seules origines du frontend !
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8080',
    'http://localhost:3000',
    'http://localhost:5000',
    'http://127.0.0.1:8080',
]
# Ajouter l'URL front-end de production si définie
_FRONTEND_CORS = config('FRONTEND_CORS_ORIGIN', default='')
if _FRONTEND_CORS:
    CORS_ALLOWED_ORIGINS.append(_FRONTEND_CORS)

# Configuration Chatbot (API externe)
CHATBOT_API_URL = config('CHATBOT_API_URL', default='https://api.groq.com/openai/v1/chat/completions')
CHATBOT_API_KEY = config('GROQ_API_KEY', default='')
CHATBOT_MODEL = config('GROQ_MODEL', default='llama-3.3-70b-versatile')
CHATBOT_TIMEOUT = config('CHATBOT_TIMEOUT', default=30, cast=int)

# Django Channels (WebSocket)
ASGI_APPLICATION = 'backend_soutenance.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# ── Logging ──────────────────────────────────────────────────────────────────
# Affiche les logs INFO+ dans la console (visible dans les logs Render)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # mettre DEBUG pour voir les requêtes SQL
            'propagate': False,
        },
    },
}


