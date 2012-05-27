from django.db import models
from accounts.models import *
from datetime import datetime, timedelta
from indexer import indexer
import logging

log = logging.getLogger('fborder')

# Create your models here.

class Lsp(models.Model):
    code = models.CharField(max_length=6, unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name

#class ShipMode(models.Model):
#    transport_mode = models.CharField(max_length=8)
#    
#    def __unicode__(self):
#        return self.shipping_mode 


class ProductGroup(models.Model):
# Product group should be client based so that a product can be assigned only to a Product Group Id.
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=40, null=True)
    client = models.ForeignKey('accounts.Client', null=True)
    # Check for products that can be shipped only locally.
    local_tag = models.BooleanField()
    ship_mode = models.CharField(max_length=8)
    high_value_flag = models.BooleanField()
    threshold_amount = models.PositiveIntegerField(blank=True, null=True)
        
    def __unicode__(self):
        return self.name

class Dc(models.Model):
# A warehouse is defined by a client-DC pair.Same warehouse may belong to multiple clients and vice versa 
    code = models.CharField(max_length=6, db_index=True)
    name = models.CharField(max_length=100)
# COD is supported only for certain warehouses. Set paytype as true if COD is supported by that DC
    cod_flag = models.BooleanField()
    client = models.ForeignKey('accounts.Client')
    address = models.CharField(max_length=250)

    def __unicode__(self):
        return self.code

    class Meta:
        unique_together = ('code','client')

class LspZipgroup(models.Model):
    lsp = models.ForeignKey(Lsp)
    zipgroup_name = models.CharField(max_length=40)  
    zipgroup_code = models.CharField(max_length=3)

    def __unicode__(self):
        return self.zipgroup_name

    class Meta:
        unique_together = ('zipgroup_name','lsp')

# Replaced by high value tag
#class ProductGroupZipgroup(models.Model):
## Certain products may be shipped only at certain pincodes (eg: Mobiles)    
#    product_group = models.ForeignKey(ProductGroup)
#    zipgroup = models.ForeignKey(LspZipgroup)  
#    
#    def __unicode__(self):
#        return self.name
#
#    class Meta:
#        unique_together = ('zipgroup','product_group')

#class LspProductGroup(models.Model):
## Certain product groups will never be shipped by an LSP   
## Both LSP and Zipgroup maps are needed since Product group needs to pass LSP filter and then Zip group filter. 
## Also together it satisfes cases when a LSP doesnt deliver a Product group in a given Zip Group   
#    product_group = models.ForeignKey(ProductGroup)
#    lsp = models.ForeignKey(Lsp)  
#    
#    def __unicode__(self):
#        return self.name
#
#    class Meta:
#        unique_together = ('lsp','product_group')

class ArticleProductgroup(models.Model):
    article_id = models.CharField(max_length=16)
    product_group = models.ForeignKey(ProductGroup)

    class Meta:
        unique_together = ('article_id','product_group')

class DcZipgroup(models.Model):
# Used for locally shippable product groups only, usual LSP Future Logistics.
    dc = models.ForeignKey(Dc)
    zipgroup = models.ForeignKey(LspZipgroup)  
    lsp = models.ForeignKey(Lsp, null=True) 
    
    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('zipgroup','dc','lsp')

class PincodeZipgroupMap(models.Model):
    zipgroup = models.ForeignKey(LspZipgroup)
    pincode = models.CharField(max_length=6)
    # Prepaid is by default accepted by all, check for COD only, hence the field can be a boolean true/false. True- accept COD, False-dont accept COD
    cod_flag = models.BooleanField()
    #For high value products
    high_value = models.BooleanField()
    # LSP assignment has a precedence for a Zip Group. 
    supported_product_groups = models.CharField(max_length=100,blank=True,null=True)
    lsp_priority = models.PositiveIntegerField(max_length=1, blank=True, null=True)            

    def __unicode__(self):
        return "Pincode %s is in Zipgroup %s" % (self.pincode, self.zipgroup)
    
    class Meta:
        unique_together = ('zipgroup','pincode') 

class LspDeliveryChart(models.Model):
    dc = models.ForeignKey(Dc)
   #shipping_mode = models.ForeignKey(ShippingMode)
    zipgroup = models.ForeignKey(LspZipgroup)
# Maintain separate columns for each delivery type
    transit_time = models.PositiveIntegerField()
    ship_mode = models.CharField(max_length=8)
#   days_to_delv_express  = models.PositiveIntegerField()
    
    def __unicode__(self):
        return self.dc 
    class Meta:
        unique_together = ('zipgroup','dc','ship_mode') 

class Shipment(models.Model):
    order = models.ForeignKey('orders.Order', related_name='shipments', db_index=True)
    tracking_number = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    delivery_number = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    lsp = models.ForeignKey(Lsp, null=True, blank=True, related_name='shipments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal(0))
    invoiced_on = models.DateTimeField(null=True, blank=True)
    pickedup_on = models.DateTimeField(null=True, blank=True)
    delivered_on = models.DateTimeField(null=True, blank=True)
    returned_on = models.DateTimeField(null=True, blank=True)
    dc = models.ForeignKey(Dc, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    expected_delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=25, null=True, blank=True, db_index=True)

    #Exceptions
    InsufficientData = type('InsufficientData', (Exception,), {})
    InvalidOperation = type('InvalidOperation', (Exception,), {})

    class Meta:
        unique_together = ('order','delivery_number')

    _promised_shipping_date = None
    def get_promised_shipment_date(self):
        if self._promised_shipping_date:
            return self._promised_shipping_date

        expected_delivery_date = None
        for shipment_item in self.shipment_items.select_related(
            'order_item', 'order_item__sap_order_item').all():
            if shipment_item.order_item:
                if shipment_item.order_item.expected_delivery_date:
                    if not expected_delivery_date:
                        expected_delivery_date = shipment_item.order_item.expected_delivery_date
                    elif expected_delivery_date < shipment_item.order_item.expected_delivery_date:
                        expected_delivery_date = shipment_item.order_item.expected_delivery_date
                    
        self._promised_shipping_date = expected_delivery_date + timedelta(days=-4)
        return self._promised_shipping_date


    def index(self, **kw):
        ''' Indexes the shipment object in solr '''
        from utils import solrutils 
        shipment_doc = self.get_shipment_solr_doc()

        order_doc = kw.get('order_doc')
        if not order_doc:
            order_doc = self.order.get_order_solr_doc()

        shipment_doc.update(order_doc)
        shipment_doc['doc_type'] = 'shipment'
        shipment_doc['unique_key'] = '%s%s' % (shipment_doc['doc_type'], self.id)

        solrutils.order_add_data(shipment_doc)

    def get_shipment_solr_doc(self):
        shipment_doc = {
            'order_id': self.order_id,
            'doc_type': 'shipment',
            'shipment_pk': self.id,
            'shipment_amount': '%.2f' % self.amount,
            'shipment_tracking_number': self.tracking_number or '',
            'shipment_delivery_number': self.delivery_number or '',
            'shipment_invoice_number': self.invoice_number or '',
            'shipment_created_on': self.created_on,
            'shipment_status': self.status
        }

        if self.lsp:
            shipment_doc['shipment_lsp'] = self.lsp.name
        if self.dc:
            shipment_doc['shipment_dc'] = self.dc.code
        if self.invoiced_on:
            shipment_doc['shipment_invoiced_on'] = self.invoiced_on
        if self.pickedup_on:
            shipment_doc['shipment_pickedup_on'] = self.pickedup_on
        if self.delivered_on:
            shipment_doc['shipment_delivered_on'] = self.delivered_on
        if self.expected_delivery_date:
            shipment_doc[
                'shipment_expected_delivery_date'] = self.expected_delivery_date
        return shipment_doc
    
    def move_shipment_state(self, request, **kwargs):
        new_state = kwargs.get('new_state')
        agent = kwargs.get('agent')
        shipment_item = kwargs.get('shipment_item')
        o_log = kwargs.get('order_log')

        data = kwargs.get('data',{})
        order = self.order
        
        from orders.models import OrderLog, OrderItemLog
        if not o_log:
            shipment_logs = ShipmentLog.objects.select_related('order_log').filter(
                shipment=self, action='status', status=new_state).order_by('-id')[:1]
            if shipment_logs:
                shipment_log = shipment_logs[0]
                o_log = shipment_log.order_log
            else:
                o_log = OrderLog(order=order, profile=agent, action='shipment')
                shipment_log = ShipmentLog(shipment=self, action='status', status=new_state,
                    delivery_number=self.delivery_number)
        
        valid_states = []
        if not self.status:
            valid_states = ['delivery created']
        if self.status == 'delivery created':
            valid_states = ['invoiced','deleted']
        elif self.status == 'invoiced':
            valid_states = ['shipped','deleted','delivered','returned','undeliverable']
        elif self.status == 'shipped':
            valid_states = ['delivered','returned','undeliverable']
        elif self.status == 'undeliverable':
            valid_states = ['delivered','returned','undeliverable']
        
        if (new_state != self.status) and (new_state not in valid_states):
            raise self.InvalidOperation
        
        self.status = new_state
        shipment_log.status = new_state
        if new_state == 'delivery created':
            delivery_number = data.get('delivery_number')
            dc = data.get('dc')
            tracking_number = data.get('tracking_number')
            lsp = data.get('lsp')
            if not (delivery_number and dc):
                raise self.InsufficientData
            self.delivery_number = delivery_number
            self.dc = dc
            shipment_log.delivery_number = delivery_number
            shipment_log.dc = dc
            if tracking_number:
                self.tracking_number = tracking_number
                shipment_log.tracking_number = tracking_number
            if lsp:
                self.lsp = lsp
                shipment_log.lsp = lsp
            self.save()
            
            if shipment_item:
                if shipment_item.quantity == shipment_item.order_item.qty:
                    item_status = 'delivery created'
                elif shipment_item.quantity < shipment_item.order_item.qty:
                    item_status = 'partial stock'
                else:
                    raise Exception('shipment item quantity (%s) greater than order item quantity (%s)' %
                    (shipment_item.quantity, shipment_item.order_item.qty))
                
                if not o_log.id:
                    o_log.save()
                shipment_log.order_log = o_log
                shipment_log.save()
                if shipment_item.sap_order_item.status not in ['cancelled', item_status]:
                    shipment_item.sap_order_item.move_state(request, new_state=item_status, order_log=o_log)
        
        elif new_state == 'invoiced':
            invoice_number = data.get('invoice_number')
            invoiced_on = data.get('invoiced_on')
            tracking_number = data.get('tracking_number')
            lsp = data.get('lsp')
            if not (invoice_number and invoiced_on):
                raise self.InsufficientData
            self.invoice_number = invoice_number
            self.invoiced_on = invoiced_on
            shipment_log.invoice_number = invoice_number
            if (not self.tracking_number) and tracking_number:
                self.tracking_number = tracking_number
                shipment_log.tracking_number = tracking_number
            if (not self.lsp) and lsp:
                self.lsp = lsp
                shipment_log.lsp = lsp
            self.save()
            if order.support_state != 'invoiced' and order.all_items_invoiced(request):
                order.support_state = 'invoiced'
                order.save()
                o_log.status = 'invoiced'
            o_log.save()
            shipment_log.order_log = o_log
            shipment_log.save()
        
        elif new_state == 'deleted':
            self.save()
            if order.support_state != 'confirmed':
                order.support_state = 'confirmed'
                order.save()
                o_log.status = 'confirmed'

            o_log.save()
            shipment_log.order_log = o_log
            shipment_log.save()

            shipment_items = self.shipment_items.select_related('sap_order_item').all()
            for shipment_item in shipment_items:
                shipment_item.sap_order_item.status = 'awaiting delivery creation'
                shipment_item.sap_order_item.save()
                OrderItemLog.objects.create(order_item=shipment_item.order_item, order_log=o_log,
                    action='status', status='awaiting delivery creation')

        else:
            tracking_number = data.get('tracking_number')
            lsp = data.get('lsp')
            pickedup_on = data.get('pickedup_on')
            delivered_on = data.get('delivered_on')
            if not (tracking_number and lsp):
                raise self.InsufficientData
            self.tracking_number = tracking_number
            self.lsp = lsp
            self.pickedup_on = pickedup_on
            shipment_log.tracking_number = tracking_number
            shipment_log.lsp = lsp
            if new_state == 'delivered':
                self.delivered_on = delivered_on or datetime.now()
            elif new_state == 'returned':
                self.returned_on = datetime.now()
            self.save()
            if new_state == 'shipped' and order.all_items_shipped(request):
                order.support_state = 'shipped'
                order.save()
                o_log.status = 'shipped'
                try:
                    # can remove once we are confident about emails
                    order.notify_shipped_order(request, self)
                except:
                    pass
            elif new_state == 'delivered' and order.all_items_delivered(request):
                order.support_state = 'delivered'
                order.save()
                o_log.status = 'delivered'
                if order.payment_mode == 'cod':
                    pas = order.get_payments(request, filter=dict(status='pending realization',
                        payment_mode='cod', amount=order.payable_amount)).order_by('-id')
                    i = 0
                    for pa in pas:
                        if i == 0:
                            pa.move_payment_state(request, new_state='paid', order_log=o_log)
                        else:
                            pa.status = 'rejected'
                            pa.save()
                        i += 1
            elif new_state == 'returned' and order.all_items_returned(request):
                order.support_state = 'returned'
                order.save()
                o_log.status = 'returned'
            elif new_state == 'undeliverable' and order.all_items_undeliverable(request):
                order.support_state = 'undeliverable'
                order.save()
                o_log.status = 'undeliverable'
            o_log.save()
            shipment_log.order_log = o_log
            shipment_log.save()
        return o_log

    def change_lsp(self, request, **kwargs):
        data = kwargs.get('data',{})
        agent = kwargs.get('agent')
        o_log = kwargs.get('order_log')
        
        lsp = data.get('lsp')
        tracking_number = data.get('tracking_number')
        if not lsp:
            return
        
        from orders.models import OrderLog
        if not o_log:
            o_log = OrderLog(order=self.order, profile=agent, action='shipment')
            shipment_log = ShipmentLog(shipment=self, action='update',
                delivery_number=self.delivery_number)

        self.lsp = lsp
        self.tracking_number = tracking_number
        self.save()
        shipment_log.lsp = lsp
        shipment_log.tracking_number = tracking_number
        
        o_log.save()
        shipment_log.order_log = o_log
        shipment_log.save()
        return
models.signals.post_save.connect(indexer.post_save_handler, sender=Shipment)


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(Shipment, related_name='shipment_items')
    order_item = models.ForeignKey('orders.OrderItem', related_name='shipment_items')
    sap_order_item = models.ForeignKey('orders.SAPOrderItem', null=True, blank=True, default=None, related_name='shipment_items')
    quantity = models.IntegerField(default=0)
    part_id = models.PositiveIntegerField(null=True, blank=True, default=None)

    class Meta:
        unique_together = ('shipment','sap_order_item','part_id')
models.signals.post_save.connect(indexer.post_save_handler, sender=ShipmentItem)

#will not be using this model - prady
class ShipmentStatus(models.Model):
    shipment = models.ForeignKey(Shipment, related_name='statuslog')
    status = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class ShipmentLog(models.Model):
    shipment = models.ForeignKey(Shipment, related_name='shipment_log')
    order_log = models.ForeignKey('orders.OrderLog', related_name='shipment_log')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=(
        ('status','status'),    #status change
        ('update','update')))   #lsp updates
    status = models.CharField(max_length=30, null=True, blank=True, default=None)
    delivery_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    invoice_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    tracking_number = models.CharField(max_length=50, null=True, blank=True, default=None)
    lsp = models.ForeignKey(Lsp, null=True, blank=True, default=None, related_name='+')
    dc = models.ForeignKey(Dc, null=True, blank=True, default=None, related_name='+')
    notes = models.TextField(null=True, blank=True, default=None)
    
    def get_class_name(self):
        return 'ShipmentLog'
