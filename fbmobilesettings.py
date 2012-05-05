from settings import *
import re
DEBUG = False


TEMPLATE_DIRS = (
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar/mobile'),
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla')
)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(SETTINGS_FILE_FOLDER, 'media/futurebazaar/mobile')
UPLOAD_ROOT = '/home/apps/uploads/u/futurebazaar'

HOME_PAGE_BRAND_IDS = [93, 438, 77, 401, 51, 111, 100, 63, 17, 52, 83, 53]
HOME_PAGE_TOP_CATEGORIES = [1053,1169,920,1104,1174,1073]
#HOME_PAGE_TOP_CATEGORIES = [1053,920,1104,1174,1038,1073]
HOME_PAGE_MOST_WANTED_SKU_IDS = [2579847, 2581790]
#HOME_PAGE_TOP_CATEGORIES = [1239, 1494, 1372, 1393, 1424, 1357]
#HOME_PAGE_TOP_CATEGORIES = [1372, 1239, 1424, 1494, 1357, 1393]

HOME_PAGE_TOP_CATEGORIES_LIST = [
    {'parent':'Computers & Memory & Storage', 'children':[1054, 1056, 1062, 1169], 'image_class':'computers'},
    {'parent':'Clothing & Accessories', 'children':[921, 931, 951, 962, 967, 974], 'image_class':'clothing-accessories'},
    {'parent':'Home & Kitchen Utility', 'children':[1106, 1133, 1144, 1154, 1160], 'image_class':'home-kitchen-utilities'},
    {'parent':'Mobile & Electronics', 'children':[1175, 1178, 1074, 1081, 1085], 'image_class':'mobiles-phones'},
    {'parent':'Bags & Luggage', 'children':[980, 981, 984, 985], 'image_class':'bags-luggage'},
    {'parent':'Beauty & Wellness Product', 'children':[995, 1005, 1011], 'image_class':'beauty-wellness-products'},
]

SOUTH_DATABASE_ADAPTERS = {
        'default': 'south.db.mysql',
        'atg': 'south.db.oracle'
        }
SKIP_SOUTH_TESTS = True
DEBUG = False
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


CCD_DOMAIN = 'ccd.futurebazaar.com'
WIN_DOMAIN = 'win.futurebazaar.com'
VISA_DOMAIN = 'visa.futurebazaar.com'
MIDDAY_DOMAIN = 'midday.futurebazaar.com'
OFFER_DOMAIN = 'offer.futurebazaar.com'
KHOJGURU_DOMAIN = 'khojguru.futurebazaar.com'
MOBILE_DOMAIN = 'm.futurebazaar.com:8000'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'tinla',
        'USER': 'root',
        'PASSWORD': 'root',
    },
    'atg': {
        'ENGINE': 'django.db.backends.oracle', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'ATGSTG2',                      # Or path to database file if using sqlite3.
        'USER': 'alpha_commerce',                      # Not used with sqlite3.
        'PASSWORD': 'alpha_commerce',                  # Not used with sqlite3.
        'HOST': '10.0.103.13',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '1521',                      # Set to empty string for default. Not used with sqlite3.
    }
}

FB_FEEDS_SERVER = 'http://feeds.futurebazaar.com:8080'

try:
    from fbmobilelocal_settings import *
except ImportError:
    pass

DYN_TEMPLATE_MAP = {
    'HTTP_HOST': {
        re.compile('^%s' % MIDDAY_DOMAIN): (
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/midday'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla'),
            ),
        re.compile('^%s' % VISA_DOMAIN): (
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/visa'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla'),
            ),
        re.compile('^%s' % WIN_DOMAIN): (
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/win'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla'),
            ),
        re.compile('^%s' % OFFER_DOMAIN): (
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/offer_fb'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla'),
            ),
        re.compile('^%s' % CCD_DOMAIN): (
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/ccd_fb'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/win'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla'),
            ),
        re.compile('^%s' % KHOJGURU_DOMAIN): (
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/khojguru'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/futurebazaar'),
            os.path.join(SETTINGS_FILE_FOLDER, 'templates/tinla'),
            ),
    }
}


DATABASE_ROUTERS = ['dbrouters.futurebazaar.FutureBazaarDBRouter']


from app_settings.futurebazaar import *

AUTHENTICATION_BACKENDS = (
        'users.backends.FutureBazaarATGBackend',
        'users.backends.ChaupaatiBackend',
        'users.backends.PhoneEmailBackend',
        'users.facebook_backends.FacebookBackend',
        'users.order_backends.OrderBackend',
        'django.contrib.auth.backends.ModelBackend',
)
CLIENT = 'Futurebazaar'
#FACEBOOK_APPLICATION_ID = '59141677994'
FACEBOOK_APPLICATION_ID = '126505110759991'
FACEBOOK_API_KEY = 'c16047677fb960ae218100c2534d3263'
FACEBOOK_APPLICATION_SECRET = 'ca930d5380e60495e236e2b0b50a3778'

