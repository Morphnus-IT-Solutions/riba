import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fbsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

#from django.contrib.auth.models import *
#from django.contrib.contenttypes.models import *
#import pyExcelerator
#import random
#from django.core.mail import EmailMessage
#from django.core.exceptions import PermissionDenied
#from django.template import Context, Template
from inventory.models import Inventory
from datetime import datetime
#from django.db.models import *

if __name__ == '__main__':
    unprocessed_vi_entries = Inventory.objects.filter(
        processed = False,
        ends_on__lte = datetime.now(),
        type = 'virtual'
        )

    #If (bookings - bookings_adjustment) == 0, mark the entry as processed.
    for item in unprocessed_vi_entries:
        if (item.bookings - item.bookings_adjustment) == Decimal('0'):
            item.processed = True
            item.save()
