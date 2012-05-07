from django.contrib import admin
from question.models import *


class OptionInline(admin.TabularInline):
    model = Option
    fk_name = "question"
    extra = 0

class FieldInline(admin.TabularInline):
    model = Field
    extra = 0

class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['question']
    list_display = ('question', 'type', 'answer_type',)
    list_filter = ('type', 'answer_type',)
    inlines = [FieldInline, OptionInline]
admin.site.register(Question, QuestionAdmin)


