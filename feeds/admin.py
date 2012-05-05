from django.contrib import admin
from feeds.models import *

class BrandMappingAdmin(admin.ModelAdmin):
    list_display = ('brand','account','mapped_to')
    list_filter = ('account','mapped_to')
    ordering = ('brand',)
    search_fields = ['brand']
admin.site.register(BrandMapping, BrandMappingAdmin)

class FeatureMappingAdmin(admin.ModelAdmin):
    list_display  = ('feature','sku_type', 'feature_name','action', )
    list_filter = ('sku_type',)
admin.site.register(FeatureMapping, FeatureMappingAdmin)

class CategoryMappingAdmin(admin.ModelAdmin):
    list_display = ('category','account','mapped_to')
    list_filter = ('account','mapped_to')
    ordering = ('category',)
    search_fields = ['category']
admin.site.register(CategoryMapping, CategoryMappingAdmin)

class BrandBlackListAdmin(admin.ModelAdmin):
    list_display = ('brand','account')
    list_filter = ('account',)
    ordering = ('brand',)
    search_fields = ['brand']
admin.site.register(BrandBlackList, BrandBlackListAdmin)

class CategoryBlackListAdmin(admin.ModelAdmin):
    list_display = ('category','account')
    list_filter = ('account',)
    ordering = ('category',)
    search_fields = ['category']
admin.site.register(CategoryBlackList, CategoryBlackListAdmin)

class SKUBlackListAdmin(admin.ModelAdmin):
    list_display = ('sku','account')
    list_filter = ('account',)
    search_fields = ['sku']
admin.site.register(SKUBlackList, SKUBlackListAdmin)

class SKUInfoAdmin(admin.ModelAdmin):
    list_display = ('sku','brand','category','model','account')
    list_filter = ('account',)
    search_fields = ('sku','brand','category','model')
admin.site.register(SKUInfo, SKUInfoAdmin)

class SyncEventAdmin(admin.ModelAdmin):
    list_display = ('account','started_at','ended_at','status','found','new_masters','adds','edits','deletes')
    list_filter = ('account','started_at','status')
    date_hierarchy = 'started_at'
admin.site.register(SyncEvent, SyncEventAdmin)

class SyncEventProductMappingAdmin(admin.ModelAdmin):
    raw_id_fields = ('product',)
    list_display = ('sync_event','sku','item_title','product','action')
    list_filter = ('action','sync_event')
admin.site.register(SyncEventProductMapping, SyncEventProductMappingAdmin)

class SyncEventRateChartMappingAdmin(admin.ModelAdmin):
    raw_id_fields = ('rate_chart',)
    list_display = ('sync_event','sku','item_title','rate_chart','action')
    list_filter = ('action','sync_event')
admin.site.register(SyncEventRateChartMapping, SyncEventRateChartMappingAdmin)

class AvailabilityMapAdmin(admin.ModelAdmin):
    list_display = ('applies_to','account','brand','category','sku','availability')
    list_filter = ('account','applies_to')
admin.site.register(AvailabilityMap, AvailabilityMapAdmin)

class SkuTypeProductTypeMappingAdmin(admin.ModelAdmin):
    list_display = ('account','sku_type','product_type')
    list_filter = ('account',)
admin.site.register(SkuTypeProductTypeMapping, SkuTypeProductTypeMappingAdmin)

class ExtPricelistAdmin(admin.ModelAdmin):
    search_fields = ['rate_chart__product__title']
    list_display = ['rate_chart','priceList']
    fieldsets = [('Price',{'fields':['list_price','offer_price']}),
                 ('Price List Details',{'fields':['priceList']}),
                 ('Seller Rate Chart Details',{'fields':['rate_chart']}),
                 ('Account',{'fields':['account']})
                ]
    raw_id_fields = ('rate_chart','priceList')
admin.site.register(ExtPricelist, ExtPricelistAdmin)
