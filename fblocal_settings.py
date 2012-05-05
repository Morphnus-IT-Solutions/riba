FB_API_URL = 'http://new.futurebazaar.com'
FB_API_PORT = '8080'

UPLOAD_ROOT = '/home/saumil/uploads/u/futurebazaar'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'ecommerce',
        'USER': 'root',
        'PASSWORD': 'allagr2nd',
    },
    'tinla_slave': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'ecommerce',
        'USER': 'root',
        'PASSWORD': 'allagr2nd',
    },
}
DEBUG=True
