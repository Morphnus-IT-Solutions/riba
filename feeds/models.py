from django.db import models

# Create your models here.
class BrandBlackList(models.Model):
    class Meta:
        unique_together = ('brand','account')

    brand = models.CharField(max_length=200, db_index=True)
    account = models.CharField(max_length=100, db_index=True)

    def __unicode__(self):
        return self.brand

class CategoryBlackList(models.Model):
    class Meta:
        unique_together = ('category','account')

    category = models.CharField(max_length=200, db_index=True)
    account = models.CharField(max_length=100, db_index=True)

    def __unicode__(self):
        return self.category

class SKUBlackList(models.Model):
    class Meta:
        unique_together = ('sku', 'account')
    sku = models.CharField(max_length=200, db_index=True)
    account = models.CharField(max_length=100, db_index=True)

class BrandMapping(models.Model):
    class Meta:
        unique_together = ('brand','account')

    brand = models.CharField(max_length=200, db_index=True)
    account = models.CharField(max_length=100, db_index=True)
    mapped_to = models.ForeignKey('catalog.Brand')

class CategoryMapping(models.Model):
    class Meta:
        unique_together = ('category', 'account')

    category = models.CharField(max_length=200, db_index=True)
    account = models.CharField(max_length=100, db_index=True)
    mapped_to = models.ForeignKey('categories.Category')

class SKUInfo(models.Model):
    class Meta:
        unique_together = ('sku', 'account')

    sku = models.CharField(max_length=200, db_index=True)
    account = models.CharField(max_length=100, db_index=True)

    brand = models.ForeignKey('catalog.Brand', blank=True, null=True)
    category = models.ForeignKey('categories.Category', blank=True, null=True)
    product = models.ForeignKey('catalog.Product', blank=True, null=True)

    model = models.CharField(max_length=500, blank=True)

class FeatureMapping(models.Model):
    feature = models.ForeignKey('categories.Feature')
    # feature mapping might belong to a category mapping, brand mapping
    # or a sku mapping
    category_mapping = models.ForeignKey(CategoryMapping, blank=True, null=True)
    skuinfo = models.ForeignKey(SKUInfo, blank=True, null=True)
    brand_mapping = models.ForeignKey(BrandMapping, blank=True, null=True)

    data = models.CharField(max_length=1000, default='', blank=True)
    value = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True)
    bool = models.BooleanField(default=False)

    # action. This info might want us to add a feature or delete it.
    # This is will help us tackle wrongly-categorized products, where category indicates
    # certain features and have to be removed because of wrong categorization
    action = models.CharField(max_length=10, default='add', choices=(
        ('add','Add'),('delete','Delete')))

    feature_name = models.CharField(max_length=100, blank=True, null=True)
    sku_type = models.CharField(max_length=200, blank=True, null=True)
    account = models.CharField(max_length=30, blank=True, null=True)

    def to_python_value(self):
        from categories.models import FeatureChoice
        choices = FeatureChoice.objects.filter(feature=self.feature)
        if choices:
            selected_choices = [choice.choice.name for choice in 
                    FeatureSelectedChoice.objects.filter(feature_mapping=self)]
            return selected_choices
            
        if self.feature.type == 'number':
            return self.value
        if self.feature.type == 'boolean':
            return self.bool
        if self.feature.type == 'text':
            return self.data

    def __unicode__(self):
        return self.feature.name

                        

class FeatureSelectedChoice(models.Model):
    class Meta:
        unique_together = ('choice','feature_mapping')

    choice = models.ForeignKey('categories.FeatureChoice')
    feature_mapping = models.ForeignKey(FeatureMapping)

    def __unicode__(self):
        return self.choice.name

class AvailabilityMap(models.Model):
    account = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=200, db_index=True, blank=True)
    brand = models.CharField(max_length=200, db_index=True, blank=True)
    sku = models.CharField(max_length=200, db_index=True, blank=True)

    applies_to = models.CharField(max_length=25, db_index=True,
            default='account', choices=(
                ('account','Account'),
                ('brand','Brand'),
                ('category','Category'),
                ('sku','SKU')))

    availability = models.ForeignKey('catalog.Availability')

class SyncEvent(models.Model):
    account = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    # status
    status = models.CharField(max_length=25, default='running', choices=(
        ('running','Running'),
        ('dead','Dead'),
        ('finished','Finished')))
    stack_trace = models.TextField(blank=True)

    # some timestamps for analyzing later
    started_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)

    # counts
    new_masters = models.PositiveIntegerField(default=0)
    found = models.PositiveIntegerField(default=0)
    adds = models.PositiveIntegerField(default=0)
    deletes = models.PositiveIntegerField(default=0)
    edits = models.PositiveIntegerField(default=0)
    unavailable = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return 'Sync for %s at %s' % (self.account, self.started_at)

class SyncEventProductMapping(models.Model):
    sync_event = models.ForeignKey(SyncEvent)
    sku = models.CharField(max_length=100, db_index=True, blank=True, default='')
    item_title = models.CharField(max_length=1000, blank=True, default='')
    product = models.ForeignKey('catalog.Product')
    action = models.CharField(max_length=25, db_index=True, choices=(
        ('added','Added'),
        ('marked_as_unavailable', 'Marked as unavailable')))

class SyncEventRateChartMapping(models.Model):
    sync_event = models.ForeignKey(SyncEvent)
    sku = models.CharField(max_length=100, db_index=True, blank=True, default='')
    item_title = models.CharField(max_length=1000, blank=True, default='')
    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    change_log = models.TextField(blank=True)
    action = models.CharField(max_length=25, db_index=True, choices=(
        ('added','Added'),
        ('edited','Edited'),
        ('marked_as_deleted', 'Marked as deleted')))

class SkuTypeProductTypeMapping(models.Model):
    account = models.CharField(max_length=100, db_index=True)
    sku_type = models.CharField(max_length=200, db_index=True)
    product_type = models.ForeignKey('categories.ProductType')

class APIResponse(models.Model):
    client = models.CharField(max_length=100, blank=True)
    session_id = models.CharField(max_length=50, blank=True, db_index=True)
    login = models.CharField(max_length=200, blank=True, db_index=True)
    order_id = models.CharField(max_length=50, blank=True, db_index=True)
    url = models.CharField(max_length=1000, blank=True, default='')
    post = models.TextField(blank=True, default='')
    response = models.TextField(blank=True, default='')


class SubscriptionSync(models.Model):
    ext_id = models.CharField(max_length=200, unique=True)
    account = models.CharField(max_length=100, db_index=True)

class ExtPricelist(models.Model):
    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    priceList = models.ForeignKey('pricing.PriceList')
    list_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2,
        null=True, blank=True)
    account = models.ForeignKey('accounts.Account')
