from django.contrib import admin
from migration.models import ListingRateChartMap, DuplicateUsers, AddressMap

class ListingRateChartMapAdmin(admin.ModelAdmin):
    list_display = ('listing_id','rate_chart')
    search_fields = ['listing_id','rate_chart']
admin.site.register(ListingRateChartMap, ListingRateChartMapAdmin)

class AddressMapAdmin(admin.ModelAdmin):
    list_display = ('address',)
admin.site.register(AddressMap, AddressMapAdmin)
