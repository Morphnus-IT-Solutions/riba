from django.contrib import admin
from help.models import Help

class HelpAdmin(admin.ModelAdmin):
    list_display = ('heading','help')
    search_fields = ['heading']
admin.site.register(Help, HelpAdmin)
