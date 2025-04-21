from pathlib import Path
import os
from django.core.management.commands.runserver import Command as runserver
import environ

# Set environment variables
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variable to set base directory
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Actual directory user files go to
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'rdlmediafiles')

# URL used to access the media
MEDIA_URL = '/rdlmedia/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django_database_prefix',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'user_app',
    'attendance_app',
    'report_app',
    'delivery_app',
    'collection_app',
    'customer_location_app',
    'conveyance_app',
    'web_view_app',
    'visit_app',
    'sap_app',
    'overdue_app',
    'mobile_app_control',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rdl_ms_api.urls'

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

WSGI_APPLICATION = 'rdl_ms_api.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DB_PREFIX = 'rdl_'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DEFAULT_DB_NAME'),
        'USER': env('DEFAULT_DB_USER'),
        'PASSWORD': env('DEFAULT_DB_PASS'),
        'HOST': env('DEFAULT_DB_HOST'),
        'PORT': env('DEFAULT_DB_PORT'),
        "TIME_ZONE": "Asia/Dhaka"
    },
    'postgres': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB_NAME'),
        'USER': env('POSTGRES_DB_USER'),
        'PASSWORD': env('POSTGRES_DB_PASS'),
        'HOST': env('POSTGRES_DB_HOST'),
        'PORT': env('POSTGRES_DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


runserver.default_port = "6042"