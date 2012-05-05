from django.db import models
from imagekit.models import ImageModel
from datetime import datetime
from catalog.models import Product, ProductTags, Tag, SellerRateChart
from storage import upload_storage
from decimal import Decimal
# Create your models here.

class List(ImageModel):
	title = models.CharField(max_length=1000)
	slug = models.SlugField(max_length=1000, null=True, blank=True)
	client = models.ForeignKey('accounts.Client', null=True, blank=True)
	type = models.CharField(max_length=50, choices=(
        ('wishlist','Wishlist'),
        ('new_arrivals', 'New Arrivals'),
        ('ezone_arrivals', 'Ezone Arrivals'),
        ('hot_sellers', 'Hot Sellers'),
        ('ezone_hotsellers', 'Ezone Hot Sellers'),
        ('rock_bottom_offers', 'RockBottom Offers'),
        ('rockbottom', 'Ezone RockBottom Offers'),
        ('desidime_offer','Desidime Offer'),
        ('itz_offer','Itz Offer'),
        ('visa_offer','Visa Offer'),
        ('bigbazaar_hot_offers','Bigbazaar Hot Offers'),
        ('khojguru_offer','Khojguru Offer'),
        ('upto75_offer','Upto75 Offer'),
        ('clearance','Clearance'),
        ('promotion_offer','Promotion Offer'),
        ('promotions', 'Promotions'),
        ('eureka','Eureka'),
        ('sabse_sasta_sale','Sabse Sasta Sale'),
	),
        default = 'eureka', db_index=True)

	template_type = models.CharField(max_length=50, choices=(
		('static', 'Static'),
		('dynamic','Dynamic')),	
		default = 'dynamic', db_index=True)
	curator = models.ForeignKey('users.Profile', null=True, blank=True)
	description = models.TextField()
	banner_image = models.ImageField(blank=True, null=True, upload_to='list/%Y/%m', storage=upload_storage)
	tagline = models.CharField(max_length=1000, blank=True, null=True)
	redirect_to = models.CharField(max_length=100, blank=True, null=True)
	banner_type = models.CharField(max_length=50, choices=(
		('image_mapping', 'Image Mapping'),
		('direct_link', 'Direct Link'),
		),
		default='direct_link')

	starts_on = models.DateTimeField(blank=True, null=True, db_index=True)
	ends_on = models.DateTimeField(blank=True, null=True, db_index=True)
	is_featured = models.BooleanField(default=False)
	percent_on_10 = models.DecimalField(max_digits=22, decimal_places=2, default=Decimal("5"))
	percent_on_5 = models.DecimalField(max_digits=22, decimal_places=2, default=Decimal("2.5"))

	detail_page_banner = models.ImageField(upload_to='top10/%Y/%m/%d/detail_banner', storage=upload_storage, blank=True, null=True)
	detail_page_thumb_banner = models.ImageField(upload_to='top10/%Y/%m/%d/detail_thumb_banner', storage=upload_storage, blank=True, null=True)
	home_page_thumb_banner = models.ImageField(upload_to='list/%Y/%m/home_thumb_banner', storage=upload_storage, blank=True, null=True)

	freebies_banner = models.ImageField(upload_to='battle/%Y/%m/%d/freebies_banner', storage=upload_storage, blank=True, null=True)
	visibility = models.CharField(max_length=10, default='private',choices=(
        ('public','Public'),
        ('private','Private')))

	class IKOptions:
			# This inner class is where we define the ImageKit options for the model
		spec_module = 'lists.specs'
		cache_dir = 'lc'
		image_field = 'banner_image'

	def update_solr_index(self):
		for l in self.listitem_set.all():
			product = l.sku.product
			try:	
				tag = ProductTags.objects.get(product=product,tag__tag=self.type)
			except ProductTags.DoesNotExist:
			   assign_tag = Tag.objects.get(tag=self.type)
			   tag = ProductTags(product=product,tag=assign_tag)
			   tag.save()
            #if self.is_featured == False:
            #    tag.delete(using='default')
            #product.update_solr_index()

	def add_item(self,item):
		try:
			l = ListItem.objects.get(list=self,sku=item)
		except ListItem.DoesNotExist:
			l = ListItem(list=self,sku=item,sequence=1)
			l.save()
		return l

	def url(self):
		if self.type == "battle":
			return "search/t/battle/"
		elif self.type == "promotions":
			return "promotions/%s/%s/" % (self.slug, self.id)
		elif self.type == "ending_soon":
			return "ending-soon/%s/%s/" % (self.slug, self.id)
		elif self.type == "promotion_offer":
			return "promotion_offer/%s/%s/" % (self.slug, self.id)
		else:
			return "top10/%s/%s/" % (self.slug,self.id)

	def __unicode__(self):
		return self.title

	def remaining_time(self):
		delta = self.ends_on - datetime.now()
		hours = delta.seconds/3600
		mins = (delta.seconds/60) % 60
		secs = delta.seconds - 60*mins - 3600*hours
		return (delta.days, hours, mins, secs)

	def banner_thumb(self):
		return self.bannerthumb.url

	def banner_main(self):
		return self.bannermain.url

	def get_active_items(self):
		return self.listitem_set.select_related(
			'sku',
			'sku__product',
			).filter(status='active').order_by('sequence')[:10]

	def get_url(self):
		if self.type == 'top_10':
			return 'top10/%s/%s/' % (self.slug, self.id)
		if self.type == 'battle':
			return 'battle/%s/%s/' % (self.slug, self.id)
		return ''

class ListItem(ImageModel):
    list = models.ForeignKey('List')
    sku = models.ForeignKey('catalog.SellerRateChart', null=True, blank=True)
    sequence = models.PositiveIntegerField(blank=True, null=True, default=1)
    user_description = models.TextField(blank=True)
    user_title = models.CharField(max_length=1000, blank=True)
    user_image = models.ImageField(blank=True, null=True, upload_to='listitem/%Y/%m', storage=upload_storage)
    user_features = models.TextField(blank=True, null=True, help_text='Enter one feature per line')
    starts_on = models.DateTimeField(blank=True, null=True)
    ends_on = models.DateTimeField(blank=True, null=True)
    status = models.CharField(blank=True, null=True,  max_length=10, default='active', choices=(
        ('active', 'Active'),
        ('in_queue','In Queue')), db_index=True)
    redirect_to = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        unique_together = ('list','sku')
    class IKOptions:
        # This inner class is where we define the ImageKit options for the model
		spec_module = 'lists.specs'
		cache_dir = 'lci'
		image_field = 'user_image'
    def __unicode__(self):
		return self.sku.product.title
    def get_desc(self):
		if self.user_description:
			return self.user_description
		else:
			return self.sku.product.description
    def get_item_title(self):
		if self.user_title.strip():
			return self.user_title.strip()
		else:
			return self.sku.product.title
    def get_filmstrip_image(self):
		if self.user_image:
			return self.filmstrip.url
		else:
			return self.sku.product.get_large_thumb_url()
    def get_thumb_image(self):
		if self.user_image:
			return self.thumbnail.url
		else:
			return self.sku.product.get_large_thumb_url()
    def get_features(self):
		if self.user_features:
			return self.user_features.replace('\r','').split('\n')
		else:
			# XXX Dont know what to return yet
			return ''
    def remaining_time(self):
		delta = self.ends_on - datetime.now()
		hours = delta.seconds/3600
		mins = (delta.seconds/60) % 60
		secs = delta.seconds - 60*mins - 3600*hours
		return (delta.days, hours, mins, secs)

class Tab(models.Model):
	name = models.CharField(max_length=100)
	list = models.ForeignKey(List)
	sort_order = models.IntegerField()

	def __unicode__(self):
		return self.name

class BattleTab(models.Model):
	name = models.CharField(max_length=100)
	tag_name = models.CharField(max_length=100, null=True, blank=True)
	list = models.ForeignKey(List)
	sort_order = models.IntegerField()
	def __unicode__(self):
		return self.name
