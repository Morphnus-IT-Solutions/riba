from django.contrib import admin
from catalog.models import ProductTags
from lists.models import *


class ListItemInline(admin.StackedInline):
    model = ListItem
    raw_id_fields = ('sku',)
    extra = 3

class ListAdmin(admin.ModelAdmin):
    list_display = ('title','curator','starts_on','ends_on','is_featured','type')
    list_filter = ('type','is_featured','client')
    raw_id_fields = ('curator',)
    inlines = [ListItemInline]
admin.site.register(List,ListAdmin)

class ListItemAdmin(admin.ModelAdmin):
    list_display = ('list','sku','sequence','user_title','status')
    list_filter = ('status','list__type')
    raw_id_fields = ('sku',)
admin.site.register(ListItem,ListItemAdmin)

class TabAdmin(admin.ModelAdmin):
    list_display = ('name','list','sort_order')
    list_filter = ('list',)
admin.site.register(Tab,TabAdmin)

class BattleTabAdmin(admin.ModelAdmin):
    list_display = ('name','list','sort_order')
    list_filter = ('list',)
admin.site.register(BattleTab,BattleTabAdmin)
