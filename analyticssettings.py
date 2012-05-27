from settings import *
import re

TEMPLATE_DIRS = (
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla'),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(SETTINGS_FILE_FOLDER, 'media/futurebazaar')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'NAME': 'tinla',
        'USER': 'root',
        'PASSWORD': 'root',
    },
    'analytics': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fbreports',                      # Or path to database file if using sqlite3.
        'USER': 'fbrep',                      # Not used with sqlite3.
        'PASSWORD': 'fbrep123',                  # Not used with sqlite3.
        'HOST': '10.0.101.50',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
    'complaints': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'fbmysqldb',
        'USER': 'reports_user',
        'PASSWORD': 'reports123',
        'HOST': '10.0.101.142',
        'PORT': '3306',
    },
}

DATABASE_ROUTERS = ['dbrouters.analytics.AnalyticsRouter', 'dbrouters.analytics.ComplaintsRouter']

INSTALLED_APPS += (
    'analytics_analytics',
    'analytics_catalog',
    'analytics_complaints',
    'analytics_deals',
    'analytics_feedback',
    'analytics_googleanalytics',
    'analytics_orders',
    'analytics_payments',
    'analytics_pentaho',
    'analytics_product_reviews',
    'analytics_report_access',
    'analytics_scm',
    'analytics_subscriptions',
    'analytics_users',
    'analytics_utils',
)
ROOT_URLCONF = 'tinla.analytics_urls'

try:
    from analytics_local_settings import *
except ImportError:
    pass
