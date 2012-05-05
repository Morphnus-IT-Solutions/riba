from django.contrib import admin
from reviews.models import Review

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'rating','product', 'rate_chart', 'user', 'status')
    list_filter = ('rating', 'status')
admin.site.register(Review, ReviewAdmin)

