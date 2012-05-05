from django.contrib import admin
from communications.models import *

class EmailAdmin(admin.ModelAdmin):
    list_display = ('client_domain', 'profile', 'sent_to', 'sent_from', 'subject', 'status', 'type')
    list_filter = ('client_domain', 'status', 'type')
admin.site.register(Email, EmailAdmin)
