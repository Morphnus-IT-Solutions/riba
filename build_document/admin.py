from django.contrib import admin
from build_document.models import *

class TemplateAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = ('title', 'category', 'offer_price', 'time_to_build', 'state',)
admin.site.register(Template, TemplateAdmin)
