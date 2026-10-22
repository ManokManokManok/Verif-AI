from pathlib import Path
import os
from dotenv import load_dotenv
import logging  # <-- Add this import

# Reduce pymongo and urllib3 log verbosity
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# =============================================================================
# SECURITY SETTINGS (OWASP Best Practices)
# =============================================================================
# SECURITY WARNING: Generate a unique secret key in production!
# Use: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')

# SECURITY: Explicitly define allowed hosts, no wildcards in production
_allowed_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '')
if DEBUG and not _allowed_hosts:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
else:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()]
    if not ALLOWED_HOSTS:
        raise ValueError("DJANGO_ALLOWED_HOSTS must be set in production")

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
    'src.apps.chatbot',
    'src.apps.reports',
    'src.apps.analytics',
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
    'src.interfaces.rest.middleware.AuthenticationMiddleware',
    'src.infrastructure.middleware.analytics_middleware.AnalyticsMiddleware',
    'src.infrastructure.middleware.request_log_middleware.RequestLogMiddleware',
]

# Analytics settings
ANALYTICS_ENABLED = True

# =============================================================================
# MFA (Multi-Factor Authentication) SETTINGS
# =============================================================================
# In development, you can bypass MFA email verification by setting MFA_ENABLED=False
# When disabled, the system will:
# - Skip sending actual email codes
# - Accept any 6-digit code (e.g., "000000") during verification
MFA_ENABLED = os.getenv('MFA_ENABLED', 'False').lower() in ('1', 'true', 'yes')
MFA_DEV_BYPASS_CODE = '000000'  # Static code accepted when MFA_ENABLED=False

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
        # Lambda's filesystem is read-only except /tmp (ephemeral; Django internals only).
        'NAME': '/tmp/db.sqlite3' if os.getenv('AWS_LAMBDA_FUNCTION_NAME') else BASE_DIR / 'db.sqlite3',
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

# CORS Configuration
_configured_cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
if _configured_cors_origins:
    CORS_ALLOWED_ORIGINS = [
        origin.strip().rstrip('/')
        for origin in _configured_cors_origins.split(',')
        if origin.strip()
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]

# Allow preview deployments belonging to this Vercel project, without allowing
# arbitrary Vercel-hosted sites to make cross-origin requests.
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://verif-ai-site-[a-z0-9-]+-manokmanokmanok\.vercel\.app$',
    r'^https://verif-ai-frontend-[a-z0-9-]+-manokmanokmanok\.vercel\.app$',
]

# Allow all origins in development for easier testing (disable in production!)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

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
    'x-session-id',
]

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
    'UNAUTHENTICATED_TOKEN': None,
    # Disable DRF's ?format= renderer override; admin exports use ?format=csv|excel
    'URL_FORMAT_OVERRIDE': None,
    # SECURITY: Limit request body size to prevent DoS
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# =============================================================================
# ADDITIONAL SECURITY SETTINGS
# =============================================================================

# SECURITY: HTTP Strict Transport Security (HSTS)
# Enable in production with HTTPS
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    if os.getenv('DJANGO_TRUST_PROXY_SSL', 'false').lower() in ('1', 'true', 'yes'):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECURITY: Secure cookies
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# SECURITY: Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# SECURITY: Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# =============================================================================
# LOGGING CONFIGURATION (Security Monitoring)
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': '[SECURITY] {levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'sensitive_data': {
            '()': 'src.infrastructure.logging.sensitive_filter.SensitiveDataFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['sensitive_data'],
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'security',
            'filters': ['sensitive_data'],
        },
    },
    'loggers': {
        'security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'verfai.access': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# On Lambda (or LOG_TO_FILE=false) log to stdout/CloudWatch only; the filesystem is read-only.
_LOG_TO_FILE = os.getenv(
    'LOG_TO_FILE', 'false' if os.getenv('AWS_LAMBDA_FUNCTION_NAME') else 'true'
).lower() in ('1', 'true', 'yes', 'on')
if not _LOG_TO_FILE:
    del LOGGING['handlers']['security_file']
    for _logger_cfg in LOGGING['loggers'].values():
        _logger_cfg['handlers'] = ['console']
