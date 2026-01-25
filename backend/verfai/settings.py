"""
Django Settings for VerfAi Backend

Security Hardening following OWASP best practices:
- Secret keys from environment variables (no defaults in production)
- Secure middleware configuration
- Rate limiting and security headers
- Proper logging configuration

OWASP References:
- https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html
"""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# SECURITY: Secret key must be set via environment variable
# In production, never use a default value
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    # Only allow insecure default in explicit development mode
    if os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes'):
        SECRET_KEY = 'dev-insecure-secret-key-CHANGE-IN-PRODUCTION'
    else:
        raise ValueError(
            "DJANGO_SECRET_KEY environment variable is not set. "
            "This is required for production deployments."
        )

# SECURITY: Debug should be False in production
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')

# SECURITY: Restrict allowed hosts in production
ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'src.apps.core',
    'src.apps.auth',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom security middleware (order matters!)
    'src.interfaces.rest.middleware.SecurityHeadersMiddleware',  # Security headers first
    'src.interfaces.rest.middleware.RateLimitMiddleware',  # Rate limiting before auth
    'src.interfaces.rest.middleware.AuthenticationMiddleware',  # JWT authentication
    'src.interfaces.rest.middleware.RequestLoggingMiddleware',  # Audit logging last
]

ROOT_URLCONF = 'verfai.urls'

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

WSGI_APPLICATION = 'verfai.wsgi.application'

# Keep SQLite for Django internals; domain data can use MongoDB via repos.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
    'UNAUTHENTICATED_TOKEN': None,
    # SECURITY: Limit request parsing
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',  # Only JSON, no form data
    ],
    # SECURITY: Limit response rendering  
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',  # Only JSON responses
    ],
}

# CORS Configuration
# SECURITY: Restrict CORS to known origins
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:5174').split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# =============================================================================
# SECURITY LOGGING CONFIGURATION
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'security',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['console', 'security_file'] if not DEBUG else ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# =============================================================================
# ADDITIONAL SECURITY SETTINGS
# =============================================================================

# SECURITY: Session security (for Django admin)
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# SECURITY: CSRF security
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# SECURITY: Content type sniffing protection
SECURE_CONTENT_TYPE_NOSNIFF = True

# SECURITY: XSS protection
SECURE_BROWSER_XSS_FILTER = True

# SECURITY: Clickjacking protection
X_FRAME_OPTIONS = 'DENY'

# SECURITY: HTTPS settings (enable in production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
