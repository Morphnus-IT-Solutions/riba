# Django settings for riba project.

import os
import logging.config

SETTINGS_FILE_FOLDER = os.path.realpath(os.path.dirname(__file__))
LOGGING_CONF = SETTINGS_FILE_FOLDER + '/logging.conf'

# where the user will go after they log in via facebook
LOGIN_REDIRECT_URL = '/'

DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'NAME': 'riba',
        'USER': 'riba',
        'PASSWORD': 'chintan1',
    },
}
FB_API_URL = ""
#DATABASE_ROUTERS = ['dbrouters.futurebazaar.FutureBazaarDBRouter']

SOUTH_DATABASE_ADAPTERS = {
        'default': 'south.db.mysql',
        }
SKIP_SOUTH_TESTS = True

#TABLE_PREFIX = '"alpha_commerce".'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Kolkata'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_PREFIX = 'media'
MEDIA_ROOT = os.path.join(SETTINGS_FILE_FOLDER, 'media/riba')
UPLOAD_ROOT = '/home/apps/uploads/u/riba'
# FEEDS ROOT
FEEDS_ROOT = os.path.join(SETTINGS_FILE_FOLDER, 'feeds/data')

#Port number for feeds.futurebazaar.com for feed sync
FEED_SYNC_PORT_NUMBER = 8080

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/adminmedia/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'yx@ci*sngi8yb*+s%sv3@6^%e&#@2(jf_b&97#+@!4ln)pugz1'

AUTH_PROFILE_MODULE = 'users.Profile'

AUTHENTICATION_BACKENDS = (
        #'users.backends.ChaupaatiBackend',
        #'users.backends.PhoneEmailBackend',
        'users.order_backends.OrderBackend',
        'users.facebook_backends.FacebookBackend',
        'django.contrib.auth.backends.ModelBackend',
        #'users.backends.PhoneEmailBackend',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'web.contextp.user',
    'web.contextp.app_settings',
    'web.contextp.facebookid',
    'web.contextp.media',
)

#CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=120&binary=1'
EMAIL_HOST = '127.0.0.1'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'dynamicloader.loader.load_template_source',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'dynamicloader.middleware.RequestMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'web.middleware.ClientMiddleWare',
    'web.middleware.ExceptionMiddleWare',
    'django.middleware.common.CommonMiddleware',
    'web.middleware.URLRestrictMiddleWare',
    'django.middleware.cache.FetchFromCacheMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    #'django.middleware.csrf.CsrfResponseMiddleware'
    'pagination.middleware.PaginationMiddleware',
    #'profiling.middleware.ProfileMiddleware',
    #'web.middleware.MobileWebMiddleWare',
)

ROOT_URLCONF = 'riba.urls'

TEMPLATE_DIRS = (
    os.path.join(SETTINGS_FILE_FOLDER, 'templates/riba'),
)

TINYMCE_JS_URL = ADMIN_MEDIA_PREFIX + 'js/tiny_mce/tiny_mce2.js'
TINYMCE_JS_ROOT = ADMIN_MEDIA_PREFIX + 'js/tiny_mce/'
TINYMCE_DEFAULT_CONFIG = {
    'theme_advanced_toolbar_location' : "top",
    'plugins': "table,paste,searchreplace",
    'theme': "advanced",
}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.comments',
    'django.contrib.messages',
    'facebookconnect',
    'feedback',
    'imagekit',
    'tinymce',
    'south',
    'admin',
	'question',
    'build_document',
    'locations',
    'accounts',
    'catalog',
    'notifications',
    'categories',
    'orders',
    'ppd',
    'promotions',
    'sms',
    'users',
    'payments',
    'payouts',
    'web',
    'migration',
    'feeds',
    'reviews',
    'help',
    'django.contrib.admin',
    'communications',
    'lists',
    'activitystream',
    'compress',
    'debug_toolbar',
    'django_extensions',
    'profiling',
    'pagination',
    'dynamicloader',
    'pricing',
    #'cs',
    'tracking',
    'support',
    'complaints',
    'sellers',
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

API_SERVER = '192.168.91.101'
API_PORT = '8080'
API_PREFIX = '/chaupaati/'

DJANGO_SETTINGS_MODULE = 'settings'

PAYMENT_PAGE_PROTOCOL = 'https'

TINLA_URL = 'http://www.chaupaati.in'

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
DONT_SHOW_GOOGLE_ANALYTICS = False

ITEMS_PER_PAGE = 15
SCRATCH_CARD_MAX_USES = 1
CCD_SCRATCH_CARD_MAX_USES = 1
FG_SCRATCH_CARD_MAX_USES = 1
BB_SCRATCH_CARD_MAX_USES = 1

#CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_dots',)
#CAPTCHA_OUTPUT_FORMAT = '%(image)s <br/>Please enter the characters shown in the image<br/>%(text_field)s %(hidden_field)s '

# paginator settings 
INTERNAL_IPS = ('localhost', '127.0.0.1')
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}

# Import app settings. This is easier to manage than a large settings file
from app_settings import *


try:
    from local_settings import *
except ImportError:
    pass
logging.config.fileConfig(LOGGING_CONF)
