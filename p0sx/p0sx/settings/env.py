import environ
from p0sx.settings.base import *

env = environ.Env()
environ.Env.read_env()

ALLOWED_HOSTS = env.str('ALLOWED_HOSTS', default="localhost").split(',')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': env.str('POSTGRES_DB', default="p0sx"),                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': env.str('POSTGRES_USER', default="p0sx"),
        'PASSWORD': env.str('POSTGRES_PASSWORD', default="p0sx"),
        'HOST': env.str('POSTGRES_HOST', default=""),                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '5432',                      # Set to empty string for default.
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[DJANGO] %(levelname)s %(asctime)s %(module)s '
                      '%(name)s.%(funcName)s:%(lineno)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        }
    },
}



SITE_URL = env.str('SITE_URL', default="")


# SumUp affiliate key. Create one on your SumUp account with application-id com.polarparty.p0sx
SUMUP_AFFILIATE_KEY = env.str("SUMUP_AFFILIATE_KEY", default="")
# SumUp callback hostname, must include https:// and port if required.
SUMUP_CALLBACK_HOSTNAME = env.str("SUMUP_CALLBACK_HOSTNAME", default="")
# SumUp Merchant code
SUMUP_MERCHANT_CODE = env.str("SUMUP_MERCHANT_CODE", default="")

SUMUP_BEARER_TOKEN = env.str("SUMUP_BEARER_TOKEN", default="")
SUMUP_CLIENT_ID = env.str("SUMUP_CLIENT_ID", default="")
SUMUP_CLIENT_SECRET = env.str("SUMUP_CLIENT_SECRET", default="")

# GeekEvents event id for the current party
GE_EVENT_ID = env.str("GE_EVENT_ID", default="")
GE_SSO_SUCCESS_REDIRECT = env.str("GE_SSO_SUCCESS_REDIRECT", default="")
