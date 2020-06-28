"""
Django settings for actas_backend project.
  
Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
# pylint: disable=no-member


import os
import ldap
import mongoengine
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion
from corsheaders.defaults import default_headers

AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_DEBUG_LEVEL: 1,
    ldap.OPT_REFERRALS: 0,
}

ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, os.getcwd()+"/certificate.pem")

AUTH_LDAP_SERVER_URI = os.environ.get('LDAP_HOST')
AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
    LDAPSearch("ou=people,o=unal.edu.co",
               ldap.SCOPE_SUBTREE, "(uid=%(user)s)"),
    LDAPSearch("ou=institucional,o=bogota,o=unal.edu.co",
               ldap.SCOPE_SUBTREE, "(uid=%(user)s)"),
    LDAPSearch("ou=dependencia,o=bogota,o=unal.edu.co",
               ldap.SCOPE_SUBTREE, "(uid=%(user)s)"),
    LDAPSearch("ou=Institucional,o=bogota,o=unal.edu.co",
               ldap.SCOPE_SUBTREE, "(uid=%(user)s)"),
    LDAPSearch("ou=Dependencia,o=bogota,o=unal.edu.co",
               ldap.SCOPE_SUBTREE, "(uid=%(user)s)"),
)
AUTH_LDAP_ALWAYS_UPDATE_USER = False
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated', )
}

# CORS_ORIGIN_WHITELIST = (
#   'http://localhost:3000',
# ) To allow only certain front ends

# TODO: Allow only certainb front ends #DONE: Done in develop
CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = default_headers + (
    'Access-Control-Allow-Origin',
)

CORS_EXPOSE_HEADERS = ['Access-Control-Allow-Origin']

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '2d=v4-s%^4(#u+4o$wz*y*stng(i4pq)gv8k38gof=a(mcjzq_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [os.environ.get('ACTAS_HOST'), '127.0.0.1']

CORS_ORIGIN_WHITELIST = [
    'http://localhost:4200',
]

CORS_ORIGIN_WHITELIST = [
    "http://fce.unal.edu.co",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]
# Application definition

INSTALLED_APPS = [
    'council_minutes.apps.CouncilMinutesConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'actas_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'actas_backend.wsgi.application'


# Database and MongoDB config
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

MONGODB_AUTH = os.environ.get('ACTAS_DB_AUTH')
MONGODB_USER = os.environ.get('ACTAS_DB_USER')
MONGODB_HOST = os.environ.get('ACTAS_DB_HOST')
MONGODB_NAME = os.environ.get('ACTAS_DB_NAME')
MONGODB_PASS = os.environ.get('ACTAS_DB_PASS')
MONGODB_PORT = 27017
MONGODB_AMCH = 'SCRAM-SHA-1'

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'AUTH_SOURCE': MONGODB_AUTH,
        'NAME': MONGODB_NAME,
        'HOST': MONGODB_HOST,
        'USER': MONGODB_USER,
        'PASSWORD': MONGODB_PASS,
        'CLIENT': {
            'host': MONGODB_HOST,
            'port': MONGODB_PORT,
            'username': MONGODB_USER,
            'password': MONGODB_PASS,
            'authSource': MONGODB_AUTH,
            'authMechanism': MONGODB_AMCH
        }
    }
}

mongoengine.connect(authentication_source=MONGODB_AUTH, db=MONGODB_NAME,
                    username=MONGODB_USER, password=MONGODB_PASS, host=MONGODB_HOST)

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/council_minutes/public/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "public"),
    '/var/www/static/',
]
