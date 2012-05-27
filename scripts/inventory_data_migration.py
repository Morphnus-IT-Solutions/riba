import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from django.contrib.auth.models import *
from django.contrib.contenttypes.models import *
from users.models import *
from analytics.models import *
import pyExcelerator
import random
from orders.models import *
from django.core.mail import EmailMessage
from django.core.exceptions import PermissionDenied
from django.template import Context, Template
from datetime import datetime
from django.db.models import *

from catalog.models import Inventory as CatalogInventory
from inventory.models import Inventory
from fulfillment.models import Dc
from datetime import datetime

if __name__ == '__main__':
    #Import data for Holii
    holii_client = Client.objects.get(name='Holii')
    holii_seller = Account.objects.get(name='holii')
    holii_dc = None
    try:
        holii_dc = Dc.objects.get(code='holii')
    except Dc.DoesNotExist:
        holii_dc = Dc.objects.create(code = 'holii',
            name = 'Holii DC',
            cod_flag = False,
            client = holii_client,
            address = 'Holii Global DC')


    catalog_inventory = CatalogInventory.objects.filter(
        rate_chart__seller = holii_seller)

    for item in catalog_inventory:
        try:
            inventory = Inventory.objects.get(
                rate_chart = item.rate_chart,
                dc = holii_dc,
                type = 'physical')
            inventory.stock = item.stock
            inventory.save()
        except Inventory.DoesNotExist:
            inventory = Inventory.objects.create(
                rate_chart = item.rate_chart,
                dc = holii_dc,
                stock = item.stock,
                type = 'physical',
                starts_on = datetime(1111,1,1),
                ends_on = datetime(9999,12,31))
        print 'done!'

    #Import data for World Holii
    wholii_client = Client.objects.get(name='World Holii')
    wholii_seller = Account.objects.get(name='World Holii')
    wholii_dc = None
    try:
        wholii_dc = Dc.objects.get(code='wholii')
    except Dc.DoesNotExist:
        wholii_dc = Dc.objects.create(code = 'wholii',
            name = 'World Holii DC',
            cod_flag = False,
            client = wholii_client,
            address = 'World Holii Global DC')

    catalog_inventory = CatalogInventory.objects.filter(
        rate_chart__seller = wholii_seller)

    for item in catalog_inventory:
        try:
            inventory = Inventory.objects.get(
                rate_chart = item.rate_chart,
                dc = wholii_dc,
                type = 'physical')
            inventory.stock = item.stock
            inventory.save()

        except Inventory.DoesNotExist:
            inventory = Inventory.objects.create(
                rate_chart = item.rate_chart,
                dc = wholii_dc,
                stock = item.stock,
                type = 'physical',
                starts_on = datetime(1111,1,1),
                ends_on = datetime(9999,12,31))
        print 'done!'

    #Import data for World Holii
    usholii_client = Client.objects.get(name='US Holii')
    usholii_seller = Account.objects.get(name='US Holii')
    usholii_dc = None
    try:
        usholii_dc = Dc.objects.get(code='uholii')
    except Dc.DoesNotExist:
        usholii_dc = Dc.objects.create(code = 'uholii',
            name = 'US Holii DC',
            cod_flag = False,
            client = usholii_client,
            address = 'US Holii Global DC')

    catalog_inventory = CatalogInventory.objects.filter(
        rate_chart__seller = usholii_seller)

    for item in catalog_inventory:
        try:
            inventory = Inventory.objects.get(
                rate_chart = item.rate_chart,
                dc = usholii_dc,
                type = 'physical')
            inventory.stock = item.stock
            inventory.save()
        except Inventory.DoesNotExist:
            inventory = Inventory.objects.create(
                rate_chart = item.rate_chart,
                dc = usholii_dc,
                stock = item.stock,
                type = 'physical',
                starts_on = datetime(1111,1,1),
                ends_on = datetime(9999,12,31))
        print 'done!'
