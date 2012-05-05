from accounts.models import Account,NotificationSettings, PaymentMode, PaymentOption,StoreOwner, Client, ClientDomain, DomainPaymentOptions
from django.contrib import admin

class NotificationSettingsAdmin(admin.ModelAdmin):
    pass
admin.site.register(NotificationSettings,NotificationSettingsAdmin)

class PaymentModeAdmin(admin.ModelAdmin):
    list_display = ('name','code','group','validate_billing_info')
    #list_filter = ('group',)
admin.site.register(PaymentMode,PaymentModeAdmin)

class NotificationSettingsInline(admin.TabularInline):
    model = NotificationSettings
    max_num = 3

class PaymentOptionInline(admin.TabularInline):
    model = PaymentOption
class StoreOwnerInline(admin.TabularInline):
    model = StoreOwner

class PaymentOptionAdmin(admin.ModelAdmin):
    list_display = ('payment_mode', 'is_active','sort_order','is_noninstant','is_instant','is_online','is_offline')
    list_filter = (['client'])
admin.site.register(PaymentOption, PaymentOptionAdmin)
class AccountAdmin(admin.ModelAdmin):
    inlines = [NotificationSettingsInline,StoreOwnerInline]
    list_display = ('name','type','primary_email')
    list_filter = ('type','dni')
    search_fields = ['name']
    ordering = ('name',)
admin.site.register(Account, AccountAdmin)

class StoreOwnerAdmin(admin.ModelAdmin):
    list_display = ('account','category','store')
    list_filter = ('account','category','store')
admin.site.register(StoreOwner, StoreOwnerAdmin)

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(Client, ClientAdmin)

class ClientDomainAdmin(admin.ModelAdmin):
    list_display = ('domain','client')
    list_filter = ('client',)
admin.site.register(ClientDomain, ClientDomainAdmin)

class DomainPaymentOptionsAdmin(admin.ModelAdmin):
    list_display = ('payment_option','client_domain','is_active','is_dynamic_pm_active')
    list_filter = ('client_domain',)
admin.site.register(DomainPaymentOptions, DomainPaymentOptionsAdmin)
