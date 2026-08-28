#settings/dev.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.app.github.dev',
]


CORS_TRUSTED_ORIGINS = [ 
    'https://*.app.github.dev',

    'http://localhost:8000',
    'https://localhost:8000',
    "http://127.0.0.1:8000",
    "https://127.0.0.1:8000",
]

CSRF_TRUSTED_ORIGINS = [ 
    'https://*.app.github.dev',

    'http://localhost:8000',
    'https://localhost:8000',
    "http://127.0.0.1:8000",
    "https://127.0.0.1:8000",
]