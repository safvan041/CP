from .base import *

DEBUG = True
ALLOWED_HOSTS = [
    'chatbot-api-platform-29773676777.us-central1.run.app',
    'localhost',
    '127.0.0.1',
]


USE_GCS = False 

CSRF_TRUSTED_ORIGINS = [
    'https://chatbot-api-platform-29773676777.us-central1.run.app',
]

CORS_TRUSTED_ORIGINS = [ 
    'https://chatbot-api-platform-29773676777.us-central1.run.app', 
]