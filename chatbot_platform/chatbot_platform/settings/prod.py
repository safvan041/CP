#settings/prod.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = [
    'chatbot-api-platform-29773676777.us-central1.run.app',
    'localhost',
    '127.0.0.1',
    'vigilant-pancake-5wq9xpv4p9vc4ggx-8000.app.github.dev',
]

SECRET_KEY = os.environ.get("SECRET_KEY")

USE_GCS = True
GCS_BUCKET_NAME=os.environ.get("GCS_BUCKET_NAME", "chatbot-api-platform")

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

CORS_TRUSTED_ORIGINS = [ 
    'https://chatbot-api-platform-29773676777.us-central1.run.app', 
]