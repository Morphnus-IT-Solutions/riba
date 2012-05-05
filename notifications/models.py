from django.db import models

class Notification(models.Model):
    type = models.CharField(max_length=15,choices=(
        ('pending_order','Pending Order'),
        ('confirmed_order','Confirmed Order'),
        ('product_sharing','Product Sharing'),
        ('shipping_status','Shipping Status')))
    order = models.ForeignKey('orders.Order',blank=True,null=True)
    product = models.ForeignKey('catalog.Product',blank=True,null=True)
    to = models.ForeignKey('accounts.Account',blank=True,null=True)
