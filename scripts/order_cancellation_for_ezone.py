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

from orders.models import Order, OrderItem, CancelledOrderItem
from catalog.models import Inventory
from utils.utils import get_ezoneonline
from datetime import datetime, timedelta
from orders.forms import OrderCancellationForm
from django.contrib.auth.models import User
from decimal import Decimal

def get_orders_booked_before_ten_days():
    ezone_client = get_ezoneonline()
    current_time = datetime.now()
    
    orders = Order.objects.filter(client = ezone_client,
        state = 'pending_order',
        modified_on__lte = (current_time + timedelta(days=-10)),
        modified_on__gte = datetime(2011,11,16,0,0,0),
        )

    return orders

class Request():
   method = 'POST'
   POST = {'cancellation_notes':'Cancelled automatically by system'} 
   user = User.objects.get(id=1187684)

request = Request()

if __name__ == '__main__':
    orders = get_orders_booked_before_ten_days()

    #orders = Order.objects.filter(reference_order_id='10071247670')
    for cart in orders:
        order_cancellation_form = OrderCancellationForm()
        error = None
        #cancelled_items = request.POST['cancelled_items'].split(',')
        order_notification = []
        order_items = cart.orderitem_set.all()
        if request.method == 'POST' and 'cancellation_notes' in request.POST:
            order_cancellation_form = OrderCancellationForm(request.POST)
            if order_cancellation_form.is_valid():
                next_action = 'action_2'#order_cancellation_form.cleaned_data.get('next_action', 'action_1')
                cart.state = 'cancelled'
                cart.save()
                try:
                    error = cart.cancel(request)
                    if error:
                        raise CancelOrderFailed

                    cart.save_history(request)
                    for order_item in order_items:
                        order_item.state = 'cancelled'
                        cancelled_order_item = CancelledOrderItem()

                        cancelled_order_item.order_item = order_item
                        cancelled_order_item.notes = order_cancellation_form.cleaned_data['cancellation_notes']
                        cancelled_order_item.refundable_amount = Decimal(str(order_item.payable_amount()))
                        if next_action == 'action_1':
                            cancelled_order_item.refund_status = 'pending'
                        if next_action == 'action_2':
                            cancelled_order_item.refund_status = 'not_required'
                        if next_action == 'action_3':
                            cancelled_order_item.refund_status = 'refunded'
                        cancelled_order_item.save()
                        order_item.save()
                    #order_items = cart.orderitem_set.all()
                    all_cancelled = True
                    for order_item in cart.orderitem_set.all():
                        if order_item.state != 'cancelled':
                            all_cancelled = False
                    cart.modified_on = datetime.now()
                    if all_cancelled:
                        cart.state = 'cancelled'
                    else:
                        cart.state = 'modified'
                    cart.save()
                    #cart.notify_cancelled_order(order_items, request)
                    #cart.update_blling()
                    #return HttpResponseRedirect('/orders/cancel/%s/cancelled' % (cart.id))
                except Exception as e:# CancelOrderFailed:
                    print 'cancel order failed'
                    print (e)
                    #log.exception("Order Cancellation failed for %s : %s" % (
                            #str(admin_order_id), error))
