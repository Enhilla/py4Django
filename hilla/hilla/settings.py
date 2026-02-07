"""
Django settings for hilla project.
"""

from pathlib import Path
import os
import sys

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

# --------------------
# BASE DIR
# --------------------
BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv:
    load_dotenv(BASE_DIR.parent / ".env")

# --------------------
# SECURITY
# --------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

DEBUG = os.environ.get("DEBUG", "False").strip().lower() == "true"

# ALLOWED_HOSTS from env + fallback (no spaces issues)
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,py4django.onrender.com"
    ).split(",")
    if h.strip()
]

# --------------------
# RECAPTCHA
# --------------------
RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY", "")
RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY", "")
_recaptcha_default = "false" if DEBUG else "true"
ENABLE_RECAPTCHA = (
    _truthy(os.environ.get("ENABLE_RECAPTCHA", _recaptcha_default))
    and bool(RECAPTCHA_PUBLIC_KEY)
    and bool(RECAPTCHA_PRIVATE_KEY)
)

# Local dev: keep captcha enabled but use Google's official test keys by default.
# This avoids host/domain verification failures on localhost.
if DEBUG and _truthy(os.environ.get("USE_RECAPTCHA_TEST_KEYS", "true")):
    RECAPTCHA_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
    ENABLE_RECAPTCHA = _truthy(os.environ.get("ENABLE_RECAPTCHA", "true"))
    SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]

# --------------------
# APPLICATIONS
# --------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third-party
    "rest_framework",

    # local
    "complaints",
    "users.apps.UsersConfig",
]

if ENABLE_RECAPTCHA:
    INSTALLED_APPS.append("django_recaptcha")

# --------------------
# MIDDLEWARE
# --------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------
# URLS / TEMPLATES
# --------------------
ROOT_URLCONF = "hilla.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hilla.wsgi.application"

# --------------------
# DATABASE
# --------------------
try:
    import dj_database_url
except Exception:
    dj_database_url = None

db_url = os.environ.get("DATABASE_URL", "").strip()
force_sqlite = _truthy(os.environ.get("FORCE_SQLITE", "false"))
use_remote_db = _truthy(os.environ.get("USE_REMOTE_DB", "false"))
is_render = bool(os.environ.get("RENDER"))
is_runserver = any(arg == "runserver" for arg in sys.argv[1:])

# Strategy:
# - local runserver => SQLite by default
# - production / Render => remote DATABASE_URL
# - explicit USE_REMOTE_DB=true => remote DATABASE_URL
should_use_remote_db = (
    not force_sqlite
    and bool(dj_database_url)
    and bool(db_url)
    and (use_remote_db or is_render or (not DEBUG and not is_runserver))
)

if should_use_remote_db:
    DATABASES = {
        "default": dj_database_url.config(default=db_url, conn_max_age=600, ssl_require=True),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --------------------
# PASSWORD VALIDATION
# --------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------
# INTERNATIONALIZATION
# --------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------
# STATIC FILES
# --------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}
# Allow WhiteNoise to serve from app static dirs if collectstatic output is stale.
WHITENOISE_USE_FINDERS = True

# --------------------
# MEDIA FILES (avatars)
# --------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------
# DEFAULT PK
# --------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------
# AUTH
# --------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
