"""Development settings."""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['*']

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable rate limiting in development
RATELIMIT_ENABLE = False

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar (optional)
INTERNAL_IPS = ['127.0.0.1']

# Simplified caching in development (use local memory if Redis not available)
import os
if not os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
        'level': 'DEBUG',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Set to DEBUG to see SQL queries
            'propagate': False,
        },
    },
}
