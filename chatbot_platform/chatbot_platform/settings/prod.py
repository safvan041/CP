from .base import *

DEBUG = False
ALLOWED_HOSTS = [
    'chatbot-api-platform-29773676777.us-central1.run.app',
    'localhost',
    '127.0.0.1',
]

SECRET_KEY = os.environ.get("SECRET_KEY")

USE_GCS = True
GCS_BUCKET_NAME=os.environ.get("GCS_BUCKET_NAME", "chatbot-api-platform")

CSRF_TRUSTED_ORIGINS = [
    'https://chatbot-api-platform-29773676777.us-central1.run.app',
]

CORS_TRUSTED_ORIGINS = [ 
    'https://chatbot-api-platform-29773676777.us-central1.run.app', 
]