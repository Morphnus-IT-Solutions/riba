from django.contrib import admin
from payouts.models import *

class ConfigurationsAdmin(admin.ModelAdmin):
    list_display = ('service_tax',)

class SellerPayoutAdmin(admin.ModelAdmin):
    list_display = ('month','year','seller','shipping_charges','gateway_charges','chaupaati_discount','seller_discount','collected_amount','applicable_amount','commission_amount','gross_payout','commission_invoice_amount','net_payout')

class SellerPayoutDetailsAdmin(admin.ModelAdmin):
    list_display = ('month','year','seller','order_item','sale_price','shipping_charges','gateway_charges','chaupaati_discount','seller_discount','collected_amount','applicable_amount','commission_amount','gross_payout','commission_invoice_amount','net_payout')

class SellerConfigurationsAdmin(admin.ModelAdmin):
    list_display = ('seller','amount_collected_by','percentage_commission')
    
admin.site.register(SellerPayout, SellerPayoutAdmin)
admin.site.register(SellerPayoutDetails, SellerPayoutDetailsAdmin)
admin.site.register(Configurations,ConfigurationsAdmin)
admin.site.register(SellerConfigurations, SellerConfigurationsAdmin)
