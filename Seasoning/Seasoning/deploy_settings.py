from global_settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '*DATABASE_NAME*',                      # Or path to database file if using sqlite3.
        'USER': '*DATABASE_USER*',                      # Not used with sqlite3.
        'PASSWORD': '*DATABASE_PASSWORD*',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

MEDIA_ROOT = '*SEASONING_HOME*/seasoning_website/media/'
STATIC_ROOT = '*SEASONING_HOME*/seasoning_website/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '*SECRET_KEY*'

EMAIL_HOST = 'smtp.live.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'joeper_100@hotmail.com'
EMAIL_HOST_PASSWORD = '*EMAIL_HOST_PASSWORD*'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'activation@seasoning.be'

# Django-recaptcha
RECAPTCHA_PUBLIC_KEY = '6LcgBtwSAAAAAGYLzvpNQ1tbir0HCabUNV56R1Gk'
RECAPTCHA_PRIVATE_KEY = '*RECAPTCHA_PRIVATE_KEY*'
RECAPTCHA_USE_SSL = True