import os

from .settings import *

# Production-specific settings
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# CSRF settings for production
CSRF_TRUSTED_ORIGINS = []
allowed_hosts_env = os.getenv("DJANGO_ALLOWED_HOSTS")
if allowed_hosts_env:
    # Build CSRF trusted origins from allowed hosts
    hosts = allowed_hosts_env.split(",")
    for host in hosts:
        if host.strip() and host.strip() not in ["localhost", "127.0.0.1"]:
            # Add both HTTP and HTTPS for external hosts
            CSRF_TRUSTED_ORIGINS.extend(
                [f"http://{host.strip()}", f"https://{host.strip()}"]
            )

    # Add localhost and 127.0.0.1 with ports for development/local production
    CSRF_TRUSTED_ORIGINS.extend(
        [
            "http://localhost:7000",
            "http://127.0.0.1:7000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )

# Additional CSRF settings for production reliability
CSRF_COOKIE_AGE = 31449600  # 1 year
CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"  # Default CSRF failure view

# Security settings for production
if not DEBUG:
    # HTTPS settings (enable when using HTTPS)
    # SECURE_SSL_REDIRECT = True
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

    # Session security
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
    CSRF_COOKIE_SECURE = False  # Set to True when using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    # CSRF_COOKIE_HTTPONLY = True  # Disabled - can interfere with CSRF token handling
    CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access to CSRF cookie if needed

# Logging configuration for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/app/logs/django.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "scripts.temperature_daemon": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "services.switchbot_service": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
