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

from accounts.models import *
from orders.models import *

QTY = 1
ORDER_ID = 2669673
SELLER_NAME = 'infomedia18'
SKU = 'workshop5'

class Request:
    method = 'POST'
    POST = {'qty':QTY}
    #clientdomain = ClientDomain.objects.get(id=36)
    clientdomain = ClientDomain.objects.get(domain='www.chaupaati.in')

request = Request()

order = Order.objects.get(id=ORDER_ID)

if order.orderitem_set.all():
    #orderitems = OrderItems.objects.get(order=order, seller_rate_chart=rate_chart)
    print 'Orderitem already present in this order'
else:
    seller = Accounts.objects.get(name=SELLER_NAME)
    rate_chart = SellerRateChart.objects.get(seller=seller,sku=SKU)
    #order.add_item(request,rate_chart)
    print 'Added orderItem successfully'
