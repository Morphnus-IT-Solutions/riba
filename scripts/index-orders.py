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

from orders.models import *
from payments.models import *
from fulfillment.models import *

import pika
import logging
import time
from datetime import datetime
import Queue
import threading
log = logging.getLogger('fborder')

orders = Queue.Queue()
queues = [orders]

class Indexer(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.kill_rcvd = False

    def run(self):
        while not self.kill_rcvd:
            self.indexer()

    def indexer(self):
        log.info('Started indexer')
        while True:
            log.info('Indexer asleep')
            time.sleep(35)
            log.info('Indexer awake')
            for queue in queues:
                current_set = {}
                stop = False
                while not queue.empty():
                    if stop:
                        break
                    item = queue.get()
                    if (datetime.now() - item['t']).seconds < 35:
                        # Flag to break in the next loop:
                        stop = True
                    try:
                        # Get the object to index. We were returning entities before
                        # But but now we always return order and index all entities
                        # of the order
                        obj = get_object(item['body'])
                        if obj: 
                            if obj.id not in current_set:
                                obj.index_all()
                                current_set[obj.id] = True
                                log.info('Indexed %s. Order %s' % (
                                    item['body'], obj.id))
                        else:
                            log.error(
                            'Object not returned to index %s' % item['body'])
                    except (Order.DoesNotExist, OrderItem.DoesNotExist, 
                        PaymentAttempt.DoesNotExist, Refund.DoesNotExist,
                        Shipment.DoesNotExist, ShipmentItem.DoesNotExist):
                        log.error('Object not found to index %s' % item['body'])
                    except Exception, e:
                        log.exception('Error indexing %s' % item['body'])

def enqueue(obj, body):
    orders.put({'body':body, 'obj': obj, 't': datetime.now()})

def get_object(body):
    klass, pk = body.split(':')
    obj = None
    order = None

    if klass == 'order':
        obj = Order.objects.get(pk=pk)
        order = obj
        client_id = obj.client_id
        if not obj.support_state:
            return None
        if not obj.payment_mode:
            return None

    if klass == 'paymentattempt':
        obj = PaymentAttempt.objects.select_related('order').get(pk=pk)
        order = obj.order
        client_id = obj.order.client_id

    if klass == 'refund':
        obj = Refund.objects.select_related('order').get(pk=pk)
        order = obj.order
        client_id = obj.order.client_id

    if klass == 'orderitem':
        obj = OrderItem.objects.select_related('order').get(pk=pk)
        order = obj.order
        client_id = obj.order.client_id
        if not obj.order.support_state:
            return None
        if not obj.order.payment_mode:
            return None

    if klass == 'shipment':
        obj = Shipment.objects.select_related('order').get(pk=pk)
        order = obj.order
        client_id = obj.order.client_id

    if klass == 'shipmentitem':
        obj = ShipmentItem.objects.select_related(
            'order_item', 'order_item__order').get(pk=pk)
        order = obj.order_item.order
        client_id = obj.order_item.order.client_id

    if client_id != 5:
        return None

    if order.reference_order_id:
        if len(order.reference_order_id) != 10:
            return None
        if order.reference_order_id.startswith('503') or order.reference_order_id.startswith('504'):
            return None
    else:
        return None

    return order


def index(ch, method, properties, body, **kw):
    log.info('Got index request for %s' % body)
    try:
        klass, pk = body.split(':')
    except ValueError, e:
        log.error('Wrong message to index. Got %s' % body)

    acked = False

    try: 
        obj = get_object(body)

        if not obj:
            # None is returned only when object is found but we
            # do not want to index it
            ch.basic_ack(delivery_tag = method.delivery_tag)
            return True

        if obj:
            # Put to a queue, Indexing will happen after 60 secs.
            enqueue(obj, body)

    except (Order.DoesNotExist, OrderItem.DoesNotExist, 
        PaymentAttempt.DoesNotExist, Refund.DoesNotExist,
        Shipment.DoesNotExist, ShipmentItem.DoesNotExist):
        enqueue(None, body)
    except Exception, e:
        log.exception('Error processing index request %s' % body)

    ch.basic_ack(delivery_tag = method.delivery_tag)
    return True

try:
    t = Indexer()
    t.daemon = True
    t.start()

    # The rabbit mq stuff
    host = settings.RABBIT_MQ_SERVER
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.queue_declare(queue='index_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(index, queue='index_queue')
    channel.start_consuming()
except KeyboardInterrupt:
    print 'Killing indexer worker thread ...'
    t.kill_rcvd = True
