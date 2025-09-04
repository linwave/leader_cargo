import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=snv8^q=%u%4ky5nbqz81akfn(l!aehv=r)$i7o7(i_6_17323'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'main.apps.MainConfig',
    'analytics.apps.AnalyticsConfig',
    'api.apps.ApiConfig',
    'bills.apps.BillsConfig',
    'telegram_bot.apps.TelegramBotConfig',
    'simple_history',
    'rest_framework',
    'django_htmx',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'main.middleware.MaintenanceModeMiddleware'
]

ROOT_URLCONF = 'leader_cargo.urls'

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

WSGI_APPLICATION = 'leader_cargo.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = []

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
AUTH_USER_MODEL = 'main.CustomUser'

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

# Настройки Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Использование пула потоков вместо prefork
CELERY_WORKER_POOL = 'threads'
CELERY_WORKER_CONCURRENCY = 4  # Установите количество потоков по вашему усмотрению

# Дополнительные настройки для Celery
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_BEAT_SCHEDULE = {
    'send-scheduled-notifications': {
        'task': 'telegram_bot.tasks.send_scheduled_telegram_notifications',  # Путь к задаче
        'schedule': 60.0,  # Проверка каждую минуту
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',  # Выводит логи в консоль
        },
        'file': {
            'class': 'logging.FileHandler',  # Записывает логи в файл
            'filename': 'debug.log',         # Имя файла для записи
        },
    },
    'root': {
        'handlers': ['console', 'file'],     # Используемые обработчики
        'level': 'DEBUG',                    # Уровень логирования
    },
}

TELEGRAM_BOT_TOKEN = "7437043774:AAH51LtcPYRjCAJSF4No1T663Fi2XcS8Rv4"
TELEGRAM_BOT_USERNAME = "magistral_import_bot"
API_ROSACCRED_TOKEN = "A5C27D361C573580E8075C35F477F5A6E06AD30015BC49433F69074E86150FC6"
CRM_DEFAULT_MANAGER_ID = 40

API_PARTNERS = {
# https://site/api/v1/calls/inbound/2f1c3cb2b3b847a5967c8f2e85d0a16a/
    "2f1c3cb2b3b847a5967c8f2e85d0a16a": {
        "crm": "Колл-центр Биг Дата",
        "token": "BIGDATA_TOKEN_KRAfQTMx1PBT6B9sR58E",
        "require_token": True,
        "parser": "default",
    },
# https://site/api/v1/calls/inbound/a9bbd3e5c4f943f9a1e6b3c7d2e8f011/
    "a9bbd3e5c4f943f9a1e6b3c7d2e8f011": {
        "crm": "Колл-центр АЗ",
        "token": "AZ_TOKEN_6F2BF9E1B0D8AC82C5251CDCEC782141",  # можно оставить как есть, но...
        "require_token": False,   # <- токен НЕ обязателен
        "parser": "az",           # <- используем ваш разбор тела AZ
    },
    "b1c3f4c96a3d4e0e8c5f2a1b7d9e1122": {
        "crm": "Наш сайт",
        "require_token": False,    # с фронта, без заголовка
        "parser": "default"        # формат {name, phone, comment, city}
    },
    # "b1c3f4c96a3d4e0e8c5f2a1b7d9e1122": {
    #     "crm": "Наш сайт",
    #     "token": "SITE_TOKEN_XXXXXXXXXXXXXXXXXXXX",
    #     "require_token": True,     # шлём с сервера, не палим токен
    #     "parser": "default"
    # },

}