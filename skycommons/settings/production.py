"""Production settings: everything environment-driven, PostgreSQL, and
whitenoise for static files (no separate static file server needed).

Required env vars: SECRET_KEY, ALLOWED_HOSTS, POSTGRES_PASSWORD.
Optional: POSTGRES_DB, POSTGRES_USER, POSTGRES_HOST, POSTGRES_PORT,
CSRF_TRUSTED_ORIGINS, WAGTAILADMIN_BASE_URL, FRONTEND_URL (read in base.py).
"""

import os

from .base import *

DEBUG = False

# Wagtail's database search backend uses SearchVectorField on PostgreSQL
INSTALLED_APPS += ["django.contrib.postgres"]

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")

# e.g. "https://backend.skycommons.okfn.org"; defaults to https on each host
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", ",".join(f"https://{h}" for h in ALLOWED_HOSTS)
).split(",")

# TLS terminates at Caddy, which proxies over HTTP and sets X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "skycommons"),
        "USER": os.environ.get("POSTGRES_USER", "skycommons"),
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# whitenoise serves the collected static files from the app container;
# manifest storage busts caches on deploys
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
STORAGES["staticfiles"]["BACKEND"] = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

WAGTAILADMIN_BASE_URL = os.environ.get(
    "WAGTAILADMIN_BASE_URL", f"https://{ALLOWED_HOSTS[0]}"
)

try:
    from .local import *
except ImportError:
    pass
