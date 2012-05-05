from locations.models import Country,State,City,Address,AddressBook
from django.contrib import admin

class CountryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name','user_created')
    list_filter = ('type','user_created')

class StateAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ('country','type','user_created')
    list_display = ('name','country','user_created')

class CityAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ('state','type','user_created')
    list_display = ('name','state','user_created')

class AddressAdmin(admin.ModelAdmin):
    search_fields = ['address','city__name']
    raw_id_fields = ('profile',)
    list_filter = ('type','state')
    list_display = ('address','pincode','city','state','country',)

class AddressBookAdmin(admin.ModelAdmin):
    search_fields = ['address','city__name','phone','email']
    raw_id_fields = ('profile',)
    list_display = ('address','pincode','city','state','country',)

admin.site.register(Country,CountryAdmin)
admin.site.register(State,StateAdmin)
admin.site.register(City,CityAdmin)
admin.site.register(Address,AddressAdmin)
admin.site.register(AddressBook,AddressBookAdmin)
