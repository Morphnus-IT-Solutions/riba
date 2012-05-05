from settings import *
import re
DEBUG = False
FB_API_URL = ''

TEMPLATE_DIRS = (
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla')
)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(SETTINGS_FILE_FOLDER, 'media/futurebazaar')
UPLOAD_ROOT = '/home/apps/uploads/u/futurebazaar'
BLACKLIST_CATEGORIES = ['1006440']

SKIP_SOUTH_TESTS = True
if DEBUG:
    INTERNAL_IPS = ('10.114.62.28','localhost','127.0.0.1', '10.202.21.30')

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
    )
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False
    }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'riba',
        'USER': 'root',
        'PASSWORD': 'allagr2nd',
    },

    'tinla_slave': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'riba',
        'USER': 'root',
        'PASSWORD': 'allagr2nd',
    },
}

FB_FEEDS_SERVER = 'http://feeds.futurebazaar.com:8080'

try:
    from fblocal_settings import *
except ImportError:
    pass


from app_settings.futurebazaar import *

AUTHENTICATION_BACKENDS = (
        'users.backends.FacebookAutoBackend',
        'users.backends.PhoneEmailBackend',
        'users.facebook_backends.FacebookBackend',
        'users.order_backends.OrderBackend',
        'django.contrib.auth.backends.ModelBackend',
)

CLIENT = 'Riba'
