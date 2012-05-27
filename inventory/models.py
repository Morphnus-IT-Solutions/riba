from django.db import models, connections
from django.db.models.query import QuerySet
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from decimal import Decimal
from utils import utils
import logging

log = logging.getLogger('fborder')

# Create your models here.
class InventoryQuerySet(QuerySet):
    #DO NOT USE 'select_related' IF YOU WANT TO USE for_update()
    def for_update(self):
        if 'sqlite' in connections[self.db].settings_dict['ENGINE'].lower():
            return self
        sql, params = self.query.get_compiler(self.db).as_sql()
        return self.model._default_manager.raw(sql.rstrip() + ' FOR UPDATE', params)

class InventoryManager(models.Manager):
    def get_query_set(self):
        return InventoryQuerySet(self.model, using=self._db)

class Inventory(models.Model):
    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    dc = models.ForeignKey('fulfillment.Dc',null=True,blank=True)
    type = models.CharField(max_length=25,default='physical',choices=(
        ('physical','Physical'),
        ('virtual','Virtual'),
        ('backorder','Backorder'),
        ('madetoorder','Made to Order'),
        ('preorder','Pre-order')))
    stock = models.DecimalField(max_digits=7, decimal_places=2,
        null=True, blank=True, default=0)

    '''
    For type = 'physical', set starts_on=1-1-1111 and ends_on=31-12-9999
    as we always want physical stock entries to be active.
    '''
    starts_on = models.DateTimeField(blank=True, null=True, db_index=True)
    ends_on = models.DateTimeField(blank=True, null=True, db_index=True)
    
    #In case of type='virtual', either of the expected_on or expected_in
    #should be non-null.
    #In case of VI, we store the date when the stock is actually 
    #expected in warehouse.
    expected_on = models.DateTimeField(blank=True, null=True, default=None)
    #For back-to-back orders, mention stock is expected in how many days
    #(i.e. sourcing time) after the order received.
    expected_in = models.PositiveIntegerField(null=True, blank=True, default=None)

    #Against orderitem bookings, we increment this column instead of 
    #decrementing stock column.
    bookings = models.DecimalField(max_digits=7, decimal_places=2,
        null=True, blank=True, default=0)

    #Will be used only for type=physical. (for VI, outward=0)
    #will store actual outward quantity received from SAP.
    outward = models.DecimalField(max_digits=7, decimal_places=2,
        null=True, blank=True, default=0)

    #At each DC level, some quantity is reserved for damaged goods.
    #For VI entries, threshold=0.
    threshold = models.DecimalField(max_digits=7, decimal_places=2,
        null=True, blank=True, default=0)

    ''' 
    In case of VI, when we receive inward event from SAP, consider usecase:
    stock = 100
    bookings = 50
    starts_on <= current time <= ends_on,
    AND we receive inward = 70, then -
    1) we set booking adjustment = 50.
    2) For (70-50)=20, we add 20 to physical stock for this (rate_chart, dc)
    3) As we have already added 20 corresponding to VI to physical stock, 
       incorporate that by incrementing stock_adjustment by 20 and while 
       computing A.T.S., we always do (stock-stock_adjustment).
    '''
    stock_adjustment = models.DecimalField(max_digits=7, decimal_places=2, 
        null=True, blank=True, default=0)

    #In case of VI, upon receiving actual stock against preorders, increment
    #bookings_adjustment. 
    #Note that bookings_adjustment <= bookings ALWAYS.
    bookings_adjustment = models.DecimalField(max_digits=7, decimal_places=2,
        null=True, blank=True, default=0)

    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    
    #To control whether we want to use this entry or not.
    is_active = models.BooleanField(default=True)
    
    #In case of VI, when A.T.S.=0, set processed=True.
    #In case of physical, processed should always be False.
    processed = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, 
        default=datetime.now(), db_index = True)

    objects = InventoryManager()

    def save(self, *args, **kwargs):
        if self.id == None and self.type == 'physical':
            try:
                conflicting_inventory = Inventory.objects.get(
                    rate_chart = self.rate_chart,
                    dc = self.dc,
                    type = 'physical')
                raise ValidationError(
                    'Cannot have multiple entries for (rate_chart,dc) combination with type=physical')
            except Inventory.DoesNotExist:
                pass
        super(Inventory, self).save(*args, **kwargs)

    def get_remaining_booking_adjustment(self):
        bookings = Decimal('0')
        if self.bookings:
            bookings = self.bookings
   
        bookings_adjustment = Decimal('0')
        if self.bookings_adjustment:
            bookings_adjustment = self.bookings_adjustment

        adjustment = (bookings - bookings_adjustment)
        if adjustment > Decimal('0'):
            return adjustment

        return Decimal('0')

    def compute_ats(self):
        stock = Decimal('0')
        if self.stock:
            stock = self.stock

        stock_adjustment = Decimal('0')
        if self.stock_adjustment:
            stock_adjustment = self.stock_adjustment

        bookings = Decimal('0')
        if self.bookings:
            bookings = self.bookings

        outward = Decimal('0')
        if self.outward:
            outward = self.outward

        threshold = Decimal('0')
        if self.threshold:
            threshold = self.threshold

        ats = (stock - stock_adjustment - bookings - outward - threshold)
        if ats > Decimal('0'):
            return ats
                
        return Decimal('0')

    def get_ats_for_future_timeslots(self):
        if self.is_active:
            return self.compute_ats()
        return Decimal('0')

    def get_available_stock(self, **kwargs):
        current_time = datetime.now()
        if self.is_active and (self.starts_on <= current_time) and (current_time <= self.ends_on):
            return self.compute_ats()
        return Decimal('0')

    def increment_virtual_inventory(self, request, quantity, inventory_log):
        from inventory.views import log_increment_virtual_inventory
        current_time = datetime.now()
        log_fields = {}
        errors = []

        if inventory_log and quantity:
            from inventory.views import log_increment_physical_inventory
            was_stock_adjustment = self.stock_adjustment
            was_bookings_adjustment = self.bookings_adjustment

            if self.starts_on <= current_time and current_time <= self.ends_on:
                self.stock_adjustment -= quantity
            else:
                self.bookings_adjustment += quantity
            self.save()

            new_stock_adjustment = self.stock_adjustment
            new_bookings_adjustment = self.bookings_adjustment

            #Set logging fields.
            log_increment_virtual_inventory(request, self, 
                inventory_log.orderitem, inventory_log.lsp,
                was_stock_adjustment, new_stock_adjustment,
                was_bookings_adjustment, new_bookings_adjustment)
            
            '''
            Now, check if product is out of stock and because of this release of 
            inventory, stock got added back, then update solr index and make 
            product available on site.
            '''
            if self.rate_chart.stock_status == 'outofstock':
                global_stock =  self.rate_chart.get_global_inventory(request)
                if global_stock:
                    self.rate_chart.stock_status = 'instock'
                    self.rate_chart.save(using='default')
                    self.rate_chart.product.update_solr_index()
        else:
            errors.append('Cannot update inventory for %s (%s)' % (orderitem.seller_rate_chart.product.title, ordeitem.seller_rate_chart.sku))

        return errors

    def increment_physical_inventory(self, request, quantity, inventory_log, **kwargs):
        #from web.views.sap_views import inward
        from inventory.views import log_increment_physical_inventory
        log_fields = {}
        errors = []

        if inventory_log and quantity:
            was_stock = self.stock
            #Actually, update the inventory.
            #Increment the bookings counter by orderitem quantity.
            self.stock += quantity
            self.save()
            new_stock = self.stock

            #Log the inventory update.
            log_increment_physical_inventory(request, self, 
                inventory_log.orderitem, inventory_log.lsp, was_stock, new_stock)

            #Now, as we have got physical inward, flush the queue.(To be done)
            #queue_flush_errors = inward(self.rate_chart, self.dc, quantity)

            '''
            Now, check if product was out of stock and because of this release of 
            inventory, stock got added back, then update solr index and make 
            product available on site.
            '''
            if self.rate_chart.stock_status == 'outofstock':
                global_stock =  self.rate_chart.get_global_inventory()
                if global_stock:
                    rate_chart.stock_status = 'instock'
                    rate_chart.save(using='default')
                    rate_chart.product.update_solr_index()
        else:
            errors.append('Sorry, %s (%s) is currently out of stock!!!' % (orderitem.seller_rate_chart.product.title, ordeitem.seller_rate_chart.sku))

        return errors

    def block_inventory(self, request, **kwargs):
        orderitem = kwargs.get('orderitem', None)
        quantity = kwargs.get('quantity', None)
        lsp_code = kwargs.get('lsp', None)
        sap_event = kwargs.get('sap_event', None)
        lsp = utils.get_lsp(lsp_code)
        log_fields = {}
        errors = []

        if (orderitem or sap_event) and quantity:
            log.info('actually blocking the inventory for inventory.id = %s' % self.id)
            from inventory.views import log_block_inventory
            was_bookings = self.bookings
            log.info('bookings = %s' % self.bookings)
            log.info('qty = %s' % quantity)
            #Actually, update the inventory.
            #Increment the bookings counter by orderitem quantity.
            self.bookings += quantity
            self.save()
            log.info('blocked the inventory for inventory.id = %s' % self.id)
            log.info('bookings = %s' % self.bookings)
            new_bookings = self.bookings

            log_block_inventory(request, self, orderitem, lsp, sap_event, 
                was_bookings, new_bookings)
        else:
            if orderitem:
                errors.append('Sorry, %s (%s) is currently out of stock!!!' % (orderitem.seller_rate_chart.product.title, orderitem.seller_rate_chart.sku))
            elif sap_event:
                errors.append('Sorry, %s (%s) is currently out of stock!!!' % (sapevent.rate_chart.product.title, sap_event.rate_chart.sku))

        return errors

    def perform_booking_adjustments(self, request, **kwargs):
        from inventory.views import log_booking_adjustments
        quantity = kwargs['quantity']
        sap_event = kwargs['sap_event']
        orderitem = kwargs['orderitem']
        if quantity:
            was_bookings_adjustment = self.bookings_adjustment
            self.bookings_adjustment += quantity
            self.save()
            new_bookings_adjustment = self.bookings_adjustment
            log_booking_adjustments(request, self, sap_event,
                orderitem, was_bookings_adjustment, new_bookings_adjustment)
        return

    def perform_stock_adjustment(self, request, **kwargs):
        from inventory.views import log_stock_adjustment
        stock_adjustment = kwargs['stock_adjustment']
        sap_event = kwargs['sap_event']
        was_stock_adjustment = self.stock_adjustment
        self.stock_adjustment += stock_adjustment
        self.save()
        new_stock_adjustment = self.stock_adjustment
        log_stock_adjustment(request, self, sap_event,
            was_stock_adjustment, new_stock_adjustment)
        return

    def update_physical_stock(self, request, **kwargs):
        from inventory.views import log_update_physical_stock
        stock = kwargs['stock']
        sap_event = kwargs['sap_event']
        was_stock = self.stock
        self.stock += stock
        self.save()
        new_stock = self.stock
        log_update_physical_stock(request, self, sap_event,
            was_stock, new_stock)
        return

    def update_outward(self, request, **kwargs):
        from inventory.views import log_update_outward
        outward = kwargs['outward']
        sap_event = kwargs['sap_event']
        was_outward = self.outward
        self.outward += outward
        self.save()
        new_outward = self.outward
        log_update_outward(request, self, sap_event,
            was_outward, new_outward)
        return

    def mark_entry_as_procesed(self):
        self.processed = True
        self.save()
        return

    def __unicode__(self):
        return 'Stock for %s(SKU=%s)' % (self.rate_chart.product.title, self.rate_chart.sku)

class InventoryDcLspResolution(models.Model):
    orderitem = models.ForeignKey('orders.OrderItem')
    dc = models.ForeignKey('fulfillment.Dc')
    lsp = models.ForeignKey('fulfillment.Lsp')
    stock_allocated = models.BooleanField(default=False, db_index=True)
    stock_to_be_allocated = models.PositiveIntegerField(default=0)
    expected_stock_arrival = models.DateTimeField(
        blank=True, null=True, default=None, db_index=True)
    expected_shipping_date = models.DateTimeField(
        blank=True, null=True, default=None, db_index=True)
    expected_delivery_date = models.DateTimeField(
        blank=True, null=True, default=None, db_index=True)
    type = models.CharField(max_length=25,default='physical',choices=(
        ('physical','Physical'),
        ('backorder','Backorder'),
        ('madetoorder','Made to Order'),
        ('preorder','Pre-order')))
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    is_valid = models.BooleanField(default=True, db_index=True)

    def set_dclsp_stock_allocated_flag(self, request, **kwargs):
        from inventory.views import log_set_dclsp_stock_allocated_flag
        sap_event = kwargs.get('sap_event', None)
        was_dclsp_stock_allocated = self.stock_allocated
        self.stock_allocated = True
        self.save()
        new_dclsp_stock_allocated = self.stock_allocated
        log_set_dclsp_stock_allocated_flag(request, self, sap_event,
            was_dclsp_stock_allocated, new_dclsp_stock_allocated)
        return

    def __unicode__(self):
        return 'Orderitem.id=%s, DC=%s, LSP=%s' % (self.orderitem.id, self.dc.code, self.lsp.code) 

class InventoryBackorder(models.Model):
    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    dc = models.ForeignKey('fulfillment.Dc',null=True,blank=True)
    backorderable = models.BooleanField(default=False)
    expected_in = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('rate_chart','dc')

    def book_backorder(self, request, **kwargs):
        log_fields = {}
        orderitem = kwargs.get('orderitem', None)
        lsp = kwargs.get('lsp', None) 
        errors = []

        #Set logging fields.
        if orderitem and lsp:
            from inventory.views import log_book_backorder
            log_book_backorder(request, self, orderitem, lsp)
        else:
            errors.append('Sorry, %s (%s) is currently out of stock!!!' % (orderitem.seller_rate_chart.product.title, ordeitem.seller_rate_chart.sku))

        return errors

    def __unicode__(self):
        return 'Backorderable for %s (sku=%s) = %s' % (self.rate_chart.product.title, self.rate_chart.sku, self.backorderable)

class InventoryStoLog(models.Model):
    orderitem = models.ForeignKey('orders.OrderItem') 
    from_dc = models.ForeignKey('fulfillment.Dc',related_name='from_dc')
    to_dc = models.ForeignKey('fulfillment.Dc',related_name='to_dc')
    ack_received = models.BooleanField(default=False)
    stock_allocated = models.BooleanField(default=False)
    stock_to_be_allocated = models.PositiveIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_on = models.DateTimeField(auto_now=True)
    is_valid = models.BooleanField(default=True, db_index=True)

    def set_sto_stock_allocated_flag(self, request, **kwargs):
        from inventory.views import log_set_sto_stock_allocated_flag
        sap_event = kwargs.get('sap_event', None)
        was_sto_stock_allocated = self.stock_allocated
        self.stock_allocated = True
        self.save()
        new_sto_stock_allocated = self.stock_allocated
        log_set_sto_stock_allocated_flag(request, self, sap_event,
            was_sto_stock_allocated, new_sto_stock_allocated)
        return

    def set_sto_ack(self, request, **kwargs):
        from inventory.views import log_sto_ack
        sap_event = kwargs.get('sap_event', None)
        was_sto_ack_received = self.ack_received        
        #Set ack_received to True.
        self.ack_received = True
        self.save()
        new_sto_ack_received = self.ack_received

        #Set logging fields.
        log_sto_ack(request, self, sap_event,
            was_sto_ack_received, new_sto_ack_received)
        return

    def __unicode__(self):
        return 'STO from DC=%s to DC=%s for OrderItem.id = %s' % (self.from_dc.code, self.to_dc.code, self.orderitem.id)

class SapEvents(models.Model):
    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    dc = models.ForeignKey('fulfillment.Dc')
    storage_location = models.PositiveIntegerField(default=10)
    quantity = models.PositiveIntegerField(default=0)
    actual_quantity = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    type = models.CharField(max_length=20,default='inward',choices=(
        ('inward','Inward'),
        ('outward','Outward')))
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(default=False)

    def mark_sap_event_as_processed(self, request):
        self.processed = True
        self.save()
        return

    def __unicode__(self):
        return 'Articleid-%s, DC-%s, type-%s, timestamp=%s' % (self.rate_chart.article_id, self.dc.code, self.type, self.created_on)

class UnprocessedSAPEvents(models.Model):
    article_id = models.CharField(max_length=100, db_index=True)
    receiving_storage_location = models.CharField(max_length=6)
    receiving_site = models.CharField(max_length=6)
    issuing_storage_location = models.CharField(max_length=6)
    issuing_site = models.CharField(max_length=6)
    quantity = models.PositiveIntegerField(default=0)
    actual_quantity = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    seller = models.ForeignKey('accounts.Account', null=True, blank=True)
    client = models.ForeignKey('accounts.Client', null=True, blank=True)
    processed = models.BooleanField(default=False, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Articleid - %s, Quantity - %s' % (self.article_id, self.quantity)

class InventoryLog(models.Model):
    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    dc = models.ForeignKey('fulfillment.Dc')
    inventory = models.ForeignKey(Inventory, blank=True, null=True)
    sto = models.ForeignKey(InventoryStoLog, blank=True, null=True)
    backorder = models.ForeignKey(InventoryBackorder, blank=True, null=True)
    sapevent = models.ForeignKey(SapEvents, blank=True, null=True)
    dclsp = models.ForeignKey(InventoryDcLspResolution, blank=True, null=True, default=None)
    was_stock = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    new_stock = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    was_starts_on = models.DateTimeField(blank=True, null=True)
    new_starts_on = models.DateTimeField(blank=True, null=True)
    was_ends_on = models.DateTimeField(blank=True, null=True)
    new_ends_on = models.DateTimeField(blank=True, null=True)
    was_expected_on = models.DateTimeField(blank=True, null=True)
    new_expected_on = models.DateTimeField(blank=True, null=True)
    was_expected_in = models.PositiveIntegerField(null=True, 
        blank=True, default=None)
    new_expected_in = models.PositiveIntegerField(null=True, 
        blank=True, default=None)
    was_bookings = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    new_bookings = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    was_outward = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    new_outward = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    was_threshold = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    new_threshold = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    was_stock_adjustment = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    new_stock_adjustment = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    was_bookings_adjustment = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    new_bookings_adjustment = models.DecimalField(max_digits=7,
        decimal_places=2, null=True, blank=True, default=0)
    was_is_active = models.NullBooleanField(default=True, null=True, blank=True)
    new_is_active = models.NullBooleanField(default=True, null=True, blank=True)
    was_sto_stock_allocated = models.NullBooleanField(default=True, null=True, blank=True)
    new_sto_stock_allocated = models.NullBooleanField(default=True, null=True, blank=True)
    was_sto_ack_received = models.NullBooleanField(default=True, null=True, blank=True)
    new_sto_ack_received = models.NullBooleanField(default=True, null=True, blank=True)
    was_dclsp_stock_allocated = models.NullBooleanField(default=True, null=True, blank=True)
    new_dclsp_stock_allocated = models.NullBooleanField(default=True, null=True, blank=True)
  
    #If modified by admin, populate user field as well. No need to populate order.
    #If modified by SAP, no need to populate order/user.
    #For other options, populate order. No need to populate user.
    order = models.ForeignKey('orders.Order', blank=True, null=True)
    orderitem = models.ForeignKey('orders.OrderItem', blank=True, null=True)
    lsp = models.ForeignKey('fulfillment.Lsp', blank=True, null=True)
    user = models.ForeignKey(User,blank=True,null=True)
    created_on = models.DateTimeField(blank=True, 
        null = True, auto_now_add = True, db_index = True)
    modified_by = models.CharField(max_length=20,default='website',choices=(
        ('admin','Admin'),
        ('sellershub','Sellers Hub'),
        ('support','Support'),
        ('sap','SAP'),
        ('website','Web User'),
        ('cc','Call Center'),
        ('store','Store'),
        ('mobileweb','Mobile')))

    def set_inventorylog(self, log_fields):
        #Compulsory fields are - rate_chart, dc, modified_by
        try:
            self.rate_chart = log_fields['rate_chart']
            self.dc = log_fields['dc']
            self.inventory = log_fields.get('inventory',None) 
            self.sto = log_fields.get('sto',None) 
            self.dclsp = log_fields.get('dclsp',None)
            self.backorder = log_fields.get('backorder',None)
            self.sapevent = log_fields.get('sap_event',None)
            self.was_stock = log_fields.get('was_stock',None)
            self.new_stock = log_fields.get('new_stock',None)
            self.was_starts_on = log_fields.get('was_starts_on', None)
            self.new_starts_on = log_fields.get('new_starts_on', None)
            self.was_ends_on = log_fields.get('was_ends_on', None)
            self.new_ends_on = log_fields.get('new_ends_on', None)
            self.was_expected_on = log_fields.get('was_expected_on', None)
            self.new_expected_on = log_fields.get('new_expected_on', None)
            self.was_expected_in = log_fields.get('was_expected_in', None)
            self.new_expected_in = log_fields.get('new_expected_in', None)
            self.was_bookings = log_fields.get('was_bookings',None)
            self.new_bookings = log_fields.get('new_bookings',None)
            self.was_outward = log_fields.get('was_outward',None)
            self.new_outward = log_fields.get('new_outward',None)
            self.was_threshold = log_fields.get('was_threshold',None)
            self.new_threshold = log_fields.get('new_threshold',None)
            self.was_stock_adjustment = log_fields.get('was_stock_adjustment',None)
            self.new_stock_adjustment = log_fields.get('new_stock_adjustment',None)
            self.was_bookings_adjustment = log_fields.get('was_bookings_adjustment',None)
            self.new_bookings_adjustment = log_fields.get('new_bookings_adjustment',None)
            self.order = log_fields.get('order', None)
            self.orderitem = log_fields.get('orderitem', None)
            self.lsp = log_fields.get('lsp', None)
            self.user = log_fields.get('user',None)
            self.modified_by = log_fields['modified_by']
            self.was_is_active = log_fields.get('was_is_active', None)
            self.new_is_active = log_fields.get('new_is_active', None)
            self.was_sto_stock_allocated = log_fields.get('was_sto_stock_allocated', None)
            self.new_sto_stock_allocated = log_fields.get('new_sto_stock_allocated', None)
            self.was_sto_ack_received = log_fields.get('was_sto_ack_received', None)
            self.new_sto_ack_received = log_fields.get('new_sto_ack_received', None)
            self.was_dclsp_stock_allocated = log_fields.get('was_dclsp_stock_allocated', None)
            self.new_dclsp_stock_allocated = log_fields.get('new_dclsp_stock_allocated', None)
            self.save()
        except Exception,e:
            log.exception('######### NOT ABLE TO SAVE INVENTORY LOG #########')
            raise

    def __unicode__(self):
        return 'Inventory log for %s' % (self.rate_chart.product.title)


