"""
Django settings for testing.
"""

from .settings import *

# Use in-memory SQLite database for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Keep migrations for core Django apps but disable for custom apps if needed
# This ensures django_content_type and other essential tables are created
# MIGRATION_MODULES = {
#     'homepage': None,  # Disable only custom app migrations if needed
# }

# Reduce password hashing rounds for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable debug mode for tests
DEBUG = False

# Use console email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable logging during tests (optional)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}

# Test-specific settings
SECRET_KEY = "test-secret-key-only-for-testing"

# Allow all hosts for testing
ALLOWED_HOSTS = ["*"]
