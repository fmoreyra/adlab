"""
Test settings for running tests with SQLite (faster than PostgreSQL).

Usage:
    # Run all tests with SQLite
    make test-with-sqlite

    # Run specific test with SQLite
    docker compose exec -T web python3 manage.py test accounts.tests --settings=config.settings_test

Why SQLite for tests?
    - ~10 seconds vs ~3-5 minutes for full test suite
    - No container networking overhead
    - In-memory database for maximum speed
    - Use this for local development (fast feedback)
    - Use PostgreSQL (make test) for CI to match production behavior

Note: Concurrency tests (tests_concurrency.py) run sequentially on SQLite
since SQLite doesn't support true concurrent writes. This is fine for testing
logic correctness - the atomic counter pattern is still validated.
"""

from .settings import *  # noqa
from .settings import BASE_DIR

# Must be False for tests
DEBUG = False
TESTING = True

# Override database to use SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use simple email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable caching during tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Use database sessions for tests (cache backend doesn't work with DummyCache)
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Use default test runner instead of DockerTestRunner (for SQLite)
TEST_RUNNER = "django.test.runner.DiscoverRunner"
