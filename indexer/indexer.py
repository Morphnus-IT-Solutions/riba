import pika
import logging
from django.conf import settings

log = logging.getLogger('request')

def send_index_request(obj, klass):
    server = getattr(settings, 'RABBIT_MQ_SERVER', None)
    if not server:
        return
 
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=server))
    channel = connection.channel()  
    channel.queue_declare(queue='index_queue', durable=True)
    channel.basic_publish(exchange='',
        routing_key='index_queue',
        body='%s:%s' % (klass, obj.pk),
        properties=pika.BasicProperties(
         delivery_mode = 2, # make message persistent
        ))
    log.info("Sent to index_queue %s:%s" % (klass, obj.pk))

def post_save_handler(sender, **kw):
    try:
        log.info("Got post save signal for %s" % sender)
        from orders.models import Order, OrderItem
        from fulfillment.models import Shipment, ShipmentItem
        from payments.models import PaymentAttempt, Refund
        obj = kw['instance']
        if isinstance(obj, Order):
            send_index_request(obj, 'order')
        if isinstance(obj, OrderItem):
            send_index_request(obj, 'orderitem')
        if isinstance(obj, Shipment):
            send_index_request(obj, 'shipment')
        if isinstance(obj, ShipmentItem):
            send_index_request(obj, 'shipmentitem')
        if isinstance(obj, PaymentAttempt):
            send_index_request(obj, 'paymentattempt')
        if isinstance(obj, Refund):
            send_index_request(obj, 'refund')
    except Exception, e:
        log.exception('Error handling post_save handler for %s' % sender)
