from django.contrib import admin
import logging
from django.db.models import *
log = logging.getLogger('request')
from franchise.models import *


class NetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'clients', 'share', 'parent_network')
    raw_id_fields = ('user',)
admin.site.register(Network, NetworkAdmin)


class FranchiseAdmin(admin.ModelAdmin):
    list_display = ('user','role','network', 'dealer_id', 'dealer_code')
    raw_id_fields = ('user',)
admin.site.register(Franchise, FranchiseAdmin)


class MerchantTypeKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'network', 'percentage')
admin.site.register(MerchantTypeKey, MerchantTypeKeyAdmin)


class CommisionOnAdmin(admin.ModelAdmin):
    list_display = ('network', 'seller_rate_chart' , 'commision')
    raw_id_fields = ('seller_rate_chart',)
admin.site.register(CommisionOn, CommisionOnAdmin)


class FranchiseOrderAdmin(admin.ModelAdmin):
    list_display = ('franchise', 'order', 'booking_timestamp', 'confirming_timestamp','franc_commission_amnt', 'network_commission_amnt' )
    raw_id_fields = ('order',)
admin.site.register(FranchiseOrder, FranchiseOrderAdmin)


class FranchiseCommissionOnItemAdmin(admin.ModelAdmin):
    list_display = ('franchise_order', 'order_item', 'franc_commission_amnt', 'network_commission_amnt')
    raw_id_fields = ('order_item',)
admin.site.register(FranchiseCommissionOnItem, FranchiseCommissionOnItemAdmin)

'''
class CommisionPrioritiesAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority')
admin.site.register(CommisionPriorities, CommisionPrioritiesAdmin)

class FranchiseCommisionAdmin(admin.ModelAdmin):
    list_display = ('franchise', 'commissionAmnt', 'franchiseOrder' )
admin.site.register(FranchiseCommision, FranchiseCommisionAdmin)

class NetworkCommisionAdmin(admin.ModelAdmin):
    list_display = ('network', 'commissionAmnt', 'franchiseOrder' )
admin.site.register(NetworkCommision, NetworkCommisionAdmin)

#class FranchiseShareAdmin(admin.ModelAdmin):
#    list_display = ('franchise', 'order', 'amount', 'order_time')
#admin.site.register(FranchiseShare, FranchiseShareAdmin)

'''



