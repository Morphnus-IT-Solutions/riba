
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

from locations.models import *
from orders.models import *
from utils import utils


addresses = []
delivery_infos = DeliveryInfo.objects.filter(order__state='confirmed').exclude(order__user=None)

for delivery_info in delivery_infos:
    try:
        addr = delivery_info.address
        addresses.append(addr)
    except:
        pass
    for addr in addresses:
        address_book = AddressBook()
        address_book.address = addr.address
        address_book.city = addr.city
        address_book.country = addr.country
        address_book.pincode = addr.pincode
        address_book.state = addr.state
        address_book.profile = addr.profile
        address_book.name = addr.name
        address_book.phone = addr.phone
        address_book.email = addr.email
        address_book.defaddress = addr.defaddress
        print "Checking if address book exists : %s" % address_book.toString()
        if addr.profile:
            if not utils.is_address_book_present(address_book,addr.profile):
	        print "adding address book for...%s" % addr.profile
	        address_book.save()
