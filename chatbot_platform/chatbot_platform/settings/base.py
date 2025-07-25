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

GOOGLE_GENAI_API_KEY = config("GOOGLE_GENAI_API_KEY").strip()
HF_TOKEN = config("HF_TOKEN").strip()
SECRET_KEY = config("SECRET_KEY", default="unset-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", default="True") == "True"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if not DEBUG else []
USE_X_FORWARDED_HOST = True 
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = False 


# CORS_ALLOWED_ORIGINS = [

# ]

CORS_TRUSTED_ORIGINS = [ 
    'https://chatbot-api-platform-29773676777.us-central1.run.app',
    'https://*.app.github.dev',
    'https://vigilant-pancake-5wq9xpv4p9vc4ggx-8000.app.github.dev',

    'http://localhost:8000',
    "http://127.0.0.1:8000",
]

CSRF_TRUSTED_ORIGINS = [ 
    'https://*.app.github.dev',
    'https://vigilant-pancake-5wq9xpv4p9vc4ggx-8000.app.github.dev',

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
    'storages',
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

USE_GCS = False
# GS_BUCKET_NAME = config("GS_BUCKET_NAME", default="chatbot-api-platform")

GS_PROJECT_ID = config("GS_PROJECT_ID", default="None")
if USE_GCS:
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_DEFAULT_ACL = 'publicRead'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'


# logger.info(f"DEBUG: OS environment DB_USER: {os.environ.get('DB_USER')}")
# logger.info(f"DEBUG: Config DB_USER: {config('DB_USER')}")
# logger.info(f"DEBUG: OS environment DB_PASSWORD: {os.environ.get('DB_PASSWORD')}")
# logger.info(f"DEBUG: Config DB_PASSWORD: {config('DB_PASSWORD')}")

USE_CLOUD_DB = config("USE_CLOUD_DB", default="True").lower() == "True"
# logger.info(f"DEBUG: USE_CLOUD_DB resolved to: {USE_CLOUD_DB}")

if USE_CLOUD_DB:
    logger.info(f"DEBUG: Using cloud database configuration")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    logger.info(f"DEBUG: Using local SQLite database configuration")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Celery Configuration
# Broker: Where Celery sends and receives tasks
CELERY_BROKER_URL = 'redis://localhost:6379/0'
# Backend: Where Celery stores task results (optional, but good for tracking)
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata' # Set to your local timezone or 'UTC'


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


#comment out this if you want to use cloud storage
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
#===


LOGIN_URL = '/login/'
X_FRAME_OPTIONS = 'ALLOWALL'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

GOOGLE_GENAI_API_KEY = config("GOOGLE_GENAI_API_KEY")


#AXES CONFIG
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = None
AXES_LOCK_OUT_AT_FAILURE = True
AXES_USE_USER_AGENT = False
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