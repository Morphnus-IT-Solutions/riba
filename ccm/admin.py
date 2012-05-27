from django.contrib import admin
from ccm.models import *
from ccm.forms import CallSlotForm

class AgentAdmin(admin.ModelAdmin):
    model = Agent
    raw_id_fields = ('user',)
    list_display = ('name', 'role', 'user')
admin.site.register(Agent, AgentAdmin)

class ExtensionAdmin(admin.ModelAdmin):
    model = Extension
    list_display = ('number', 'allotted_to')
admin.site.register(Extension, ExtensionAdmin)

class AgentLoginLogoutAdmin(admin.ModelAdmin):
    list_display = ('agent', 'time', 'action')
    list_filter = ('action', )
admin.site.register(AgentLoginLogout, AgentLoginLogoutAdmin)

class CallSlotAdmin(admin.ModelAdmin):
    form = CallSlotForm
    #readonly_fields = ('days_of_week',)
admin.site.register(CallSlot, CallSlotAdmin)

