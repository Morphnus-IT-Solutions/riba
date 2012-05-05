from django.contrib import admin
from users.models import *
import pyExcelerator
from django.http import HttpResponse, HttpResponseRedirect, Http404

class UserProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('full_name','primary_phone','primary_email')
    search_fields = ['primary_phone','primary_email','secondary_phone','secondary_email','full_name']
    list_filter = ('marketing_alerts','acquired_through_account','customer_of_accounts','is_agent')
    date_hierarchy = 'created_on'
    filter_horizontal = ('customer_of_accounts','managed_accounts')

admin.site.register(Profile, UserProfileAdmin)

class UserTagAdmin(admin.ModelAdmin):
    list_display = ('tag','type')
    list_filter = ('type',)

admin.site.register(UserTag, UserTagAdmin)

class NewsLetterAdmin(admin.ModelAdmin):
    list_display = ('newsletter',)
admin.site.register(NewsLetter,NewsLetterAdmin)

class DailySubscriptionAdmin(admin.ModelAdmin):
    #raw_id_fields = ('email_alert_on','sms_alert_on')
    list_display = ('newsletter','email_alert_on', 'is_email_alert', 'sms_alert_on', 'is_sms_alert', 'timestamp', 'last_modified_date')
    list_filter = ('source','last_modified_date')
    date_hierarchy = 'last_modified_date'
    actions= ['download_report']
    search_fields = ['newsletter']

    def download_report(self,request,queryset):
        wb = pyExcelerator.Workbook()
        ws_1 = wb.add_sheet('subscribed')
        ws_2 = wb.add_sheet('email_unsubscribed')
        ws_3 = wb.add_sheet('mobile_unsubscribed')
        row = 0
        ws_1.write(row,0,'EMAIL')
        ws_1.write(row,1,'PHONE')
        ws_1.write(row,2,'SOURCE')
        ws_1.write(row,3,'EMAIL ALERT')
        ws_1.write(row,4,'SMS ALERT')
        ws_2.write(row,0,'EMAIL')
        ws_2.write(row,1,'SOURCE')
        ws_2.write(row,2,'EMAIL ALERT')
        ws_3.write(row,0,'MOBILE')
        ws_3.write(row,1,'SOURCE')
        ws_3.write(row,2,'SMS ALERT')
        row += 1       
        row1, row2, row3 = 1, 1, 1
        for qs in queryset:
            is_subscribed_any = False
            try:
                if qs.email_alert_on.email:
                    if qs.is_email_alert:
                        ws_1.write(row1,0,unicode(qs.email_alert_on.email))
                        ws_1.write(row1,3,unicode(qs.is_email_alert))
                        is_subscribed_any = True
                    else:
                        ws_2.write(row2,0,unicode(qs.email_alert_on.email))
                        ws_2.write(row2,1,unicode(qs.source))
                        ws_2.write(row2,2,unicode(qs.is_email_alert))
                        row2 += 1
            except:
                pass
            try:
                if qs.sms_alert_on.phone:
                    if qs.is_sms_alert:
                        ws_1.write(row1,1, unicode(qs.sms_alert_on.phone))
                        ws_1.write(row1,4,unicode(qs.is_sms_alert))
                        is_subscribed_any = True
                    else:
                        ws_3.write(row3,0,unicode(qs.sms_alert_on.phone))
                        ws_3.write(row3,1,unicode(qs.source))
                        ws_3.write(row3,2,unicode(qs.is_sms_alert))
                        row3 += 1
            except:
                pass
            if is_subscribed_any:
                ws_1.write(row1,2,unicode(qs.source))
                row1 += 1
        filename = '/tmp/emailreport'
        wb.save(filename)
        response = HttpResponse(file(filename).read(),mimetype='text/xls')
        response['Content-Disposition'] = 'attachment; filename=report.xls'
        return response
    download_report.short_description = "Download Report"

admin.site.register(DailySubscription,DailySubscriptionAdmin)

class ShoppingPageAdmin(admin.ModelAdmin):
    list_display = ('redirect_page','newsletter','image')
admin.site.register(ShoppingPage, ShoppingPageAdmin)

class EmailAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('user','email','type')
    list_display_links = ('email',)
    search_fields = ['email']
    list_filter = ('type',)
admin.site.register(Email,EmailAdmin)

class PhoneAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('user','phone','type')
    list_display_links = ('phone',)
    search_fields = ['phone']
    list_filter = ('type',)
admin.site.register(Phone,PhoneAdmin)

class PpdAdminUserAdmin(admin.ModelAdmin):
    raw_id_fields = ('profile',)
    list_display = ('profile',)
    list_filter = ('accounts',)
    filter_horizontal = ('accounts',)
admin.site.register(PpdAdminUser, PpdAdminUserAdmin)

class TabAdmin(admin.ModelAdmin):
    model = Tab
admin.site.register(Tab, TabAdmin)

class UserTabAdmin(admin.ModelAdmin):
    model = UserTab
    raw_id_fields = ('user',)
admin.site.register(UserTab, UserTabAdmin)

