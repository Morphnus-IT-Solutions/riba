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

from payments.models import PaymentAttempt
from datetime import datetime

def check_orderid_change():
    payment_attempts = PaymentAttempt.objects.select_related(
        'order').filter(
        created_on__gte = datetime(year=2011, month=6, day=1)).exclude(
        gateway='cash').exclude(gateway='deposit').exclude(
        gateway='icici').exclude(gateway='moto').exclude(
        gateway='mail').exclude(gateway='transfer')

    confimred_payments = payment_attempts.filter(status='approved')
    print 'Confirmed payments: %s' % confimred_payments.count()

    for attempt in confimred_payments:
        print '%s, %s, %s, %s, %s' % (attempt.gateway,
            attempt.order.payment_realized_on,
            attempt.order.reference_order_id,
            attempt.amount,
            attempt.transaction_id)
    
    

    

if __name__ == '__main__':
    check_orderid_change()
