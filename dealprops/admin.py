from django.contrib import admin
from dealprops.models import *

class DealProductInline(admin.StackedInline):
    model = DailyDealProduct   
    raw_id_fields = ('product',)
    extra = 5

class DealImageInline(admin.TabularInline):
    model = DailyDealImage
    extra = 2

class DailyDealAdmin(admin.ModelAdmin):
    inlines = [DealProductInline, DealImageInline]
    list_display = ('title', 'type', 'client','starts_on','ends_on')
    list_filter = ('starts_on','ends_on',  'type', 'client',)
    raw_id_fields = ('rate_chart',)
    exclude = ('rate_chart', 'tag_line', 'tag_line_color_code', 'note_bg_color_code', 'n_orders', 'description', \
                'product_color_code', 'market_price_color_code', 'todays_steal_color_code', 'weekday_image',\
                'in_box_accessories', 'manufactures_warranty', 'slug')

admin.site.register(DailyDeal, DailyDealAdmin)

class MidDayProductsInline(admin.StackedInline):
    model = MidDayProducts
    raw_id_fields = ('sku',)

class MidDayDealAdmin(admin.ModelAdmin):
    inlines = [MidDayProductsInline]
    list_display = ('status','starts_on','ends_on')
    list_filter = ('starts_on','ends_on')
admin.site.register(MidDayDeal, MidDayDealAdmin)

class FridayDealProductsInline(admin.StackedInline):
    model = FridayDealProducts
    raw_id_fields = ('product',)

class FridayDealAdmin(admin.ModelAdmin):
    inlines = [FridayDealProductsInline]
    list_display = ('status','starts_on','ends_on')
    list_filter = ('starts_on','ends_on')
admin.site.register(FridayDeal, FridayDealAdmin)
