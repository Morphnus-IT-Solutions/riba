import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.wholiisettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from orders.models import Order, OrderItem
from catalog.models import Inventory
from utils.utils import get_wholii_client
from datetime import *

if __name__ == '__main__':
    #1) Get the list of all orders in last 10 minutes where-
    #   a) order.state = 'pending_order'
    #   b) payment_mode in instant payment mode
    #   c) payment_attempt.status is 'rejected'
    wholii_client = get_wholii_client()
    current_time = datetime.now()

    orders = Order.objects.filter(client=wholii_client,
        state = 'pending_order',
        payment_mode__in = ['netbanking','credit-card','credit-card-emi-web','debit-card','payback'] ,
        modified_on__gte = (current_time + timedelta(minutes=-60)),
        modified_on__lte = (current_time + timedelta(minutes=-10)),
        )
    
    for order in orders:
        is_all_payment_attempts_rejected = True
        payment_attempts = order.paymentattempt_set.all()
        
        if payment_attempts:
            for pa in order.paymentattempt_set.all():
                if pa.state in ['approved','pending','captured']:
                    is_all_payment_attempts_rejected = False
                
            if is_all_payment_attempts_rejected:
                for item in order.orderitem_set.all():
                    item.is_inventory_blocked = False
                    item.save()
                        
                order.update_inventory('add')

