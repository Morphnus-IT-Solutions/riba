from django.db import models
from decimal import Decimal
from django.core.exceptions import ValidationError

class PriceList(models.Model):
    ''' Defines the meta data for a price list like name etc.
    '''
    name = models.CharField(max_length=100, unique=True)
    offer_price_label = models.CharField(max_length=100, default='Offer Price')
    list_price_label = models.CharField(max_length=100, default='List Price')
    exchange_rate = models.DecimalField(max_digits=4,decimal_places=2,null=False, blank=False, default=1)
    currency = models.CharField(max_length=3,default='inr',choices=(
        ('inr','inr'),
        ('usd','usd')))

    def __unicode__(self):
        return self.name

class Price(models.Model):
    ''' Maintians the price for a rate_chart in a price_list
        Optionally defines if a price is time based and the time range
    '''

    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    price_list = models.ForeignKey(PriceList)
    list_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    cashback_amount = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True, default=Decimal(0))
    price_type = models.CharField(max_length=15, db_index=True, choices = (
        ('fixed', 'Fixed pricing'),
        ('timed', 'Time based pricing')), default='fixed')
    start_time = models.DateTimeField(null=True, blank=True, db_index=True)
    end_time = models.DateTimeField(null=True, blank=True, db_index=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __unicode__(self):
        if self.price_type == 'timed':
            return 'price for %s in %s - %s - %s TO %s' % (self.rate_chart, self.price_list, self.price_type, self.start_time, self.end_time)
        else:#Fixed
            return 'price for %s in %s - %s' % (self.rate_chart, self.price_list, self.price_type)

    def getSavings(self):
        if self.list_price and self.offer_price:
           return self.list_price - self.offer_price
        return 0

    def getDiscount(self):
        if self.list_price:
            return int(round((Decimal(self.getSavings())/Decimal(self.list_price))*100))
        return 0

    def clean(self):
        if self.price_type == 'timed':
            if not self.start_time:
                raise ValidationError(
                    'Start time cannot be null for price_type fixed')
            if not self.end_time:
                raise ValidationError(
                    'End time cannot be null for price_type fixed')
            if not self.end_time > self.start_time:
                raise ValidationError(
                    'End time should be after start time')

    def save(self, *args, **kwargs):
        self.clean() #raises validation error if something is invalid
        super(Price, self).save(*args, **kwargs)

class ClientLevelPriceList(models.Model):
    price_list = models.ForeignKey(PriceList)
    client = models.ForeignKey('accounts.Client')
    priority = models.IntegerField()
    def __unicode__(self):
        return 'price for %s in %s with priority %s' % (self.price_list, self.client.name, self.priority)

class DomainLevelPriceList(models.Model):
    price_list = models.ForeignKey(PriceList)
    domain = models.ForeignKey('accounts.ClientDomain')
    priority = models.IntegerField()

    def __unicode__(self):
        return 'price for %s in %s with priority %s' % (self.price_list, self.domain, self.priority)
        
class PriceVersion(models.Model):
    ''' Maintains the price for a rate_chart in a when it is
        uploaded through pricing tool or SAP feed.
    '''

    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    price_list = models.ForeignKey(PriceList)
    current_list_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    new_list_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    current_offer_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    new_offer_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    current_cashback_amount = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    new_cashback_amount = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)   
    price_type = models.CharField(max_length=15, db_index=True, choices = (
        ('fixed', 'Fixed pricing'),
        ('timed', 'Time based pricing')), default='fixed')
    current_start_time = models.DateTimeField(null=True, blank=True)
    new_start_time = models.DateTimeField(null=True, blank=True)
    current_end_time = models.DateTimeField(null=True, blank=True)
    new_end_time = models.DateTimeField(null=True, blank=True)
    action = models.CharField(max_length=10, db_index=True, choices = (
        ('add', 'Add'),
        ('update', 'Update'),
        ('delete','Delete')), default='update')
    status = models.CharField(max_length=20, db_index=True, choices = (
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved')), default='pending')
    created_by = models.CharField(max_length=50, null=True, blank=True)
    created_on = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=50, null=True, blank=True)
    approved_on = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        if self.price_type == 'timed':
            return '%s - %s - %s - %s TO %s' % (self.rate_chart, self.price_list, self.price_type, self.new_start_time, self.new_end_time)
        else:#Fixed
            return '%s - %s - %s' % (self.rate_chart, self.price_list, self.price_type)
