from django.contrib import admin
from django.db.models import *
from orders.models import Order,OrderItem,DeliveryInfo, GiftInfo, ShippingDetails, ShippingTracker
from locations.models import *

def get_field(self, name, many_to_many=True):
    to_search = many_to_many and (self.fields + self.many_to_many) or self.fields
    if hasattr(self, '_copy_fields'):
        to_search += self._copy_fields
    for f in to_search:
        if f.name == name:
            return f
    if not name.startswith('__') and '__' in name:
        f = None 
        model = self 
        path = name.split('__') 
        for field_name in path: 
            f = model._get_field(field_name)
            if isinstance(f, ForeignKey):
                model = f.rel.to._meta
        f = copy.deepcopy(f)
        f.name = name
        if not hasattr(self, "_copy_fields"):
            self._copy_fields = list()
        self._copy_fields.append(f)
        return f
    raise FieldDoesNotExist, '%s has no field named %r' % (self.object_name, name)

setattr(options.Options, '_get_field', options.Options.get_field.im_func)

setattr(options.Options, 'get_field', get_field)

class OrderItemInlne(admin.TabularInline):
    can_delete = False
    raw_id_fields = ('seller_rate_chart',)
    extra = 0
    model = OrderItem

class DeliveryInfoInlne(admin.StackedInline):
    raw_id_fields = ('address',)
    can_delete = False
    model = DeliveryInfo
    max_num = 1
    extra = 0

class GiftInfoInline(admin.StackedInline):
    can_delete = False
    model = GiftInfo
    max_num = 1
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    search_fields = ['id','reference_order_id']
    list_display = ('id','state','booking_date','order_date','phone','name','city','list_price_total','total','coupon_discount','shipping_charges','payable_amount','coupon','notes')
    list_filter = ('state','timestamp','agent','payment_mode','medium')
    totals = ('list_price_total','total','coupon_discount','shipping_charges','payable_amount')
    inlines = [DeliveryInfoInlne, GiftInfoInline, OrderItemInlne]
    date_hierarchy = 'timestamp'

class CancelledOrderItemAdmin(admin.ModelAdmin):
    search_fields = ['order_item__order__id']
    list_display = ('order','item','cancellation_date','refund_status','refundable_amount','notes')
    list_filter = ('refund_status',)
    date_hierarchy = 'cancellation_date'
    def item(self,cancelled_order_item):
        return cancelled_order_item.order_item.item_title
    def order(self,cancelled_order_item):
        return cancelled_order_item.order_item.order

class OrderItemAdmin(admin.ModelAdmin):
    search_fields = ['order__id','item_title']
    list_filter = ('order__state','order__timestamp','seller_rate_chart__product__category__store','order__agent','order__payment_mode','order__medium','seller_rate_chart__seller','seller_rate_chart__product__category')
    list_display = ('order','state','order_date','item_title','gift_title','qty','list_price','sale_price','spl_discount','shipping_charges','payable_amount','agent','payment_mode','medium')
    totals = ('list_price','sale_price','spl_discount','shipping_charges','payable_amount')
    def agent(self,order_item):
        return order_item.order.agent
    def payment_mode(self,order_item):
        return order_item.order.payment_mode
    def medium(self,order_item):
        return order_item.order.medium
    def state(self,order_item):
        return order_item.order.state
class DeliveryInfoAdmin(admin.ModelAdmin):
    list_display = ('order','notes')

class ShippingDetailsAdmin(admin.ModelAdmin):
    list_display = ('order_item','tracking_no','tracking_url','courier','notes')

class ShippingTrackerAdmin(admin.ModelAdmin):
    list_display = ('order','order_date','item_title','gift_title','qty','status','phone','city','shipping_due_on','shipped_on','shipper','AWB','shipper_status','notes','agent')
    list_filter = ('status','order_item__seller_rate_chart__product__category__store','order_item__seller_rate_chart__seller','order_item__order__payment_realized_mode','order_item__order__medium')

    search_fields = ['order_item__order__id','tracking_no']
    def queryset(self,request):
        set = super(ShippingTrackerAdmin,self).queryset(request).filter(order_item__order__state='confirmed')
        return set
    def order_date(self,shipping_details):
        return shipping_details.order_item.order.payment_realized_on.strftime('%d-%m-%y')
    def order(self, shipping_details):
        return shipping_details.order_item.order.id
    def phone(self,shipping_details):
        return shipping_details.order_item.order.user.primary_phone
    def city(self,shipping_details):
        delivery_info = DeliveryInfo.objects.get(order=shipping_details.order_item.order)
        return delivery_info.address.city
    def shipping_due_on(self,shipping_details):
        return shipping_details.order_item.dispatch_due_on
    def shipped_on(self,shipping_details):
        return shipping_details.order_item.dispatched_on.strftime('%d-%m-%y')
    def shipper(self,shipping_details):
        return shipping_details.courier
    def AWB(self,shipping_details):
        return shipping_details.tracking_no
    def agent(self,shipping_details):
        return shipping_details.order_item.order.agent
    def item_title(self,shipping_details):
        return shipping_details.order_item.item_title
    def gift_title(self,shipping_details):
        return shipping_details.order_item.gift_title
    def qty(self,shipping_details):
        return shipping_details.order_item.qty
    
#admin.site.register(DeliveryInfo,DeliveryInfoAdmin)
##admin.site.register(Order,OrderAdmin)
##admin.site.register(OrderItem,OrderItemAdmin)
#admin.site.register(ShippingDetails,ShippingDetailsAdmin)
##admin.site.register(ShippingTracker,ShippingTrackerAdmin)
##admin.site.register(CancelledOrderItem,CancelledOrderItemAdmin)
#admin.site.register(AgentOrder,AgentOrderAdmin)
