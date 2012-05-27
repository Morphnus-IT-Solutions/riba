from django.contrib import admin
from rms.models import (Campaign, Funnel, FunnelState, FunnelSubState,
        Response, Interaction)

class ResponseAdmin(admin.ModelAdmin):
    raw_id_fields = ('phone','assigned_to')
    list_display = ('phone', 'assigned_to',
            'funnel_sub_state', 'created_on', 'closed_on')
    list_filter = ('created_on', 'closed_on',)
    class Meta:
        model = Response

class FunnelStateAdmin(admin.ModelAdmin):
    list_display = ('funnel', '__unicode__', )
    list_display_links = ('__unicode__',)
    class Meta:
        model = FunnelState

class FunnelSubStateAdmin(admin.ModelAdmin):
    list_display = ('funnel_state', '__unicode__',  'exit_substate', 'is_active')
    list_display_links = ('__unicode__',)
    class Meta:
        model = FunnelSubState

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'dni_number', 'starts_on', 'ends_on', 'client', 'funnel', 'draft')
    list_filter = ('client', 'draft')
    class Meta:
        model = Campaign

class InteractionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'timestamp', 'pre_funnel_state', 'pre_funnel_sub_state', 'post_funnel_state', 'post_funnel_sub_state', 'followup_on')
    class Meta:
        model = Interaction

admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Funnel)
admin.site.register(FunnelState, FunnelStateAdmin)
admin.site.register(FunnelSubState, FunnelSubStateAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(Interaction, InteractionAdmin)
