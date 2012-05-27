from django.contrib import admin
from promotions.models import *
from users.models import *
from affiliates.models import *

class AffiliateAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name','logo')
admin.site.register(Affiliate, AffiliateAdmin)

class SubscriptionLinkAdmin(admin.ModelAdmin):
    list_display = ('path','newsletter')
admin.site.register(SubscriptionLink, SubscriptionLinkAdmin) 

class CouponTypeAdmin(admin.ModelAdmin):
    list_display = ('coupon_type','terms_and_conditions','discount_type','is_price_range','min_price','max_price','percentage_off','discount_value','discount_available_on','affiliate','offer')
admin.site.register(CouponType,CouponTypeAdmin)

class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code','type','uses','status','expires_on')
    list_filter = ('type__affiliate',)
    search_fields = ['code']
admin.site.register(Voucher,VoucherAdmin)

