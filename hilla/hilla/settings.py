"""
Django settings for hilla project.
"""

from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

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
ENABLE_RECAPTCHA = (
    os.environ.get("ENABLE_RECAPTCHA", "true").strip().lower() == "true"
    and bool(RECAPTCHA_PUBLIC_KEY)
    and bool(RECAPTCHA_PRIVATE_KEY)
)

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
# DEFAULT PK
# --------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------
# AUTH
# --------------------
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
