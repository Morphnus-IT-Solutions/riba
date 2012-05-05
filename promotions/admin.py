from django.contrib import admin
from promotions.models import *

class FeatureProductsAdmin(admin.ModelAdmin):
    raw_id_fields = ('product',)
    list_display = ('section', 'type','product','store','category')
    search_fields = ['product__title']
    list_filter = ('type','store','category')
admin.site.register(FeaturedProducts, FeatureProductsAdmin)

class FeaturedCategoriesAdmin(admin.ModelAdmin):
    raw_id_fields = ('category',)
    list_display = ('category','type','sort_order')
    search_fields = ['category__name']
    list_filter = ('type',)
admin.site.register(FeaturedCategories, FeaturedCategoriesAdmin)

class CouponAdmin(admin.ModelAdmin):
    exclude = ('applicable_on',)
    list_display = ('code','status','given_by','applies_to','discount_type','discount_value','discount_available_on','newsletter')
    list_filter = ('given_by',)
    search_fields = ['code']
admin.site.register(Coupon, CouponAdmin)

class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'type', 'starts_on', 'ends_on')
    list_filter = ('type', 'status')
    search_fields = ['name']
admin.site.register(Offer, OfferAdmin)

class OfferProductAdmin(admin.ModelAdmin):
    raw_id_fields = ('product',)
    list_display = ('offer','product')
    list_filter = ('offer',)
admin.site.register(OfferProduct, OfferProductAdmin)

class BundleOfferAdmin(admin.ModelAdmin):
    raw_id_fields = ('bundle_product',)
    list_display = ('offer', 'status', 'bundle_product', 'percentage_off')
    list_filter = ('offer','status')
admin.site.register(BundleOffer, BundleOfferAdmin)

class BundleAdmin(admin.ModelAdmin):
    filter_horizontal = ('primary_products',)
    list_display = ('offer','status')
    list_filter = ('offer','status')
admin.site.register(Bundle,BundleAdmin)

class DiscountedProductsAdmin(admin.ModelAdmin):
    raw_id_fields = ('product',)
    list_display = ('bundle','product','percentage_off')
admin.site.register(DiscountedProducts,DiscountedProductsAdmin)

class ScratchCardAdmin(admin.ModelAdmin):
    list_display = ('name','email','mobile','scratch_card_no','status', 'store')
admin.site.register(ScratchCard,ScratchCardAdmin)
