#settings/dev.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = [
    'chatbot-api-platform-29773676777.us-central1.run.app',
    'localhost',
    '127.0.0.1',
    'app.github.dev',
    'vigilant-pancake-5wq9xpv4p9vc4ggx-8000.app.github.dev',
]


USE_GCS = False 

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
