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

from orders.models import Order
from atg.models import DcsppOrder, FtbOrder
from datetime import datetime, timedelta
import logging
log = logging.getLogger('fborder')
ATG_CLIENTS = (5, 7)

def send_payment_reminder(order):
    log.info('Send payment reminder for %s, %s created on %s' % (order.id, order.reference_order_id, order.timestamp))
    from notifications.paymentremindernotification import PaymentReminderNotification
    n = PaymentReminderNotification(order, groups=('buyer',))
    n.send()

def send_reminder_email():
    now = datetime.now()
    qs = Order.objects.using('tinla_slave').filter(state='pending_order',
        timestamp__lte = now + timedelta(days=-2),
        timestamp__gte = now + timedelta(days=-2, hours=-1)
        )
    for order in qs:
        if order.client_id in ATG_CLIENTS:
            try:
                atg_order = FtbOrder.objects.select_related('order').get(pk=order.reference_order_id)
                # Check if atg order is still not paid
                if not atg_order.sap_created_date:
                    # Order not sent to SAP, but can still be in queue
                    if atg_order.order.order_state.lower() not in ('submitted','failed'):
                        # order_state is submitted for those in queue and failed
                        # for those where sap submission failed
                        try:
                            send_payment_reminder(order)
                        except Exception, e:
                            log.exception('Error sending reminder email for order %s' % order.reference_order_id)
                        # we can no send the notification
            except FtbOrder.DoesNotExist:
                log.error(
                    'Order %s not found in atg for sending payment reminder' % order.reference_order_id) 
            except DcsppOrder.DoesNotExist:
                log.error(
                    'Order %s not found in atg for sending payment reminder' % order.reference_order_id) 
        else:
            send_payment_reminder(order)


if __name__ == '__main__':
    send_reminder_email()
