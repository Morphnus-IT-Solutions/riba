from django.contrib import admin
from activitystream.models import *

class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user','aclientdomain', 'atype', 'asrc','atime','astream','astatus')
admin.site.register(Activity,ActivityAdmin)
