from pricing.models import *
from catalog.models import SellerRateChart
from django.contrib import admin
from django.db.models import *
from django import forms

class PriceListAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name','list_price_label','offer_price_label')
admin.site.register(PriceList, PriceListAdmin)

class PriceAdmin(admin.ModelAdmin):
    search_fields = ['rate_chart__product__title','rate_chart__sku']
    list_display = ('rate_chart','price_list','price_type','list_price','offer_price','start_time','end_time','modified_on')
    fieldsets = [('Price',{'fields':['list_price','offer_price','cashback_amount']}),
                 ('Price Type',{'fields':['price_type','start_time','end_time']}),
                 ('Price List Details',{'fields':['price_list']}),
                 ('Seller Rate Chart Details',{'fields':['rate_chart']})
                ]
    raw_id_fields = ('rate_chart','price_list')
    list_filter = ('price_type','price_list')
admin.site.register(Price, PriceAdmin)

class ClientLevelPriceListAdmin(admin.ModelAdmin):
    search_fields = ['price__rate_chart__product__title','price__rate_chart__sku']
    list_display = ('client','price_list','priority')
admin.site.register(ClientLevelPriceList, ClientLevelPriceListAdmin)

class DomainLevelPriceListAdmin(admin.ModelAdmin):
    search_fields = ['price__rate_chart__product__title','price__rate_chart__sku']
    list_display = ('domain','price_list','priority')
admin.site.register(DomainLevelPriceList, DomainLevelPriceListAdmin)

class PriceVersionAdmin(admin.ModelAdmin):
    search_fields = ['rate_chart__product__title','rate_chart__sku','pricing_job']
    list_display = ('rate_chart','price_list','price_type','current_list_price','new_list_price','current_offer_price','new_offer_price','current_start_time','new_start_time','current_end_time','new_end_time','action','status','created_by','created_on','approved_by','approved_on')
    fieldsets = [('Price',{'fields':['current_list_price','new_list_price','current_offer_price','new_offer_price','current_cashback_amount','new_cashback_amount']}),
                 ('Price Type',{'fields':['price_type','current_start_time','new_start_time','current_end_time','new_end_time']}),
                 ('Price List Details',{'fields':['price_list']}),
                 ('Seller Rate Chart Details',{'fields':['rate_chart']}),
                 ('Creation History',{'fields':['created_by','created_on']}),
                 ('Approval History',{'fields':['approved_by','approved_on']}),
                ]
    raw_id_fields = ('rate_chart','price_list')
    list_filter = ('price_type','price_list')
admin.site.register(PriceVersion, PriceVersionAdmin)


