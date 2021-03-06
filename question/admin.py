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
    list_display = ('question', 'category', 'answer_type',)
    list_filter = ('category', 'answer_type',)
    inlines = [FieldInline, OptionInline]
admin.site.register(Question, QuestionAdmin)

class QuestionTreeAdmin(admin.ModelAdmin):
    search_fields = ['question']
    list_display = ('parent_question', 'parent_value','question', 'lft', 'rgt', 'level')
admin.site.register(QuestionTree, QuestionTreeAdmin)
