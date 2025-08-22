import os
from datetime import timedelta
from urllib.parse import parse_qsl, urlparse

from dotenv import load_dotenv

load_dotenv()

from decouple import config

from .base import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', cast=str)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", cast=bool, default=False)

ALLOWED_HOSTS = ["127.0.0.1", "localhost",]
allowed_host_value = config("ALLOWED_HOSTS", default="", cast=str)
if allowed_host_value:
    ALLOWED_HOSTS.extend([h.strip() for h in allowed_host_value.split(",") if h.strip()])

# Replace the DATABASES section of your settings.py with this
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
        'OPTIONS': dict(parse_qsl(tmpPostgres.query)),
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": config("POSTGRESQL_DB_NAME"),
#         "USER": config("POSTGRESQL_DB_USER"),
#         "PASSWORD": config("POSTGRESQL_DB_PASSWORD"),
#         "HOST": config("POSTGRESQL_DB_HOST"),
#         "PORT": config("POSTGRESQL_DB_PORT"),
#         'CONN_MAX_AGE': 600,
#     }
    
# }

if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
    WHITENOISE_AUTOREFRESH = True
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_COMPRESS = True
    WHITENOISE_MANIFEST_STRICT = True


SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()
]

STATIC_URL = 'static/'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),]


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        hours=config("ACCESS_TOKEN_LIFETIME", cast=int, default=6)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("REFRESH_TOKEN_LIFETIME", cast=int, default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}



EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # Use your email provider's SMTP server
EMAIL_PORT = 587  # Use 465 for SSL, 587 for TLS
EMAIL_USE_TLS = True  # Set to False if using SSL (465)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", cast=str)  # Your email address
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", cast=str)  # App password (not your real password)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", cast=str)


LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # Keep Django's default loggers
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} [{name}:{lineno}] {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",  # Change to "simple" if you want less detail
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # "django.db.backends": {
        #     "handlers": ["console"],
        #     "level": "DEBUG" if DEBUG else "INFO",  # Show SQL queries in DEBUG
        #     "propagate": False,
        # },
        # "myapp": {  # Replace with your app name, e.g., 'users'
        #     "handlers": ["console"],
        #     "level": LOG_LEVEL,
        #     "propagate": False,
        # },
    },
}

# docker build -t josesholly22/medimind:latest .
# docker push josesholly22/medimind:latest