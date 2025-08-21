import os
from datetime import timedelta

from decouple import config

from .base import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7h=$4_vo_lrgvm(q(k3f+3-1^bg)tmaiow7y*abgg8lbr8amcl'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []



DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRESQL_DB_NAME"),
        "USER": config("POSTGRESQL_DB_USER"),
        "PASSWORD": config("POSTGRESQL_DB_PASSWORD"),
        "HOST": config("POSTGRESQL_DB_HOST"),
        "PORT": config("POSTGRESQL_DB_PORT"),
        'CONN_MAX_AGE': 600,
    }
    
}


STATIC_URL = 'static/'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),]


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours = 6),  # How long an access token is valid
    "REFRESH_TOKEN_LIFETIME": timedelta(days= 7), 
    "ROTATE_REFRESH_TOKENS": True,  # Whether to issue a new refresh token during refresh
    "BLACKLIST_AFTER_ROTATION": True,  # Whether to blacklist old refresh tokens
}



EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # Use your email provider's SMTP server
EMAIL_PORT = 587  # Use 465 for SSL, 587 for TLS
EMAIL_USE_TLS = True  # Set to False if using SSL (465)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", cast=str)  # Your email address
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", cast=str)  # App password (not your real password)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", cast=str)