from global_settings import *
from dev_secrets import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'seasoning_dev',                      # Or path to database file if using sqlite3.
        'USER': 'dev',                      # Not used with sqlite3.
        'PASSWORD': 'lame',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'devkey123123'

EMAIL_HOST = 'smtp.live.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'test@seasoning.be'
EMAIL_HOST_PASSWORD = 'none'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'activation@seasoning.be'

# Django-recaptcha
RECAPTCHA_PUBLIC_KEY = '6LcgBtwSAAAAAGYLzvpNQ1tbir0HCabUNV56R1Gk'
#RECAPTCHA_PRIVATE_KEY = '*RECAPTCHA_PRIVATE_KEY*'
RECAPTCHA_USE_SSL = True