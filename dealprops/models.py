from tinymce.models import HTMLField
from south.modelsinspector import add_introspection_rules
import re
from django.db import models
from imagekit.models import ImageModel
from datetime import datetime
from storage import upload_storage
from catalog.models import ProductTags,Tag
from accounts.models import Client
from django.template.defaultfilters import slugify


add_introspection_rules([],["^tinymce\.models\.HTMLField"])
# Create your models here.

class DailyDeal(models.Model):
    rate_chart = models.ForeignKey('catalog.SellerRateChart',limit_choices_to={'product__status':'active'}, blank=True, null=True)
    client = models.ForeignKey('accounts.Client', default=5)
    starts_on = models.DateTimeField(db_index=True)
    ends_on = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=15, db_index=True, choices=(
        ('draft','Draft'),
        ('published', 'Published')))
    type = models.CharField(max_length=15, default="hero", blank=False, choices=(
        ('hero_deal','Hero Deal'),
        ('todays_deals', 'Todays Deals'),
        ('clearance_deals', 'Clearance Deals')))

    title = models.CharField(max_length=100, blank=False, null=False)
    slug = models.CharField(max_length=100, blank=True, null=True)
    tag_line = models.TextField(blank=True, null=True)
    tag_line_color_code = models.CharField(max_length=50, blank=True, null=True)
    note_bg_color_code = models.CharField(max_length=50, blank=True, null=True)
    n_orders = models.PositiveIntegerField(default=0, null=True, blank=True)
    description = HTMLField(null=True,blank=True)
    features = models.TextField(help_text='Enter one feature per line', blank=True)
    product_color_code = models.CharField(max_length=50, blank=True, null=True)
    market_price_color_code = models.CharField(max_length=50, blank=True, null=True)
    todays_steal_color_code = models.CharField(max_length=50, blank=True, null=True)
    home_thumb_banner = models.ImageField(upload_to='dailydeal/%Y/%m/%d/home_thumb_banner', storage=upload_storage, blank=True, null=True)
    weekday_image = models.ImageField(upload_to='dailydeal/%Y/%m/%d/weekday', storage=upload_storage, blank=True, null=True)

    in_box_accessories = models.TextField(blank=True, null=True)
    manufactures_warranty = models.CharField(max_length=50,help_text='Plz specify data in Months OR Years.', null=True, blank=True)
 

    def __unicode__(self):
        return '%s on %s to %s' % (self.title, 
                self.starts_on.strftime('%d-%m-%Y'), self.ends_on.strftime('%d-%m-%Y'))

    def remaining_time(self, **kwargs):
        delta = self.ends_on - datetime.now()
        hours = delta.seconds/3600
        mins = (delta.seconds/60) % 60
        secs = delta.seconds - 60*mins - 3600*hours
        data = {
                'days' : delta.days,
                'hours' : hours,
                'mins' : mins, 
                'secs' : secs
            }
        render_data = kwargs.get("render_data", None)
        if render_data and render_data in data:
            return data[render_data]
        return (delta.days, hours, mins, secs)
    
    def update_solr_index(self):
	product = self.rate_chart.product
    	try:
	    tag = ProductTags.objects.get(product=product,tag__tag="steal")
    	except ProductTags.DoesNotExist:
	    assign_tag = Tag.objects.get(tag="steal")
	    tag = ProductTags(product=product,tag=assign_tag)
	    tag.save()
        product.update_solr_index()

    def get_url(self):
        return "stealoftheday/%s/%s/" % (self.slug, self.id)

    def save(self, *args, **kwargs):
        super(DailyDeal, self).save(*args, **kwargs)
        if not self.slug:
            self.slug = slugify(self.title)
            self.save()

class DailyDealProduct(models.Model):
    product = models.ForeignKey('catalog.Product',limit_choices_to={'status':'active'} , help_text="Select Product as per suggested")
    daily_deal = models.ForeignKey(DailyDeal)
    order = models.PositiveIntegerField(default=1)
    def __unicode__(self):
        return self.product.title

class DailyDealImage(ImageModel):
    daily_deal = models.ForeignKey(DailyDeal)
    image = models.ImageField(upload_to='dailydeal/%Y/%m/%d', storage=upload_storage)
    order = models.PositiveIntegerField(default=1)

    class IKOptions:
        # This inner class is where we define the ImageKit options for the model
        spec_module = 'dealprops.specs'
        cache_dir = 'dp'
        image_field = 'image'


class MidDayDeal(models.Model):
    starts_on = models.DateTimeField()
    ends_on = models.DateTimeField()
    status = models.CharField(max_length=15, db_index=True,default="published", choices=(
        ('draft','Draft'),
        ('published', 'Published')))
    title = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return "%s, %s to %s" % (self.title,self.starts_on,self.ends_on)

class MidDayProducts(models.Model):
    midday = models.ForeignKey(MidDayDeal)
    sku = models.ForeignKey('catalog.SellerRateChart')
    sequence = models.PositiveIntegerField()

    description = models.TextField(blank=True)
    title = models.CharField(max_length=1000, blank=True)
    image = models.ImageField(blank=True, null=True, upload_to='midday/%Y/%m', storage=upload_storage)
    features = models.TextField(blank=True, null=True, help_text='Enter one feature per line')
    
    def __unicode__(self):
        return self.sku.product.title
    class Meta:
        unique_together = ('midday','sku')

class FridayDeal(models.Model):
    starts_on = models.DateTimeField()
    ends_on = models.DateTimeField()
    status = models.CharField(max_length=15, db_index=True,default="published", choices=(
        ('draft','Draft'),
        ('published', 'Published')))
    title = models.CharField(max_length=100, blank=True)
    banner_image = models.ImageField(blank=True, null=True, upload_to='fridaydeal/%Y/%m', storage=upload_storage)

    def remaining_time(self):
        delta = self.ends_on - datetime.now()
        hours = delta.seconds/3600
        mins = (delta.seconds/60) % 60
        secs = delta.seconds - 60*mins - 3600*hours
        return (delta.days, hours, mins, secs)

    def __unicode__(self):
        return "%s, %s to %s" % (self.title,self.starts_on,self.ends_on)

class FridayDealProducts(models.Model):
    deal = models.ForeignKey(FridayDeal)
    product = models.ForeignKey('catalog.Product')
    sequence = models.PositiveIntegerField()
    title = models.CharField(max_length=1000, blank=True)
    starts_on = models.DateTimeField(blank=False, null=False)
    ends_on = models.DateTimeField(blank=False, null=False)

    def __unicode__(self):
        return self.product.title

    def remaining_time(self):
        delta = self.ends_on - datetime.now()
        hours = delta.seconds/3600
        mins = (delta.seconds/60) % 60
        secs = delta.seconds - 60*mins - 3600*hours
        return (delta.days, hours, mins, secs)

    class Meta:
        unique_together = ('deal','product')
