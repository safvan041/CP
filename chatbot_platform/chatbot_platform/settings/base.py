#settings/base.py
import os
from pathlib import Path
from decouple import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'statics'),
]

NVIDIA_API_KEY = config("NVIDIA_API_KEY").strip()
NVIDIA_BASE_URL = config(
    "NVIDIA_BASE_URL",
    default="https://integrate.api.nvidia.com/v1",
).strip()
NVIDIA_CHAT_MODEL = config(
    "NVIDIA_CHAT_MODEL",
    default="Deepseek-v4-pro-0813",
).strip()
NVIDIA_EMBEDDING_MODEL = config(
    "NVIDIA_EMBEDDING_MODEL",
    default="nemotron-3-embed-1b",
).strip()

# === NVIDIA EMBEDDING-SPECIFIC CONFIGURATION (separate API key) ===
NVIDIA_EMBEDDING_API_KEY = config(
    "NVIDIA_EMBEDDING_API_KEY",
    default=config("NVIDIA_API_KEY"),  # Fallback to chat API key if not specified
).strip()
NVIDIA_EMBEDDING_BASE_URL = config(
    "NVIDIA_EMBEDDING_BASE_URL",
    default=config("NVIDIA_BASE_URL"),  # Fallback to chat base URL if not specified
).strip()
MAX_KNOWLEDGE_BASE_SIZE = 50 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024
# ====================================================================
SECRET_KEY = config("SECRET_KEY", default="unset-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", default="True") == "True"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if not DEBUG else []
USE_X_FORWARDED_HOST = True 
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# === SESSION & CSRF COOKIE CONFIGURATION (Critical for Codespaces) ===
SESSION_COOKIE_SECURE = False  # False for HTTP local dev, True for production HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-site requests but mitigate CSRF
CSRF_COOKIE_SECURE = False  # False for HTTP local dev, True for production HTTPS
CSRF_COOKIE_HTTPONLY = False  # Must be False - JS needs to read CSRF token
CSRF_COOKIE_SAMESITE = 'Lax'  # Allow cross-site requests but mitigate CSRF
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'  # Header name for CSRF token in POST requests
# ======================================================================== 


# CORS_ALLOWED_ORIGINS = [

# ]

CORS_TRUSTED_ORIGINS = [ 
    'https://*.github.dev',
    'https://improved-space-bassoon-7g9xp47r4752rjw5-8000.app.github.dev/',

    'http://localhost:8000',
    "http://127.0.0.1:8000",
]

CSRF_TRUSTED_ORIGINS = [ 
    'https://*.github.dev',
    'https://improved-space-bassoon-7g9xp47r4752rjw5-8000.app.github.dev/',

    'http://localhost:8000',
    "http://127.0.0.1:8000",
]


CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'webapp',
    'axes',
    'usage_analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatbot_platform.urls'

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

WSGI_APPLICATION = 'chatbot_platform.wsgi.application'

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


LOGIN_URL = '/login/'
X_FRAME_OPTIONS = 'ALLOWALL'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#AXES CONFIG
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 500
AXES_COOLOFF_TIME = None
AXES_LOCK_OUT_AT_FAILURE = True
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
# AXES_LOCKOUT_TEMPLATE = 'axes/locked_out.html'
AXES_BEHIND_REVERSE_PROXY = False


#email-config
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'testexample041@gmail.com'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = 'safwanbakkar.dev@hotmail.com'

SERVER_EMAIL = 'safwanbakkar.dev@hotmail.com'



#app level logging.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {name} {message}', # Shows logger name (e.g., webapp.views)
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG', # This handler outputs all messages from DEBUG level up
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': { # Django's own internal logs
            'handlers': ['console'],
            'level': 'INFO', # Keep this at INFO to avoid excessive verbosity from Django framework
            'propagate': False,
        },
        'webapp': { # Logger for your webapp app
            'handlers': ['console'],
            'level': 'DEBUG', # <--- CRUCIAL: Set to DEBUG to see all your logger.debug/info calls
            'propagate': False,
        },
        'core': { # Logger for your core app
            'handlers': ['console'],
            'level': 'DEBUG', # <--- CRUCIAL: Set to DEBUG to see all your logger.debug/info calls
            'propagate': False,
        },
        'celery': { # If you still have Celery configured, this controls its logging
            'handlers': ['console'],
            'level': 'INFO', # Can be DEBUG if you need detailed Celery logs
            'propagate': False,
        },
        # You can add more specific loggers here if needed, e.g.,
        # 'core.utils.conversation.manager': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': False,
        # },
    },
    'root': { # Default logger for anything not explicitly handled by specific loggers
        'handlers': ['console'],
        'level': 'WARNING', # Generally keep root logger at WARNING or INFO
    },
}