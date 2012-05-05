from django.db import models
from decimal import Decimal
from datetime import date
from django.db.models import Q

class Configurations(models.Model):
    service_tax = models.DecimalField(max_digits=5,decimal_places=2,default=Decimal(0))

class SellerConfigurations(models.Model):
    seller = models.ForeignKey('accounts.Account',verbose_name='Seller')
    amount_collected_by = models.CharField(max_length=10,default='chaupaati',choices=(
        ('chaupaati','Chaupaati'),
        ('seller','Seller')))
    percentage_commission = models.DecimalField(max_digits=5,decimal_places=2,default=Decimal(0))

class SellerPayout(models.Model):
    MONTHS = (
        (1,'January'),
        (2,'February'),
        (3,'March'),
        (4,'April'),
        (5,'May'),
        (6,'June'),
        (7,'July'),
        (8,'August'),
        (9,'September'),
        (10,'October'),
        (11,'November'),
        (12,'December'))
    seller = models.ForeignKey('accounts.Account',verbose_name='Seller')
    year = models.IntegerField(default=date.today().year, choices=(
        (2007,2007),
        (2008,2008),
        (2009,2009),
        (2010,2010),
        (2011,2011),
        (2012,2012),
        (2013,2013)))
    month = models.IntegerField(max_length=2,choices=MONTHS)
    sale_price = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Offer price')
    shipping_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Shipping')
    gateway_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    chaupaati_discount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    seller_discount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    collected_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    applicable_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    commission_amount= models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    gross_payout = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    commission_invoice_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    net_payout = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0)) 

class SellerPayoutDetails(models.Model):
    MONTHS = (
        (1,'January'),
        (2,'February'),
        (3,'March'),
        (4,'April'),
        (5,'May'),
        (6,'June'),
        (7,'July'),
        (8,'August'),
        (9,'September'),
        (10,'October'),
        (11,'November'),
        (12,'December'))
    year = models.IntegerField(default=date.today().year, choices=(
        (2007,2007),
        (2008,2008),
        (2009,2009),
        (2010,2010),
        (2011,2011),
        (2012,2012),
        (2013,2013)))
    month = models.IntegerField(max_length=2,choices=MONTHS)
    seller = models.ForeignKey('accounts.Account',verbose_name='Seller')
    order_item = models.ForeignKey('orders.OrderItem',limit_choices_to=(~Q(state='cancelled') | ~Q(state='refunded') | ~Q(state='pending')))
    sale_price = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Offer price')
    shipping_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Shipping')
    gateway_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    chaupaati_discount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    seller_discount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    collected_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    applicable_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    commission_amount= models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    gross_payout = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    commission_invoice_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    net_payout = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0)) 
