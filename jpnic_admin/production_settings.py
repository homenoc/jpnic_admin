from jpnic_admin.settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# # candidates value for X-Forwarded-Host header
ALLOWED_HOSTS = []

# django backend database config
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASSWORD"),
        'HOST': 'db',
        'PORT': 3306,
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

SITE_TITLE = 'JPNIC管理システム'
SITE_HEADER = 'JPNIC管理システム'

# CSRF Check
# CSRF_TRUSTED_ORIGINS = ['http://*.localhost', 'https://*.127.0.0.1']
CA_PATH = '/opt/app/config/ca.cert'
JPNIC_BASE_URL = 'https://iphostmaster.nic.ad.jp'