from django.contrib import admin
from document.models import *

class QuestionnaireInline(admin.TabularInline):
    model = Questionnaire
    extra = 0

class TemplateAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = ('title', 'category', 'offer_price', 'time_to_build', 'state',)
    list_filter = ('category', 'state',)
    inlines = [QuestionnaireInline]
admin.site.register(Template, TemplateAdmin)
