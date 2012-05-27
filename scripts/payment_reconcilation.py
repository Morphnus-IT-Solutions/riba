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

from orders.models import Order
from payments.models import PaymentAttempt
from decimal import Decimal
from django.http import HttpRequest
from accounts.models import ClientDomain
from django.db.models import Q
from django.db import transaction
from users.models import Phone

if __name__ == '__main__':
    request = HttpRequest()
    request.session = {}
    client = ClientDomain(domain='www.futurebazaar.com')
    request.client = client
    ph = Phone.objects.get(phone='9967442905')
    user = ph.user
    
    f = open('payment_reconciliation.txt','r')
    total_matches = 0
    pending_payments = 0
    for line in f:
        d = line.split(' ')
        ref_order_id = d[0]
        tx_id = d[1]
        amount = Decimal(d[2])
        payment_mode = d[3]
        try:
            pa = PaymentAttempt.objects.select_related('order').get(
                Q(Q(transaction_id=tx_id) | Q(pg_transaction_id=tx_id)),
                order__reference_order_id=ref_order_id, action='fulfil',
                payment_mode=payment_mode, status__in['paid','pending realization',
                'in verification'], amount=amount)
            with transaction.commit_on_success():
                if pa.status == 'pending realization':
                    pa.move_payment_state(request, new_state='paid', agent=user)
                    pending_payments += 1
                pa.action = 'captured'
                pa.save()
            total_matches += 1
        except PaymentAttempt.DoesNotExist:
            print 'No payment found with order id - %s, tx_id - %s' % (ref_order_id, tx_id)
        except Order.InventoryError, e:
            print 'Inventory Error for order %s - %s' % (ref_order_id, e.errors)
        except Exception, e:
            print 'Exception - order_id %s, tx_id %s - %s' % (ref_order_id, tx_id, repr(e))
    
    print 'total matches - %s, pending payments - %s' % (total_matches, pending_payments)
