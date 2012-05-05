from django.db import models
from users.models import *
from datetime import datetime

# Create your models here.
class Coupon(models.Model):
    class Meta:
        unique_together = ('code', 'status')
    code = models.CharField(max_length=50)
    promo_name = models.CharField(max_length=100,blank=True)
    max_uses = models.PositiveIntegerField(default=0)
    uses = models.PositiveIntegerField(default=0)
    expires_on = models.DateTimeField(blank=True, null=True)

    status = models.CharField(max_length=25, default='inactive', choices=(
        ('inactive','Inactive'),
        ('active', 'Active'),
        ('expired', 'Expired')))

    use_when = models.CharField(max_length=25, default='manual', choices=(
        ('manual','Manual'),
        ('auto','Auto')))

    given_by = models.ForeignKey('accounts.Account', blank=True, null=True)

    applies_to = models.CharField(max_length=25, choices=(
        ('order_total','Discount order total by'),
        ('order_list_price','Discount order list price by'),
        ('order_shipping_charge','Discount order shipping charge by'),
        ('product_list_price','Discount product list price by'),
        ('product_offer_price','Discount product offer price by'),
        ('product_shipping_charge','Discount product shipping charge by'),
        ('payment_mode_charge','Discount payment mode charge by')))

    applicable_on = models.ManyToManyField('catalog.SellerRateChart',blank=True,null=True)

    discount_type = models.CharField(max_length=15, choices=(
        ('percentage', 'Percentage off'),
        ('fixed', 'Fixed Value off')))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    discount_available_on = models.CharField(max_length = 30,blank = True, null =True)
    newsletter = models.ForeignKey(NewsLetter, blank=True, null = True)
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return self.code
    
    #for template - prady
    def get_discount_on(self):
        if self.applies_to == 'order_total':
            return 'Sale Price'
        elif self.applies_to == 'order_list_price':
            return 'MRP'
        elif self.applies_to == 'order_shipping_charge':
            return 'Shipping Charge'
        elif self.applies_to == 'product_list_price':
            return 'Product MRP'
        elif self.applies_to == 'product_offer_price':
            return 'Product Sale Price'
        elif self.applies_to == 'product_shipping_charge':
            return 'Product Shipping Charge'
        elif self.applies_to == 'payment_mode_charge':
            return 'Payment Mode Charge'
        return ''

class CouponConstraint(models.Model):
    coupon = models.ForeignKey(Coupon)
    type = models.CharField(max_length=50, choices=(
        ('category_products','All products of category'),
        ('account_products', 'All products of account'),
        ('selected_products','Manually selected products'),
        ('order_total_min','For orders above'),
        ('product_qty_min','If orders more than')))

    logical_operator = models.CharField(max_length='3', default='and', choices=(
        ('and','AND'),
        ('or','OR')))

    category = models.ForeignKey('categories.Category', blank=True, null=True,related_name='category_coupons')
    account = models.ForeignKey('accounts.Account', blank=True, null=True,related_name='account_coupons')
    products = models.ManyToManyField('catalog.Product', blank=True, null=True)

    order_min_total = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    product_qty_min = models.PositiveIntegerField(blank=True, null=True)


class FeaturedProducts(models.Model):
    class Meta:
        verbose_name_plural = 'Featured products'
    type = models.CharField(max_length=25, default='store', choices=(
        ('mega_drop_down','Mega Drop Down'),
        ('store_page','Store Page'),
        ('category_page','Category Page'),
        ('home_page','Home Page')),
        db_index=True, verbose_name='Page')
    section = models.CharField(max_length=500, blank=True)
    product = models.ForeignKey('catalog.Product', null=True)
    store = models.ForeignKey('categories.Store', null=True, blank=True)
    category = models.ForeignKey('categories.Category', null=True, blank=True)

class FeaturedCategories(models.Model):
    class Meta:
        verbose_name_plural = 'Featured categories'
    category = models.ForeignKey('categories.Category')
    type = models.CharField(max_length=25, default='store', choices=(
        ('store_page','Store Page'),
        ('category_page','Category Page'),
        ('home_page','Home Page'),
        ('footer', 'Footer')),
        db_index=True, verbose_name='Page')
    sort_order = models.PositiveIntegerField(default=1)

class Offer(models.Model):
    name = models.CharField(max_length=200)
    client = models.ForeignKey('accounts.Client')
    description = models.TextField(blank=True)
    price_label = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=25, default='draft', choices=(
        ('draft','Draft'),
        ('published','Published')))
    type = models.CharField(max_length=25, choices=(
        ('combo','Combo Offer'),
        ('bundle','Bundle Offer'),
        ('fixed_discount','Fixed Discount'),
        ('percentage_discount','Percentage Discount'),
        ('gift_voucher','Gift Voucher')))
    starts_on = models.DateTimeField(null=True)
    ends_on = models.DateTimeField(null=True)

    stackable = models.CharField(max_length=25, default='no', choices=(
        ('yes','Yes'),
        ('no','No')))

    def __unicode__(self):
        return self.name


class OfferProduct(models.Model):
    offer = models.ForeignKey(Offer)
    product = models.ForeignKey('catalog.SellerRateChart', limit_choices_to={'stock_status':'instock'})

    sticker_price = models.DecimalField(max_digits=12, decimal_places=2,blank=True,null=True)
    transfer_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True,null=True)
    
    def __unicode__(self):
        return "%s : %s" % (self.product.product, self.offer)

class BundleOffer(models.Model):
    offer = models.ForeignKey(Offer)
    status = models.CharField(max_length=25, default='active', choices=(
        ('active', 'Active'),
        ('inactive', 'InActive')))
    bundle_product = models.ForeignKey('catalog.SellerRateChart', limit_choices_to={'stock_status':'instock'})
    percentage_off = models.DecimalField(max_digits=5,decimal_places=2)

class Bundle(models.Model):
    offer = models.ForeignKey(Offer)
    status = models.CharField(max_length=25, default='active', choices=(
        ('active','Active'),
        ('inactive','InActive')))
    primary_products = models.ManyToManyField('catalog.SellerRateChart', limit_choices_to={'stock_status':'instock','product__status':'active','seller__id':2})

    def __unicode__(self):
        return self.offer.name

class DiscountedProducts(models.Model):
    bundle = models.ForeignKey(Bundle)
    product = models.ForeignKey('catalog.SellerRateChart',limit_choices_to={'stock_status':'instock','product__status':'active','seller__id':2})
    percentage_off = models.DecimalField(max_digits=5, decimal_places=2)

class ScratchCard(models.Model):
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    scratch_card_no = models.CharField(max_length=100, db_index=True)
    coupon_code = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=25, default='active', choices=(
        ('active','Active'),
        ('inactive','InActive')), db_index=True)
    store = models.CharField(max_length=50, default='future_group', choices=(
        ('future_group','Future Group'),
        ('scratch_and_win', 'Scratch and Win'),
        ('ccd','CCD'),
        ('big_bazaar','Big Bazaar')), db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, default=datetime.now(), db_index=True)

    def __unicode__(self):
        return "%s - %s" % (self.scratch_card_no, self.status)

class ScratchCardCoupons(models.Model):
    coupon_code = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    store = models.CharField(max_length=50, default='future_group', choices=(
        ('future_group','Future Group'),
        ('scratch_and_win', 'Scratch and Win'),
        ('ccd','CCD'), 
        ('big_bazaar', 'Big Bazaar')), db_index=True)

class Promotion(models.Model):
    '''
    Promotion table maintained from Colada
    '''
    id = models.IntegerField(primary_key=True, editable=False, db_column='promotion_id')
    order_amount = models.FloatField(null=True, blank=True, editable=False)
    applied_on = models.CharField(max_length=135, blank=True, editable=False)
    discount_type = models.CharField(max_length=150, blank=True, editable=False)
    discount_value = models.CharField(max_length=135, blank=True, editable=False)
    min_order_value = models.FloatField(null=True, blank=True, editable=False)
    max_uses = models.IntegerField(null=True, blank=True, editable=False)
    max_uses_per_user = models.IntegerField(null=True, blank=True, editable=False)
    total_uses = models.IntegerField(null=True, blank=True)
    can_be_claimed_by = models.CharField(max_length=600, blank=True, editable=False)
    name_of_promotion = models.CharField(max_length=150, blank=True, editable=False)
    start_date = models.DateField(null=True, blank=True, editable=False)
    end_date = models.DateField(null=True, blank=True, editable=False)
    created_on = models.DateField(null=True, blank=True, editable=False)
    last_modified_on = models.DateField(null=True, blank=True, editable=False)
    created_by = models.CharField(max_length=300, blank=True, editable=False)
    celin = models.FloatField(null=True, blank=True, editable=False)
    promotion_type = models.CharField(max_length=135, blank=True, editable=False)
    bundle_id = models.IntegerField(null=True, blank=True, editable=False)
    discount_bundle_id = models.CharField(max_length=135, blank=True, editable=False)
    active = models.BooleanField(blank=True, editable=False)
    global_field = models.BooleanField(db_column='global', editable=False, blank=True) # Field renamed because it was a Python reserved word.

    class Meta:
        managed = False
        db_table = 'promotion'

    def __unicode__(self):
        return  "%s - from %s to %s" % (self.name_of_promotion, self.start_date, self.end_date)

class PromoCoupon(models.Model):
    '''
    Promotion Coupon relationship table maintained from Colada
    '''
    promotion = models.ForeignKey('Promotion', db_column='promotion_id', editable=False)
    coupon_code = models.CharField(max_length=135, editable=False, db_column='coupon_code')
    last_modified_on = models.DateTimeField(null=True, blank=True, editable=False, db_column='last_modified_on')
    client = models.ForeignKey('accounts.Client', null=True, blank=True, editable=False, db_column='client_id')
    id = models.CharField(primary_key=True, db_column='coupon_code', max_length=100)

    class Meta:
        managed = False
        db_table = 'promo_coupon'

    def __unicode__(self):
        return "%s of %s" % (self.coupon_code, self.promotion)

class CouponProfile(models.Model):
    coupon_code = models.ForeignKey('PromoCoupon', db_column='coupon_code')
    profile = models.ForeignKey('users.Profile', primary_key=True)
    class Meta:
        managed = False
        db_table = u'coupon_profile'

