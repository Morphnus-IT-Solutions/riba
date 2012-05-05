from django.contrib import admin
from web.models import MenuItem, Announcements, Banner, Coordinates

class MenuItemAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'type', 'filters', 'parent','category', 'store','url', 'sort_order')
    list_filter = ('type', 'parent','store','category')

admin.site.register(MenuItem, MenuItemAdmin)

class AnnouncementsAdmin(admin.ModelAdmin):
    list_display = ('title','text', 'landing_page_url', 'starts_on', 'ends_on')
    list_filter = ('domain', 'starts_on', 'ends_on')
admin.site.register(Announcements, AnnouncementsAdmin)


class BannerAdmin(admin.ModelAdmin):
    list_display = ('name','client', 'sort_order')
    list_filter = ('sort_order',)
admin.site.register(Banner, BannerAdmin)

class CoordinatesAdmin(admin.ModelAdmin):
	list_display=('list', 'co_ordinates', 'link')
admin.site.register(Coordinates, CoordinatesAdmin)
