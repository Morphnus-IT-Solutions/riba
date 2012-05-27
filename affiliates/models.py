from django.db import models
from storage import upload_storage
from users.models import *
from promotions.models import *
from datetime import datetime
# Create your models here.

class Affiliate(models.Model):
    name = models.CharField(max_length=255,unique=True)
    logo = models.ImageField(upload_to='images/logos/',blank=True, null=True, storage=upload_storage)
    text = models.CharField(max_length =1000, blank=True, null=True)
    is_coupon_avail = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name

class SubscriptionLink(models.Model):
    path = models.CharField(max_length = 200)
    newsletter =models.ForeignKey('users.Newsletter')
    affiliate = models.ForeignKey('affiliates.Affiliate')

    def __unicode__(self):
        return "%s-%s-%s" % (self.path,self.affiliate,self.newsletter)

class CouponType(models.Model):
    coupon_type = models.CharField(max_length = 200)
    terms_and_conditions = models.TextField()
    discount_type = models.CharField(max_length = 100, choices = (
                                        ('fixed_value_off','Fixed value off'),
                                        ('percentage_off','Percentage off'),
                                        ))
    is_price_range = models.BooleanField()
    min_price = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    max_price = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    percentage_off = models.PositiveIntegerField(blank=True,null=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    discount_available_on = models.CharField(max_length = 30,blank=True,null=True, choices = (
                                                                                        ('futurebazaar','Futurebazaar'),
                                                                                        ('bigbazaar','Bigbazaar'),
                                                                                        ('pantaloon','Pantaloons'),
                                                                                        ))
    affiliate = models.ForeignKey('Affiliate',blank=True,null=True)
    offer = models.CharField(max_length = 200, null=True,blank = True)
    shopping_page = models.URLField(blank=True,null=True)
    
    def __unicode__(self):
        return "%s-%s-%s-%s-%s-%s-%s-%s-%s" % (self.coupon_type,self.discount_type,self.is_price_range,self.min_price,self.max_price,self.percentage_off,self.discount_value,self.discount_available_on,self.affiliate)

class Voucher(models.Model):
    code = models.CharField(max_length = 50,unique = True)
    type = models.ForeignKey(CouponType, blank=True, null=True)
    uses = models.PositiveIntegerField(default = 0)
    expires_on = models.DateTimeField(blank=True, null=True, default=datetime.now())
    status = models.CharField(max_length=25, default='inactive', choices=(
        ('inactive','Inactive'),
        ('active', 'Active'),
        ), db_index=True)
    affiliate = models.ForeignKey('Affiliate',blank=True,null=True, db_index=True)
    def __unicode__(self):
        return self.code

class VoucherEmailMapping(models.Model):
    voucher = models.ForeignKey(Voucher)
    email = models.ForeignKey(Email)

class VoucherPhoneMapping(models.Model):
    voucher = models.ForeignKey(Voucher)
    phone = models.ForeignKey(Phone)

class CouponEmailMapping(models.Model):
    coupon = models.ForeignKey(Coupon)
    email = models.ForeignKey(Email)

