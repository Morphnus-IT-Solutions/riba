from django.contrib import admin
from stores.models import WhiteLabelStore

class WhiteLabelStoreAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(WhiteLabelStore, WhiteLabelStoreAdmin)
