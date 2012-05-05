from django.contrib import admin
from payments.models import PaymentAttempt

class PaymentAttemptAdmin(admin.ModelAdmin):
    raw_id_fields = ('order',)
    list_display = ('order','order_amount','created_on','transaction_id','gateway','response_detail','status','payment_mode')
    list_filter = ('status','gateway')
    search_fields = ['order__id','transaction_id','response_detail']
    def order_amount(self,payment_attempt):
        return payment_attempt.order.payable_amount
    def payment_mode(self,payment_attempt):
        return payment_attempt.order.payment_realized_mode
admin.site.register(PaymentAttempt, PaymentAttemptAdmin)
