from settings import *

TEMPLATE_DIRS = (
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/bigbazaar'),
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla')
)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(SETTINGS_FILE_FOLDER, 'media/bigbazaar')
UPLOAD_ROOT = '/home/apps/uploads/u/bigbazaar'

HOME_PAGE_BRAND_IDS = [93, 438, 77, 401, 51, 111, 100, 63, 17, 52, 83, 53]
HOME_PAGE_TOP_CATEGORIES = [1053,920,1104,1174,1038,1073]
#HOME_PAGE_TOP_CATEGORIES = [1239, 1494, 1372, 1393, 1424, 1357]
#HOME_PAGE_TOP_CATEGORIES = [1372, 1239, 1424, 1494, 1357, 1393]

SOUTH_DATABASE_ADAPTERS = {
        'default': 'south.db.mysql',
        #'atg': 'south.db.oracle'
        }
SKIP_SOUTH_TESTS = True

if DEBUG:
    INTERNAL_IPS = ('10.114.62.28','localhost','127.0.0.1')

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
        'HOST': '127.0.0.1',
        'NAME': 'tinla',
        'USER': 'root',
        'PASSWORD': 'root',
    },

#    'atg': {
#        'ENGINE': 'django.db.backends.oracle', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#        'NAME': 'ATGSTG2',                      # Or path to database file if using sqlite3.
#        'USER': 'alpha_commerce',                      # Not used with sqlite3.
#        'PASSWORD': 'alpha_commerce',                  # Not used with sqlite3.
#        'HOST': '10.0.103.12',                      # Set to empty string for localhost. Not used with sqlite3.
#        'PORT': '1521',                      # Set to empty string for default. Not used with sqlite3.
#    }
}
ITEMS_PER_PAGE = 16
try:
    from bigbazaarlocal_settings import *
except ImportError:
    pass

DATABASE_ROUTERS = ['dbrouters.futurebazaar.FutureBazaarDBRouter']


from app_settings.ezone import *

AUTHENTICATION_BACKENDS = (
        'users.backends.FutureBazaarATGBackend',
        'users.backends.ChaupaatiBackend',
        'users.backends.PhoneEmailBackend',
        'users.order_backends.OrderBackend',
        'users.facebook_backends.FacebookBackend',
        'django.contrib.auth.backends.ModelBackend',
)
CLIENT = 'bigbazaar'
FACEBOOK_APPLICATION_ID = '126505110759991'
FACEBOOK_API_KEY = 'c16047677fb960ae218100c2534d3263'
FACEBOOK_APPLICATION_SECRET = 'ca930d5380e60495e236e2b0b50a3778'

