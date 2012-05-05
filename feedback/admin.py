from django.contrib import admin
from feedback.models import *
from accounts.models import Account
from django.http import HttpResponse, HttpResponseRedirect, Http404
import pyExcelerator

class CustomerImageInline(admin.TabularInline):
    model = CustomerImage
    extra = 1

class FeedbackAdmin(admin.ModelAdmin):
    inlines = [CustomerImageInline]
    list_display = ('publish_it', 'name','email','phone','feedback','type')
    actions= ['download_report']
    list_filter = ('type', 'publish_it', 'client',)
    def download_report(self,request,queryset):
        wb = pyExcelerator.Workbook()
        ws = wb.add_sheet('user feedback')
        row = 0
        ws.write(row,0,'NAME')
        ws.write(row,1,'EMAIL')
        ws.write(row,2,'PHONE')
        ws.write(row,3,'FEEDBACK')
        ws.write(row,4,'SUBMITTED DATE')
        ws.write(row,5,'TYPE')
        row += 1        
        for qs in queryset:
            ws.write(row,0,unicode(qs.name))
            ws.write(row,1,unicode(qs.email))
            ws.write(row,2, unicode(qs.phone))
            ws.write(row,3,unicode(qs.feedback))
            ws.write(row,4,unicode(qs.submitted_on))
            ws.write(row,5,unicode(qs.type))
            row += 1
        filename = '/tmp/feedbackreport'
        wb.save(filename)
        response = HttpResponse(file(filename).read(),mimetype='text/xls')
        response['Content-Disposition'] = 'attachment; filename=report.xls'
        return response
    download_report.short_description = "Download Report"

admin.site.register(Feedback, FeedbackAdmin)

class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'subject','comments', 'client', 'submitted_on')
admin.site.register(ContactUs, ContactUsAdmin)
