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

from users.models import Profile
from integrations.fbapi import users, orders, fbapiutils
from orders.models import *
from payments.models import PaymentAttempt
from datetime import datetime, timedelta
from atg.models import *


def test():
    sku = FtbSku.objects.get(pk='2576963').to_map()
    price_dict = {}
    offer_price = Decimal("0.00")
    list_price = Decimal("0.00")
    shipping_charges = Decimal("0.00")

    for price in sku['prices']:
        price_dict[price['price_list']] = price['price']

    # price list priorities. first future bazaar, then anonymous 
    list_price_priority = ['plist3350002', 'plist130002']
    sale_price_priority = ['plist3350003', 'plist130003']

    for price_list in list_price_priority:
        if price_list in price_dict:
            print price_list
            list_price = Decimal(price_dict[price_list])
            print list_price
            break

    for price_list in sale_price_priority:
        if price_list in price_dict:
            print price_list
            offer_price = Decimal(price_dict[price_list])
            print offer_price
            break

    if list_price < offer_price:
        list_price = offer_price

    if offer_price == Decimal("0.00"):
        offer_price = list_price

    print offer_price, list_price


if __name__ == '__main__':
    test()
